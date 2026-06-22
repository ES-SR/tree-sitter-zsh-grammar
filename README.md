# tree-sitter-zsh

A [tree-sitter](https://tree-sitter.github.io/) grammar for the **Z shell (zsh)**, written
**from scratch from the zsh manual** — not a fork of tree-sitter-bash.

> **Status:** early but already useful. **91.2% of entries parse with no error node** on a
> 16,445-entry corpus of real-world zsh history (≈96% of the *syntactically valid* subset —
> see [Coverage](#coverage)). The command/control-flow skeleton is structured for real; the
> expansion/glob interiors are permissive stubs being fleshed out cluster by cluster.

## Why from scratch

A prior attempt forked tree-sitter-bash and plateaued around 58% clean parse on the same
corpus. zsh's syntax diverges from bash in ways that fight a bash-shaped grammar (short loop
forms, `[[ ]]` and `(( ))` brace bodies, anonymous functions, glob flags `(#i)`, `${(flags)…}`
parameter forms, MULTIOS, …), and the inherited bash external scanner was a large part of the
ceiling. The zsh manual, by contrast, is a precise and internally consistent specification, so
this grammar is **derived from the manual**: structure follows zsh's own grammar terminology and
documented order of operations, never an imposed taxonomy. The analysis trail lives in
[`refs/`](#the-manual-analysis-trail).

## Project layout

```
grammar.js                  the grammar (the primary artifact)
src/
  scanner.c                 external scanner (here-documents)
  parser.c                  generated — do not edit
  grammar.json, node-types.json, tree_sitter/   generated
tree-sitter.json            grammar manifest
tools/
  grammar_coverage.py       coverage / regression harness (run before & after every change)
  ts_zsh.py                 ctypes binding to the locally-built parser.so
  man_structure.zsh, *.py   the manual-analysis tooling that produced refs/
corpus.hist                 16,445-entry real-world zsh history corpus (the test bed)
refs/                       the manual deep-read: structural maps + precedence inventory
```

## Building

Requires the `tree-sitter` CLI (≥0.26) and a recent `node` (used by `tree-sitter generate`),
plus a C compiler. Node is often not on `PATH`; point at it explicitly:

```sh
export PATH="$HOME/.nvm/versions/node/v26.3.0/bin:$PATH"   # adjust to your node
tree-sitter generate
cc -O2 -fPIC -shared -I src src/parser.c src/scanner.c -o parser.so
```

> **Note:** `src/scanner.c` **must** be included in the compile — the grammar declares external
> tokens (here-documents) that live there. Omitting it produces link errors at load time.

## Coverage

The harness parses every entry in `corpus.hist` and reports two things:

```sh
python3 tools/grammar_coverage.py
python3 tools/grammar_coverage.py --samples 20   # also print failing samples
```

- **clean-entry rate** — fraction of entries that parse with **no** `ERROR`/`MISSING` node.
- **node ERROR rate** (micro = pooled over all nodes, macro = mean of per-entry rates) — a
  *lower bound on wrongness*: with no gold trees we can only prove a node **is** an error, not
  that a non-error node is structurally correct. Lower is better.

Because the corpus is raw history it contains genuinely malformed commands (typos, abandoned
edits) that a correct grammar *should* reject. Partitioning with zsh's own syntax checker
(`zsh -n -c "$entry"`) shows that of the entries we currently fail, well over half are
genuinely invalid; the **valid** failures are the real headroom.

### Regression workflow

Coverage is the objective gate. The established loop for any grammar change:

1. Snapshot per-entry results to a pickle (errflag + node counts) **before** the change.
2. Make the change; rebuild.
3. Snapshot **after**, and diff: count **newly-clean** vs **newly-broken** entries.

A change ships only when newly-broken is zero (or limited to provably zsh-invalid input). The
aggregate clean-rate alone is not trusted — node-error *micro* is non-monotonic (it can rise on
an already-broken entry that now parses deeper before collapsing), so per-entry A/B diffs plus
the macro rate and the full-collapse count are the signals that matter.

## Design

The grammar splits along the two loosely-coupled regimes the manual analysis surfaced:

- **Regime B — the command / control-flow skeleton** (`list → sublist → pipeline → command`,
  the complex commands, redirection). This is structured **for real**, following zsh's own
  grammar terms and its documented precedence. Includes: pipelines with `!`/`time`/`coproc`
  prefixes, `&&`/`||` sublists, all the complex commands and their **short brace-body forms**
  (`if … { }`, `while … { }`, `for x ( … ) { }`), `case`/`select`, anonymous and multi-name
  functions, `[[ … ]]` conditionals with real operator precedence, `(( … ))` arithmetic
  commands, and redirection (here-strings, here-documents, MULTIOS-style operators).

- **Regime A — expansions, glob patterns, quoting** (`${…}`, `$(…)`, `$((…))`, `(#…)` glob
  flags, glob qualifiers, brace expansion). These are **permissive stubs**: named rules that
  *accept* the construct without an error, but do not yet impose the full internal structure
  (e.g. the 25-rule `${…}` pipeline is accepted as balanced text with nested expansions
  recognised, not decomposed into its operators). They are being filled in cluster by cluster.

Precedence values trace to explicit ordering statements in the manual
([`refs/ordering_inventory.md`](refs/ordering_inventory.md)); where the manual is genuinely
silent (e.g. conditional-expression operator precedence) the resolution was determined by
testing zsh itself and is flagged in the grammar as *implementation-determined*.

### The external scanner

Most nesting (`${…}` inside `$(…)` inside `${…}`, arbitrarily deep) needs **no** scanner —
that is what the parser's stack is for. The scanner exists only for constructs that are not
regular at the token level. Currently that is **here-documents** (`src/scanner.c`): the body
delimiter is chosen at runtime and the body is deferred past the rest of the line, a non-regular
dependency the generated lexer cannot express. The scanner maintains a serialized queue of
pending here-documents and supports the expansion-bearing body, raw (quoted-delimiter) bodies,
`<<-` indentation stripping, same-line pipe/`&&`/`||` tails, bare `<<EOF` (no command), and
here-documents nested inside `$(…)`. Here-strings (`<<<`) are a fixed operator and stay in the
grammar.

Other documented scanner candidates (the `(#…)` triple-overload, balanced-delimiter `${(s:…:)…}`
flag bodies, lexical aliasing) remain approximated in the grammar for now, per the standing
decision to defer C scanner work until pure-grammar gains slow.

## Scope and known limitations

- Regime-A interiors are accepted but not fully structured (see above).
- `${(l:EXPR:…)…}`-style flag bodies with runtime delimiters are matched opaquely — the
  arithmetic/string sub-fields between delimiters are not yet recognised as such.
- Multiple here-documents on one line (`cat <<A <<B`) are not yet handled (single per command).
- Glob qualifiers and `(#…)` flags are recognised as tokens/groups, not decomposed into their
  full sub-grammar.

## The manual analysis trail

[`refs/`](refs/) contains the source-of-truth analysis the grammar is built from — verbatim
manual extracts, an indentation-based structural map, a coarse→fine connection graph, the
explicit-ordering inventory, and per-cluster deep-read maps (parameter expansion, filename
generation, arithmetic, conditional expressions, quoting, …). Start with
[`refs/DEEP_READ_SYNTHESIS.md`](refs/DEEP_READ_SYNTHESIS.md) and
[`refs/regime_b_map.md`](refs/regime_b_map.md).

## License

MIT.
