"""Physical accounting checks on the generated screening model."""
import json,math
from pathlib import Path
d=json.loads(Path('calculated.json').read_text()); count=0
for r in d['rows']:
    assert r['n']==r['s']*r['p']
    assert abs(r['mass']-r['n']*d['models'][r['model']]['kg'])<1e-9
    for key,s in r['simulations'].items():
        if not s:continue
        count+=1;b=int(key.split('_')[0])
        assert 0<s['output_kwh']<=s['chemical_kwh']<=.85*r['energy']*b+1e-8,(r['id'],key)
        assert s['heat_kj']/3600<=s['chemical_kwh']-s['output_kwh']+1e-8
        assert 0<=s['full_minutes']<=s['minutes']
        assert 9.999<s['end_soc']<=95
        assert 25<=s['t_end']<=60.1
        assert 0<=s['mean_power']<=30
        ts=s['trace'];assert all(a['soc']>=b['soc'] for a,b in zip(ts,ts[1:]))
        assert all(a['minute']<=b['minute'] for a,b in zip(ts,ts[1:]))
        assert all(math.isfinite(v) for t in ts for v in t.values())
        if '_constant15' in key:assert s['mean_power']<=15
        if r['id'] in ['C03','C16','C17','C18'] and key=='1_5_constant15':
            assert r['simulations']['1_20_constant15']['t_end']<s['t_end']
assert len({r['id'] for r in d['rows']})==len(d['rows'])
assert len({s['id'] for s in d['sources']})==len(d['sources'])
print(f'PASS: energy conservation, reserve, finite values, limits and cooling comparison in {count} simulations.')
