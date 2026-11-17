import sys;sys.path.insert(0,'/home/claude/craig/elementor');import build
r=build.call('elementor-create-preview-link',{'post_id':int(sys.argv[1])});open(build.S+'/purl','w').write(r['url']);print(r['url'][:60])
