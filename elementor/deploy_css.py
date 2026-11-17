import sys,json,subprocess
sys.path.insert(0,'/home/claude/craig/elementor');import build
S=build.S
subprocess.run(f"python3 css.py {S}/media_map.json ../assets/css/v5.css ../assets/css/v6.css ../assets/css/v7.css > {S}/proto.css",shell=True,cwd='/home/claude/craig/elementor',check=True)
css=open('base.css').read()+open('icons.css').read()+open(S+'/proto.css').read()+open('tail.css').read()
open('site.css','w').write(css)
r=build.call('elementor-update-page-settings',{'post_id':6,'settings':{'custom_css':css,'system_typography':[{'_id':i,'title':i.title(),'typography_typography':'custom','typography_font_family':'Hagrid'} for i in ('primary','secondary','text','accent')]}})
print(build.call('elementor-publish-document',{'post_id':6}).get('status'), len(css))
print(build.call('elementor-clear-cache',{}).get('success'))
