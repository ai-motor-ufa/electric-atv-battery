"""Build traceable photo transcription and a partial forum extraction; never fill missing tests."""
import csv,json,re,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'dist'; OUT.mkdir(exist_ok=True)
photo=[]
for row in csv.DictReader((ROOT/'mooch_photo.psv').open(),delimiter='|'):
    assert None not in row, row
    for key in row:
        if key not in ['model','test_date_raw','note']:
            row[key]=float(row[key]) if row[key] else None
    row['test_date']=datetime.datetime.strptime(row['test_date_raw'],'%m/%d/%y').date().isoformat()
    row['source']='IMG_3419.jpeg, Battery Mooch, 2026-08-11'
    row['source_kind']='Фото'
    row['cutoff_energy_V']=2.8
    row['capacity_basis']='rated_mAh' if row['rated_mAh'] else 'tested_mAh (rated неизвестна)'
    assert (row['rated_mAh'] or row['tested_mAh'])>4000
    photo.append(row)
harvest_path=ROOT/'research_input'/'ecf_tests_2026-09-21.json'
harvest=json.loads(harvest_path.read_text()) if harvest_path.exists() else []
links=([{'url':x['url'],'title':x.get('title') or x['url'],'thread_id':x.get('thread_id'),
         'capacity_mah':x.get('capacity_mah'),'manufacturer':x.get('manufacturer'),
         'model':x.get('model'),'publication_date':x.get('publication_date'),
         'status':x.get('status'),'dcir_mohm_samples':x.get('dcir_mohm_samples') or [],
         'verdict_flags':x.get('verdict_flags') or []} for x in harvest]
       if harvest else json.loads((ROOT/'forum_links.json').read_text()))
reviewed=json.loads((ROOT/'forum_reviewed.json').read_text())
selected=json.loads((ROOT/'harvested_cells.json').read_text()) if (ROOT/'harvested_cells.json').exists() else {'models':{}}
selected_by_url={m.get('market',{}).get('ecf_url'):m for m in selected['models'].values() if m.get('market',{}).get('ecf_url')}
for rec in reviewed:
    if rec.get('url') and not any(x['url']==rec['url'] for x in links):links.append({'url':rec['url'],'title':rec['title']})
forum=[]
for rec in links:
    r={'title':rec['title'],'url':rec['url'],'source_kind':'Форум','accessed':'2026-09-21'}
    cap=rec.get('capacity_mah')
    match=re.search(r'(\d{4})mAh',rec['title'],re.I)
    r['rated_mAh']=int(cap or (match.group(1) if match else 0)) or None
    r['model']=(' '.join(x for x in [rec.get('manufacturer'),rec.get('model')] if x)
                or re.sub(r'^Bench (?:Re)?[Tt]est Results:\s*','',rec['title']).split(' - ')[0])
    r['status']='Текст статьи прочитан' if rec.get('status')=='manual_html_extracted' else 'Только заголовок; текст не извлечён'
    r['publication_date']=rec.get('publication_date')
    r['date']=(rec.get('publication_date') or '')[:10] or None
    if rec.get('dcir_mohm_samples'):
        r['DCIR_mOhm']=round(sum(rec['dcir_mohm_samples'])/len(rec['dcir_mohm_samples']),3)
        r['dc1_mOhm']=rec['dcir_mohm_samples'][0]
        r['dc2_mOhm']=rec['dcir_mohm_samples'][-1] if len(rec['dcir_mohm_samples'])>1 else rec['dcir_mohm_samples'][0]
    selected_model=selected_by_url.get(rec['url'])
    if selected_model:
        r['estimated_CDR_A']=selected_model.get('continuous')
        r['rated_TL_A']=selected_model.get('conditional_current')
    if rec.get('verdict_flags'):
        r['note']='; '.join(rec['verdict_flags'])
    found=next((x for x in reviewed if '.'+x['thread']+'/' in rec['url']),None)
    if found:
        r.update({k:v for k,v in found.items() if k not in ['thread','title','url']})
        r['status']='Текст статьи прочитан'
    forum.append(r)
# Exact model/edition matching, explicitly reviewed; no fuzzy joins.
matches={'Tenpower 50XG':'992040','Tenpower 50SG':'995125','Tenpower 60XG':'994796','Linkdata 55P':'995029','Linkdata 60P':'994389','Linkdata 65P':'994761','BAK 65E':'993668','BAK 50D2':'994042','BAK 45D':'988135','Reliance RS50 (CCC logo, batch G3E)':'994194','Reliance RS60 (direct from Reliance)':'994495','Reliance RH60 (regular top contact, small spiral)':'993997','FEB 21700G (68E)':'993807','Great Power (GPHN) 50Q':'994348','Amprius INR21700/50Q (5000Q?)':'993503','Amprius INR21700/65 (SA112)':'993201','Ampace JP50P1':'993063','EVE 50PL (CCC logo)':'992920','BTCAP 42P':'992208','EVE 50E (CCC logo)':'992147','LG H51T':'992064','LG M58T':'990859','Lishen LR2170SK':'990568','EVE 58E':'990414','Samsung 45T (CC4503F101 Ver C)':'989513','Samsung 50S2':'988832','Samsung 53G':'987143','Molicel P50B (2024-dated)':'988690','Molicel P45B (2024-dated)':'988596','LG M50LT':'979634'}
for r in photo:
    f=next((f for f in forum if '.'+matches.get(r['model'],'UNMATCHED')+'/' in f['url']),None)
    r['url']=f['url'] if f else ''
    r['article_status']=f['status'] if f else 'Ссылка на точную версию не установлена'
combined=list(photo)
for r in forum:
    if r['model'] in ['Linkdata 50T','Great Power 60Q']:
        combined.append({'model':r['model'],'rated_mAh':r['rated_mAh'],'tested_mAh':None,'estimated_CDR_A':r['estimated_CDR_A'],'DCIR_mOhm':round((r['dc1_mOhm']+r['dc2_mOhm'])/2,3),'source_kind':'Форум','test_date':None,'publication_date':r['date'],'source':r['url'],'url':r['url'],'note':r['note'],'article_status':r['status']})
method=[
 ['Охват',f'41 строка фото с ёмкостью строго более 4000 мА·ч и {len(forum)} тем форума. Полный текст структурирован у {sum(r["status"]=="Текст статьи прочитан" for r in forum)} статей; три записи остались ссылками без извлечения текста.'],
 ['Дата','Фото обновлено 11.08.2026; страницы форума сохранены и обработаны 21.09.2026. Дата испытания с фото не равна дате публикации статьи.'],
 ['Отбор','По Rated mAh >4000; при неизвестном Rated — Tested mAh >4000 (LG H50). 4000 мА·ч исключены, в том числе строка P42A как напечатано на фото.'],
 ['Ёмкость','Tested mAh с фото сохранена буквально. Это не всегда точный результат отдельного образца: статья может приводить более точные значения.'],
 ['E-Scores','Энергия в Вт·ч при указанном токе до 2.80 В; пустая ячейка означает отсутствие теста, не ноль. Не интерполировать отсутствующие 15/50 А.'],
 ['Токи','Rated CDR/TL — номинал/температурно ограниченный ток из фото. Estimated CDR/TL — оценка Mooch. TL не является длительным током без контроля температуры.'],
 ['DCIR','Mooch измеряет начальную просадку при полном заряде 4.20 В. Это не эквивалент паспортному DCIR при другом SOC/длительности импульса.'],
 ['Версии','Предсерия, CCC, год и партия сохранены. LG H51 ≠ H51T, Samsung 50S ≠ 50S2. Значения разных версий не усредняются.'],
 ['Неясная строка Samsung','На фото Samsung 58E / CC4593F101 / 5499 мА·ч. На форуме найдена 55E / CC5493F101 / 5490 мА·ч. Автоматическое объединение запрещено.'],
 ['Доступность',f'Структурированные данные извлечены из {sum(r["status"]=="Текст статьи прочитан" for r in forum)} статей; {sum(r["status"]!="Текст статьи прочитан" for r in forum)} записи содержат только заголовок и ссылку. Парсинг не подтверждает наличие товара в продаже.'],
 ['Перенос в сборку','Результаты одиночных ячеек не подтверждают нагрев герметичного блока. Рекомендации по покупке требуют проверки партии и паспорта.'],
 ['Автор','Испытания Battery Mooch. Числа фото предоставлены пользователем. Пометка исходной таблицы: не распространять после 11.02.2027 без обновления.']
]
payload={'date':'2026-09-21','photo_date':'2026-08-11','photo':photo,'forum':forum,'combined':combined,'method':method}
(OUT/'mooch_data.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2))
def write_csv(name,items):
    keys=list(dict.fromkeys(k for r in items for k in r))
    with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys,delimiter=';',lineterminator='\n');w.writeheader();w.writerows(items)
write_csv('mooch_21700_photo.csv',photo)
write_csv('mooch_21700_forum.csv',forum)
write_csv('mooch_21700_comparison.csv',combined)
print({'photo_rows':len(photo),'forum_threads':len(forum),'full_text_articles':sum(r['status']=='Текст статьи прочитан' for r in forum),'comparison_rows':len(combined)})
