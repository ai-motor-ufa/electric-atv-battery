"""Build the static report and the matching, paginated PDF from shared data."""
import json,html,re
from io import BytesIO
from PIL import Image as RasterImage
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.pagesizes import A3,landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing,Rect,String,Line,PolyLine
from report_content import SECTIONS,TEST_ROWS
from recommendations import INTRO, METHOD, GEOMETRY, HEAT_METHOD, COOLING, DIMENSION_NOTE, POUCH_INTRO, POUCH, DECISION, HIGH_CAPACITY_MARKET_NOTE, ranked_groups, render_html
from mooch_section import section as mooch_section
from test_sections import section as updated_test_section, manufacturer, exports as export_test_tables
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'dist'; PDF='AKB_96V_Comparative_Study_2026-10-02.pdf'; RELEASE='20261002-r14a'
data=json.loads((ROOT/'calculated.json').read_text()); rows=data['rows']; models=data['models']; photos=json.loads((ROOT/'photos.json').read_text())
mooch_json=(OUT/'mooch_data.json').read_text(); mooch_data=json.loads(mooch_json); forum_threads=len(mooch_data['forum'])
data['photos']=photos
export_test_tables()
candidate_21700=sum(r['candidate'] and r['format']=='21700' for r in rows)
candidate_pouch=sum(r['candidate'] and r['format']=='Пакетный' for r in rows)
SOURCES={s['id']:s for s in data['sources']}
esc=lambda x:html.escape(str(x))
def n(x,d=1):return '—' if x is None else f'{x:.{d}f}'.replace('.',',')
def dim(a):return '×'.join(n(x,0 if float(x).is_integer() else 2) for x in a)
def cell_dim(m):
 return 'Ø'+n(m['dims'][0],2)+' × '+n(m['dims'][2],2) if m['type'].startswith('21700') else dim(m['dims'])
def linked(text,pdf=False):
    text=esc(text)
    def sub(match):
        keys=match.group(1).split(', '); ls=[]
        for k in keys:
            src=SOURCES.get(k)
            if not src:ls.append(k);continue
            url=src['url'] if pdf else '#source-'+k
            ls.append(f'<a href="{esc(url)}"'+(' color="#0071e3"' if pdf else '')+'>'+k+'</a>' if url else k)
        return '['+', '.join(ls)+']'
    return re.sub(r'\[([A-Z0-9, ]+)\]',sub,text)
def pic(key):return esc(photos[key]['file']) if key in photos else ''

opts=''.join(f'<option value="{r["id"]}">{esc(r["name"])}</option>' for r in rows if r['candidate'])
p_opts=''.join(f'<option value="{p["id"]}">{esc(p["name"])}</option>' for p in data['profiles'])
import copy
web_data=copy.deepcopy(data);web_data.pop('discharge_tests',None)
(OUT/'traces').mkdir(exist_ok=True)
for r in web_data['rows']:
 traces={}
 for simkey in list(r['simulations']):
  if simkey.count('_')==2:del r['simulations'][simkey];continue
  v=copy.deepcopy(r['simulations'][simkey]);r['simulations'][simkey]=v
  if v:
   stride=max(1,len(v['trace'])//320)
   sampled=v['trace'][::stride]
   if sampled[-1]!=v['trace'][-1]:sampled.append(v['trace'][-1])
   traces[simkey]=[[t[k] for k in ('minute','soc','temp','power')] for t in sampled]
   del v['trace']
 if traces:(OUT/'traces'/f"{r['id']}.json").write_text(json.dumps(traces,separators=(',',':')))
embedded_data=json.dumps(web_data,ensure_ascii=False,separators=(',',':')).replace('</',r'<\/')
method=[
 'Начало: полный заряд и 25 °C. Для ячеек с распределённым токосъёмом выбрана отсечка 2,9 В под нагрузкой; доступны 2,8 и 3,0 В. Ограничения 50% заряда и 85% энергии сняты. Для Linkdata 60P/65P паспорт рекомендует запас над 2,5 В в последовательной батарее, например 3,0 В: 2,8–2,9 В здесь проверочный сценарий, требующий согласования и контроля разбаланса. Для остальных ячеек оставлены 3,0 В и прежняя предварительная карта по заряду. Это сценарий управления, а не подтверждение допустимости каждого режима паспортом.',
 'Запрос 15 или 30 кВт может поступать на любом уровне заряда ячеек с распределённым токосъёмом. Фактическая мощность ограничивается током ячейки, проверенным диапазоном разрядных кривых, напряжением и температурой. Удлинённый импульс не считается автоматически разрешённым: при недостатке тока тяга снижается сразу.',
 'КПД двигателя с контроллером принят 88%, вспомогательная нагрузка — 0,2 кВт на ветвь. Карты КПД, нагрева двигателя и контроллера отсутствуют. Нужны паспорт или измерения для расчёта их температур и допустимой длительности пика.',
 'Умеренная поездка: повторяющийся цикл 100 с — 10 с без тяги, 75 с при 3 кВт, 12 с при 10 кВт, 3 с при 30 кВт. Частые разгоны: 5 с без тяги, 45 с при 5 кВт, 35 с при 15 кВт, 15 с при 30 кВт. Эти длительности — принятые сценарии для сравнения, не запись реальной поездки.',
 'Энергия интегрируется по напряжению и току на клеммах; заряд — по отданным ампер-часам. Температура: C·dT/dt = I²R − G·(T−25), с потерями обвязки 1 мОм внутри корпуса. Теплоёмкость 1000 Дж/(кг·К); снижение тяги начинается при средней температуре 45 °C, остановка при 60 °C. Это консервативные настройки модели, не паспортные предельные температуры и не температура наиболее горячей ячейки.',
 'Оцифрованные кривые используются только в наблюдаемом диапазоне. По мере разряда ток ограничен оставшимися измеренными кривыми; при их завершении расчёт останавливается. Неизвестные хвосты ниже измеренной ёмкости не достраиваются. Для моделей без подходящих кривых используется общая зависимость напряжения от заряда; без сопротивления или рейтинга тока численный результат отсутствует.',
 'BRP Outlander Electric 2026: 8,9 кВт·ч, 80 км по WMTC, 50 км в средней эксплуатации, сухая масса 398 кг. Ваш квадроцикл принят с той же сухой массой, без поправки по массе. Водитель и груз предполагаются сопоставимыми. Различия шин, трансмиссии, рекуперации и дороги не рассчитаны.',
 'Номинальный эквивалент = число блоков × номинальная энергия / индекс BRP. Сценарный эквивалент = выданная энергия / индекс BRP. Индексы 0,11125 и 0,178 кВт·ч/км основаны на заявленной ёмкости BRP; его полезная энергия неизвестна. Поэтому это условное сравнение, а не воспроизведение WMTC или обещание реального пробега.',
 'Два двигателя: на каждый приходится один блок 26S16P и собственный запрос 15/30 кВт. Суммарный запрос — 30/60 кВт. Для одинаковых ветвей длительность и температура каждого блока такие же, как для одной ветви, а суммарная энергия, мощность и выделенное тепло удваиваются. Это отличается от двух блоков, делящих нагрузку одного двигателя. Для пакетных конфигураций применяется собственная компоновка строки, а не 26S16P.'
]
method_html=''.join('<p>'+esc(t)+'</p>' for t in method)
source_html=''.join(f'<p id="source-{s["id"]}"><a href="{esc(s["url"])}">Источник {esc(s["id"])}</a></p>' for s in data['sources'] if s['url'])
brp_url='https://can-am.brp.com/content/dam/global/en/can-am-off-road/my26/spec-sheets/na/atv/en/ORV_ATV_MY26_5_SPEC_OUT_EV_ENNA_HR.pdf'
doc=f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>АКБ квадроцикла — редакция 14</title><link rel="stylesheet" href="report.css?v={RELEASE}"></head><body>
<header class="nav"><div class="wrap"><a href="#compare">Сравнение</a> · <a href="#catalog">Ячейки и цены</a> · <a href="{PDF}">Отчёт PDF</a></div></header>
<main><section class="hero section"><div class="wrap"><p class="eyebrow">Редакция 14 · 02.10.2026</p><h1>АКБ квадроцикла</h1><p>Сравнение энергии, времени работы и нагрева. Один блок по умолчанию; отдельный вариант с двумя двигателями 15/30 кВт.</p></div></section>
<section class="section" id="compare"><div class="wrap"><p class="eyebrow">Расчётное сравнение конфигураций</p><h2>Энергия, длительность работы и тепловыделение</h2>
<div class="segmented"><button data-metric="range" aria-pressed="true">Пробег</button><button data-metric="runtime" aria-pressed="false">Время работы</button><button data-metric="heat" aria-pressed="false">Нагрев</button></div>
<div class="toolbar"><div class="field"><label for="range-mode">Ориентир пробега</label><select id="range-mode"><option value="wmtc">По циклу WMTC</option><option value="utility">Средняя эксплуатация</option></select></div>
<div class="field"><label for="motors">Двигателей 15/30 кВт</label><select id="motors"><option value="1">Один</option><option value="2">Два: свой блок на каждый</option></select></div>
<div class="field"><label for="blocks">Подключено одновременно</label><select id="blocks"><option value="1" selected>Один блок</option><option value="2">Два одинаковых блока</option></select></div>
<div class="field"><label for="cutoff">Отсечка ячеек с распределённым токосъёмом</label><select id="cutoff"><option value="2.8">2,8 В</option><option value="2.9" selected>2,9 В</option><option value="3.0">3,0 В</option></select></div>
<div class="field"><label for="profile">Запрос на один двигатель</label><select id="profile">{p_opts}</select></div>
<div class="field"><label for="cooling">Теплоотвод одного блока</label><select id="cooling"><option value="0">Без теплоотвода</option><option value="5" selected>5 Вт/К</option><option value="20">20 Вт/К</option></select></div>
<div class="field wide"><label for="selection">Сборка</label><select id="selection"><option value="all">Все кандидаты</option>{opts}</select></div></div>
<div class="chart"><h3 id="chart-title"></h3><button id="back-all" class="text-button" hidden>Все сборки</button><div id="chart-legend" class="legend"></div><div id="bars"></div><div id="axis" class="axis"></div><p id="chart-note" class="note"></p></div><div id="detail" class="detail" hidden></div>
<details id="control"><summary>Как рассчитаны энергия, импульсы и температура</summary>{method_html}<p><a href="{brp_url}">Паспорт BRP</a> · <a href="calculation_audit.json">Все расчётные сценарии</a></p></details>
</div></section>
<section class="section soft" id="catalog"><div class="wrap"><h2>Исходные данные и расчётные параметры</h2><p class="note">Закупка прежде всего на Alibaba. Показано самое дешёвое предложение точной модели с указанной ценой, кроме отсутствующих в наличии. Стоимость рассчитана для выбранного числа блоков и относится только к ячейкам; наличие, партия и доставка требуют уточнения. <a href="alibaba_quotes_2026-10-01.csv">Все исходные предложения</a></p>
<div class="segmented"><button data-view="energy" aria-pressed="true">Энергия и цена</button><button data-view="modes" aria-pressed="false">Результаты режима</button><button data-view="electrical" aria-pressed="false">Электрические параметры</button><button data-view="cells" aria-pressed="false">Паспорта</button></div><div class="tables-intro"><p id="table-state"></p><button id="reset-sort" class="text-button">Сбросить сортировку</button></div><div class="table-wrap"><table><thead id="table-head"></thead><tbody id="table-body"></tbody></table></div></div></section>
<section class="section"><div class="wrap"><details><summary>Разрядные испытания и проверка температуры</summary>{updated_test_section(esc).split('<section class="soft section" id="alibaba">')[0]}</details><details><summary>Источники и паспорта</summary>{source_html}</details></div></section>
</main><footer class="footer"><div class="wrap">Редакция 14 · <a href="{PDF}">Отчёт PDF</a></div></footer><script type="application/json" id="report-data">{embedded_data}</script><script src="report.js?v={RELEASE}" defer></script></body></html>'''
# Russian prose replacements outside scripts, preserving source URLs and names.
from html.parser import HTMLParser
class RussianHTML(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=False);self.parts=[];self.script=False
 def handle_starttag(self,tag,attrs):self.parts.append(self.get_starttag_text());self.script=tag=='script' or self.script
 def handle_endtag(self,tag):self.parts.append('</'+tag+'>');self.script=False if tag=='script' else self.script
 def handle_data(self,t):
  if not self.script:
   for a,b in [('tabless','с распределённым токосъёмом'),('no CCC logo','без маркировки CCC'),('no CCC','без маркировки CCC'),('identity unconfirmed','идентичность не подтверждена'),('gray legend 25 A / curve label 30 A','серая подпись 25 А / кривая 30 А'),('April 2025','апрель 2025'),('not 50P','не 50P'),('not H51','не H51'),('small spiral CCC retest','повторное испытание малой спирали с CCC'),('engineering sample','инженерный образец'),('production','серийная версия'),('Pouch','Пакетные'),('pouch','пакетные'),('Datasheet','Паспорт'),('≈Wh','≈Вт·ч'),('≈Ah','≈А·ч'),('Tmax','Максимум температуры'),('SOC','заряд'),('CAD','трёхмерная компоновка')]:t=t.replace(a,b)
  self.parts.append(t)
 def handle_entityref(self,n):self.parts.append('&'+n+';')
 def handle_charref(self,n):self.parts.append('&#'+n+';')
 def handle_decl(self,d):self.parts.append('<!'+d+'>')
parser=RussianHTML();parser.feed(doc);doc=''.join(parser.parts)
(OUT/'index.html').write_text(doc)
pdfmetrics.registerFont(TTFont('DV','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DV-Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFontFamily('DV',normal='DV',bold='DV-Bold')
styles=getSampleStyleSheet()
for key,size,lead in [('Normal',12,18),('BodyText',12,18),('Heading1',29,34),('Heading2',20,26),('Heading3',15,21)]:
 styles[key].fontName='DV-Bold' if key.startswith('Heading') else 'DV';styles[key].fontSize=size;styles[key].leading=lead
styles.add(ParagraphStyle('Cell',fontName='DV',fontSize=9.5,leading=13,textColor=colors.HexColor('#1d1d1f')))
styles.add(ParagraphStyle('Method',fontName='DV',fontSize=11,leading=16))
styles.add(ParagraphStyle('Small',fontName='DV',fontSize=10,leading=14,textColor=colors.HexColor('#626269')))
styles.add(ParagraphStyle('Cover',fontName='DV-Bold',fontSize=45,leading=49,spaceAfter=20))
W,H=landscape(A3); margin=38; avail=W-2*margin
story=[]
def para(s,style='BodyText'):return Paragraph(linked(s,True),styles[style])
def raw(s,style='Cell'):return Paragraph(s,styles[style])
def add(text,style='BodyText'):story.extend([para(text,style),Spacer(1,10)])
def page(title):
 while story and isinstance(story[-1],Spacer):story.pop()
 story.append(PageBreak());add(title,'Heading1')
def pdf_photo(k,width=76):
 p=photos.get(k)
 if not p:return [raw('Фото точной модели не найдено','Small')]
 # Embed a print-sized image instead of the multi-megapixel source.
 with RasterImage.open(OUT/p['file']) as source:
  source.thumbnail((480,400),RasterImage.Resampling.LANCZOS)
  raster=source.convert('RGBA');background=RasterImage.new('RGB',raster.size,'white');background.paste(raster,mask=raster.getchannel('A'))
  stream=BytesIO();background.save(stream,format='JPEG',quality=90);stream.seek(0)
 im=Image(stream);scale=min(width/im.imageWidth,64/im.imageHeight);im.drawWidth=im.imageWidth*scale;im.drawHeight=im.imageHeight*scale
 return [im]
def table(head,values,widths,photo_col=None):
 items=[[raw('<b>'+esc(h)+'</b>') for h in head]]
 for row in values:
  items.append([pdf_photo(x) if i==photo_col else (x if not isinstance(x,(str,int,float)) else raw(esc(x).replace('\n','<br/>'))) for i,x in enumerate(row)])
 t=Table(items,colWidths=[avail*w/sum(widths) for w in widths],repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9eef4')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f7f7f9')]),('LINEBELOW',(0,0),(-1,-1),.35,colors.HexColor('#dedee3')),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
 story.append(t)
def sim(r,b=1,g=5,p='constant15'):return r['simulations'][f'{b}_{g}_{p}']
def chart(metric,b=1,g=5,p='mixed'):
 rr=[r for r in rows if r['candidate']]; step=25; bar_h=13; ht=(len(rr)+1)*step+34; dr=Drawing(avail,ht);left=245;plotw=avail-left-130
 vals=[]
 for r in rr:
  s=sim(r,b,g,p);vals.append((s['wmtc_equiv' if metric=='range' else 'utility_equiv'] if s else None) if metric in ['range','utility'] else (None if not s else s['minutes' if metric=='runtime' else 'heat_mean']))
 pairs=sorted(zip(rr,vals),key=lambda item:(item[1] is None, (item[1] if metric=='heat' else -item[1]) if item[1] is not None else 0))
 rr,vals=map(list,zip(*pairs))
 mx=max([v for v in vals if v is not None]+([80 if metric=='range' else 50] if metric in ['range','utility'] else [1]))*1.07
 if metric in ['range','utility']:
  y=ht-24;v=80 if metric=='range' else 50
  dr.add(String(0,y+3,'BRP Outlander Electric 2026',fontName='DV',fontSize=10.5))
  dr.add(Rect(left,y,plotw*v/mx,bar_h,fillColor=colors.HexColor('#ed9296'),strokeColor=None))
  dr.add(String(left+plotw+14,y+3,str(v)+' км',fontName='DV',fontSize=10.5))
 for i,(r,v) in enumerate(zip(rr,vals)):
  y=ht-24-(i+1)*step;s=sim(r,b,g,p)
  dr.add(String(0,y+3,(r['name'] if len(r['name'])<39 else r['name'][:36]+'…'),fontName='DV',fontSize=10.5,fillColor=colors.HexColor('#1d1d1f')))
  dr.add(Rect(left,y,plotw,bar_h,fillColor=colors.HexColor('#f1f1f5'),strokeColor=None))
  if v is not None:
   dr.add(Rect(left,y,plotw*v/mx,bar_h,fillColor=colors.HexColor('#0071e3' if s else '#c9c9d0'),strokeColor=None))
   if metric=='runtime' and s:
    dr.add(Rect(left,y,plotw*v/mx,bar_h,fillColor=colors.HexColor('#b4d6f7'),strokeColor=None))
    dr.add(Rect(left,y,plotw*s['full_minutes']/mx,bar_h,fillColor=colors.HexColor('#0071e3'),strokeColor=None))
  label='нет данных' if v is None else (('≤ ' if not s else '')+n(v,0)+(' км' if metric in ['range','utility'] else ' мин' if metric=='runtime' else ' Вт'))
  if metric=='runtime' and s:label=n(s['full_minutes'],0)+' / '+n(v,0)+' мин'
  dr.add(String(left+plotw+14,y+3,label,fontName='DV',fontSize=10.5,fillColor=colors.HexColor('#626269')))
 return dr


add('АКБ квадроцикла','Cover');add('Энергия, время работы и нагрев','Heading1')
add('Редакция 14 · 02.10.2026. Один блок по умолчанию; один или два двигателя 15/30 кВт. Для цилиндрических кандидатов — 26S16P; корпус 230×400×340 мм, цель до 40 кг на блок.')
for t in method:add(t.replace('tabless','с распределённым токосъёмом'),'Method')
for metric,title in [('range','Пробег: энергетический ориентир WMTC'),('utility','Пробег: средняя эксплуатация'),('runtime','Длительность умеренной поездки'),('heat','Среднее тепловыделение в умеренной поездке')]:
 page(title);add('Один блок; полный заряд; 25 °C; теплоотвод 5 Вт/К. Сценарная оценка. Светло-красный ориентир — BRP; синий — результат расчёта. Неизвестные данные не заменены границами по энергии.','Small');story.append(chart(metric))
page('Номинальная и выданная энергия: все конфигурации')
table(['Сборка','Номинал, кВт·ч','Выдано, кВт·ч','WMTC, км-экв.','Средняя эксплуатация, км-экв.','Мин полный / всего','Максимум температуры, °C','Завершение'],[[r['name'],n(r['energy'],2),n(sim(r,p='mixed')['output_kwh'],2) if sim(r,p='mixed') else '—',n(sim(r,p='mixed')['wmtc_equiv'],0) if sim(r,p='mixed') else '—',n(sim(r,p='mixed')['utility_equiv'],0) if sim(r,p='mixed') else '—',n(sim(r,p='mixed')['full_minutes'],0)+' / '+n(sim(r,p='mixed')['minutes'],0) if sim(r,p='mixed') else '—',n(sim(r,p='mixed')['t_peak'],1) if sim(r,p='mixed') else '—',sim(r,p='mixed')['stop_reason'] if sim(r,p='mixed') else 'Нужны исходные данные'] for r in rows],[2,1,1,1,1.2,1.1,1,1.7])
page('Два двигателя: отдельный блок 26S16P на каждый')
add('Суммарный запрос 30/60 кВт; каждый блок питает свой двигатель 15/30 кВт. Время и температура относятся к каждой ветви; энергия и тепло — сумма двух. По постоянному запросу 15 кВт на каждый двигатель.','Small')
table(['Сборка','Энергия двух блоков, кВт·ч','Выдано вместе, кВт·ч','Мин без снижения / всего','Максимум температуры, °C','Тепло ячеек вместе, кДж','Средняя суммарная мощность, кВт'],[[r['name'],n(2*r['energy'],2),n(2*sim(r)['output_kwh'],2) if sim(r) else '—',n(sim(r)['full_minutes'],0)+' / '+n(sim(r)['minutes'],0) if sim(r) else '—',n(sim(r)['t_peak'],1) if sim(r) else '—',n(2*sim(r)['heat_kj'],0) if sim(r) else '—',n(2*sim(r)['mean_power'],1) if sim(r) else '—'] for r in rows if r['s']==26 and r['p']==16],[2,1.3,1.3,1.3,1.1,1.2,1.4])
page('Исходные данные и закупка на Alibaba')
from procurement import best_offer
values=[]
for r in rows:
 o=best_offer(models[r['model']].get('market',{}).get('alibaba',{}).get('offers',[]))
 values.append([r['model'],r['cell_name'],str(r['s'])+'S'+str(r['p'])+'P',n(r['energy'],2),n(r['mass'],1)+' / '+n(r['finished'][0])+'–'+n(r['finished'][1]),dim(models[r['model']]['dims']), '—' if o is None else n(o['price'],2)+' / '+n(o['price']*r['n'],2)+' $',r['fit']])
table(['Фото','Ячейка','Сборка','Номинал, кВт·ч','Масса ячеек / блока, кг','Размер, мм','Alibaba: шт. / блок','Компоновка'],values,[.9,1.8,.8,.8,1.2,1.2,1.2,1.8],0)
page('Электрические ограничения')
table(['Модель','Сопротивление, мОм','Источник сопротивления','Предел тока и условия'],[[r['cell_name'],n(r['dc_model'],2),r['dc_basis'],models[r['model']]['note']] for r in rows],[1.6,.8,1.3,5])
page('Источники')
add('Паспорт BRP: '+brp_url,'Small')
for v in data['sources']:
 if v['url']:add('Источник '+v['id']+' — '+v['url'],'Small')
def footer(canvas,doc):
 canvas.setFont('DV',9);canvas.drawString(margin,20,'Редакция 14 · 02.10.2026');canvas.drawRightString(W-margin,20,str(doc.page))
while story and isinstance(story[-1],Spacer):story.pop()
SimpleDocTemplate(str(OUT/PDF),pagesize=landscape(A3),rightMargin=margin,leftMargin=margin,topMargin=margin,bottomMargin=margin,title='АКБ квадроцикла · редакция 14',author='').build(story,onFirstPage=footer,onLaterPages=footer)
print('Built',OUT/PDF)
