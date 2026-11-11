"""The Markdown subset tack's documentation uses, rendered to HTML with every piece of text escaped.

Headings, paragraphs, flat lists, tables, fenced code, quotes and inline code, emphasis and links.
Raw HTML blocks are skipped rather than passed through, so a document cannot inject markup.
"""
import html
import re

FENCE = re.compile(r'^\s*```\s*([\w+-]*)\s*$')
HEADING = re.compile(r'^(#{1,6})\s+(.*?)\s*#*\s*$')
BULLET = re.compile(r'^\s*[-*+]\s+(.*)$')
NUMBERED = re.compile(r'^\s*\d+[.)]\s+(.*)$')
RULE = re.compile(r'^\s*(-{3,}|\*{3,}|_{3,})\s*$')
DIVIDER = re.compile(r'^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$')
SAFE_LINK = re.compile(r'^(https?:|mailto:|file:|#|[^:]*$)', re.IGNORECASE)
INLINE = re.compile(r'(`+)(.+?)\1|\[([^\]]+)\]\(([^)\s]+(?:\([^)\s]*\))?)\)|\*\*(.+?)\*\*|(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])')


def slug(text):
    """A heading's anchor as GitHub writes it, so links between the Markdown files keep working."""
    return re.sub(r'[^a-z0-9 _-]', '', text.lower()).replace(' ', '-') or 'section'


def inline(text, link):
    """Escaped text with code spans, links, bold and emphasis; code spans stay literal."""
    out, last = [], 0
    for match in INLINE.finditer(text):
        out.append(html.escape(text[last:match.start()], quote=False))
        code, label, target, bold, em = match.group(2), match.group(3), match.group(4), match.group(5), match.group(6)
        if code is not None:
            out.append(f'<code>{html.escape(code.strip(), quote=False)}</code>')
        elif label is not None:
            href = link(target)
            body = inline(label, link)
            out.append(f'<a href="{html.escape(href)}">{body}</a>' if href and SAFE_LINK.match(href) else body)
        elif bold is not None:
            out.append(f'<strong>{inline(bold, link)}</strong>')
        else:
            out.append(f'<em>{inline(em, link)}</em>')
        last = match.end()
    out.append(html.escape(text[last:], quote=False))
    return ''.join(out)


def cells(row):
    """The cells of a table row; a pipe inside a code span belongs to the cell."""
    row = row.strip()
    row = row[1:] if row.startswith('|') else row
    row = row[:-1] if row.endswith('|') and not row.endswith('\\|') else row
    found, current, ticks = [], '', False
    for char in row:
        if char == '`':
            ticks = not ticks
        if char == '|' and not ticks:
            found.append(current.strip())
            current = ''
        else:
            current += char
    found.append(current.strip())
    return found


def render(text, prefix, link):
    """HTML for TEXT; heading ids start with PREFIX and LINK maps each link target to an href."""
    lines = text.splitlines()
    out, used, i = [], {}, 0

    def heading_id(title):
        base = f'{prefix}-{slug(title)}'
        used[base] = used.get(base, 0) + 1
        return base if used[base] == 1 else f'{base}-{used[base]}'

    def paragraph_end(j):
        line = lines[j]
        return (not line.strip() or FENCE.match(line) or HEADING.match(line) or BULLET.match(line)
                or NUMBERED.match(line) or line.lstrip().startswith(('>', '|', '<')) or RULE.match(line))

    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
        elif FENCE.match(line):
            language = FENCE.match(line).group(1)
            body, i = [], i + 1
            while i < len(lines) and not FENCE.match(lines[i]):
                body.append(lines[i])
                i += 1
            i += 1
            attr = f' class="language-{language}"' if language else ''
            out.append(f'<pre><code{attr}>' + ''.join(html.escape(row, quote=False) + '\n' for row in body)
                       + '</code></pre>')
        elif line.lstrip().startswith('<'):
            while i < len(lines) and lines[i].strip():
                i += 1
        elif HEADING.match(line):
            level, title = HEADING.match(line).groups()
            out.append(f'<h{len(level)} id="{heading_id(title)}">{inline(title, link)}</h{len(level)}>')
            i += 1
        elif RULE.match(line):
            out.append('<hr>')
            i += 1
        elif line.lstrip().startswith('|') and i + 1 < len(lines) and DIVIDER.match(lines[i + 1]):
            head = ''.join(f'<th>{inline(cell, link)}</th>' for cell in cells(line))
            rows, i = [], i + 2
            while i < len(lines) and lines[i].lstrip().startswith('|'):
                rows.append('<tr>' + ''.join(f'<td>{inline(cell, link)}</td>' for cell in cells(lines[i])) + '</tr>')
                i += 1
            out.append(f'<div class="table"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')
        elif line.lstrip().startswith('>'):
            quoted = []
            while i < len(lines) and lines[i].lstrip().startswith('>'):
                quoted.append(lines[i].lstrip()[1:].lstrip())
                i += 1
            out.append(f'<blockquote>{render(chr(10).join(quoted), prefix + "-q", link)}</blockquote>')
        elif BULLET.match(line) or NUMBERED.match(line):
            pattern, tag = (BULLET, 'ul') if BULLET.match(line) else (NUMBERED, 'ol')
            items = []
            while i < len(lines) and lines[i].strip():
                if pattern.match(lines[i]):
                    items.append(pattern.match(lines[i]).group(1).strip())
                elif lines[i].startswith((' ', '\t')) or not (BULLET.match(lines[i]) or NUMBERED.match(lines[i])):
                    items[-1] += ' ' + lines[i].strip()
                else:
                    break
                i += 1
            out.append(f'<{tag}>' + ''.join(f'<li>{inline(item, link)}</li>' for item in items) + f'</{tag}>')
        else:
            body = [line.strip()]
            i += 1
            while i < len(lines) and not paragraph_end(i):
                body.append(lines[i].strip())
                i += 1
            out.append(f'<p>{inline(" ".join(body), link)}</p>')
    return '\n'.join(out)
