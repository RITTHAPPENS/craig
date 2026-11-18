import sys,json,os,re,requests,glob
sys.path.insert(0,'/home/claude/craig/elementor');import build,run
H={'Authorization':'Basic '+open(os.path.expanduser('~/.wp/auth')).read().strip()}
pages=json.load(open('pages.json'))
TITLES={'aussenanlagen-galabau':'Garten- & Landschaftsbau','badsanierung':'Badsanierung','bauen':'Bauausführung','bauleitung-baubegleitung':'Bauleitung & Baubegleitung','bausachverstaendiger':'Bausachverständiger','fliesen-bodenarbeiten':'Fliesen- & Bodenarbeiten','hochbau':'Hochbau','kontakt':'Kontakt','poolbau':'Poolbau','referenzen':'Referenzen','sanierung-modernisierung':'Sanierung & Modernisierung','team':'Team','tiefbau':'Tiefbau','trockenbau-innenausbau':'Trockenbau & Innenausbau','unsere-geschichte':'Unsere Geschichte','karriere':'Karriere'}
only=sys.argv[1:]
for slug,title in TITLES.items():
    f=slug+'.html'
    if only and f not in only: continue
    if f not in pages:
        r=build.call('elementor-create-page',{'title':title,'template':'elementor_header_footer','hide_title':True})
        pages[f]=r['id']
        requests.post(f"https://bauservice-craig.de/wp-json/wp/v2/pages/{r['id']}",headers=H,json={'slug':slug})
        json.dump(pages,open('pages.json','w'),indent=0)
    run.page(f,pages[f])
