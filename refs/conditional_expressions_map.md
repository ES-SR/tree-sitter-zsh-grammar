# Conditional expressions map — the `[[ exp ]]` test sub-grammar

This is the grammar of `exp` inside the `[[` complex command. The host `[[ exp ]]` form
itself is defined in Regime B (`regime_b_map.md`, complex commands, `zshmisc:316`); this
file captures only the **conditional-expression** sub-language it contains, from section
**CONDITIONAL EXPRESSIONS** (`zshmisc:1607–1842`). Manual's OWN forms, verbatim, with
`zshmisc:line` citations. Structural map, not yet `grammar.js`. Precedence quoted from
source / `ordering_inventory.md` only.

The section opens (`:1608–1610`):
> A conditional expression is used with the [[ compound command to test attributes of files
> and to compare strings. Each expression can be constructed from one or more of the
> following unary or binary expressions:

So the top production is: `exp` = one-or-more of {unary | binary | grouped | negated |
combined} expressions. The leaves are file/string/option/varname/fd/regexp/arith operands.

```
exp        → primary | '!' exp | '(' exp ')' | exp '&&' exp | exp '||' exp
                                                     ; :1776–1784  prec !>&&>|| left-assoc (impl-test, ordering §11)
primary    → '(' exp ')'                             ; :1776  grouping
           | '!' exp                                 ; :1779  negation
           | unary_expr | binary_expr
           | word                                    ; :1787  bare single-arg ≡ '-n word'
unary_expr → UNARY_OP operand                        ; :1612–1696
binary_expr→ operand BINARY_OP operand              ; :1698–1753
```

## host entry (the complex-command seam IN)

`[[ exp ]]` — complex command, `zshmisc:316` (catalogued in `regime_b_map.md`). This sub-grammar
is the content of the `exp` slot. The `[[` and `]]` tokens belong to the host (reserved word
`[[`, `regime_b_map.md` reserved words `:389–398`); they are NOT part of `exp`.

## unary operators (`UNARY_OP operand`) — `:1612–1696`

Each is `OP operand`; operand kind quoted from the manual's argument name.

| op | operand (manual's name) | source | true if |
|---|---|---|---|
| `-a` | file | `:1612` | file exists |
| `-b` | file | `:1615` | exists and is a block special file |
| `-c` | file | `:1618` | exists and is a character special file |
| `-d` | file | `:1621` | exists and is a directory |
| `-e` | file | `:1624` | file exists |
| `-f` | file | `:1627` | exists and is a regular file |
| `-g` | file | `:1630` | exists and has its setgid bit set |
| `-h` | file | `:1633` | exists and is a symbolic link |
| `-k` | file | `:1636` | exists and has its sticky bit set |
| `-n` | string | `:1639` | length of string is non-zero |
| `-o` | option | `:1642` | option named option is on (see below — OPTION gate) |
| `-p` | file | `:1651` | exists and is a FIFO special file (named pipe) |
| `-r` | file | `:1654` | exists and is readable by current process |
| `-s` | file | `:1657` | exists and has size greater than zero |
| `-t` | fd | `:1660` | fd is open and associated with a terminal device (**"fd is not optional"**, `:1661`) |
| `-u` | file | `:1663` | exists and has its setuid bit set |
| `-v` | varname | `:1666` | shell variable varname is set |
| `-w` | file | `:1669` | exists and is writable by current process |
| `-x` | file | `:1672` | exists and is executable by current process (dir ⇒ searchable, `:1673`) |
| `-z` | string | `:1677` | length of string is zero |
| `-L` | file | `:1680` | exists and is a symbolic link |
| `-O` | file | `:1683` | exists and is owned by the effective user ID of this process |
| `-G` | file | `:1687` | exists and its group matches the effective group ID |
| `-S` | file | `:1691` | exists and is a socket |
| `-N` | file | `:1694` | exists and access time is not newer than modification time |

**`-o option` (OPTION gate, `:1642–1649`)** — operand is an option name, "may be a single
character … single letter option name. (See the section 'Specifying Options'.)" Note: this
is the OPTION-test unary, distinct from the `||`-class logical OR (which the section never
spells `-o`). Behavior is gated by **POSIX_BUILTINS**:
> When no option named option exists, and the POSIX_BUILTINS option hasn't been set, return 3
> with a warning. If that option is set, return 1 with no warning. (`:1647–1649`)
This is a runtime/return gate, not a syntax change.

Note: the section gives no `-a`/`-o` as binary logical and/or operators in this list — the
ONLY `-a` here is the unary "file exists" (`:1612`). Logical and/or are the `&&`/`||` forms
below. (See Open questions re: `[`/`test` builtin's `-a`/`-o`.)

## binary operators (`operand BINARY_OP operand`) — `:1698–1774`

### file-comparison (`:1698–1705`)
| form | source | true if |
|---|---|---|
| `file1 -nt file2` | `:1698` | file1 exists and is newer than file2 |
| `file1 -ot file2` | `:1701` | file1 exists and is older than file2 |
| `file1 -ef file2` | `:1704` | file1 and file2 exist and refer to the same file |

### string match / pattern (`:1707–1716`) — SEAM to filename-generation patterns
| form | source | true if |
|---|---|---|
| `string = pattern` | `:1707` | string matches pattern (traditional shell syntax) |
| `string == pattern` | `:1708` | string matches pattern (`=` and `==` "exactly equivalent", `:1709`) |
| `string != pattern` | `:1715` | string does not match pattern |

`=`/`==`/`!=` RHS is a **pattern**, not a literal — SEAM: "Pattern metacharacters are active
for the pattern arguments; the patterns are the same as those used for filename generation,
see zshexpn(1), but there is no special behaviour of '/' nor initial dots, and no glob
qualifiers are allowed." (`:1822–1825`). Equivalence of `=` and `==` (`:1709–1713`): `=` is
traditional (the only form with `test`/`[`); `==` for compatibility with other languages.

### regex match (`:1718–1745`) — SEAM to regex engine + OPTION gates
| form | source | true if |
|---|---|---|
| `string =~ regexp` | `:1718` | string matches the regular expression regexp |

**OPTION gate RE_MATCH_PCRE (`:1719–1722`):**
> If the option RE_MATCH_PCRE is set regexp is tested as a PCRE regular expression using the
> zsh/pcre module, else it is tested as a POSIX extended regular expression using the
> zsh/regex module.
This selects the regex engine (zsh/pcre vs zsh/regex) — a SEAM to an external regex grammar,
not zsh's own pattern grammar.

**Match-variable side effects (`:1723–1745`)** — "Upon successful match, some variables will
be updated; no variables are changed if the matching fails." (`:1723`). Two OPTION-gated sets:
- **BASH_REMATCH not set** (default, `:1726–1741`): scalar `MATCH` = matched substring;
  integers `MBEGIN`/`MEND` = start/end indices (so `${var[$MBEGIN,$MEND]}` ≡ `$MATCH`);
  array `match` = parenthesised-subexpression matches; arrays `mbegin`/`mend` = their indices.
  Arrays unset if no parenthesised subexpressions (`:1735`). "The setting of the option
  KSH_ARRAYS is respected." (`:1731`).
- **BASH_REMATCH set** (`:1743–1745`): array `BASH_REMATCH` = whole match followed by the
  parenthesised-subexpression matches.
These are output-parameter effects (gated by BASH_REMATCH, KSH_ARRAYS), not syntax.

### string ordering (`:1747–1753`)
| form | source | true if |
|---|---|---|
| `string1 < string2` | `:1747` | string1 comes before string2 by ASCII value |
| `string1 > string2` | `:1751` | string1 comes after string2 by ASCII value |

### numeric comparison (`:1755–1774`) — SEAM to ARITHMETIC EVALUATION
| form | source | true if |
|---|---|---|
| `exp1 -eq exp2` | `:1755` | exp1 numerically equal to exp2 |
| `exp1 -ne exp2` | `:1761` | exp1 numerically not equal to exp2 |
| `exp1 -lt exp2` | `:1764` | exp1 numerically less than exp2 |
| `exp1 -gt exp2` | `:1767` | exp1 numerically greater than exp2 |
| `exp1 -le exp2` | `:1770` | exp1 numerically less than or equal to exp2 |
| `exp1 -ge exp2` | `:1773` | exp1 numerically greater than or equal to exp2 |

The `exp1`/`exp2` operands are ARITHMETIC operands (SEAM, Regime A):
> In the forms which do numeric comparison, the expressions exp undergo arithmetic expansion
> as if they were enclosed in $((...)). (`:1832–1833`)
Manual also notes `((...))` is more convenient for "purely numeric comparisons" (`:1756–1759`).

## grouping, negation, logical combinators (`:1776–1785`)

| form | source | meaning |
|---|---|---|
| `( exp )` | `:1776` | true if exp is true — **grouping** |
| `! exp` | `:1779` | true if exp is false — **negation** |
| `exp1 && exp2` | `:1781` | true if exp1 and exp2 are both true — logical AND |
| `exp1 \|\| exp2` | `:1784` | true if either exp1 or exp2 is true — logical OR |

These are the ONLY logical combinators the section defines. Logical AND/OR are spelled
`&&`/`||` — NOT `-a`/`-o`. (`-o` here is exclusively the unary option-test, `:1642`.)

### precedence — RESOLVED via implementation test (manual is silent)
This section gives NO explicit precedence/associativity statement for `&&`, `||`, `!`, or
`( )`, and no other page does either (full `precedence` grep). Since the manual is silent,
precedence was determined by testing the reference implementation (zsh 5.9.1) — recorded as
**`ordering_inventory.md §11` (IMPLEMENTATION-DETERMINED, not spec-derived)**:

> **`!` > `&&` > `||`** (high→low), `( )` grouping, left-associative.

Tests: `[[ T || T && F ]]`→true ⇒ `&&` tighter than `||`; `[[ ! T && F ]]`→false ⇒ `!` highest.
This is the OPPOSITE of the Regime-B sublist, where `&&`/`||` are EXPLICITLY equal precedence
(`zshmisc:49`) — `[[ ]]` and command lists are distinct grammars. Mark this `prec` as
implementation-derived in `grammar.js`. The example at `:1837`
(`[[ ( -f foo || -f bar ) && $report = y* ]]`) is consistent (parens force `||` under `&&`).

## bare single-argument form (`:1787–1791`)
> For compatibility, if there is a single argument that is not syntactically significant,
> typically a variable, the condition is treated as a test for whether the expression expands
> as a string of non-zero length. In other words, [[ $var ]] is the same as [[ -n $var ]].
So `[[ word ]]` (a single non-operator argument) is a `primary` ≡ `-n word`.

## operand expansion rules (apply to every operand) — `:1793–1830`

These constrain how operands (file/string/pattern args) expand — relevant because they fix
what the operand grammar may contain.

- **Single-word constraint (`:1793–1795`):** "Normal shell expansion is performed on the file,
  string and pattern arguments, but the result of each expansion is constrained to be a single
  word, similar to the effect of double quotes." (SEAM to expansion, but quoted-like.)
- **No filename generation by default (`:1797–1805`):** "Filename generation is not performed
  on any form of argument to conditions." It CAN be forced, gated by **EXTENDED_GLOB**, via an
  explicit glob qualifier `(#q)` at the end of the string ("A normal glob qualifier expression
  may appear between the 'q' and the closing parenthesis"). Results joined to a single word.
- **`[[`-only (`:1807–1811`):** "This special use of filename generation is only available with
  the [[ syntax." With `[`/`test`, globbing happens earlier as normal command-line expansion.
  (Distinguishes the `[[` host from the `[`/`test` builtins.)
- **Example (`:1813–1820`):** `[[ -n file*(#qN) ]]` — status zero iff ≥1 file beginning with
  'file'; `N` glob qualifier ⇒ empty if no match.
- **Pattern-arg metacharacters (`:1822–1825`):** patterns = filename-generation patterns (SEAM
  to zshexpn) but no special `/`, no initial-dot behaviour, no glob qualifiers.
- **`/dev/fd/n` operands (`:1827–1830`):** if a `file` operand is `/dev/fd/n` (n integer), the
  test applies to the open file with descriptor n, even without OS `/dev/fd` support.
- **Numeric-operand arithmetic (`:1832–1833`):** numeric-comparison exps undergo arithmetic
  expansion as if in `$((...))` (the SEAM noted above).

## Seams OUT of this sub-grammar
1. `[[ ... ]]` host ← **Regime B** (`zshmisc:316`); `[[`/`]]` tokens are the host's.
2. `=` / `==` / `!=` RHS **pattern** → **FILENAME GENERATION pattern grammar** (zshexpn),
   minus `/`/initial-dot specials and glob qualifiers (`:1822–1825`).
3. `=~` RHS **regexp** → external regex engine: **zsh/pcre** (if RE_MATCH_PCRE) or **zsh/regex**
   POSIX ERE (else) (`:1719–1722`) — not zsh's own pattern grammar.
4. `-eq`/`-ne`/`-lt`/`-gt`/`-le`/`-ge` operands → **ARITHMETIC EVALUATION** (`$((...))`-style,
   `:1832–1833`).
5. all operands → **expansion**, single-word-constrained (`:1793–1795`); optional forced
   filename generation via `(#q)` (`:1797–1805`).

## Option switches affecting this sub-grammar (modifier layer)
- **RE_MATCH_PCRE** — selects PCRE vs POSIX-ERE engine for `=~` (`:1719`). Engine seam, not syntax.
- **BASH_REMATCH** — selects which match parameters are set after `=~` (`:1726`, `:1743`). Output only.
- **KSH_ARRAYS** — respected for the `=~` match-variable indices (`:1731`). Output only.
- **EXTENDED_GLOB** — gates the forced `(#q)` filename-generation qualifier on operands (`:1799`). Syntax-adjacent.
- **POSIX_BUILTINS** — return-code/warning behaviour of `-o option` when option absent (`:1647`). Runtime only.

## What this gives the grammar
A `conditional_expression` sub-rule (the `exp` slot of the `[[` complex command), comprising:
- a flat operator set: ~24 prefix unary ops (`-a`…`-N`, plus `-o`/`-v`/`-t`/`-n`/`-z`),
  3 file-comparison binaries (`-nt -ot -ef`), pattern binaries (`= == !=`), regex binary
  (`=~`), string-order binaries (`< >`), 6 arithmetic binaries (`-eq`…`-ge`);
- `( exp )` grouping, `! exp` negation, `exp && exp` / `exp || exp` combinators
  (precedence `!`>`&&`>`||`, left-assoc — impl-test, `ordering_inventory.md §11`);
- a bare-`word` primary ≡ `-n word` (`:1787`);
- operands as expansion seams (single-word), with pattern/regex/arith RHS as distinct seams.

---

## Open questions (ambiguities — not guessed)
1. **`&&` / `||` precedence & associativity — RESOLVED** (implementation test, not spec).
   Manual is silent; tested zsh 5.9.1 → `!` > `&&` > `||`, left-assoc, `( )` grouping. See
   `ordering_inventory.md §11` and the "precedence" section above. (Contrast: Regime-B sublist
   `&&`/`||` are stated EQUAL-prec at `zshmisc:49` — opposite of conditional context.)
2. **`!` and `( )` binding — RESOLVED** with #1: `! a && b` parses as `(!a) && b` (`!` highest).
3. **`<` / `>` operand collision with redirection.** Inside `[[`, `string1 < string2` /
   `> string2` use `<`/`>` as string-order operators (`:1747`,`:1751`), but `<`/`>` are
   redirection operators in Regime B. The section does not state how the lexer disambiguates
   (presumably the `[[` host context, but not spelled out here).
4. **`-a` / `-o` as binary logical operators.** This section defines `-a` only as unary
   "file exists" (`:1612`) and `-o` only as unary "option is on" (`:1642`); logical and/or are
   `&&`/`||`. The classic `test`/`[` binary `-a`/`-o` (and/or) are NOT documented in this `[[`
   section — whether they are accepted inside `[[` is unstated here.
5. **Operand lexical boundaries.** "single word" expansion result (`:1794`) constrains the
   value but the section does not give the token grammar of an unexpanded operand (where a
   `word` ends, how an operator is distinguished from an operand that looks like `-a`).
