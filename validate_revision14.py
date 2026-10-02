import json, math
from pathlib import Path
from procurement import best_offer
x=json.loads(Path('calculated.json').read_text())
assert x['assumptions']['soc_start']==1
assert x['assumptions']['vehicle_dry_mass_kg']==398
import adaptive_model as model
known=0
for r in x['rows']:
 for key,v in r['simulations'].items():
  if not v:continue
  known+=1
  assert abs(v['chemical_kwh']-v['output_kwh']-(v['heat_kj']+v['line_heat_kj'])/3600)<1e-8,(r['id'],key)
  assert -1e-10<=v['end_soc']<=100 and 25<=v['t_peak']<=60.01
  curves=model.empirical_curves(r['model'])
  if curves:
   q=(1-v['end_soc']/100)*x['models'][r['model']]['ah']
   assert q<=max(c['points'][-1][0] for c in curves)+1e-7,(r['id'],key,'unmeasured tail')
  assert v['output_kwh']>0 and v['full_minutes']<=v['minutes']+.001
  if r['model'] in x['assumptions']['tabless_models']:assert 'SOC' not in v['first_limit'] and v['soc_policy']=='Без ограничения по заряду'
 for g in [0,5,20]:
  for p in x['profiles']:
   a=r['simulations'][f"1_{g}_{p['id']}_2.8"];b=r['simulations'][f"1_{g}_{p['id']}_2.9"]
   if a and b:assert a['output_kwh']+0.005>=b['output_kwh'],(r['id'],g,p['id'])
for m in x['models'].values():
 os=m.get('market',{}).get('alibaba',{}).get('offers',[]);o=best_offer(os)
 if o:assert all(o['price']<=b['price'] for b in os if b['price'] is not None and b['availability']!='out_of_stock')
html=Path('dist/index.html').read_text()
assert '<option value="1" selected>Один блок</option>' in html
assert 'Цены Alibaba: отдельные предложения' not in html
assert 'id="wmtc-audit"' not in html
assert Path('dist/assets/cells/t50xg.jpg').exists()
print('PASS energy conservation, voltage scenarios, temperature bounds, charge policy, procurement and default controls;',known,'numeric scenario entries')
