#!/usr/bin/env python3
"""Coarse pass (R1) for the topological connection map — deterministic, statistical.

Words/entities are SIGNALS that POINT toward connections between manual sections;
they are never used to infer intent. Three edge signals, all evidence-based:

  vocab  : shared distinctive vocabulary (TF-IDF cosine) — bulk topical overlap.
  entity : shared named entities (ALL_CAPS option/param-shaped tokens) — the rare,
           high-value connectors the plain TF-IDF pass under-weights.
  xref   : literal cross-references — `zshXxx` page mentions and mentions of another
           section/subsection's distinctive name (the manual pointing at itself).

Outputs (refs/graph/):
  sections.tsv  page, section, start_line, end_line, words   (manifest w/ line ranges)
  nodes.tsv     page, section, words, top_terms, entities
  edges.tsv     type, weight, section_a, section_b, shared_pointers
"""
import os, re, math
from collections import Counter

REFS = os.path.join(os.path.dirname(__file__), "..", "refs")
PAGES = ["zshmisc", "zshexpn", "zshparam", "zshoptions", "zshbuiltins"]

SECTION_RE = re.compile(r"^[A-Z][A-Z0-9 &/_-]*[A-Z]$")
WORD_RE    = re.compile(r"[a-z_][a-z0-9_]+")
ENTITY_RE  = re.compile(r"\b[A-Z][A-Z0-9]{2,}(?:_[A-Z0-9]+)*\b")   # NOMATCH, EXTENDED_GLOB, IFS
PAGE_RE    = re.compile(r"\bzsh[a-z]{2,}\b")                        # zshexpn, zshparam, ...
GENERIC_NAMES = {"Notes", "Rules", "Examples", "Overview", "Precedence",
                 "Description", "Modifiers"}

def split_sections(path):
    """Yield (section, start_line, end_line, body_lines) for one page (1-based)."""
    name, start, body = None, 0, []
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    for i, line in enumerate(lines, 1):
        if SECTION_RE.match(line) and "MANUAL" not in line.upper():
            if name is not None:
                yield name, start, i - 1, body
            name, start, body = line.strip(), i, []
        elif name is not None:
            body.append(line)
    if name is not None:
        yield name, start, len(lines), body

def load_name_catalog():
    """Map distinctive section/subsection name -> owning node id, from the outlines."""
    catalog = {}
    for page in PAGES:
        op = os.path.join(REFS, "structure", page + ".outline.txt")
        if not os.path.exists(op):
            continue
        cur_l1 = None
        for ln in open(op):
            m = re.match(r"^L(\d+)\s+(.*)$", ln.rstrip("\n"))
            if not m:
                continue
            lvl, nm = int(m.group(1)), m.group(2).strip()
            if lvl == 1:
                cur_l1 = f"{page}:{nm}"
            node = f"{page}:{nm}" if lvl == 1 else cur_l1
            # keep only distinctive names: multi-word or long, not generic, not page furniture
            if nm in GENERIC_NAMES or "MANUAL" in nm.upper() or "(1)" in nm:
                continue
            if (" " in nm and len(nm) >= 8) or len(nm) >= 12:
                catalog[nm] = node
    return catalog

def main():
    nodes = []   # dict per node
    for page in PAGES:
        for sec, s, e, body in split_sections(os.path.join(REFS, page + ".txt")):
            text = "\n".join(body)
            words = Counter(WORD_RE.findall(text.lower()))
            if sum(words.values()) < 20:
                continue
            nodes.append(dict(page=page, sec=sec, id=f"{page}:{sec}", s=s, e=e,
                              words=words, text=text,
                              entities=Counter(ENTITY_RE.findall(text)),
                              pages=Counter(p for p in PAGE_RE.findall(text))))
    N = len(nodes)

    # ---- TF-IDF over words ----
    df = Counter()
    for nd in nodes:
        df.update(nd["words"].keys())
    idf = {t: math.log(N / df[t]) for t in df}
    for nd in nodes:
        tot = sum(nd["words"].values())
        v = {t: (c / tot) * idf[t] for t, c in nd["words"].items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        nd["vec"] = {t: x / norm for t, x in v.items()}

    catalog = load_name_catalog()
    own_pages = {nd["page"] for nd in nodes}

    os.makedirs(os.path.join(REFS, "graph"), exist_ok=True)
    # ---- manifest ----
    with open(os.path.join(REFS, "graph", "sections.tsv"), "w") as fh:
        fh.write("page\tsection\tstart_line\tend_line\twords\n")
        for nd in nodes:
            fh.write(f"{nd['page']}\t{nd['sec']}\t{nd['s']}\t{nd['e']}\t{sum(nd['words'].values())}\n")
    # ---- nodes ----
    with open(os.path.join(REFS, "graph", "nodes.tsv"), "w") as fh:
        fh.write("page\tsection\twords\ttop_terms\tentities\n")
        for nd in nodes:
            top = sorted(nd["vec"], key=nd["vec"].get, reverse=True)[:12]
            ents = [e for e, _ in nd["entities"].most_common(12)]
            fh.write(f"{nd['page']}\t{nd['sec']}\t{sum(nd['words'].values())}\t"
                     f"{' '.join(top)}\t{' '.join(ents)}\n")

    edges = []
    # vocab edges (cosine)
    for i in range(N):
        for j in range(i + 1, N):
            sh = set(nodes[i]["vec"]) & set(nodes[j]["vec"])
            cos = sum(nodes[i]["vec"][t] * nodes[j]["vec"][t] for t in sh)
            if cos >= 0.05:
                ptr = sorted(sh, key=lambda t: nodes[i]["vec"][t]*nodes[j]["vec"][t], reverse=True)[:6]
                edges.append(("vocab", round(cos,3), nodes[i]["id"], nodes[j]["id"], ptr))
    # entity edges (shared named entities, weighted by count)
    for i in range(N):
        for j in range(i + 1, N):
            sh = set(nodes[i]["entities"]) & set(nodes[j]["entities"])
            sh = {e for e in sh if len(e) >= 4}            # drop tiny acronyms
            if len(sh) >= 2:
                w = sum(min(nodes[i]["entities"][e], nodes[j]["entities"][e]) for e in sh)
                ptr = sorted(sh, key=lambda e: min(nodes[i]["entities"][e], nodes[j]["entities"][e]), reverse=True)[:8]
                edges.append(("entity", w, nodes[i]["id"], nodes[j]["id"], ptr))
    # xref edges: page mentions + section/subsection-name mentions
    for nd in nodes:
        for pg, c in nd["pages"].items():
            if pg in own_pages and pg != nd["page"]:
                edges.append(("xref", c, nd["id"], f"{pg}:*", [pg]))
        for nm, target in catalog.items():
            if target.split(":")[0] == nd["page"] and target == nd["id"]:
                continue
            c = nd["text"].count(nm)
            if c and target != nd["id"]:
                edges.append(("xref", c, nd["id"], target, [f"“{nm}”"]))

    order = {"xref":0, "entity":1, "vocab":2}
    edges.sort(key=lambda x: (order[x[0]], -x[1]))
    with open(os.path.join(REFS, "graph", "edges.tsv"), "w") as fh:
        fh.write("type\tweight\tsection_a\tsection_b\tshared_pointers\n")
        for t, w, a, b, ptr in edges:
            fh.write(f"{t}\t{w}\t{a}\t{b}\t{' '.join(ptr)}\n")

    ec = Counter(t for t,*_ in edges)
    print(f"nodes: {N}   edges: vocab={ec['vocab']} entity={ec['entity']} xref={ec['xref']}")
    print("\n# sample ENTITY edges (rare-connector overlap the plain TF-IDF missed):")
    for t,w,a,b,ptr in [e for e in edges if e[0]=="entity"][:12]:
        print(f"  {w:>3}  {a:34s} <-> {b:34s} | {' '.join(ptr[:6])}")
    print("\n# sample XREF edges (manual pointing at itself):")
    for t,w,a,b,ptr in [e for e in edges if e[0]=="xref"][:14]:
        print(f"  {w:>3}  {a:40s} -> {b:30s} | {' '.join(ptr)}")

if __name__ == "__main__":
    main()
