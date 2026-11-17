"""Transform prototype CSS (v5+v6+v7) so it applies 1:1 to the Elementor atomic DOM."""
import re, sys, json, tinycss2
from tinycss2.ast import IdentToken, LiteralToken, WhitespaceToken, HashToken, FunctionBlock

TG = {'li', 'ul', 'ol', 'figure', 'figcaption', 'picture', 'dl', 'dt', 'dd', 'details', 'summary',
      'label', 'small', 'strong', 'em', 'b', 'i', 'blockquote', 'form', 'fieldset', 'legend', 'svg',
      'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table', 'tr', 'td', 'th', 'time', 'address', 'cite', 'mark', 'q'}
BOOST = ':not(#z)'


def ser(toks):
    return tinycss2.serialize(toks)


def rewrite_tokens(toks):
    """tag -> :is(tag,.tg-tag); .v7 -> body:not(.zz)"""
    out = []
    i = 0
    while i < len(toks):
        t = toks[i]
        prev = out[-1] if out else None
        if isinstance(t, LiteralToken) and t.value == '.' and i + 1 < len(toks) and isinstance(toks[i + 1], IdentToken) and toks[i + 1].value == 'v7':
            out.append(('RAW', ':where(body):not(.zz)'))
            i += 2
            continue
        if isinstance(t, LiteralToken) and t.value == '.' and i + 1 < len(toks) and isinstance(toks[i + 1], IdentToken) and toks[i + 1].value in ('js', 'menu-open', 'sub-page', 'gl-page', 'bn-page', 'rf-page') and not (prev is not None and not isinstance(prev, WhitespaceToken)):
            out.append(('RAW', ':where(html).' + toks[i + 1].value))
            i += 2
            continue
        if isinstance(t, IdentToken) and t.lower_value in TG:
            pv = prev.value if isinstance(prev, LiteralToken) else None
            if not (pv in ('.', ':', '::') or isinstance(prev, tuple) and prev[1].endswith(':')):
                if t.lower_value == 'span':
                    out.append(('RAW', ':is(span:where(:not(.x-t)),:where(.tg-span))'))
                else:
                    out.append(('RAW', f':is({t.value},:where(.tg-{t.lower_value}))'))
                i += 1
                continue
        if isinstance(t, IdentToken) and t.lower_value == 'div':
            pv = prev.value if isinstance(prev, LiteralToken) else None
            if pv not in ('.', ':', '::'):
                out.append(('RAW', 'div:where(:not([class*="tg-"]))'))
                i += 1
                continue
        if isinstance(t, LiteralToken) and t.value == '.' and i + 1 < len(toks) and isinstance(toks[i + 1], IdentToken) and toks[i + 1].value in ('req', 'nowrap', 'br-desk'):
            c = toks[i + 1].value
            out.append(('RAW', f':is(.{c},:where(.has-{c}) ' + ('br' if c == 'br-desk' else 'span') + ')'))
            i += 2
            continue
        if False:
                i += 1
                continue
        if isinstance(t, FunctionBlock) and t.lower_name in ('not', 'is', 'where', 'has'):
            out.append(('RAW', f'{t.name}(' + ser_mixed(rewrite_tokens(t.arguments)) + ')'))
            i += 1
            continue
        out.append(t)
        i += 1
    return out


def ser_mixed(lst):
    s = ''
    for t in lst:
        s += t[1] if isinstance(t, tuple) else ser([t])
    return s


def scope(sel):
    """Insert .elementor after root compounds, add specificity boost."""
    sel = sel.strip()
    if sel.startswith(':root') and ' ' not in sel:
        return sel
    if sel.startswith('@'):
        return sel
    # split into compounds keeping combinators
    comps = split_compounds(sel)
    # find leading root compounds
    k = 0
    roots = []
    while k < len(comps):
        c = comps[k]
        if re.match(r'^(html|body|:root|:where\((html|body)\))', c):
            roots.append(k)
            k += 2  # skip combinator
        else:
            break
    if roots:
        first = comps[0]
        # add boost onto first compound before pseudo-elements
        comps[0] = add_boost(first)
        last_root = roots[-1]
        if last_root + 1 >= len(comps):
            return ''.join(comps)
        rest = ''.join(comps[last_root + 2:])
        head = ''.join(comps[:last_root + 1])
        return f'{head} .elementor {rest}'
    return f':where(html){BOOST} .elementor {sel}'


def split_compounds(sel):
    """[compound, combinator, compound, ...] respecting brackets/parens/quotes."""
    out, cur, depth, q, i = [], '', 0, None, 0
    while i < len(sel):
        ch = sel[i]
        if q:
            cur += ch
            if ch == q:
                q = None
            i += 1
            continue
        if ch in '"\'':
            q = ch
        if ch in '([':
            depth += 1
        elif ch in ')]':
            depth -= 1
        if depth == 0 and (ch.isspace() or ch in '>+~'):
            j = i
            while j < len(sel) and (sel[j].isspace() or sel[j] in '>+~'):
                j += 1
            out.append(cur)
            out.append(sel[i:j])
            cur = ''
            i = j
            continue
        cur += ch
        i += 1
    out.append(cur)
    return out


def add_boost(comp):
    m = re.search(r'::', comp)
    if m:
        return comp[:m.start()] + BOOST + comp[m.start():]
    return comp + BOOST


def transform_rule(r, out):
    sel_toks = rewrite_tokens(list(r.prelude))
    sel = ser_mixed(sel_toks)
    sels = split_commas(sel)
    new = ', '.join(scope(s) for s in sels if s.strip())
    body = ser(r.content)
    body = rewrite_urls(body)
    out.append(f'{new}{{{body}}}')


def split_commas(s):
    out, depth, cur = [], 0, ''
    for ch in s:
        if ch in '([':
            depth += 1
        elif ch in ')]':
            depth -= 1
        if ch == ',' and depth == 0:
            out.append(cur)
            cur = ''
        else:
            cur += ch
    out.append(cur)
    return out


FONTS = {'hagrid-display-var.woff2': '/wp-content/uploads/fonts/hagrid-display-var.woff2',
         'redhat-display-var.woff2': '/wp-content/uploads/fonts/redhat-display-var.woff2'}
MEDIA = {}


def rewrite_urls(body):
    def f(m):
        u = m.group(2)
        if u.startswith('data:'):
            return m.group(0)
        base = u.split('/')[-1].split('?')[0]
        if base in FONTS:
            return f'url("{FONTS[base]}")'
        key = re.sub(r'^(\.\./)+', 'assets/', u) if not u.startswith('assets/') else u
        key = key.replace('assets/assets/', 'assets/')
        if key in MEDIA:
            return f'url("{MEDIA[key]}")'
        print('WARN url', u, file=sys.stderr)
        return m.group(0)
    return re.sub(r'url\((["\']?)([^)"\']+)\1\)', f, body)


def walk(rules, out):
    for r in rules:
        if r.type == 'qualified-rule':
            transform_rule(r, out)
        elif r.type == 'at-rule':
            kw = r.lower_at_keyword
            if kw in ('media', 'supports', 'container', 'layer') and r.content is not None:
                inner = []
                walk(tinycss2.parse_rule_list(r.content, skip_whitespace=True, skip_comments=True), inner)
                out.append(f'@{kw} {ser(r.prelude).strip()}{{' + ''.join(inner) + '}')
            elif kw == 'font-face':
                out.append('@font-face{' + rewrite_urls(ser(r.content)) + '}')
            elif kw == 'import':
                continue
            else:
                out.append('@' + kw + ' ' + ser(r.prelude).strip() + ('{' + ser(r.content) + '}' if r.content is not None else ';'))


def minify(s):
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'\s*([{};,>])\s*', r'\1', s)
    s = s.replace(';}', '}')
    return s


def build(files, media):
    MEDIA.update(media)
    out = []
    for f in files:
        walk(tinycss2.parse_stylesheet(open(f).read(), skip_whitespace=True, skip_comments=True), out)
    return '\n'.join(out)


if __name__ == '__main__':
    media = {k: v['url'].replace('https://bauservice-craig.de', '') for k, v in json.load(open(sys.argv[1])).items()}
    css = build(sys.argv[2:], media)
    print(minify(css))
