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
from mooch_section import section as mooch_section
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'dist'; PDF='AKB_96V_Comparative_Study_2026-09-20.pdf'; RELEASE='20260920-r6'
data=json.loads((ROOT/'calculated.json').read_text()); rows=data['rows']; models=data['models']; photos=json.loads((ROOT/'photos.json').read_text())
data['photos']=photos
SOURCES={s['id']:s for s in data['sources']}
esc=lambda x:html.escape(str(x))
def n(x,d=1):return '—' if x is None else f'{x:.{d}f}'.replace('.',',')
def dim(a):return '×'.join(n(x,0 if float(x).is_integer() else 2) for x in a)
def cell_dim(m):
 return 'Ø'+n(m['dims'][0],2)+' × '+n(m['dims'][2],2) if m['type'].startswith(('21700','18650')) else dim(m['dims'])
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
knowledge=''.join(f'<details id="{key}"><summary>{esc(title)}</summary>'+''.join('<p>'+linked(t)+'</p>' for t in texts)+'</details>' for key,title,texts in SECTIONS if key!='conclusion')
conclusion=SECTIONS[-1][2]
source_html=''.join(f'<div class="source-item" id="source-{s["id"]}"><a href="{esc(s["url"])}" target="_blank" rel="noopener">[{s["id"]}] {esc(s["title"])}</a><p>{esc(s["note"])}</p></div>' if s['url'] else f'<div class="source-item" id="source-{s["id"]}"><strong>[{s["id"]}] {esc(s["title"])}</strong><p>{esc(s["note"])}</p></div>' for s in data['sources'])
opts=''.join(f'<option value="{r["id"]}">{esc(r["name"])}</option>' for r in rows if r['candidate'])
p_opts=''.join(f'<option value="{p["id"]}">{esc(p["name"])}</option>' for p in data['profiles'])
cards=''.join(f'<article class="recommend"><img src="{pic(k)}" alt="{esc(models[k]["name"])}: {esc(photos[k]["caption"])}"><h3>{esc(models[k]["name"])}</h3><p>{txt}</p></article>' for k,txt in [
 ('rs50','<strong>Первым на испытание.</strong> Около 14,83 кВт·ч на два блока по минимальной ёмкости. Хороший запас массы и свежий независимый тест.'),
 ('bak50d2','<strong>Сильная альтернатива.</strong> Низкий измеренный DCIR. Проверить серийность и повторяемость партии. На фото — линейка BAK.'),
 ('eve50pl','<strong>После сверки партии.</strong> Перспективная мощность и масса. Паспорта и испытания разных версий нельзя объединять без проверки.')])
embedded_data=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
doc=f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Сравнение аккумуляторов съёмного блока 96 В: компоновка, масса, энергоёмкость, ограничения мощности и тепловая оценка."><title>АКБ 96 В — энергия, мощность, маршрут</title><link rel="stylesheet" href="report.css?v={RELEASE}"></head><body>
<nav class="nav" aria-label="Основная навигация"><div class="wrap"><a href="#" class="brand">АКБ 96 В</a><a href="#compare">Сравнение</a><a href="#mooch">Тесты 21700</a><a class="hide-mobile" href="#research">Исследование</a><a class="hide-mobile" href="#choice">Вывод</a><a class="pill" href="{PDF}">Скачать PDF</a></div></nav>
<main><div class="wrap"><aside class="release-note" id="release"><strong>Обновление {RELEASE}</strong><span>{len(models)} моделей · {len(rows)} конфигурации · 43 записи Mooch</span><a href="#mooch">Тесты и выгрузки</a></aside><header class="hero"><div><p class="eyebrow">Редакция 6 · 20 сентября 2026</p><h1>Энергия для<br>вашего маршрута.</h1><p>Два съёмных блока. Один должен питать двигатель 15/30 кВт. Сравнение ячеек с учётом нагрева и ограничения мощности.</p></div><div class="hero-stats"><div><strong>230×400×340</strong><span>мм · наружные Ш×Г×В</span></div><div><strong>до 40 кг</strong><span>цель для готового блока</span></div><div><strong>≈15 кВт·ч</strong><span>цель для двух блоков</span></div><div><strong>26S</strong><span>109,2 В при заряде до 4,2 В/яч.</span></div></div></header></div>
<section class="soft section" id="compare"><div class="wrap"><div class="section-top"><div><p class="eyebrow">Сначала — общая картина</p><h2>Сравните свой запас.</h2><p>На графике — {sum(r['candidate'] for r in rows)} предварительных кандидатов. Выберите сборку, чтобы увидеть заряд, температуру и доступную мощность во времени.</p></div></div><div class="panel">
<div class="toolbar"><div class="field"><label for="blocks">Подключено одновременно</label><select id="blocks"><option value="1">Один блок</option><option value="2" selected>Два одинаковых блока</option></select></div><div class="field"><label for="profile">Запрос мощности</label><select id="profile">{p_opts}</select></div><div class="field"><label for="cooling">Сценарий теплоотвода</label><select id="cooling"><option value="5">Слабый · G = 5 Вт/К</option><option value="20">Улучшенный · G = 20 Вт/К</option></select></div><div class="field wide"><label for="selection">Сборка</label><select id="selection"><option value="all">Все кандидаты</option>{opts}</select></div></div>
<div class="segmented" aria-label="Показатель графика"><button data-metric="range" aria-pressed="true">Пробег</button><button data-metric="runtime" aria-pressed="false">Время работы</button><button data-metric="heat" aria-pressed="false">Нагрев</button></div><div class="chart-heading"><h3 id="chart-title"></h3><button class="text-button" id="back-all" hidden>← Все сборки</button></div><div id="chart-legend" class="legend"></div><div class="bars" id="bars"></div><div id="axis" class="axis"></div><p id="chart-note" class="note" style="margin-top:24px"></p><div class="detail" id="detail" hidden></div>
<div class="callout"><strong>Ограничение тяги, а не фиксированный ток.</strong> Модель учитывает падение напряжения, рейтинг ячейки и выбранное снижение мощности по SOC и температуре. Карты управления предварительные; 50% SOC не универсальная граница. <a href="#control">Методика расчёта</a></div>
</div></div></section>
<section class="section" id="catalog"><div class="wrap"><p class="eyebrow">{len(models)} моделей · {len(rows)} конфигурации</p><h2>Все параметры.<br>В одном каталоге.</h2><div class="segmented" aria-label="Вид таблицы"><button data-view="energy" aria-pressed="true">Энергия и компоновка</button><button data-view="electrical" aria-pressed="false">Ток и сопротивление</button><button data-view="modes" aria-pressed="false">Режимы работы</button><button data-view="cells" aria-pressed="false">Паспорта элементов</button></div><div class="tables-intro"><p id="table-state"></p><button class="text-button" id="reset-sort">Вернуть исходный порядок ↺</button></div><p class="note">Нажмите заголовок для сортировки. «Фото» и «Элемент / сборка» возвращают исходную группировку по типу и производителю. В разделе режимов действуют настройки графика выше. Масса сортируется по нижней границе, корпус — по объёму. Пустые данные всегда в конце.</p><div class="table-wrap" tabindex="0" role="region" aria-label="Сравнение сборок, таблицу можно прокручивать"><table><thead id="table-head"></thead><tbody id="table-body"></tbody></table></div><p class="note" style="margin-top:18px">* Граница по энергии без доказанной токоотдачи и нагрева. Размеры — для дальнейшей проработки в CAD. В цилиндрической схеме не учтены размеры ячеек с приваренными лепестками; фото могут относиться к иной партии.</p></div></section>
{mooch_section()}<section class="soft section" id="research"><div class="wrap"><div class="knowledge"><p class="eyebrow">Откуда берутся цифры</p><h2>За каждым результатом<br>есть условия.</h2>{knowledge}</div></div></section>
<section class="dark section" id="choice"><div class="wrap"><p class="eyebrow muted">Итог исследования</p><h2>Начать с секции.<br>Выбрать по измерениям.</h2><p class="muted">Первая группа для испытания: RS50, BAK 50D2, подтверждённая версия EVE 50PL и Tenpower 50XG. Свежие 50T/60Q — в каталоге тестов.</p><div class="recommendations">{cards}</div><div class="knowledge">{''.join('<p>'+linked(p)+'</p>' for p in conclusion)}</div></div></section>
<section class="section" id="sources"><div class="wrap"><p class="eyebrow">Проверяемые источники</p><h2>Паспорта и испытания.</h2><div class="sources">{source_html}</div></div></section></main><footer class="footer"><div class="wrap">Редакция 6 · Предварительный инженерный отбор · <a href="{PDF}">Полный отчёт PDF</a></div></footer><noscript>Для интерактивного сравнения включите JavaScript. Все таблицы и расчёты также доступны в PDF по ссылке сверху.</noscript><script type="application/json" id="report-data">{embedded_data}</script><script src="report.js?v={RELEASE}" defer></script><script id="mooch-data" type="application/json">{(OUT/"mooch_data.json").read_text()}</script><script src="mooch.js?v={RELEASE}" defer></script></body></html>'''
(OUT/'index.html').write_text(doc)

# PDF: broad tables separated into views, then model cards and complete methodology.
pdfmetrics.registerFont(TTFont('DV','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DV-Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFontFamily('DV',normal='DV',bold='DV-Bold')
styles=getSampleStyleSheet()
for key,size,lead in [('Normal',12,18),('BodyText',12,18),('Heading1',29,34),('Heading2',20,26),('Heading3',15,21)]:
 styles[key].fontName='DV-Bold' if key.startswith('Heading') else 'DV';styles[key].fontSize=size;styles[key].leading=lead
styles.add(ParagraphStyle('Cell',fontName='DV',fontSize=9.5,leading=13,textColor=colors.HexColor('#1d1d1f')))
styles.add(ParagraphStyle('Small',fontName='DV',fontSize=10,leading=14,textColor=colors.HexColor('#626269')))
styles.add(ParagraphStyle('Cover',fontName='DV-Bold',fontSize=45,leading=49,spaceAfter=20))
W,H=landscape(A3); margin=38; avail=W-2*margin
story=[]
def para(s,style='BodyText'):return Paragraph(linked(s,True),styles[style])
def raw(s,style='Cell'):return Paragraph(s,styles[style])
def add(text,style='BodyText'):story.extend([para(text,style),Spacer(1,10)])
def page(title):story.append(PageBreak());add(title,'Heading1')
def pdf_photo(k):
 p=photos.get(k)
 if not p:return raw('Фото точной модели не найдено','Small')
 # Embed a print-sized image instead of the multi-megapixel source.
 with RasterImage.open(OUT/p['file']) as source:
  source.thumbnail((480,400),RasterImage.Resampling.LANCZOS)
  raster=source.convert('RGBA');background=RasterImage.new('RGB',raster.size,'white');background.paste(raster,mask=raster.getchannel('A'))
  stream=BytesIO();background.save(stream,format='JPEG',quality=90);stream.seek(0)
 im=Image(stream);scale=min(76/im.imageWidth,64/im.imageHeight);im.drawWidth=im.imageWidth*scale;im.drawHeight=im.imageHeight*scale
 return [im,raw(esc(p['caption']),'Small')]
def table(head,values,widths,photo_col=None):
 items=[[raw('<b>'+esc(h)+'</b>') for h in head]]
 for row in values:
  items.append([pdf_photo(x) if i==photo_col else (x if not isinstance(x,(str,int,float)) else raw(esc(x).replace('\n','<br/>'))) for i,x in enumerate(row)])
 t=Table(items,colWidths=[avail*w/sum(widths) for w in widths],repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9eef4')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f7f7f9')]),('LINEBELOW',(0,0),(-1,-1),.35,colors.HexColor('#dedee3')),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
 story.append(t)
def sim(r,b=1,g=5,p='constant15'):return r['simulations'][f'{b}_{g}_{p}']
def chart(metric,b=2,g=5,p='mixed'):
 rr=[r for r in rows if r['candidate']]; ht=len(rr)*31+42; dr=Drawing(avail,ht);left=245;plotw=avail-left-130
 vals=[]
 for r in rr:
  s=sim(r,b,g,p);vals.append((s['wmtc_equiv'] if s else r['energy_ceiling_wmtc']*b) if metric=='range' else (None if not s else s['minutes' if metric=='runtime' else 'heat_mean']))
 mx=max(v for v in vals if v is not None)*1.07
 for i,(r,v) in enumerate(zip(rr,vals)):
  y=ht-29-i*31;s=sim(r,b,g,p)
  dr.add(String(0,y+3,r['name'],fontName='DV',fontSize=10.5,fillColor=colors.HexColor('#1d1d1f')))
  dr.add(Rect(left,y,plotw,16,fillColor=colors.HexColor('#f1f1f5'),strokeColor=None))
  if v is not None:
   dr.add(Rect(left,y,plotw*v/mx,16,fillColor=colors.HexColor('#0071e3' if s else '#c9c9d0'),strokeColor=None))
   if metric=='runtime' and s:
    dr.add(Rect(left,y,plotw*v/mx,16,fillColor=colors.HexColor('#b4d6f7'),strokeColor=None))
    dr.add(Rect(left,y,plotw*s['full_minutes']/mx,16,fillColor=colors.HexColor('#0071e3'),strokeColor=None))
  label='нет данных' if v is None else (('≤ ' if not s else '')+n(v,0)+(' км' if metric=='range' else ' мин' if metric=='runtime' else ' Вт'))
  if metric=='runtime' and s:label=n(s['full_minutes'],0)+' / '+n(v,0)+' мин'
  dr.add(String(left+plotw+14,y+3,label,fontName='DV',fontSize=10.5,fillColor=colors.HexColor('#626269')))
 return dr

add('АКБ квадроцикла','Cover');add('Энергия, мощность и температура','Heading1')
add('Редакция 6 · 20.09.2026. Два съёмных блока; каждый должен самостоятельно питать двигатель 15/30 кВт. Наружные Ш×Г×В 230×400×340 мм, цель до 40 кг. Все токи относятся к DC-стороне батареи.')
table(['Объём блока','Целевая масса','Энергия двух блоков','Полный заряд 26S'],[['31,28 л','≤40 кг','Около 15 кВт·ч','109,2 В при 4,2 В/яч.; S45A до 113,1 В']],[1,1,1,2])
for t in [
 'В первую очередь испытать Reliance RS50 26S16P и BAK 50D2 26S16P; добавить Tenpower 50XG в испытания партии. EVE 50PL интересна после согласования версии. Molicel P50B — документированный ориентир; Farasis S46/P79/P84 остаются кандидатами с недостающими токовыми и тепловыми данными.',
 'Расчёт больше не задаёт условный постоянный ток батареи: он определяется запросом мощности, напряжением, просадкой и ограничениями. Контроллер должен снижать тягу по данным BMS, а не ждать аварийного отключения.',
 'Время до первого снижения мощности и полное время до резерва показаны раздельно. Пробег — энергетический эквивалент по индексам BRP, а не сертифицированный WMTC. После снижения мощности соблюдение графика WMTC не подтверждается.',
 'Численные температуры — предварительная модель средней температуры. Нет DCIR или применимого рейтинга тока — нет достоверного теплового прогноза. «Нет данных» не означает отсутствие нагрева.'
]:add(t)
add('Как читать отчёт: обзорные графики → сводка режимов → полный каталог компоновок → паспорта элементов → методика и источники → окончательный выбор. На сайте те же данные доступны с сортировкой и индивидуальными графиками.','Small')
page('Общий запас: все предварительные кандидаты')
add('Два одинаковых блока одновременно; умеренный сценарий; G=5 Вт/К. Синий — расчёт выданной энергии с ограничениями. Серый — только граница 85% Eном, без доказанной токоотдачи и неизвестных потерь. Километры — энергетический эквивалент по индексу WMTC, не дорожный прогноз.','Small')
story.append(chart('range'))
page('Сколько времени сохраняется тяга')
add('Один блок; постоянный запрос 15 кВт на валу; G=5 Вт/К. Синий — до снижения запрошенной мощности более чем на 2%; светло-синий — работа после снижения до выбранного резерва. Модель не доказывает ресурс или отсутствие локального перегрева.','Small')
story.append(chart('runtime',1,5,'constant15'))
page('Нагрев при запросе 15 кВт')
add('Среднее тепловыделение в ячейках одного блока за всю поездку с действующим ограничением мощности. Это не тепло при неизменных 15 кВт на всём протяжении. Неизвестные DCIR не заменены ACIR. Внешние потери линии проверяются отдельно.','Small')
story.append(chart('heat',1,5,'constant15'))
page('Режимы: измеримые исходные данные')
add('Один блок, 25 °C, G=5 Вт/К. Точность округления не означает точность модели. Тепло и температура из независимого DCIR имеют статус условного переноса на сборку.','Small')
vals=[]
for r in rows:
 s=sim(r)
 if s:
  a=sim(r,p='mixed');two=sim(r,2);cool=sim(r,1,20)
  vals.append([r['model'],r['name'],r['format'],n(a['minutes'],0)+' / '+n(a['utility_equiv'],0),n(s['full_minutes'])+' / '+n(s['minutes']),n(s['heat_mean'],0)+' / '+n(s['t_end'],0),n(two['full_minutes'])+' / '+n(two['minutes']),n(cool['full_minutes'])+' / '+n(cool['t_end'],0),s['first_limit']])
table(['Фото','Сборка','Тип','Умеренно: мин / рабочий км-экв.','15 кВт: мин полный / всего','15 кВт: Вт / °C','Два: мин полный / всего','G=20: мин полный / °C','Первое ограничение'],vals,[.8,1.5,.7,1,1.1,1,1.1,1,1.2],0)
page('Весь каталог: энергия и компоновка')
add('Исходный порядок: тип → производитель → модель. Масса обвязки оценочная: цилиндры +8–13 кг, pouch по сложности +8–15 кг. Полный жидкостный контур может потребовать дополнительной массы. Корпус — для дальнейшей проработки, не гарантированный минимум.','Small')
vals=[]
for r in rows:
 vals.append([r['model'],r['name']+'\n'+r['format'],r['n'],n(r['energy'],2)+' / '+n(2*r['energy'],2),n(r['mass'],2)+'\n'+n(r['finished'][0])+'–'+n(r['finished'][1]),r['layout'],r['fit'],dim(r['box'])+'\nΔ '+ '/'.join(f'{x:+d}' for x in r['delta']),n(40-r['mass'],2)])
table(['Фото','Элемент / тип / сборка','Число','Энергия 1 / 2, кВт·ч','Ячейки / готовый, кг','Предлагаемое размещение, мм','Оценка для 230×400×340','Корпус для CAD / Δ, мм','Обвязка до 40 кг'],vals,[.8,1.5,.45,.8,1,1.8,1.25,1.1,.7],0)
page('Паспорта элементов и электрические ограничения')
add('Фото служит идентификации модели; оно не подтверждает партию. В строках EVE 50PL масса выбранной редакции и независимый DCIR не принадлежат доказанно одному исполнению. На графике такой перенос условный. Сопротивление при разных длительностях импульса нельзя сравнивать как одну и ту же величину.','Small')
seen=set();vals=[]
for r in rows:
 k=r['model']
 if k in seen:continue
 seen.add(k);m=models[k]
 rating=[]
 if m.get('continuous'):rating.append(n(m['continuous'],0)+' А; условия в примечании')
 if m.get('conditional_current'):rating.append(n(m['conditional_current'],0)+' А с температурной отсечкой')
 if m.get('pulse'):rating.append(n(m['pulse'],0)+' А / '+str(m['seconds'])+' с')
 if m.get('reported_current'):rating.append(n(m['reported_current'],0)+' А по исследованию')
 vals.append([k,m['name']+'\n'+r['format'],n(m['ah'],2)+' А·ч\n'+n(m['v'],2)+' В',cell_dim(m)+' мм\n'+n(m['kg']*1000,1)+' г','; '.join(rating) or 'Не подтверждён',m['res']+(('\nВ модели '+n(r['dc_model'],2)+' мОм; '+r['dc_basis']) if r['dc_model'] else ''),m['note']+' ['+m['source']+']'])
table(['Фото','Модель / тип','Номиналы','Размер / масса','Ток ячейки','Сопротивление','Условия и редакция'],vals,[.9,1.25,.7,1.0,1.25,1.55,3.3],0)
page('Сопротивление последовательной ветви и линии')
add('r — DCIR одной ячейки в мОм. Ветвь: Ns×r; эквивалент всей сборки: Ns/Np×r. Линия дополнительно включает условный 1 мОм внешних проводников и коммутации. При неизвестном DCIR приведена формула, численного прогноза тепла нет.','Small')
table(['Сборка','Источник DCIR','DCIR, мОм','Ветвь, мОм','Сборка + линия, мОм','Ток ячейки для 30 кВт при Uном'],[[r['name'],r['dc_basis'],n(r['dc_model'],2),n(r['r_string'],2) if r['r_string'] else str(r['s'])+'r',n(r['r_total'],2) if r['r_total'] else n(r['s']/r['p'],3)+'r + 1',n(34290.909/r['voltage']/r['p'])+' А / '+n(r['voltage'])+' В'] for r in rows],[2,1.8,1,1,1.4,2.1])
for key,title,texts in SECTIONS:
 if key=='conclusion':continue
 page(title)
 for t in texts:add(t)
 if key=='control':
  table(['Напряжение под нагрузкой','15 кВт на валу: ток блока','30 кВт на валу: ток блока','30 кВт: ток ячейки 16P'],[[str(v)+' В',n((15/.88+.2)*1000/v)+' А',n((30/.88+.2)*1000/v)+' А',n((30/.88+.2)*1000/v/16)+' А'] for v in [109.2,105,100,95,90,85]],[1,1,1,1])
  add('Все строки показывают требуемый ток до ограничений по току ячейки, SOC и температуре. Ни 90 В, ни 85 В не считаются универсальным порогом мощности. Напряжение после отдыха и напряжение при полном газе не взаимозаменяемы.','Small')
 if key=='tests':table(['Ток','Ячейки','Источник','Результат / ограничение'],[[*r[:4]] for r in TEST_ROWS],[.7,1.5,1.3,4])
 if key=='thermal':
  table(['Сборка','0,75×R: мин полный / T конца','1,5×R: мин полный / T конца'],[[r['name'],n(r['sensitivity15'][0]['full_minutes'])+' / '+n(r['sensitivity15'][0]['t_end'])+' °C',n(r['sensitivity15'][1]['full_minutes'])+' / '+n(r['sensitivity15'][1]['t_end'])+' °C'] for r in rows if r['id'] in ['C03','C16','C17','C18']],[2,2,2])
  add('Чувствительность для запроса 15 кВт, одного блока, G=5. Множители сопротивления выбраны для проверки устойчивости вывода, не являются доверительным интервалом измерений.','Small')
page('Источники и основания расчёта')
for s in data['sources']:
 entry=[para('['+s['id']+'] '+s['title'],'Heading3'),Spacer(1,8),para(s['note'],'Small'),Spacer(1,8)]
 if s['url']:entry.append(raw(f'<a href="{esc(s["url"])}" color="#0071e3">Открыть источник</a>','Small'))
 entry.append(Spacer(1,16));story.append(KeepTogether(entry))
page('Итог: наиболее подходящие элементы')
for t in conclusion:add(t)
add('Перед заказом полного комплекта: согласовать паспорт и маркировку партии, измерить DCIR/разрядную энергию на целевых токах, выполнить тепловой тест секции и готового блока, проверить связь BMS с контроллером и рекуперацию. По имеющимся данным первым кандидатом остаётся Reliance RS50; окончательное подтверждение даёт испытание вашего блока.','Heading3')
def footer(c,doc):
 c.setFont('DV',9);c.setFillColor(colors.HexColor('#626269'));c.drawString(margin,22,'АКБ 96 В · редакция 6 · 20.09.2026 · расчёт с ограничениями SOC / температуры');c.drawRightString(W-margin,22,str(doc.page))
pdfdoc=SimpleDocTemplate(str(OUT/PDF),pagesize=(W,H),leftMargin=margin,rightMargin=margin,topMargin=35,bottomMargin=42,title='АКБ 96 В: энергия, мощность и температура',author='Исследование для проекта квадроцикла')
pdfdoc.build(story,onFirstPage=footer,onLaterPages=footer)
print('Built',len(rows),'configurations;',len(models),'models;',PDF)
