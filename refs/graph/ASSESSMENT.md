# Connection-map assessment (R1 + R2)

Built coarse→fine, deterministic + grep-verified-model layers. Tools:
`section_keywords.py` (R1), `r2_sections.py` (R2), `verify_terms.py`, `merge_graph.py`,
`assess_graph.py`, `factor_catalogs.py`.

## What the graph showed

1. **The raw graph is a hairball** — entity (option) overlap puts 31/45 sections in one
   component; even vocab≥0.18 leaves 34/45 merged. Cause: the **reference catalogs**
   (`DESCRIPTION OF OPTIONS`, `SHELL BUILTIN COMMANDS`, the `PARAMETERS` lists) are
   universal connectors — they describe nearly every construct.

2. **Factoring the catalogs out by UNFOLDING** (Stallings-style: replace each catalog
   super-hub with its individual option/param entries, attach each entry only to the
   constructs that use it, re-project onto constructs with weight Σ 1/df(entry)) dissolves
   the hairball and reveals the structure.

## The structure (two loosely-coupled regimes + a cross-cutting layer)

- **Regime A — expansion / pattern machinery.** Bound by shared OPTIONS. Cluster:
  `PARAMETER EXPANSION` (+flags), `FILENAME GENERATION` (+glob-operators/globbing-flags/
  glob-qualifiers), `HISTORY EXPANSION`, `CONDITIONAL EXPRESSIONS`, `EXPANSION OF PROMPT
  SEQUENCES`. Options ARE the connective tissue here.
- **Regime B — command / control-flow skeleton.** Barely references options; bound by
  GRAMMAR TERMS (list, sublist, pipeline, command, word). Members: `SIMPLE COMMANDS &
  PIPELINES`, `COMPLEX COMMANDS`, `ALTERNATE FORMS`, `RESERVED WORDS`, `FUNCTIONS`/
  `ANONYMOUS`/`AUTOLOADING`, `PRECOMMAND MODIFIERS`, `JOBS`, and the I/O sub-cluster
  (`REDIRECTION`/`MULTIOS`/`OPENING FD`). (Seen via R1 vocab + R2 edges, not options.)
- **The seam:** the two regimes meet at exactly one place — a command's **words undergo
  expansion**. That word↔expansion interface is the key joint in the grammar.
- **Cross-cutting modifier layer (NOT structural):** `EXTENDED_GLOB`, `KSH_ARRAYS`,
  `GLOB_SUBST`, `IFS`, `MULTIBYTE`, `GLOB_DOTS`, `KSH_GLOB`, `NOMATCH`, `SH_WORD_SPLIT`,
  `POSIX*`. These are global behavior modifiers (mostly options) that change HOW constructs
  parse/expand. Several gate whole sub-grammars (e.g. `EXTENDED_GLOB` enables the extended
  pattern operators; `KSH_ARRAYS` changes subscript base; `SH_WORD_SPLIT` toggles splitting).
  Model them as an orthogonal flag/context layer, not as nodes in any cluster.
- **Clean small subsystems** that fell out on their own: Aliasing, Prompt expansion, I/O.

## Implications for the grammar

- Decompose into **(A) expansion/pattern** and **(B) command/control-flow**, co-designed,
  joined at the word/expansion seam — consistent with "work sections simultaneously".
- Treat options as a **cross-cutting context layer**; the ones that gate sub-grammars are
  exactly the overloaded-character / context switches identified earlier (e.g. EXTENDED_GLOB).
- Precedence must still come ONLY from the manual's explicit ordering statements
  (expansion order, glob Precedence, arithmetic precedence) — the pending ordering inventory.
