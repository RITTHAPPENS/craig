import json,re,glob as G
PAGECLS={}
for f in G.glob('../v7/*.html'):
    b=re.search(r'<body class="([^"]*)"',open(f).read()).group(1).split()
    k=f.split('/')[-1][:-5]
    PAGECLS['' if k=='index' else k]=[c for c in b if c!='v7']
import glob
attrs={}
for f in glob.glob('attrs/*.json'): attrs.update(json.load(open(f)))
js=open('shim.js').read()
proto=''.join(open('../assets/js/'+f).read()+'\n' for f in ['site.js','v3.js','v5.js'])
body='<script>window.CRAIG_ATTRS='+json.dumps(attrs,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+';</script>\n<script>'+js+'</script>\n<script>'+proto+'</script>'
head='''<script src="https://cloud.ccm19.de/app.js?apiKey=9bf6c069b80f6b3ab65a0964614ef64aa02f408c17c1fdcc&domain=6afc5dfdecc439bd8f0c1442" referrerpolicy="origin"></script>
<link rel="preload" href="/wp-content/uploads/fonts/hagrid-display-var.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/wp-content/uploads/fonts/redhat-display-var.woff2" as="font" type="font/woff2" crossorigin>
<meta name="theme-color" content="#141414">
<script>(function(){var d=document.documentElement,p=location.pathname.replace(/\\/+$/,'')||'/',m=%s;d.classList.add('js');(m[p.split('/').pop()]||[]).forEach(function(c){d.classList.add(c)});})();</script>''' % json.dumps(PAGECLS)
open('snippet-body.html','w').write(body); open('snippet-head.html','w').write(head)
print(len(body),len(head))
