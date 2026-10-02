"""Verify ranking inputs, eligibility, formula and presentation basis independently."""
import json, math
from pathlib import Path
from selection_rating import calculate, WEIGHTS
from procurement import best_offer
source=json.loads(Path('calculated.json').read_text())
rating=json.loads(Path('dist/selection_ratings.json').read_text())
assert rating==calculate(source)
by={e['id']:e for e in rating['entries']}
rows={r['id']:r for r in source['rows']}
eligible=[e for e in by.values() if e['eligible']]
assert sum(WEIGHTS.values())==100
for e in by.values():
 r=rows[e['id']];o=best_offer(source['models'][r['model']].get('market',{}).get('alibaba',{}).get('offers',[]))
 assert r['s']==26 and r['p']==16
 assert (e['cost_pair'] is None)==(o is None)
 if o: assert math.isclose(e['cost_pair'],832*o['price'])
 s=r['simulations']['1_5_mixed_2.9']
 if s:assert math.isclose(e['output_pair'],2*s['output_kwh'])
 assert e['eligible']==(o is not None and s is not None and r['simulations']['1_5_active_2.9'] is not None and e['nominal_shaft_kw'] is not None and e['nominal_shaft_kw']>=30)
 if e['eligible']:
  expected=35*min(x['cost_pair'] for x in eligible)/e['cost_pair']+25*e['output_pair']/max(x['output_pair'] for x in eligible)+15*min(x['heat_W_per_block'] for x in eligible)/e['heat_W_per_block']+15*e['power_fraction']+5*min(x['mass_cells'] for x in eligible)/e['mass_cells']+5*e['evidence']
  assert math.isclose(e['score'],expected) and 0<e['score']<=100
 else:assert e['score'] is None
assert rating['top_five']==rating['orders']['overall'][:5]
for kind,key,descending in [('overall','score',True),('range','output_pair',True),('price','cost_pair',False)]:
 values=[by[id][key] for id in rating['orders'][kind]]
 assert values==sorted(values,reverse=descending)
assert next(e for e in by.values() if e['model']=='rs60')['score'] is None
assert not next(e for e in by.values() if e['model']=='s50s')['eligible']
assert next(e for e in by.values() if e['model']=='tp60xg')['evidence']==.25
assert all(sum(1 for e in by.values() if e['model']==m)==1 for m in ['link65p','tp60xg'])
html=Path('dist/index.html').read_text()
for kind in ['overall','range','price']:assert f'data-ranking="{kind}"' in html
assert html.count('class="final-cell"')==5
for m in ['link65p','tp60xg']:
 r=next(r for r in rows.values() if r['model']==m)
 assert r['nominal_wmtc']>80 and r['simulations']['1_5_mixed_2.9']['wmtc_equiv']<80
print('PASS: price/energy basis, eligible current limits, weighted ranking, three orders, unknown prices, preproduction caveat and five derived finalists.')
print('Top five:',[by[id]['name'] for id in rating['top_five']])
