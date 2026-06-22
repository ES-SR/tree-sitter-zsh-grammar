# Parameter expansion map — the `$`/`${...}` cluster

The parameter-expansion cluster (zshexpn **PARAMETER EXPANSION**, `:458–1536`) is one of
the five middle expansions of the master pipeline (`ordering_inventory.md` §1). It is
introduced by `$` (`:459`) and has a brace-free short context and a brace `${...}` context.
This file maps the manual's OWN forms verbatim with `zshexpn:line` citations. It is a
structural map, not yet `grammar.js`. Internal processing order is NOT re-derived here — it
lives in `ordering_inventory.md` §4 (the 25 Rules, `:1305–1495`); cited where relevant.

The manual is explicit that "the full rules are complicated and are noted at the end"
(`:483`) and that this section defines the operators/flags, with §4 fixing their order.
"In the following descriptions, 'word' refers to a single word substituted on the command
line, not necessarily a space delimited word." (`:496`)

## A. Expansion forms (the `name`-position + trailing-operator productions)

All `name` slots accept: a parameter name; OR a nested `${...}`; OR a `$(...)` command
substitution — "If a ${...} type parameter expression or a $(...) type command substitution
is used in place of name above, it is expanded first and the result is used as if it were
the value of name" (`:789`). Each `name` or nested `${...}` may also be followed by a
subscript `[...]` (`:795`).

| form | source | meaning (terse) |
|---|---|---|
| `$name` / `${name}` | `:499` | value of `name`; braces required if followed by letter/digit/`_`, or for complex forms (`:500`) |
| `${+name}` / `$+name` | `:517` | `1` if `name` is a set parameter, else `0` |
| `${name-word}` | `:521` | if `name` set → value, else `word` |
| `${name:-word}` | `:522` | if `name` set **and non-null** → value, else `word`; `name` may be omitted (`:524`) |
| `${name+word}` | `:527` | if `name` set → `word`, else nothing |
| `${name:+word}` | `:528` | if `name` set and non-null → `word`, else nothing |
| `${name=word}` | `:532` | if `name` unset → set to `word`; then substitute value |
| `${name:=word}` | `:533` | if `name` unset or null → set to `word`; then value |
| `${name::=word}` | `:534` | unconditionally set `name` to `word`; then value |
| `${name?word}` | `:540` | if `name` set → value, else print `word` & exit |
| `${name:?word}` | `:541` | if `name` set and non-null → value, else print `word` & exit; `word` omittable (`:545`) |
| `${name#pattern}` | `:558` | delete shortest match of `pattern` at **start** |
| `${name##pattern}` | `:559` | delete largest match of `pattern` at **start** |
| `${name%pattern}` | `:566` | delete shortest match of `pattern` at **end** |
| `${name%%pattern}` | `:567` | delete largest match of `pattern` at **end** |
| `${name:#pattern}` | `:574` | if `pattern` matches value → empty; on arrays removes matching elements ((M) inverts) |
| `${name:\|arrayname}` | `:580` | remove elements of `name` that are present in array `arrayname` (name, not contents) |
| `${name:*arrayname}` | `:588` | retain elements present in both `name` and `arrayname` (intersection) |
| `${name:^arrayname}` | `:593` | zip `name` & `arrayname`, length of **shorter** |
| `${name:^^arrayname}` | `:594` | zip, length of **longer** (inputs repeated) |
| `${name:offset}` | `:619` | substring/subarray from `offset` (compat with other shells; ≈ `$name[start,end]`) |
| `${name:offset:length}` | `:620` | substring/subarray, `length` chars/elements |
| `${name/pattern/repl}` | `:687` | replace **first** longest match of `pattern` with `repl` |
| `${name//pattern/repl}` | `:688` | replace **all** matches |
| `${name:/pattern/repl}` | `:689` | replace only if `pattern` matches **entire** string |
| `${#spec}` | `:727` | length: chars of result, or element count if array (`:728`) |
| `${^spec}` / `${^^spec}` | `:742` | turn RC_EXPAND_PARAM on / off for `spec` (doubled = off) |
| `${=spec}` / `${==spec}` | `:759` | force SH_WORD_SPLIT for `spec` (doubled = off) |
| `${~spec}` / `${~~spec}` | `:772` | turn GLOB_SUBST on / off for `spec` (doubled = off) |
| `${(flags)name}` | `:481`,`:807` | flag list (see §C); `(` must directly follow `{` (`:808`) |

Notes on the trailing-pattern forms:
- `:-`-family (`- := ? + = :: ` etc.) test/substitute. SH_WORD_SPLIT and `=`-flag splitting
  of `word` can be overridden with standard shell quoting in `word`, but NOT `s:string:`
  splitting (`:549–552`).
- For `#`,`##`,`%`,`%%`,`:#`,`/`-family: when `name` is an array and substitution is unquoted
  (or `(@)` / `name[@]` used), match/replace is per-element (`:554`,`:710`).
- In `/`-replacement, `pattern` may itself begin with `#` (anchor start), `%` (anchor end),
  or `#%` (whole string) — but these anchors are inactive inside a substituted parameter
  (`:700–708`). Empty `repl` lets the final `/` be omitted; final `/` quoted by one `\`
  (`:703–706`).
- `${name:offset}` interacts with `:-`: a negative offset's `-` "may not appear immediately
  after the :" (collides with `${name:-word}`) — insert a space (`:668`). `offset`/`length`
  may not begin with an alphabetic char or `&` (collides with history modifiers) (`:670`).
  `offset`/`length` undergo scalar-assignment substitutions then arithmetic evaluation
  (`:651`) — a SEAM to arithmetic.

## B. Combination / ordering of leading single-char operators

These single-char operators sit **before** the name inside braces and may stack:
`${(flags)...}`, then `^`/`^^`, `=`/`==`, `~`/`~~`, `#` (length), `+`.
The manual's explicit constraint: "Note that '^', '=', and '~', below, must appear to the
left of '#' when these forms are combined." (`:733`). Order of operations among ALL of them
is governed by `ordering_inventory.md` §4 (e.g. length is rule 9, RC_EXPAND_PARAM is rule
20, word splitting is rule 11). The brace-free exceptions that work without `{}` (only if
KSH_ARRAYS unset): a single subscript or colon modifiers after the name, or `^ = ~ # +`
before the name (`:504–508`).

## C. Parameter-expansion flags `(...)` — the `${(flags)...}` list (`:807–1296`)

Opening `(` must **directly** follow `{`; flags run to the matching `)` (`:808`). Repeats
need not be consecutive: `(q%q%q)` = `(%%qqq)` (`:811`).

### Argument-less flags (`:814–1073`)
| flag | char | effect | source |
|---|---|---|---|
| `#` | `#` | eval words as numeric expr → character codes (distinct from non-paren `#`) | `:814` |
| `%` | `%` | expand `%` prompt escapes; doubled = full prompt expansion | `:822` |
| `@` | `@` | in `"..."`, array elements → separate words (≡ `"${foo[@]}"`) | `:828` |
| `A` | `A` | force array result; doubled `AA` = associative on assignment | `:834` |
| `a` | `a` | sort in array index order; `Oa` = reverse index order | `:853` |
| `b` | `b` | backslash-quote only pattern-special chars (for GLOB_SUBST/`${~...}`) | `:858` |
| `c` | `c` | with `${#name}`, count total chars of array (joined w/ spaces) | `:876` |
| `C` | `C` | capitalize words (alnum runs) | `:882` |
| `D` | `D` | substitute leading dir by name (reverse of `~`); SEAM to FILENAME EXPANSION | `:886` |
| `e` | `e` | single-word shell expansions (param/cmd-sub/arith) on result; nestable | `:893` |
| `f` | `f` | split result at newlines; shorthand for `ps:\n:` | `:898` |
| `F` | `F` | join array with newline; shorthand for `pj:\n:` | `:901` |
| `i` | `i` | sort case-insensitively; combine w/ `n`/`O` | `:913` |
| `k` | `k` | substitute keys of assoc array; with subscripts force indices/keys | `:915` |
| `L` | `L` | lower-case result | `:923` |
| `n` | `n` | sort decimal integers numerically; combine w/ `i`/`O` | `:925` |
| `-` | `-` | as `n` but handle leading minus as negative integer | `:933` |
| `o` | `o` | sort ascending (lexical default) | `:938` |
| `O` | `O` | sort descending | `:944` |
| `P` | `P` | interpret value of `name` as a further parameter name (indirection) | `:948` |
| `q` | `q` | backslash-quote shell-special; `qq`/`qqq`/`qqqq`/`q-`/`q+` variants | `:968` |
| `Q` | `Q` | remove one level of quotes | `:991` |
| `t` | `t` | type-description string of the parameter | `:993` |
| `u` | `u` | keep only first occurrence of each unique word | `:1040` |
| `U` | `U` | upper-case result | `:1042` |
| `v` | `v` | with `k`, substitute key+value; with subscripts force values | `:1044` |
| `V` | `V` | make special chars visible | `:1049` |
| `w` | `w` | with `${#name}`, count words; `s` sets delimiter | `:1051` |
| `W` | `W` | as `w` but count empty words between repeated delimiters | `:1054` |
| `X` | `X` | report parse errors from `Q`/`e`/`#` flags & pattern forms | `:1057` |
| `z` | `z` | split result via shell parsing (honors quoting); very late (`:1067`) | `:1061` |
| `0` | `0` | split result on null bytes; shorthand for `ps:\0:` | `:1072` |

### Argument-taking flags (`:1075–1218`)
Delimiter is `:` or a matched pair `(...)` `{...}` `[...]` `<...>`; multi-arg flags must
surround **each** argument with a matched pair (`:1075–1079`).

| flag | form | effect | source |
|---|---|---|---|
| `p` | `p` | recognize print-builtin escapes in following flags' string args; `$var` form allowed | `:1081` |
| `~` | `~` | treat strings inserted by following flags as patterns; repeat toggles; scope = this `()` | `:1098` |
| `j` | `j:string:` | join array words with `string` (before `s`/SH_WORD_SPLIT) | `:1111` |
| `l` | `l:expr::string1::string2:` | left-pad to width `expr`; optional fill strings | `:1116` |
| `m` | `m` | (with `l`/`r`/`#`, MULTIBYTE) use char display width; repeat = glyph count | `:1145` |
| `r` | `r:expr::string1::string2:` | right-pad (mirror of `l`) | `:1161` |
| `s` | `s:string:` | force field splitting at `string` (multi-char = whole seq); empty = per-char | `:1171` |
| `Z` | `Z:opts:` | as `z` with option letters `(Z+c+)` `(Z+C+)` `(Z+n+)` | `:1190` |
| `_` | `_:flags:` | reserved for future use; currently no valid flags | `:1214` |

### Match-form flags — only with `${...#...}` / `${...%...}` (some with `/`) (`:1220–1296`)
"The S, I, and * flags may also be used with the ${.../...} forms." (`:1221`)
| flag | form | effect | source |
|---|---|---|---|
| `S` | `S` | substring match (`#`/`%`); with `/` = non-greedy | `:1223` |
| `I` | `I:expr:` | match the `expr`th match | `:1258` |
| `*` | `*` | enable EXTENDED_GLOB for `/`-substitution | `:1283` |
| `B` | `B` | include index of beginning of match | `:1286` |
| `E` | `E` | include index one past end of match | `:1288` |
| `M` | `M` | include matched portion | `:1292` |
| `N` | `N` | include length of match | `:1294` |
| `R` | `R` | include unmatched portion (the Rest) | `:1296` |

Note: with `/`-forms the flags `M R B E N` are "not useful" (`:713`); `S I *` are.

## D. Trailing operators (the operator alphabet inside `${...}`)
Grouped by the syntactic slot they occupy after the name:
- **test/default operators:** `-` `:-` `+` `:+` `=` `:=` `::=` `?` `:?` (each optionally
  with leading `:` for the null-test variant) — `:521–541`.
- **pattern-removal operators:** `#` `##` (start), `%` `%%` (end), `:#` (whole, elide) — `:558–574`.
- **array-set operators:** `:|` `:*` `:^` `:^^` — `:580–594`.
- **substring operators:** `:offset` `:offset:length` (the `:` then numeric/arith) — `:619`.
- **replacement operators:** `/` `//` `:/` with inner `/repl`; inner pattern anchors `#` `%` `#%` — `:687–708`.
- **leading operators (before name):** `(flags)` `#`(length) `^` `^^` `=` `==` `~` `~~` `+` — see §B.
- **subscript:** `[...]` (zshparam Array Parameters; see §F) — `:795`.
- **colon modifiers:** `:h :t :r :e :s/.../.../ :& :g …` — shared with History Expansion
  Modifiers; e.g. `${i:s/foo/bar/}` (`:491–494`). This is a SEAM to the Modifiers grammar.

## E. Nesting rules (`:789–805`, §4 rule 1)
- `${...}` and `$(...)` may stand in for `name`; expanded inside-out (`:789`,`:1305`).
- `${${foo#head}%tail}` deletes head then tail (`:792`).
- Flags do NOT propagate up; each level returns scalar/array per its own flags (`:1311`).
- `${${foo}}` behaves exactly as `${foo}` unless `(P)` present (`:1318`).
- Double quotes may surround a nested expression: only the inner part is quoted; quotes nest:
  `"${(@f)"$(foo)"}"` has two quote sets (`:799–805`).
- Each nested level undergoes all single-word substitutions (cmd-sub, arith, filename exp ~/=)
  but NOT filename generation (`:1324`); e.g. `${${:-=cat}:h}` (`:1328`).
- Subscript may follow each `name` / nested `${...}` (`:795`). Subscripts evaluated L-to-R
  (`:1351`; `ordering_inventory.md` §8).

## F. Subscript / `[...]` forms
The section delegates subscript notation to zshparam Array Parameters (`:460`,`:796`). Inside
`${...}`, relevant cited subscript tokens: `[@]` (`:478`,`:829`), `[*]` (`:665`,`:920`),
`[1,2]` ranges (`:830`), `[3]` (`:1350`), chained `[1][2]` / `[2,4][2]` (`:1353`). Special
cases: `(k)`/`(v)` alter subscript result (`:917`,`:1044`); `(k)` may NOT combine with
subscript ranges (`:919`); with KSH_ARRAYS a `[*]`/`[@]` is needed for whole-array ops
(`:920`). Full subscript grammar is OWNED BY zshparam — a SEAM, not enumerated here.

## G. Option-gates (options that CHANGE the parse/syntax)
- **KSH_ARRAYS** (`:505`,`:510`,`:637`,`:663`,`:920`) — when SET: brace-free exceptions
  (`:504`) do NOT apply (braces required); `$array` → first element only; offset 0 always
  scalar; `${foo[*]:3}` needed for array elements. Major syntactic gate.
- **POSIX_IDENTIFIERS** (`:736`) — when SET, braces required for `${#name}` length on simple
  names (`$#-`, `$#*` change meaning).
- **SH_WORD_SPLIT** (`:464`,`:514`,`:761`,`:1418`) — enables implicit IFS word-splitting of
  unquoted param expansions (rule 11). The `=`/`==` operators force/unforce it locally.
- **RC_EXPAND_PARAM** (`:744`,`:1457`) — element-wise combination with surrounding text
  (`foo${xx}bar`); `^`/`^^` toggle it locally (rule 20). Converts to brace-expansion form.
- **GLOB_SUBST** (`:697`,`:774`) — makes expansion result a pattern; `~`/`~~` toggle locally;
  also affects whether `$opat` in `/`-replacement is a pattern.
- **EXTENDED_GLOB** — gated on by the `*` match-flag for `/`-substitution (`:1283`).
- **MULTIBYTE** (`:648`,`:819`,`:1133`,`:1146`) — offset/length & padding/`#` count chars vs
  bytes; the `(#)` flag treats >127 as Unicode; the `m` flag uses display width.
- **PROMPT_PERCENT / PROMPT_SUBST / PROMPT_BANG** (`:825`) — affect doubled `%%` flag.
- **INTERACTIVE_COMMENTS** (`:1064`) — referenced for `(z)`/`(Z)` comment handling.

## H. Seams (where parameter expansion hands off)
1. **Patterns** in `#/##/%/%%/:#//` and `:^` etc. → FILENAME GENERATION pattern grammar
   ("the form of the pattern is the same as that used for filename generation", `:486`).
2. **`name`-position nested `$(...)`** → COMMAND SUBSTITUTION (`:789`, next section `:1537`).
3. **offset/length** and `(#)` flag → ARITHMETIC EVALUATION (`:651`,`:814`).
4. **colon modifiers** `${i:s/foo/bar/}` etc. → History-Expansion Modifiers grammar
   (`:491`; `ordering_inventory.md` §7).
5. **`(D)` flag and `~`/`=` in nested levels** → FILENAME EXPANSION (`:886`,`:1327`).
6. **subscripts `[...]`** → zshparam Array Parameters (`:460`,`:796`).
7. **`(e)` / `(P)` flags** re-enter expansion (re-evaluation, indirection) (`:893`,`:948`).
8. **patterns/repl themselves** are subject to parameter/cmd/arith expansion (`:488`).

## What this gives the grammar
- A single `expansion` node fanning into: short `$name`/`$+name`/`$#name` (brace-free,
  KSH_ARRAYS-gated) vs. full `${ ... }`.
- Inside `${}`: an optional leading `(flags)` group, optional stacked leading operators
  (`# ^ ^^ = == ~ ~~ +`, with `# ` rightmost per `:733`), a `name` slot (param | nested
  `${...}` | `$(...)`), optional `[subscript]`, then at most one trailing operator from the
  closed alphabet in §D (test/default | pattern-removal | array-set | substring | replace),
  plus optional trailing colon-modifiers.
- A flag sub-grammar: argless flags (single chars), arg-flags with one of four delimiter
  pairs, match-flags restricted to `#/%//` forms.
- Internal **processing** order is rule §4 (already captured) — not parse precedence, but it
  fixes co-occurrence/positioning (e.g. length `#` outermost, flags before name).
- Six external seams as references to separately-built rules (patterns, cmd-sub, arith,
  modifiers, filename-exp, subscripts).

## Open questions
1. **Exact stacking grammar of leading operators.** The manual constrains only `^ = ~` left
   of `#` (`:733`) and the §4 processing order; it does not give an explicit production for
   how `(flags)`, `# ^ = ~ +` co-occur as a token sequence. Whether all are simultaneously
   legal in one `${...}` (and in what concrete left-to-right text order) is not stated as a
   syntax rule — only as processing order. Needs test-corpus confirmation, not invention.
2. **Whether more than one trailing operator can co-occur** (e.g. substring + modifier, or
   subscript + `#`). `:1380` shows `${foo[2,4][2]}` (chained subscripts) and §4 orders
   modifiers (rule 7) after subscripting (rule 3,6); but the concrete grammar of "name +
   subscript + trailing-op + colon-modifier" sequencing is implied, not stated as one form.
3. **`+` operator brace-free vs `${+name}` placement.** `:507` lists `+` as a *before-name*
   char working without braces, and `:517` gives `${+name}`; the relationship to `${name+word}`
   (after-name `+`) means `+` is overloaded by position — needs care to disambiguate in lexer.
4. **`q` variant tokenization:** `q` `qq` `qqq` `qqqq` `q-` `q+` (`:968–989`) — `q-`/`q+` take
   a trailing sign char, distinct from repetition counting; whether `q` repetition interleaves
   with other flags (`:811` says repeats need not be consecutive) complicates flag tokenizing.
5. **Delimiter pairing for multi-arg flags** (`l`/`r`/`Z`/`g`): manual says any char or a
   matched pair, and each arg needs its own matched pair (`:1075`). The full legal delimiter
   set and nesting interaction with the surrounding `${...}` braces is under-specified here.
6. **`:: =` vs `:=` vs `=`** and the `::=` three-char operator (`:534`) — confirm lexer
   greediness (`::=` must not be read as `:` + `:=`).
