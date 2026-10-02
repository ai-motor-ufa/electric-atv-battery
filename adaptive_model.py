"""Screening only: generic OCV, lumped heat, proposed control maps; no WMTC trace."""
import json, math, bisect
from functools import lru_cache
from pathlib import Path
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/'data.json').read_text()); NEW=json.loads((ROOT/'new_cells.json').read_text())
HARVESTED=json.loads((ROOT/'harvested_cells.json').read_text())
TESTS=json.loads((ROOT/'discharge_tests.json').read_text())
TEST_BY_KEY={t['key']:t for t in TESTS['datasets']}
QUOTES=json.loads((ROOT/'alibaba_quotes.json').read_text())
D['models'].update(NEW['models']); D['sources'].extend(NEW['sources'])
D['models'].update(HARVESTED['models']); D['sources'].extend(HARVESTED['sources'])
for key,market in HARVESTED.get('existing_market',{}).items():
    if key in D['models']:D['models'][key]['market']=market
from procurement import attach_offers
attach_offers(D['models'],QUOTES)
D['sources'].append(dict(id='ARCHIVE30',title='Графики Mooch: архив пользователя от 30.09.2026',url='discharge_tests.json',note='23 графика 21700; энергия оцифрована приблизительно, температуры переписаны с подписей. Начало около 25 °C.'))
D['sources'].append(dict(id='QUOTE01',title='Предложения Alibaba A, B и Vapcell',url='https://ai-motor-ufa.github.io/electric-atv-battery/#alibaba',note='Получены от пользователя 30.09 и 01.10.2026. Имена продавцов A/B неизвестны; цены и остатки не объединены.'))
D['sources'].append(dict(id='RATING21700',title='Battery Mooch: рейтинг 21700 от 27.09.2026',url='assets/mooch-21700-2026-09-27.jpg',note='Транскрипция E-Scores до 2,8 В; предсерия Tenpower 60XG и ZG13 раздельны. Не распространять после 27.03.2027 без обновления.'))
for brand,client in json.loads((ROOT/'manufacturer_clients.json').read_text())['manufacturers'].items():
 if client.get('id'):
  D['sources'].append(dict(id=client['id'],title=client['title'],url=client['url'],note=client['text']))
  if client.get('extra_url'):D['sources'].append(dict(id=client['id']+'_2',title=brand+': дополнительный источник',url=client['extra_url'],note='Второй первичный источник к разделу о клиентах компании.'))
# Use the new photo for exact named independent-test versions. Preserve prior
# forum values for provenance; manufacturer DCIR stays a separate parameter.
import csv
RATING_MAP={'jp50p1':'Ampace JP50P1','amprius50q':'Amprius INR21700/50Q (5000Q?)','bak50d2':'BAK 50D2','eve50pl':'EVE 50PL (CCC logo)','gp50q':'Great Power (GPHN) 50Q','link60p':'Linkdata 60P','link65p':'Linkdata 65P','rs50':'Reliance RS50 (CCC logo, batch G3E)','rs60':'Reliance RS60 (direct from Reliance)','t50xg':'Tenpower 50XG','tp60xg':'Tenpower 60XG (pre-production)','s50s2':'Samsung 50S2','p50b':'Molicel P50B (2024-dated)'}
PHOTO_BY_NAME={r['model']:r for r in csv.DictReader((ROOT/'mooch_photo.psv').open(),delimiter='|')}
for key,name in RATING_MAP.items():
 m=D['models'][key];r=PHOTO_BY_NAME[name]
 m['photo_rating']={k:float(r[k]) for k in ['estimated_CDR_A','DCIR_mOhm']}
 m['photo_rating']['model']=name;m['photo_rating']['date']='2026-09-27'
 if m.get('dc') is None:
  m['dc_test_forum_previous']=m.get('dc_test');m['dc_test']=float(r['DCIR_mOhm'])
  m['note']+=' Для текущего расчёта независимый DCIR взят из сводного фото Mooch от 27.09.2026; прежнее значение статьи сохранено отдельно.'
D['models']['tp60xg']['name']='Tenpower 60XG · предсерия июня'
D['models']['p30a']['note']=D['models']['p30a']['note'].replace('Не путать с цилиндрической Molicel P30B.','Пакетная модель каталога Farasis.')
D['models']['jp50p1']['name']='Ampace JP50P1 · испытание без маркировки CCC'
D['models']['jp50p1'].get('market',{}).pop('nkon',None) # JP50 listing is a different name.
# Passport DCIR stays separate; use the independently assessed CDR for screening.
D['models']['eve50pl']['screening_continuous']=40
D['models']['bak50d2']['screening_continuous']=40
D['models']['rs50']['screening_continuous']=40
D['sources']=[s for s in D['sources'] if s['id'] not in {'M35','P30','SUP','M65','LG'}]
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
# Reject whole configurations by known limits, not by absence of test data.
REJECTED_MODELS={'m35a','p30b','lg','m65a','sup'}
REJECTED_VARIANTS={'F01','L04'}
D['variants']=[v for v in D['variants'] if v['model'] not in REJECTED_MODELS and v['id'] not in REJECTED_VARIANTS]
active={v['model'] for v in D['variants']}
D['models']={k:m for k,m in D['models'].items() if k in active}
ETA=.88; AUX=.20; USABLE=1.; R_EXT=.001; CP=1000.; DT=5.; V_MIN=2.9
TABLESS=set(RATING_MAP)-{'s50s2','p50b'}
WMTC_INDEX=8.9/80; UTILITY_INDEX=8.9/50
OCV=[(0,2.50),(.05,3.20),(.10,3.40),(.20,3.50),(.30,3.60),(.50,3.70),(.70,3.85),(.90,4.05),(1,4.20)]
@lru_cache(None)
def empirical_curves(key):
    # Keep the observed 1 A curve where available. Most of a two-block
    # mixed scenario is below 5 A/cell; extrapolating only the 5/10 A curve
    # with a fixed DCIR cannot recover the measured low-current tail.
    return sorted([c for c in TEST_BY_KEY.get(key,{}).get('curves',[]) if c['current_A']>=1 and c.get('energy_3_0_Wh') and not c['thermal_stop']],key=lambda c:c['current_A'])
def curve_voltage(key,soc,current):
    curves=empirical_curves(key)
    if not curves:return None
    q=(1-soc)*D['models'][key]['ah']
    values=[(c['current_A'],interp(q,c['points']) if q<=c['points'][-1][0] else 2.79) for c in curves]
    if current<values[0][0]:
        m=D['models'][key];rr=(m.get('dc') or m.get('dc_test'))/1000
        return min(4.2,values[0][1]+(values[0][0]-current)*rr)
    return interp(current,values)
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
    return '21700' if m['type'].startswith('21700') else 'Пакетный'
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
    if key in ['eve50pl','bak50d2','rs50']:return 40 # Common conservative limit of conflicting versions.
    return m.get('screening_continuous') or m.get('continuous') or m.get('conditional_current')
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
       'nominal_wmtc':e/WMTC_INDEX,'nominal_utility':e/UTILITY_INDEX,
       'energy_ceiling_wmtc':USABLE*e/WMTC_INDEX,'energy_ceiling_utility':USABLE*e/UTILITY_INDEX,
       'candidate':v['id'] in SHORTLIST,'source':m['source'],
       'voltage_basis':'Оцифрованные V(Ah,I) Mooch; приблизительный перенос' if empirical_curves(v['model']) else 'Общая OCV + DCIR; токовые кривые отсутствуют',
       'delta':[v['box'][i]-[230,400,340][i] for i in range(3)],'simulations':{}})
ORDER={'21700':0,'Пакетный':1}
ROWS.sort(key=lambda r:(ORDER[r['format']],r['manufacturer'].lower(),r['cell_name'].lower(),r['p']))
for i,r in enumerate(ROWS):r['order']=i

def simulate(row,profile,blocks=1,g=5.,rscale=1.,peak_soc=.50,cutoff=2.9):
    # Identical simultaneous parallel blocks. Unknown DCIR or current map => no numeric promise.
    if row['dc_model'] is None or cell_limit(row['model'],25) is None:return None
    tabless=row['model'] in TABLESS
    vmin=cutoff if tabless else 3.0
    floor=0. if tabless else .10
    ns,np=row['s'],row['p']; soc=1.; temp=25.; peak_temp=25.; secs=chem=output=heat=lineheat=0.
    budget=float('inf'); c=row['mass']*CP; trace=[]
    first=reason=None; first_soc=first_voltage=first_temp=None; maxi=maxh=work=limited_secs=0.
    voltage_stop=False
    sample=dict(seconds=0,minute=0,soc=100,temp=25,power=0,voltage=0,current=0,heat=0)
    while secs<8*3600 and soc>floor+1e-7 and chem<budget-1e-8 and temp<60:
        voc=interp(soc,OCV)*ns
        rb=row['r_bank']/1000*rscale*(1+.6*(max(0,.5-soc)/.4)**2); rt=rb+R_EXT
        soc_cap=30 if tabless else interp(soc,[(.10,5),(.20,15),(peak_soc,30),(1,30)])
        thermal_cap=interp(temp,[(25,30),(45,30),(55,5),(60,0)])
        curves=empirical_curves(row['model'])
        q=(1-soc)*D['models'][row['model']]['ah']
        curve_values=[(c['current_A'],interp(q,c['points']) if q<=c['points'][-1][0] else 2.79) for c in curves]
        icap=cell_limit(row['model'],temp)*np
        if curves:icap=min(icap,curves[-1]['current_A']*np)
        ia=hs=hl=po=pc=shaft=0.; limited=False; causes=set(); highest_i=0.; lowest_v=voc
        # Repeat an explicit 100 s cycle; each stage is a real pulse, not an averaged load.
        phase=secs%100.; endpoint=0.; phase_left=100.
        for share,kw in profile['stages']:
            endpoint+=share*100
            if phase<endpoint-1e-7:
                stage_power=kw; phase_left=endpoint-phase; break
        else:stage_power=profile['stages'][0][1]
        for fraction,power in [(1.,stage_power)]:
            target=min(power,soc_cap,thermal_cap)
            req=(target/ETA+AUX)*1000/blocks; disc=voc*voc-4*rt*req
            ireq=2*req/(voc+math.sqrt(disc)) if disc>0 else voc/(2*rt)
            # No universal 90 V / 3.45 V derating. Limit only by the selected
            # minimum group voltage, cell current and the explicit SOC/T maps.
            voltage_icap=max(0,(voc-ns*vmin)/rt)
            current=min(ireq,icap,voc/(2*rt),voltage_icap)
            u=voc-current*rt
            stage_voc=voc
            if curves:
                def terminal(i):
                    ci=i/np
                    cv=interp(ci,curve_values) if ci>=curve_values[0][0] else min(4.2,curve_values[0][1]+(curve_values[0][0]-ci)*row['dc_model']/1000)
                    return cv*ns-i*R_EXT
                # Bisection of measured loaded V vs current; DCIR voltage loss
                # is already in the trace and must not be subtracted a second time.
                lo,hi=0.,icap
                for _ in range(20):
                    mid=(lo+hi)/2
                    if terminal(mid)<ns*vmin:hi=mid
                    else:lo=mid
                curve_cap=lo
                lo,hi=0.,curve_cap
                if terminal(hi)*hi<req:current=hi
                else:
                    for _ in range(20):
                        mid=(lo+hi)/2
                        if terminal(mid)*mid<req:lo=mid
                        else:hi=mid
                    current=(lo+hi)/2
                u=terminal(current)
                # Accounting reservoir: measured terminal output plus modeled
                # irreversible I²R loss, not a measured thermodynamic OCV.
                stage_voc=u+current*rt
            delivered=max(0,(blocks*u*current/1000-AUX)*ETA)
            if power>0 and delivered<power*.98:
                limited=True
                if soc_cap<power*.98:causes.add('SOC')
                if thermal_cap<power*.98:causes.add('температура')
                if icap<ireq*.98:causes.add('рейтинг тока ячейки')
                if voltage_icap<ireq*.98:causes.add('минимальное напряжение группы')
                if curves and u<=ns*vmin+.05:causes.add('граница напряжения по измеренной кривой')
                if curves and current>=icap*.99:causes.add('предел тока/проверенных кривых')
            ia+=fraction*current; hs+=fraction*current**2*rb
            hl+=fraction*current**2*R_EXT
            po+=fraction*blocks*u*current/1000; pc+=fraction*blocks*stage_voc*current/1000
            shaft+=fraction*delivered; highest_i=max(highest_i,current); lowest_v=min(lowest_v,u)
        if limited and first is None:
            first=secs/60;reason=', '.join(sorted(causes)) or 'доступная мощность'
            first_soc=soc*100;first_voltage=lowest_v;first_temp=temp
        if pc<.01:
            voltage_stop=True
            break
        dt=min(DT,phase_left,(soc-floor)*row['ah']*3600/max(ia,1e-9))
        net_heat=hs+hl-g*(temp-25)
        if net_heat>0:dt=min(dt,max(0,(60-temp)*c/net_heat))
        if dt<1e-5:break
        sample=dict(seconds=round(secs,1),minute=round(secs/60,3),soc=round(soc*100,2),temp=round(temp,2),power=round(shaft,3),voltage=round(lowest_v,2),current=round(highest_i,2),heat=round(hs,1))
        if not trace or secs-trace[-1]['seconds']>=30 or abs(trace[-1]['power']-sample['power'])>2:trace.append(sample)
        soc-=ia*dt/(row['ah']*3600); chem+=pc*dt/3600; output+=po*dt/3600; heat+=hs*blocks*dt/1000
        lineheat+=hl*blocks*dt/1000
        work+=shaft*dt; limited_secs+=dt if limited else 0
        # Conservative assumption: entire 1 mOhm electrical path is inside box.
        # G is whole cells-to-environment conductance, not an air-gap coefficient.
        temp+=(hs+hl-g*(temp-25))/c*dt;peak_temp=max(peak_temp,temp)
        secs+=dt; maxi=max(maxi,highest_i); maxh=max(maxh,hs)
    trace.append({**sample,'seconds':round(secs,1),'minute':round(secs/60,3),'soc':round(soc*100,2),'temp':round(temp,2)})
    return dict(minutes=secs/60,full_minutes=first if first is not None else secs/60,
       first_limit=reason or 'До завершения без снижения запроса',first_soc=first_soc,first_voltage=first_voltage,first_temp=first_temp,end_soc=max(0,soc)*100,
       output_kwh=output,chemical_kwh=chem,heat_kj=heat,heat_mean=heat*1000/max(secs,1)/blocks,
       heat_peak=maxh,max_current=maxi,mean_power=work/max(secs,1),t_end=temp,
       stop_reason='Температурная остановка 60 °C' if temp>=59.99 else ('Исчерпана ёмкость' if tabless else 'Резерв заряда 10%') if soc<=floor+.00001 else 'Минимальное напряжение группы'  if voltage_stop else 'Предел времени / интегрирования',t_peak=peak_temp,line_heat_kj=lineheat,heat_enclosed_mean=(heat+lineheat)*1000/max(secs,1)/blocks,
       cutoff_V=vmin,soc_policy='Без ограничения по заряду' if tabless else 'Предварительная карта по заряду',voltage_basis=row['voltage_basis'],thermal_status='Сценарный прогноз; теплоотвод собранного блока не измерен',
       limited_pct=100*limited_secs/max(secs,1),wmtc_equiv=output/WMTC_INDEX,utility_equiv=output/UTILITY_INDEX,
       nominal_wmtc_equiv=row['nominal_wmtc']*blocks,
       available_fraction=output/(row['energy']*blocks),
       rough_range=[output/.40,output/.25],trace=trace)

ASSUMPTIONS=dict(eta=ETA,aux_kw=AUX,energy_budget=None,soc_start=1.,soc_end=None,r_ext_mohm=R_EXT*1000,
 wmtc_index_kwh_km=WMTC_INDEX,utility_index_kwh_km=UTILITY_INDEX,
 cp_J_kgK=CP,ambient_C=25,dt_s=DT,passive_G=5,enhanced_G=20,derate_start_C=45,stop_C=60,peak_soc=None,tabless_models=sorted(TABLESS),pulse_cycle_s=100,vehicle_dry_mass_kg=398,two_motor_method='Two independent identical branches; per-branch time and temperature unchanged; total energy, shaft power and heat doubled',
 voltage_min_per_cell=V_MIN,ocv_generic=OCV,
 range_method='Energy equivalent against BRP indexes; not a WMTC speed simulation',
 capacity_rate_derating='For matched chart identities, loaded voltage is interpolated in Ah/current up to selected cutoff, no synthetic curve extension without double-subtracting DCIR. Other models retain generic OCV; no universal 10% capacity correction.',
 thermal_validation='Single-cell maximum temperatures audit I²R with cp=1000 J/kg/K; cannot identify G of sealed pack. No fitted bench cooling is transferred to pack.',
 enclosed_line_losses=True,temperature_display='peak and end; not cell hotspots',
 unknown_data='No thermal simulation without DCIR and usable discharge-current rating')
def calculate():
    for r in ROWS:
        for b in [1,2]:
            for g in [0,5,20]:
                for p in PROFILES:
                    for cutoff in [2.8,2.9,3.0]:
                        result=simulate(r,p,b,g,cutoff=cutoff) if r['model'] in TABLESS or cutoff==2.9 else r['simulations'][f"{b}_{g}_{p['id']}_2.9"] if f"{b}_{g}_{p['id']}_2.9" in r['simulations'] else simulate(r,p,b,g,cutoff=cutoff)
                        r['simulations'][f"{b}_{g}_{p['id']}_{cutoff}"]=result
                    r['simulations'][f"{b}_{g}_{p['id']}"]=r['simulations'][f"{b}_{g}_{p['id']}_2.9"]
        r['sensitivity15']=[simulate(r,PROFILES[4],1,5,s) for s in [.75,1.5]]
        for a in r['sensitivity15']:
            if a:a.pop('trace')
    payload={'assumptions':ASSUMPTIONS,'profiles':PROFILES,'rows':ROWS,'models':D['models'],'sources':D['sources'],'discharge_tests':TESTS,'quotes':QUOTES}
    (ROOT/'calculated.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')))
    return payload
if __name__=='__main__':
    calculate()
    for r in ROWS:
        if r['id'] in ['C03','C16','C17','C18','F02','F10']:
            p=r['simulations']['1_5_constant15']
            print(r['id'],r['name'],round(r['energy'],3),'kg',r['finished'],None if not p else {k:round(p[k],2) for k in ['minutes','full_minutes','output_kwh','wmtc_equiv','heat_mean','t_end']})
