# Prompt expansion map — `%`-escape mini-language

This file captures the prompt expansion sub-grammar defined in **zshmisc** sections
EXPANSION OF PROMPT SEQUENCES (`:1843`), SIMPLE PROMPT ESCAPES (`:1864`), and
CONDITIONAL SUBSTRINGS IN PROMPTS (`:2056`). All forms are verbatim from the manual
with `zshmisc:line` citations.

Prompt expansion is a string-internal mini-language — it operates on the value of prompt
parameters (PS1, PS2, PS4, RPS1, etc.) and is also available via `print -P` (`:1845`).

---

## Option gates (processing order)

The manual specifies three option-gated layers applied in this order (`:1847–1862`):

1. **PROMPT_SUBST** — "the prompt string is first subjected to parameter expansion,
   command substitution and arithmetic expansion" (`:1847–1848`). This happens **first**,
   before any `%`-escape processing.
2. **PROMPT_BANG** — "a '!' in the prompt is replaced by the current history event
   number. A literal '!' may then be represented as '!!'" (`:1853–1855`).
3. **PROMPT_PERCENT** — "certain escape sequences that start with '%' are expanded"
   (`:1857–1858`). This gates the entire `%`-escape alphabet below.

The manual's word "first" for PROMPT_SUBST (`:1847`) establishes ordering:
PROMPT_SUBST before PROMPT_BANG / PROMPT_PERCENT. No explicit ordering between
PROMPT_BANG and PROMPT_PERCENT is stated beyond their textual sequence.

---

## General `%`-escape syntax

"Many escapes are followed by a single character, although some of these take an optional
integer argument that should appear between the '%' and the next character of the sequence.
More complicated escape sequences are available to provide conditional expansion." (`:1858–1862`)

General form: `%` [integer] char — where integer is optional and defaults vary per escape.

---

## Simple prompt escapes (`:1864–2055`)

### Special characters (`:1865`)

| Escape | Expansion | Citation |
|--------|-----------|----------|
| `%%`   | A literal `%` | `:1866` |
| `%)`   | A literal `)` | `:1868` |

### Login information (`:1870`)

| Escape | Expansion | Integer arg | Citation |
|--------|-----------|-------------|----------|
| `%l`   | The line (tty) without `/dev/` prefix; `/dev/tty` prefix also stripped | — | `:1871–1872` |
| `%M`   | The full machine hostname | — | `:1874` |
| `%m`   | Hostname up to the first `.` | "An integer may follow the '%' to specify how many components of the hostname are desired. With a negative integer, trailing components of the hostname are shown." | `:1876–1878` |
| `%n`   | `$USERNAME` | — | `:1880` |
| `%y`   | The line (tty) without `/dev/` prefix; does NOT strip `/dev/tty` specially | — | `:1882–1883` |

### Shell state (`:1885`)

| Escape | Expansion | Integer arg | Citation |
|--------|-----------|-------------|----------|
| `%#`   | `#` if privileged, `%` if not. "Equivalent to `%(!.#.%%)`" | — | `:1886–1887` |
| `%?`   | Return status of last command before the prompt | — | `:1893–1894` |
| `%_`   | Parser status (shell constructs started on cmd line) | "If given an integer number that many strings will be printed; zero or negative or no integer means print as many as there are." | `:1896–1902` |
| `%^`   | Parser status in reverse (same as `%_`, reversed order) | — | `:1904–1905` |
| `%d` / `%/` | Current working directory | "If an integer follows the '%', it specifies a number of trailing components of the current working directory to show; zero means the whole path. A negative integer specifies leading components" | `:1907–1912` |
| `%~`   | As `%d`/`%/`, but `$HOME` replaced by `~`; named dirs replaced by `~name` if shorter | (same as `%d`) | `:1914–1919` |
| `%e`   | Evaluation depth of current sourced file / function / eval | — | `:1921–1924` |
| `%h` / `%!` | Current history event number | — | `:1926–1927` |
| `%i`   | Line number in script/sourced file/function given by `%N` | — | `:1929–1931` |
| `%I`   | Line number in the file `%x` (always file-level, even in functions) | — | `:1933–1936` |
| `%j`   | Number of jobs | — | `:1938` |
| `%L`   | Current value of `$SHLVL` | — | `:1940` |
| `%N`   | Name of script/sourced file/function most recently started | "An integer may follow the '%' to specify a number of trailing path components to show; zero means the full path. A negative integer specifies leading components." | `:1942–1947` |
| `%x`   | Name of file containing source code currently executing (like `%N` but function/eval names not shown) | (same as `%N`) | `:1949–1951` |
| `%c` / `%.` / `%C` | Trailing component of cwd | "An integer may follow the '%' to get more than one component." `%c`/`%.` do tilde contraction first; `%C` does not. Deprecated: `%c`≡`%1~`, `%C`≡`%1/` | `:1953–1960` |

### Date and time (`:1962`)

| Escape | Expansion | Citation |
|--------|-----------|----------|
| `%D`   | Date in `yy-mm-dd` format | `:1963` |
| `%T`   | Time in 24-hour format | `:1965` |
| `%t` / `%@` | Time in 12-hour am/pm format | `:1967–1968` |
| `%*`   | Time in 24-hour format with seconds | `:1970` |
| `%w`   | Date in `day-dd` format | `:1972` |
| `%W`   | Date in `mm/dd/yy` format | `:1974` |
| `%D{string}` | `string` formatted via `strftime(3)` | `:1976–1977` |

**`%D{string}` sub-escapes** (zsh extensions within the strftime string, `:1979–2003`):
- `%f` — day of month, no leading zero/space (`:1981`)
- `%K` — hour (24h clock), no leading zero/space (`:1982`)
- `%L` — hour (12h clock), no leading zero/space (`:1983`)
- `%.` — decimal fractions of a second since epoch (default 3 digits; `%N.` for N digits, max 9) (`:1986–1989`)
- `%N` — synonym for `%9.` (GNU extension) (`:1995`)
- `%-X` — GNU extension: strip leading zero/space; handled by shell for `d f H k l m M S y`; other chars passed to system strftime (`:1997–2003`)

### Visual effects (`:2005`)

| Escape | Expansion | Integer/brace arg | Citation |
|--------|-----------|-------------------|----------|
| `%B` / `(%b)` | Start (stop) boldface mode | — | `:2006–2007` |
| `%E`   | Clear to end of line | — | `:2009` |
| `%U` / `(%u)` | Start (stop) underline mode | — | `:2011–2012` |
| `%S` / `(%s)` | Start (stop) standout mode | — | `:2014–2015` |
| `%F` / `(%f)` | Start (stop) foreground colour | "either as a numeric argument, as normal, or by a sequence in braces following the %F, for example %F{red}" | `:2017–2024` |
| `%K` / `(%k)` | Start (stop) background colour | (same syntax as `%F`/`%f`) | `:2026–2028` |
| `%{...%}` | Literal escape sequence (no cursor movement) | "Brace pairs can nest." "A positive numeric argument between the % and the { is treated as described for %G" | `:2030–2036` |
| `%G`   | Within `%{...%}`, assume single-char width output | "An integer between the '%' and 'G' indicates a character width other than one." "Multiple uses of %G accumulate" "Negative integers are not handled." | `:2038–2050` |

---

## Conditional substrings in prompts (`:2056`)

### `%v` — psvar access (`:2057`)

"The value of the first element of the psvar array parameter. Following the '%' with an
integer gives that element of the array. Negative integers count from the end of the
array." (`:2057–2059`)

### `%(x.true-text.false-text)` — ternary expression (`:2061`)

This is the most grammar-like construct in prompt expansion. Verbatim structure:

> "Specifies a ternary expression. The character following the x is arbitrary; the same
> character is used to separate the text for the 'true' result from that for the 'false'
> result. This separator may not appear in the true-text, except as part of a %-escape
> sequence. A ')' may appear in the false-text as '%)'. true-text and false-text may both
> contain arbitrarily-nested escape sequences, including further ternary expressions."
> (`:2061–2068`)

Grammar form:
```
%(  [n] x  sep  true-text  sep  false-text  )

where:
  n     = optional positive integer (default 0); "A negative integer will be
          multiplied by -1, except as noted below for 'l'" (:2070–2072)
  x     = test character (see table below)
  sep   = the character immediately after x; arbitrary; used as delimiter (:2062)
  true-text  = prompt string (may contain nested escapes including further ternary) (:2067–2068)
  false-text = prompt string (may contain nested escapes including further ternary) (:2067–2068)

Constraints on sep within the fields:
  - sep may NOT appear in true-text except as part of a %-escape (:2065)
  - ')' may appear in false-text as '%)' (:2066)
```

"The left parenthesis may be preceded or followed by a positive integer n, which defaults
to zero." (`:2070–2071`) — i.e. the integer may go before OR after the `(`.

### Ternary test characters (`:2073–2103`)

| Char | Test | Citation |
|------|------|----------|
| `!`  | True if shell is running with privileges | `:2075` |
| `#`  | True if effective uid of current process is n | `:2076` |
| `?`  | True if exit status of last command was n | `:2077` |
| `_`  | True if at least n shell constructs were started | `:2078` |
| `C` / `/` | True if current absolute path has at least n elements (/ = 0 elements) | `:2079–2082` |
| `c` / `.` / `~` | True if current path (with prefix replacement) has at least n elements (/ = 0) | `:2083–2087` |
| `D`  | True if month equals n (January = 0) | `:2088` |
| `d`  | True if day of month equals n | `:2089` |
| `e`  | True if evaluation depth is at least n | `:2090` |
| `g`  | True if effective gid of current process is n | `:2091` |
| `j`  | True if number of jobs is at least n | `:2092` |
| `L`  | True if SHLVL is at least n | `:2093` |
| `l`  | True if at least n characters already printed on current line; "When n is negative, true if at least abs(n) characters remain before the opposite margin" | `:2094–2097` |
| `S`  | True if SECONDS parameter is at least n | `:2098` |
| `T`  | True if time in hours equals n | `:2099` |
| `t`  | True if time in minutes equals n | `:2100` |
| `v`  | True if psvar has at least n elements | `:2101` |
| `V`  | True if element n of psvar is set and non-empty | `:2102` |
| `w`  | True if day of week equals n (Sunday = 0) | `:2103` |

### Truncation (`:2105–2161`)

Three syntactic forms:

```
%<string<          truncate at left  (:2105)
%>string>          truncate at right (:2106)
%[xstring]         deprecated form, equivalent to %xstringx where x is '<' or '>' (:2107–2109)
```

- Numeric argument specifies maximum permitted length (`:2114–2115`).
- In the first two forms, numeric argument may be negative: "truncation length is
  determined by subtracting the absolute value of the numeric argument from the number
  of character positions remaining on the current prompt line" (`:2117–2120`).
- The string replaces the truncated portion; "note this does not undergo prompt
  expansion" (`:2111–2112`).
- Scope: "runs to the end of the string, or to the end of the next enclosing group of
  the '%(' construct, or to the next truncation encountered at the same grouping level …
  which ever comes first" (`:2140–2143`).
- `%<<` (arg zero) marks end of truncation range and turns off truncation (`:2144–2146`).
- `%-0<<` is NOT equivalent to `%<<` — it "specifies that the prompt is truncated at the
  right margin" (`:2150–2152`).
- Truncation is per-line, delimited by embedded newlines (`:2154`).
- Terminating char may be quoted by preceding `\` (`:2130–2131`).

---

## Seams OUT of prompt expansion

1. **PROMPT_SUBST → parameter/command/arithmetic expansion** (`:1847–1848`) — when set,
   the prompt string undergoes the standard expansion pipeline (zshexpn) **before** any
   `%`-escape processing. This is the primary seam: the prompt value is first a regular
   word subject to `${}`, `$()`, `$(())`, then the result is `%`-expanded.
2. **`%D{string}` → strftime(3)** (`:1977`) — the brace-delimited string is passed to
   the C library's strftime; zsh extends it with `%f`, `%K`, `%L`, `%.`, `%N`, `%-X`.
3. **`%F{name}` / `%K{name}` → zle_highlight colour values** (`:2022–2023`) — the brace
   arg is resolved per the `fg` zle_highlight attribute (zshzle).
4. **`print -P`** (`:1845`) — prompt expansion is available outside prompt parameters
   via this builtin.

## Nesting

- `%{...%}` — "Brace pairs can nest." (`:2033`)
- `%(x.true.false)` — "true-text and false-text may both contain arbitrarily-nested
  escape sequences, including further ternary expressions." (`:2067–2068`)
- Truncation scoping interacts with `%(` grouping: "the end of the next enclosing group
  of the '%(' construct" (`:2141`).

## Option switches that affect prompt expansion syntax

| Option | Effect | Citation |
|--------|--------|----------|
| `PROMPT_SUBST` | Enables parameter/command/arithmetic expansion on prompt string (first pass) | `:1847` |
| `PROMPT_BANG` | `!` → history event number; `!!` → literal `!` | `:1853` |
| `PROMPT_PERCENT` | Gates all `%`-escape expansion | `:1857` |

Note: `PROMPT_CR` and `PROMPT_SP` are mentioned in zshoptions but NOT in these zshmisc
sections as affecting expansion syntax — they affect output behavior (carriage return
before prompt), not the escape grammar.

---

## What this gives the grammar

Prompt expansion is a **string-internal mini-language** — it would be parsed inside
string literals that are values of prompt variables, or inside `print -P` arguments.
The key grammar-relevant structures are:

- A flat `%`-escape alphabet: `%` [integer] char — the char determines meaning, the
  integer is optional with per-char defaults. This is a simple lexer-level pattern.
- Two brace-delimited forms: `%D{strftime-string}` and `%F{color}` / `%K{color}` —
  the brace content is a different sub-language (strftime vs colour name).
- `%{...%}` literal-escape brackets — nestable.
- `%(x.true.false)` ternary — the grammar-like core. Recursive (nests arbitrarily),
  with an unusual delimiter: the separator character is determined by position (the
  char after the test char), not fixed. This requires careful scanner/grammar handling.
- Truncation `%<str<` / `%>str>` — scope interacts with `%(` grouping.
- The PROMPT_SUBST seam means the prompt string is first a regular expansion-eligible
  word, then `%`-expanded — two parsing passes on the same string.
