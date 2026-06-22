#!/usr/bin/env python3
"""Factor out the reference catalogs by UNFOLDING (Stallings-style), not excluding.

A reference catalog (DESCRIPTION OF OPTIONS, SHELL BUILTIN COMMANDS, the PARAMETERS
lists) is a FOLDED star: all (construct, entry) relationships collapse into one
super-hub, which over-connects the graph. We UNFOLD it:

  catalog vertex  ->  its individual entries (each option / builtin / param name)
  entry           ->  attached only to the CONSTRUCT nodes that actually use it
  project onto constructs: edge(A,B) = sum over shared entries e of 1/df(e)

so a catalog's information survives as fine-grained mediating leaves. Rare shared
entries => strong structural edges; ubiquitous entries (cross-cutting options) self-
weight toward zero. The catalog super-hub dissolves and construct subsystems emerge.
"""
import os, re
from collections import defaultdict, Counter

REFS = os.path.join(os.path.dirname(__file__), "..", "refs")
SR2 = os.path.join(REFS, "sections_r2")
ENTITY_RE = re.compile(r"\b[A-Z][A-Z0-9]{2,}(?:_[A-Z0-9]+)*\b")

CATALOG_PREFIXES = ("zshoptions__",
                    "zshbuiltins__shell-builtin-commands",
                    "zshparam__parameters-used-by-the-shell",
                    "zshparam__parameters-set-by-the-shell")
def is_catalog(fn): return fn.startswith(CATALOG_PREFIXES)

def node_id(fn):
    base = fn[:-4]
    page, rest = base.split("__", 1)
    parts = rest.split("--")
    sec = parts[0].replace("-", " ").upper()
    return f"{page}:{sec}" + (f"›{parts[1]}" if len(parts) > 1 else "")

def main():
    files = sorted(os.listdir(SR2))
    # ---- unfold catalogs into entry names ----
    # Unfold catalogs into their ALL_CAPS option/param names only — unambiguous,
    # unlike builtin command words which collide with ordinary English (set/file/...).
    entries = set()
    for fn in files:
        if not is_catalog(fn):
            continue
        text = open(os.path.join(SR2, fn), errors="replace").read()
        entries |= set(ENTITY_RE.findall(text))
    entries = {e for e in entries if len(e) >= 3}

    # ---- attach entries to the CONSTRUCT nodes that use them ----
    construct = {}                       # node id -> text
    for fn in files:
        if is_catalog(fn):
            continue
        construct[node_id(fn)] = open(os.path.join(SR2, fn), errors="replace").read()

    refs_of = defaultdict(set)           # node -> entries it references
    for nid, text in construct.items():
        for e in entries:
            patt = r"\b" + re.escape(e) + r"\b"
            if re.search(patt, text):
                refs_of[nid].add(e)
    df = Counter()
    for nid, es in refs_of.items():
        df.update(es)

    # ---- project onto constructs: edge weight = sum 1/df(shared entry) ----
    nodes = sorted(construct)
    edges = []
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            sh = refs_of[nodes[i]] & refs_of[nodes[j]]
            if not sh:
                continue
            w = sum(1.0 / df[e] for e in sh if df[e] >= 2)
            if w >= 0.6:
                top = sorted(sh, key=lambda e: df[e])[:5]
                edges.append((w, nodes[i], nodes[j], top))
    # ---- cluster (connected components of the projected graph) ----
    adj = defaultdict(set); deg = Counter()
    for w, a, b, _ in edges:
        adj[a].add(b); adj[b].add(a); deg[a]+=1; deg[b]+=1
    seen, comps = set(), []
    for n in adj:
        if n in seen: continue
        st, comp = [n], []
        while st:
            x = st.pop()
            if x in seen: continue
            seen.add(x); comp.append(x); st += [y for y in adj[x] if y not in seen]
        comps.append(comp)
    comps.sort(key=len, reverse=True)

    print(f"construct nodes={len(nodes)}  catalog entries unfolded={len(entries)}  "
          f"projected edges(w>=0.6)={len(edges)}")
    print("\n=== CONSTRUCT CLUSTERS (catalogs unfolded & projected away) ===")
    for k, c in enumerate(comps, 1):
        print(f"\ncluster {k} ({len(c)}):")
        for n in sorted(c, key=lambda x: -deg[x]):
            print(f"   deg{deg[n]:<2} {n}")
    iso = [n for n in nodes if n not in adj]
    print(f"\nunclustered ({len(iso)}): " + ", ".join(iso))
    print("\n=== CROSS-CUTTING ENTRIES (highest df = global concerns, self-weighted out) ===")
    for e, c in df.most_common(15):
        print(f"   {c:>2}  {e}")

if __name__ == "__main__":
    main()
