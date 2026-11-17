import sys,json,os,requests,subprocess
sys.path.insert(0,'/home/claude/craig/elementor');import build
H={'Authorization':'Basic '+open(os.path.expanduser('~/.wp/auth')).read().strip()}
def js():
    subprocess.run('python3 mkjs.py',shell=True,check=True,cwd='/home/claude/craig/elementor')
    sn=json.load(open('snippets.json'))
    for name,f in [('Craig Head','snippet-head.html'),('Craig Body JS','snippet-body.html')]:
        r=requests.post(f'https://bauservice-craig.de/wp-json/wp/v2/elementor_snippet/{sn[name]}',headers=H,json={'meta':{'_elementor_code':open(f).read()}})
        print(name,r.status_code)
def parts():
    s=build.page_soup('index.html')
    build.clear(693); build.clear(694)
    c,ids=build.build_nodes(693,[s.find('a',class_='skip'),s.find('header',class_='site-head'),s.find('div',class_='nav-backdrop')],chunk=3);print('header',len(ids))
    c,ids=build.build_nodes(694,[s.find('footer')],chunk=1);print('footer',len(ids))
    for p in (693,694): build.call('elementor-publish-document',{'post_id':p})
def page(f,pid):
    build.clear(pid)
    s=build.page_soup(f)
    c,ids=build.build_nodes(pid,[],root_tag=s.find('main'),chunk=4);print(f,len(ids))
if __name__=='__main__':
    cmd=sys.argv[1]
    if cmd=='parts': parts()
    elif cmd=='page': page(sys.argv[2],int(sys.argv[3]))
    elif cmd=='js': js()
