#!/usr/bin/env python3
"""Verify model-proposed terms against the actual section text (the no-intent gate).

Reads refs/graph/haiku_raw.txt (=== <section file> === then terms), and for each
term checks presence in that file:
  PRESENT     exact case-insensitive substring
  REFORMATTED not exact, but alphanumeric-only form matches (hyphen/underscore/
              spacing normalization, e.g. SUN_KEYBOARD_HACK vs SUNKEYBOARDHACK)
  ABSENT      not found either way -> dropped (paraphrase or injected)

Only PRESENT/REFORMATTED terms are kept (written to refs/graph/haiku_terms.tsv).
This turns the model from "interpreter" into "pointer the text confirms".
"""
import os, re, sys
from collections import Counter

ROOT = os.path.join(os.path.dirname(__file__), "..")
RAW  = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "refs", "graph", "haiku_raw.txt")
OUT  = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "refs", "graph", "haiku_terms.tsv")
alnum = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())

def parse(path):
    cur, out = None, {}
    for ln in open(path):
        ln = ln.rstrip("\n")
        m = re.match(r"^=== (.+) ===$", ln)
        if m:
            cur = m.group(1).strip(); out[cur] = []
        elif cur and ln.strip():
            out[cur].append(ln.strip())
    return out

def main():
    blocks = parse(RAW)
    rows, summary = [], []
    tot = Counter()
    for secfile, terms in blocks.items():
        text = open(os.path.join(ROOT, secfile), errors="replace").read()
        tl, ta = text.lower(), alnum(text)
        absent = []
        for t in terms:
            if t.lower() in tl:
                status = "PRESENT"
            elif len(alnum(t)) >= 3 and alnum(t) in ta:
                status = "REFORMATTED"
            else:
                status = "ABSENT"; absent.append(t)
            tot[status] += 1
            if status != "ABSENT":
                rows.append((secfile, t, status))
        summary.append((secfile, len(terms), absent))

    with open(OUT, "w") as fh:
        fh.write("section_file\tterm\tstatus\n")
        for sf, t, s in rows:
            fh.write(f"{sf}\t{t}\t{s}\n")

    n = sum(tot.values())
    print(f"terms: {n}   PRESENT={tot['PRESENT']}  REFORMATTED={tot['REFORMATTED']}  "
          f"ABSENT={tot['ABSENT']}  (kept {n-tot['ABSENT']}/{n} = "
          f"{100*(n-tot['ABSENT'])//n}%)")
    print("\n# ABSENT (dropped — paraphrase or not literally in section):")
    for sf, _, absent in summary:
        if absent:
            print(f"  {sf.split('/')[-1]:46s} {', '.join(absent)}")

if __name__ == "__main__":
    main()
