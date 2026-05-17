#!/usr/bin/env python3
"""Extract text and images from PDFs. Usage: python extract_pdfs.py <pdf_map.json> <output_dir>"""
import fitz, json, sys, os, hashlib

def extract(pdf_path, img_dir, text_dir):
    """Extract text and images from a single PDF. Returns (text_path, image_count)."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(pdf_path)

    doc = fitz.open(pdf_path)
    all_text = []
    img_count = 0

    for page in doc:
        all_text.append(page.get_text())
        for img in page.get_images(full=True):
            xref = img[0]
            base = doc.extract_image(xref)
            img_bytes = base["image"]
            if len(img_bytes) < 5000:
                continue
            img_hash = hashlib.md5(img_bytes).hexdigest()[:12]
            img_path = os.path.join(img_dir, f"{img_hash}.{base['ext']}")
            if not os.path.exists(img_path):
                with open(img_path, 'wb') as f:
                    f.write(img_bytes)
            img_count += 1

    doc.close()

    text_content = '\n'.join(all_text)
    text_path = os.path.join(text_dir, 'full_text.txt')
    with open(text_path, 'w') as f:
        f.write(text_content)

    return text_path, img_count


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: extract_pdfs.py <pdf_map.json> <output_dir>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        pdf_map = json.load(f)

    out_dir = sys.argv[2]
    img_dir = os.path.join(out_dir, 'images')
    text_dir = os.path.join(out_dir, 'texts')
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(text_dir, exist_ok=True)

    results = {}
    for pmid, info in pdf_map.items():
        path = info.get('path', '')
        if not path:
            print(f"SKIP PMID {pmid}: no path")
            continue
        try:
            txt_path, n_imgs = extract(path, img_dir, os.path.join(text_dir, pmid))
            results[pmid] = {'text_path': txt_path, 'images': n_imgs}
            print(f"OK PMID {pmid}: {n_imgs} images")
        except Exception as e:
            print(f"ERR PMID {pmid}: {e}")

    with open(os.path.join(out_dir, 'results.json'), 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nDone. {len(results)} PDFs processed. Results: {out_dir}/results.json")
