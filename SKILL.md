---
name: academic-ppt
description: Generate an academic presentation from a PubMed literature review. Covers the full pipeline: PubMed search via Zotero, paper screening, PDF full-text extraction, and citation-verified PPT generation. Use when the user wants to create a research presentation, journal club slides, or conference talk from biomedical literature.
argument-hint: "[topic description, e.g., 'advances in limb sarcoma surgery']"
---

# Academic PPT from PubMed Literature

End-to-end pipeline: search PubMed → import to Zotero → screen & assess → extract full text → generate PPT with verified citations.

## Prerequisites

- Zotero desktop with [Zotero MCP for Claude Code](https://github.com/lricher7329/zotero-mcp-claude-code) plugin installed
- Zotero MCP write scopes enabled: `collections`, `metadata`, `bulk`
- Chrome DevTools MCP configured (`claude mcp add -s user chrome-devtools -- npx -y chrome-devtools-mcp@latest`)
- Chrome running with remote debugging: `/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="$HOME/.chrome-debug-profile"`
- Python packages: `pymupdf` (PDF text/image extraction)
- Node.js packages: `pptxgenjs` (slide generation)

## Phase 0: Environment Check

Before starting, verify MCP servers:

```bash
claude mcp list
# Must show chrome-devtools and zotero-mcp as Connected
```

Check Zotero write scopes by listing tools—at minimum `create_item`, `batch_add_to_collection`, and `batch_tag` must be present:

```bash
curl -s -X POST http://127.0.0.1:23120/mcp -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 -c "
import json,sys
tools=[t['name'] for t in json.load(sys.stdin)['result']['tools']]
for t in ['create_item','batch_add_to_collection','batch_tag','search_by_identifier']:
    print(f'{t}: {\"✅\" if t in tools else \"❌\"}')"
```

## Phase 1: Literature Search & Zotero Import

### 1a. Break the topic into modules

Work with the user to define 3-5 thematic modules. Example for a surgical topic:

| Module | Sub-topics |
|--------|-----------|
| Module 1 | sub-topic A, sub-topic B |
| Module 2 | sub-topic C, sub-topic D |
| ... | ... |

### 1b. Search PubMed per sub-topic

For each sub-topic, design 1-2 English search queries. PubMed API via curl (avoids Python SSL issues):

```bash
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=$(python3 -c 'import urllib.parse; print(urllib.parse.quote("YOUR QUERY"))')&retmax=20&retmode=json&sort=relevance"
```

Prioritize: reviews & meta-analyses first, then original articles. Use date filter `2018:2026[pdat]`.

### 1c. Batch import to Zotero

For each search, get PMIDs → fetch metadata → create items in Zotero via MCP `create_item` with the target collection key. Use `search_collections` and `get_subcollections` to find collection keys.

**Important**: `create_item` calls MCP for each paper. With 20 papers, use 50ms delays between calls.

### 1d. Organize into collections

Create a main collection and sub-collections per module via MCP `create_collection`. Import papers directly into the correct sub-collection by passing `collections: [collectionKey]` to `create_item`.

## Phase 2: Paper Screening & Quality Assessment

### 2a. Remove non-English & off-topic papers

Scan titles and abstracts. Reject:
- Non-English articles (check for `[Article in French/German/...]` patterns)
- Papers about unrelated anatomical sites or diseases
- Case reports (unless specifically needed)

### 2b. Quality score (recommended)

Score each paper on a 9-dimension heuristic (see `scripts/score_papers.py`):
- Has substantive abstract (>200 chars): +3
- Review/Meta-analysis/Guideline: +5
- Clinical trial/RCT: +4
- Structured abstract (IMRaD): +1-3
- Contains statistical data (p-values, CI, HR/OR): +2
- High-impact journal: +2
- Recent (2022+): +1-3
- Keywords >= 3: +1

Target: ~8 papers per module after filtering (score >= 12).

### 2c. Tag selected papers

Use MCP `batch_tag` to tag the selected papers with a unique tag (e.g., "PPT_YYYYMMDD_topic"). The user can then screen further in Zotero.

## Phase 3: Full-Text Extraction — THE CRITICAL PHASE

### ⚠️ IRON RULE: Every data point on every slide MUST come from a paper in the user's Zotero library. Never cite a paper you haven't read the full text of. Never assume a PMCID mapping is correct.

### 3a. Identify papers with accessible full text

For each tagged paper, check via MCP `get_item_details` (mode="complete") whether it has a PDF attachment with a file path. Also check PubMed esummary for PMCID.

Papers have 3 tiers:
1. **PDF in Zotero** → extract with PyMuPDF (best: text + images + tables)
2. **PMC full text** → fetch via efetch API (text only, no images)
3. **Abstract only** → limited use, cite sparingly

### 3b. Extract PDF text with PyMuPDF

```python
import fitz
doc = fitz.open(pdf_path)
for page in doc:
    text = page.get_text()
    # Extract images
    for img in page.get_images(full=True):
        xref = img[0]
        base = doc.extract_image(xref)
        # Save to img_dir
```

### 3c. Extract PMC full text via efetch

```bash
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=PMC1234567&retmode=xml"
```

Parse XML for body paragraphs. Focus on: abstract, results, discussion/conclusion sections.

### 3d. Store extracted images

Create a `ppt_images/` folder. All extracted images go there, named as `pmid{PMID}_p{page}_{hash}.{ext}`. These are referenced by the PPT script.

## Phase 4: PPT Generation

### 4a. Design first

Before writing code, decide:
- Slide count (rule of thumb: 25-30 for a 25-minute talk)
- Color palette (one primary + one accent + dark/light backgrounds)
- Slide layout patterns (content slides, section dividers, summary slides)
- Module allocation

### 4b. Write pptxgenjs script

Use helper functions to reduce repetition:

```javascript
function sl(bg) { /* create slide with background */ }
function bar(s, title) { /* add top color bar + title */ }
function bul(s, items, x, y, w, h) { /* bullet list */ }
function tbl(s, headers, rows, x, y, w) { /* data table */ }
function card(s, num, label, x, y, w) { /* stat callout */ }
function img(s, pmid, num, opts) { /* insert extracted image */ }
function ref(s, text) { /* citation footnote */ }
function pg(s, n) { /* page number */ }
```

### 4c. Strict citation rules

**Every fact on every slide must be traceable to a specific PMID in the user's library.**

- Each content slide footnotes its source PMID(s)
- Never use data from papers outside the library
- If a PMCID looks suspicious, verify via PubMed esummary first
- Avoid "composite" citations that mix data from multiple unverified sources

### 4d. Visual design principles

- **Every slide needs a visual element**: image, table, or stat card — never text-only
- **1-3 papers per slide maximum**: deeper extraction, less superficial coverage
- **Tables for comparisons**: tech A vs B, before vs after, outcomes comparison
- **Stat cards for key numbers**: survival rates, recurrence rates, sample sizes
- **Section dividers**: dark background slides between modules
- **Consistent margins**: 0.5" minimum, left-align body text

### 4e. Information density balance

- 3-5 bullet points per content slide
- Each bullet: one clear claim, not a paragraph
- Tables: 4-7 rows, 3-5 columns — more than that, split into two slides
- If a slide has no visual element, it's not finished

## Phase 5: QA (Required)

### 5a. Content verification

```bash
python3 -m markitdown output.pptx | grep "来源:" | sort -u
```

Verify every PMID against the user's library. For any PMID that raises doubt, check:

```bash
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=XXXXX&retmode=json" | python3 -c "import json,sys; r=json.load(sys.stdin)['result']['XXXXX']; print(r['title'])"
```

### 5b. Slide count check

```bash
python3 -m markitdown output.pptx | grep -c "Slide number"
```

### 5c. Visual QA

Convert to PDF and inspect screenshots. If LibreOffice is not available, open the .pptx in PowerPoint/Keynote manually.

## Common Pitfalls (from painful experience)

1. **NEVER trust PMCID mappings from cached JSON**. Always re-verify via PubMed esummary.
2. **NEVER cite a paper you haven't read**. Data that "sounds right" may be from a completely different paper.
3. **NEVER generate slides from abstracts alone**, except as last resort. Full text is essential for data integrity.
4. **Always verify PDF paths** before extraction. A paper can have `atts=1` in collection scan but no PDF in `get_item_details`.
5. **PubMed API returns HTML for PMC PDFs**. Use the efetch XML API for full text, not PDF download links.
6. **pptxgenjs color values must NOT have `#` prefix**. Use `"XXXXXX"` not `"#XXXXXX"`. Always use the user's chosen color palette, never default to a preset.
