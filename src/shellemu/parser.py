"""Command-line tokenization for the shell emulator."""


class ParseError(Exception):
    """Raised when a raw input line cannot be tokenized."""


def parse_command_line(line):
    """Split a raw input line into a command name and its arguments.

    A character-by-character scan: outside of quotes, whitespace
    separates tokens; inside a pair of matching single or double
    quotes, every character (including whitespace) is taken
    literally and becomes part of the current token. So
    ``cat "my file.txt"`` yields the single argument
    ``my file.txt`` instead of two separate ones.

    Returns a ``(name, args)`` tuple; ``name`` is an empty string
    for a blank or whitespace-only line.
    """
    tokens = []
    current = []
    quote_char = None
    for char in line:
        if quote_char is not None:
            if char == quote_char:
                quote_char = None
            else:
                current.append(char)
        elif char in ("'", '"'):
            quote_char = char
        elif char.isspace():
            if current:
                tokens.append("".join(current))
                current = []
        else:
            current.append(char)
    if quote_char is not None:
        raise ParseError(f"missing closing quote: {quote_char}")
    if current:
        tokens.append("".join(current))
    if not tokens:
        return "", []
    return tokens[0], tokens[1:]
