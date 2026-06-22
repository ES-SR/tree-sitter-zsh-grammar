#!/usr/bin/env python3
"""Merge verified model terms into the coarse graph and quantify the model's add.

Combines, per node (L1 section):
  - script connectors : ALL_CAPS entities from nodes.tsv
  - model connectors  : verified terms from haiku_terms.tsv (PRESENT/REFORMATTED)
Builds connector-overlap edges over the union, and reports how many connectors and
edges the model contributed that the deterministic pass did not have.

Outputs refs/graph/edges_enriched.tsv (connector-overlap edges, union sources).
"""
import os, re
from collections import defaultdict, Counter

ROOT = os.path.join(os.path.dirname(__file__), "..")
G = os.path.join(ROOT, "refs", "graph")
slug = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

# slug -> node id, from manifest
node_of = {}
for ln in open(os.path.join(G, "sections.tsv")):
    p, sec, *_ = ln.rstrip("\n").split("\t")
    if p == "page":
        continue
    node_of[(p, slug(sec))] = f"{p}:{sec}"

def file_to_node(secfile):
    base = secfile.split("/")[-1][:-4]            # drop .txt
    p, sl = base.split("__", 1)
    return node_of.get((p, sl))

script_conn = defaultdict(set)   # node -> {entities}
for ln in open(os.path.join(G, "nodes.tsv")):
    f = ln.rstrip("\n").split("\t")
    if f[0] == "page":
        continue
    node = f"{f[0]}:{f[1]}"
    ents = f[4].split() if len(f) > 4 else []
    script_conn[node] |= {e for e in ents if len(e) >= 4}

model_conn = defaultdict(set)    # node -> {verified terms}
for ln in open(os.path.join(G, "haiku_terms.tsv")):
    f = ln.rstrip("\n").split("\t")
    if f[0] == "section_file":
        continue
    node = file_to_node(f[0])
    if node:
        model_conn[node].add(f[1])

nodes = set(script_conn) | set(model_conn)
union = {n: script_conn[n] | model_conn[n] for n in nodes}

# connector -> nodes (inverted index) over the union
inv = defaultdict(set)
for n, cs in union.items():
    for c in cs:
        inv[c].add(n)

# edges by shared connectors
edges = []
nl = sorted(nodes)
for i in range(len(nl)):
    for j in range(i + 1, len(nl)):
        sh = union[nl[i]] & union[nl[j]]
        sh = {c for c in sh if len(inv[c]) <= 12}      # drop ubiquitous connectors
        if len(sh) >= 2:
            edges.append((len(sh), nl[i], nl[j], sorted(sh, key=lambda c: len(inv[c]))[:8]))
edges.sort(reverse=True)
with open(os.path.join(G, "edges_enriched.tsv"), "w") as fh:
    fh.write("shared\tsection_a\tsection_b\tconnectors\n")
    for w, a, b, sh in edges:
        fh.write(f"{w}\t{a}\t{b}\t{' '.join(sh)}\n")

# quantify model contribution
model_only_terms = Counter()
for n in nodes:
    for t in model_conn[n] - script_conn[n]:
        model_only_terms[t] += 1
print(f"nodes={len(nodes)}  union connectors={len(inv)}  enriched edges={len(edges)}")
print(f"connectors only from model (not in script entities): {len(model_only_terms)}")
print("\n# top model-contributed connectors (by #sections sharing them):")
for t, c in model_only_terms.most_common(20):
    if c >= 2:
        print(f"  {c:>2}  {t}")
print("\n# strongest enriched edges:")
for w, a, b, sh in edges[:18]:
    print(f"  {w}  {a:40s} <-> {b:40s} | {' '.join(sh[:6])}")
