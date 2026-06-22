#!/usr/bin/env python3
"""R2 (finer resolution): split pages into indentation-tree nodes.

Faithful to "structure = indentation only": per page, distinct leading-space
widths are ranked into levels. level-1 lines that match SECTION_RE are sections;
level-2 lines are subsection boundaries; level-3+ is body. A node is:
  - each level-2 block (subsection heading + its deeper-indented body), or
  - a level-1 section that has no level-2 children (kept whole), or
  - the preamble body of a section before its first level-2 child.

`list`  -> print the R2 node manifest (id, words, line range)
`graph` -> deterministic connection analysis (vocab + entity edges) at R2 grain
"""
import os, re, sys, math
from collections import Counter

REFS = os.path.join(os.path.dirname(__file__), "..", "refs")
PAGES = ["zshmisc", "zshexpn", "zshparam", "zshoptions", "zshbuiltins"]
SECTION_RE = re.compile(r"^[A-Z][A-Z0-9 &/_-]*[A-Z]$")

def levels_for(lines):
    widths = sorted({len(l) - len(l.lstrip(" ")) for l in lines if l.strip()})
    rank = {w: i + 1 for i, w in enumerate(widths)}
    return [rank.get(len(l) - len(l.lstrip(" ")), 0) if l.strip() else 0 for l in lines]

def r2_nodes(page):
    lines = open(os.path.join(REFS, page + ".txt"), errors="replace").read().splitlines()
    lvl = levels_for(lines)
    nodes, cur_sec, cur_sub, buf, start = [], None, None, [], 1
    def flush(end):
        if cur_sec and buf:
            name = f"{page}:{cur_sec}" + (f" › {cur_sub}" if cur_sub else "")
            nodes.append([name, start, end, "\n".join(buf)])
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if lvl[i-1] == 1 and SECTION_RE.match(s) and "MANUAL" not in s.upper():
            flush(i-1); cur_sec, cur_sub, buf, start = s, None, [], i
        elif lvl[i-1] == 2 and cur_sec:
            flush(i-1); cur_sub, buf, start = s, [], i
        elif cur_sec:
            buf.append(line)
    flush(len(lines))
    return nodes

def main():
    alln = []
    for p in PAGES:
        alln += r2_nodes(p)
    alln = [n for n in alln if len(Counter(re.findall(r"[a-z_][a-z0-9_]+", n[3].lower()))) and
            sum(Counter(re.findall(r"[a-z_][a-z0-9_]+", n[3].lower())).values()) >= 20]
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        print(f"R2 nodes: {len(alln)}")
        for name, s, e, body in alln:
            w = len(re.findall(r"[a-z_][a-z0-9_]+", body.lower()))
            print(f"  {w:5d}  L{s}-{e}  {name}")
        return
    if len(sys.argv) > 1 and sys.argv[1] == "dump":
        d = os.path.join(REFS, "sections_r2"); os.makedirs(d, exist_ok=True)
        slug = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:50]
        for name, s, e, body in alln:
            page, rest = name.split(":", 1)
            parts = rest.split(" › ")
            fn = f"{page}__{slug(parts[0])}" + (f"--{slug(parts[1])}" if len(parts) > 1 else "") + ".txt"
            open(os.path.join(d, fn), "w").write(body + "\n")
            print(f"{name}\t{d}/{fn}")
        return
    graph(alln)

WORD_RE   = re.compile(r"[a-z_][a-z0-9_]+")
ENTITY_RE = re.compile(r"\b[A-Z][A-Z0-9]{2,}(?:_[A-Z0-9]+)*\b")

def graph(nodes):
    ids   = [n[0] for n in nodes]
    words = [Counter(WORD_RE.findall(n[3].lower())) for n in nodes]
    ents  = [Counter(ENTITY_RE.findall(n[3])) for n in nodes]
    N = len(nodes)
    df = Counter()
    for w in words: df.update(w.keys())
    idf = {t: math.log(N/df[t]) for t in df}
    vecs = []
    for w in words:
        tot = sum(w.values())
        v = {t:(c/tot)*idf[t] for t,c in w.items()}
        nrm = math.sqrt(sum(x*x for x in v.values())) or 1.0
        vecs.append({t:x/nrm for t,x in v.items()})
    edges = []
    for i in range(N):
        for j in range(i+1,N):
            sh = set(vecs[i]) & set(vecs[j])
            cos = sum(vecs[i][t]*vecs[j][t] for t in sh)
            if cos >= 0.08:
                ptr = sorted(sh, key=lambda t: vecs[i][t]*vecs[j][t], reverse=True)[:5]
                edges.append(("vocab", round(cos,3), ids[i], ids[j], ptr))
            she = {e for e in set(ents[i])&set(ents[j]) if len(e)>=4}
            if len(she) >= 2:
                w = sum(min(ents[i][e],ents[j][e]) for e in she)
                ptr = sorted(she, key=lambda e: min(ents[i][e],ents[j][e]), reverse=True)[:5]
                edges.append(("entity", w, ids[i], ids[j], ptr))
    edges.sort(key=lambda x:(x[0],-x[1]))
    os.makedirs(os.path.join(REFS,"graph","r2"), exist_ok=True)
    with open(os.path.join(REFS,"graph","r2","edges.tsv"),"w") as fh:
        fh.write("type\tweight\tnode_a\tnode_b\tshared\n")
        for t,w,a,b,ptr in edges:
            fh.write(f"{t}\t{w}\t{a}\t{b}\t{' '.join(ptr)}\n")
    ec = Counter(t for t,*_ in edges)
    print(f"R2 nodes={N}  edges: vocab={ec['vocab']} entity={ec['entity']}")
    def show(title, pred, key, k=8):
        print(f"\n# {title}")
        sel = sorted([e for e in edges if pred(e)], key=key, reverse=True)[:k]
        for t,w,a,b,ptr in sel:
            print(f"  {t[:3]} {w:>5}  {a.split(':',1)[1]:42.42s} <-> {b.split(':',1)[1]:42.42s} | {' '.join(ptr[:4])}")
    inhub = lambda h: (lambda e: h in e[2] and h in e[3])
    show("intra PARAMETER EXPANSION", inhub("PARAMETER EXPANSION"), lambda e:e[1])
    show("intra FILENAME GENERATION", inhub("FILENAME GENERATION"), lambda e:e[1])
    show("cross-page subsection edges (different pages)",
         lambda e: e[2].split(':')[0]!=e[3].split(':')[0] and e[0]=='entity', lambda e:e[1], 10)

if __name__ == "__main__":
    main()
