"""Export reproducible numerical scenarios without the display traces."""
import json,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def calculate_audit():
    data=json.loads((ROOT/'calculated.json').read_text())
    rows=[]
    for r in data['rows']:
        scenarios={k:None if v is None else {a:b for a,b in v.items() if a!='trace'} for k,v in r['simulations'].items() if k.count('_')==3}
        independent={}
        if r['s']==26 and r['p']==16:
            for k,v in scenarios.items():
                if not k.startswith('1_'):continue
                v=copy.deepcopy(v)
                if v:
                    for field in ['output_kwh','chemical_kwh','heat_kj','line_heat_kj','mean_power','wmtc_equiv','utility_equiv','nominal_wmtc_equiv']:v[field]*=2
                    v['rough_range']=[2*q for q in v['rough_range']]
                    v['branches']=2;v['time_temperature_current_basis']='На одну независимую ветвь'
                independent[k]=v
        rows.append(dict(id=r['id'],model=r['model'],name=r['name'],nominal_kwh_per_block=r['energy'],finished_kg_per_block=r['finished'],cells_per_block=r['n'],voltage_basis=r['voltage_basis'],scenarios=scenarios,two_independent_motors=independent))
    audit=dict(release='20261002-r14',assumptions=data['assumptions'],profiles=data['profiles'],method='Номинальный эквивалент = энергия номинала / индекс BRP; сценарный = выданная энергия / индекс BRP. Два двигателя: независимые ветви с запросом на каждый. Дорожный цикл не моделируется.',configurations=len(rows),scenarios_per_configuration=108,rows=rows)
    (ROOT/'dist/calculation_audit.json').write_text(json.dumps(audit,ensure_ascii=False,separators=(',',':'))+'\n')
    return audit
if __name__=='__main__':
    a=calculate_audit();print('Calculation audit:',a['configurations'],'configurations,',a['scenarios_per_configuration'],'scenarios each')
