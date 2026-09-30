"""Independent energy checks, provenance and physical boundary checks."""
import json,math
from pathlib import Path
from digitize_discharge import integral
root=Path(__file__).parent
d=json.loads((root/'discharge_tests.json').read_text())
by={x['key']:x for x in d['datasets']}
assert len(by)==23
# Independent exact trapezoid fixture: 4->3 V across 2 Ah = 7 Wh.
assert integral([[0,4],[2,3]],3)==(7.,2.)
assert integral([[0,4],[1,3.5]],3)==(None,None)
for ds in by.values():
 assert ds['initial_C']==25 and (root/'dist'/ds['image']).exists()
 for c in ds['curves']:
  pts=c['points'];assert all(a[0]<b[0] for a,b in zip(pts,pts[1:]))
  assert all(2.6<v<4.3 for q,v in pts)
  if c['max_C'] is not None:assert c['delta_C']==c['max_C']-25
  e,q=integral(pts,3)
  if c['energy_3_0_Wh'] is not None:
   assert e is not None and abs(e-c['energy_3_0_Wh'])<.02
   assert abs(q-c['capacity_3_0_Ah'])<.004
   assert 3*q<=e<=4.3*q
  if c['energy_2_8_Wh'] is not None and c['energy_3_0_Wh'] is not None:assert c['energy_2_8_Wh']>c['energy_3_0_Wh']
for key,temp in [('rs50',53),('t50xg',48),('eve50pl',47),('bak50d2',50),('p50b',54)]:
 c=next(c for c in by[key]['curves'] if c['current_A']==20);assert c['max_C']==temp
for key,current in [('link55p',50),('tp60xg',60)]:
 c=next(c for c in by[key]['curves'] if c['current_A']==current)
 assert c['thermal_stop'] and c['energy_3_0_Wh'] is None
assert 'no CCC' in by['jp50p1']['title']
assert '50T' in by['link50t']['title']
assert not any(c['current_A'] in [25,30] for c in by['bak65e']['curves'])
assert any(c['thermal_stop'] and c['energy_3_0_Wh'] is None for c in by['link60p']['curves'])
q=json.loads((root/'alibaba_quotes.json').read_text())
assert len(q['offers'])==16
for o in q['offers']:
 if o['availability']!='quoted':assert o['price'] is None
for name in ['Ampace JP50','Linkdata INR21700S-50P','Vapcell T60','Vapcell Q65']:
 assert next(o for o in q['offers'] if o['model']==name)['key'] is None
calc=json.loads((root/'calculated.json').read_text())
assert calc['assumptions']['enclosed_line_losses']
assert all('1_0_constant15' in r['simulations'] for r in calc['rows'])
for r in calc['rows']:
 for s in r['simulations'].values():
  if s:
   assert s['heat_enclosed_mean']>=s['heat_mean']
   assert s['t_peak']>=s['t_end'] and s['t_peak']<=60.00001
   assert s['voltage_basis']==r['voltage_basis']
print('PASS: curve integration, cutoffs, annotated temperatures, identity separation, all 16 quotes, maximum temperature and enclosed losses.')
