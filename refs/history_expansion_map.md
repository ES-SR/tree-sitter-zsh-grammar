# History expansion map — event / word / modifier sub-grammars

History expansion (per `graph/ASSESSMENT.md`) belongs to Regime A (expansion/pattern
machinery). This file captures the three sub-grammars in the manual's OWN definitions, with
`zshexpn:line` citations. It is a structural map, not yet `grammar.js`. Precedence/structure
here is quoted from the source (cross-checked against `ordering_inventory.md`).

Source: **HISTORY EXPANSION** section, `zshexpn:40–348`.

---

## Structural overview

> "A history expansion begins with the first character of the histchars parameter, which is
> '!' by default" (`:55`)

> "The first character is followed by an optional event designator ... and then an optional
> word designator; if neither of these designators is present, no history expansion occurs."
> (`:60–63`)

> "History expansions do not nest." (`:70`)

Internal order: **event designator** then **word designator** then **modifiers**.
(`ordering_inventory.md` §2, citing `zshexpn:60–70`; modifiers shared with §7.)

> "Input lines containing history expansions are echoed after being expanded, but before any
> other expansions take place and before the command is executed." (`:65–67`)

History expansion runs **first** in the master expansion pipeline (`ordering_inventory.md`
§1, citing `zshexpn:7–9`); it is performed **only in interactive shells** (`:9`).

## Quoting interaction

History expansion may occur "anywhere on the command line, including inside double quotes
(but not inside single quotes `'...'` or C-style quotes `$'...'` nor when escaped with a
backslash)" (`:56–58`).

The `!"` escape: "If the shell encounters the character sequence `!"` in the input, the
history mechanism is temporarily disabled until the current list ... is fully parsed. The
`!"` is removed from the input, and any subsequent `!` characters have no special
significance." (`:96–99`)

Exceptions to `!` starting expansion: "except when followed by a blank, newline, `=` or
`(`" (`:109–110`).

---

## 1. Event designators (`zshexpn:104–134`)

> "An event designator is a reference to a command-line entry in the history list." (`:105`)

> "the initial '!' in each item may be changed to another character by setting the histchars
> parameter." (`:106–107`)

| Form | Meaning (verbatim-sourced) | Citation |
|---|---|---|
| `!` | "Start a history expansion, except when followed by a blank, newline, `=` or `(`. If followed immediately by a word designator ... this forms a history reference with no event designator" | `:109–112` |
| `!!` | "Refer to the previous command. By itself, this expansion repeats the previous command." | `:114–115` |
| `!n` | "Refer to command-line n." | `:117` |
| `!-n` | "Refer to the current command-line minus n." | `:119` |
| `!str` | "Refer to the most recent command starting with str." | `:121` |
| `!?str[?]` | "Refer to the most recent command containing str. The trailing `?` is necessary if this reference is to be followed by a modifier or followed by any text that is not to be considered part of str." | `:123–126` |
| `!#` | "Refer to the current command line typed in so far. The line is treated as if it were complete up to and including the word before the one with the `!#` reference." | `:128–130` |
| `!{...}` | "Insulate a history reference from adjacent characters (if necessary)." | `:132–134` |

### No-event-designator default behavior (`:72–87`)

> "By default, a history reference with no event designator refers to the same event as any
> preceding history reference on that command line; if it is the only history reference in a
> command, it refers to the previous command." (`:72–74`)

> "However, if the option CSH_JUNKIE_HISTORY is set, then every history reference with no
> event specification always refers to the previous command." (`:75–77`)

### Quick substitution — `^foo^bar` (`:89–94`)

> "The character sequence `^foo^bar` (where `^` is actually the second character of the
> histchars parameter) repeats the last command, replacing the string foo with bar." (`:89–91`)

> "More precisely, the sequence `^foo^bar^` is synonymous with `!!:s^foo^bar^`, hence other
> modifiers ... may follow the final `^`. In particular, `^foo^bar^:G` performs a global
> substitution." (`:91–94`)

Note: the `^` character here is configurable — it is the **second** character of `histchars`.

---

## 2. Word designators (`zshexpn:136–156`)

> "A word designator indicates which word or words of a given command line are to be included
> in a history reference." (`:137–138`)

> "A `:` usually separates the event specification from the word designator. It may be
> omitted only if the word designator begins with a `^`, `$`, `*`, `-` or `%`." (`:138–140`)

| Form | Meaning (verbatim-sourced) | Citation |
|---|---|---|
| `0` | "The first input word (command)." | `:143` |
| `n` | "The nth argument." | `:144` |
| `^` | "The first argument. That is, 1." | `:145` |
| `$` | "The last argument." | `:146` |
| `%` | "The word matched by (the most recent) ?str search." | `:147` |
| `x-y` | "A range of words; x defaults to 0." | `:148` |
| `*` | "All the arguments, or a null value if there are none." | `:149` |
| `x*` | "Abbreviates `x-$`." | `:150` |
| `x-` | "Like `x*` but omitting word $." | `:151` |

### `%` restriction (`:153–156`)

> "a `%` word designator works only when used in one of `!%`, `!:%` or `!?str?:%`, and only
> when used after a `!?` expansion (possibly in an earlier command). Anything else results in
> an error, although the error may not be the most obvious one." (`:153–156`)

### Optional `:` rule

The leading `:` between event and word designator **may be omitted** when the word designator
begins with `^`, `$`, `*`, `-`, or `%` (`:139–140`). Otherwise the `:` is required. This
means e.g. `!!^` = `!!:^`, `!!$` = `!!:$`, `!!*` = `!!:*`.

---

## 3. Modifiers (`zshexpn:158–348`)

> "After the optional word designator, you can add a sequence of one or more of the
> following modifiers, each preceded by a `:`." (`:159–160`)

**SEAM (shared modifier grammar):** "These modifiers also work on the result of filename
generation and parameter expansion, except where noted." (`:161–162`) — The modifier
sub-grammar is shared by history expansion, parameter expansion (`ordering_inventory.md`
§4 rule 7, `zshexpn:1389`), and glob qualifiers (`ordering_inventory.md` §7,
`zshexpn:2580–2584`). The `ordering_inventory.md` §7 states: modifiers are "applied left
to right."

| Modifier | Meaning (verbatim-sourced) | Context restrictions | Citation |
|---|---|---|---|
| `:a` | "Turn a file name into an absolute path: prepends the current directory, if necessary; remove `.` path segments; and remove `..` path segments and the segments that immediately precede them." | — | `:164–174` |
| `:A` | "Turn a file name into an absolute path as the `a` modifier does, and then pass the result through the realpath(3) library function to resolve symbolic links." | — | `:176–185` |
| `:c` | "Resolve a command name into an absolute path by searching the command path given by the PATH variable." | "does not work for commands containing directory parts" | `:187–190` |
| `:e` | "Remove all but the part of the filename extension following the `.`" | — | `:193–196` |
| `:h [digits]` | "Remove a trailing pathname component, shortening the path by one directory level: this is the 'head' of the pathname." Digits: "that number of leading components is preserved instead of the final component being removed." | In parameter substitution, digits only inside braces (`${var:h2}` vs `$var:h2`). "No restriction applies to the use of digits in history substitution or globbing qualifiers." | `:198–214` |
| `:l` | "Convert the words to all lowercase." | — | `:216` |
| `:p` | "Print the new command but do not execute it." | "Only works with history expansion." | `:218–219` |
| `:P` | "Turn a file name into an absolute path, like realpath(3)." | — | `:221–228` |
| `:q` | "Quote the substituted words, escaping further substitutions." | "Works with history expansion and parameter expansion" | `:229–232` |
| `:Q` | "Remove one level of quotes from the substituted words." | — | `:234` |
| `:r` | "Remove a filename extension leaving the root name." | — | `:236–241` |
| `:s/l/r[/]` | "Substitute r for l ... The substitution is done only for the first string that matches l." | — | `:243–253` |
| `:gs/l/r[/]` or `:s/l/r/:G` | "perform global substitution, i.e. substitute every occurrence of r for l. Note that the g or :G must appear in exactly the position shown." | — | `:249–251` |
| `:&` | "Repeat the previous s substitution. Like s, may be preceded immediately by a g." | "In parameter expansion the & must appear inside braces, and in filename generation it must be quoted with a backslash." | `:255–258` |
| `:t [digits]` | "Remove all leading pathname components, leaving the final component (tail). This works like `basename`." Digits handled same as `:h`. | — | `:260–265` |
| `:u` | "Convert the words to all uppercase." | — | `:267` |
| `:x` | "Like q, but break into words at whitespace." | "Does not work with parameter expansion." | `:269–270` |

### Substitution details — `s/l/r/` (`:272–308`)

> "By default the left-hand side of substitutions are not patterns, but character strings.
> Any character can be used as the delimiter in place of `/`. A backslash quotes the delimiter
> character." (`:273–274`)

> "The character `&`, in the right-hand-side r, is replaced by the text from the left-hand-
> side l. The `&` can be quoted with a backslash." (`:275–276`)

> "A null l uses the previous string either from the previous l or from the contextual scan
> string s from `!?s`." (`:277–278`)

> "You can omit the rightmost delimiter if a newline immediately follows r" (`:278–279`)

> "the same record of the last l and r is maintained across all forms of expansion." (`:280–281`)

Interpretation of `l` and `r` varies by expansion context:
- In history expansion: "l and r are treated as literal strings" (`:288`)
- In parameter expansion: "replacement of r into the parameter's value is done first, and
  then any additional ... expansions are applied" (`:290–292`)
- In glob qualifiers: "any substitutions or expansions are performed once at the time the
  qualifier is parsed, even before the `:s` expression itself is divided into l and r sides"
  (`:294–296`)

### Modifiers restricted to parameter expansion & filename generation (`:328–348`)

> "The following f, F, w and W modifiers work only with parameter expansion and filename
> generation." (`:328–329`)

| Modifier | Meaning | Citation |
|---|---|---|
| `f` | "Repeats the immediately (without a colon) following modifier until the resulting word doesn't change any more." | `:332–333` |
| `F:expr:` | "Like f, but repeats only n times if the expression expr evaluates to n." Delimiter may be `(`, `[`, `{` with matching close. | `:335–339` |
| `w` | "Makes the immediately following modifier work on each word in the string." | `:341–342` |
| `W:sep:` | "Like w but words are considered to be the parts of the string that are separated by sep." | `:344–347` |

These four (`f`, `F`, `w`, `W`) do NOT work with history expansion — they are listed here only
because the manual lists them in the HISTORY EXPANSION section "to provide a single point of
reference for all modifiers" (`:329–330`).

---

## Option gates

| Option | Effect on history expansion | Citation |
|---|---|---|
| **BANG_HIST** | Controls whether `!` is active for history expansion (when off, `!` has no special meaning). | `zshoptions` (not in zshexpn text; cross-ref) |
| **CSH_JUNKIE_HISTORY** | "every history reference with no event specification always refers to the previous command" (changes no-event-designator default). | `:75–77` |
| **HIST_SUBST_PATTERN** | "l is treated as a pattern of the usual form described in the section FILENAME GENERATION" (makes `:s` LHS a pattern instead of literal string). When set, `l` may start with `#` (anchor to start) and/or `%` (anchor to end). | `:298–314` |

## Configurable characters — `histchars` parameter (`:55–56`, `:89–91`, `:106–107`)

The `histchars` parameter has (at least) three characters:
1. **First character** (default `!`): starts a history expansion (`:55`).
2. **Second character** (default `^`): the quick-substitution character in `^foo^bar` (`:89–91`).
3. **Third character** (default `#`): used for history comments (from `zshparam`; not
   explicitly described in this section).

> "the initial `!` in each item may be changed to another character by setting the histchars
> parameter" (`:106–107`)

---

## Seams

1. **Modifiers shared with parameter expansion and glob qualifiers** — The `:h :t :r :e :s
   :& :a :A :c :l :u :p :P :q :Q :x :g` modifier set is the same grammar used by parameter
   expansion (`${var:h}`, `ordering_inventory.md` §4 rule 7) and glob qualifiers
   (`ordering_inventory.md` §7, `zshexpn:2580`). The `f/F/w/W` modifiers are
   param-expansion/glob-only. The `:p` modifier is history-only. The `:x` modifier does not
   work with parameter expansion. **This is a shared sub-grammar that must be factored.**

2. **Quoting interaction** — history expansion occurs inside `"..."` but not `'...'` or
   `$'...'`; the `!"` escape disables it for the rest of the current list (`:96–99`). This
   interacts with the quoting layer.

3. **HIST_SUBST_PATTERN** — when set, the `:s/l/r/` modifier's LHS becomes a filename-
   generation pattern (`:298–300`), creating a seam to the glob pattern grammar. The `#`/`%`
   anchoring syntax (`:310–313`) overlaps with parameter expansion's `${var#pat}` / `${var%pat}`
   syntax visually but is a different mechanism.

4. **Master expansion pipeline** — history expansion is step 1 of the master pipeline
   (`ordering_inventory.md` §1); it completes before alias expansion, before all other
   expansions. The expanded form is what gets recorded as the history event (`:67`).

---

## Internal structure summary

The history expansion sub-grammar is a **flat, non-nesting, three-stage pipeline**
(`ordering_inventory.md` §2):

```
history_expansion → histchar event_designator? (':')? word_designator? (':' modifier)*
```

Where:
- `histchar` is the first character of `histchars` (default `!`).
- `event_designator` selects which history event (previous command, command N, search, etc.).
- `word_designator` selects which word(s) from that event. The `:` separator between event
  and word may be omitted when word begins with `^ $ * - %`.
- `modifier` transforms the selected text (`:h :t :r :e :s/l/r/ :& :l :u :p :q :Q :x :a :A
  :c :P :g`). Multiple modifiers chain left-to-right (`ordering_inventory.md` §7).

The quick-substitution form `^foo^bar^` is syntactic sugar for `!!:s^foo^bar^` (`:91`).

The `!{...}` brace-insulation form wraps any history reference to delimit it from surrounding
text (`:132–134`).

**Does not nest** (`:70`). Runs only in interactive shells (`:9`). Precedes all other
expansion (`:65–67`, `ordering_inventory.md` §1).

## What this gives the grammar

- Three ordered sub-components (event, word, modifier) composed linearly — no recursion,
  no nesting, no precedence ladder. Simple sequential parse.
- The modifier sub-grammar is a **shared rule** that must be defined once and referenced from
  history expansion, parameter expansion (`${...}`), and glob qualifiers. Context-dependent
  restrictions (`:p` history-only; `:x` not in param-expansion; `f/F/w/W` not in history)
  can be handled by per-context modifier sets or by parse-time validation.
- The `histchars` configurability means the trigger characters are not hardcoded `!` and `^`
  — the grammar must either treat them as configurable tokens or document the assumption of
  defaults.
- Option-gated behavior (CSH_JUNKIE_HISTORY, HIST_SUBST_PATTERN, BANG_HIST) changes
  semantics but not surface syntax, except HIST_SUBST_PATTERN which changes the `:s` LHS
  from literal string to pattern.

---

## Open questions

1. **`histchars` third character:** the third character of `histchars` (default `#`) is
   described in `zshparam` as the history comment character, but the HISTORY EXPANSION section
   of `zshexpn` does not describe it. Does this character participate in the history expansion
   grammar or is it purely a lexer/tokenizer concern (comment stripping)?

2. **`!{...}` internal grammar:** the manual says `!{...}` "insulate[s] a history reference
   from adjacent characters" but does not specify what `...` may contain — presumably any
   valid event+word+modifier sequence, but this is not stated explicitly.

3. **Word designator `n` range:** the manual does not explicitly state the range of valid
   values for `n` in `!n` (event) or `:n` (word). Presumably non-negative integers, but
   are leading zeros accepted? Is there an upper bound?

4. **Delimiter in `s/l/r/`:** "Any character can be used as the delimiter in place of `/`"
   (`:273–274`). Are there characters that cannot serve as delimiters (e.g., the history
   character itself, newline)? The manual does not enumerate exclusions.

5. **`g` modifier prefix vs `:G` suffix:** the manual shows `gs/l/r` and `s/l/r/:G` as
   the two global-substitution forms (`:249–251`), and `g` may also precede `&` (`:255`).
   Is `g` a freestanding modifier that can precede any modifier, or strictly only `s` and
   `&`? The manual only shows those two combinations.

6. **BANG_HIST option:** referenced as the gate for history expansion, but not mentioned
   in the `zshexpn` HISTORY EXPANSION text itself — it is in `zshoptions`. Should the
   grammar treat `BANG_HIST=off` as "history expansion rule does not exist" or as "the `!`
   character is not special"?
