# Explicit-ordering inventory

The ONLY sanctioned source of precedence/order for the grammar is the manual's own
explicit ordering statements. This file collects every such statement, verbatim, with
citations (`page:line`). Nothing here is inferred — only quoted. Derived precedence in
`grammar.js` must trace back to an entry here.

Pages are the `refs/*.txt` extractions (`man --nh --nj | col -bx`, zsh 5.9.1).

---

## 1. Master expansion order (the top-level pipeline) — `zshexpn:7–37`

> The following types of expansions are performed in the indicated order in five steps:
>
> **History Expansion** — This is performed only in interactive shells.
> **Alias Expansion** — Aliases are expanded immediately before the command line is parsed…
> **Process Substitution / Parameter Expansion / Command Substitution / Arithmetic Expansion / Brace Expansion**
>   — These five are performed in left-to-right fashion. On each argument, any of the five
>   steps that are needed are performed one after the other. Hence … all the parts of
>   parameter expansion are completed before command substitution is started. After these
>   expansions, all unquoted occurrences of the characters '\', ''' and '"' are removed.
> **Filename Expansion** — If the SH_FILE_EXPANSION option is set, the order … is modified …
>   filename expansion is performed immediately after alias expansion, preceding the set of
>   five expansions mentioned above.
> **Filename Generation** — … commonly referred to as globbing, is always done last.

Order (default): History → Alias → {Process Sub, Parameter, Command Sub, Arithmetic, Brace}
(L-to-R, completed per-stage per-argument) → Filename Expansion → Filename Generation.
**Option switch:** `SH_FILE_EXPANSION` moves Filename Expansion to just after Alias.
The five middle expansions are a *seam group* — important: parameter expansion fully
completes before command substitution begins, etc.

## 2. History expansion internal structure — `zshexpn:60–70`

> The first character is followed by an optional event designator … and then an optional
> word designator …; if neither of these designators is present, no history expansion occurs.
> … History expansions do not nest.

Internal order: `event-designator` then `word-designator` then modifiers (modifiers shared
with §7). History expansion **does not nest**, and runs before all other expansion.

## 3. Alias expansion placement — `zshmisc:505`

> Alias expansion is done on the shell input before any other expansion except history
> expansion.

Consistent with §1. (Aliasing is lexical — "while text is being read", `zshoptions:1297`.)

## 4. Parameter Expansion internal Rules (25 ordered steps) — `zshexpn:~1300–1495`

The manual numbers these explicitly ("1. … 25."). Verbatim step names + the operative clause:

1.  **Nested substitution** — innermost `${…${…}…}` first; each nested level undergoes all
    single-word substitutions (not filename generation). (`:1300–1332`)
2.  **Internal parameter flags** — typeset-family flags (-L -R -Z -u -l) applied to value. (`:1334`)
3.  **Parameter subscripting** — `${var[3]}`; *subscripts evaluated left to right*; nested
    subscripts apply to prior result. (`:1348–1358`)
4.  **Parameter name replacement** — `(P)` at outermost level only. (`:1360`)
5.  **Double-quoted joining** — array in `"…"` w/o `(@)`/`#` joined by first char of `$IFS`
    (or `(j)`). (`:1371`)
6.  **Nested subscripting** — remaining (nested-substitution) subscripts. (`:1380`)
7.  **Modifiers** — trailing `#` `%` `/` (poss. doubled) or `:...` modifiers (shared w/ §7). (`:1389`)
8.  **Character evaluation** — `(#)` flag, numeric→character. (`:1395`)
9.  **Length** — `${#var}` length. (`:1399`)
10. **Forced joining** — `(j)` / implied join before split. (`:1403`)
11. **Simple word splitting** — `(s)`/`(f)`/`=` , else `SH_WORD_SPLIT` on `$IFS`;
    *takes place at all levels of a nested substitution*. (`:1411`)
12. **Case modification** — `(L)`/`(U)`/`(C)`. (`:1422`)
13. **Escape sequence replacement** — first `(g)`, then `(%)` family. (`:1426`)
14. **Quote application** — `(q)`/`(Q)`. (`:1430`)
15. **Directory naming** — `(D)`. (`:1434`)
16. **Visibility enhancement** — `(V)`. (`:1437`)
17. **Lexical word splitting** — `(z)`/`(Z)`; distinct from rule 11 (no `$IFS`). (`:1441`)
18. **Uniqueness** — `(u)`. (`:1449`)
19. **Ordering** — `(o)`/`(O)`. (`:1453`)
20. **RC_EXPAND_PARAM** — `^` flag / RC_EXPAND_PARAM option. (`:1457`)
21. **Re-evaluation** — `(e)` re-examines for new param/cmd/arith substitutions. (`:1463`)
22. **Padding** — `(l.fill.)`/`(r.fill.)`. (`:1468`)
23. **Semantic joining** — rejoin to single word w/ first char of IFS where required. (`:1472`)
24. **Empty argument removal** — unquoted zero-length args elided. (`:1481`)
25. **Nested parameter name replacement** — `(P)` if rule 4 didn't apply. (`:1491`)

This is the master rule for the `${...}` sub-grammar's operator ordering.

## 5. Filename-generation pattern-operator precedence — `zshexpn:1961–1969`

> The precedence of the operators given above is (highest) '^', '/', '~', '|' (lowest); the
> remaining operators are simply treated from left to right as part of a string, with '#' and
> '##' applying to the shortest possible preceding unit (i.e. a character, '?', '[...]',
> '<...>', or a parenthesised expression).

Per-operator precedence notes (corroborating):
- `x|y` — "lower precedence than any other"; alternatives tried L-to-R. (`:1905`)
- `^x` — "higher precedence than '/'". (`:1911`)
- `x~y` — "lower precedence than any operator except '|'". (`:1916`)
- `x#` / `x##` — "high precedence"; `12#` ≡ `1(2#)` not `(12)#`. (`:1923–1936`)

So pattern op precedence (high→low): `#`/`##` (closure, binds shortest unit) > `^` > `/`
> `~` > `|`. All require `EXTENDED_GLOB` except `/` and `|`.

## 6. Arithmetic operator precedence — `zshmisc:1483–1534`

Default (decreasing precedence), verbatim grouping (`:1485–1502`):
`+ - ! ~ ++ --` > `<< >>` > `&` > `^` > `|` > `**` > `* / %` > `+ -` > `< > <= >=`
> `== !=` > `&&` > `|| ^^` > `? :` > assignment (`= += …`) > `,` (comma).

> Note the precedence of the bitwise AND, OR, and XOR operators. (`:1506`)

**Option switch `C_PRECEDENCES`** (`:1508–1530`) reorders to C-like:
`unary` > `**` > `* / %` > `+ -` > `<< >>` > `< > <= >=` > `== !=` > `&` > `^` > `|`
> `&&` > `^^` > `||` > `? :` > assignment > `,`.

> Note the precedence of exponentiation in both cases is below that of unary operators,
> hence '-3**2' evaluates as '9', not '-9'. (`:1532`)
Short-circuit: `&& || &&= ||=`; ternary evaluates only one branch (`:1504`).

## 7. Modifier / glob-qualifier chaining order — `zshexpn:2580–2584`

> The ordinary qualifier '.' is applied first, then the colon modifiers in order from left
> to right.

History/expansion modifiers (the `:h :t :r :e :s :& :g …` set, shared by §2-step-7 and §4):
applied left to right.

## 8. Subscript evaluation order — `zshexpn:1351`, `zshparam:448`

> Subscripts are evaluated left to right; subsequent subscripts apply to the scalar or array
> value yielded by the previous subscript. (`zshexpn:1351`)
> innermost subscript first, as each expansion is encountered left to right (`zshparam:448`)

## 9. Redirection evaluation order — `zshmisc:801`

> As redirections are evaluated in order, when the >&1 is encountered the standard output is
> set to the file output…

Redirections are applied left-to-right in source order. (MULTIOS: the word after a
redirection operator is also globbed, `zshmisc:805`.)

## 10. Brace expansion vs filename generation — `zshexpn:1604`

> … and */bar before filename generation takes place.

Brace expansion precedes filename generation (consistent with §1: Brace is in the
middle-five group, Filename Generation is last). Individual chars in `{…}` ranges are
sorted into character order (`zshexpn:1594`).

## 11. Conditional-expression operator precedence — ⚠ IMPLEMENTATION-DETERMINED (not manual-stated)

**Provenance differs from every entry above.** The CONDITIONAL EXPRESSIONS section
(`zshmisc:1607–1842`) defines the combinator forms `( exp )` (`:1776`), `! exp` (`:1779`),
`exp1 && exp2` (`:1781`), `exp1 || exp2` (`:1784`) but states NO precedence/associativity for
them — confirmed by a full `precedence` grep across all pages (only sublist §-`zshmisc:49`,
arithmetic §6, glob §5 are stated). The worked example `[[ ( -f foo || -f bar ) && $report = y* ]]`
(`:1837`) only *implies* it via parenthesization.

Resolved by testing the reference implementation (zsh 5.9.1), since the manual is silent:
- `[[ 1 = 1 || 1 = 1 && 1 = 2 ]]` → **true** ⇒ `&&` binds **tighter** than `||`
  (parses `A || (B && C)`, not `(A || B) && C`).
- `[[ 1 = 2 && 1 = 1 || 1 = 1 ]]` → **true** ⇒ consistent (`(A&&B) || C`).
- `[[ ! 1 = 1 && 1 = 2 ]]` → **false** ⇒ `!` is **highest** (binds the operand: `(!A) && B`).

**Conditional precedence (high→low): `!` > `&&` > `||`, with `( )` grouping.** Associativity is
not truth-observable for boolean `&&`/`||`; adopt **left** (matches sublist `:49` and tree-sitter
`prec.left` convention). NOTE: this is the OPPOSITE of command-context sublists, where `&&`/`||`
are EXPLICITLY *equal* precedence (`zshmisc:49`) — `[[ ]]` and command lists are distinct grammars.
This entry must be marked in `grammar.js` as implementation-derived, not spec-derived.

---

## Cross-cutting option switches that change ordering/precedence
(these belong to the orthogonal "modifier layer" from ASSESSMENT.md, but they specifically
mutate ORDER, so are listed here for the precedence model)

- `SH_FILE_EXPANSION` — moves Filename Expansion earlier (§1).
- `C_PRECEDENCES` — reorders arithmetic operators (§6).
- `SH_WORD_SPLIT` — enables implicit word splitting at rule 11 (§4).
- `RC_EXPAND_PARAM` — rule 20 behavior (§4).
- `EXTENDED_GLOB` — gates the `^ ~ # ##` pattern operators (§5).
- `KSH_GLOB` — enables `@( *( +( ?( !(` operators (§5, `zshexpn:1938`).

## What this gives the grammar
Three independent precedence ladders that the grammar must encode as explicit
operator-precedence chains (tree-sitter `prec`/`prec.left`/`prec.right`):
  (a) arithmetic expression operators (§6),
  (b) filename-generation pattern operators (§5),
  (c) the `${...}` rule pipeline (§4) — largely a *processing* order, not a parse-precedence,
      but it fixes which syntactic markers may co-occur and bind tighter.
Plus three *sequencing* facts (not parse precedence, but structural): the master expansion
pipeline (§1), redirection order (§9), L-to-R subscript/modifier chaining (§7,§8).
