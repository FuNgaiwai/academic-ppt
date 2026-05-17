#!/usr/bin/env python3
"""Score PubMed papers for PPT relevance. Higher = better for presentation use."""
import json, sys, re

def quality_score(paper):
    """Score paper quality based on abstract and metadata. Score >= 12 = keep."""
    score = 0
    abstract = paper.get('abstract', '')
    title = paper.get('title', '')
    pubtype = paper.get('pubtype', [])
    journal = paper.get('journal', '')
    pubdate = paper.get('pubdate', '')

    # Has abstract
    if abstract and len(abstract) > 200:
        score += 3
    elif abstract:
        score += 1

    # Publication type
    pt_str = ' '.join(pubtype).lower()
    if 'review' in pt_str or 'meta-analysis' in pt_str or 'systematic review' in pt_str:
        score += 5
    elif 'guideline' in pt_str or 'practice guideline' in pt_str:
        score += 5
    elif 'clinical trial' in pt_str or 'randomized controlled trial' in pt_str:
        score += 4

    # Title check for review
    title_lower = title.lower()
    if 'systematic review' in title_lower or 'meta-analysis' in title_lower:
        score += 5
    if 'review' in title_lower and ('narrative' in title_lower or 'comprehensive' in title_lower):
        score += 3

    # Abstract structure
    if abstract:
        structure_markers = ['background', 'methods', 'results', 'conclusions', 'purpose']
        marker_count = sum(1 for m in structure_markers if m in abstract.lower())
        if marker_count >= 4: score += 3
        elif marker_count >= 2: score += 1

    # Statistical data
    if re.search(r'(p\s*[<>=]\s*0\.\d+|95%\s*CI|HR\s*=|OR\s*=|RR\s*=|n\s*=\s*\d+)', abstract):
        score += 2

    # Abstract length
    if len(abstract) > 1500: score += 2
    elif len(abstract) > 800: score += 1

    # High-impact journal (partial match list)
    high_impact = ['lancet', 'jco', 'jama', 'bmj', 'corr', 'jbjs', 'bone joint',
                   'cancer', 'annals of surgical oncology', 'j surg oncol',
                   'int j radiat oncol', 'radiotherapy oncol', 'eur j cancer',
                   'clinical orthop', 'journal of pediatric orthop', 'skeletal radiol']
    if any(j in journal.lower() for j in high_impact):
        score += 2

    # Recency
    year_match = re.search(r'(\d{4})', pubdate)
    if year_match:
        year = int(year_match.group(1))
        if year >= 2024: score += 3
        elif year >= 2022: score += 2
        elif year >= 2020: score += 1

    # Case report penalty
    if 'case report' in pt_str.lower() or 'case reports' in pt_str.lower():
        score -= 2

    # Keywords
    if len(paper.get('keywords', [])) >= 3:
        score += 1

    # Non-English rejection
    if re.search(r'[一-鿿가-힯]', title + abstract):
        return -100

    return score


if __name__ == '__main__':
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            papers = json.load(f)
    else:
        papers = json.load(sys.stdin)

    if isinstance(papers, dict):
        papers = [papers]

    scored = []
    for p in papers:
        s = quality_score(p)
        scored.append((s, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    for score, paper in scored:
        pmid = paper.get('pmid', '?')
        title = paper.get('title', '?')[:80]
        pubdate = paper.get('pubdate', '?')
        print(f'[{score:>3}] PMID {pmid} ({pubdate}): {title}')

    kept = [s for s, _ in scored if s >= 12]
    rejected = [s for s, _ in scored if s < 0]
    print(f'\n---')
    print(f'Total: {len(scored)} | Keep (>=12): {len(kept)} | Rejected (<0): {len(rejected)}')
