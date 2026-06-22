# Minor expansions map — process sub, command sub, arithmetic, brace, filename expansion

These five sections from **zshexpn** cover the smaller members of the "five middle expansions"
(process substitution, command substitution, arithmetic expansion, brace expansion) plus
filename expansion (the `~`/`=` forms). Together with parameter expansion (the major member,
mapped separately), they constitute the expansion machinery that operates on each word after
alias expansion, per the master expansion pipeline.

Placement in the master pipeline (from `ordering_inventory.md` §1, citing `zshexpn:7–37`):

```
History → Alias → { Process Sub, Parameter, Command Sub, Arithmetic, Brace }
                    (L-to-R, completed per-stage per-argument)
                  → Filename Expansion → Filename Generation
```

Option switch: `SH_FILE_EXPANSION` moves Filename Expansion to just after Alias
(`ordering_inventory.md` §1; `zshexpn:23`).

Brace expansion precedes filename generation (`ordering_inventory.md` §10; `zshexpn:1604`).

---

## 1. Process Substitution (`zshexpn:349–457`)

### Syntactic forms (verbatim)

| form | description | source |
|---|---|---|
| `<(list)` | replaced with path to fd/FIFO connected to `list`'s output | `:350,364` |
| `>(list)` | replaced with path to fd/FIFO connected to `list`'s input | `:350,369` |
| `=(list)` | replaced with path to temporary file containing `list`'s output | `:351,379` |

Quoted constraints on syntax:
- "Each part of a command argument that takes the form `<(list)`, `>(list)` or `=(list)` is
  subject to process substitution." (`:350–351`)
- "The expression may be preceded or followed by other strings except that, to prevent clashes
  with commonly occurring strings and patterns, the last form must occur at the start of a
  command argument" (`:352–354`) — i.e. `=(list)` must be word-initial; `<(list)` and `>(list)`
  may appear mid-word.
- "the forms are only expanded when first parsing command or assignment arguments" (`:355–356`)
- "Process substitutions may be used following redirection operators; in this case, the
  substitution must appear with no trailing string." (`:356–357`)
- "`<<(list)` is not a special syntax; it is equivalent to `< <(list)`" (`:359–360`)

Special optimization:
- `=(<<<arg)` — produces a file containing the value of `arg` after substitutions; handled
  entirely within the current shell. "This is effectively the reverse of the special form
  `$(<arg)`" (`:384–390`). (`:384–390`)

### SEAM: operand is `list`

The operand inside all three forms is a `list` — the universal recursion point of Regime B
(`regime_b_map.md`; `zshmisc:70`). This is the primary seam from these expansion forms back
into the command grammar.

### SEAM: interaction with redirection

Process substitutions "may be used following redirection operators" (`:356`), connecting to
the I/O sub-cluster in `regime_b_map.md` (`:715`). When used after a redirection operator, no
trailing string is allowed.

---

## 2. Command Substitution (`zshexpn:1537–1552`)

### Syntactic forms (verbatim)

| form | description | source |
|---|---|---|
| `$(list)` | replaced with stdout of `list`, trailing newlines deleted | `:1538–1540` |
| `` `list` `` (backtick) | same semantics as `$(list)` | `:1539` |
| `$(<file)` | replaced with contents of `file` (faster `$(cat file)`) | `:1544` |

Quoted constraints:
- "A command enclosed in parentheses preceded by a dollar sign, like `$(...)`, or quoted with
  grave accents, like `` `...` ``, is replaced with its standard output, with any trailing
  newlines deleted." (`:1538–1540`)
- "If the substitution is not enclosed in double quotes, the output is broken into words using
  the IFS parameter." (`:1541–1542`)
- For `$(<file)`: "foo undergoes single word shell expansions (parameter expansion, command
  substitution and arithmetic expansion), but not filename generation." (`:1544–1547`)

### Option gate

- **GLOB_SUBST**: "If the option GLOB_SUBST is set, the result of any unquoted command
  substitution, including the special form just mentioned, is eligible for filename
  generation." (`:1549–1551`)

### SEAM: operand is `list`

The operand of `$(list)` and `` `list` `` is a `list` — the universal recursion point of
Regime B. The `$(<file)` form takes a filename word instead.

---

## 3. Arithmetic Expansion (`zshexpn:1553–1558`)

### Syntactic forms (verbatim)

| form | description | source |
|---|---|---|
| `$((exp))` | substituted with value of arithmetic expression `exp` | `:1554` |
| `$[exp]` | same as `$((exp))` (older form) | `:1554` |

Quoted constraints:
- "A string of the form `$[exp]` or `$((exp))` is substituted with the value of the
  arithmetic expression exp." (`:1554`)
- "exp is subjected to parameter expansion, command substitution and arithmetic expansion
  before it is evaluated." (`:1555–1556`)
- "See the section 'Arithmetic Evaluation'." (`:1557`) — this is in `zshmisc`.

### SEAM: `exp` → ARITHMETIC EVALUATION

The expression `exp` is evaluated under the arithmetic operator precedence defined in
`zshmisc:1483–1534` (documented in `ordering_inventory.md` §6). The internal grammar of `exp`
is the arithmetic expression sub-grammar (separate map).

---

## 4. Brace Expansion (`zshexpn:1559–1611`)

### Syntactic forms (verbatim)

| form | description | source |
|---|---|---|
| `foo{xx,yy,zz}bar` | expanded to `fooxxbar fooyybar foozzbar` | `:1560–1561` |
| `{n1..n2}` | integer range, `n1` to `n2` inclusive | `:1565` |
| `{n1..n2..n3}` | integer range with step `n3` | `:1572` |
| `{c1..c2}` | character range, single characters (may be multibyte) | `:1582` |
| `{chars-and-ranges}` | character class (BRACE_CCL only) | `:1592–1600` |

Quoted constraints:
- Comma form: "Left-to-right order is preserved. This construct may be nested. Commas may be
  quoted in order to include them literally in a word." (`:1561–1562`)
- Integer range: "If either number begins with a zero, all the resulting numbers will be padded
  with leading zeroes to that minimum width, but for negative numbers the - character is also
  included in the width." (`:1566–1569`)
- Integer range with step: "If n3 is negative the numbers are output in reverse order"
  (`:1574`). "Zero padding can be specified in any of the three numbers" (`:1576–1577`).
- Character range: "expanded to every character in the range from c1 to c2 in whatever
  character sequence is used internally" (`:1583–1584`). "If the character sequence is
  reversed, the output is in reverse order" (`:1588–1589`).
- Fallthrough to BRACE_CCL: "If a brace expression matches none of the above forms, it is left
  unchanged, unless the option BRACE_CCL ... is set." (`:1591–1593`)
- BRACE_CCL syntax: "similar to a [...] expression in filename generation: '-' is treated
  specially to denote a range of characters, but '^' or '!' as the first character is treated
  normally." (`:1596–1598`)

### Precedence (from `ordering_inventory.md`)

Brace expansion is in the five middle expansions (§1) and "is not part of filename generation
(globbing)" (`:1602`). "an expression such as `*/{foo,bar}` is split into two separate words
`*/foo` and `*/bar` before filename generation takes place" (`:1603–1604`;
`ordering_inventory.md` §10).

### Option gates

- **IGNORE_BRACES**: disables brace expansion entirely. (Not stated in this section but
  referenced in `zshoptions`; also `regime_b_map.md` notes IGNORE_BRACES affects `}` recognition
  and `{varid}>` redirection.)
- **BRACE_CCL**: enables the character-class fallback form `{chars-and-ranges}` (`:1592`).
- **RC_EXPAND_PARAM**: the `${^spec}` form for combining brace expansion with array expansion;
  "see the `${^spec}` form described in the section 'Parameter Expansion' above" (`:1609–1610`).

### SEAM: nesting and interaction with other expansions

- Brace expansion nests: "This construct may be nested" (`:1562`).
- Brace + array: `${^spec}` connects to parameter expansion's rule 20 (`ordering_inventory.md`
  §4, step 20).
- Contrast with glob alternation: `*/{foo,bar}` (brace, two words) vs `*/(foo|bar)` (single
  glob pattern) — "this is liable to produce a 'no match' error if either of the two expressions
  does not match" (`:1605–1606`).

---

## 5. Filename Expansion (`zshexpn:1612–1757`)

### Syntactic forms (verbatim)

**Tilde expansion** (`:1612–1631`):

| form | description | source |
|---|---|---|
| `~` | replaced by `$HOME` | `:1619` |
| `~user` | home directory of `user` (static named directory) | `:1718–1719` |
| `~+` | current working directory | `:1620` |
| `~-` | previous working directory | `:1621` |
| `~N` (number) | directory at position N in directory stack | `:1623` |
| `~+N` | directory at position N in directory stack (from top) | `:1625` |
| `~-N` | directory N positions from bottom of stack | `:1627` |
| `~name` | static named directory (alphanumeric, `_`, `-`, `.`) | `:1718–1719` |
| `~[namstr]` | dynamic named directory | `:1640` |

Quoted constraints:
- "Each word is checked to see if it begins with an unquoted `~`. If it does, then the word up
  to a `/`, or the end of the word if there is no `/`, is checked to see if it can be
  substituted" (`:1613–1616`)
- "`~0` is equivalent to `~+`" (`:1624`)
- "The PUSHD_MINUS option exchanges the effects of `~+` and `~-` where they are followed by a
  number." (`:1629–1630`)

**Dynamic named directories** (`:1632–1715`):

- "A `~` followed by a string namstr in unquoted square brackets is treated specially as a
  dynamic directory name." (`:1640–1641`)
- "the first unquoted closing square bracket always terminates namstr" (`:1641–1642`)
- Resolution via `zsh_directory_name` function or `zsh_directory_name_functions` array
  (`:1633–1634`).

**Static named directories** (`:1717–1736`):

- "A `~` followed by anything not already covered consisting of any number of alphanumeric
  characters or underscore (`_`), hyphen (`-`), or dot (`.`) is looked up as a named directory"
  (`:1718–1720`)
- "They may also be defined if the text after the `~` is the name of a string shell parameter
  whose value begins with a `/`." (`:1722–1723`)
- Also definable via `hash -d` (`:1727–1728`).

**`=` expansion** (`:1738–1742`):

| form | description | source |
|---|---|---|
| `=cmd` | replaced with full pathname of `cmd` | `:1739–1742` |

- "If a word begins with an unquoted `=` and the EQUALS option is set, the remainder of the
  word is taken as the name of a command." (`:1739–1740`)

**Assignment context / colon behavior** (`:1744–1757`):

- "Filename expansion is performed on the right hand side of a parameter assignment ... the
  right hand side will be treated as a colon-separated list in the manner of the PATH parameter,
  so that a `~` or an `=` following a `:` is eligible for expansion." (`:1745–1749`)
- "All such behaviour can be disabled by quoting the `~`, the `=`, or the whole expression (but
  not simply the colon); the EQUALS option is also respected." (`:1750–1751`)

### Option gates

- **EQUALS**: gates `=cmd` expansion (`:1739`). Quoting `=` also inhibits.
- **MAGIC_EQUAL_SUBST**: "any unquoted shell argument in the form `identifier=expression`
  becomes eligible for file expansion as described in the previous paragraph" (`:1753–1755`).
  Extends the colon-separated `~`/`=` expansion to arbitrary `id=expr` arguments, not just
  actual parameter assignments.
- **NOMATCH**: if dynamic named directory resolution fails and NOMATCH is set, an error results
  (`:1649`).
- **PUSHD_MINUS**: exchanges `~+N` and `~-N` semantics (`:1629–1630`).
- **SH_FILE_EXPANSION**: moves filename expansion to before the five middle expansions
  (`ordering_inventory.md` §1; `zshexpn:23`).

### SEAM: dynamic named directories → `zsh_directory_name`

Dynamic directory naming (`~[namstr]`) calls the user-defined function `zsh_directory_name` or
functions in `zsh_directory_name_functions` (`:1633–1634`). This is a runtime seam — the
grammar sees `~[...]` as a syntactic form; resolution is at execution time.

---

## Internal structure summary

These five sections are syntactically simple — each defines a small set of delimited forms
(mostly prefix + delimiters + operand). The complexity is in their interactions:

- **Process sub and command sub** share the `list` operand (Regime B recursion point).
- **Arithmetic expansion** delegates to the arithmetic expression sub-grammar (`zshmisc`).
- **Brace expansion** is self-contained but nests, and interacts with parameter expansion via
  `${^spec}` (RC_EXPAND_PARAM).
- **Filename expansion** is a lookup/substitution step with multiple sub-forms gated by
  distinct options.

All five are positioned in the master pipeline by `ordering_inventory.md` §1: the first four
are in the middle-five group (L-to-R, per-stage per-argument); filename expansion follows them
(or precedes them if SH_FILE_EXPANSION is set).

## Seams summary

| from | to | nature |
|---|---|---|
| `<(list)` / `>(list)` / `=(list)` operand | Regime B `list` | `list` is full command grammar |
| `$(list)` / `` `list` `` operand | Regime B `list` | `list` is full command grammar |
| `$(<file)` operand | word (parameter/cmd/arith expansion, no filename gen) | restricted expansion |
| `$((exp))` / `$[exp]` operand | arithmetic expression sub-grammar (`zshmisc:1483`) | separate precedence ladder |
| `${^spec}` | parameter expansion rule 20 | RC_EXPAND_PARAM / brace+array |
| `~[namstr]` | `zsh_directory_name` function | runtime resolution |
| brace result → filename generation | filename generation (globbing) | §10: brace before glob |
| filename expansion → five middle expansions | pipeline ordering | SH_FILE_EXPANSION reorders |

## Option switches that affect syntax in these sections

| option | effect | source |
|---|---|---|
| IGNORE_BRACES | disables brace expansion | `zshoptions` |
| BRACE_CCL | enables `{char-class}` fallback | `zshexpn:1592` |
| RC_EXPAND_PARAM | `${^spec}` brace+array combination | `zshexpn:1609` |
| EQUALS | gates `=cmd` expansion | `zshexpn:1739` |
| MAGIC_EQUAL_SUBST | extends `~`/`=` expansion to `id=expr` args | `zshexpn:1753` |
| NOMATCH | error on failed dynamic named dir | `zshexpn:1649` |
| PUSHD_MINUS | swaps `~+N`/`~-N` | `zshexpn:1629` |
| SH_FILE_EXPANSION | reorders filename expansion in pipeline | `zshexpn:23` |
| GLOB_SUBST | command sub result eligible for filename gen | `zshexpn:1549` |

---

## Open questions

1. **`=(list)` word-initial constraint precision:** The manual says `=(list)` "must occur at the
   start of a command argument" (`:353–354`). Does "start" mean the very first character of the
   word token, or can it follow an assignment `var=`? The grammar needs a clear token-boundary
   rule here. (Contrast: `<(list)` and `>(list)` may appear mid-word.)

2. **Backtick nesting:** The manual does not describe nesting rules for the backtick form of
   command substitution in this section. The `$(...)` form nests naturally by delimiter matching.
   Backtick nesting requires escaping (POSIX behavior) — is this stated elsewhere in the zsh
   manual, or is POSIX behavior assumed?

3. **`$[exp]` deprecation status:** The `$[exp]` form is described alongside `$((exp))` with no
   deprecation warning in zsh 5.9.1. Should the grammar treat it as fully equivalent, or is
   there any option that disables it?

4. **Brace expansion inside `${...}`:** The manual says brace expansion and parameter expansion
   are in the same middle-five group, completed per-stage L-to-R. Can `{a,b}` appear inside
   `${...}` or vice versa? The interaction between nesting and L-to-R per-stage completion needs
   clarification for the parser.

5. **`~` vs `~name` tokenization:** The manual says the word "up to a `/`" is checked
   (`:1614–1615`). For the grammar, the tilde-prefix is a context-sensitive token that ends at
   `/` or word-end. How does this interact with other expansion forms that might produce a `/`
   (e.g., `~${var}` where `$var` contains `/`)?
