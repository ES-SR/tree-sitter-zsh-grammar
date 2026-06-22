/**
 * tree-sitter-zsh — grammar SKELETON
 *
 * Built from scratch from the zsh manual deep-read maps in refs/:
 *   - regime_b_map.md          spine (list>sublist>pipeline>command) + command fan-out + I/O
 *   - ordering_inventory.md     all sanctioned precedence (incl. §11 conditional, impl-determined)
 *   - conditional_expressions_map.md   [[ ]] internals (real structure)
 *   - parameter_expansion_map.md, filename_generation_map.md, arithmetic_map.md,
 *     minor_expansions_map.md, history_expansion_map.md, quoting_aliasing_map.md
 *
 * SCOPE: the command/control-flow skeleton (Regime B) is structured for real; Regime-A interiors
 * (${...}, $((...)), glob patterns, brace expansion) are PERMISSIVE STUBS — named rules that accept
 * the construct without imposing its full internal structure, fleshed out cluster-by-cluster.
 *
 * EXTERNAL SCANNER (src/scanner.c): here-documents (runtime delimiter + body deferred past the
 * line = non-regular; see README "The external scanner"). Glob flags (#X), glob groups (a|b),
 * numeric ranges <n-m> and glob qualifiers are handled in-grammar as tokens/groups (not yet
 * decomposed). Still approximated, scanner deferred until pure-grammar gains slow: precise word
 * concatenation, lexical aliasing, the (#q...) free-form / (( vs ( ( / [ overloads, and the
 * balanced-delimiter ${(s:.:)...} flag bodies. See README.md for status, build, and coverage.
 */

// Precedence ladders — values trace to refs/ordering_inventory.md
const PREC = {
  // §11 conditional-expression operators (IMPLEMENTATION-determined: ! > && > ||, left-assoc)
  cond_or: 1,
  cond_and: 2,
  cond_not: 3,
  cond_binary: 4,
  cond_unary: 5,
  // command spine
  and_or: 2,    // sublist &&/|| — equal precedence, left-assoc (zshmisc:49)
  pipe: 3,      // pipeline | |& — tighter than &&/||
};

module.exports = grammar({
  name: 'zsh',

  word: $ => $.word,

  // External scanner (src/scanner.c) — here-documents only, for now. The body
  // delimiter is chosen at runtime and must be remembered across the rest of the
  // line: a non-regular dependency the generated lexer cannot express. ORDER must
  // match `enum TokenType` in src/scanner.c.
  externals: $ => [
    $._heredoc_arrow,            // <<
    $._heredoc_arrow_dash,       // <<-
    $.heredoc_start,             // delimiter word
    $.simple_heredoc_body,       // raw body (quoted delimiter)
    $._heredoc_body_beginning,   // body up to first expansion
    $.heredoc_content,           // body between expansions
    $.heredoc_end,               // closing delimiter line
    $._error_recovery,           // sentinel (never used in a rule)
  ],

  extras: $ => [
    /[ \t\r]+/,
    $.line_continuation,
    $.comment,
  ],

  conflicts: $ => [
    // `if [[ ]] / (( )) / ( )` — the test may be the classic `_list` condition (→ `then`)
    // or the SHORT brace-form `_test_command` (→ `{`); only the following token disambiguates.
    [$._complex_command, $._test_command],
    // dangling elif/else across nested brace-form ifs — attach to the innermost.
    [$.if_command],
    // `[[ ( … ` — a `(` may open a cond_group `( expr )` or a glob_group `(a|b)` that
    // starts a comparison's LHS pattern; only the inside (`||` vs `|`, or a trailing op)
    // disambiguates. GLR explores both.
    [$._cond_expr, $._cond_pattern],
  ],

  rules: {
    // ===================================================================
    // Spine: program > list > sublist > pipeline > command   (regime_b_map.md, zshmisc:6-73)
    // ===================================================================
    program: $ => optional($._list),

    // list = sublists separated/terminated by terminators (zshmisc:59)
    _list: $ => prec.right(seq(
      repeat('\n'),
      $._sublist,
      repeat(seq($._terminator, $._sublist)),
      optional($._terminator),
    )),

    // sublist = pipelines joined by && / || (equal prec, left-assoc — zshmisc:49)
    _sublist: $ => choice(
      $._pipeline,
      $.and_or,
    ),
    and_or: $ => prec.left(PREC.and_or, seq(
      field('left', $._sublist),
      field('operator', choice('&&', '||')),
      repeat('\n'),
      field('right', $._sublist),
    )),

    // pipeline = commands joined by | / |& ; optional !/coproc/time prefix (zshmisc:21,:36).
    // A prefix applies to a pipeline of ANY length, so `time ( … )` / `! cmd` / `coproc cmd`
    // (no `|`) is a pipeline too. The unprefixed form needs ≥1 `|` (else it's just a command).
    _pipeline: $ => choice($._command, $.pipeline),
    pipeline: $ => prec.left(PREC.pipe, choice(
      seq(
        field('prefix', choice('!', 'coproc', 'time')),
        $._command,
        repeat(seq(field('operator', choice('|', '|&')), repeat('\n'), $._command)),
      ),
      seq(
        $._command,
        repeat1(seq(field('operator', choice('|', '|&')), repeat('\n'), $._command)),
      ),
    )),

    // terminator: keep the meaningful separator, swallow trailing blank lines
    _terminator: $ => seq(
      choice(';', '&', '&|', '&!', '\n'),
      repeat('\n'),
    ),

    // ===================================================================
    // command fan-out (regime_b_map.md, zshmisc:124-388)
    // ===================================================================
    _command: $ => choice(
      $.simple_command,
      $._complex_command,
      $.redirected_command,
      $.heredoc_command,
    ),

    // A command whose line carries a here-document. The body is deferred past the
    // rest of the line, so everything from `<<` through the closing delimiter lives
    // in heredoc_redirect; trailing args/redirects on the same line are absorbed
    // there too (they cannot be siblings — the body must stay contiguous in source).
    // SCOPE v1: a single heredoc per command; multi-heredoc lines (`<<A <<B`) still
    // fall to ERROR as before. <<< here-strings are unaffected (regular operator).
    // Usually a command leads (`cat <<EOF`). The leading command is OPTIONAL so a BARE
    // `<<EOF` (no command) also parses — a redirect-only command feeding the body to the
    // default sink — which is the `$(<<EOF … )` / `$(<<-"EOF" | tee … )` idiom for
    // capturing a here-document as a value (a deliberate dev pattern of this user's).
    // Trade-off (measured): bare `<<` is now in the command-start FIRST set, which
    // perturbs error-RECOVERY on entries already broken for unrelated reasons (e.g.
    // `(#i)` globs) — ~69 such entries collapse harder. It breaks ZERO valid, previously
    // -clean entries (the one new break is zsh-invalid input), and nets +38 clean.
    heredoc_command: $ => seq(
      optional(field('command', $.simple_command)),
      repeat1($.heredoc_redirect),
    ),
    heredoc_redirect: $ => seq(
      field('operator', choice($._heredoc_arrow, $._heredoc_arrow_dash)),
      field('delimiter', $.heredoc_start),
      repeat(field('argument', $._word)),
      repeat(field('redirect', $.redirect)),
      // Same-line pipe / && / || tail. It must be absorbed HERE (not left as a
      // sibling pipeline) because the body token follows the whole line: the tree
      // has `cat <<EOF | tee` with the pipe nested under the redirect. `cat<<X | tee`
      // is a common save idiom. (mirrors bash's _heredoc_pipeline/_heredoc_expression)
      optional($._heredoc_pipeline),
      optional($._heredoc_and_or),
      '\n',
      field('body', choice($._heredoc_body, $._simple_heredoc_body)),
    ),
    _heredoc_pipeline: $ => prec.left(repeat1(
      seq(field('operator', choice('|', '|&')), repeat('\n'), $._command),
    )),
    _heredoc_and_or: $ => seq(
      field('operator', choice('&&', '||')), repeat('\n'),
      field('right', $._sublist),
    ),
    _heredoc_body: $ => seq($.heredoc_body, $.heredoc_end),
    heredoc_body: $ => seq(
      $._heredoc_body_beginning,
      repeat(choice(
        $.expansion,
        $.simple_expansion,
        $.command_substitution,
        $.arithmetic_expansion,
        $.heredoc_content,
      )),
    ),
    _simple_heredoc_body: $ => seq(
      alias($.simple_heredoc_body, $.heredoc_body),
      $.heredoc_end,
    ),
    // redirections may precede or follow a complex command (regime_b_map.md, zshmisc:594)
    _complex_command: $ => choice(
      $.subshell,
      $.brace_group,
      $.if_command,
      $.for_command,
      $.c_for_command,
      $.while_command,
      $.until_command,
      $.repeat_command,
      $.case_command,
      $.select_command,
      $.function_definition,
      $.conditional_command,
      $.arithmetic_command,
    ),
    redirected_command: $ => prec.right(seq(
      $._complex_command,
      repeat1($.redirect),
    )),

    // simple command: assignments* word* redirects (interspersed) — zshmisc:7
    // plus the redirections-with-no-command form (zshmisc:872)
    simple_command: $ => prec.right(choice(
      seq(
        repeat($._assignment_or_redirect),
        field('name', $._word),
        repeat($._argument_or_redirect),
      ),
      repeat1($._assignment_or_redirect),
    )),
    _assignment_or_redirect: $ => choice($.variable_assignment, $.redirect),
    // array assignments also appear as ARGUMENTS to assignment-builtins
    // (`local -a x=(...)`, `typeset A=(...)`, `declare ...`) — extremely common in fn bodies.
    _argument_or_redirect: $ => choice($._word, $.redirect, $.variable_assignment),

    // assignment (seam to zshparam). STUB: only the array form is structured here, because a
    // scalar `VAR=value` already lexes harmlessly as a single `word` (= is a word char). The
    // `name=` / `name[sub]=` / `name+=` token only wins over `word` when it cannot extend as a
    // word (i.e. immediately followed by `(` for an array). Full assignment grammar TBD.
    variable_assignment: $ => seq(
      field('name', $.assignment_name),
      optional(field('value', $.array)),
    ),
    assignment_name: $ => token(/[A-Za-z_][A-Za-z0-9_]*(\[[^\]]*\])?\+?=/),
    // array literal `(a b c)` / assoc `([key]=val …)`. Glob constructs are allowed as
    // elements so a glob-keyed assoc element `[(0|(#i)Reset)]=x` parses (the `[`/`]=x`
    // lex as words; the `(0|(#i)Reset)` is a glob_group). Permissive: no key/value structure.
    array: $ => seq(token.immediate('('), repeat(choice(
      $._word, $.glob_group, $.numeric_range, '\n',
    )), ')'),

    // ---- complex commands ----
    // if/while/until/repeat have an alternate SHORT brace-body form (zshmisc:337-377).
    // The brace-form TEST must be self-delimiting ([[ ]] / (( )) / ( )); a bare-command test
    // does NOT work there (manual: `if true { } # Does not work!`, :341). So the brace
    // condition is a &&/|| chain of self-delimiting tests, NOT a general list — this is what
    // stops the `{ }` body from being swallowed as a brace_group command in the condition.
    _test_command: $ => choice($.conditional_command, $.arithmetic_command, $.subshell),
    _brace_condition: $ => prec.left(seq(
      optional('!'), $._test_command,
      repeat(seq(choice('&&', '||'), repeat('\n'), optional('!'), $._test_command)),
    )),

    if_command: $ => choice(
      seq('if', field('condition', $._list),
          'then', field('consequence', $._list),
          repeat($.elif_clause), optional($.else_clause), 'fi'),
      seq('if', field('condition', $._brace_condition),
          field('consequence', $.brace_group),
          repeat($.elif_brace_clause), optional($.else_brace_clause)),
    ),
    elif_clause: $ => seq('elif', $._list, 'then', $._list),
    else_clause: $ => seq('else', $._list),
    elif_brace_clause: $ => seq('elif', field('condition', $._brace_condition), $.brace_group),
    else_brace_clause: $ => seq('else', $.brace_group),

    // for name [in word... | ( word... )] term body   (zshmisc:133; short forms :356-361)
    //   body = do…done OR { list } (the SHORT_LOOPS brace form). `( word... )` is the
    //   parenthesised word-source; both it and `{ }` are self-delimiting (no ambiguity).
    // `name` is repeatable: `for k v in ...` / `for k v ( ... )` iterate the words in
    // groups of N over the N names (zshmisc:133 "for name ..."). Keyword `in` and `(` are
    // not words (keyword-extraction makes `in` lex as a keyword), so the greedy name list
    // stops cleanly before the word-source.
    for_command: $ => seq(
      'for', repeat1(field('variable', $._word)),
      optional(choice(
        seq('in', repeat($._word)),
        seq('(', repeat($._word), ')'),
      )),
      optional($._terminator),
      field('body', choice($.do_group, $.brace_group)),
    ),
    // for (( e1 ; e2 ; e3 )) body (zshmisc:150; short form :363)
    c_for_command: $ => seq(
      'for', '((',
      optional($._arith_segment), ';',
      optional($._arith_segment), ';',
      optional($._arith_segment), '))',
      optional($._terminator),
      field('body', choice($.do_group, $.brace_group)),
    ),
    while_command: $ => seq('while', choice(
      seq(field('condition', $._list), $.do_group),
      seq(field('condition', $._brace_condition), $.brace_group),
    )),
    until_command: $ => seq('until', choice(
      seq(field('condition', $._list), $.do_group),
      seq(field('condition', $._brace_condition), $.brace_group),
    )),
    repeat_command: $ => seq('repeat', field('count', $._word), optional($._terminator),
      field('body', choice($.do_group, $.brace_group))),
    do_group: $ => seq('do', $._list, 'done'),

    // case word in ( pat | pat ) list ;; ... esac (zshmisc:173)
    case_command: $ => seq(
      'case', field('value', $._word), optional($._terminator),
      'in', repeat('\n'),
      repeat($.case_item),
      'esac',
    ),
    case_item: $ => seq(
      optional('('),
      $.case_pattern,
      repeat(seq('|', $.case_pattern)),
      ')',
      optional($._list),
      choice(';;', ';&', ';|'),
      repeat('\n'),
    ),
    case_pattern: $ => $._word,   // SEAM -> filename-generation pattern grammar (stub)

    select_command: $ => seq(
      'select', field('variable', $._word),
      optional(seq('in', repeat($._word))),
      optional($._terminator),
      $.do_group,
    ),

    // function forms (zshmisc:280-282, :386, anonymous :1059-1062)
    //   function [-T] word ... [()] [term] body   -- keyword-led: multi-name SAFE
    //   word () [term] body                        -- name-form: single name OR anonymous ()
    // The name-form multi-name variant (`a b ()`) is omitted: rare ("usually only useful for
    // setting traps", zshmisc:284) and indistinguishable from a simple command until the `()`,
    // which forces a simple_command/function_definition conflict that mis-parses ordinary
    // multi-word commands (A/B: 650 regressions). Multi-name is recovered via the keyword form.
    // Trailing args: an ANONYMOUS function is immediately CALLED and may take positional args —
    // `() { print $1 } hello` (zshmisc:1059-1062). Accepted on both forms (a no-op for named defs).
    function_definition: $ => choice(
      seq('function', repeat(field('name', $._word)), optional(seq('(', ')')),
          optional($._terminator), field('body', $._function_body),
          repeat(field('argument', $._word))),
      seq(optional(field('name', $._word)), '(', ')',
          optional($._terminator), field('body', $._function_body),
          repeat(field('argument', $._word))),
    ),
    _function_body: $ => choice($.brace_group, $.subshell),

    subshell: $ => seq('(', $._list, ')'),
    brace_group: $ => seq('{', $._list, '}', optional($.always_clause)),
    always_clause: $ => seq('always', '{', $._list, '}'),

    // (( ... )) arithmetic command (arithmetic_map.md; ≡ let)
    arithmetic_command: $ => seq('((', optional($._arithmetic), '))'),

    // ===================================================================
    // Redirection (regime_b_map.md I/O, zshmisc:587-719). order-significant.
    // `<<<` here-string is a fixed operator (below); `<<`/`<<-` here-documents are handled by
    // heredoc_command/heredoc_redirect via the external scanner (src/scanner.c).
    // ===================================================================
    redirect: $ => prec.left(seq(
      field('operator', $._redirect_operator),
      field('destination', $._word),
    )),
    _redirect_operator: $ => token(seq(
      optional(/\d+/),
      choice(
        '<', '<>', '<<<',
        '>', '>|', '>!', '>>', '>>|', '>>!',
        '<&', '>&', '&>', '>&|', '>&!', '&>|', '&>!',
        '>>&', '&>>', '>>&|', '>>&!', '&>>|', '&>>!',
      ),
    )),

    // ===================================================================
    // Conditional expressions [[ ... ]]  — REAL structure
    // precedence ! > && > ||, left-assoc (ordering_inventory §11, impl-determined)
    // (conditional_expressions_map.md)
    // ===================================================================
    conditional_command: $ => seq('[[', $._cond_expr, ']]'),
    _cond_expr: $ => choice(
      $.cond_unary,
      $.cond_binary,
      $.cond_and,
      $.cond_or,
      $.cond_negation,
      $.cond_group,
      $._word,                                   // bare-word ≡ -n word (zshmisc:1787)
    ),
    cond_negation: $ => prec(PREC.cond_not, seq('!', $._cond_expr)),
    cond_and: $ => prec.left(PREC.cond_and, seq($._cond_expr, '&&', repeat('\n'), $._cond_expr)),
    cond_or: $ => prec.left(PREC.cond_or, seq($._cond_expr, '||', repeat('\n'), $._cond_expr)),
    cond_group: $ => seq('(', $._cond_expr, ')'),
    cond_unary: $ => prec(PREC.cond_unary, seq(field('operator', $._cond_unary_op), $._cond_pattern)),
    cond_binary: $ => prec(PREC.cond_binary, seq(
      $._cond_pattern, field('operator', $._cond_binary_op), $._cond_pattern,
    )),
    // An operand is a PATTERN: a concatenation of words/expansions, glob flags
    // (`(#i)y`, `(#ia2)$P`) and glob groups (`(integer|scalar)*`, `(0|(#i)Reset)`).
    // Only reached after a conditional operator, so a `(` here is unambiguously a glob
    // group (never the cond_group `( … )`, which lives at expression position). Accepted
    // permissively (no glob structure beyond the flag token + alternation).
    _cond_pattern: $ => prec.right(repeat1(choice($._word, $.glob_group, $.numeric_range))),
    glob_group: $ => seq('(', $._cond_pattern, repeat(seq('|', $._cond_pattern)), ')'),
    // numeric range glob `<min-max>` (`<0->`, `<->`, `<1-100>`) — zshexpn filename generation.
    // `<`/`>` aren't word chars; this token only fires in pattern position so it never shadows
    // the `<`/`>` comparison operators or redirections.
    numeric_range: $ => token(/<[0-9]*-[0-9]*>/),
    _cond_unary_op: $ => token(choice(
      '-a', '-b', '-c', '-d', '-e', '-f', '-g', '-h', '-k', '-n', '-o', '-p',
      '-r', '-s', '-t', '-u', '-v', '-w', '-x', '-z',
      '-L', '-O', '-G', '-S', '-N',
    )),
    _cond_binary_op: $ => token(choice(
      '-nt', '-ot', '-ef',
      '-eq', '-ne', '-lt', '-gt', '-le', '-ge',
      '==', '!=', '=~', '=', '<', '>',
    )),

    // ===================================================================
    // Expansions (Regime A seams) — STUBS, see maps for full grammar
    // ===================================================================
    _word: $ => choice(
      $.word,
      $.glob_qualified,
      $.glob_flag,
      $.string,
      $.raw_string,
      $.ansi_c_string,
      $.simple_expansion,
      $.expansion,
      $.command_substitution,
      $.arithmetic_expansion,
      $.process_substitution,
    ),

    // filename-generation glob qualifier(s)/group attached to a pattern: `**/*(^/)`,
    // `*(N/)`, `*(#i)(mkv|mp4)`. token.immediate = no space before `(` (distinguishes a
    // subshell); content has no spaces or nested parens (so `name=(a b c)` arrays and
    // `foo()` funcs are untouched). One-level approximation; full glob-qual grammar TBD.
    glob_qualified: $ => prec.right(seq(
      $.word,
      repeat1($._glob_qualifier),
    )),
    _glob_qualifier: $ => token.immediate(/\([^()\s]+\)/),

    // globbing flag `(#X)` (filename_generation_map.md:134-161, zshexpn:1973-2140) — EXTENDED_GLOB.
    // Flags affect text to their right; combinable in one group: i l I b B cN,M m M aN s e q u U.
    // `(#` immediately followed by a flag letter distinguishes it from a subshell `( …`. The `q`
    // flag's "rest-to-) ignored" free-form body (rare) is not covered by this token.
    glob_flag: $ => token(/\(#[A-Za-z][A-Za-z0-9,]*\)/),

    // $name and $special  (parameter_expansion_map.md short form)
    simple_expansion: $ => token(seq('$', choice(
      /[A-Za-z_][A-Za-z0-9_]*/,
      /[0-9]/,
      /[!@*#?$\-]/,
    ))),

    // ${ ... }  — PERMISSIVE body (parameter_expansion_map.md: full 25-rule pipeline TBD).
    // The body mixes (flags), operators (//,##,%,:-,…), subscripts [..], nested expansions,
    // and quotes/$'..' arbitrarily; we don't structure it yet, only ACCEPT it without error.
    // Quotes and nested expansions are named atoms so their interior `}`/`$` is protected;
    // a stray-special fallback catches a lone $/'/"/` that doesn't open a valid construct.
    expansion: $ => seq('${', optional($._expansion_body), '}'),
    _expansion_body: $ => repeat1($._expansion_atom),
    _expansion_atom: $ => choice(
      $.expansion,
      $.arithmetic_expansion,
      $.command_substitution,
      $.simple_expansion,
      $.string,
      $.raw_string,
      $.ansi_c_string,
      seq('{', optional($._expansion_body), '}'),   // balanced nested braces
      token(/\\./),                                  // escaped char (\" \} \$ …) — keep as a unit
      token(prec(-1, /[^{}$'"`\\]+/)),
      token(prec(-2, /[$'"`]/)),                     // stray special-char fallback
    ),

    // $( list ) and `...`  (minor_expansions_map.md)
    command_substitution: $ => choice(
      seq('$(', optional($._list), ')'),
      seq('`', repeat(token(prec(-1, /[^`]+/))), '`'),
    ),

    // $(( ... ))  (minor_expansions_map.md -> arithmetic_map.md). STUB interior.
    arithmetic_expansion: $ => seq('$((', optional($._arithmetic), '))'),

    // <(list) >(list) =(list)  (minor_expansions_map.md)
    process_substitution: $ => seq(choice('<(', '>(', '=('), optional($._list), ')'),

    // arithmetic interior STUB: arbitrarily-nested balanced parens (arithmetic_map.md TBD).
    // Recursive so `$(( (a+b)*(c-(d)) ))`, nested `$(( ))`, and `$(...)`/`${..}` whose parens
    // sit inside the expression all balance instead of collapsing to ERROR. No operator
    // structure yet — only error-free acceptance.
    _arithmetic: $ => repeat1($._arith_atom),
    _arith_atom: $ => choice(
      token(prec(-1, /[^()]+/)),
      seq('(', optional($._arithmetic), ')'),
    ),
    // c-for segment: same nesting tolerance, but also stops at the `;` field separator.
    _arith_segment: $ => repeat1(choice(
      token(prec(-1, /[^;()]+/)),
      seq('(', optional($._arithmetic), ')'),
    )),

    // ===================================================================
    // Quoting (quoting_aliasing_map.md, zshmisc:564-586)
    // ===================================================================
    string: $ => seq('"', repeat(choice(
      token.immediate(prec(1, /[^"`$\\]+/)),
      /\\./,
      $.simple_expansion,
      $.expansion,
      $.command_substitution,
      $.arithmetic_expansion,
      token(prec(-1, '$')),   // literal $ not opening an expansion (e.g. "$'", "$ ")
    )), '"'),
    raw_string: $ => token(seq("'", /[^']*/, "'")),
    ansi_c_string: $ => token(seq("$'", /([^'\\]|\\.)*/, "'")),

    // ===================================================================
    // Lexical bits
    // ===================================================================
    // bare word: runs of non-special chars + escapes. Permissive (globs/braces/= are literal
    // here for now; structured later). Excludes whitespace, quotes, $, | & ; < > ( ) # \
    word: $ => token(prec(-1, repeat1(choice(
      /[^ \t\r\n'"`$|&;<>()#\\]/,
      /\\./,
    )))),

    comment: $ => token(prec(-10, /#[^\n]*/)),
    line_continuation: $ => token(seq('\\', '\n')),
  },
});
