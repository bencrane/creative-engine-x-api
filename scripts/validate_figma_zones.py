#!/usr/bin/env python3
"""
Figma Scaffold Zone Extraction & Cross-Validation Script.

Extracts zone dimensions from Figma metadata text labels (which contain
explicit inch measurements) and cross-validates against JSON constraint files.

Usage:
    python3 scripts/validate_figma_zones.py dump
    python3 scripts/validate_figma_zones.py validate [--tolerance 0.01] [--scaffold postcard-4x6]
"""

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.scaffolds import get_by_slug, list_slugs

PPI = 96

# --- Data models ---

@dataclass
class ExtractedDimension:
    """A dimension extracted from a text label."""
    label: str       # What this dimension describes
    width_in: float
    height_in: float
    source_text: str  # The raw text it came from


@dataclass
class ExtractedSurface:
    surface_id: str
    label: str
    # Canvas frame dimensions (the CSS surface div)
    canvas_width_px: float = 0
    canvas_height_px: float = 0
    dimensions: list[ExtractedDimension] = field(default_factory=list)

    @property
    def canvas_width_in(self) -> float:
        return self.canvas_width_px / PPI

    @property
    def canvas_height_in(self) -> float:
        return self.canvas_height_px / PPI


@dataclass
class ExtractedPage:
    page_name: str
    page_id: str
    slug: str
    surfaces: list[ExtractedSurface] = field(default_factory=list)
    # Page-level text labels (from heading area)
    header_dims: list[ExtractedDimension] = field(default_factory=list)


# --- Page name → slug mapping ---

PAGE_SLUG_MAP = {
    "Postcard 4x6": "postcard-4x6",
    "Postcard 5x7": "postcard-5x7",
    "Postcard 6x9": "postcard-6x9",
    "Postcard 6x11": "postcard-6x11",
    "Letter 8.5x11": "letter-8.5x11",
    "Letter 8.5x14": "letter-8.5x14",
    "Self-Mailer 6x18 Bifold": "selfmailer-6x18-bifold",
    "Self-Mailer 12x9 Bifold": "selfmailer-12x9-bifold",
    "Self-Mailer 11x9 Bifold": "selfmailer-11x9-bifold",
    "Self-Mailer 17.75x9 Trifold": "selfmailer-17.75x9-trifold",
    "Snap Pack 8.5x11": "snappack-8.5x11",
    "Booklet 8.375x5.375": "booklet-8.375x5.375",
    "Buckslip": "buckslip",
    "Card Affix": "card-affix",
}


def page_name_to_slug(name: str) -> str | None:
    clean = re.sub(r"\s*[-–—]\s*Base Scaffold.*$", "", name, flags=re.IGNORECASE).strip()
    if clean in PAGE_SLUG_MAP:
        return PAGE_SLUG_MAP[clean]
    normalized = re.sub(r"[^a-z0-9x.]", "", clean.lower())
    for slug in list_slugs():
        slug_norm = re.sub(r"[^a-z0-9x.]", "", slug.lower())
        if normalized == slug_norm or slug_norm in normalized:
            return slug
    return None


# --- Text label dimension parsers ---

def parse_dim_pair(text: str) -> list[tuple[str, float, float]]:
    """
    Extract WxH dimension pairs from text labels like:
      'File: 6.25" x 4.25" | Trim: 6" x 4" | Safe: 5.875"'
      '3.2835" x 2.375"'
      'TRIM LINE — 6" x 4"'
      '3.875" x 5.875" SAFE ZONE (0.0625" inset)'
      'GLUE ZONE — 9" x 0.5"'
    Returns list of (context_label, width, height).
    """
    results = []
    # Unescape XML entities
    text = text.replace("&quot;", '"').replace("&amp;", "&")

    # Pattern: labeled pairs like "File: 6.25" x 4.25""
    for m in re.finditer(r'(\w[\w\s]*?):\s*([\d.]+)[""]\s*x\s*([\d.]+)["""]', text):
        label = m.group(1).strip()
        w, h = float(m.group(2)), float(m.group(3))
        results.append((label, w, h))

    # Pattern: "W" x H" LABEL" (dimensions before label)
    for m in re.finditer(r'([\d.]+)[""]\s*x\s*([\d.]+)[""]\s+([\w\s]+?)(?:\(|$|[|—])', text):
        label = m.group(3).strip()
        w, h = float(m.group(1)), float(m.group(2))
        results.append((label, w, h))

    # Pattern: "LABEL — W" x H"" or "LABEL LINE — W" x H""
    for m in re.finditer(r'([\w\s]+?)\s*[—–-]\s*([\d.]+)[""]\s*x\s*([\d.]+)["""]', text):
        label = m.group(1).strip()
        w, h = float(m.group(2)), float(m.group(3))
        if label.upper() not in [r[0].upper() for r in results]:
            results.append((label, w, h))

    # Pattern: standalone "W" x H"" (no label)
    if not results:
        for m in re.finditer(r'([\d.]+)[""]\s*x\s*([\d.]+)["""]', text):
            w, h = float(m.group(1)), float(m.group(2))
            results.append(("unlabeled", w, h))

    return results


def parse_single_dim(text: str) -> list[tuple[str, float]]:
    """
    Extract single dimensions like:
      'BLEED (0.125")'
      'SAFE ZONE (0.0625" inset)'
      '0.5" no-print border'
    """
    results = []
    text = text.replace("&quot;", '"').replace("&amp;", "&")

    # "LABEL (N" ...)"
    for m in re.finditer(r'([\w\s-]+?)\s*\(\s*([\d.]+)["""]', text):
        results.append((m.group(1).strip(), float(m.group(2))))

    # "N" LABEL"
    for m in re.finditer(r'([\d.]+)[""]\s+([\w-]+)', text):
        results.append((m.group(2).strip(), float(m.group(1))))

    return results


# --- Figma XML structure understanding ---

def direct_text_children(elem: ET.Element) -> list[str]:
    """Get text 'name' attributes from DIRECT children only (not recursive)."""
    texts = []
    for child in elem:
        if child.tag == "text":
            name = child.get("name", "")
            if name:
                texts.append(name)
        # Also check one level deeper (text inside a label Container)
        for grandchild in child:
            if grandchild.tag == "text":
                name = grandchild.get("name", "")
                if name:
                    texts.append(name)
    return texts


def identify_surface(texts: list[str]) -> tuple[str, str] | None:
    """Identify surface type from text labels."""
    combined = " ".join(texts).lower()
    if "front" in combined and "back" not in combined:
        return ("front", "Front")
    if "back" in combined and "front" not in combined:
        return ("back", "Back")
    if "outside" in combined and "inside" not in combined:
        return ("outside", "Outside")
    if "inside" in combined and "outside" not in combined:
        return ("inside", "Inside")
    if "page 1" in combined:
        return ("page1", "Page 1")
    if "subsequent" in combined:
        return ("pageN", "Subsequent Pages")
    return None


def find_canvas_frames(surface_container: ET.Element) -> list[ET.Element]:
    """
    Find the actual canvas frames within a surface container.
    These are the frames that represent the CSS surface divs (file-size dimensions).
    They're typically the largest child frames within the surface.
    """
    candidates = []
    for child in surface_container:
        if child.tag == "frame":
            w = float(child.get("width", "0"))
            h = float(child.get("height", "0"))
            # Canvas frames are substantial (>100px both dims)
            if w > 100 and h > 100:
                candidates.append(child)
    # Sort by area descending — the canvas is usually the largest
    candidates.sort(key=lambda f: float(f.get("width", "0")) * float(f.get("height", "0")), reverse=True)
    return candidates


# --- Main parser ---

def parse_metadata(xml_text: str) -> list[ExtractedPage]:
    root = ET.fromstring(xml_text)
    pages = []

    for scaffold_frame in root:
        if scaffold_frame.tag != "frame":
            continue
        name = scaffold_frame.get("name", "")
        frame_id = scaffold_frame.get("id", "")
        slug = page_name_to_slug(name)
        if not slug:
            print(f"  [SKIP] Could not map page '{name}' to a slug", file=sys.stderr)
            continue

        page = ExtractedPage(page_name=name, page_id=frame_id, slug=slug)

        # Collect ALL text nodes in this scaffold for dimension extraction
        all_texts = []
        for text_elem in scaffold_frame.iter("text"):
            t = text_elem.get("name", "")
            if t:
                all_texts.append(t)

        # Extract dimensions from header text (first few text nodes)
        for t in all_texts[:5]:
            for label, w, h in parse_dim_pair(t):
                page.header_dims.append(ExtractedDimension(label, w, h, t[:80]))

        # Now walk the structure to find surfaces and their zones
        # The structure is: scaffold > Body > Container (content area) > surface containers
        body = scaffold_frame.find("frame")  # Body
        if body is None:
            pages.append(page)
            continue

        # Find the main content container (skip headings)
        content_containers = []
        for child in body:
            if child.tag == "frame":
                w = float(child.get("width", "0"))
                h = float(child.get("height", "0"))
                # The content area is the large container below headings
                if w > 400 and h > 200:
                    content_containers.append(child)

        if not content_containers:
            # Fallback: use body itself
            content_containers = [body]

        # Within the content area, find surface containers
        # Surface containers are identified by their label text children
        for content in content_containers:
            surface_groups = _find_surface_groups(content)

            if surface_groups:
                for sid, slabel, frame in surface_groups:
                    surface = _extract_surface(sid, slabel, frame, all_texts)
                    page.surfaces.append(surface)
            else:
                # Single surface — extract from the content container itself
                surface = _extract_surface("all", "All", content, all_texts)
                page.surfaces.append(surface)

        pages.append(page)

    return pages


def _find_surface_groups(container: ET.Element) -> list[tuple[str, str, ET.Element]]:
    """
    Find surface group frames within a container.
    Each surface group has a text label (FRONT/BACK/etc) and contains the canvas.
    """
    results = []
    for child in container:
        if child.tag != "frame":
            continue
        # Check direct text children for surface labels
        texts = direct_text_children(child)
        surface = identify_surface(texts)
        if surface:
            w = float(child.get("width", "0"))
            h = float(child.get("height", "0"))
            if w > 100 and h > 100:
                results.append((surface[0], surface[1], child))
    return results


def _extract_surface(sid: str, label: str, frame: ET.Element, all_texts: list[str]) -> ExtractedSurface:
    """Extract dimension data from a surface frame."""
    surface = ExtractedSurface(surface_id=sid, label=label)

    # Find the canvas frame (largest child that represents the CSS surface)
    canvases = find_canvas_frames(frame)
    if canvases:
        canvas = canvases[0]
        surface.canvas_width_px = float(canvas.get("width", "0"))
        surface.canvas_height_px = float(canvas.get("height", "0"))

        # Extract dimensions from ALL text nodes within this surface's tree
        for text_elem in frame.iter("text"):
            t = text_elem.get("name", "")
            if not t:
                continue

            # Parse WxH pairs
            for dim_label, w, h in parse_dim_pair(t):
                surface.dimensions.append(ExtractedDimension(dim_label, w, h, t[:80]))

            # Parse single dimensions (insets, borders)
            for dim_label, val in parse_single_dim(t):
                # Store as width=val, height=0 for single dims
                surface.dimensions.append(ExtractedDimension(dim_label, val, 0, t[:80]))
    else:
        surface.canvas_width_px = float(frame.get("width", "0"))
        surface.canvas_height_px = float(frame.get("height", "0"))

    return surface


# --- Comparison logic ---

@dataclass
class ComparisonResult:
    scaffold: str
    surface: str
    check: str
    expected: float
    actual: float
    diff: float
    status: str  # "OK", "WARN", "MISMATCH", "MISSING"


def _closer_match(aw: float, ah: float, ew: float, eh: float) -> bool:
    """Check if (aw, ah) is a closer match to (ew, eh) than (ah, aw)."""
    direct = abs(aw - ew) + abs(ah - eh)
    swapped = abs(ah - ew) + abs(aw - eh)
    return direct <= swapped


def _check(slug: str, surface: str, check: str, expected: float, actual: float, tolerance: float) -> ComparisonResult:
    diff = abs(expected - actual)
    if diff <= tolerance:
        status = "OK"
    elif diff <= tolerance * 3:
        status = "WARN"
    else:
        status = "MISMATCH"
    return ComparisonResult(slug, surface, check, expected, actual, diff, status)


def _find_dim(dims: list[ExtractedDimension], label_pattern: str) -> ExtractedDimension | None:
    """Find a dimension by label pattern (case-insensitive regex)."""
    for d in dims:
        if re.search(label_pattern, d.label, re.IGNORECASE):
            return d
    return None


def compare_scaffold(page: ExtractedPage, tolerance: float) -> list[ComparisonResult]:
    results = []
    scaffold = get_by_slug(page.slug)
    if not scaffold:
        return [ComparisonResult(page.slug, "-", "scaffold lookup", 0, 0, 0, "ERROR")]

    dims = scaffold.get("dimensions")
    bleed_model = scaffold.get("bleedModel", {})
    safe_zone = scaffold.get("safeZone")

    if not dims:
        # Some formats (card-affix) use orientations instead of dimensions
        return results
    json_surfaces = scaffold.get("surfaces", [])

    # Collect dimensions from surface-level text (more reliable than header due to orientation)
    # Surface text uses CSS layout orientation (width x height matching the actual canvas)
    all_surface_dims = []
    for s in page.surfaces:
        all_surface_dims.extend(s.dimensions)

    # --- File dimensions from header (only if clearly labeled "File") ---
    file_dim = _find_dim(page.header_dims, r"^File$|^File with bleed$|^Bleed$")
    if file_dim and file_dim.height_in > 0:
        fw, fh = file_dim.width_in, file_dim.height_in
        ew, eh = dims["fileWidth"], dims["fileHeight"]
        if _closer_match(fw, fh, ew, eh):
            results.append(_check(page.slug, "header", "File width", ew, fw, tolerance))
            results.append(_check(page.slug, "header", "File height", eh, fh, tolerance))
        else:
            results.append(_check(page.slug, "header", "File width", ew, fh, tolerance))
            results.append(_check(page.slug, "header", "File height", eh, fw, tolerance))

    # --- Bleed inset (single value) ---
    bleed_dim = _find_dim(all_surface_dims, r"^BLEED$")
    if bleed_dim and bleed_dim.height_in == 0:
        results.append(_check(page.slug, "header", "Bleed inset", bleed_model.get("bleed", 0), bleed_dim.width_in, tolerance))

    # --- Trim dimensions (from surface-level TRIM labels, not header) ---
    trim_dim = _find_dim(all_surface_dims, r"^TRIM")
    if trim_dim:
        # Surface-level trim text uses CSS orientation — but may still be HxW
        # Try both orientations and pick the one that matches better
        tw, th = trim_dim.width_in, trim_dim.height_in
        ew, eh = dims["trimWidth"], dims["trimHeight"]
        if _closer_match(tw, th, ew, eh):
            results.append(_check(page.slug, "header", "Trim width", ew, tw, tolerance))
            results.append(_check(page.slug, "header", "Trim height", eh, th, tolerance))
        else:
            # Swapped orientation
            results.append(_check(page.slug, "header", "Trim width", ew, th, tolerance))
            results.append(_check(page.slug, "header", "Trim height", eh, tw, tolerance))

    # --- Safe zone ---
    if safe_zone:
        safe_dim = _find_dim(all_surface_dims, r"safe|SAFE")
        if safe_dim and safe_dim.height_in > 0:
            sw, sh = safe_dim.width_in, safe_dim.height_in
            ew, eh = safe_zone["safeWidth"], safe_zone["safeHeight"]
            if _closer_match(sw, sh, ew, eh):
                results.append(_check(page.slug, "header", "Safe width", ew, sw, tolerance))
                results.append(_check(page.slug, "header", "Safe height", eh, sh, tolerance))
            else:
                results.append(_check(page.slug, "header", "Safe width", ew, sh, tolerance))
                results.append(_check(page.slug, "header", "Safe height", eh, sw, tolerance))

    # --- Per-surface zone checks ---
    for surface in page.surfaces:
        surface_label = f"{surface.label} ({surface.surface_id})"

        # Canvas frame should match file dimensions
        if surface.canvas_width_px > 0:
            results.append(_check(
                page.slug, surface_label, "Canvas width",
                dims["fileWidth"], surface.canvas_width_in, tolerance
            ))
            results.append(_check(
                page.slug, surface_label, "Canvas height",
                dims["fileHeight"], surface.canvas_height_in, tolerance
            ))

        # Find matching JSON surface
        json_surface = None
        for js in json_surfaces:
            if js["id"] == surface.surface_id:
                json_surface = js
                break

        if not json_surface:
            continue

        # Check zone dimensions from text labels
        for json_zone in json_surface.get("zones", []):
            zone_id = json_zone["id"]
            zone_size = json_zone.get("size", {})

            # Try to find matching dimension in extracted text
            zone_dim = None
            if "ink-free" in zone_id:
                zone_dim = _find_dim(surface.dimensions, r"ink.?free|address.*postage")
            elif "glue" in zone_id:
                zone_dim = _find_dim(surface.dimensions, r"glue")
            elif "address-block" in zone_id:
                zone_dim = _find_dim(surface.dimensions, r"address")
            elif "qr-code" in zone_id:
                zone_dim = _find_dim(surface.dimensions, r"qr")
            elif "usps" in zone_id or "scan" in zone_id:
                zone_dim = _find_dim(surface.dimensions, r"usps|scan|warning")
            elif "envelope" in zone_id:
                zone_dim = _find_dim(surface.dimensions, r"envelope|window")

            if zone_dim and zone_size:
                if zone_size.get("width"):
                    results.append(_check(
                        page.slug, surface_label,
                        f"{zone_id} width",
                        zone_size["width"], zone_dim.width_in,
                        tolerance
                    ))
                if zone_size.get("height"):
                    results.append(_check(
                        page.slug, surface_label,
                        f"{zone_id} height",
                        zone_size["height"], zone_dim.height_in,
                        tolerance
                    ))

    return results


# --- Output ---

def print_dump(pages: list[ExtractedPage]) -> None:
    for page in pages:
        print(f"\n{'='*70}")
        print(f"  {page.page_name}  →  {page.slug}")
        print(f"{'='*70}")

        if page.header_dims:
            print(f"\n  Header dimensions:")
            for d in page.header_dims:
                print(f"    {d.label:20s} = {d.width_in:.4f}\" x {d.height_in:.4f}\"")

        for surface in page.surfaces:
            print(f"\n  {surface.label} ({surface.surface_id})")
            print(f"    Canvas: {surface.canvas_width_px:.0f}×{surface.canvas_height_px:.0f} px "
                  f"= {surface.canvas_width_in:.4f}\" × {surface.canvas_height_in:.4f}\"")

            if surface.dimensions:
                # Deduplicate by label+value
                seen = set()
                for d in surface.dimensions:
                    key = (d.label, d.width_in, d.height_in)
                    if key in seen:
                        continue
                    seen.add(key)
                    if d.height_in == 0:
                        print(f"    {d.label:25s} = {d.width_in:.4f}\"")
                    else:
                        print(f"    {d.label:25s} = {d.width_in:.4f}\" x {d.height_in:.4f}\"")
            else:
                print(f"    (no dimension labels extracted)")
    print()


def print_validate(all_results: list[ComparisonResult]) -> None:
    current_scaffold = None
    current_surface = None
    ok_count = warn_count = fail_count = error_count = 0

    for r in all_results:
        if r.scaffold != current_scaffold:
            current_scaffold = r.scaffold
            current_surface = None
            print(f"\n=== {r.scaffold} ===")
        if r.surface != current_surface:
            current_surface = r.surface
            print(f"  {r.surface}")

        if r.status == "OK":
            ok_count += 1
            print(f"    \033[32m[OK]\033[0m {r.check}: {r.actual:.4f}\" (expected {r.expected:.4f}\")")
        elif r.status == "WARN":
            warn_count += 1
            print(f"    \033[33m[WARN]\033[0m {r.check}: {r.actual:.4f}\" (expected {r.expected:.4f}\", diff: {r.diff:.4f}\")")
        elif r.status == "MISMATCH":
            fail_count += 1
            print(f"    \033[31m[MISMATCH]\033[0m {r.check}: {r.actual:.4f}\" (expected {r.expected:.4f}\", diff: {r.diff:.4f}\")")
        elif r.status == "ERROR":
            error_count += 1
            print(f"    \033[31m[ERROR]\033[0m {r.check}")

    total = ok_count + warn_count + fail_count + error_count
    print(f"\n{'='*70}")
    print(f"SUMMARY: {len(set(r.scaffold for r in all_results))} scaffolds, "
          f"{total} checks — "
          f"\033[32m{ok_count} OK\033[0m, "
          f"\033[33m{warn_count} warnings\033[0m, "
          f"\033[31m{fail_count} mismatches\033[0m"
          + (f", {error_count} errors" if error_count else ""))
    print(f"{'='*70}\n")


# --- Export ---

def export_all(pages: list[ExtractedPage], tolerance: float, outdir: Path) -> None:
    """Export extracted dimensions + validation results to JSON and Markdown."""
    outdir.mkdir(parents=True, exist_ok=True)

    # Build structured data per scaffold
    all_data = {}
    all_results = []
    for page in pages:
        results = compare_scaffold(page, tolerance)
        all_results.extend(results)

        scaffold_json = get_by_slug(page.slug)
        entry = {
            "slug": page.slug,
            "pageName": page.page_name,
            "figmaFileKey": "f5KZBEihbdL5D4oZdROVKD",
            "figmaNodeId": page.page_id,
            "extractedDimensions": {},
            "surfaces": [],
            "validation": {
                "checks": [],
                "status": "pass",
            },
        }

        # Header dims
        seen_header = set()
        for d in page.header_dims:
            key = (d.label, d.width_in, d.height_in)
            if key in seen_header or d.label in ("x", "a", "unlabeled"):
                continue
            seen_header.add(key)
            if d.height_in > 0:
                entry["extractedDimensions"][d.label] = {
                    "width": round(d.width_in, 4),
                    "height": round(d.height_in, 4),
                    "unit": "inches",
                }
            else:
                entry["extractedDimensions"][d.label] = {
                    "value": round(d.width_in, 4),
                    "unit": "inches",
                }

        # Surfaces
        for surface in page.surfaces:
            surf_data = {
                "id": surface.surface_id,
                "label": surface.label,
                "canvas": {
                    "widthPx": round(surface.canvas_width_px, 1),
                    "heightPx": round(surface.canvas_height_px, 1),
                    "widthIn": round(surface.canvas_width_in, 4),
                    "heightIn": round(surface.canvas_height_in, 4),
                },
                "extractedZones": {},
            }
            seen = set()
            for d in surface.dimensions:
                key = (d.label, d.width_in, d.height_in)
                if key in seen or d.label in ("x", "a", "unlabeled", "from", "on", "at", "around"):
                    continue
                seen.add(key)
                zone_key = d.label.replace(" ", "_").lower()
                if d.height_in > 0:
                    surf_data["extractedZones"][zone_key] = {
                        "width": round(d.width_in, 4),
                        "height": round(d.height_in, 4),
                        "unit": "inches",
                    }
                else:
                    surf_data["extractedZones"][zone_key] = {
                        "value": round(d.width_in, 4),
                        "unit": "inches",
                    }
            entry["surfaces"].append(surf_data)

        # Validation checks for this scaffold
        scaffold_results = [r for r in all_results if r.scaffold == page.slug]
        for r in scaffold_results:
            entry["validation"]["checks"].append({
                "surface": r.surface,
                "check": r.check,
                "expected": round(r.expected, 4),
                "actual": round(r.actual, 4),
                "diff": round(r.diff, 4),
                "status": r.status,
            })
        if any(r.status == "MISMATCH" for r in scaffold_results):
            entry["validation"]["status"] = "fail"
        elif any(r.status == "WARN" for r in scaffold_results):
            entry["validation"]["status"] = "warn"

        all_data[page.slug] = entry

    # Write JSON
    json_path = outdir / "figma-extraction-report.json"
    json_path.write_text(json.dumps(all_data, indent=2) + "\n")
    print(f"Wrote {json_path}")

    # Write validation summary JSON
    summary = {
        "totalScaffolds": len(pages),
        "totalChecks": len(all_results),
        "ok": sum(1 for r in all_results if r.status == "OK"),
        "warnings": sum(1 for r in all_results if r.status == "WARN"),
        "mismatches": sum(1 for r in all_results if r.status == "MISMATCH"),
        "tolerance": tolerance,
        "scaffolds": {slug: data["validation"]["status"] for slug, data in all_data.items()},
    }
    summary_path = outdir / "figma-validation-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"Wrote {summary_path}")

    # Write Markdown report
    md_path = outdir / "FIGMA_EXTRACTION_REPORT.md"
    md_lines = [
        "# Figma Scaffold Extraction & Validation Report",
        "",
        f"**Source Figma file:** `f5KZBEihbdL5D4oZdROVKD` — [Open in Figma](https://www.figma.com/design/f5KZBEihbdL5D4oZdROVKD)",
        f"**Scaffolds checked:** {len(pages)}",
        f"**Total validation checks:** {len(all_results)}",
        f"**Result:** {summary['ok']} OK, {summary['warnings']} warnings, {summary['mismatches']} mismatches",
        f"**Tolerance:** {tolerance}\" (~{tolerance * 96:.1f}px at 96dpi)",
        "",
        "---",
        "",
        "## How This Works",
        "",
        "1. All 14 Lob mailer scaffold HTML files are captured into a single Figma file",
        "2. The Figma MCP `get_metadata` tool extracts the full node tree (frames, text labels, positions, sizes)",
        "3. This script parses dimension values from text labels in the Figma capture (e.g., `\"Trim: 6\\\" x 4\\\"\"`)",
        "4. Extracted values are compared against the hand-authored JSON constraint files in `src/scaffolds/`",
        "5. The JSON files are the canonical source of truth; Figma is the visual verification",
        "",
        "## What Gets Validated",
        "",
        "| Check | Description |",
        "|-------|-------------|",
        "| File/Bleed dimensions | The full canvas size including bleed (e.g., 6.25\" x 4.25\") |",
        "| Trim dimensions | The final cut size (e.g., 6\" x 4\") |",
        "| Bleed inset | Distance from file edge to trim (0.125\" standard) |",
        "| Safe zone | Inset area where critical content must stay |",
        "| Canvas frame size | Pixel dimensions of the CSS surface div (÷96 = inches) |",
        "| Zone-specific sizes | Ink-free zones, address blocks, QR codes, envelope windows |",
        "",
        "---",
        "",
        "## Per-Scaffold Results",
        "",
    ]

    for slug, entry in all_data.items():
        status_emoji = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}[entry["validation"]["status"]]
        md_lines.append(f"### {slug} — {status_emoji}")
        md_lines.append("")

        # Header dimensions
        if entry["extractedDimensions"]:
            md_lines.append("**Extracted from Figma text labels:**")
            md_lines.append("")
            md_lines.append("| Label | Value |")
            md_lines.append("|-------|-------|")
            for label, val in entry["extractedDimensions"].items():
                if "width" in val:
                    md_lines.append(f"| {label} | {val['width']}\" x {val['height']}\" |")
                else:
                    md_lines.append(f"| {label} | {val['value']}\" |")
            md_lines.append("")

        # Surfaces
        for surf in entry["surfaces"]:
            md_lines.append(f"**{surf['label']} ({surf['id']})** — "
                          f"Canvas: {surf['canvas']['widthPx']:.0f} x {surf['canvas']['heightPx']:.0f} px "
                          f"= {surf['canvas']['widthIn']}\" x {surf['canvas']['heightIn']}\"")
            md_lines.append("")
            if surf["extractedZones"]:
                md_lines.append("| Zone | Dimensions |")
                md_lines.append("|------|------------|")
                for zone_name, val in surf["extractedZones"].items():
                    if "width" in val:
                        md_lines.append(f"| {zone_name} | {val['width']}\" x {val['height']}\" |")
                    else:
                        md_lines.append(f"| {zone_name} | {val['value']}\" |")
                md_lines.append("")

        # Validation checks
        checks = entry["validation"]["checks"]
        if checks:
            md_lines.append("**Validation:**")
            md_lines.append("")
            md_lines.append("| Check | Expected | Actual | Diff | Status |")
            md_lines.append("|-------|----------|--------|------|--------|")
            for c in checks:
                md_lines.append(f"| {c['check']} | {c['expected']}\" | {c['actual']}\" | {c['diff']}\" | {c['status']} |")
            md_lines.append("")

        md_lines.append("---")
        md_lines.append("")

    md_lines.extend([
        "## Files",
        "",
        "| File | Purpose |",
        "|------|---------|",
        "| `src/scaffolds/*.json` | Canonical JSON constraint files (14 total) |",
        "| `scaffolds/*.html` | HTML scaffold templates with zone overlays |",
        "| `scripts/validate_figma_zones.py` | This extraction + validation script |",
        "| `scripts/data/figma-metadata.txt` | Cached Figma metadata XML |",
        "| `docs/figma-extraction-report.json` | Full extracted data per scaffold |",
        "| `docs/figma-validation-summary.json` | Pass/fail summary |",
        "",
        "## Running",
        "",
        "```bash",
        "# Print extracted dimensions",
        "python3 scripts/validate_figma_zones.py dump",
        "",
        "# Cross-validate against JSON constraints",
        "python3 scripts/validate_figma_zones.py validate",
        "",
        "# Export JSON + Markdown reports",
        "python3 scripts/validate_figma_zones.py export",
        "```",
    ])

    md_path.write_text("\n".join(md_lines) + "\n")
    print(f"Wrote {md_path}")


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(description="Validate Figma scaffold zones against JSON constraints")
    sub = parser.add_subparsers(dest="command", required=True)

    meta_default = str(PROJECT_ROOT / "scripts" / "data" / "figma-metadata.txt")

    dump_p = sub.add_parser("dump", help="Extract and print all zone dimensions")
    dump_p.add_argument("--metadata", default=meta_default)

    val_p = sub.add_parser("validate", help="Cross-validate against JSON constraints")
    val_p.add_argument("--metadata", default=meta_default)
    val_p.add_argument("--tolerance", type=float, default=0.01)
    val_p.add_argument("--scaffold", type=str)

    export_p = sub.add_parser("export", help="Export extracted data + validation to JSON and Markdown")
    export_p.add_argument("--metadata", default=meta_default)
    export_p.add_argument("--tolerance", type=float, default=0.01)
    export_p.add_argument("--outdir", default=str(PROJECT_ROOT / "docs"))

    args = parser.parse_args()
    metadata_path = Path(args.metadata)
    if not metadata_path.exists():
        print(f"Error: Metadata file not found: {metadata_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading metadata from {metadata_path}...")
    raw = metadata_path.read_text()
    data = json.loads(raw)
    xml_text = data[0]["text"] if isinstance(data, list) else raw
    print(f"Parsing {len(xml_text):,} chars of XML...")
    pages = parse_metadata(xml_text)
    print(f"Found {len(pages)} scaffold pages.\n")

    if args.command == "dump":
        print_dump(pages)
    elif args.command == "validate":
        if args.scaffold:
            pages = [p for p in pages if p.slug == args.scaffold]
            if not pages:
                print(f"No page found for scaffold '{args.scaffold}'", file=sys.stderr)
                sys.exit(1)
        all_results = []
        for page in pages:
            all_results.extend(compare_scaffold(page, args.tolerance))
        print_validate(all_results)
        sys.exit(1 if any(r.status in ("MISMATCH", "ERROR") for r in all_results) else 0)
    elif args.command == "export":
        export_all(pages, args.tolerance, Path(args.outdir))


if __name__ == "__main__":
    main()
