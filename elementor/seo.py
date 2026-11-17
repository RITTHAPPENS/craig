import sys,json,os,re,requests,html
sys.path.insert(0,'/home/claude/craig/elementor');import build
from bs4 import BeautifulSoup
H={'Authorization':'Basic '+open(os.path.expanduser('~/.wp/auth')).read().strip()}
B='https://bauservice-craig.de'
pages=json.load(open('pages.json'))
sn=json.load(open('snippets.json'))
def fixurls(t):
    t=re.sub(r'https://bauservice-craig\.de/assets/[^"]+',lambda m:B+build.asset(m.group(0).replace(B+'/','')),t)
    t=re.sub(r'https://bauservice-craig\.de/([a-z0-9-]+)\.html',lambda m:B+('/' if m.group(1)=='index' else '/'+m.group(1)+'/'),t)
    return t
for f,pid in pages.items():
    s=BeautifulSoup(open('../v7/'+f).read(),'html.parser')
    title=s.title.get_text().strip()
    desc=s.find('meta',attrs={'name':'description'})['content']
    r=requests.post(B+'/wp-json/rankmath/v1/updateMeta',headers=H,json={'objectType':'post','objectID':pid,'meta':{'rank_math_title':title,'rank_math_description':desc,'rank_math_robots':['index','follow']}})
    lds=[fixurls(x.string.strip()) for x in s.find_all('script',type='application/ld+json')]
    code=''.join(f'<script type="application/ld+json">{x}</script>' for x in lds)
    key='LD '+f
    if key in sn:
        requests.post(f'{B}/wp-json/wp/v2/elementor_snippet/{sn[key]}',headers=H,json={'meta':{'_elementor_code':code}})
    else:
        x=requests.post(B+'/wp-json/wp/v2/elementor_snippet',headers=H,json={'title':'Schema '+f[:-5],'status':'publish','meta':{'_elementor_location':'elementor_head','_elementor_priority':5,'_elementor_code':code}}).json()
        sn[key]=x['id']
        c=requests.post(f'{B}/wp-json/elementor/v1/site-editor/templates-conditions/{x["id"]}',headers=H,json={'conditions':[{'type':'include','name':'singular','sub_name':'page','sub_id':str(pid)}]})
        print('cond',c.status_code,c.text[:80])
    print(f,r.status_code,r.text[:80],len(code))
json.dump(sn,open('snippets.json','w'),indent=0)
