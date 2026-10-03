"""Bounded shell lexical analysis for guard-bash; never executes shell input."""

import re
import sys

SEP = "\x1f"
REDIR = "\x1e"
MAX_TOKENS = 1024
MAX_DEPTH = 4
MAX_SUBSTITUTIONS = 64
CONTROL_WORDS = {"!", "if", "then", "elif", "else", "fi", "for", "while", "until", "do", "done", "case", "esac", "select", "function", "{", "}"}
DATA_READERS = {"cat", "tee", "grep", "sort", "wc", "head", "tail", "read", "printf", "echo"}
DOUBLE_QUOTED = re.compile(r'[^"\\`$]+')
PLAIN = re.compile(r"[^\s'\"\\; &|()<>`$]+")


class ReviewRequired(Exception):
    pass


class Parser:
    def __init__(self, source):
        self.source = source
        self.length = len(source)
        self.count = 0

    def add(self, tokens, value):
        self.count += 1
        if self.count > MAX_TOKENS:
            raise ReviewRequired("Shell token limit exceeded; review the complete command.")
        tokens.append(value)

    def substitution(self, index, depth):
        if depth >= MAX_DEPTH:
            raise ReviewRequired("Shell substitution depth limit exceeded; review the complete command.")
        if self.source.startswith("$((", index):
            raise ReviewRequired("Arithmetic shell expansion requires review.")
        end, _, _ = self.parse(index + 2, ")", depth + 1)
        return end, self.source[index + 2 : end - 1]

    def backtick(self, index):
        end = index + 1
        while end < self.length:
            if self.source[end] == "\\":
                raise ReviewRequired("Escaped backtick substitution requires review.")
            if self.source[end] == "`":
                return end + 1, self.source[index + 1 : end]
            end += 1
        raise ReviewRequired("Unterminated command substitution requires review.")

    def word(self, index, depth, delimiter=False):
        parts, subs = [], []
        quote = ""
        quoted = False
        while index < self.length:
            char = self.source[index]
            if not delimiter and not quote and self.source.startswith(("$'", '$"'), index):
                raise ReviewRequired("Unsupported shell quoting requires review.")
            if quote == "'":
                end = self.source.find("'", index)
                if end < 0:
                    raise ReviewRequired("Unterminated shell quote requires review.")
                parts.append(self.source[index:end])
                index = end + 1
                quote = ""
                continue
            if char == "\\":
                quoted = True
                if index + 1 >= self.length:
                    raise ReviewRequired("Incomplete shell escape requires review.")
                following = self.source[index + 1]
                if quote == '"' and following not in '$`"\\\n':
                    parts.append("\\")
                    index += 1
                    continue
                if following != "\n":
                    parts.append(following)
                index += 2
                continue
            if char == quote and quote:
                quote = ""
                index += 1
                continue
            if not quote and char in "'\"":
                quoted = True
                quote = char
                index += 1
                continue
            if not quote and char in " \t\n;&|()<>":
                break
            if not delimiter and self.source.startswith("$(", index):
                index, body = self.substitution(index, depth)
                subs.append(body)
                parts.append("__subst__")
                continue
            if not delimiter and char == "`":
                index, body = self.backtick(index)
                subs.append(body)
                parts.append("__subst__")
                continue
            match = PLAIN.match(self.source, index) if not quote else None
            if quote == '"':
                match = DOUBLE_QUOTED.match(self.source, index)
            if match:
                value = match.group()
                parts.append(value)
                index += len(value)
                continue
            parts.append(char)
            index += 1
        if quote:
            raise ReviewRequired("Unterminated shell quote requires review.")
        return index, "".join(parts), quoted, subs

    def heredoc_substitutions(self, body, depth):
        parser = Parser(body)
        subs = []
        index = 0
        while index < parser.length:
            char = body[index]
            if char == "\\" and index + 1 < parser.length and body[index + 1] in "\\$`\n":
                index += 2
            elif body.startswith("$(", index):
                index, substitution = parser.substitution(index, depth)
                subs.append(substitution)
            elif char == "`":
                index, substitution = parser.backtick(index)
                subs.append(substitution)
            else:
                index += 1
        return subs

    def heredocs(self, index, pending, line_tokens, depth):
        segments, words = [], []
        skip_target = False
        for token in line_tokens + [SEP]:
            if skip_target:
                skip_target = False
                continue
            if token == REDIR:
                skip_target = True
            elif token == SEP:
                if words:
                    segments.append(words)
                words = []
            else:
                words.append(token)
        for words in segments:
            first = next((word for word in words if "=" not in word), "")
            base = first.rsplit("/", 1)[-1]
            if base not in DATA_READERS and base != "git":
                raise ReviewRequired("Executable or unsupported heredoc consumer requires review.")
            if base == "git" and (len(words) < 2 or words[1] != "commit"):
                raise ReviewRequired("Unsupported git heredoc consumer requires review.")
        subs = []
        for delimiter, quoted, strip_tabs in pending:
            start = index
            while index < self.length:
                end = self.source.find("\n", index)
                if end < 0:
                    end = self.length
                line = self.source[index:end]
                if (line.lstrip("\t") if strip_tabs else line) == delimiter:
                    if not quoted:
                        subs.extend(self.heredoc_substitutions(self.source[start:index], depth))
                    index = min(end + 1, self.length)
                    break
                index = min(end + 1, self.length)
            else:
                raise ReviewRequired("Unterminated heredoc requires review.")
        return index, subs

    def parse(self, index=0, closing=None, depth=0):
        tokens, subs, pending = [], [], []
        line_start = 0
        command_start = True
        while index < self.length:
            char = self.source[index]
            if char in " \t":
                index += 1
                continue
            if char == "#":
                end = self.source.find("\n", index)
                index = end if end >= 0 else self.length
                continue
            if char == ")" and closing:
                if pending:
                    raise ReviewRequired("Incomplete heredoc inside substitution requires review.")
                return index + 1, tokens, subs
            if char in ";&|()\n":
                if self.source.startswith("((", index) or self.source.startswith(";&", index):
                    raise ReviewRequired("Unsupported shell control flow requires review.")
                if char == "(":
                    if depth >= MAX_DEPTH:
                        raise ReviewRequired("Shell grouping depth limit exceeded; review the complete command.")
                    index, group_tokens, group_subs = self.parse(index + 1, ")", depth + 1)
                    self.add(tokens, SEP)
                    tokens.extend(group_tokens)
                    subs.extend(group_subs)
                    self.add(tokens, SEP)
                    command_start = True
                    continue
                self.add(tokens, SEP)
                command_start = True
                index += 1
                if char == "\n":
                    if pending:
                        index, heredoc_subs = self.heredocs(index, pending, tokens[line_start:], depth)
                        subs.extend(heredoc_subs)
                        pending = []
                    line_start = len(tokens)
                continue
            if char in "<>":
                if self.source.startswith(("<(", ">("), index):
                    raise ReviewRequired("Shell process substitution requires review.")
                if self.source.startswith("<<", index) and not self.source.startswith("<<<", index):
                    index += 2
                    strip_tabs = index < self.length and self.source[index] == "-"
                    index += int(strip_tabs)
                    while index < self.length and self.source[index] in " \t":
                        index += 1
                    index, delimiter, quoted, _ = self.word(index, depth, delimiter=True)
                    if not delimiter:
                        raise ReviewRequired("Empty heredoc delimiter requires review.")
                    pending.append((delimiter, quoted, strip_tabs))
                    continue
                while index < self.length and self.source[index] in "<>&|":
                    index += 1
                self.add(tokens, REDIR)
                continue
            index, word, quoted, word_subs = self.word(index, depth)
            if command_start and not quoted and word in CONTROL_WORDS:
                raise ReviewRequired("Unsupported shell control flow requires review.")
            if not word and not quoted:
                continue
            if "\x00" in word or SEP in word or REDIR in word:
                raise ReviewRequired("Shell control characters require review.")
            self.add(tokens, word)
            subs.extend(word_subs)
            if not re.match(r"[A-Za-z_][A-Za-z0-9_]*=", word):
                command_start = False
        if len(subs) > MAX_SUBSTITUTIONS:
            raise ReviewRequired("Shell substitution count limit exceeded; review the complete command.")
        if closing or pending:
            raise ReviewRequired("Incomplete shell construct requires review.")
        return index, tokens, subs


def main():
    try:
        _, tokens, subs = Parser(sys.stdin.read()).parse()
        records = [("T", value) for value in tokens] + [("S", value) for value in subs]
    except ReviewRequired as error:
        records = [("E", str(error))]
    except Exception:
        records = [("E", "Shell parser failed; review the complete command.")]
    output = "".join(kind + "\x00" + value + "\x00" for kind, value in records + [("Z", "")])
    sys.stdout.buffer.write(output.encode("utf-8"))


if __name__ == "__main__":
    main()
