# Regime B map — command / control-flow skeleton

Regime B (per `graph/ASSESSMENT.md`) is the command grammar, bound by the manual's own
GRAMMAR TERMS (list, sublist, pipeline, command, word), almost entirely in **zshmisc**.
This file captures that skeleton in the manual's OWN definitions, with `zshmisc:line`
citations. It is a structural map, not yet `grammar.js`. Precedence/associativity here is
quoted from the source (cross-checked against `ordering_inventory.md`).

The manual defines the spine top-down in **SIMPLE COMMANDS & PIPELINES** (`:6–73`). The
production hierarchy, verbatim-sourced:

```
list      → sublist ( term sublist )*  [ term ]          ; :59
sublist   → pipeline ( ('&&'|'||') pipeline )*           ; :44  (&&,|| EQUAL prec, LEFT assoc :49)
pipeline  → ['coproc'] ['!'] command ( ('|'|'|&') command )*   ; :21,:36  (not both coproc & ! :40)
command   → simple_command | complex_command            ; (complex_command defined :124)
simple_command → (assignment)* word* (redirection interspersed)*   ; :7  (first word = cmd, rest = args :11)
term      → ';' | '&' | '&|' | '&!' | NEWLINE            ; :60  (term optional on last sublist inside (...)/{...} :61)
```

Key quoted facts:
- "`&&` ... `||` ... Both operators have equal precedence and are left associative." (`:49`)
- `|&` ≡ `2>&1 |` (`:24`, `:712`); `!` inverts pipeline value (`:28`); `coproc` makes a coprocess (`:36`).
- list terminators: `;`, `&`, `&|`, `&!`, newline. `&`/`&|`/`&!` background the **last pipeline** (`:64`).
- "a list can be seen as a set of any shell commands whatsoever, including the complex
  commands below; this is implied wherever the word 'list' appears" (`:70`) — **list is the
  universal recursion point**; every `list` slot in a complex command is the full grammar.

## command alternatives

### simple command (`:7`)
`(assignment)* word+ (redir)*` — assignments precede words; redirections may be interspersed
("anywhere in a simple command", `:594`). For assignment syntax see zshparam (the seam to
parameter handling). The empty-command case (only assignments+redirs, no command word) is
**REDIRECTIONS WITH NO COMMAND** (`:872`) — resolved at runtime via NULLCMD/READNULLCMD/
SH_NULLCMD/CSH_NULLCMD (option-gated; not a syntax difference).

### complex commands (`:124–319`) — each is a `command` alternative
| form | source | notes |
|---|---|---|
| `if list then list (elif list then list)* (else list)? fi` | `:127` | |
| `for name... [in word...] term do list done` | `:133` | `in` only as first name (`:147`); term = newline/`;` |
| `for (( [e1]; [e2]; [e3] )) do list done` | `:150` | arithmetic for; exprs → ARITHMETIC EVALUATION (seam to Regime A) |
| `while list do list done` | `:157` | |
| `until list do list done` | `:161` | |
| `repeat word do list done` | `:165` | word = arith count; SHORT_REPEAT/disabled-in-emulation |
| `case word in ( [(]pat( \| pat)* ) list (;;\|;&\|;\|) )* esac` | `:173` | pat = filename-gen pattern (seam to Regime A); SH_GLOB changes parse (`:178`) |
| `select name [in word... term] do list done` | `:200` | uses PROMPT3, REPLY |
| `( list )` | `:214` | subshell |
| `{ list }` | `:220` | group |
| `{ try-list } always { always-list }` | `:223` | `always` is contextual; no term between `}` and `always` (`:232`) |
| `function [-T] word... [()] [term] { list }` / `word... () [term] { list }` / `word... () [term] command` | `:280` | redir may follow body, stored w/ function (`:300`) |
| `time [ pipeline ]` | `:310` | |
| `[[ exp ]]` | `:316` | exp → CONDITIONAL EXPRESSIONS (seam to Regime A) |

### ALTERNATE / short forms (`:321–388`)
Gated: "only work if sublist is of the form `{ list }` or if SHORT_LOOPS is set"; for
if/while/until the test must also be delimited by `[[...]]` or `((...))` (`:327–334`).
Forms: `if list { list }...` (`:337`), `if list sublist` (`:352`), `for name...( word... ) sublist`
(`:356`), `for name...[in word...] term sublist` (`:359`), `for ((...)) sublist` (`:363`),
`foreach name...( word... ) list end` (`:366`), `while list { list }` (`:369`),
`until list { list }` (`:373`), `repeat word sublist` (`:377`),
`case word { ... }` (`:380`), `select name [in...] sublist` (`:383`),
`function word... [()] [term] sublist` (`:386`). Gated by **SHORT_LOOPS / SHORT_REPEAT**.

## reserved words (terminals) (`:389–398`)
Recognized as reserved **only as the first word of a command** unless quoted / `disable -r`:
> do done esac then elif else fi for case if while function repeat time until select coproc
> nocorrect foreach end ! [[ { } declare export float integer local readonly typeset
Plus `}` recognized in any position unless IGNORE_BRACES / IGNORE_CLOSE_BRACES (`:397`).
Note `nocorrect` is a reserved word but acts as a precommand modifier; `declare export float
integer local readonly typeset` are reserved (assignment-context keywords).

## precommand modifiers (`:75–123`)
`simple_command` may be preceded by a precommand modifier; all are builtins **except
`nocorrect`** (reserved word, must come first, interpreted before parsing, `:114`).
Set: `-` (`:80`), `builtin` (`:82`), `command [-pvV]` (`:86`), `exec [-cl] [-a argv0]` (`:95`),
`nocorrect` (`:114`), `noglob` (`:120`).

## I/O sub-cluster — redirection (`:587–719`, `:721`, `:771`, `:872`)
Attachment rule (structural): redirections "may appear **anywhere in a simple command** or
may **precede or follow a complex command**" (`:594`). Optional leading digit = fd (`:698`).
**Order is significant**, evaluated L-to-R (`:700`; ordering_inventory §9).

Operators (verbatim from `:600–696`):
- input: `< word`, `<> word`
- output: `> word`, `>| word` / `>! word`, `>> word`, `>>| word` / `>>! word`
- heredoc: `<<[-] word` (`:630`), here-string: `<<< word` (`:653`)
- fd dup/close/coproc: `<& number` / `>& number` (`:659`), `<& -` / `>& -` (`:664`),
  `<& p` / `>& p` (`:667`)
- combined out+err: `>& word` / `&> word` (`:671`), `>&| >&! &>| &>!` (`:679`),
  `>>& &>>` (`:686`), `>>&| >>&! &>>| &>>!` (`:691`)
- **param-fd allocation**: `{varid}>...` / `{varid}>&-` (`:721`) — valid shell identifier in
  braces instead of digit; no whitespace before operator; **not** around complex commands
  (`:754`); gated by **IGNORE_BRACES** (`:722`).
- **MULTIOS** (`:771`): multiple write/read redirs → implicit tee/cat; gated by **MULTIOS**
  option; word after redir also globbed (`:805`).
- process substitution `<(list)` `=(list)` `>(list)` used with redirection (`:715`) — but
  defined in zshexpn (Regime A seam).

## command execution / word resolution (`:896–927`)
Runtime resolution order for a slashless command word (NOT parse precedence, but fixes what
`command`/`builtin` modifiers override): function → builtin → `$path` search → (fail 127/126)
→ shell-script / `#!` → `command_not_found_handler`. `builtin`/`command` modifiers force a
branch.

## functions (`:929–1100`)
Defined via `function` reserved word or `funcname ()` syntax (`:929`). Body = `list` between
`{ }`. AUTOLOADING (`:946`), ANONYMOUS (`:1058`, `() { ... } args`), SPECIAL/hook/trap (`:1101`).
All resolve to the `function`/`word ()` complex-command forms above.

---

## Internal structure summary (the Regime-B dependency picture)

The regime is a **single recursive containment tree**, not loosely-coupled like Regime A:
- **Spine** (`list ⊃ sublist ⊃ pipeline ⊃ command`) is the backbone; every section below
  plugs a node into it.
- **`command`** is the fan-out: `simple_command` ∪ {13 complex-command forms} ∪ {short forms}.
- **`list`** is the universal recursion point (`:70`) — re-entered by every complex command's
  body slot, closing the tree.
- **redirection** is an orthogonal decorator on both `simple_command` and `complex_command`.
- **reserved words** are the terminal set that disambiguates `command` alternatives, gated by
  first-word position.
- **precommand modifiers** decorate `simple_command`.

## Seams OUT of Regime B (into Regime A / arithmetic / conditionals)
1. `simple_command` **words & assignments → expansion** (the master word↔expansion seam).
2. `for (( ))` exprs, `repeat word`, `(( ))` test → **ARITHMETIC EVALUATION**.
3. `case` patterns → **FILENAME GENERATION** pattern grammar.
4. `[[ exp ]]` → **CONDITIONAL EXPRESSIONS**.
5. process substitution operands → **zshexpn Process Substitution**.

## Option switches that change Regime-B SYNTAX (cross-cutting layer)
- **SHORT_LOOPS / SHORT_REPEAT** — enable alternate/short complex-command forms (`:328,:334`).
- **SH_GLOB** — changes `case` pattern parse (`:178`) and `func ()` whitespace parse (`:295`).
- **IGNORE_BRACES / IGNORE_CLOSE_BRACES** — `}` recognition (`:397`) and `{varid}>` redir (`:722`).
- **MULTIOS** — multiple-redirection tee/cat semantics (`:771`).
- **CLOBBER / APPEND_CREATE** — `>`/`>>` error behavior (not syntax, but `>|`/`>!` exist to
  override, so they're syntactic variants, `:614,:625`).
- **POSIX_BUILTINS** — `command` modifier behavior (`:88`).
- **NULLCMD/READNULLCMD/SH_NULLCMD/CSH_NULLCMD** — redirections-with-no-command (`:872`).

## What this gives the grammar
The top-level `grammar.js` skeleton is essentially the spine + the `command` fan-out, with:
- `_list`/`_sublist`/`pipeline` as left-assoc binary chains (`&&`/`||` equal prec; `|`/`|&`
  tighter than `&&`/`||`; `!`/`coproc`/`time` as pipeline prefixes),
- each complex command a named rule whose body slots recurse to `_list`,
- `redirection` as a repeatable element attachable to simple & complex commands,
- reserved words as a `token`-level keyword set valid in command-first position,
- the five seams as references to the (separately-built) Regime A rules.
