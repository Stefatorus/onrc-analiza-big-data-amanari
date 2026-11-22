"""Internal links in the complete report (post-processing of the assembled PDF).

1. Table of contents: every row links to its page (targets from the PDF's own bookmarks).
2. Claim codes [Cxx] in the text link to the claim's row in the claims register (Part 8).
3. References "Partea N" and "capitolul N din Partea 2" link to the part / chapter.
4. The running head at the top of every page (after the TOC) links back to the TOC.

  python -X utf8 add_pdf_links.py <in.pdf> [<out.pdf>]      (default: in place)
"""
import re, sys, os
from pathlib import Path
import fitz


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def link(page, rect, target, zoom_top=True):
    page.insert_link({"kind": fitz.LINK_GOTO, "from": rect, "page": target, "to": fitz.Point(0, 0), "zoom": 0})


def main(src, dst):
    d = fitz.open(src)
    toc = d.get_toc()                                         # [lvl, title, page(1-based)]
    pages_of = {norm(t): p for _, t, p in toc}
    part_start = {int(m.group(1)): p for _, t, p in toc for m in [re.match(r"^Partea (\d+) · ", t)] if m}
    chap_page = {int(m.group(1)): p for _, t, p in toc for m in [re.match(r"^Cap\. (\d+) · ", t)] if m}
    toc_first = next(p for _, t, p in toc if t == "Cuprins")
    synth = next(p for _, t, p in toc if t.startswith("Sinteză"))
    toc_pages = range(toc_first - 1, synth - 1)               # 0-based TOC pages
    n_links = {"toc": 0, "claims": 0, "refs": 0, "home": 0}

    # 1. TOC rows: find each title on the TOC pages; link the full row width
    for _, t, p in toc:
        if t in ("Copertă", "Cuprins"):
            continue
        title = re.sub(r"^(Cap\. \d+|Anexa [A-Z]|Partea \d+|Anexă|S?\d{1,2}) · ", "", t)
        probe = title[:60]
        for k in toc_pages:
            hits = d[k].search_for(probe)
            if hits:
                r = hits[0]; W = d[k].rect.width
                row = fitz.Rect(40, r.y0 - 2, W - 40, r.y1 + 2)
                link(d[k], row, p - 1); n_links["toc"] += 1
                break

    # 2. claims register rows in Part 8: page where a register row starts with the claim id
    p8 = part_start.get(8)
    reg_page = {}
    if p8:
        end = min([p for n, p in part_start.items() if n > 8] + [len(d) + 1]) - 1
        ann = [p for _, t, p in toc if t.startswith("Anexă")]
        end = min([end] + [a - 1 for a in ann if a > p8])
        for k in range(p8 - 1, end):
            for b in d[k].get_text("dict")["blocks"]:
                for ln in b.get("lines", []):
                    txt = "".join(s["text"] for s in ln["spans"]).strip()
                    if re.fullmatch(r"C\d{2,3}", txt) and txt not in reg_page:
                        reg_page[txt] = k
    for k in range(len(d)):
        if k in toc_pages:
            continue
        page = d[k]
        for cid in set(re.findall(r"\[(C\d{2,3})\]", page.get_text("text"))):
            if cid in reg_page and reg_page[cid] != k:
                for r in page.search_for(f"[{cid}]"):
                    link(page, r, reg_page[cid]); n_links["claims"] += 1

    # 3. cross-references to parts and chapters
    for k in range(len(d)):
        if k in toc_pages:
            continue
        page = d[k]; txt = page.get_text("text")
        for n in set(int(x) for x in re.findall(r"Partea (\d)\b", txt)):
            if n in part_start:
                for r in page.search_for(f"Partea {n}"):
                    if r.y0 > 60:                              # not the running head
                        link(page, r, part_start[n] - 1); n_links["refs"] += 1
        for n in set(int(x) for x in re.findall(r"[Cc]apitolul (\d{1,2}) din Partea 2", txt)):
            if n in chap_page:
                for r in page.search_for(f"apitolul {n} din Partea 2"):
                    link(page, r, chap_page[n] - 1); n_links["refs"] += 1

    # 4. running head → table of contents (every page after the TOC)
    for k in range(synth - 1, len(d)):
        page = d[k]; W = page.rect.width
        link(page, fitz.Rect(40, 20, W * 0.6, 58), toc_first - 1); n_links["home"] += 1

    if dst == src:
        tmp = src + ".tmp.pdf"; d.save(tmp, garbage=3, deflate=True); d.close(); os.replace(tmp, src)
    else:
        d.save(dst, garbage=3, deflate=True)
    print(f"links added: {n_links} · register rows found: {len(reg_page)}")


if __name__ == "__main__":
    src = sys.argv[1]; dst = sys.argv[2] if len(sys.argv) > 2 else src
    main(src, dst)
