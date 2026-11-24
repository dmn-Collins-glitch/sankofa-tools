import json, warnings, sys
warnings.simplefilter('ignore')
from part3 import B
ns = {}
bad = 0
out = {}
for wk, w in B.items():
    out[wk] = {'name': w['name'], 'drills': []}
    for i, d in enumerate(w['drills']):
        tag = f"{wk}#{i+1} {d['t']}"
        # starter must FAIL
        n1 = dict(ns)
        try:
            exec(d['s'], n1); exec(d['x'], n1)
            print('STARTER PASSES (bad):', tag); bad += 1
        except BaseException:
            pass
        # reference must PASS
        n2 = dict(ns)
        try:
            exec(d['r'], n2); exec(d['x'], n2)
            ns = n2
        except BaseException as e:
            print('REFERENCE FAILS:', tag, repr(e)); bad += 1
        e = {k: v for k, v in d.items() if k != 'r'}
        out[wk]['drills'].append(e)
print('problems:', bad)
if not bad:
    json.dump(out, open('drill_banks.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('wrote drill_banks.json', sum(len(w['drills']) for w in out.values()), 'drills')
