"""
grobid_to_minjson.py

1) Runs GROBID to produce TEI XML files.
2) Converts each TEI into:
   - <paper>.json        (paper_id, title, abstract?, fulltext, authors, year, references=[ref_id...])
   - <paper>.refs.json   (references objects with generated stable ref_id)
3) Rewrites inline citations in fulltext:
   - <ref type="bibr" target="#bX">...</ref> -> "(Author, Year)"
4) Optionally moves successfully processed PDFs into another directory.

Assumes GROBID server is running, e.g.
  docker run --rm --init -p 8070:8070 grobid/grobid:0.8.2-crf
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET

from grobid_client.grobid_client import GrobidClient

TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}
XML_NS = "{http://www.w3.org/XML/1998/namespace}"


def norm(s: str) -> str:
    return " ".join(s.split()) if s else ""


def all_text(el: ET.Element | None) -> str:
    return norm("".join(el.itertext())) if el is not None else ""


def stable_id(prefix: str, *parts: str, n: int = 16) -> str:
    raw = "||".join(norm(p).lower() for p in parts if p)
    h = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:n]
    return f"{prefix}{h}"


# ---------- paper-level fields ----------

def pick_title(root: ET.Element) -> str:
    el = root.find(".//tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title", TEI_NS)
    if el is None:
        el = root.find(".//tei:title", TEI_NS)
    return all_text(el)


def pick_abstract(root: ET.Element) -> str | None:
    ps = root.findall(".//tei:teiHeader//tei:profileDesc//tei:abstract//tei:p", TEI_NS)
    text = norm(" ".join(all_text(p) for p in ps))
    return text or None


def pick_authors(root: ET.Element) -> list[str]:
    authors: list[str] = []

    for a in root.findall(".//tei:teiHeader//tei:sourceDesc//tei:biblStruct//tei:analytic//tei:author", TEI_NS):
        pers = a.find(".//tei:persName", TEI_NS)
        if pers is not None:
            forenames = [all_text(fn) for fn in pers.findall(".//tei:forename", TEI_NS)]
            surnames = [all_text(sn) for sn in pers.findall(".//tei:surname", TEI_NS)]
            name = norm(" ".join([p for p in forenames + surnames if p]))
            if name:
                authors.append(name)
                continue
        t = all_text(a)
        if t:
            authors.append(t)

    if authors:
        return authors

    for a in root.findall(".//tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:author", TEI_NS):
        t = all_text(a)
        if t:
            authors.append(t)

    return authors


def pick_year(root: ET.Element) -> str | None:
    for path in [
        ".//tei:teiHeader//tei:sourceDesc//tei:biblStruct//tei:monogr//tei:imprint//tei:date",
        ".//tei:teiHeader//tei:fileDesc//tei:publicationStmt//tei:date",
    ]:
        for d in root.findall(path, TEI_NS):
            when = d.attrib.get("when")
            if when:
                y = when.strip()[:4]
                if y.isdigit():
                    return y
            t = all_text(d)
            for token in t.split():
                if len(token) >= 4 and token[:4].isdigit():
                    return token[:4]
    return None


# ---------- references extraction ----------

def _surname_from_name(name: str) -> str:
    name = norm(name)
    if not name:
        return ""
    # Simple heuristic: surname = last token
    return name.split()[-1]


def _format_author_year(authors: list[str] | None, year: str | None) -> str:
    year_str = year if (year and year.strip()) else "n.d."
    if not authors:
        return f"(Anon, {year_str})"
    surnames = [_surname_from_name(a) for a in authors if _surname_from_name(a)]
    if not surnames:
        return f"(Anon, {year_str})"
    if len(surnames) == 1:
        return f"({surnames[0]}, {year_str})"
    if len(surnames) == 2:
        return f"({surnames[0]} & {surnames[1]}, {year_str})"
    return f"({surnames[0]} et al., {year_str})"


def extract_reference_obj(biblstruct: ET.Element) -> tuple[dict, str]:
    """
    Returns (ref_obj, tei_key) where tei_key is the xml:id like 'b1' used by inline targets '#b1'.
    """
    tei_key = biblstruct.attrib.get(f"{XML_NS}id") or ""  # e.g. b1

    title_el = (
        biblstruct.find(".//tei:analytic//tei:title", TEI_NS)
        or biblstruct.find(".//tei:monogr//tei:title", TEI_NS)
        or biblstruct.find(".//tei:title", TEI_NS)
    )
    title = all_text(title_el)

    ref_authors: list[str] = []
    for a in biblstruct.findall(".//tei:analytic//tei:author", TEI_NS):
        pers = a.find(".//tei:persName", TEI_NS)
        if pers is not None:
            forenames = [all_text(fn) for fn in pers.findall(".//tei:forename", TEI_NS)]
            surnames = [all_text(sn) for sn in pers.findall(".//tei:surname", TEI_NS)]
            name = norm(" ".join([p for p in forenames + surnames if p]))
            if name:
                ref_authors.append(name)
                continue
        t = all_text(a)
        if t:
            ref_authors.append(t)

    year = None
    for d in biblstruct.findall(".//tei:date", TEI_NS):
        when = d.attrib.get("when")
        if when and when[:4].isdigit():
            year = when[:4]
            break
        t = all_text(d)
        for token in t.split():
            if len(token) >= 4 and token[:4].isdigit():
                year = token[:4]
                break
        if year:
            break

    doi = None
    for idno in biblstruct.findall(".//tei:idno", TEI_NS):
        if idno.attrib.get("type", "").lower() == "doi":
            doi = all_text(idno)
            if doi:
                break

    if doi:
        ref_id = stable_id("R_", doi)
    else:
        first_author = ref_authors[0] if ref_authors else ""
        ref_id = stable_id("R_", title, year or "", first_author)

    out = {"ref_id": ref_id}
    if title:
        out["title"] = title
    if ref_authors:
        out["authors"] = ref_authors
    if year:
        out["year"] = year
    if doi:
        out["doi"] = doi

    return out, tei_key


def extract_references(root: ET.Element) -> tuple[list[dict], dict[str, dict]]:
    """
    Returns (refs_list, tei_key_to_refmeta)
    tei_key_to_refmeta maps 'b1' -> {'ref_id':..., 'authors':..., 'year':...}
    """
    biblstructs = root.findall(".//tei:text//tei:back//tei:listBibl//tei:biblStruct", TEI_NS)
    if not biblstructs:
        biblstructs = root.findall(".//tei:teiHeader//tei:listBibl//tei:biblStruct", TEI_NS)

    refs: list[dict] = []
    seen_ref_ids: set[str] = set()
    tei_key_to_refmeta: dict[str, dict] = {}

    for bs in biblstructs:
        ref, tei_key = extract_reference_obj(bs)
        rid = ref["ref_id"]
        if rid in seen_ref_ids:
            # still map tei_key if present
            if tei_key and tei_key not in tei_key_to_refmeta:
                tei_key_to_refmeta[tei_key] = ref
            continue
        seen_ref_ids.add(rid)
        refs.append(ref)
        if tei_key and tei_key not in tei_key_to_refmeta:
            tei_key_to_refmeta[tei_key] = ref

    return refs, tei_key_to_refmeta


# ---------- inline citation rewriting ----------

def render_with_citation_rewrite(el: ET.Element | None, tei_key_to_refmeta: dict[str, dict]) -> str:
    """
    Render element text recursively, replacing <ref type="bibr" target="#bX">...</ref>
    with "(Author, Year)" using reference metadata.
    """
    if el is None:
        return ""

    parts: list[str] = []
    if el.text:
        parts.append(el.text)

    for child in list(el):
        tag_local = child.tag.split("}")[-1]  # handles namespaces
        if tag_local == "ref" and child.attrib.get("type") == "bibr":
            target = child.attrib.get("target", "")
            tei_key = target[1:] if target.startswith("#") else target
            meta = tei_key_to_refmeta.get(tei_key)
            if meta:
                cite = _format_author_year(meta.get("authors"), meta.get("year"))
            else:
                cite = "(Anon, n.d.)"
            parts.append(cite)
        else:
            parts.append(render_with_citation_rewrite(child, tei_key_to_refmeta))

        if child.tail:
            parts.append(child.tail)

    return norm("".join(parts))


def pick_fulltext_with_citations(root: ET.Element, tei_key_to_refmeta: dict[str, dict]) -> str:
    ps = root.findall(".//tei:text/tei:body//tei:p", TEI_NS)
    return norm(" ".join(render_with_citation_rewrite(p, tei_key_to_refmeta) for p in ps))


# ---------- main conversion ----------

def tei_to_outputs(tei_path: Path) -> tuple[dict, list[dict]]:
    tree = ET.parse(tei_path)
    root = tree.getroot()

    title = pick_title(root)
    abstract = pick_abstract(root)
    authors = pick_authors(root)
    year = pick_year(root)

    refs, tei_key_to_refmeta = extract_references(root)
    fulltext = pick_fulltext_with_citations(root, tei_key_to_refmeta)

    paper_id = tei_path.name.replace(".tei.xml", "")

    paper = {
        "paper_id": paper_id,
        "title": title,
        "full_text": fulltext,
        "authors": authors,
        "references": [r["ref_id"] for r in refs],
    }
    if abstract:
        paper["abstract"] = abstract
    if year:
        paper["year"] = year

    return paper, refs


def iter_pdfs(inp: Path) -> list[Path]:
    if inp.is_file():
        return [inp] if inp.suffix.lower() == ".pdf" else []
    return sorted(p for p in inp.glob("*.pdf") if p.is_file())


def pdf_for_tei(tei_path: Path, pdf_candidates: dict[str, Path]) -> Path | None:
    """
    Best-effort mapping:
    <name>.grobid.tei.xml  -> <name>.pdf (same stem before '.grobid')
    """
    name = tei_path.name
    if name.endswith(".grobid.tei.xml"):
        base = name.replace(".grobid.tei.xml", "")
        return pdf_candidates.get(base.lower())
    # fallback: try stripping ".tei.xml"
    base2 = name.replace(".tei.xml", "")
    return pdf_candidates.get(base2.lower())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="PDF file or directory of PDFs")
    ap.add_argument("--output", required=True, help="Output directory")
    ap.add_argument("--grobid-url", default="http://localhost:8070")
    ap.add_argument("--n", type=int, default=2)
    ap.add_argument("--force", action="store_true", help="Overwrite existing TEI/JSON")
    ap.add_argument("--processed-pdf-dir", default=None, help="Move successfully processed PDFs here")
    args = ap.parse_args()

    inp = Path(args.input).expanduser().resolve()
    out = Path(args.output).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    processed_dir = Path(args.processed_pdf_dir).expanduser().resolve() if args.processed_pdf_dir else None
    if processed_dir:
        processed_dir.mkdir(parents=True, exist_ok=True)

    # Map input PDFs by basename for moving later
    pdfs = iter_pdfs(inp)
    pdf_candidates = {p.stem.lower(): p for p in pdfs}

    client = GrobidClient(grobid_server=args.grobid_url)

    # 1) Run GROBID -> TEI XML
    client.process(
        "processFulltextDocument",
        input_path=str(inp),
        output=str(out),
        n=args.n,
        json_output=False,
        force=args.force,
        verbose=False,
    )

    # 2) Convert TEI -> JSON + refs JSON
    tei_files = sorted(out.glob("*.tei.xml"))
    print(f"Found {len(tei_files)} TEI file(s) to convert")

    ok, err = 0, 0
    moved = 0

    for tei in tei_files:
        try:
            paper, refs = tei_to_outputs(tei)

            paper_json = tei.with_suffix("").with_suffix(".json")
            refs_json = tei.with_suffix("").with_suffix(".refs.json")

            if (not args.force) and (paper_json.exists() or refs_json.exists()):
                print(f"[SKIP] {tei.name} (json exists). Use --force to overwrite.")
                continue

            paper_json.write_text(json.dumps(paper, ensure_ascii=False, indent=2), encoding="utf-8")
            refs_json.write_text(json.dumps(refs, ensure_ascii=False, indent=2), encoding="utf-8")
            ok += 1

            # 3) Move processed PDF if configured
            if processed_dir:
                pdf_path = pdf_for_tei(tei, pdf_candidates)
                if pdf_path and pdf_path.exists():
                    dst = processed_dir / pdf_path.name
                    shutil.move(str(pdf_path), str(dst))
                    moved += 1

        except Exception as e:
            err += 1
            print(f"[ERROR] TEI->JSON failed for {tei.name}: {e}")

    print(f"[DONE] Converted OK={ok}, ERR={err}. PDFs moved={moved}. Output dir: {out}")


if __name__ == "__main__":
    main()
