import json, os, re, sys, subprocess, html
from bs4 import BeautifulSoup, Tag
sys.path.insert(0, os.path.dirname(__file__))
from conv import Conv

S = '/tmp/claude-0/-home-claude/3b326d7a-a278-5817-8ef5-93465d04eedd/scratchpad'
ROOT = '/home/claude/craig'
D = os.path.join(ROOT, 'elementor')
MEDIA = json.load(open(S + '/media_map.json'))
ATTRS_F = D + '/attrs.json'
LABELS_F = D + '/labels.json'


def rel(u):
    return u.replace('https://bauservice-craig.de', '').replace('http://bauservice-craig.de', '')


def asset(p):
    p = re.sub(r'\?.*', '', p or '')
    k = re.sub(r'^(\.\./)+', '', p)
    if not k.startswith('assets/'):
        k = 'assets/' + k
    m = MEDIA.get(k)
    if not m:
        print('WARN asset', p, file=sys.stderr)
        return p
    return rel(m['url'])


def link(h):
    if not h:
        return '#'
    if re.match(r'^(tel:|mailto:|https?:|#)', h):
        return h
    path, _, frag = h.partition('#')
    if path in ('./', 'index.html', ''):
        u = '/'
    elif path.endswith('.html'):
        u = '/' + path[:-5] + '/'
    else:
        u = path
    return u + ('#' + frag if frag else '')


def call(name, args):
    body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': name, 'arguments': args}})
    bf = os.path.join(S, 'mcp_body.json')
    open(bf, 'w').write(body)
    p = subprocess.run([os.path.expanduser('~/.wp/mcp.sh'), '@file', bf], capture_output=True, text=True)
    out = p.stdout
    try:
        d = json.loads(out)
    except Exception:
        # SSE framing
        m = re.search(r'data: (\{.*\})', out)
        d = json.loads(m.group(1)) if m else {'raw': out[:2000]}
    if 'result' in d:
        r = d['result']
        sc = r.get('structuredContent')
        if sc is None:
            try:
                sc = json.loads(r['content'][0]['text'])
            except Exception:
                sc = {'text': r['content'][0]['text']}
        if r.get('isError'):
            print('ERROR', name, json.dumps(sc)[:1500], file=sys.stderr)
        return sc
    print('ERROR', name, out[:1500], file=sys.stderr)
    return d


def load(f, d):
    return json.load(open(f)) if os.path.exists(f) else d


def ids_from_resolved(xml):
    return dict(re.findall(r'configuration-id="([^"]+)" id="([0-9a-f]+)"', html.unescape(xml)))


def compose(post_id, conv, xml, parent=None):
    cids = set(re.findall(r'configuration-id="([^"]+)"', xml))
    args = {'post_id': post_id, 'xml_structure': xml,
            'element_config': {k: v for k, v in conv.cfg.items() if k in cids},
            'classes': {k: v for k, v in conv.cls.items() if k in cids and v},
            'style': {k: v for k, v in conv.style.items() if k in cids}}
    if parent:
        args['parent_id'] = parent
    r = call('elementor-build-composition', args)
    if not r.get('success'):
        print('compose failed', json.dumps(r)[:2000], file=sys.stderr)
        return {}, r
    w = r.get('warnings') or []
    if w:
        print('warnings', len(w), json.dumps(w[:12], ensure_ascii=False)[:3000], file=sys.stderr)
    return ids_from_resolved(r['resolved_xml']), r


def store_attrs(conv, idmap, post_id):
    f = f'{D}/attrs/{post_id}.json'
    attrs = load(f, {})
    for cid, m in conv.meta.items():
        eid = idmap.get(cid)
        if not eid:
            continue
        e = {}
        if m.get('attrs'):
            e['a'] = m['attrs']
        if m.get('replace'):
            e['r'] = m['replace']
        if e:
            attrs[eid] = e
    os.makedirs(D + '/attrs', exist_ok=True)
    json.dump(attrs, open(f, 'w'), ensure_ascii=False, indent=0)


def clear(post_id):
    f = f'{D}/attrs/{post_id}.json'
    if os.path.exists(f):
        os.remove(f)
    r = call('elementor-get-page-structure', {'post_id': post_id})
    els = r.get('elements') or r.get('structure') or []
    ops = [{'action': 'delete', 'element_id': e['id']} for e in els]
    for i in range(0, len(ops), 50):
        call('elementor-manage-elements', {'post_id': post_id, 'operations': ops[i:i + 50]})


def build_nodes(post_id, nodes, root_tag=None, root_attrs=None, chunk=6):
    """nodes: list of top-level Tags. If root_tag given, wraps them in one container (e.g. main)."""
    conv = Conv(MEDIA, link, asset)
    allids = {}
    if root_tag is not None:
        rcid = 'Root ' + root_tag.name
        conv.cfg[rcid] = {'tag': root_tag.name} if root_tag.name != 'div' else {}
        if root_tag.get('id'):
            conv.cfg[rcid]['_cssid'] = root_tag['id']
        conv.cls[rcid] = conv.classes(root_tag) + [c for c in (root_tag.find_parent('body') or {}).get('class', []) if c != 'v7']
        kids = [c for c in root_tag.children if isinstance(c, Tag)]
        first = ''.join(conv.node(c) for c in kids[:chunk])
        ids, r = compose(post_id, conv, f'<e-div-block configuration-id="{rcid}">{first}</e-div-block>')
        allids.update(ids)
        root_id = ids.get(rcid)
        for i in range(chunk, len(kids), chunk):
            part = ''.join(conv.node(c) for c in kids[i:i + chunk])
            ids, r = compose(post_id, conv, part, parent=root_id)
            allids.update(ids)
    else:
        for i in range(0, len(nodes), chunk):
            part = ''.join(conv.node(c) for c in nodes[i:i + chunk])
            ids, r = compose(post_id, conv, part)
            allids.update(ids)
    store_attrs(conv, allids, post_id)
    labels = set(load(LABELS_F, []))
    labels |= conv.labels
    json.dump(sorted(labels), open(LABELS_F, 'w'))
    return conv, allids


def page_soup(name):
    return BeautifulSoup(open(os.path.join(ROOT, 'v7', name)).read(), 'html.parser')


def collect_labels(names):
    labels = set()
    for name in names:
        s = page_soup(name)
        conv = Conv(MEDIA, link, asset)
        for part in [s.find('header', class_='site-head'), s.find('main'), s.find('footer')]:
            if part:
                conv.node(part)
        labels |= conv.labels
    return labels
