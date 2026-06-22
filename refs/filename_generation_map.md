# Filename generation map — the glob / pattern sub-grammar

This is the **FILENAME GENERATION** cluster of Regime A, entirely in **zshexpn**
(`:1758–2585`). It is "commonly referred to as globbing" and "always done last" in the
master expansion order (`ordering_inventory.md §1`). The cluster is a self-contained
**pattern grammar** that is *reused* by `case`, `[[ = ]]`, and parameter-expansion pattern
operators (the SEAMS, below). This file captures the manual's OWN syntactic forms verbatim
with `zshexpn:line` citations. It is a structural map, not yet `grammar.js`. Precedence is
quoted from the source and cross-checked against `ordering_inventory.md §5`.

## Trigger / framing (`:1758–1775`)

A word becomes a pattern for filename generation if it contains an **unquoted** instance of
one of these chars (`:1759–1760`):

```
*  (  |  <  [  ?                              ; always pattern-triggering (:1759)
^  #                                          ; only if EXTENDED_GLOB set (:1761–1763)
```

> "it is regarded as a pattern for filename generation, unless the GLOB option is unset." (`:1760`)

Result handling, option-gated (`:1765–1769`):
- match → "replaced with a list of **sorted** filenames" (`:1765`).
- no match → error, **unless NULL_GLOB** (word deleted) or **NOMATCH unset** (word left
  unchanged) (`:1766–1769`).

Path/dot rules in **filename generation** specifically (`:1771–1775`):
- `/` "must be matched explicitly" (`:1771`).
- leading `.` (start of pattern or after `/`) must be matched explicitly **unless GLOB_DOTS** (`:1772`).
- no pattern matches `.` or `..` (`:1774`).
- "In other instances of pattern matching, the '/' and '.' are not treated specially." (`:1775`)
  — this is the key SEAM caveat: the grammar is shared, the `/`-special behaviour is not.

---

## (a) Base glob / pattern operators (`:1777–1908`)

Sub-grammar of the always-available pattern atoms (no option gate except where noted).

| form | meaning (verbatim gist) | source |
|---|---|---|
| `*` | "Matches any string, including the null string." | `:1778` |
| `?` | "Matches any character." | `:1780` |
| `[...]` | "Matches any of the enclosed characters." ranges via `-`; leading `-`/`]` matched literally | `:1782–1784` |
| `[^...]` / `[!...]` | "Like [...], except that it matches any character which is **not** in the given set." | `:1873–1876` |
| `<[x]-[y]>` | "Matches any number in the range x to y, inclusive." either bound omittable; `<->` = any number | `:1878–1882` |
| `(...)` | "Matches the enclosed pattern. This is used for grouping." | `:1892` |
| `x\|y` | "Matches either x or y." lowest precedence; `\|` must be inside `(...)`; alts tried L-to-R | `:1905–1908` |

Notes carried verbatim:
- `<0-9>*` trap: longest-match rule means `<0-9>` matches first digit, `*` the rest;
  use `<0-9>[^[:digit:]]*` instead (`:1884–1890`).
- `(...)` grouping **cannot span directories**: "it is an error to have a '/' within a
  group (this only applies for patterns used in filename generation)." (`:1898–1900`)
- Exception: `(pat/)#` "appearing as a complete path segment can match a sequence of
  directories" — e.g. `foo/(a*/)#bar` (`:1900–1903`). This is the recursive-glob seam (§ Recursive Globbing).
- `(...)` parse is modified by **KSH_GLOB** (preceding `@ * + ? !`); **SH_GLOB** "prevents
  bare parentheses from being used in this way, though KSH_GLOB is still available." (`:1893–1896`)

### Character classes inside `[...]` (`:1785–1871`)

`[:name:]` — "the square brackets are additional to those enclosing the whole set", so a
single class char is `[[:alnum:]]` (`:1868–1870`); mixable, e.g. `[[:alpha:]0-9]` (`:1871`).

POSIX/ctype set, locale-sensitive (`:1786–1830`):
`[:alnum:] [:alpha:] [:ascii:] [:blank:] [:cntrl:] [:digit:] [:graph:] [:lower:] [:print:]
[:punct:] [:space:] [:upper:] [:xdigit:]`

Shell-internal set, **not** locale-sensitive (`:1832–1866`):
`[:IDENT:]` (respects POSIX_IDENTIFIERS), `[:IFS:]`, `[:IFSSPACE:]`, `[:INCOMPLETE:]`,
`[:INVALID:]`, `[:WORD:]` (respects WORDCHARS).

---

## (b) EXTENDED_GLOB operators (`:1910–1936`) — gated by **EXTENDED_GLOB**

Each entry below is explicitly tagged "(Requires EXTENDED_GLOB to be set.)".

| form | meaning | precedence note | source |
|---|---|---|---|
| `^x` | "Matches anything except the pattern x." | "higher precedence than '/'" | `:1910–1913` |
| `x~y` | "Match anything that matches x but does not match y." multi: `foo~bar~baz`; in y, `/` & `.` not special | "lower precedence than any operator except '\|'" | `:1915–1921` |
| `x#` | "Matches zero or more occurrences of the pattern x." | "high precedence"; `12#` ≡ `1(2#)` | `:1923–1929` |
| `x##` | "Matches one or more occurrences of the pattern x." | "high precedence"; `12##` ≡ `1(2##)` | `:1931–1936` |

`#`/`##` constraints (`:1925–1936`):
- error for unquoted `#` to follow something "which cannot be repeated": empty string,
  pattern already followed by `##`, or KSH_GLOB parentheses (`!(foo)#` invalid → `*(!(foo))`) (`:1926–1929`).
- "No more than two active '#' characters may appear together." (`:1934`)
- clash warning: `1(2##)` form collides with glob qualifiers, "should therefore be avoided" (`:1935`).

The `^`, `#` chars ALSO act as pattern triggers only under EXTENDED_GLOB (`:1761–1763`).

---

## (c) ksh-like Glob Operators (`:1938–1959`) — gated by **KSH_GLOB**

> "If the KSH_GLOB option is set, the effects of parentheses can be modified by a preceding
> '@', '*', '+', '?' or '!'. This character need **not be unquoted**… but the '(' must be." (`:1939–1941`)

| form | meaning | equivalent | source |
|---|---|---|---|
| `@(...)` | "Match the pattern in the parentheses." | `(...)` | `:1943–1944` |
| `*(...)` | "Match any number of occurrences." | `(...)#` (no recursive dir search) | `:1946–1948` |
| `+(...)` | "Match at least one occurrence." | `(...)##` (no recursive dir search) | `:1950–1952` |
| `?(...)` | "Match zero or one occurrence." | `(\|...)` | `:1954–1955` |
| `!(...)` | "Match anything but the expression in parentheses." | `(^(...))` | `:1957–1959` |

Cross-gate: for ksh **grouping** with globbing flags, "both KSH_GLOB and EXTENDED_GLOB must
be set and the left parenthesis should be preceded by @" (`:2134–2135`).

---

## Precedence (`:1961–1971`) — cross-ref `ordering_inventory.md §5`

> "The precedence of the operators given above is (highest) '^', '/', '~', '|' (lowest);
> the remaining operators are simply treated from left to right as part of a string, with
> '#' and '##' applying to the shortest possible preceding unit (i.e. a character, '?',
> '[...]', '<...>', or a parenthesised expression)." (`:1962–1966`)

Ladder (high → low): `#`/`##` (closure; binds shortest unit) > `^` > `/` > `~` > `|`.
All-string operators (`* ? [...] <...> (...)`) are concatenation, L-to-R.
Of the precedence operators, **`^` and `~` require EXTENDED_GLOB**; `/` and `|` are base.

Context caveat (the SEAM rule, `:1966–1971`):
- `/` may not appear inside `(...)`; `|` must (`:1966–1967`).
- "in patterns used in other contexts than filename generation (for example, in case
  statements and tests within '[[...]]'), a '/' is **not** special" (`:1968–1969`).
- `/` "is also not special after a '~' appearing outside parentheses in a filename pattern" (`:1970–1971`).

---

## (b′) Globbing Flags `(#X)` (`:1973–2140`) — gated by **EXTENDED_GLOB**

> "various flags which affect any text to their right up to the end of the enclosing group
> or to the end of the pattern; they require the EXTENDED_GLOB option. All take the form
> (#X)…" (`:1974–1977`)

Scope = rightward to end of enclosing group / pattern. Flag forms `X` (`:1979–2127`):

| flag | effect | source |
|---|---|---|
| `i` | case insensitive | `:1979` |
| `l` | lowercase-in-pattern matches either case; uppercase still strict | `:1982` |
| `I` | case sensitive; locally negates `i`/`l` | `:1986` |
| `b` | activate backreferences → `$match`/`$mbegin`/`$mend`; **not in filename generation**; only first 9 parens | `:1989–2039` |
| `B` | deactivate backreferences | `:2041` |
| `cN,M` | `{N,M}`-style repetition count; `(#cN)` exact, `(#c,M)` ⇒ N=0, `(#cN,)` no max; **cannot combine with other flags** | `:2044–2052` |
| `m` | set `$MATCH`/`$MBEGIN`/`$MEND` for whole match; **not in filename generation**; must hold at end of pattern | `:2054–2073` |
| `M` | deactivate `m` | `:2075` |
| `anum` | approximate matching, `num` errors allowed (see Approximate Matching) | `:2078–2080` |
| `s`, `e` | local, each alone: `(#s)`=start anchor, `(#e)`=end anchor (≈ `^`/`$`) | `:2082–2105` |
| `q` | flag + rest to `)` ignored by matcher; supports dual glob-qualifier/match use | `:2107–2116` |
| `u` | respect locale for multibyte (needs MULTIBYTE_SUPPORT); overrides MULTIBYTE option | `:2118–2124` |
| `U` | all chars single-byte; opposite of `u`; overrides MULTIBYTE option | `:2126–2127` |

Combination facts (verbatim, `:2129–2140`):
- `(#i)FOOXX` matches `fooxx`; `(#l)FOOXX`, `(#i)FOO(#I)XX`, `((#i)FOOX)X` do not (`:2129–2130`).
- `(#ia2)readme` = case-insensitive `readme` with ≤2 errors (flags combine in one `(#…)`) (`:2131`).
- flags "do not affect letters inside [...] groups": `(#i)[a-z]` still only lowercase (`:2136–2137`).

## Approximate Matching (`:2142–2192`) — driven by the `anum` flag

Four error types (`:2147–2155`): (1) different char, (2) transposition, (3) char missing in
target, (4) extra char in target. One overall error count, but `(#anum)` may be re-scoped
locally and delimited by grouping (`:2178–2185`); exclusions via `~` counted separately and
must be activated separately (`:2171–2176`). Non-literal pattern parts, initial dots, and
slashes must match exactly (`:2161–2167`). This is a *matching-semantics* subsection, not new
syntax — the only syntactic surface is the `(#anum)` flag.

## Recursive Globbing (`:2194–2223`) — relates to **GLOB_STAR_SHORT**

| form | meaning | source |
|---|---|---|
| `(foo/)#` | "matches a path consisting of zero or more directories matching the pattern foo" | `:2195–2196` |
| `**/` | "equivalent to '(*/)#'"; matches current dir too; does NOT follow symlinks | `:2198–2208` |
| `***/` | like `**/` but DOES follow symlinks | `:2209–2210` |

Constraint: "Neither of these can be combined with other forms of globbing within the same
path segment; in that case, the '*' operators revert to their usual effect." (`:2210–2212`)
**GLOB_STAR_SHORT**: if no `/` follows `**`/`***`, treated as if `/` plus further `*` present —
`**.c` ≡ `**/*.c` (`:2214–2223`).

---

## (d) Glob Qualifiers (`:2225–2584`)

> "Patterns used for filename generation may end in a list of qualifiers enclosed in
> parentheses. The qualifiers specify which filenames that otherwise match the given pattern
> will be inserted in the argument list." (`:2226–2228`)

Three recognition syntaxes (option-gated):
1. **BARE_GLOB_QUAL** (`:2230–2235`): trailing `(...)` containing no `|` or `(` (or `~` if
   special) is taken as qualifiers. Force-into-pattern by doubling: `(^x)` → `((^x))`.
2. **EXTENDED_GLOB** form `(#qx)` (`:2237–2253`): must appear at end of pattern; **multiple
   may be chained** (logical AND); recognised "just as long any parentheses contained within
   it are balanced; appearance of '|', '(' or '~' does not negate the effect." Chains even if
   a bare qualifier also ends the pattern: `*(#q*)(.)` (`:2245–2248`). In `[[...]]`, a trailing
   `(#q...)` "indicates that globbing should be performed" — valid even as bare `(#q)`; "does
   not apply to the right hand side of pattern match operators" (`:2249–2253`).

### Qualifier atoms (`:2255–2531`)

File-type / FS:
`/` dir (`:2257`), `F` full (non-empty) dir (`:2259`), `.` plain file (`:2263`), `@` symlink
(`:2265`), `=` socket (`:2267`), `p` named pipe (`:2269`), `*` executable plain file (`:2271`),
`%` device (`:2273`), `%b` block special (`:2275`), `%c` char special (`:2277`).

Permission bits (`:2279–2301`):
`r w x` owner r/w/x; `A I E` group r/w/x; `R W X` world r/w/x; `s` setuid, `S` setgid,
`t` sticky.

Parameterised qualifiers (take an argument / sub-spec):
| form | meaning | source |
|---|---|---|
| `fspec` | files with access rights matching `spec` (octal w/ `= + -`, `?` wildcards; or `[`/`{`/`<`-delimited `u g o a` + `= + -` + `r w x s t` sub-spec list) | `:2303–2340` |
| `estring` | execute delimited shell code; include file if zero status; `REPLY`/`reply` controllable | `:2342–2366` |
| `+cmd` | like `e`, no delimiters; `cmd` = longest alnum/underscore run after `+` | `:2368–2379` |
| `ddev` | files on device `dev` | `:2381` |
| `l[-\|+]ct` | link count `<`/`>`/`=` ct | `:2383–2385` |
| `U` | owned by effective UID | `:2387` |
| `G` | owned by effective GID | `:2389` |
| `uid` | owned by user `id` (number) or delimited name | `:2391–2398` |
| `gid` | like `uid` but group | `:2400` |
| `a[Mwhms][-\|+]n` | accessed n days ago (`-` within, `+` more than); unit specifiers `M w h m s d` | `:2402–2416` |
| `m[Mwhms][-\|+]n` | like `a`, modification time | `:2418–2420` |
| `c[Mwhms][-\|+]n` | like `a`, inode change time | `:2422–2424` |
| `L[+\|-]n` | size `<`/`>`/`=` n bytes; size specifiers `k K m M p P` (`g G t T` on some systems) | `:2426–2440` |

Modifier / global qualifiers:
| form | meaning | source |
|---|---|---|
| `^` | "negates all qualifiers following it" | `:2442` |
| `-` | toggle symlink-vs-target for following qualifiers | `:2444–2447` |
| `M` | set MARK_DIRS for this pattern | `:2449` |
| `T` | append type mark (like LIST_TYPES); overrides M | `:2451` |
| `N` | set NULL_GLOB for this pattern | `:2454` |
| `D` | set GLOB_DOTS for this pattern | `:2456` |
| `n` | set NUMERIC_GLOB_SORT for this pattern | `:2458` |
| `Yn` | short-circuit: at most n filenames; implies `oN` if no `oc` | `:2460–2464` |
| `oc` / `Oc` | sort ascending / descending by `c` ∈ `n L l a m c d N e +` (`oe`/`o+` = shell code) | `:2466–2505` |
| `[beg[,end]]` | subscript selection of matches (array-subscript syntax; math exprs; negative ok) | `:2507–2513` |
| `Pstring` | prepend (or append under `^`) string as separate word; repeatable | `:2515–2531` |

### Qualifier-list combination & chaining (`:2533–2584`)

- "More than one of these lists can be combined, **separated by commas**. The whole list
  matches if at least one of the sublists matches (they are 'or'ed, the qualifiers in the
  sublists are 'and'ed)." (`:2533–2535`)
- Some qualifiers affect **all** matches regardless of sublist: `M T N D n o O` and `[...]`
  subscripts (`:2535–2538`).
- **`:` modifier seam** (`:2540–2548`): "If a ':' appears in a qualifier list, the remainder
  of the expression in parenthesis is interpreted as a modifier (see … 'Modifiers' in …
  'History Expansion'). Each modifier must be introduced by a separate ':'." The result need
  not be an existing file; `(:…)` may follow any existing filename. → SEAM to the history-
  expansion modifier set (`:h :t :r :e :s :& :g …`), shared with `ordering_inventory.md §7`.
- **Chaining order** (`:2580–2584`, = `ordering_inventory.md §7`): "The ordinary qualifier
  '.' is applied first, then the colon modifiers in order from left to right." Example
  `b*.pro(#q:s/pro/shmo/)(#q.:s/builtin/shmiltin/)` → `shmiltin.shmo` (`:2578–2584`).

---

## Option-gates (summary)

| option | gates | source |
|---|---|---|
| `GLOB` | whole mechanism (unset ⇒ no globbing) | `:1760` |
| `EXTENDED_GLOB` | `^x` `x~y` `x#` `x##`; `^`/`#` as triggers; globbing flags `(#…)`; `(#q…)` qualifier syntax | `:1761,:1910,:1976,:2237` |
| `KSH_GLOB` | `@( *( +( ?( !(` | `:1893,:1939` |
| `SH_GLOB` | disables bare `(...)` ksh-style grouping (KSH_GLOB still works) | `:1895` |
| `GLOB_DOTS` | leading-`.` matching; qualifier `D` sets per-pattern | `:1773,:2456` |
| `NULL_GLOB` | no-match ⇒ delete word; qualifier `N` sets per-pattern | `:1767,:2454` |
| `NOMATCH` | unset ⇒ no-match leaves word unchanged | `:1768` |
| `NUMERIC_GLOB_SORT` | numeric sort; qualifier `n` sets per-pattern | `:2458` |
| `BARE_GLOB_QUAL` | trailing `(...)` as qualifiers | `:2230` |
| `GLOB_STAR_SHORT` | `**`/`***` without `/` ⇒ implicit `/*` | `:2214` |
| `POSIX_IDENTIFIERS` | affects `[:IDENT:]` | `:1838` |
| `MULTIBYTE` | default for `u`/`U` flags | `:2121,:2127` |
| `MARK_DIRS` / `LIST_TYPES` | per-pattern via qualifiers `M`/`T` | `:2449,:2451` |

Note: **CASE_GLOB** is listed in the prompt's candidate gate set but does **not** appear in
this section (`:1758–2585`) — see Open questions.

## SEAMS (reuse points of this pattern grammar)

1. **`case` patterns** → the `case word in (pat) …` slot reuses this grammar; `/` not special
   there (`:1968–1969`; regime_b_map.md `:173`).
2. **`[[ = ]]` / `[[ == ]]`** → conditional pattern-match RHS reuses it; `/` not special;
   `(#q…)` indicates globbing but "does not apply to the right hand side of pattern match
   operators" (`:1968,:2249–2253`).
3. **Parameter-expansion pattern operators** (`${var#pat}`, `${var%pat}`, `${var/pat/repl}`,
   `${var//…}`) → reuse the same grammar; backreference (`b`) / match (`m`) flags and `(#s)`/
   `(#e)` are documented in terms of these contexts (`:2014–2018,:2055,:2094–2099`). Seam into
   `ordering_inventory.md §4` (param-expansion rule pipeline).
4. **History-expansion modifiers** (the `:h :t :r …` set) → reused by the `:`-modifier tail of
   a glob-qualifier list (`:2540–2543`; `ordering_inventory.md §7`).
5. **`(pat/)#` / `**/`** recursive form is the only place `/` may appear "inside" a closure —
   structurally a path-segment construct, not a general group.

## Internal structure summary (the cluster's grammar shape)

- **Three nested sub-grammars share one entry symbol `pattern`**: (a) base operators, (b)
  EXTENDED_GLOB operators + `(#…)` flags, (c) KSH_GLOB `X(...)` groups. They are not separate
  languages — they are option-gated *extensions* of one operator-precedence expression.
- **One precedence ladder** governs the operator core: `#`/`##` > `^` > `/` > `~` > `|`, with
  everything else concatenation L-to-R (`:1962–1966`, §5). This is the single `prec` chain the
  grammar must encode for patterns.
- **Glob qualifiers are a distinct trailing sub-grammar**, not part of the pattern precedence
  ladder: a comma-separated OR of AND-ed sublists `(q1q2,q3…)` or chained `(#q…)(#q…)`,
  terminating optionally in a `:`-modifier tail. It only attaches in *filename-generation*
  context, not in the reuse seams.
- **The cluster is gate-stratified**: base layer needs only GLOB; EXTENDED_GLOB and KSH_GLOB
  each unlock disjoint operator sets; SH_GLOB subtracts bare-paren grouping. The grammar will
  likely parse the union and reject/flag gated forms via externals or supertype rules.
- **`(#…)` is overloaded** three ways by leading char: globbing-flag (`(#i)` etc.), counted-
  repetition (`(#cN,M)`), and qualifier (`(#q…)`) — all share the `(#` opener, disambiguated
  by the char after `#`.

## Open questions / ambiguities

1. **CASE_GLOB** — named in the extraction brief as a candidate gate but absent from this
   section. It governs case-sensitivity of filename generation but is documented in
   zshoptions, not here. Left out of the gate table except as this note.
2. **`(#q…)` vs `(#cN,M)` vs `(#b)` lexing** — all open with `(#`; the disambiguator is the
   next char (`q`/`c`/letter-flag). Whether tree-sitter needs an external scanner to resolve
   `(#…)` against an ordinary `(#…)`-less group, and against the `12(2##)` qualifier clash
   warned at `:1935`, is a grammar-design decision, not resolved by the manual.
3. **Bare-qualifier vs grouping ambiguity** — `(^x)` is qualifiers under BARE_GLOB_QUAL but a
   pattern group otherwise (`:2233–2235`); resolution is option-gated and position-dependent
   (must be trailing). The manual gives the disambiguation rule but it is genuinely
   context-sensitive (depends on options + trailing position).
4. **`f`/`e`/`u`/`o`-code delimiter scanning** — `fspec`, `estring`, `uid`, `oe`/`o+` use a
   "first char is the delimiter, matching bracket for `[ { <`" rule (`:2314–2320,:2347–2349,
   :2393–2396`). This is balanced-delimiter scanning that a CFG cannot express cleanly;
   likely needs an external scanner. Noted, not resolved.
5. **`x~y` exclusion-context `/` and `.`** rules (`:1920`) and the `~`-outside-parens `/`
   rule (`:1970`) make `/`-specialness *position- and context-sensitive* even within filename
   generation — flagged as a parsing subtlety for the grammar.
