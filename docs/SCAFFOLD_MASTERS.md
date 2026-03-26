# Scaffold Masters — Physical Mail Template System

**Purpose:** This document describes the base scaffold master templates created for every Lob mailer type and size. These scaffolds live in Figma as canonical "never touch" references — every design iteration starts by cloning a scaffold. They encode all physical printing constraints (zones, folds, bleeds, etc.) so designers never have to guess what's safe to design on.

---

## Architecture Overview

```
HTML Scaffold (local)
    ↓  Figma MCP capture
Figma Base Scaffold (canonical, locked)
    ↓  clone per design iteration
Figma Design Variant (editable)
    ↓  creative-engine-x-api
Lob Template (HTML/PDF with {{merge_vars}})
    ↓  campaign-engine-x / outbound-engine-x
Lob Render + Print → Physical Mail
```

- **creative-engine-x-api** owns template creation, management, and preview via Figma
- **campaign-engine-x / outbound-engine-x** injects content and merge variables, orchestrates campaigns
- **Lob** receives final templates + merge data, renders, prints, and mails

Each scaffold is an HTML file in `scaffolds/` with color-coded zone overlays. The Figma capture script (`https://mcp.figma.com/mcp/html-to-design/capture.js`) converts these into Figma frames when opened via the capture hash URL workflow.

---

## Figma Files

| Figma File | File Key | Scaffolds |
|---|---|---|
| [CEX] Postcards - Base Scaffolds | `SMoEklS7SoNgukwFUMw6SU` | 4x6, 5x7, 6x9, 6x11 |
| [CEX] Letters - Base Scaffolds | `WS8RDic5GCof4sPPyRykax` | 8.5x11 (standard), 8.5x14 (legal) |
| [CEX] Self-Mailers - Base Scaffolds | `lDuFGZUZiHzx3R7LPehW0O` | 6x18 bifold, 12x9 bifold, 11x9 bifold, 17.75x9 trifold |
| [CEX] Snap Packs - Base Scaffolds | `JYVeNFPdnzX8PqNfuwJSwK` | 8.5x11 |
| [CEX] Booklets - Base Scaffolds | `RvO5pI8G5IykFL6pQQJNU1` | 8.375x5.375 (digest) |
| [CEX] Letter Add-ons - Base Scaffolds | `813wa8IuLYf0kleraFSGju` | Buckslip 8.75x3.75, Card Affix (vertical + horizontal) |

---

## Local Scaffold Files

```
scaffolds/
├── postcard-4x6.html
├── postcard-5x7.html
├── postcard-6x9.html
├── postcard-6x11.html
├── letter-8.5x11.html
├── letter-8.5x14.html
├── selfmailer-6x18-bifold.html
├── selfmailer-12x9-bifold.html
├── selfmailer-11x9-bifold.html
├── selfmailer-17.75x9-trifold.html
├── snappack-8.5x11.html
├── booklet-8.375x5.375.html
├── buckslip.html
└── card-affix.html
```

---

## Physical Mail Zone Reference

This is the core knowledge for designing anything that gets physically printed and mailed. Every zone exists because of a physical printing or USPS postal regulation constraint. Violating these causes rejected mail, misprints, or wasted budget.

### Zone Types

#### 1. Bleed Zone
- **What:** The area beyond the trim edge that gets cut off after printing
- **Why it exists:** Printers can't print exactly to the edge. You extend your design 1/8" past the trim line so that when the blade cuts, there's no white edge showing
- **Size:** 0.125" (1/8") on all sides
- **Rule:** File dimensions INCLUDE bleed. A "4x6 postcard" is actually submitted as 4.25" x 6.25"
- **Design implication:** Extend background colors/images into the bleed, but never put text or critical content there — it gets cut off
- **Exception:** Letters have NO bleed. They use 1/16" clear space instead (no edge-to-edge printing)
- **Exception:** Buckslips DO have bleed (8.75" x 3.75" bleed, trimmed to 8.5" x 3.5")
- **Exception:** Card affix has NO bleed (edge-to-edge within trim, 1/8" rounded corners)
- **Exception:** Snap packs are NO-BLEED with a 0.5" no-print border instead

#### 2. Trim Line
- **What:** The actual cut line — the final edge of the printed piece
- **Why it exists:** This is where the paper gets physically cut after printing
- **Size:** 0.125" inset from file edge (i.e., the bleed boundary)
- **Design implication:** This is the "real" edge of your piece. Everything outside this gets cut. Everything inside is what the recipient sees

#### 3. Safe Zone
- **What:** The inner margin where critical content (text, logos, CTAs) must stay
- **Size varies by format:**
  - **Postcards:** 0.0625" (1/16") inset from trim (e.g., 4x6 safe zone = 3.875" x 5.875")
  - **Self-mailers:** 0.125" (1/8") inset from trim
  - **Buckslips:** 0.125" (1/8") inset from trim
  - **Snap packs:** 0.125" inset from perf line (not from file edge)
  - **Card affix:** 0.125" inset from trim
- **Why it exists:** Cutting machines have slight variance (1-2mm). Text right at the trim line might get clipped on some prints. The safe zone accounts for this tolerance
- **Design implication:** ALL text, logos, and important visual elements must be inside the safe zone. Background images can extend through safe zone into bleed

#### 4. Ink-Free Zone (Address + Postage)
- **What:** A reserved rectangle on the address side where NO ink/design can appear
- **Why it exists:** USPS requires a clear area for the printed recipient address and postage indicia. Ink in this area causes OCR read failures and mail rejection
- **Size varies by format:**
  - **4x6 postcards:** 3.2835" x 2.375" (smaller card = smaller zone)
  - **All other postcards (5x7, 6x9, 6x11):** 4" x 2.375"
  - **Self-mailers:** 4" x 2.375"
  - **Snap packs (outside):** 4" x 2.375"
- **Position:** Bottom-right of the address side, typically 0.275" from right edge and 0.25" from bottom (postcards), or 0.15" from fold and 0.25" from edge (self-mailers)
- **Design implication:** This zone is completely hands-off. No background images, no color, no watermarks — pure white only

#### 5. USPS Scan Warning Zone (Postcards — Front Only)
- **What:** The bottom 2.375" of the FRONT of a postcard
- **Why it exists:** USPS automated sorting machines scan the bottom portion of both sides looking for an address. If the front has address-like text (street names, city/state, zip codes) in this zone, the machine may misread it as the address side and route the mail incorrectly
- **Design implication:** Avoid any address-like text in the bottom 2.375" of the front. Images, logos, marketing copy — all fine. Just not text that looks like an address

#### 6. Fold Lines
- **What:** Dashed lines indicating where the paper physically folds
- **Why they exist:** Self-mailers and snap packs are printed flat and then machine-folded
- **Applies to:**
  - **Bifold self-mailers:** Single center fold (6x18: horizontal fold at 9"; 12x9: vertical fold at 6"; 11x9: vertical fold with 1" offset)
  - **Trifold self-mailer (17.75x9):** Two fold lines — fold 1 at ~6" and fold 2 (score) at 12", creating three panels via C-fold
  - **Snap packs:** Center fold at 5.5" on the inside (8.5x11 folds to 8.5x5.5)
- **Design implication:** Don't place critical text or elements directly on a fold line — they'll be distorted. Design each panel as its own composition. Account for the slight paper distortion at the fold crease

#### 7. Glue Zone (All Self-Mailers)
- **What:** An area where adhesive is applied to seal the mailer for delivery
- **Trifold (17.75x9):** 9" wide x 0.5" tall strip at the 12" score line
- **Bifolds:** Glue zone on inside surface along one edge (varies by format — right edge for 6x18, top edge for 12x9, bottom for 11x9)
- **Why it exists:** Self-mailers must be sealed to meet USPS mailing requirements
- **Design implication:** Content under the glue may be obscured or damaged when opened. Artwork CAN be placed in the glue zone, but avoid critical content. On the 11x9 bifold, the area below the glue zone (1" strip) is visible when closed and can be used for attention-grabbing creative

#### 8. Panel Offset (Some Self-Mailers)
- **What:** One panel is intentionally shorter than the other(s)
- **Why it exists:** When folded, the inner panel needs to be slightly shorter so it doesn't stick out or cause paper jams in automated equipment
- **Applies to:**
  - **11x9 bifold:** 1" offset (top panel = 6", bottom panel = 5")
  - **17.75x9 trifold:** 0.25" offset on bottom panel (~5.75" vs ~6" for other panels)
- **Design implication:** The shorter panel has less usable design space. Don't design to the full unfolded dimension — account for the offset

#### 9. Perforated Edges (Snap Packs)
- **What:** The left and right sides of a snap pack are perforated so recipients can tear it open
- **Why it exists:** Snap packs are pressure-sealed mailers. The perforation is the "opening mechanism" — recipients tear along the sides to access the interior
- **Design implication:** Don't place critical content right at the perforation line. Content may be slightly torn or obscured during opening. The interior is HIPAA-compliant (sealed until opened)

#### 10. Address Block (Letters)
- **What:** A fixed rectangle on page 1 where Lob prints the recipient address
- **Size:** 3.15" x 2", positioned 0.6" from left edge and 0.84" from top
- **Why it exists:** Letters go in #10 double-window envelopes. The address block must align with the envelope window so the recipient's address shows through. This position is standardized
- **Design implication:** You cannot put any design content in this rectangle on page 1. The address is printed by Lob, not by your template

#### 11. Envelope Windows (Letters)
- **What:** Two areas on page 1 that are visible through the #10 double-window envelope
- **Top window (return address):** 3.25"W x 0.875"H, placed 0.63" from left edge and 0.5" from top edge
- **Bottom window (recipient address):** 4"W x 1"H, placed 0.63" from left edge and 1.71" from top edge
- **Why they exist:** The #10 double-window envelope has two die-cut windows. The top shows the sender/return address, the bottom shows the recipient address (which overlaps with the address block)
- **Design implication:** Content in these rectangles will be visible through the envelope. Place your logo/return address in the top window area. The bottom window aligns with the address block

#### 12. QR Code Zone (Letters)
- **What:** A white box in the bottom-left corner of each page containing a 2D barcode
- **White box:** 0.5" x 0.5", placed 0.087" from left and bottom edges
- **Barcode:** 0.2" x 0.2", centered inside the white box
- **Why it exists:** Lob prints a QR code here for quality control and mail piece tracking during production. The white box ensures barcode readability regardless of background
- **Design implication:** Don't design into this corner. Lob will print a white box with a QR code on every page that has content

#### 13. Sequence ID Zone (Letters)
- **What:** A thin horizontal strip for a machine-readable sequence identifier
- **Size:** 1.45" x 0.09", positioned 0.3" from left and 2.2375" from bottom
- **Why it exists:** Production tracking — helps Lob match pages to mail pieces during collation
- **Design implication:** Avoid this area. It's small and easy to overlook but will be overprinted

#### 14. Spine (Booklets)
- **What:** The binding edge of a saddle-stitched booklet
- **Why it exists:** Pages are stapled along this edge. Content too close to the spine will be hidden in the binding gutter
- **Design implication:** Keep text and critical elements at least 0.25" from the spine edge. Images can extend to the spine but expect some to be lost in the fold

#### 15. Clear Space (Letters — Instead of Bleed)
- **What:** A 1/16" (0.0625") margin around all edges where no content can appear
- **Why it exists:** Letters are NOT edge-to-edge printed. The printing process for letter pages leaves a small unprinted border
- **Size:** 0.0625" on all sides
- **Design implication:** Letters cannot have full-bleed backgrounds or edge-to-edge color. Always design with a white border in mind

---

## Zone Summary by Mailer Type

| Zone | Postcards | Self-Mailers | Letters | Snap Packs | Booklets | Buckslips | Card Affix |
|------|-----------|-------------|---------|------------|----------|-----------|------------|
| Bleed (0.125") | Yes | Yes | **No** | **No** | Yes | Yes | No |
| No-Print Border | N/A | N/A | 1/16" clear | **0.5"** | N/A | N/A | N/A |
| Trim Line | Yes | Yes | N/A | Yes | Yes | Yes | Yes |
| Safe Zone | Yes (1/16") | Yes (1/8") | N/A | Yes (1/8" from perf) | Yes | Yes (1/8") | Yes (1/8") |
| Ink-Free Zone | Back only | Outside only | N/A | Outside only | N/A | N/A | N/A |
| USPS Scan Warning | Front only | N/A | N/A | N/A | N/A | N/A | N/A |
| Fold Lines | N/A | Yes | N/A | Yes | N/A | N/A | N/A |
| Glue Zone | N/A | All (inside) | N/A | N/A | N/A | N/A | N/A |
| Panel Offset | N/A | 11x9, 17.75x9 | N/A | N/A | N/A | N/A | N/A |
| Perforated Edges | N/A | N/A | N/A | Yes (sides) | N/A | N/A | N/A |
| Address Block | N/A | N/A | Page 1 | N/A | N/A | N/A | N/A |
| QR Code Zone | N/A | N/A | Every page | N/A | N/A | N/A | N/A |
| Sequence ID | N/A | N/A | Every page | N/A | N/A | N/A | N/A |
| Clear Space (1/16") | N/A | N/A | Yes | N/A | N/A | N/A | N/A |
| Spine | N/A | N/A | N/A | N/A | Yes | N/A | N/A |

---

## Scaffold Details by Mailer Type

### Postcards (All Plans)

| Size | Trim | File w/ Bleed | Ink-Free Size | Surfaces | Scaffold File |
|------|------|---------------|---------------|----------|---------------|
| 4x6 | 4" x 6" | 4.25" x 6.25" | 3.2835" x 2.375" | Front + Back | `postcard-4x6.html` |
| 5x7 | 5" x 7" | 5.25" x 7.25" | 4" x 2.375" | Front + Back | `postcard-5x7.html` |
| 6x9 | 6" x 9" | 6.25" x 9.25" | 4" x 2.375" | Front + Back | `postcard-6x9.html` |
| 6x11 | 6" x 11" | 6.25" x 11.25" | 4" x 2.375" | Front + Back | `postcard-6x11.html` |

**Key rules:**
- Front: Fully customizable. Avoid address-like text in bottom 2.375" (USPS scan zone)
- Back: Design around the ink-free zone (bottom-right). The rest is customizable
- 4x6 is the only size that can go international
- 6x9 is the most popular (balance of visibility and cost)
- Merge variables (`{{var}}`) supported on all sizes

### Letters (Standard: All Plans / Legal: Enterprise)

| Size | Page | Envelope | Sheets | Scaffold File |
|------|------|----------|--------|---------------|
| 8.5x11 | 8.5" x 11" | #10 double-window (1-6 sheets), flat (7-60) | 1-60 | `letter-8.5x11.html` |
| 8.5x14 | 8.5" x 14" | #10 (folded, double parallel fold) | 1-3 max | `letter-8.5x14.html` |

**Key rules:**
- NO bleed / NO edge-to-edge printing — 1/16" clear space on all sides
- Page 1 has reserved zones: address block (3.15" x 2"), envelope windows (top: 3.25"x0.875", bottom: 4"x1"), QR code (0.5" x 0.5" white box at 0.087" from edges), sequence ID
- Every page with content gets a QR code (bottom-left) and sequence ID
- Legal letters fold with a double parallel fold to fit #10 envelope
- Merge variables supported; B&W or color; single or double-sided
- Over 6 sheets incurs extra postage (flat envelope)

### Self-Mailers (Enterprise Only)

All fold down to a 6" x 9" finished size.

| Size | Fold Type | Panels | Offset | File w/ Bleed | Scaffold File |
|------|-----------|--------|--------|---------------|---------------|
| 6x18 | Horizontal bifold | 2 | None | 6.25" x 18.25" | `selfmailer-6x18-bifold.html` |
| 12x9 | Vertical bifold | 2 | None | 12.25" x 9.25" | `selfmailer-12x9-bifold.html` |
| 11x9 | Vertical bifold | 2 | 1" (top=6", bottom=5") | 11.25" x 9.25" | `selfmailer-11x9-bifold.html` |
| 17.75x9 | C-fold (trifold) | 3 | 0.25" on bottom panel | 18" x 9.25" | `selfmailer-17.75x9-trifold.html` |

**Key rules:**
- Outside surface: Must have ink-free zone (4" x 2.375") for address/postage
- Inside surface: Fully customizable
- Ink-free zone position: 0.15" from fold, 0.25" from edge
- Trifold has a glue zone (9" x 0.5") at the 12" score line
- Submit inside artwork upright — printers invert it during production
- Merge variables supported

### Snap Packs (Enterprise Only)

| Component | Dimensions | Format | Scaffold File |
|-----------|-----------|--------|---------------|
| Inside (flat) | 8.5" x 11" | NO BLEED | `snappack-8.5x11.html` |
| Outside (flat) | 8.5" x 11" | NO BLEED | (same file) |

**Key rules:**
- **NO BLEED format** — file size equals trim size (8.5" x 11")
- 0.5" no-print border on all sides (NOT 0.125" bleed)
- Perforated size: 7.5" x 10" (inside the no-print border)
- Safe zone: 7.25" x 9.75" (0.125" inset from perforation)
- Pressure-sealed with perforated sides — recipients tear open
- Interior is HIPAA-compliant (sealed until opened)
- Inside folds at center (5.5") — design both halves; inside panel rotates 180°
- Outside has ink-free zone (4" x 2.375") for address/postage
- High open rates due to the "what's inside?" factor
- Merge variables supported

### Booklets (Enterprise Only)

| Size | Page | Pages | Stock | Scaffold File |
|------|------|-------|-------|---------------|
| Digest | 8.375" x 5.375" | 8-32 (increments of 4) | 60# Gloss Text | `booklet-8.375x5.375.html` |

**Key rules:**
- Saddle-stitched (stapled at spine)
- Currently NOT personalizable (no merge variables)
- Offset printed (not digital) — higher quality but no personalization
- A 9x6" digitally printed version with personalization is coming
- Account for spine gutter — keep text 0.25" from binding edge
- Page count must be in increments of 4

### Buckslips (Enterprise Only)

| Size | Bleed | Trim | Safe Zone | Format | Scaffold File |
|------|-------|------|-----------|--------|---------------|
| Standard | 8.75" x 3.75" | 8.5" x 3.5" | 8.25" x 3.25" | PDF only | `buckslip.html` |

**Key rules:**
- **Buckslips HAVE bleed** — 8.75" x 3.75" is the bleed size, NOT the trim
- Trim: 8.5" x 3.5" (0.125" bleed per side)
- Safe zone: 8.25" x 3.25" (0.125" inset from trim)
- Letter inserts only — included with 8.5x11" letters via Campaigns API
- PDF format only (no HTML)
- No merge variables
- Stock: 80# Text or Cover, Gloss or Matte
- Front + Back surfaces

### Card Affix (Enterprise Only)

| Orientation | Trim | Format | Scaffold File |
|-------------|------|--------|---------------|
| Vertical | 2.125" x 3.375" | PDF only | `card-affix.html` |
| Horizontal | 3.375" x 2.125" | PDF only | (same file) |

**Key rules:**
- Physical cards affixed to 8.5x11" letters
- PDF format only (no HTML)
- No merge variables
- Minimum order: 10,000 cards
- Front + Back for each orientation

---

## Universal Rules

| Rule | Value |
|------|-------|
| Minimum DPI | 300 (for raster: PNG, JPEG) |
| Bleed | 0.125" (1/8") on all sides — except: letters (no bleed), card affix (no bleed), snap packs (no bleed, 0.5" no-print border instead). Buckslips DO have bleed. |
| Safe zone | Varies by format: 1/16" (0.0625") for postcards, 1/8" (0.125") for self-mailers/buckslips/snap packs. Letters have no traditional safe zone. |
| Max file size | 5 MB |
| Accepted formats | HTML, PDF, PNG, JPEG (varies by type) |
| Merge variable syntax | `{{variable_name}}` |
| Max merge content | 25,000 characters |
| Variable name restrictions | No whitespace; no `! " # % & ' ( ) * + , / ; < = > @ [ \ ] ^ \` { \| } ~` |

---

## Plan Requirements

### Available Without Enterprise (Designable)
- **Postcards:** 4 sizes x 2 surfaces = 8 template surfaces
- **Letters (standard 8.5x11):** 1 size, multi-page

### Requires Enterprise (Designable)
- **Self-Mailers:** 4 sizes x 2 surfaces = 8 template surfaces
- **Letters (legal 8.5x14):** 1 size, multi-page
- **Snap Packs:** 2 components (inside + outside)
- **Booklets:** 1 size, 8-32 pages
- **Buckslips:** 1 surface (front + back)
- **Card Affix:** 2 surfaces per orientation
- **Custom/Return Envelopes:** branded designs

---

## Lob PDF Cross-Check — Discrepancies Found & Fixed

We built all 14 scaffolds from scratch using Lob's API documentation, then downloaded Lob's official PDF templates from S3 and compared zone-by-zone. Several discrepancies were found and corrected.

### Official Lob PDF Templates

All stored in `docs/lob-templates/`:

```
docs/lob-templates/
├── 4x6_postcard.pdf
├── 5x7_postcard.pdf
├── 6x9_postcard.pdf
├── 6x11_postcard.pdf
├── letter_standard.pdf
├── letter_flat.pdf
├── letter_legal.pdf
├── selfmailer_6x18_bifold.pdf
├── selfmailer_12x9_bifold.pdf
├── selfmailer_11x9_bifold.pdf
├── selfmailer_17.75x9_trifold.pdf
├── snappack_8.5x11.pdf
├── booklet_8.375x5.375.pdf
├── buckslip.pdf
└── card_affix.pdf
```

### Discrepancies Found

| Issue | What We Had | What Lob Shows | Root Cause |
|-------|------------|----------------|------------|
| **Postcard safe zone** | 1/8" (0.125") inset from trim | 1/16" (0.0625") inset from trim | API docs don't specify safe zone size; we used industry default. Lob uses tighter tolerance for postcards. |
| **Buckslip dimensions** | 8.75" x 3.75" listed as trim (no bleed) | 8.75" x 3.75" is BLEED; trim is 8.5" x 3.5" | API lists one dimension without clarifying bleed vs trim. |
| **Snap pack format** | Standard bleed format (8.75" x 11.25" file) | NO-BLEED format, 8.5" x 11" file, 0.5" no-print border | API docs describe file size as 8.5x11 but don't emphasize the completely different no-bleed model. |
| **Letter QR zone** | 0.58" box at corner | 0.5" x 0.5" box at 0.087" from edges | Slight measurement error from spec interpretation. |
| **Letter "logo area"** | Generic logo placement box | Two specific envelope windows (top: 3.25"x0.875", bottom: 4"x1") | API describes envelope type but not window positions. PDF template shows exact window rectangles. |
| **Legal letter fold lines** | ~4.5" and ~9.5" from top | 3.75" and 7" (3.75/3.25/3.25/3.75 pattern) | Assumed even thirds. Actual fold is a double parallel fold with specific section sizes. |
| **Self-mailer glue zones** | Only on trifold | All self-mailers (bifolds too) | API mentions "sealed" but doesn't specify glue location/size for bifolds. |
| **Card affix corners** | Square corners | 1/8" rounded corners | Not in API spec; only visible in PDF template. |

### Why the Discrepancies Existed

The root cause is that **Lob's API documentation and their physical printing templates are two different sources of truth that don't fully overlap**:

1. **API docs give dimensions and format types** — enough to submit valid files, but not enough to design accurately
2. **PDF templates give manufacturing reality** — zone positions, fold patterns, envelope windows, glue areas, and actual safe zone measurements
3. **Some specs are ambiguous** — a single dimension without "bleed" or "trim" qualifier (buckslips)
4. **Some constraints aren't in the API at all** — safe zone sizes, envelope window positions, fold patterns, glue zone locations, QR zone exact placement
5. **Some formats break the standard pattern** — snap packs use a completely different model (no-bleed with no-print border) that isn't obvious from the API

**Lesson: Always cross-reference API specs against official PDF templates before finalizing scaffolds. The PDFs are ground truth for physical printing constraints.**

### Corrections Applied

All 14 HTML scaffold files were updated. Key changes:
- **Postcards (all 4):** Safe zone CSS changed from 24px to 18px inset from file edge; added explanatory text
- **Snap pack:** Complete rewrite — no-bleed format, 48px no-print border, perf at 48px, safe at 60px
- **Buckslip:** Added bleed/trim/safe zone overlays with proper 12px bleed border
- **Letters (both):** QR zone corrected, envelope windows added replacing logo area, legal fold lines fixed
- **Self-mailers (all 4):** Glue zones added to all bifolds (not just trifold), explanatory text added
- **Card affix:** Added border-radius for rounded corners, added safe zone overlays

> **Note:** The Figma files may still contain pre-correction versions and need re-capture.

---

## HTML-to-Figma Capture Workflow

This is how scaffold HTML files get pushed into Figma:

1. **Serve locally:** `python3 -m http.server 8787 --directory /path/to/houston`
2. **Get capture ID:** Call `generate_figma_design` with `outputMode: newFile` (first scaffold) or `existingFile` (subsequent)
3. **Open with hash URL:** `open "http://localhost:8787/scaffolds/{file}.html#figmacapture={captureId}&figmaendpoint=...&figmadelay=2000"`
4. **Poll for completion:** Call `generate_figma_design` with the `captureId` every 5 seconds until status is `completed`
5. **One at a time:** Parallel captures are unreliable with Chrome tab reuse. Do them sequentially

### Gotchas
- If Chrome reuses a tab, the hash fragment (capture params) may not trigger — use `open -n -a "Google Chrome" --args --new-window` to force a new window
- The HTTP server must be serving from the correct directory — verify with `curl` before attempting captures
- Large pages (like the 1728px-tall trifold) may need a longer `figmadelay` (3000ms+)
- Each capture ID is single-use — if a capture goes stale, generate a fresh one

---

## Color Coding Convention (Scaffolds)

All scaffolds use a consistent visual language:

| Color | Zone | CSS |
|-------|------|-----|
| Light red border | Bleed area | `rgba(255, 180, 180, 0.5)` |
| Dark solid line | Trim line | `#333` |
| Green dashed | Safe zone | `#22aa22` |
| Red filled | Ink-free zone (address/postage) | `rgba(220, 50, 50, 0.25)` with `#cc3333` border |
| Orange dashed | Fold lines | `#ff6600` |
| Yellow dashed | Glue zone | `rgba(255, 200, 0, 0.15)` with `#cc9900` border |
| Blue dotted | Perforated edges | `#0088cc` |
| Orange hatched | USPS scan warning | `rgba(255, 165, 0, 0.08)` diagonal stripes |
| Blue dashed | Logo area (letters) | `#3366cc` |
| Purple filled | QR code / sequence ID zones | `#9933cc` |
| Purple badge | Enterprise-only indicator | `#6B21A8` |
| Green badge | HIPAA indicator | `#059669` |
