# Academic PPT Skill for Claude Code

End-to-end pipeline: search PubMed → import to Zotero → screen & assess → extract full text → generate citation-verified PowerPoint.

## What It Does

Generates a complete academic presentation from a PubMed literature review. Invoked via `/academic-ppt` in Claude Code.

The skill enforces strict data integrity: **every fact on every slide must be traceable to a specific PMID in the user's Zotero library**, verified against the paper's actual full text.

## Prerequisites

| Component | Required |
|-----------|----------|
| [Zotero desktop](https://www.zotero.org/) 7+ | ✅ |
| [Zotero MCP for Claude Code](https://github.com/lricher7329/zotero-mcp-claude-code) plugin | ✅ |
| Zotero MCP write scopes: `collections`, `metadata`, `bulk` | ✅ |
| Chrome DevTools MCP (`claude mcp add -s user chrome-devtools -- npx -y chrome-devtools-mcp@latest`) | ✅ |
| Node.js + `pptxgenjs` (`npm install -g pptxgenjs`) | ✅ |
| Python `pymupdf` (`pip install pymupdf`) | ✅ |

## Installation

```bash
git clone git@github.com:FuNgaiwai/academic-ppt.git ~/.claude/skills/academic-ppt
```

## Usage

In Claude Code, type:

```
/academic-ppt advances in limb salvage surgery for bone sarcoma
```

The skill will guide you through 5 phases:

1. **Literature Search** — PubMed → Zotero, organized by thematic modules
2. **Paper Screening** — quality scoring, non-English removal, tag selected papers
3. **Full-Text Extraction** — PyMuPDF extracts text + images from PDFs in your library
4. **PPT Generation** — slides with data tables, stat cards, and source citations
5. **QA Verification** — every PMID verified against PubMed, every slide checked

## Files

```
academic-ppt/
├── SKILL.md              # Full pipeline instructions for Claude Code
├── README.md             # This file
└── scripts/
    ├── score_papers.py   # Paper quality scoring (9-dimension heuristic)
    └── extract_pdfs.py   # PDF text + image extraction (PyMuPDF)
```

## Example Output

| Metric | Value |
|--------|-------|
| Papers searched | ~300 |
| After quality filter | ~90 (score ≥ 12) |
| Selected for PPT | ~20-25 |
| Final slide count | 25–30 |
| Images extracted | 50–100 |

## License

MIT
