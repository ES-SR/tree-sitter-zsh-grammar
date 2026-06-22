# Deep-read synthesis — bridge from cluster maps to grammar.js

All grammar-bearing sections of the manual are now deep-read into per-cluster structural
maps (verbatim forms + `page:line` citations, no imposed taxonomy). Sample citations
grep-verified accurate. This file is the index + the **cross-cluster** findings that only
appear when the maps are read together — these drive the grammar's architecture.

## The maps
| cluster | file | regime |
|---|---|---|
| command/control-flow skeleton | `regime_b_map.md` | B (spine) |
| parameter expansion `${...}` | `parameter_expansion_map.md` | A |
| filename generation / globbing | `filename_generation_map.md` | A |
| history expansion `!`…`^…^` | `history_expansion_map.md` | A |
| arithmetic evaluation `(( ))` | `arithmetic_map.md` | A/seam |
| conditional expressions `[[ ]]` | `conditional_expressions_map.md` | A/seam |
| minor expansions (proc/cmd/arith/brace/filename) | `minor_expansions_map.md` | A (seams) |
| prompt expansion `%…` | `prompt_expansion_map.md` | A (string mini-lang) |
| quoting + aliasing | `quoting_aliasing_map.md` | cross-cutting |
| explicit ordering/precedence | `ordering_inventory.md` | — (precedence source) |

## CROSS-CLUSTER FINDING 1 — the shared MODIFIER sub-grammar
The `:h :t :r :e :s/l/r/ :& :g :q :Q :l :u :x :p :a :A :c :P ...` modifier set is ONE grammar
reused in three contexts (flagged independently by the history, parameter-expansion, and
filename-generation reads):
- history expansion (its defining home) — `history_expansion_map.md`
- parameter expansion, applied at Rule 7 — `ordering_inventory.md §4`, `parameter_expansion_map.md`
- glob qualifier tails (`(#q....:s/a/b/)`) — `filename_generation_map.md`
→ **Grammar decision:** factor a single `_modifier` rule, with per-context restrictions
(`:p` history-only; `f/F/w/W` param-only; `:x` not in param-expansion). Do NOT write it three
times. This is the modifier-layer analog of the Regime-A "shared options" binding.

## CROSS-CLUSTER FINDING 2 — external-scanner candidates (overloaded openers)
Every cluster surfaced a construct that needs context the CFG can't see — consolidated here so
the scanner is designed once (per locked decision, deferred until pure-grammar gains slow, but
these are the known targets):
- `(#` triple-overload: globbing-flags `(#i)`, counted-repeat `(#cN,M)`, qualifiers `(#q…)` — next-char disambiguation. (`filename_generation_map.md`)
- `((` vs `( (`: arithmetic command vs nested subshell — "until a full statement is parsed" (`zshmisc:545`, quoting/aliasing + arithmetic maps).
- `[` overload in arithmetic: `[#base]` output-marker vs `[base]n` legacy literal vs array `[subscript]` — hinges on `#`. (`arithmetic_map.md`)
- balanced-delimiter scanning: parameter-expansion arg-flags `(l.fill.)` and glob flag bodies `e`/`+`/`o` with `[ { <` matching — not a clean CFG. (`parameter_expansion_map.md`, `filename_generation_map.md`)
- here-documents: `<<word` … closing-line match; word-quoting changes inner expansion. (`regime_b_map.md` I/O)
- `${(...)name}` flag run vs trailing operators co-occurrence ordering — implied, not a stated production. (`parameter_expansion_map.md` open-Q)
- prompt `%(x.t.f)` arbitrary separator + recursive nesting. (`prompt_expansion_map.md`)
- **aliasing is lexical / pre-parse** (`zshmisc:505`, ordering §3): alias expansion happens
  while reading input, before the grammar sees tokens — it CANNOT live in grammar.js. Either a
  scanner concern or out-of-scope for the static parser (note for measurement: aliased input
  may simply not parse as the alias target — acceptable).

## CROSS-CLUSTER FINDING 3 — unresolved precedence (method gap)
Precedence may come ONLY from the manual's explicit statements (method rule). Status:
- **arithmetic** — fully stated, two ladders (default + C_PRECEDENCES). `ordering_inventory §6`. ✅
- **glob pattern operators** — fully stated. `ordering_inventory §5`. ✅
- **`${...}` rule pipeline** — fully stated (25 rules). `ordering_inventory §4`. ✅
- **sublist `&&`/`||`** — stated: equal precedence, left-assoc (`zshmisc:49`). ✅
- **conditional-expression `&& || ! ( )`** — **RESOLVED** (`ordering_inventory.md §11`). Manual
  states none (confirmed by full grep); resolved by testing zsh 5.9.1: **`!` > `&&` > `||`,
  left-assoc, `( )` grouping**. Marked IMPLEMENTATION-DETERMINED (not spec) — to be flagged as
  such in `grammar.js`. Opposite of command sublists (`&&`/`||` equal per `zshmisc:49`). ✅

## CONSOLIDATED SEAM GRAPH (the grammar's rule-reference edges)
From the maps, the inter-cluster references the grammar must wire:
- `simple_command` words/assignments → **the whole expansion pipeline** (master seam, `ordering §1`).
- `for ((`, `(( ))`, `repeat word`, `$(( ))`, array `[sub]`, param `(#)` char-eval → **arithmetic**.
- `case` patterns, `[[ = ]]` RHS, parameter pattern-ops (`#`,`%`,`/`), glob qualifiers → **filename-generation pattern grammar**.
- `[[ exp ]]` → **conditional expressions**.
- process/command/arith substitution operands (`<(…)`,`$(…)`,`$((…))`) → **list (regime B)** / arithmetic.
- history `:s` LHS (with HIST_SUBST_PATTERN), conditional `=~` → external pattern/regex engines.
- shared `_modifier` rule (Finding 1) across history / param / qualifiers.
- PROMPT_SUBST → prompt strings re-enter param/command/arith expansion.

## OPTION LAYER (syntax-changing switches, consolidated from all maps)
Orthogonal context that changes WHICH grammar applies (model as flags, per ASSESSMENT):
EXTENDED_GLOB, KSH_GLOB, SH_GLOB, KSH_ARRAYS, RC_EXPAND_PARAM, SH_WORD_SPLIT, GLOB_SUBST,
MULTIBYTE, BARE_GLOB_QUAL, NUMERIC_GLOB_SORT, GLOB_DOTS, C_PRECEDENCES, C_BASES, OCTAL_ZEROES,
IGNORE_BRACES / IGNORE_CLOSE_BRACES, BRACE_CCL, MAGIC_EQUAL_SUBST, EQUALS, SH_FILE_EXPANSION,
NOMATCH, SHORT_LOOPS / SHORT_REPEAT, NULLCMD-family, POSIX_* , PROMPT_SUBST/BANG/PERCENT,
RE_MATCH_PCRE, BASH_REMATCH, RC_QUOTES, POSIX_ALIASES, ALIAS_FUNC_DEF, HIST_SUBST_PATTERN,
BANG_HIST, CSH_JUNKIE_HISTORY. (Full per-construct attribution in the individual maps.)

## READINESS FOR grammar.js
- **Ready to draft now** (forms + precedence fully sanctioned): Regime-B spine & command
  fan-out; redirection; arithmetic operators; glob pattern operators; brace/command/process/
  filename expansion forms; parameter-expansion forms (processing order known, co-occurrence
  production to be pinned by tests); quoting forms.
- **Draft with a recorded assumption:** conditional-expression operator precedence (Finding 3).
- **Defer to external scanner:** Finding 2 list (per locked decision — stub in grammar first).
- **Out of static-parser scope:** lexical alias expansion (Finding 2, last item).

Suggested first grammar.js increment: the Regime-B spine + command fan-out with every seam as a
named-but-minimal stub (bare `_arithmetic`, `_pattern`, `_conditional`, `parameter_expansion`,
etc.), so it builds and can be measured against the corpus immediately, then flesh out seams
cluster-by-cluster using these maps.
