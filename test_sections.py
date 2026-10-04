"""User-supplied evidence, separate from manufacturer specifications."""
import json,html,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MANUFACTURERS={
 'EVE':dict(url='https://www.evebattery.com/en/about.htm',text='EVE Energy — китайский производитель литиевых батарей, основанный в 2001 году; работает с потребительскими, тяговыми и стационарными батареями. Для 50PL важны конкретная редакция и масса: испытание образца не объединяет варианты 68 и 72 г в один паспорт.'),
 'Tenpower':dict(url='https://www.tenpowercell.com/about/about-us',text='Tenpower основана в 2006 году и специализируется на цилиндрических литий-ионных ячейках. Основное направление — элементы для силовых применений, включая электроинструмент и малую электрическую технику. В проекте 50XG и 60XG рассматриваются отдельно; доступность 60XG пока ожидает подтверждения продавца.'),
 'Reliance':dict(url='https://www.reliance-battery.com/about-en.html',text='Jiangsu Reliance New Energy Technology основана в 2021 году и разрабатывает цилиндрические ячейки с распределённым токосъёмом (tabless). Компания выпускает линейки RS и RH. Для RS50 критична идентичность партии: здесь использован график small spiral / CCC; это не автоматическое подтверждение всех элементов с названием RS50.'),
 'Great Power':dict(url='https://www.greatpower.net/en/about/',text='Guangzhou Great Power Energy & Technology — китайский изготовитель батарей, основанный в 2001 году. Помимо решений для накопителей энергии компания выпускает цилиндрические ячейки. 50Q и 60Q имеют разные графики разряда; цена 60Q уже получена, но массу и паспорт для компоновки необходимо подтвердить.'),
 'BAK':dict(url='https://www.bakpower.com/about_en.php',text='BAK — китайский производитель литий-ионных батарей с историей с 2001 года и цилиндрическими силовыми линейками. 50D2 относится к tabless-элементам. По предоставленному предложению Vapcell 50D2 отсутствует; это ограничивает закупку у этого продавца, а не отменяет техническую оценку.'),
 'Molicel':dict(url='https://www.molicel.com/about/',text='Molicel — марка E-One Moli Energy, входящей в группу Taiwan Cement Corporation. Истоки компании связаны с канадской Moli Energy (1977); современная специализация — цилиндрические ячейки высокой мощности, производство и разработка в Тайване. Для P50B сохранён серийный график января 2025 отдельно от инженерного образца 2024 года.'),
 'Ampace':dict(url='https://www.tdk.com/en/news_center/press/20210428_01.html',text='Ampace создана в 2021 году как совместное предприятие ATL и CATL для литиевых батарей, в том числе для малой электрической техники и накопителей. Предложение продавца относится к JP50; предоставленный график — к JP50P1 no CCC. Происхождение компании не является основанием считать эти исполнения взаимозаменяемыми.'),
 'Linkdata':dict(url='https://batteryrealdata.com/assets/datasheets/linkdata-inr21700s-50p-21700-5000mah-60a-lithium-ion-cell-datasheet.pdf',text='В оригинальном паспорте INR21700S-50P изготовитель указан как LinkData New Energy Co., Ltd. (联动天翼新能源有限公司); здесь паспорт доступен через сторонний зеркальный сервер. В архиве есть 50T, 55P, 60P и 65P. График 50T не относится к предлагаемой 50P; единое торговое имя не подтверждает одинаковый внутренний элемент.'),
 'Samsung':dict(url='https://www.samsungsdi.com/about-sdi/history.html',text='Samsung SDI — корейский производитель литий-ионных батарей, включая цилиндрические элементы и решения для транспорта и накопителей. 50S и обновлённая 50S2 остаются отдельными моделями с разными результатами испытаний. Новых графиков этих моделей в предоставленном архиве нет; прежние данные сохранены.'),
 'Farasis':dict(url='https://www.farasis-energy.com/en/about-us/',text='Farasis Energy основана в 2002 году и разрабатывает литий-ионные батареи для транспорта. В данном проекте рассматриваются её пакетные ячейки из каталогов и оригинальных паспортов. Рейтинг 21700 не закрывает отсутствие DCIR и токовых карт некоторых pouch-моделей; их тепловые поля остаются неизвестными.'),
 'LG':dict(url='https://www.lgensol.com/mobile/en/company/info-history',text='LG Energy Solution выделена из батарейного бизнеса LG Chem в 2020 году; выпускает батареи для транспорта, накопителей и потребительских применений. В архиве есть M50LT и H51T, а в проекте также H51 и EV-pouch. H51T не подменяет H51, а испытания цилиндров не подтверждают нагрев пакетных ячеек.'),
 'Vapcell':dict(url='https://www.vapcelltech.com/',text='Vapcell — бренд и поставщик аккумуляторов и зарядных устройств. Изготовитель внутреннего элемента под торговой оболочкой должен подтверждаться отдельно: результаты G50 2020 года не относятся к T60 или Q65. Yichuan 50PL также не объединена с EVE 50PL без документа изготовителя.'),
}
def manufacturer(model):
 m=next((value for brand,value in MANUFACTURERS.items() if model.startswith(brand+' ')),None)
 if not m:return ''
 brand=next(brand for brand,value in MANUFACTURERS.items() if value is m)
 client=json.loads((ROOT/'manufacturer_clients.json').read_text())['manufacturers'].get(brand,{})
 text=m['text']+' '+client.get('text','')
 if client.get('id'):text+=' ['+client['id']+(', '+client['id']+'_2' if client.get('extra_url') else '')+']'
 return text
def exports():
 d=json.loads((ROOT/'discharge_tests.json').read_text());q=json.loads((ROOT/'alibaba_quotes.json').read_text())
 with (ROOT/'dist/discharge_energy_temperature.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f,delimiter=';',lineterminator='\n');w.writerow(['Модель / версия','Дата испытания','Ток, А','Энергия до 2.8 В, Wh (оцифровка)','Энергия до 3.0 В, Wh (оцифровка)','Ah до 3.0 В','Tmax, C','Начальная T, C','Прирост T, C','Тепловая остановка','Источник'])
  for ds in d['datasets']:
   for c in ds['curves']:w.writerow([ds['title'],ds['test_date'],c['current_A'],c['energy_2_8_Wh'],c['energy_3_0_Wh'],c['capacity_3_0_Ah'],c['max_C'],25,None if c['delta_C'] is None else round(c['delta_C'],2),c['thermal_stop'],ds['source_filename']])
 with (ROOT/'dist/alibaba_quotes_2026-10-01.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f,delimiter=';',lineterminator='\n');w.writerow(['Модель','USD/шт','Продавец / предложение','Дата предложения','Статус','USD/416 ячеек (условно)','USD/832 ячейки (условно)','Примечание','Дата','Источник'])
  for o in q['offers']:w.writerow([o['model'],o['price'],o['seller'],o['observed_at'],o['availability'],None if o['price'] is None else round(o['price']*416,2),None if o['price'] is None else round(o['price']*832,2),o['note'],o['observed_at'],o['seller_url']])
EXCLUDED_TESTS={'sa112','lg','m50a','g50'}
def test_title(title):
 for old,new in [('no CCC logo','без маркировки CCC'),('identity unconfirmed','идентичность не подтверждена'),('gray legend 25 A / curve label 30 A','серая подпись 25 А / кривая 30 А'),('April 2025','апрель 2025'),('(not H51)','(не H51)'),('(not 50P)','(не 50P)'),('engineering sample','инженерный образец'),('production','серийная версия'),('small spiral CCC retest','повторное испытание малой спирали с CCC')]:
  title=title.replace(old,new)
 return title

def test_cards(esc,include_photo=True):
 d=json.loads((ROOT/'discharge_tests.json').read_text());photos=json.loads((ROOT/'photos.json').read_text())
 val=lambda x:'—' if x is None else f'{x:g}'.replace('.',',')
 cards={}
 for ds in d['datasets']:
  if ds['key'] in EXCLUDED_TESTS:continue
  title=test_title(ds['title']);rows=[]
  for c in ds['curves']:
   status='Остановлен по температуре; без продолжения до отсечки' if c['thermal_stop'] else 'Кривая до 2,8 В' if c['energy_2_8_Wh'] else 'Конец оцифровки неполный; полная энергия неизвестна'
   rows.append('<tr>'+''.join('<td>'+esc(x)+'</td>' for x in [c['current_A'],val(c['energy_2_8_Wh']),val(c['energy_3_0_Wh']),val(c['capacity_3_0_Ah']),val(c['max_C']),val(c['delta_C']),val(c['energy_loss_vs_5A_pct']),status])+'</tr>')
  photo=photos.get('h51' if ds['key']=='h51t' else ds['key'].replace('p50b_sample','p50b'))
  appearance=''
  if include_photo and photo:
   url=photo['file']+'?v='+photo['original_sha256'][:12]
   caption='<figcaption>'+esc(photo['caption'])+'</figcaption>' if photo.get('caption') else ''
   appearance=f'<figure class="cell-appearance"><a href="{url}" target="_blank" rel="noopener"><img src="{url}" loading="lazy" alt="{esc(title)}: фото элемента"></a>{caption}</figure>'
  headings=['Ток, А','≈Вт·ч до 2,8 В','≈Вт·ч до 3,0 В','≈А·ч до 3,0 В','Максимум температуры, °C','ΔT от 25 °C','Потеря E к 5 А, %','Охват']
  cards[ds['key']]=f'<article class="selected-test" data-test="{ds["key"]}"><h3>{esc(title)} · {ds["test_date"]}</h3>{appearance}<p class="note">{esc(ds.get("identity_note","Измерен отдельный образец; перенос на партию и герметичный блок требует проверки."))}</p><a href="{ds["image"]}" target="_blank" rel="noopener"><img class="discharge-chart" src="{ds["image"]}" loading="lazy" alt="{esc(title)}: первичный график разряда Mooch" width="1000"></a><div class="table-wrap"><table><thead><tr>'+''.join('<th>'+x+'</th>' for x in headings)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div></article>'
 return cards

def test_archive(esc):
 cards=test_cards(esc)
 return '<details id="test-archive"><summary>Все разрядные испытания Mooch · '+str(len(cards))+'</summary><p class="note">График и таблица выбранной модели показаны выше, после результатов расчёта. Здесь доступны остальные версии и сравнительные испытания. Энергия приближённо оцифрована по изображениям; начальная температура около 25 °C.</p>'+''.join('<details class="test-card"><summary>'+content.split('<h3>')[1].split('</h3>')[0]+'</summary>'+content+'</details>' for content in cards.values())+'</details>'

def section(esc):
 d=json.loads((ROOT/'discharge_tests.json').read_text());q=json.loads((ROOT/'alibaba_quotes.json').read_text());photos=json.loads((ROOT/'photos.json').read_text())
 archive_count=len(d['datasets'])
 d['datasets']=[ds for ds in d['datasets'] if ds['key'] not in {'sa112','lg','m50a','g50'}]
 d['thermal_audit']=[a for a in d['thermal_audit'] if a['key'] not in {'sa112','lg','m50a','g50'}]
 val=lambda x:'—' if x is None else f'{x:g}'.replace('.',',')
 gallery=[]
 names={r['model']:r['cell_name'].split(' · ')[0] for r in json.loads((ROOT/'calculated.json').read_text())['rows']}
 for key,p in photos.items():
  title=p.get('display_name') or names.get(key) or test_title(next((x['title'] for x in d['datasets'] if x['key']==key),key)).split(' · ')[0].replace(' (не 50P)','')
  alt=f'<a href="{p["alternate"]}" target="_blank">Второй снимок маркировки</a>' if p.get('alternate') else ''
  gallery.append(f'<article class="cell-photo-card"><h3>{esc(title)}</h3><a href="{p["file"]}" target="_blank"><img src="{p["file"]}" loading="lazy" alt="{esc(title)} — реальный элемент"></a><p>{esc(p.get('caption',''))}</p>{alt}</article>')
 gallery_html='<section class="section" id="cell-photos"><div class="wrap"><p class="eyebrow">Фотографии пользователя</p><h2>Как выглядят элементы</h2><p>Снимки взяты из архива пользователя и отдельного вложения Tenpower 50XG. Надпись и оформление относятся к изображённому образцу; параметры другой партии ими не подтверждаются. Наличие фото не означает готовность модели к расчёту блока.</p><div class="cell-photo-grid">'+''.join(gallery)+'</div></div></section>'
 # A load-specific energy order, distinct from project engineering recommendations.
 rank=[]
 for ds in d['datasets']:
  c=next((c for c in ds['curves'] if c['current_A']==20 and c['energy_3_0_Wh'] and not c['thermal_stop']),None)
  if c:rank.append((ds,c))
 rank.sort(key=lambda x:-x[1]['energy_3_0_Wh'])
 rankrows=''.join('<tr>'+''.join('<td>'+esc(x)+'</td>' for x in [i+1,ds['title'],val(c['energy_3_0_Wh']),val(c['capacity_3_0_Ah']),val(c['max_C']),val(c['delta_C'])])+'</tr>' for i,(ds,c) in enumerate(rank))
 status={'quoted':'Цена получена; остаток не подтверждён','out_of_stock':'Нет в наличии у продавца','pending_confirmation':'Ожидается подтверждение'}
 quotes=''.join('<tr>'+''.join('<td>'+esc(x)+'</td>' for x in [o['model'],val(o['price']),o['seller'],o['observed_at'],status[o['availability']],val(None if o['price'] is None else round(416*o['price'],2)),val(None if o['price'] is None else round(832*o['price'],2)),o['note']])+'</tr>' for o in q['offers'])
 auditrows=''.join('<tr>'+''.join('<td>'+esc(x)+'</td>' for x in [a['title'],a['current_A'],val(a['measured_C']),val(a['delta_C']),val(round(a['minutes'],1)),val(a['pack_G5_equivalent_C']),val(a['pack_G20_equivalent_C']),val(a['bench_fit_C']),val(a['bench_residual_C'])])+'</tr>' for a in d['thermal_audit'])
 return gallery_html+f'''<section class="section" id="updated-tests"><div class="wrap"><p class="eyebrow">Данные пользователя · обновление 1 октября 2026</p><h2>Сопоставление разрядных испытаний и тепловой модели</h2><p>Исходный архив содержит {archive_count} графика 21700. В разделе расчётного сравнения доступны {len(d['datasets'])} испытаний силовых кандидатов и сравнительных версий; полные исходные данные сохранены в скачиваемом архиве точек. Энергия рассчитана как ∫V dAh по оцифрованному изображению; это приближённая оценка, а не точная исходная числовая таблица Mooch. Температуры взяты из подписей. Начальное состояние — около 25 °C. Два образца разных лет и исполнения с CCC / без CCC сохранены отдельно.</p><div class="download-links"><a href="discharge_energy_temperature.csv">CSV: энергия и температура</a> · <a href="discharge_tests.json">Точки кривых и аудит модели (JSON)</a> · <a href="#thermal-audit">Проверка тепловой модели</a></div><div class="callout"><strong>Порог напряжения.</strong> В расчёте при 2,9 В включается режим «черепаха» с потолком 3 кВт на двигатель; остановка при 2,65 В либо раньше по границе измерений. В карточке выбранной сборки приведены график и таблица одиночного испытания до 2,8 и 3,0 В. Полный заряд и фактическая отсечка заменили фиксированный бюджет 85% энергии.</div><h3>Рейтинг по энергии при 20 А до 3,0 В</h3><p>Ранжирование по отдаваемой энергии одиночного элемента. Это не рейтинг готовых блоков: масса, охлаждение, лимит тока и цена учитываются отдельно в заключении.</p><div class="table-wrap"><table><thead><tr><th>Место</th><th>Модель / версия</th><th>≈Wh</th><th>≈Ah</th><th>Tmax, °C</th><th>ΔT, °C</th></tr></thead><tbody>{rankrows}</tbody></table></div><div id="thermal-audit" class="callout"><h3>Проверка модели «Нагрев»</h3><p>Для сравнения прежнее уравнение C·dT/dt = I²R − G·(T−25) воспроизведено при том же постоянном токе до конца наблюдаемого участка, без снижения мощности контроллером. Приняты c=1000 Дж/(кг·К), прежний DCIR и прежний множитель сопротивления на низком SOC. G=5/416 и 20/416 Вт/К — равное распределение условного теплоотвода 416-ячеечного блока, не измерение стендовой ячейки.</p><p>Столбец «Подгонка стенда» показывает результат подбора только G одиночной ячейки к максимумам нескольких разрядов. Остаточные расхождения означают, что один DCIR и одна теплоотдача не описывают все токи. Из максимальной температуры нельзя независимо установить теплоёмкость, R(SOC,T), обратимое тепло и конвекцию. Подобранный G стенда не переносится на закрытый блок.</p><p><strong>Статус:</strong> модель температуры герметичного блока остаётся сценарной. В расчёт добавлены потери условной обвязки 1 мОм внутри корпуса, сценарий без теплоотвода и максимальная температура до резерва. G=5 и 20 Вт/К должны быть измерены на собранном блоке; датчик горячей внутренней ячейки остаётся необходимым.</p></div><details><summary>Таблица сопоставления измерений и прежней тепловой модели · {len(d['thermal_audit'])} точек</summary><div class="table-wrap"><table><thead><tr>''' + ''.join('<th>'+x+'</th>' for x in ['Модель / версия','I, А','Измерено, °C','ΔT, °C','Длительность, мин','G=5/416, °C','G=20/416, °C','Подгонка стенда, °C','Остаток, °C']) + f'''</tr></thead><tbody>{auditrows}</tbody></table></div></details><details id="rating-21700"><summary>Новый рейтинг Battery Mooch · 21700 · 27.09.2026</summary><p>Новый исходный рейтинг заменяет прежнюю сводную таблицу. E-Scores относятся к 2,8 В. Предсерия Tenpower 60XG и ZG13 показаны отдельно; в оригинале массовое производство ZG13 отмечено вопросом. Автор просит обновить таблицу до 27.03.2027.</p><a href="assets/mooch-21700-2026-09-27.jpg" target="_blank"><img loading="lazy" src="assets/mooch-21700-2026-09-27.jpg" alt="Рейтинг Battery Mooch 21700 от 27 сентября 2026" style="width:100%;height:auto"></a></details></div></section><section class="soft section" id="alibaba"><div class="wrap"><p class="eyebrow">Предложение продавца · {q['date']} · USD</p><h2>Цены Alibaba: отдельные предложения</h2><p>{esc(q['seller'])}. {esc(q['source'])}. {esc(q['conditions'])}</p><a href="alibaba_quotes_2026-10-01.csv">CSV: цены и статусы</a><div class="table-wrap"><table><thead><tr><th>Модель продавца</th><th>USD/шт.</th><th>Предложение / продавец</th><th>Дата</th><th>Статус</th><th>416 шт., USD</th><th>832 шт., USD</th><th>Идентичность и ограничения</th></tr></thead><tbody>{quotes}</tbody></table></div><p>Числа 416/832 — стоимость наборов для одного/двух 26S16P при неизменной цене за штуку. Для ещё не подтверждённых моделей это не доказанная компоновка. Ampace JP50, Linkdata 50P, Vapcell T60/Q65 и Yichuan 50PL сохраняются как предложения без подмены характеристиками других ячеек.</p></div></section>'''
if __name__=='__main__':exports()
