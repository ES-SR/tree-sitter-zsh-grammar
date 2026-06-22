#!/usr/bin/env python3
"""Regression harness for the from-scratch zsh tree-sitter grammar.

Parses every entry in corpus.hist with the locally-built grammar and reports
the clean-parse rate plus a breakdown of the first-error construct category.
This is the objective gate for grammar work — run before/after a change to see
real coverage movement on a 16k-entry real-world zsh corpus.

Usage:
  python3 tools/grammar_coverage.py                # summary
  python3 tools/grammar_coverage.py --samples 20   # also show N failing samples
"""
import re, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from collections import Counter

HIST = os.path.join(os.path.dirname(__file__), '..', 'corpus.hist')

def load_entries(path):
    """zsh EXTENDED_HISTORY ': <ts>:<dur>;<cmd>', multiline via trailing '\\'
    (escaped-newline marker, stripped to recover the real command)."""
    hdr=re.compile(r'^: (\d+):(\d+);(.*)$')
    entries=[]; cur=None; buf=[]; prev_cont=False
    def flush():
        nonlocal cur,buf
        if cur is not None: entries.append('\n'.join(buf))
        cur=None; buf=[]
    with open(path,encoding='utf-8',errors='replace') as f:
        for raw in f:
            line=raw.rstrip('\n'); m=hdr.match(line)
            cont=(len(line)-len(line.rstrip('\\')))%2==1
            if m and not prev_cont:
                flush(); cur=1; seg=m.group(3); buf=[seg[:-1] if cont else seg]
            elif cur is not None:
                buf.append(line[:-1] if cont else line)
            prev_cont=cont
        flush()
    return entries

def first_error(root):
    if root.type in ('ERROR','MISSING'): return root
    for c in root.children:
        r=first_error(c)
        if r: return r
    return None

def score_tree(root):
    """Count ERROR nodes: a node is 'bad' if it is ERROR/MISSING or sits inside
    an ERROR/MISSING subtree (once the parser enters recovery, the subtree below
    is unreliable). Returns (bad_named, total_named, bad_all, total_all).
    We report bad/total as a LOWER BOUND on how wrong the parse is — with no gold
    tree we cannot prove a node is correct, only that it is (not) an error."""
    bn=tn=ba=ta=0
    stack=[(root, False)]
    while stack:
        node, in_err = stack.pop()
        bad = in_err or node.type=='ERROR' or node.missing
        ta+=1
        if bad: ba+=1
        if node.named:
            tn+=1
            if bad: bn+=1
        for c in node.children:
            stack.append((c, bad))
    return bn,tn,ba,ta

def categorize(sig):
    s=sig.strip().split('\n')[0]
    if re.search(r'\[\([A-Za-z]+\)', s): return 'subscript-flag'
    if re.search(r'\$\(\(|\(\( ', s): return 'arithmetic (( ))'
    if '(#' in s: return 'pattern-flag (#..)'
    if s.startswith('function ') or s.startswith('() '): return 'func-body-inner'
    if '${' in s[:6]: return 'expansion'
    if s.startswith('|'): return 'leading-pipe fragment'
    if '<<' in s: return 'heredoc'
    if '[[' in s: return '[[ test ]]'
    return 'other'

def main():
    show = 0
    if '--samples' in sys.argv:
        i=sys.argv.index('--samples'); show=int(sys.argv[i+1])
    from ts_zsh import Parser
    entries=load_entries(HIST)
    P=Parser(); bad=0; cats=Counter(); samples=[]
    sum_bn=sum_tn=sum_ba=sum_ta=0   # pooled (micro)
    macro_named=macro_all=scored=0  # mean of per-entry error rates (macro)
    for t in entries:
        tree,root=P.parse(t)
        bn,tn,ba,ta=score_tree(root)
        sum_bn+=bn; sum_tn+=tn; sum_ba+=ba; sum_ta+=ta
        if tn:
            macro_named+=bn/tn; macro_all+=ba/ta; scored+=1
        e=first_error(root)
        if e:
            bad+=1; cats[categorize(e.text)]+=1
            if len(samples)<show: samples.append((t, e.text.split('\n')[0][:60]))
        P.free(tree)
    P.close()
    n=len(entries)
    print(f"grammar=zsh (from-scratch)  entries={n}")
    print(f"clean-entry={n-bad} ({100*(n-bad)/n:.1f}%)  error-entry={bad} ({100*bad/n:.1f}%)")
    print("node ERROR rate (lower bound on wrongness; lower is better):")
    print(f"  named: micro={100*sum_bn/sum_tn:.2f}%  ({sum_bn}/{sum_tn} err)"
          f"   macro={100*macro_named/scored:.2f}%")
    print(f"  all:   micro={100*sum_ba/sum_ta:.2f}%  ({sum_ba}/{sum_ta} err)"
          f"   macro={100*macro_all/scored:.2f}%")
    print("error categories:")
    for c,k in cats.most_common():
        print(f"  {k:6}  {c}")
    if samples:
        print("\nfailing samples (entry | first-error text):")
        for t,et in samples:
            print(f"  {t.splitlines()[0][:70]!r}  ->  {et!r}")

if __name__=='__main__':
    main()
