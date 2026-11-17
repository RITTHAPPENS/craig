#!/bin/bash
S=/tmp/claude-0/-home-claude/3b326d7a-a278-5817-8ef5-93465d04eedd/scratchpad
W=${2:-1440}
for f in $1; do pid=$(python3 -c "import json;print(json.load(open('/home/claude/craig/elementor/pages.json'))['$f'])")
 python3 /home/claude/craig/elementor/purl.py $pid >/dev/null
 (cd $S && node dom.js http://localhost:8765/v7/$f pa.json $W && node dom.js "$(cat purl)" pb.json $W && echo "== $f" && python3 diff.py pa.json pb.json 8 | grep -v "MISSING ('nowrap'\|brand'")
done
