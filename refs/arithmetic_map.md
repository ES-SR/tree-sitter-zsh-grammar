# Arithmetic map — ARITHMETIC EVALUATION (Regime A)

The arithmetic expression sub-grammar, bound by the manual's **ARITHMETIC EVALUATION**
section (`zshmisc:1375–1606`). This file captures the syntactic forms in the manual's OWN
wording, with `zshmisc:line` citations. It is a structural map, not yet `grammar.js`.
Operator precedence is NOT re-derived here — it is the property of `ordering_inventory.md §6`
(the only sanctioned precedence source) and is cited, not restated.

Arithmetic is a *seam target*, not a top-level regime: it is always entered FROM some host
construct (see "Seams IN" below). The grammar needs one `_arith_expr` rule reachable from
each seam.

## Entry forms (how arithmetic text is delimited)

| form | source | notes |
|---|---|---|
| `let WORD...` (builtin) | `:1376,:1385` | "takes arithmetic expressions as arguments; each is evaluated separately" (`:1385`) — each arg is one independent expression |
| `(( ... ))` command | `:1387–1391` | "any command which begins with a '((', all the characters until a matching '))' are treated as a double-quoted expression"; "'((...))' is equivalent to 'let \"...\"'" (`:1390`). Return status 0/1/2 (`:1391`) |
| `$(( ... ))` substitution | `:1377` | "a substitution of the form $((...))"; arithmetic *expansion* |

Note: `let` and `((...))` are also Regime-B terminals (`let` is a builtin; `(( ` opens the
arithmetic-command form). `$((...))` is the arithmetic-expansion member of the master
expansion five-group (`ordering_inventory §1`). The body of all three is the same
`_arith_expr` grammar.

## Numeric literal forms

VERBATIM forms from `:1405–1477`:

| literal | source | form |
|---|---|---|
| decimal | (implicit) | base 10 default (`:1410` "base# … omitted, base 10 is used") |
| hexadecimal | `:1405` | leading `0x` or `0X` |
| binary | `:1406` | leading `0b` or `0B` |
| explicit base | `:1407` | `base#n`, base = decimal 2..36, n in that base (e.g. `16#ff` = 255, `:1408`) |
| legacy base | `:1410` | `[base]n` — "for backwards compatibility the form '[base]n' is also accepted" |
| underscores in integers | `:1413–1416` | `_` allowed *after the leading digit* in an integer or `base#n`; ignored in computation (`1_000_000`, `0xffff_ffff`) |
| floating point | `:1472` | "recognized by the presence of a decimal point or an exponent" |
| float — decimal point | `:1473` | decimal point may be the *first* character of the constant |
| float — exponent | `:1473–1474` | `e`/`E` exponent, but **may not be the first character** ("will be taken for a parameter name") |
| underscores in floats | `:1475` | `_` allowed after leading digit in all numeric parts (before/after point, in exponent); ignored |

Output-base markers (these appear at the *start of an expression*, not operand positions):

| marker | source | notes |
|---|---|---|
| `[#base]` | `:1418–1419` | output base spec, e.g. `[#16]`. "has no precedence"; if it occurs more than once, last encountered is used; recommended at beginning (`:1425–1427`) |
| `[##base]` | `:1469` | doubled `#` → no base prefix output |
| `[#base_]` / `[#base_N]` | `:1439–1443` | trailing `_` (opt. followed by positive int, default 3) → insert grouping underscores in output |
| `[#_]` / `[#_N]` | `:1450–1455` | for floats the base must be omitted; grouping away from decimal point |

## Operand forms

| operand | source | notes |
|---|---|---|
| bare parameter name | `:1553–1559` | "Named parameters … can be referenced by name within an arithmetic expression without using the parameter expansion syntax" — no `$` needed. Example `((val2 = val1 * 2))` (`:1557`) |
| subscripted array | `:1553` | "subscripted arrays can be referenced by name" — array name with subscript, bare (no `$`) |
| character value `##x` | `:1543` | `##x` where x is any character sequence (`a`, `^A`, `\M-\C-x`) → value of that character |
| character value `#name` | `:1545` | `#name` → value of the first character of the contents of parameter `name` |
| character value `#\c` | `:1550` | "'#\\' is accepted instead of '##', but its use is deprecated" |
| function call | `:1536` | `func(args)` — "the function decides if the args is used as a string or a comma-separated list of arithmetic expressions". No math functions by default; `zsh/mathfunc` provides them (`:1538`) |
| parenthesised subexpr | `:1480,:1533` | "nearly the same syntax … as in C"; explicit `(3**2)` grouping shown (`:1534`) |

Disambiguation hazards the parser must respect:
- `#name` (char value, `:1545`) vs `$#name` (parameter length, a parameter substitution,
  NOT arithmetic) — "this form is different from '$#name'" (`:1549`).
- exponent `e`/`E` not allowed as first char of a float constant because it would be read as
  a parameter name (`:1474`).

## Operators (forms only — precedence is §6, not here)

The full operator set and BOTH precedence orderings (default native + `C_PRECEDENCES`) are
captured verbatim as **`ordering_inventory.md §6`** (`zshmisc:1483–1534`). Do not re-derive
the ladder; cite §6. Forms appearing in the section, for parser token coverage:

- unary: `+ - ! ~ ++ --` (`:1485`) — `++`/`--` are pre/post in/decrement (`:1486`)
- binary arithmetic: `** * / % + -` (`:1491–1493`)
- bitwise: `<< >> & ^ |` (`:1487–1490`)
- comparison: `< > <= >= == !=` (`:1494–1496`)
- logical: `&& || ^^` (`:1497–1498`)
- ternary: `? :` (`:1499`)
- assignment: `= += -= *= /= %= &= ^= |= <<= >>= &&= ||= ^^= **=` (`:1500`)
- comma operator: `,` (`:1502`)

Evaluation-property facts (semantic, may affect how a node is shaped but not token forms):
- `&& || &&= ||=` are short-circuiting; only one of the two ternary branches is evaluated
  (`:1504–1505`).
- exponentiation `**` binds *below* unary in both orderings: `-3**2` == `9` (`:1532–1533`).

## Type rules that touch the parse

These are mostly semantic, but two affect tokenization/disambiguation (kept here per the
constraint to note type rules that affect parse):
- A constant is parsed as float iff it has a decimal point or exponent (`:1472`) — the
  presence of `.` / `e`/`E` is the lexical integer↔float discriminator.
- `e`/`E` not first char of constant (else parameter name) (`:1474`).
- Integer-requiring operators (`& | ^ << >>` and their `=` forms) silently round float args
  toward zero, `~` rounds down (`:1575–1578`) — semantic, no parse effect.
- Implicit typing: a first-assigned-in-numeric-context bare name is typed integer or float
  and keeps that type (`:1591–1593`) — semantic; the `for ((f=0; f<1; f+=0.1))` caveat
  (`:1597–1604`) is the worked example. No parse effect.
- `integer`/`float` builtins declare internal representation (`:1561,:1567`) — these are
  Regime-B assignment-context reserved words (see regime_b_map `:69`); the seam is the
  *value* side of such an assignment, evaluated as arithmetic (`:1562`).

## Option-gates (change literal/output behavior, mostly NOT parse)

| option | source | effect |
|---|---|---|
| `C_PRECEDENCES` | `:1508` | reorders operator precedence to C-like (the alternate ladder in §6). The ONE option that changes the parse tree shape |
| `C_BASES` | `:1460` | hex output in C format (`0xFF` vs `16#FF`) — *output* only; "these formats are always understood on input" (`:1465`) |
| `OCTAL_ZEROES` | `:1462` | with `C_BASES`, octal output as `077` vs `8#77` — output only; off by default |
| `FORCE_FLOAT` | `:1585` | float evaluation throughout (overrides term-at-a-time integer truncation) — semantic, no parse effect |
| `MULTIBYTE` | `:1547` | required for multibyte handling of `##x` character values — affects char-value operand meaning, not its form |
| `cbases` (`C_BASES`) | `:1445` | enabled in the `[#16_4]` grouping example |

Only **`C_PRECEDENCES`** alters the parse (precedence reshuffle). `C_BASES`/`OCTAL_ZEROES`
are output-format; both bases are always accepted on *input* (`:1465`), so the input grammar
is invariant under them. `FORCE_FLOAT`/`MULTIBYTE` are semantic.

## Seams IN (where arithmetic is entered FROM)

The arithmetic grammar is reached from these host constructs (the inbound edges):

1. `(( ... ))` arithmetic command (`:1387`) — Regime-B `command` alternative.
2. `$(( ... ))` arithmetic expansion (`:1377`) — member of the master expansion five-group
   (`ordering_inventory §1`).
3. `let WORD...` builtin (`:1385`) — each argument is one independent arithmetic expression.
4. `for (( e1; e2; e3 ))` arithmetic for-loop — three arithmetic exprs (regime_b_map `:43`,
   defined `zshmisc:150`); worked example at `:1597`.
5. `repeat WORD` count — WORD is an arithmetic count (regime_b_map `:46`).
6. array / parameter subscripts — subscript text is arithmetic (`ordering_inventory §8`;
   bare subscripted-array reference noted `zshmisc:1553`).
7. parameter-expansion character evaluation `(#)` flag — numeric→character
   (`ordering_inventory §4` rule 8, `zshexpn:1395`).

(The first four are the explicit `zshmisc` arithmetic entry forms; 5–7 are cross-section
seams that feed the same `_arith_expr`.)

## What this gives the grammar

A single `_arith_expr` rule, reachable from each of the seven seams above, encoding:
- the operator-precedence chain from `ordering_inventory §6` (default + a `C_PRECEDENCES`
  variant — the only option that reshapes the tree),
- literal tokens for all bases (`0x`/`0X`, `0b`/`0B`, `base#n`, legacy `[base]n`, underscore
  digits) and floats (point/exponent, underscore digits),
- the `[#…]` / `[##…]` / `[#…_…]` output-base prefix as a (precedence-less, `:1425`) leading
  marker,
- operand alternatives: bare parameter name, bare subscripted array, `func(args)` call,
  `##x` / `#name` / `#\c` character values, parenthesised subexpression,
- ternary, assignment family, and comma operator as the low-precedence tail.

The three delimiter forms (`((`/`$((`/`let`) are Regime-B-side terminals that hand their body
to `_arith_expr`.

## Open questions / ambiguities

1. **Whitespace inside `(( ))`**: the body is "treated as a double-quoted expression"
   (`:1389`); the manual does not state a token-level whitespace grammar inside arithmetic
   (the `let` rationale is that operators/spaces "require quoting", `:1386`). Whether the
   parser tokenizes whitespace-insensitively inside arithmetic vs. relies on the
   double-quote framing is not specified here.
2. **`((` vs `( (` (subshell-in-subshell)**: the manual says a command "which begins with a
   '((' " is arithmetic (`:1388`); the disambiguation from a nested subshell `( ( ... ) )`
   is not described in this section.
3. **Subscript syntax detail**: `:1553` states subscripted arrays "can be referenced by
   name" but gives no subscript grammar here — the bracket/range forms live in zshparam
   (`ordering_inventory §8` cites `zshparam:448`). Out-of-section.
4. **`func(args)` arg grammar**: `:1537` says the function decides if args is a string or a
   comma-separated list of arithmetic expressions — so the arg-list parse is
   function-dependent and not fixed by the grammar. How to parse uniformly is unresolved.
5. **`[base]n` legacy vs `[#base]` output marker**: both start with `[` (`:1411` operand,
   `:1419` output marker). Disambiguation (`[16]ff` operand vs `[#16] …` marker) hinges on
   the `#`; confirm the lexer can distinguish without lookahead conflict.
6. **`[#base]` "no precedence"** (`:1425`): stated to have no precedence and "if it occurs
   more than once, the last … is used". Whether it can syntactically appear mid-expression
   (vs. only leading) is described as a recommendation ("for clarity … beginning", `:1427`),
   not a rule — so mid-expression placement appears legal but underspecified.
7. **`let` argument quoting**: each `let` arg is a separate expression (`:1385`), but how
   word-splitting/quoting at the Regime-B word level interacts with arithmetic tokenization
   is a Regime-A↔B boundary not pinned down in this section.
