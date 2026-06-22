# Quoting & aliasing map — lexical pre-processing layer

These two subsystems sit BEFORE the grammar proper. Per `ordering_inventory.md` §3
(`zshmisc:505`): "Alias expansion is done on the shell input before any other expansion
except history expansion." Both operate at the lexical level — aliasing rewrites tokens
before parsing; quoting defeats aliasing and controls which characters remain special
through later stages. This file captures both subsystems from **zshmisc** in the manual's
OWN forms, with `zshmisc:line` citations.

---

## QUOTING (`:564–586`)

### Quoting forms (exhaustive from source)

1. **Backslash quoting** — "A character may be quoted (that is, made to stand for itself) by
   preceding it with a `\`." (`:565`). Special case: `\` followed by a newline is ignored
   (line continuation) (`:566`).

2. **Single quotes `'...'`** — "All characters enclosed between a pair of single quotes (`''`)
   that is not preceded by a `$` are quoted." (`:573`). A single quote cannot appear inside
   single quotes **unless** `RC_QUOTES` is set, in which case `''` inside single quotes
   produces a literal `'` (`:575`).

3. **Double quotes `"..."`** — Inside double quotes, parameter and command substitution
   occur (`:583`). `\` quotes only the characters: `\`, `` ` ``, `"`, `$`, and the first
   character of `$histchars` (default `!`) (`:584`). All other `\x` sequences are literal
   inside double quotes.
   - **Characters that remain special inside `"..."`**: `$` (parameter/command substitution),
     `` ` `` (command substitution), `\` (but only before the five chars listed above),
     `"` (terminates the string), `!` (history expansion, first char of `$histchars`).

4. **`$'...'` (C-style / ANSI quoting)** — "A string enclosed between `$'` and `'` is
   processed the same way as the string arguments of the `print` builtin, and the resulting
   string is considered to be entirely quoted." (`:568`). A literal `'` inside is
   represented by the `\'` escape (`:571`).

5. **`$"..."` (locale translation)** — Not mentioned in the QUOTING section of zshmisc.
   (Absence noted; may appear in other manual pages or not be a zsh feature.)

### Option gates (quoting)

| option | effect | source |
|---|---|---|
| `RC_QUOTES` | Allows `''` inside single quotes to produce a literal `'` | `:575` |

### Cross-cutting role of quoting

- **Quoting defeats aliasing**: "if an alias is defined for the word `foo`, alias expansion
  may be avoided by quoting part of the word, e.g. `\foo`. Any form of quoting works" (`:507`).
- **Quoting defeats expansion generally**: quoting is the universal mechanism that makes
  characters "stand for themselves" (`:565`), suppressing their special meaning in later
  expansion stages.

---

## ALIASING (`:473–563`)

### Expansion placement / parser-architecture fact

> "Alias expansion is done on the shell input before any other expansion except history
> expansion." (`:505`)

This is consistent with `ordering_inventory.md` §3 and §1. Aliasing is **lexical** — it
happens "while text is being read" (`zshoptions:1297`, cited in ordering_inventory §3),
**before** the grammar sees tokens. This is a key parser-architecture constraint: alias
expansion must occur in the lexer/scanner layer, not in grammar rules.

### Alias types

1. **Ordinary (command-position) aliases** — Replacement occurs "if it is in command
   position (if it could be the first word of a simple command)" (`:476`). Defined with the
   `alias` builtin (`:485`).

2. **Global aliases (`alias -g`)** — Replacement occurs regardless of position; defined
   using the `-g` option to the `alias` builtin (`:477`, `:486`). Global aliases expand a
   broader class of words (see word definition item 6 below).

3. **Suffix aliases** — Not mentioned in the ALIASING section of zshmisc. (May be defined
   elsewhere, e.g. `alias -s` in zshbuiltins.)

### Trailing-space rule

> "If the replacement text ends with a space, the next word in the shell input is always
> eligible for purposes of alias expansion." (`:478`)

This means alias expansion can chain: the token following the replacement text is also
checked for aliasing, regardless of its position.

### What counts as an alias-able WORD (`:488–503`)

The manual explicitly lists what constitutes a "word" for alias purposes:

1. "Any plain string or glob pattern" (`:490`)
2. "Any quoted string, using any quoting method (note that the quotes must be part of the
   alias definition for this to be eligible)" (`:492`)
3. "Any parameter reference or command substitution" (`:495`)
4. "Any series of the foregoing, concatenated without whitespace or other tokens between
   them" (`:497`)
5. "Any reserved word (`case`, `do`, `else`, etc.)" (`:500`)
6. "With global aliasing, any command separator, any redirection operator, and `(` or `)`
   when not part of a glob pattern" (`:502`) — this item applies ONLY to global aliases.

### What is NOT an alias-able word (`:529–549`)

> "Any set of characters not listed as a word above is not a word, hence no attempt is made
> to expand it as an alias" (`:533`).

Specific non-aliasable cases stated:
- An expression containing `=` at the start of a command line is an assignment, not
  aliasable (`:540`).
- The `((` token that introduces arithmetic expressions cannot presently be aliased,
  because it cannot be distinguished from two consecutive `(` tokens introducing nested
  subshells (`:545`).
- If a separator such as `&&` is aliased, `\&&` becomes two tokens `\&` and `&`, each
  potentially aliased separately (`:548`). Similarly for `\<<`, `\>|`, etc. (`:549`).

### Alias timing / read-time constraint (`:552–562`)

> "aliases are expanded when the code is read in; the entire line is read in one go, so
> that when `echobar` is executed it is too late to expand the newly defined alias." (`:558`)

This means an alias defined on the same line cannot be used later on that same line.
The manual recommends functions over aliases in non-interactive code (`:561`).

### Function definition interaction (`:481–483`)

> "It is an error for the function name, word, in the sh-compatible function definition
> syntax `word () ...` to be a word that resulted from alias expansion, unless the
> ALIAS_FUNC_DEF option is set." (`:481`)

### Option gates (aliasing)

| option | effect | source |
|---|---|---|
| `POSIX_ALIASES` | "only plain unquoted strings are eligible for aliasing" — narrows the word definition to item 1 only (no quoted strings, param refs, reserved words, etc.) | `:520` |
| `ALIAS_FUNC_DEF` | Allows alias-expanded words to serve as function names in `word () ...` syntax | `:483` |

---

## Precedence / ordering (only from explicit statements)

1. **History expansion** runs first (ordering_inventory §1, §2).
2. **Alias expansion** runs second, before all other expansion — "before any other expansion
   except history expansion" (`:505`; ordering_inventory §3).
3. **Quoting defeats aliasing** — any form of quoting prevents alias expansion for the
   quoted word (`:507`).
4. **Quoting suppresses special character meaning** in later expansion stages (`:565`).
5. **Alias expansion is read-time** — the entire line/block is read, then aliases are
   expanded, before execution of any command on that line (`:558`).

---

## Seams

- **Quoting → all expansion stages**: quoting is the universal gate/defeat mechanism. Every
  expansion stage must check whether its trigger character is quoted.
- **Aliasing → lexer/scanner**: alias expansion is pre-parse; it feeds rewritten text back
  to the lexer. The grammar never sees alias names — it sees replacement text. This means
  alias handling belongs in the scanner or a pre-processing pass, NOT in grammar rules.
- **`$'...'` → print builtin escape processing**: the escape set for `$'...'` is defined by
  the `print` builtin's string processing (`:569`), which is a seam to zshbuiltins.
- **Double quotes → parameter/command substitution**: `"..."` allows `$` and `` ` `` to
  trigger expansion inside (`:583`), which is a seam to the expansion subsystem (Regime A).

---

## Internal structure summary

These two subsystems form the **lexical pre-processing layer** that sits between history
expansion and the parser:

- **Quoting** is a character-level mechanism with four forms (backslash, single, double,
  `$'...'`), each with different rules for what remains special inside. It is cross-cutting:
  it gates aliasing and all downstream expansion.
- **Aliasing** is a word-level text-substitution mechanism with a precisely defined "word"
  vocabulary. It runs at read-time, before parsing, and feeds rewritten text back to the
  lexer. It has three variants (ordinary, global, suffix — suffix not documented here) with
  distinct triggering rules.
- The two interact via a one-way gate: quoting defeats aliasing, never the reverse.

## What this gives the grammar

- **Quoting** must be handled at the token/lexer level: the grammar needs `single_quoted`,
  `double_quoted`, `ansi_quoted` (`$'...'`), and `backslash_escape` token types. Inside
  `double_quoted`, the grammar must allow embedded `$`-expansions and `` ` ``-substitutions
  (recursive token structure).
- **Aliasing** is architecturally pre-grammar. Tree-sitter has no built-in alias expansion
  mechanism, so this will likely need to be handled either (a) by ignoring aliases in the
  grammar (parsing the expanded form), or (b) in an external scanner that performs a
  substitution pass. The "word" definition for aliasing may inform what the lexer considers
  a token boundary.
- **`RC_QUOTES`** is the only quoting option that changes SYNTAX (inserting `''` as an
  escape inside single quotes). `POSIX_ALIASES` narrows what triggers aliasing but does
  not change the grammar's own token types.

---

## Open questions

1. **`$"..."` locale-translated strings**: not mentioned in zshmisc QUOTING. Does zsh
   support this form? If so, where is it documented? (bash has it; zsh may or may not.)

2. **`$'...'` escape set**: the manual says "processed the same way as the string arguments
   of the `print` builtin" (`:569`). The exact escape set (`\n`, `\t`, `\xHH`, `\uHHHH`,
   `\UHHHHHHHH`, `\0NNN`, etc.) is defined in zshbuiltins, not here. Should it be
   enumerated in this map or deferred to a zshbuiltins extraction?

3. **Suffix aliases (`alias -s`)**: not mentioned in the ALIASING section. Where are they
   documented, and do they have different word/triggering rules?

4. **Nested aliasing**: when alias expansion produces text containing another alias name,
   does re-expansion occur? The manual says the "next word" is checked if replacement ends
   with space (`:478`), but does the replacement text itself get re-scanned for aliases?
   The read-time constraint (`:558`) suggests yes (the replacement is re-read), but this is
   not explicitly stated in this section.

5. **Tree-sitter aliasing strategy**: since alias expansion is pre-parse, tree-sitter
   cannot handle it in `grammar.js`. The practical question is whether to (a) ignore it
   entirely (parse expanded text only), (b) treat alias definitions as opaque, or (c) add
   external scanner support. This is an architecture decision, not a manual-extraction
   question.

6. **History character (`$histchars`) inside double quotes**: the manual says `\` quotes
   "the first character of `$histchars` (default `!`)" inside `"..."` (`:584`). Since
   `$histchars` is configurable, the set of characters special inside double quotes is
   technically variable. How should the grammar handle this?
