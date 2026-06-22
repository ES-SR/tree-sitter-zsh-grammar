#include "tree_sitter/array.h"
#include "tree_sitter/parser.h"

#include <stdlib.h>
#include <string.h>
#include <wctype.h>

// External token types. ORDER MUST MATCH the `externals` array in grammar.js.
enum TokenType {
    HEREDOC_ARROW,           // <<   (also pushes a pending heredoc)
    HEREDOC_ARROW_DASH,      // <<-  (strips leading tabs on the close line)
    HEREDOC_START,           // the delimiter word right after the arrow
    SIMPLE_HEREDOC_BODY,     // whole body, raw (quoted) delimiter — no expansions
    HEREDOC_BODY_BEGINNING,  // body up to the first expansion (non-raw delimiter)
    HEREDOC_CONTENT,         // body run between/after expansions
    HEREDOC_END,             // the closing delimiter line
    ERROR_RECOVERY,          // sentinel: parser is in error recovery
};

typedef Array(char) String;

// One pending here-document. zsh allows the body to be deferred past the rest of
// the line, so the runtime-chosen delimiter must be remembered in scanner state
// (this is the non-regular property that forces an external scanner).
typedef struct {
    bool is_raw;        // delimiter was quoted/escaped -> body is literal, no $ expansion
    bool started;       // we have already emitted the BODY_BEGINNING piece
    bool allows_indent; // <<- : leading tabs on the close line are ignored
    String delimiter;
    String current_leading_word;
} Heredoc;

#define heredoc_new()                       \
    {                                       \
        .is_raw = false,                    \
        .started = false,                   \
        .allows_indent = false,             \
        .delimiter = array_new(),           \
        .current_leading_word = array_new(),\
    }

typedef struct {
    Array(Heredoc) heredocs;
} Scanner;

static inline void advance(TSLexer *lexer) { lexer->advance(lexer, false); }
static inline void skip(TSLexer *lexer) { lexer->advance(lexer, true); }
static inline bool in_error_recovery(const bool *valid_symbols) { return valid_symbols[ERROR_RECOVERY]; }

static inline void reset_string(String *s) {
    if (s->size > 0) {
        memset(s->contents, 0, s->size);
        array_clear(s);
    }
}

static inline void reset_heredoc(Heredoc *h) {
    h->is_raw = false;
    h->started = false;
    h->allows_indent = false;
    reset_string(&h->delimiter);
}

static unsigned serialize(Scanner *scanner, char *buffer) {
    uint32_t size = 0;
    buffer[size++] = (char)scanner->heredocs.size;
    for (uint32_t i = 0; i < scanner->heredocs.size; i++) {
        Heredoc *h = array_get(&scanner->heredocs, i);
        if (size + 3 + sizeof(uint32_t) + h->delimiter.size >= TREE_SITTER_SERIALIZATION_BUFFER_SIZE) {
            return 0;
        }
        buffer[size++] = (char)h->is_raw;
        buffer[size++] = (char)h->started;
        buffer[size++] = (char)h->allows_indent;
        memcpy(&buffer[size], &h->delimiter.size, sizeof(uint32_t));
        size += sizeof(uint32_t);
        if (h->delimiter.size > 0) {
            memcpy(&buffer[size], h->delimiter.contents, h->delimiter.size);
            size += h->delimiter.size;
        }
    }
    return size;
}

static void deserialize(Scanner *scanner, const char *buffer, unsigned length) {
    for (uint32_t i = 0; i < scanner->heredocs.size; i++) {
        Heredoc *h = array_get(&scanner->heredocs, i);
        array_delete(&h->delimiter);
        array_delete(&h->current_leading_word);
    }
    array_clear(&scanner->heredocs);

    if (length == 0) {
        return;
    }
    uint32_t size = 0;
    uint32_t count = (unsigned char)buffer[size++];
    for (uint32_t i = 0; i < count; i++) {
        Heredoc h = heredoc_new();
        h.is_raw = buffer[size++];
        h.started = buffer[size++];
        h.allows_indent = buffer[size++];
        uint32_t dsize;
        memcpy(&dsize, &buffer[size], sizeof(uint32_t));
        size += sizeof(uint32_t);
        if (dsize > 0) {
            array_reserve(&h.delimiter, dsize);
            memcpy(h.delimiter.contents, &buffer[size], dsize);
            h.delimiter.size = dsize;
            size += dsize;
        }
        array_push(&scanner->heredocs, h);
    }
}

// Consume the delimiter word after `<<`/`<<-`, recording it unquoted. A quoted or
// backslash-escaped delimiter makes the body raw (no expansion).
static bool advance_word(TSLexer *lexer, String *word) {
    bool empty = true;
    int32_t quote = 0;
    if (lexer->lookahead == '\'' || lexer->lookahead == '"') {
        quote = lexer->lookahead;
        advance(lexer);
    }
    while (lexer->lookahead &&
           !(quote ? (lexer->lookahead == quote || lexer->lookahead == '\r' || lexer->lookahead == '\n')
                   : iswspace(lexer->lookahead))) {
        if (lexer->lookahead == '\\') {
            advance(lexer);
            if (!lexer->lookahead) {
                return false;
            }
        }
        empty = false;
        array_push(word, lexer->lookahead);
        advance(lexer);
    }
    array_push(word, '\0');
    if (quote && lexer->lookahead == quote) {
        advance(lexer);
    }
    return !empty;
}

static bool scan_heredoc_start(Heredoc *h, TSLexer *lexer) {
    while (iswspace(lexer->lookahead)) {
        skip(lexer);
    }
    lexer->result_symbol = HEREDOC_START;
    h->is_raw = lexer->lookahead == '\'' || lexer->lookahead == '"' || lexer->lookahead == '\\';
    bool found = advance_word(lexer, &h->delimiter);
    if (!found) {
        reset_string(&h->delimiter);
        return false;
    }
    return true;
}

// Does the current line (from lookahead) equal the delimiter? Consumes the matched
// prefix; the caller decides what the match means (END vs. content boundary).
static bool scan_heredoc_end_identifier(Heredoc *h, TSLexer *lexer) {
    reset_string(&h->current_leading_word);
    int32_t i = 0;
    if (h->delimiter.size > 0) {
        while (lexer->lookahead != '\0' && lexer->lookahead != '\n' &&
               (int32_t)*array_get(&h->delimiter, i) == lexer->lookahead &&
               h->current_leading_word.size < h->delimiter.size) {
            array_push(&h->current_leading_word, lexer->lookahead);
            advance(lexer);
            i++;
        }
    }
    array_push(&h->current_leading_word, '\0');
    return h->delimiter.size == 0
               ? false
               : strcmp(h->current_leading_word.contents, h->delimiter.contents) == 0;
}

static bool scan_heredoc_content(Scanner *scanner, TSLexer *lexer, enum TokenType middle_type,
                                 enum TokenType end_type) {
    bool did_advance = false;
    Heredoc *h = array_back(&scanner->heredocs);

    for (;;) {
        switch (lexer->lookahead) {
            case '\0': {
                if (lexer->eof(lexer) && did_advance) {
                    reset_heredoc(h);
                    lexer->result_symbol = end_type;
                    return true;
                }
                return false;
            }
            case '\\': {
                did_advance = true;
                advance(lexer);
                advance(lexer);
                break;
            }
            case '$': {
                if (h->is_raw) {
                    did_advance = true;
                    advance(lexer);
                    break;
                }
                if (did_advance) {
                    lexer->mark_end(lexer);
                    lexer->result_symbol = middle_type;
                    h->started = true;
                    advance(lexer);
                    if (iswalpha(lexer->lookahead) || lexer->lookahead == '{' || lexer->lookahead == '(') {
                        return true;
                    }
                    break;
                }
                if (middle_type == HEREDOC_BODY_BEGINNING && lexer->get_column(lexer) == 0) {
                    lexer->result_symbol = middle_type;
                    h->started = true;
                    return true;
                }
                return false;
            }
            case '\n': {
                if (!did_advance) {
                    skip(lexer);
                } else {
                    advance(lexer);
                }
                did_advance = true;
                if (h->allows_indent) {
                    while (iswspace(lexer->lookahead)) {
                        advance(lexer);
                    }
                }
                lexer->result_symbol = h->started ? middle_type : end_type;
                lexer->mark_end(lexer);
                if (scan_heredoc_end_identifier(h, lexer)) {
                    if (lexer->result_symbol == HEREDOC_END) {
                        array_pop(&scanner->heredocs);
                    }
                    return true;
                }
                break;
            }
            default: {
                if (lexer->get_column(lexer) == 0) {
                    while (iswspace(lexer->lookahead)) {
                        if (did_advance) {
                            advance(lexer);
                        } else {
                            skip(lexer);
                        }
                    }
                    if (end_type != SIMPLE_HEREDOC_BODY) {
                        lexer->result_symbol = middle_type;
                        if (scan_heredoc_end_identifier(h, lexer)) {
                            return true;
                        }
                    } else {
                        lexer->result_symbol = end_type;
                        lexer->mark_end(lexer);
                        if (scan_heredoc_end_identifier(h, lexer)) {
                            return true;
                        }
                    }
                }
                did_advance = true;
                advance(lexer);
                break;
            }
        }
    }
}

bool tree_sitter_zsh_external_scanner_scan(void *payload, TSLexer *lexer, const bool *valid_symbols) {
    Scanner *scanner = (Scanner *)payload;

    // Body pieces are dispatched before anything else, since once we are inside a
    // here-document the normal lexer must not look at the bytes.
    if ((valid_symbols[HEREDOC_BODY_BEGINNING] || valid_symbols[SIMPLE_HEREDOC_BODY]) &&
        scanner->heredocs.size > 0 && !array_back(&scanner->heredocs)->started &&
        !in_error_recovery(valid_symbols)) {
        return scan_heredoc_content(scanner, lexer, HEREDOC_BODY_BEGINNING, SIMPLE_HEREDOC_BODY);
    }

    if (valid_symbols[HEREDOC_END] && scanner->heredocs.size > 0) {
        Heredoc *h = array_back(&scanner->heredocs);
        if (scan_heredoc_end_identifier(h, lexer)) {
            array_pop(&scanner->heredocs);
            lexer->result_symbol = HEREDOC_END;
            return true;
        }
    }

    if (valid_symbols[HEREDOC_CONTENT] && scanner->heredocs.size > 0 &&
        array_back(&scanner->heredocs)->started && !in_error_recovery(valid_symbols)) {
        return scan_heredoc_content(scanner, lexer, HEREDOC_CONTENT, HEREDOC_END);
    }

    if (valid_symbols[HEREDOC_START] && !in_error_recovery(valid_symbols) && scanner->heredocs.size > 0) {
        return scan_heredoc_start(array_back(&scanner->heredocs), lexer);
    }

    // `<<` / `<<-` : the arrow itself. Reject `<<<` (here-string) and `<<=`. On a
    // real arrow, push a fresh pending heredoc whose delimiter HEREDOC_START fills.
    if ((valid_symbols[HEREDOC_ARROW] || valid_symbols[HEREDOC_ARROW_DASH]) &&
        !in_error_recovery(valid_symbols)) {
        while (lexer->lookahead == ' ' || lexer->lookahead == '\t') {
            skip(lexer);
        }
        if (lexer->lookahead == '<') {
            advance(lexer);
            if (lexer->lookahead == '<') {
                advance(lexer);
                if (lexer->lookahead == '-') {
                    advance(lexer);
                    Heredoc h = heredoc_new();
                    h.allows_indent = true;
                    array_push(&scanner->heredocs, h);
                    lexer->result_symbol = HEREDOC_ARROW_DASH;
                    return true;
                }
                if (lexer->lookahead == '<' || lexer->lookahead == '=') {
                    return false; // <<<  here-string, or <<=  (not a heredoc)
                }
                Heredoc h = heredoc_new();
                array_push(&scanner->heredocs, h);
                lexer->result_symbol = HEREDOC_ARROW;
                return true;
            }
            return false;
        }
    }

    return false;
}

void *tree_sitter_zsh_external_scanner_create(void) {
    Scanner *scanner = calloc(1, sizeof(Scanner));
    array_init(&scanner->heredocs);
    return scanner;
}

void tree_sitter_zsh_external_scanner_destroy(void *payload) {
    Scanner *scanner = (Scanner *)payload;
    for (uint32_t i = 0; i < scanner->heredocs.size; i++) {
        Heredoc *h = array_get(&scanner->heredocs, i);
        array_delete(&h->delimiter);
        array_delete(&h->current_leading_word);
    }
    array_delete(&scanner->heredocs);
    free(scanner);
}

unsigned tree_sitter_zsh_external_scanner_serialize(void *payload, char *buffer) {
    return serialize((Scanner *)payload, buffer);
}

void tree_sitter_zsh_external_scanner_deserialize(void *payload, const char *buffer, unsigned length) {
    deserialize((Scanner *)payload, buffer, length);
}
