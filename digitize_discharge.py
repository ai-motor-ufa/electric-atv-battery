"""Reproducible raster digitisation. Source identity is read from chart, not filename.

Wh = integral V dAh. Annotated maximum temperatures are transcribed manually.
These are approximate curve integrals, never claimed as exact Mooch E-Scores.
"""
import json, hashlib, shutil, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy.optimize import minimize_scalar

ROOT = Path(__file__).resolve().parent
SRC = ROOT.parent / 'discharge-charts'
OUT = ROOT / 'dist' / 'tests'; OUT.mkdir(exist_ok=True)
# key, filename prefix, chart title, date, axis maximum Ah, current/color/Tmax.
# Colors are literal chart colors. A thermal stop has no invented voltage tail.
CONFIG = [
 ('jp50p1','Ampace','Ampace JP50P1 · no CCC logo','2026-01-06',5,[(5,'red',34),(10,'green',40),(20,'teal',50),(30,'pink',61),(40,'gray',69),(50,'orange',76),(60,'darkgreen',81)]),
 ('amprius50q','Amprius INR','Amprius INR21700/50Q · identity unconfirmed','2026-02-27',5,[(5,'red',34),(10,'green',42),(20,'blue',51),(30,'pink',62),(40,'gray',73),(50,'orange',80)]),
 ('sa112','Amprius SA','Amprius SA112 · no CCC logo','2026-01-21',6.5,[(1,'red',26),(5,'green',38),(10,'blue',53),(15,'purple',73)]),
 ('bak50d2','BAK 50D','BAK 50D2','2026-05-03',5,[(1,'red',None),(5,'green',32),(10,'blue',38),(20,'pink',50),(30,'gray',61),(40,'orange',71),(60,'darkgreen',81.3)]),
 ('bak65e','BAK 65','BAK 65E · gray legend 25 A / curve label 30 A','2026-03-24',6.5,[(1,'red',None),(5,'green',36),(10,'blue',46),(20,'pink',67)]),
 ('eve50pl','EVE','EVE 50PL · April 2025','2025-04-10',5,[(5,'red',30),(10,'green',36),(20,'blue',47),(30,'pink',59),(40,'gray',69),(50,'orange',77),(60,'darkgreen',80.7)]),
 ('gp50q','Great Power 50','Great Power 50Q','2026-05-07',5,[(1,'red',None),(5,'green',32),(10,'blue',39),(20,'pink',51),(30,'gray',62),(40,'orange',72),(50,'darkgreen',80.9)]),
 ('gp60q','Great Power 60','Great Power 60Q · CCC','2026-08-22',6,[(1,'red',None),(5,'green',35),(10,'blue',42),(20,'pink',53),(30,'gray',63),(40,'orange',73),(60,'darkgreen',75.8)]),
 ('h51t','LG H51','LG H51T (not H51)','2025-10-18',5,[(5,'red',38),(10,'green',45),(15,'blue',61),(20,'purple',71)]),
 ('lg','LG M50','LG M50LT','2022-12-22',5,[(5,'red',36),(10,'green',51),(15,'blue',67)]),
 ('link50t','Linkdata 50T','Linkdata 50T (not 50P)','2026-08-17',5,[(1,'red',None),(5,'green',36),(10,'blue',40),(20,'darkgreen',49),(30,'pink',58),(40,'gray',67),(50,'orange',74),(60,'teal',81.2)]),
 ('link55p','Linkdata 55','Linkdata 55P','2026-08-02',5.5,[(1,'red',None),(5,'green',37),(10,'blue',42),(20,'pink',54),(30,'gray',67),(40,'orange',77),(50,'darkgreen',80.5)]),
 ('link60p','Linkdata 60P','Linkdata 60P','2026-05-03',6,[(1,'red',None),(5,'green',32),(10,'blue',42),(20,'pink',59),(30,'gray',76),(60,'orange',81.6)]),
 ('link65p','Linkdata 65','Linkdata 65P','2026-06-11',6.5,[(1,'red',None),(5,'green',36),(10,'blue',44),(20,'pink',58),(30,'gray',71),(40,'orange',80.2),(50,'darkgreen',80.6)]),
 ('m50a','Molicel M50','Molicel M50A · production','2020-09-19',5,[(5,'red',39),(10,'green',58),(15,'blue',70)]),
 ('p50b_sample','Molicel P50B -','Molicel P50B · engineering sample','2024-02-18',5,[(5,'red',32),(10,'green',39),(20,'blue',55),(30,'pink',70),(40,'teal',80),(50,'orange',80),(60,'darkgreen',80)]),
 ('p50b','Molicel P50B Production','Molicel P50B · production','2025-01-04',5,[(5,'red',32),(10,'green',39),(20,'blue',54),(30,'pink',69),(40,'gray',80),(50,'orange',80),(60,'darkgreen',80)]),
 ('rh60','Reliance RH','Reliance RH60','2026-05-01',6,[(1,'red',None),(5,'green',35),(10,'blue',46),(15,'pink',57),(20,'gray',67),(30,'orange',80.2)]),
 ('rs50','Reliance RS50','Reliance RS50 · small spiral CCC retest','2026-05-05',5,[(1,'red',None),(5,'green',34),(10,'blue',41),(20,'pink',53),(30,'gray',65),(40,'orange',74),(70,'darkgreen',81)]),
 ('rs60','Reliance RS60','Reliance RS60','2026-05-19',6,[(1,'red',None),(5,'green',38),(10,'blue',46),(20,'pink',59),(30,'gray',73),(40,'orange',80.2),(50,'darkgreen',80.4)]),
 ('t50xg','Tenpower 50','Tenpower 50XG','2025-10-12',5,[(5,'red',31),(10,'green',41),(20,'blue',48),(30,'pink',58),(40,'gray',66),(90,'orange',78.6)]),
 ('tp60xg','Tenpower 60','Tenpower 60XG','2026-06-25',6,[(1,'red',None),(5,'green',37),(10,'blue',43),(20,'pink',56),(30,'gray',68),(40,'orange',78),(50,'darkgreen',80.4),(60,'cyan',80.7)]),
 ('g50','Vapcell','Vapcell G50 · 2020 (not T60/Q65)','2020-04-17',5,[(5,'red',37),(10,'green',52),(15,'blue',69),(20,'pink',82)]),
]
# Manually verified endpoints of temperature-stopped traces. Prevent nearby
# same-colour text/other traces from creating a fictitious discharge tail.
STOP_ENDPOINTS = {('link55p',50):4.03, ('tp60xg',50):4.32,
                  ('tp60xg',60):3.50, ('gp50q',50):4.51}
def mask_for(a,color):
 r,g,b=[a[:,:,i].astype(float) for i in range(3)]
 if color=='red':return (r>160)&(g<140)&(b<140)&(r-g>90)&(r-b>90)
 if color=='green':return (g>155)&(r<155)&(b<155)&(g-r>130)&(g-b>130)
 if color=='blue':return (b>150)&(r<155)&(g<160)&(b-r>60)&(b-g>60)
 if color=='pink':return (r>170)&(b>160)&(g<200)&(r-g>25)&(b-g>25)
 if color=='purple':return (r>65)&(b>70)&(g<90)&(r-g>40)&(b-g>40)&(r<200)
 if color=='gray':return (abs(r-g)<8)&(abs(g-b)<8)&(r>125)&(r<195)
 if color=='orange':return (r>210)&(g>125)&(g<205)&(b<110)&(r-g>40)&(g-b>60)
 if color=='darkgreen':return (g>65)&(g<160)&(r<80)&(b<80)&(g-r>50)&(g-b>50)
 if color=='teal':return (g>65)&(g<175)&(b>65)&(b<175)&(r<100)&(abs(g-b)<55)
 if color=='cyan':return (g>150)&(b>150)&(r<150)&(g-r>50)&(b-r>50)
 raise ValueError(color)
def trace(a,color,axes):
 x0,x1,ybottom,y3,y4,maxah=axes
 mask=mask_for(a,color); ytop=int(y4-(y3-y4)*.21)
 points=[];last=None;lastx=None
 for x in range(int(x0)+3,int(x1)+1):
  ys=np.flatnonzero(mask[ytop:int(ybottom)+1,x])+ytop
  if not len(ys):continue
  if last is None:y=float(min(ys))
  else:
   ys=ys[np.abs(ys-last)<max(12,(x-lastx)*3)]
   if not len(ys):continue
   y=float(ys[np.argmin(np.abs(ys-last))])
  if lastx is not None and x-lastx>65:break
  points.append((x,y));last=y;lastx=x
  if y>=ybottom-1:break
 if len(points)<70:raise ValueError(f'Insufficient trace {color}')
 xy=np.array(points);q=(xy[:,0]-x0)/(x1-x0)*maxah;v=3+(y3-xy[:,1])/(y3-y4)
 # Include only the observed extent. No tail to nominal Ah.
 q=np.r_[0,q];v=np.r_[min(4.2,v[0]),v]
 grid=np.linspace(0,q[-1],min(260,len(q)))
 vals=np.interp(grid,q,v)
 return np.column_stack([grid,vals]),xy
def integral(points,cut):
 p=np.array(points); hits=np.flatnonzero(p[:,1]<=cut)
 if not len(hits):return None,None
 i=hits[0]
 if i<1:return None,None
 q0,v0=p[i-1];q1,v1=p[i];qc=q0+(cut-v0)*(q1-q0)/(v1-v0)
 part=np.vstack([p[:i],[qc,cut]])
 return float(np.trapezoid(part[:,1],part[:,0])),float(qc)

def main():
 import adaptive_model as old
 datasets=[];audit=[]
 for key,prefix,title,date,maxah,curves in CONFIG:
  matches=[p for p in SRC.glob('*.jpeg') if p.name.startswith(prefix)]
  if not matches and (OUT/(key+'.jpg')).exists():matches=[OUT/(key+'.jpg')]
  assert len(matches)==1,(prefix,matches)
  path=matches[0];im=Image.open(path).convert('RGB');a=np.array(im)
  if im.width==1297:
   bottom=554;x0=84;x1=1254;y3=492 if key in ['lg','g50'] else 494 if key=='m50a' else 496
   y4=184 if key in ['lg','g50'] else 197 if key=='m50a' else 208
  else:
   x0=107;x1=1183;bottom=554;y3=494 if maxah in [5,6] and key not in ['gp60q','tp60xg','p50b','link50t'] else 496
   y4=203 if y3==494 else 215
   if key=='bak65e':y3=492;y4=191
   if key=='h51t':y3=492;y4=191
   if key in ['link55p','link60p','rh60','rs60']:y3=494;y4=203
   if key=='sa112':y3=494;y4=203
  axes=[x0,x1,bottom,y3,y4,maxah]
  ds=dict(key=key,title=title,test_date=date,source_filename=(next((x['source_filename'] for x in json.loads((ROOT/'discharge_tests.json').read_text())['datasets'] if x['key']==key),path.name) if (ROOT/'discharge_tests.json').exists() else path.name),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),image='tests/'+key+'.jpg',initial_C=25,axis_calibration=axes,curves=[])
  if key=='jp50p1':ds['identity_note']='В имени файла CCC, в самом графике no CCC. Использована подпись графика; предложение JP50 не приравнено к JP50P1.'
  if key=='sa112':ds['identity_note']='Заголовок 6500 мА·ч, легенда ошибочно 4.0 Ah. Оцифровка использует численную ось Ah; номинал не подменён легендой.'
  if key=='m50a':ds['identity_note']='На 15 A показаны два образца: 70 и 72 °C. Оцифрована синяя кривая образца с максимумом 70 °C.'
  if key=='bak65e':ds['identity_note']='Серая кривая: в легенде 25 A, рядом с линией 30 A. Исключена из численных данных; конфликт не исправлен догадкой.'
  if path.resolve()!=(OUT/(key+'.jpg')).resolve():shutil.copyfile(path,OUT/(key+'.jpg'))
  overlay=im.copy();draw=ImageDraw.Draw(overlay)
  for current,color,temp in curves:
   try:points,xy=trace(a,color,axes)
   except ValueError as e:print(key,current,e);continue
   endpoint=STOP_ENDPOINTS.get((key,current))
   if endpoint is not None and points[-1,0]>endpoint:
    voltage=float(np.interp(endpoint,points[:,0],points[:,1]))
    points=np.vstack([points[points[:,0]<endpoint],[endpoint,voltage]])
   e28,q28=integral(points,2.8);e30,q30=integral(points,3.0)
   # Last row is at 2.80 V axis even when JPEG antialiasing is slightly above.
   if e28 is None and points[-1,1]<2.83:
    points[-1,1]=2.8;e28,q28=integral(points,2.8)
   stop=(key,current) in STOP_ENDPOINTS or (temp is not None and temp>=75.8 and e28 is None)
   ds['curves'].append(dict(current_A=current,max_C=temp,delta_C=None if temp is None else temp-25,thermal_stop=stop,points=[[round(float(q),5),round(float(v),4)] for q,v in points],energy_2_8_Wh=None if e28 is None else round(e28,3),capacity_2_8_Ah=None if q28 is None else round(q28,4),energy_3_0_Wh=None if e30 is None else round(e30,3),capacity_3_0_Ah=None if q30 is None else round(q30,4),observed_until_Ah=round(float(points[-1,0]),4),observed_integral_Wh=round(float(np.trapezoid(points[:,1],points[:,0])),3)))
   draw.line([tuple(p) for p in xy],fill='black',width=1)
  overlay.save(ROOT.parent/('digitization-'+key+'.jpg'))
  baseline=next((c for c in ds['curves'] if c['current_A']==5),None)
  for c in ds['curves']:
   c['energy_loss_vs_5A_pct']=None if not baseline or not c['energy_3_0_Wh'] or not baseline['energy_3_0_Wh'] else round(100*(1-c['energy_3_0_Wh']/baseline['energy_3_0_Wh']),2)
  # Audit old model with same I, discharge extent, 25 C initial, no pack controller.
  m=old.D['models'].get(key)
  if m:
   dc=m.get('dc',m.get('dc_test')); mass=m['kg']
   if dc:
    usable=[c for c in ds['curves'] if c['max_C'] is not None and not c['thermal_stop'] and c['current_A']<=40]
    def temp_model(c,g):
     current=c['current_A'];qend=c['observed_until_Ah'];dt=2.;t=25.;q=0.
     while q<qend:
      h=min(dt,(qend-q)/current*3600);soc=max(0,1-q/m['ah']);r=dc/1000*(1+.6*(max(0,.5-soc)/.4)**2)
      t+=(current**2*r-g*(t-25))/(mass*1000)*h;q+=current*h/3600
     return t
    fit=minimize_scalar(lambda g:sum((temp_model(c,g)-c['max_C'])**2 for c in usable),bounds=(.001,.8),method='bounded') if len(usable)>=2 else None
    for c in usable:
     item=dict(key=key,title=title,current_A=c['current_A'],measured_C=c['max_C'],delta_C=c['delta_C'],minutes=c['observed_until_Ah']/c['current_A']*60,dc_mOhm=dc,cell_mass_g=mass*1000,
      pack_G5_equivalent_C=round(temp_model(c,5/416),1),pack_G20_equivalent_C=round(temp_model(c,20/416),1),adiabatic_C=round(temp_model(c,0),1),bench_G_fit_W_K=None if fit is None else round(float(fit.x),5),bench_fit_C=None if fit is None else round(temp_model(c,fit.x),1))
     item['bench_residual_C']=None if fit is None else round(item['bench_fit_C']-c['max_C'],1)
     audit.append(item)
  datasets.append(ds)
 data=dict(date='2026-09-30',format='21700',initial_C=25,method='Raster colour tracking; trapezoidal integral V dAh; maxima manually transcribed from original annotations',energy_accuracy='Приближённая оцифровка JPEG, не точный E-Score. Типичный ориентир погрешности несколько процентов; сырые измерения отсутствуют.',datasets=datasets,thermal_audit=audit)
 (ROOT/'discharge_tests.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 (ROOT/'dist/discharge_tests.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
 print('Digitized',len(datasets),'charts;',sum(len(d['curves']) for d in datasets),'curves;',len(audit),'thermal comparisons')
 for d in datasets:print(d['key'],[(c['current_A'],c['energy_3_0_Wh'],c['max_C'],c['thermal_stop']) for c in d['curves']])
if __name__=='__main__':main()
