#!/usr/bin/env python3
"""Assess the R1+R2 connection map: clusters, centrality, cross-cutting connectors."""
import os, re
from collections import defaultdict, Counter

G = os.path.join(os.path.dirname(__file__), "..", "refs", "graph")

def load_edges(path, has_type):
    es = []
    for ln in open(path):
        f = ln.rstrip("\n").split("\t")
        if f[0] in ("type", "shared", "weight"):
            continue
        if has_type:
            t, w, a, b, *_ = f; es.append((a, b, float(w), t))
        else:
            w, a, b, *_ = f; es.append((a, b, float(w), "merged"))
    return es

# reference/catalog sections are universal connectors (they describe everything) ->
# exclude from structural clustering to reveal the construct subsystems.
REF = {
  "zshoptions:DESCRIPTION OF OPTIONS", "zshoptions:SINGLE LETTER OPTIONS",
  "zshoptions:OPTION ALIASES", "zshoptions:SPECIFYING OPTIONS",
  "zshbuiltins:SHELL BUILTIN COMMANDS",
  "zshparam:PARAMETERS USED BY THE SHELL", "zshparam:PARAMETERS SET BY THE SHELL",
}
# ---- STRUCTURAL clusters from vocab edges among CONSTRUCT sections ----
THRESH = 0.15
edges = [e for e in load_edges(os.path.join(G, "edges.tsv"), has_type=True)
         if e[3] == "vocab" and e[2] >= THRESH and e[0] not in REF and e[1] not in REF]
adj = defaultdict(set); deg = Counter()
for a, b, w, _ in edges:
    adj[a].add(b); adj[b].add(a); deg[a]+=1; deg[b]+=1
print(f"(structural graph: vocab cosine >= {THRESH}, reference catalogs excluded)")

seen, comps = set(), []
for n in adj:
    if n in seen: continue
    stack, comp = [n], []
    while stack:
        x = stack.pop()
        if x in seen: continue
        seen.add(x); comp.append(x); stack += [y for y in adj[x] if y not in seen]
    comps.append(sorted(comp))
comps.sort(key=len, reverse=True)

print("=== CLUSTERS (connected components of the enriched R1 graph) ===")
for i, c in enumerate(comps):
    print(f"\ncluster {i+1} ({len(c)} sections):")
    for n in sorted(c, key=lambda x: -deg[x]):
        print(f"    deg{deg[n]:<2} {n}")

# ---- centrality: most-connected hubs ----
print("\n=== TOP HUBS (degree in enriched graph) ===")
for n, d in deg.most_common(10):
    print(f"   {d:>2}  {n}")

# ---- cross-cutting connectors (entities shared across many sections) ----
inv = defaultdict(set)
for ln in open(os.path.join(G, "nodes.tsv")):
    f = ln.rstrip("\n").split("\t")
    if f[0] == "page": continue
    node = f"{f[0]}:{f[1]}"
    for e in (f[4].split() if len(f) > 4 else []):
        if len(e) >= 4: inv[e].add(node)
spread = sorted(inv.items(), key=lambda kv: len(kv[1]), reverse=True)
print("\n=== CROSS-CUTTING CONNECTORS (entities spanning the most sections) ===")
for t, ns in spread[:18]:
    print(f"   {len(ns):>2}  {t}")
