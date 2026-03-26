# Figma Scaffold Extraction & Validation Report

**Source Figma file:** `f5KZBEihbdL5D4oZdROVKD` — [Open in Figma](https://www.figma.com/design/f5KZBEihbdL5D4oZdROVKD)
**Scaffolds checked:** 14
**Total validation checks:** 94
**Result:** 94 OK, 0 warnings, 0 mismatches
**Tolerance:** 0.01" (~1.0px at 96dpi)

---

## How This Works

1. All 14 Lob mailer scaffold HTML files are captured into a single Figma file
2. The Figma MCP `get_metadata` tool extracts the full node tree (frames, text labels, positions, sizes)
3. This script parses dimension values from text labels in the Figma capture (e.g., `"Trim: 6\" x 4\""`)
4. Extracted values are compared against the hand-authored JSON constraint files in `src/scaffolds/`
5. The JSON files are the canonical source of truth; Figma is the visual verification

## What Gets Validated

| Check | Description |
|-------|-------------|
| File/Bleed dimensions | The full canvas size including bleed (e.g., 6.25" x 4.25") |
| Trim dimensions | The final cut size (e.g., 6" x 4") |
| Bleed inset | Distance from file edge to trim (0.125" standard) |
| Safe zone | Inset area where critical content must stay |
| Canvas frame size | Pixel dimensions of the CSS surface div (÷96 = inches) |
| Zone-specific sizes | Ink-free zones, address blocks, QR codes, envelope windows |

---

## Per-Scaffold Results

### postcard-4x6 — PASS

**Extracted from Figma text labels:**

| Label | Value |
|-------|-------|
| Trim | 6.0" x 4.0" |
| File with bleed | 4.25" x 6.25" |
| File | 6.25" x 4.25" |

**Front (front)** — Canvas: 600 x 408 px = 6.25" x 4.2499"

| Zone | Dimensions |
|------|------------|
| file | 6.25" x 4.25" |
| trim | 6.0" x 4.0" |
| bleed | 0.125" |
| trim_line | 6.0" x 4.0" |
| safe_zone | 0.0625" |
| safe | 5.875" |
| inset | 0.0625" |

**Back (back)** — Canvas: 600 x 408 px = 6.25" x 4.2499"

| Zone | Dimensions |
|------|------------|
| free_zone | 3.2835" x 2.375" |
| bleed | 0.125" |
| trim_line | 6.0" x 4.0" |
| safe_zone | 0.0625" |
| safe | 5.875" |
| inset | 0.0625" |

**Validation:**

| Check | Expected | Actual | Diff | Status |
|-------|----------|--------|------|--------|
| File width | 6.25" | 6.25" | 0.0" | OK |
| File height | 4.25" | 4.25" | 0.0" | OK |
| Bleed inset | 0.125" | 0.125" | 0.0" | OK |
| Trim width | 6" | 6.0" | 0.0" | OK |
| Trim height | 4" | 4.0" | 0.0" | OK |
| Safe width | 5.875" | 5.875" | 0.0" | OK |
| Safe height | 3.875" | 3.875" | 0.0" | OK |
| Canvas width | 6.25" | 6.25" | 0.0" | OK |
| Canvas height | 4.25" | 4.2499" | 0.0001" | OK |
| Canvas width | 6.25" | 6.25" | 0.0" | OK |
| Canvas height | 4.25" | 4.2499" | 0.0001" | OK |

---

### postcard-5x7 — PASS

**Extracted from Figma text labels:**

| Label | Value |
|-------|-------|
| Trim | 7.0" x 5.0" |
| File with bleed | 5.25" x 7.25" |
| File | 7.25" x 5.25" |

**Front (front)** — Canvas: 696 x 504 px = 7.25" x 5.2499"

| Zone | Dimensions |
|------|------------|
| file | 7.25" x 5.25" |
| trim | 7.0" x 5.0" |
| bleed | 0.125" |
| trim_line | 7.0" x 5.0" |
| safe_zone | 0.0625" |
| safe | 6.875" |
| inset | 0.0625" |

**Back (back)** — Canvas: 696 x 504 px = 7.25" x 5.2499"

| Zone | Dimensions |
|------|------------|
| free_zone | 4.0" x 2.375" |
| bleed | 0.125" |
| trim_line | 7.0" x 5.0" |
| safe_zone | 0.0625" |
| safe | 6.875" |
| inset | 0.0625" |

**Validation:**

| Check | Expected | Actual | Diff | Status |
|-------|----------|--------|------|--------|
| File width | 7.25" | 7.25" | 0.0" | OK |
| File height | 5.25" | 5.25" | 0.0" | OK |
| Bleed inset | 0.125" | 0.125" | 0.0" | OK |
| Trim width | 7" | 7.0" | 0.0" | OK |
| Trim height | 5" | 5.0" | 0.0" | OK |
| Safe width | 6.875" | 6.875" | 0.0" | OK |
| Safe height | 4.875" | 4.875" | 0.0" | OK |
| Canvas width | 7.25" | 7.25" | 0.0" | OK |
| Canvas height | 5.25" | 5.2499" | 0.0001" | OK |
| Canvas width | 7.25" | 7.25" | 0.0" | OK |
| Canvas height | 5.25" | 5.2499" | 0.0001" | OK |

---

### postcard-6x9 — PASS

**Extracted from Figma text labels:**

| Label | Value |
|-------|-------|
| Trim | 9.0" x 6.0" |
| File with bleed | 6.25" x 9.25" |
| File | 9.25" x 6.25" |

**Front (front)** — Canvas: 888 x 600 px = 9.2499" x 6.25"

| Zone | Dimensions |
|------|------------|
| file | 9.25" x 6.25" |
| trim | 9.0" x 6.0" |
| bleed | 0.125" |
| trim_line | 9.0" x 6.0" |
| safe_zone | 0.0625" |
| safe | 8.875" |
| inset | 0.0625" |

**Back (back)** — Canvas: 888 x 600 px = 9.2499" x 6.25"

| Zone | Dimensions |
|------|------------|
| free_zone | 4.0" x 2.375" |
| bleed | 0.125" |
| trim_line | 9.0" x 6.0" |
| safe_zone | 0.0625" |
| safe | 8.875" |
| inset | 0.0625" |

**Validation:**

| Check | Expected | Actual | Diff | Status |
|-------|----------|--------|------|--------|
| File width | 9.25" | 9.25" | 0.0" | OK |
| File height | 6.25" | 6.25" | 0.0" | OK |
| Bleed inset | 0.125" | 0.125" | 0.0" | OK |
| Trim width | 9" | 9.0" | 0.0" | OK |
| Trim height | 6" | 6.0" | 0.0" | OK |
| Safe width | 8.875" | 8.875" | 0.0" | OK |
| Safe height | 5.875" | 5.875" | 0.0" | OK |
| Canvas width | 9.25" | 9.2499" | 0.0001" | OK |
| Canvas height | 6.25" | 6.25" | 0.0" | OK |
| Canvas width | 9.25" | 9.2499" | 0.0001" | OK |
| Canvas height | 6.25" | 6.25" | 0.0" | OK |

---

### postcard-6x11 — PASS

**Extracted from Figma text labels:**

| Label | Value |
|-------|-------|
| Trim | 11.0" x 6.0" |
| File with bleed | 6.25" x 11.25" |
| File | 11.25" x 6.25" |

**Front (front)** — Canvas: 1080 x 600 px = 11.25" x 6.25"

| Zone | Dimensions |
|------|------------|
| file | 11.25" x 6.25" |
| trim | 11.0" x 6.0" |
| bleed | 0.125" |
| trim_line | 11.0" x 6.0" |
| safe_zone | 0.0625" |
| safe | 10.875" |
| inset | 0.0625" |

**Back (back)** — Canvas: 1080 x 600 px = 11.25" x 6.25"

| Zone | Dimensions |
|------|------------|
| free_zone | 4.0" x 2.375" |
| bleed | 0.125" |
| trim_line | 11.0" x 6.0" |
| safe_zone | 0.0625" |
| safe | 10.875" |
| inset | 0.0625" |

**Validation:**

| Check | Expected | Actual | Diff | Status |
|-------|----------|--------|------|--------|
| File width | 11.25" | 11.25" | 0.0" | OK |
| File height | 6.25" | 6.25" | 0.0" | OK |
| Bleed inset | 0.125" | 0.125" | 0.0" | OK |
| Trim width | 11" | 11.0" | 0.0" | OK |
| Trim height | 6" | 6.0" | 0.0" | OK |
| Safe width | 10.875" | 10.875" | 0.0" | OK |
| Safe height | 5.875" | 5.875" | 0.0" | OK |
| Canvas width | 11.25" | 11.25" | 0.0" | OK |
| Canvas height | 6.25" | 6.25" | 0.0" | OK |
| Canvas width | 11.25" | 11.25" | 0.0" | OK |
| Canvas height | 6.25" | 6.25" | 0.0" | OK |

---

### letter-8.5x11 — PASS

**Extracted from Figma text labels:**

| Label | Value |
|-------|-------|
| Page | 8.5" x 11.0" |
| Address block | 3.15" x 2.0" |
| QR zone | 0.5" x 0.5" |

**Page 1 (page1)** — Canvas: 816 x 1056 px = 8.5" x 11.0"

| Zone | Dimensions |
|------|------------|
| address_block | 3.15" x 2.0" |
| qr_zone | 0.5" x 0.5" |
| sequence_id | 1.45" |
| page_edge | 8.5" x 11.0" |

**Validation:**

| Check | Expected | Actual | Diff | Status |
|-------|----------|--------|------|--------|
| Canvas width | 8.5" | 8.5" | 0.0" | OK |
| Canvas height | 11" | 11.0" | 0.0" | OK |
| address-block width | 3.15" | 3.15" | 0.0" | OK |
| address-block height | 2" | 2.0" | 0.0" | OK |
| qr-code-zone width | 0.5" | 0.5" | 0.0" | OK |
| qr-code-zone height | 0.5" | 0.5" | 0.0" | OK |

---

### letter-8.5x14 — PASS

**Extracted from Figma text labels:**

| Label | Value |
|-------|-------|
| Page | 8.5" x 14.0" |

**Page 1 (page1)** — Canvas: 816 x 1344 px = 8.5" x 13.9999"

| Zone | Dimensions |
|------|------------|
| and | 3.75" |
| page_edge | 8.5" x 14.0" |
| fold_line_1 | 3.75" |
| fold_line_2 | 7.0" |

**Validation:**

| Check | Expected | Actual | Diff | Status |
|-------|----------|--------|------|--------|
| Canvas width | 8.5" | 8.5" | 0.0" | OK |
| Canvas height | 14" | 13.9999" | 0.0001" | OK |

---

### card-affix — PASS

**All (all)** — Canvas: 1158 x 360 px = 12.0602" x 3.751"

| Zone | Dimensions |
|------|------------|
| vertical_orientation | 2.125" |
| safe_zone | 1.875" x 3.125" |
| safe | 3.125" |

**All (all)** — Canvas: 1158 x 240 px = 12.0602" x 2.501"

| Zone | Dimensions |
|------|------------|
| horizontal_orientation | 3.375" |
| safe_zone | 3.125" x 1.875" |
| safe | 1.875" |

---

### selfmailer-6x18-bifold — PASS

**Extracted from Figma text labels:**

| Label | Value |
|-------|-------|
| Unfolded | 6.0" x 18.0" |
| horizontally | 6.0" x 9.0" |
| free | 4.0" x 2.375" |
| on left panel | 4.0" x 2.375" |

**Outside (outside)** — Canvas: 1752 x 600 px = 18.25" x 6.25"

| Zone | Dimensions |
|------|------------|
| free | 4.0" x 2.375" |
| on_left_panel | 4.0" x 2.375" |
| bleed | 0.125" |
| trim | 6.0" x 18.0" |

**Inside (inside)** — Canvas: 1752 x 600 px = 18.25" x 6.25"

| Zone | Dimensions |
|------|------------|
| bleed | 0.125" |
| trim | 6.0" x 18.0" |

**Validation:**

| Check | Expected | Actual | Diff | Status |
|-------|----------|--------|------|--------|
| Bleed inset | 0.125" | 0.125" | 0.0" | OK |
| Trim width | 18" | 18.0" | 0.0" | OK |
| Trim height | 6" | 6.0" | 0.0" | OK |
| Canvas width | 18.25" | 18.25" | 0.0" | OK |
| Canvas height | 6.25" | 6.25" | 0.0" | OK |
| Canvas width | 18.25" | 18.25" | 0.0" | OK |
| Canvas height | 6.25" | 6.25" | 0.0" | OK |

---

### selfmailer-12x9-bifold — PASS

**Extracted from Figma text labels:**

| Label | Value |
|-------|-------|
| Unfolded | 12.0" x 9.0" |
| free | 4.0" x 2.375" |
| on top panel | 4.0" x 2.375" |

**Outside (outside)** — Canvas: 888 x 1176 px = 9.2499" x 12.25"

| Zone | Dimensions |
|------|------------|
| free | 4.0" x 2.375" |
| on_top_panel | 4.0" x 2.375" |
| bleed | 0.125" |
| trim | 12.0" x 9.0" |

**Inside (inside)** — Canvas: 888 x 1176 px = 9.2499" x 12.25"

| Zone | Dimensions |
|------|------------|
| bleed | 0.125" |
| trim | 12.0" x 9.0" |

**Validation:**

| Check | Expected | Actual | Diff | Status |
|-------|----------|--------|------|--------|
| Bleed inset | 0.125" | 0.125" | 0.0" | OK |
| Trim width | 9" | 9.0" | 0.0" | OK |
| Trim height | 12" | 12.0" | 0.0" | OK |
| Canvas width | 9.25" | 9.2499" | 0.0001" | OK |
| Canvas height | 12.25" | 12.25" | 0.0" | OK |
| Canvas width | 9.25" | 9.2499" | 0.0001" | OK |
| Canvas height | 12.25" | 12.25" | 0.0" | OK |

---

### selfmailer-11x9-bifold — PASS

**Extracted from Figma text labels:**

| Label | Value |
|-------|-------|
| Unfolded | 11.0" x 9.0" |

**Outside (outside)** — Canvas: 888 x 1080 px = 9.2499" x 11.25"

| Zone | Dimensions |
|------|------------|
| offset | 1.0" |
| bleed | 0.125" |
| trim | 11.0" x 9.0" |
| fold | 1.0" |

**Inside (inside)** — Canvas: 888 x 1080 px = 9.2499" x 11.25"

| Zone | Dimensions |
|------|------------|
| bleed | 0.125" |
| trim | 11.0" x 9.0" |

**Validation:**

| Check | Expected | Actual | Diff | Status |
|-------|----------|--------|------|--------|
| Bleed inset | 0.125" | 0.125" | 0.0" | OK |
| Trim width | 9" | 9.0" | 0.0" | OK |
| Trim height | 11" | 11.0" | 0.0" | OK |
| Canvas width | 9.25" | 9.2499" | 0.0001" | OK |
| Canvas height | 11.25" | 11.25" | 0.0" | OK |
| Canvas width | 9.25" | 9.2499" | 0.0001" | OK |
| Canvas height | 11.25" | 11.25" | 0.0" | OK |

---

### selfmailer-17.75x9-trifold — PASS

**Extracted from Figma text labels:**

| Label | Value |
|-------|-------|
| Unfolded | 17.75" x 9.0" |

**Outside (outside)** — Canvas: 888 x 1728 px = 9.2499" x 17.9999"

| Zone | Dimensions |
|------|------------|
| score | 12.0" |
| offset | 0.25" |
| glue_zone | 9.0" x 0.5" |
| bleed | 0.125" |
| trim | 17.75" x 9.0" |

**Inside (inside)** — Canvas: 888 x 1728 px = 9.2499" x 17.9999"

| Zone | Dimensions |
|------|------------|
| bleed | 0.125" |
| trim | 17.75" x 9.0" |

**Validation:**

| Check | Expected | Actual | Diff | Status |
|-------|----------|--------|------|--------|
| Bleed inset | 0.125" | 0.125" | 0.0" | OK |
| Trim width | 9" | 9.0" | 0.0" | OK |
| Trim height | 17.75" | 17.75" | 0.0" | OK |
| Canvas width | 9.25" | 9.2499" | 0.0001" | OK |
| Canvas height | 18" | 17.9999" | 0.0001" | OK |
| Canvas width | 9.25" | 9.2499" | 0.0001" | OK |
| Canvas height | 18" | 17.9999" | 0.0001" | OK |

---

### snappack-8.5x11 — PASS

**Extracted from Figma text labels:**

| Label | Value |
|-------|-------|
| Final Trim | 8.5" x 11.0" |
| Folded | 8.5" x 5.5" |

**Outside (outside)** — Canvas: 816 x 1056 px = 8.5" x 11.0"

| Zone | Dimensions |
|------|------------|
| 816px_x_1056px | 8.5" |
| no-print_area | 0.5" |
| perf | 7.5" x 10.0" |
| safe | 7.25" x 9.75" |

**Inside (inside)** — Canvas: 816 x 1056 px = 8.5" x 11.0"

| Zone | Dimensions |
|------|------------|
| 816px_x_1056px | 8.5" |
| no-print_area | 0.5" |
| perf | 7.5" x 10.0" |
| safe | 7.25" x 9.75" |

**Validation:**

| Check | Expected | Actual | Diff | Status |
|-------|----------|--------|------|--------|
| Safe width | 7.25" | 7.25" | 0.0" | OK |
| Safe height | 9.75" | 9.75" | 0.0" | OK |
| Canvas width | 8.5" | 8.5" | 0.0" | OK |
| Canvas height | 11" | 11.0" | 0.0" | OK |
| Canvas width | 8.5" | 8.5" | 0.0" | OK |
| Canvas height | 11" | 11.0" | 0.0" | OK |

---

### booklet-8.375x5.375 — PASS

**Extracted from Figma text labels:**

| Label | Value |
|-------|-------|
| Page | 8.375" x 5.375" |

**Front (front)** — Canvas: 804 x 516 px = 8.3749" x 5.375"

**Validation:**

| Check | Expected | Actual | Diff | Status |
|-------|----------|--------|------|--------|
| Canvas width | 8.375" | 8.3749" | 0.0001" | OK |
| Canvas height | 5.375" | 5.375" | 0.0" | OK |

---

### buckslip — PASS

**Extracted from Figma text labels:**

| Label | Value |
|-------|-------|
| Bleed | 8.75" x 3.75" |
| Trim | 8.5" x 3.5" |

**Front (front)** — Canvas: 840 x 360 px = 8.75" x 3.75"

**Back (back)** — Canvas: 840 x 360 px = 8.75" x 3.75"

**Validation:**

| Check | Expected | Actual | Diff | Status |
|-------|----------|--------|------|--------|
| File width | 8.75" | 8.75" | 0.0" | OK |
| File height | 3.75" | 3.75" | 0.0" | OK |
| Canvas width | 8.75" | 8.75" | 0.0" | OK |
| Canvas height | 3.75" | 3.75" | 0.0" | OK |
| Canvas width | 8.75" | 8.75" | 0.0" | OK |
| Canvas height | 3.75" | 3.75" | 0.0" | OK |

---

## Files

| File | Purpose |
|------|---------|
| `src/scaffolds/*.json` | Canonical JSON constraint files (14 total) |
| `scaffolds/*.html` | HTML scaffold templates with zone overlays |
| `scripts/validate_figma_zones.py` | This extraction + validation script |
| `scripts/data/figma-metadata.txt` | Cached Figma metadata XML |
| `docs/figma-extraction-report.json` | Full extracted data per scaffold |
| `docs/figma-validation-summary.json` | Pass/fail summary |

## Running

```bash
# Print extracted dimensions
python3 scripts/validate_figma_zones.py dump

# Cross-validate against JSON constraints
python3 scripts/validate_figma_zones.py validate

# Export JSON + Markdown reports
python3 scripts/validate_figma_zones.py export
```
