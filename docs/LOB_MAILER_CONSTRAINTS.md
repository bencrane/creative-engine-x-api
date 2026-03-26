# Lob Mailer Physical Constraints

**Purpose:** Defines the finite set of physical mailer types and their size/format constraints. Every Figma template created in this system must conform to one of these specs.

---

## Universal Rules

- **DPI:** 300 minimum for all raster files (PNG, JPEG)
- **Bleed:** 1/8" (0.125") on all sides for postcards, self-mailers, buckslips. **No bleed** for letters, card affix, snap packs.
- **Safe zone:** Varies by format — 1/16" (0.0625") for postcards, 1/8" (0.125") for self-mailers/buckslips. Snap packs use 0.125" inset from perforation edge.
- **Max file size:** 5MB
- **Accepted formats:** HTML, PDF, PNG, JPEG (varies by type)
- **Merge variables:** `{{variable_name}}` syntax, max 25,000 characters
  - Variable names cannot contain whitespace or: `! " # % & ' ( ) * + , / ; < = > @ [ \ ] ^ \` { | } ~`

---

## Postcards (All Plans)

| Size | Trim (inches) | File w/ Bleed (inches) | Pixels @ 300 DPI | Sides |
|------|---------------|----------------------|-------------------|-------|
| 4x6 | 4" x 6" | 4.25" x 6.25" | 1,275 x 1,875 | Front + Back |
| 5x7 | 5" x 7" | 5.25" x 7.25" | 1,575 x 2,175 | Front + Back |
| 6x9 | 6" x 9" | 6.25" x 9.25" | 1,875 x 2,775 | Front + Back |
| 6x11 | 6" x 11" | 6.25" x 11.25" | 1,875 x 3,375 | Front + Back |

- Formats: HTML, PDF, PNG, JPEG
- Merge variables: Yes
- 4x6 qualifies for USPS First Class at lower postcard rate
- 6x9 is the most popular — good balance of visibility and cost
- 6x11 is the largest, qualifies for Marketing Mail letter rate
- Only 4x6 can go international
- Back side must leave room for address block and postage

---

## Self-Mailers (Enterprise Only)

All fold down to a 6x9" finished size.

| Size | Unfolded (inches) | File w/ Bleed (inches) | Pixels @ 300 DPI | Fold Type |
|------|-------------------|----------------------|-------------------|-----------|
| 6x18_bifold | 6" x 18" | 6.25" x 18.25" | 1,875 x 5,475 | Horizontal bifold, 2 panels |
| 12x9_bifold | 12" x 9" | 12.25" x 9.25" | 3,675 x 2,775 | Vertical bifold, 2 panels |
| 11x9_bifold | 11" x 9" | 11.25" x 9.25" | 3,375 x 2,775 | Vertical bifold, 1" panel offset |
| 17.75x9_trifold | 17.75" x 9" | 18" x 9.25" | 5,400 x 2,775 | C-fold inward, 3 panels, 0.25" offset on bottom |

- Formats: HTML, PDF, PNG, JPEG
- Merge variables: Yes
- Surfaces: Inside + Outside
- Outside must leave room for address block and postage

---

## Letters (In Envelopes)

| Size | Page (inches) | Plan | Envelope | Notes |
|------|--------------|------|----------|-------|
| Standard | 8.5" x 11" | All plans | #10 double-window (1-6 sheets), flat (7-60 sheets) | B&W or color, single or double-sided |
| Legal | 8.5" x 14" | Enterprise only | #10 (folded to fit) | Max 3 sheets currently |

- Formats: HTML, PDF
- Merge variables: Yes
- Pages: Variable (multi-page supported)

---

## Letter Add-ons (Enterprise Only, 8.5x11" Letters Only)

### Buckslips
| Size | Bleed (inches) | Trim (inches) | Safe Zone (inches) |
|------|---------------|--------------|-------------------|
| Standard | 8.75" x 3.75" | 8.5" x 3.5" | 8.25" x 3.25" |

- Formats: PDF only
- Merge variables: No
- Via Campaigns API only
- Stock: 80# Text or Cover, Gloss or Matte
- **8.75" x 3.75" is the bleed size** — trim is 8.5" x 3.5"
- Front + Back surfaces

### Card Affix
| Size | Trim (inches) | Orientation |
|------|--------------|-------------|
| Standard | 2.125" x 3.375" | Vertical |
| Standard | 3.375" x 2.125" | Horizontal |

- Formats: PDF only
- Merge variables: No
- Min order: 10,000 cards

### Return Envelopes
- #9 return envelope (BRM or courtesy reply)
- Included as insert with the letter

### Custom Envelopes
- Branded #10 outer envelopes
- Branded #9 return envelopes

---

## Snap Packs (Enterprise Only)

Pressure-sealed with perforated sides. High open rates. HIPAA-compliant for interior content.

**NO BLEED format** — file size equals trim size.

| Component | File Size (inches) | No-Print Border | Perf Size | Safe Zone | Pixels @ 300 DPI |
|-----------|-------------------|-----------------|-----------|-----------|-------------------|
| Inside (flat) | 8.5" x 11" | 0.5" all sides | 7.5" x 10" | 7.25" x 9.75" | 2,550 x 3,300 |
| Outside (flat) | 8.5" x 11" | 0.5" all sides | 7.5" x 10" | 7.25" x 9.75" | 2,550 x 3,300 |
| Folded | 8.5" x 5.5" | — | — | — | — |

- Formats: HTML, PDF, PNG, JPEG
- Merge variables: Yes
- Color option: true/false
- Inside folds at center (5.5") — inside panel rotates 180° during production
- 0.5" no-print border (not 0.125" bleed) — nothing prints in this area

---

## Booklets (Enterprise Only)

Offset printed, saddle-stitched.

| Size | Page (inches) | Pixels @ 300 DPI | Plan | Personalizable |
|------|--------------|-------------------|------|----------------|
| Digest | 8.375" x 5.375" | 2,513 x 1,613 | Enterprise | No (not currently) |
| 9x6 | 9" x 6" | TBD | Enterprise | Yes (coming soon, digitally printed) |

- Formats: HTML, PDF, PNG, JPEG
- Page counts: 8, 12, 16, 20, 24, 28, or 32 (increments of 4)
- Stock: 60# Gloss Text (default)

---

## Checks

| Size | Notes |
|------|-------|
| Standard check | Sent in #10 envelope, same as letters |

- Up to 6 sheets; over 6 incurs extra postage
- Non-designable format (standard check layout)

---

## Certified Mail

- Letters sent in large single-windowed #10 Certified Mail envelope with security tint
- Non-customizable envelope
- Not a design target for creative templates

---

## Template Type Summary

| Mailer Type | Plan | Sizes | Surfaces to Design | Merge Vars | Primary Formats |
|-------------|------|-------|-------------------|------------|-----------------|
| **Postcards** | All | 4 sizes | Front + Back | Yes | HTML, PDF |
| **Self-Mailers** | Enterprise | 4 sizes | Inside + Outside | Yes | HTML, PDF |
| **Letters** | All (legal: Enterprise) | 2 sizes | Pages | Yes | HTML, PDF |
| **Snap Packs** | Enterprise | 1 size (2 components) | Inside + Outside | Yes | HTML, PDF |
| **Booklets** | Enterprise | 1 size (2nd coming) | Pages (8-32) | No (yet) | HTML, PDF |
| **Buckslips** | Enterprise | 1 size | Single side | No | PDF |
| **Card Affix** | Enterprise | 1 size (2 orientations) | Front + Back | No | PDF |
| **Checks** | All | 1 format | N/A (standard layout) | N/A | N/A |
| **Certified Mail** | All | 1 format | N/A (non-customizable) | N/A | N/A |

### Available Without Enterprise (Designable)

- **Postcards:** 4 sizes x 2 surfaces = **8 template surfaces**
- **Letters (standard):** 1 size x N pages = **page templates**

### Requires Enterprise (Designable)

- **Self-Mailers:** 4 sizes x 2 surfaces = **8 template surfaces**
- **Letters (legal):** 1 size x N pages
- **Snap Packs:** 2 components = **2 template surfaces**
- **Booklets:** 1 size x 8-32 pages
- **Buckslips:** 1 surface
- **Card Affix:** 2 surfaces
- **Custom/Return Envelopes:** branded designs
