"""Screening only: generic OCV, lumped heat, proposed control maps; no WMTC trace."""
import json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/'data.json').read_text()); NEW=json.loads((ROOT/'new_cells.json').read_text())
HARVESTED=json.loads((ROOT/'harvested_cells.json').read_text())
D['models'].update(NEW['models']); D['sources'].extend(NEW['sources'])
D['models'].update(HARVESTED['models']); D['sources'].extend(HARVESTED['sources'])
for key,market in HARVESTED.get('existing_market',{}).items():
    if key in D['models']:D['models'][key]['market']=market
assert all(not any(x in m['type'].upper() for x in ['LFP','LMFP']) for m in D['models'].values()), 'Phosphate chemistry is excluded from this study'
for v in NEW['variants']:
    m=D['models'][v['model']]; dia,_,h=m['dims']
    v.update(s=26,p=16,box=[230,400,340],extra=[8,13],
        layout=f'3 яруса 9S / 9S / 8S, шаг 22,5 мм; {180+dia:.1f}×{337.5+dia:.1f}×{3*h:.1f} мм',
        fit='Предварительно входит; масса и теплоотвод требуют CAD',
        comment='416 ячеек. Размер тел без межъярусных шин, держателей и теплоотводов.')
    D['variants'].append(v)
for v in HARVESTED['variants']:
    m=D['models'][v['model']]; dia,_,h=m['dims']
    v.update(s=26,p=16,box=[230,400,340],extra=[8,13],
        layout=f'3 яруса 9S / 9S / 8S, шаг 22,5 мм; {180+dia:.1f}×{337.5+dia:.1f}×{3*h:.1f} мм',
        fit='Предварительно входит; масса и теплоотвод требуют CAD',
        comment='416 ячеек. Размер тел без межъярусных шин, держателей и теплоотводов.')
    D['variants'].append(v)
ETA=.88; AUX=.20; USABLE=.85; R_EXT=.001; CP=1000.; DT=5.; V_MIN=3.0
OCV=[(0,2.50),(.05,3.20),(.10,3.40),(.20,3.50),(.30,3.60),(.50,3.70),(.70,3.85),(.90,4.05),(1,4.20)]
PROFILES=[
 {'id':'mixed','name':'Умеренная поездка','stages':[(.10,0),(.75,3),(.12,10),(.03,30)]},
 {'id':'active','name':'Частые разгоны','stages':[(.05,0),(.45,5),(.35,15),(.15,30)]},
 {'id':'constant5','name':'Постоянный запрос 5 кВт','stages':[(1.,5)]},
 {'id':'constant10','name':'Постоянный запрос 10 кВт','stages':[(1.,10)]},
 {'id':'constant15','name':'Постоянный запрос 15 кВт','stages':[(1.,15)]},
 {'id':'constant30','name':'Запрос 30 кВт (проверочный)','stages':[(1.,30)]}]
for p in PROFILES:p['battery_avg']=sum(w*(kw/ETA+AUX) for w,kw in p['stages'])
SHORTLIST={
 'C03','C08','C09','C10','C16','C17','C18','C19',
 'C20','C21','C22','C23','C24','C25','C26','C27',
 'F02','F06','F08','F09','F10','F16',
}
def fmt_type(m):
    return '21700' if m['type'].startswith('21700') else '18650' if m['type'].startswith('18650') else 'Pouch'
def interp(x,table):
    if x<=table[0][0]:return table[0][1]
    for (a,b),(c,d) in zip(table,table[1:]):
        if x<=c:return b+(d-b)*(x-a)/(c-a)
    return table[-1][1]
def clip(x):return max(0,min(1,x))
def cell_limit(key,temp):
    m=D['models'][key]
    if key=='lg':return 14.4 if temp<=25 else 7.2
    if key=='h51':return 25 if temp<=25 else 20 if temp<=45 else 7.5
    if key=='sup':return None # Full manufacturer SOC/time map is required.
    if key=='eve50pl':return 50 # Common conservative limit of conflicting versions.
    return m.get('continuous') or m.get('conditional_current')
ROWS=[]
for v in D['variants']:
    m=D['models'][v['model']]; n=v['s']*v['p']; mass=n*m['kg']
    dc=m.get('dc'); rr=dc if dc is not None else m.get('dc_test')
    e=n*m.get('wh',m['ah']*m['v'])/1000
    ROWS.append({**v,'name':m.get('short',m['name'])+f" · {v['s']}S{v['p']}P",'cell_name':m['name'],
       'format':fmt_type(m),'manufacturer':m['name'].split()[0],'n':n,'voltage':v['s']*m['v'],
       'vmax':None if m['vmax'] is None else v['s']*m['vmax'],'ah':m['ah']*v['p'],
       'energy':e,'mass':mass,'finished':[mass+x for x in v['extra']],
       'dcir':dc,'dc_model':rr,'dc_basis':'Паспорт' if dc is not None else 'Независимый тест; условный перенос' if rr is not None else 'Нет DCIR',
       'r_string':None if rr is None else v['s']*rr,'r_bank':None if rr is None else v['s']/v['p']*rr,
       'r_total':None if rr is None else v['s']/v['p']*rr+R_EXT*1000,
       'nominal_wmtc':e/8.9*80,'nominal_utility':e/8.9*50,
       'energy_ceiling_wmtc':USABLE*e/.11125,'energy_ceiling_utility':USABLE*e/.178,
       'candidate':v['id'] in SHORTLIST,'source':m['source'],
       'delta':[v['box'][i]-[230,400,340][i] for i in range(3)],'simulations':{}})
ORDER={'21700':0,'18650':1,'Pouch':2}
ROWS.sort(key=lambda r:(ORDER[r['format']],r['manufacturer'].lower(),r['cell_name'].lower(),r['p']))
for i,r in enumerate(ROWS):r['order']=i

def simulate(row,profile,blocks=1,g=5.,rscale=1.,peak_soc=.50):
    # Identical simultaneous parallel blocks. Unknown DCIR or current map => no numeric promise.
    if row['dc_model'] is None or cell_limit(row['model'],25) is None:return None
    ns,np=row['s'],row['p']; soc=.95; temp=25.; secs=chem=output=heat=0.
    budget=USABLE*row['energy']*blocks; c=row['mass']*CP; trace=[]
    first=reason=None; first_soc=first_voltage=first_temp=None; maxi=maxh=work=limited_secs=0.
    while secs<8*3600 and soc>.1000001 and chem<budget-1e-8:
        voc=interp(soc,OCV)*ns
        rb=row['r_bank']/1000*rscale*(1+.6*(max(0,.5-soc)/.4)**2); rt=rb+R_EXT
        soc_cap=interp(soc,[(.10,5),(.20,15),(peak_soc,30),(1,30)])
        thermal_cap=interp(temp,[(25,30),(45,30),(55,5),(60,0)])
        icap=cell_limit(row['model'],temp)*np
        ia=hs=po=pc=shaft=0.; limited=False; causes=set(); highest_i=0.; lowest_v=voc
        for fraction,power in profile['stages']:
            target=min(power,soc_cap,thermal_cap)
            req=(target/ETA+AUX)*1000/blocks; disc=voc*voc-4*rt*req
            ireq=2*req/(voc+math.sqrt(disc)) if disc>0 else voc/(2*rt)
            # No universal 90 V / 3.45 V derating. Limit only by the selected
            # minimum group voltage, cell current and the explicit SOC/T maps.
            voltage_icap=max(0,(voc-ns*V_MIN)/rt)
            current=min(ireq,icap,voc/(2*rt),voltage_icap)
            u=voc-current*rt; delivered=max(0,(blocks*u*current/1000-AUX)*ETA)
            if power>0 and delivered<power*.98:
                limited=True
                if soc_cap<power*.98:causes.add('SOC')
                if thermal_cap<power*.98:causes.add('температура')
                if icap<ireq*.98:causes.add('рейтинг тока ячейки')
                if voltage_icap<ireq*.98:causes.add('минимальное напряжение группы')
            ia+=fraction*current; hs+=fraction*current**2*rb
            po+=fraction*blocks*u*current/1000; pc+=fraction*blocks*voc*current/1000
            shaft+=fraction*delivered; highest_i=max(highest_i,current); lowest_v=min(lowest_v,u)
        if limited and first is None:
            first=secs/60;reason=', '.join(sorted(causes)) or 'доступная мощность'
            first_soc=soc*100;first_voltage=lowest_v;first_temp=temp
        if pc<.01:break
        dt=min(DT,(budget-chem)*3600/pc,(soc-.10)*row['ah']*3600/max(ia,1e-9))
        if dt<1e-5:break
        sample=dict(seconds=round(secs,1),minute=round(secs/60,3),soc=round(soc*100,2),temp=round(temp,2),power=round(shaft,3),voltage=round(lowest_v,2),current=round(highest_i,2),heat=round(hs,1))
        if not trace or secs-trace[-1]['seconds']>=30:trace.append(sample)
        soc-=ia*dt/(row['ah']*3600); chem+=pc*dt/3600; output+=po*dt/3600; heat+=hs*blocks*dt/1000
        work+=shaft*dt; limited_secs+=dt if limited else 0
        temp+=(hs-g*(temp-25))/c*dt
        secs+=dt; maxi=max(maxi,highest_i); maxh=max(maxh,hs)
    trace.append({**sample,'seconds':round(secs,1),'minute':round(secs/60,3),'soc':round(soc*100,2),'temp':round(temp,2)})
    return dict(minutes=secs/60,full_minutes=first if first is not None else secs/60,
       first_limit=reason or 'До выбранного резерва без снижения запроса',first_soc=first_soc,first_voltage=first_voltage,first_temp=first_temp,end_soc=soc*100,
       output_kwh=output,chemical_kwh=chem,heat_kj=heat,heat_mean=heat*1000/max(secs,1)/blocks,
       heat_peak=maxh,max_current=maxi,mean_power=work/max(secs,1),t_end=temp,
       limited_pct=100*limited_secs/max(secs,1),wmtc_equiv=output/.11125,utility_equiv=output/.178,
       rough_range=[output/.40,output/.25],trace=trace)

ASSUMPTIONS=dict(eta=ETA,aux_kw=AUX,energy_budget=USABLE,soc_start=.95,soc_end=.10,r_ext_mohm=R_EXT*1000,
 cp_J_kgK=CP,ambient_C=25,dt_s=DT,passive_G=5,enhanced_G=20,derate_start_C=45,stop_C=60,peak_soc=.5,
 voltage_min_per_cell=V_MIN,ocv_generic=OCV,
 range_method='Energy equivalent against BRP indexes; not a WMTC speed simulation',
 capacity_rate_derating='Not applied per cell model. The 85% energy budget is a SOC/reserve window, not a correction for capacity loss at high C-rate.',
 unknown_data='No thermal simulation without DCIR and usable discharge-current rating')
def calculate():
    for r in ROWS:
        for b in [1,2]:
            for g in [5,20]:
                for p in PROFILES:r['simulations'][f"{b}_{g}_{p['id']}"]=simulate(r,p,b,g)
        r['sensitivity15']=[simulate(r,PROFILES[4],1,5,s) for s in [.75,1.5]]
        for a in r['sensitivity15']:
            if a:a.pop('trace')
    payload={'assumptions':ASSUMPTIONS,'profiles':PROFILES,'rows':ROWS,'models':D['models'],'sources':D['sources']}
    (ROOT/'calculated.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')))
    return payload
if __name__=='__main__':
    calculate()
    for r in ROWS:
        if r['id'] in ['C03','C16','C17','C18','F02','F10']:
            p=r['simulations']['1_5_constant15']
            print(r['id'],r['name'],round(r['energy'],3),'kg',r['finished'],None if not p else {k:round(p[k],2) for k in ['minutes','full_minutes','output_kwh','wmtc_equiv','heat_mean','t_end']})
