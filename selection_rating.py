"""Transparent project procurement rankings, shared by HTML and PDF."""
from procurement import best_offer
from adaptive_model import cell_limit, ETA, AUX

WEIGHTS=dict(cost=35,energy=25,heat=15,power=15,mass=5,evidence=5)
NOTES={
 'gp50q':('Баланс цены и энергии','При почти минимальной цене выдаёт больше энергии, чем EVE 50PL в принятом сценарии. Токоотдача позволяет рассматривать отдельный блок для 15/30 кВт.','Независимые данные относятся к испытанным образцам; перед закупкой проверить точное исполнение и партию.'),
 'eve50pl':('Минимальная цена комплекта','Самая низкая известная цена Alibaba; небольшой расчётный вес ячеек. Подходит для бюджетного прототипа с контролем температуры.','Редакции расходятся по массе и току: согласовать 68/72 г, паспорт и маркировку; тепловые потери выше BAK 50D2.'),
 'bak50d2':('Приоритет для силового прототипа','Низкое сопротивление и небольшие расчётные потери при частых разгонах. Цена выше EVE и Great Power, но запас по току полезен при работе от отдельного блока.','Паспорт и независимый тест не гарантируют одинаковые характеристики закупаемой партии; проверить образцы.'),
 'rs50':('Лучший запас по массе','Самые лёгкие ячейки среди этой пятёрки; остаётся больше массы на корпус, коммутацию и охлаждение. Выданная энергия близка к BAK 50D2.','Нужны проверка партии и ведомость массы готового блока: верх оценки всё ещё может превышать 40 кг.'),
 't50xg':('Повторные запросы мощности','В принятом режиме частых разгонов мала доля времени со снижением запроса. Есть паспорт и независимые данные; цена умеренная.','Выданная энергия ниже BAK и Great Power, потери выше; масса готового блока также требует проверки.'),
 'jp50p1':('Силовой резерв','Хорошее сохранение мощности в принятом режиме частых разгонов.','Дороже основной пятёрки; JP50 и JP50P1 нельзя подменять, партия и исполнение требуют подтверждения.'),
 'tp60xg':('Перспективный вариант 6 А·ч','Большая выданная энергия и низкие расчётные потери делают вариант интересным для увеличения запаса энергии.','Тестируется предсерия июня. Предложение Alibaba не подтверждает эту версию или ZG13: цена и характеристики вместе условны.'),
 'link65p':('Максимум энергии','Наибольшая выданная энергия в рассматриваемом умеренном сценарии.','Высокая цена и меньший принятый длительный ток: покупать ради энергии, после проверки партии и ограничений разгона.'),
 'link60p':('Энергия с меньшей массой','Энергия выше большинства вариантов 5 А·ч, при небольшой расчётной массе.','Цена заметно выше бюджетных моделей; независимые характеристики переносятся на поставку условно.'),
 'rs60':('Резерв по энергии без закупочной цены','Хороший результат по выданной энергии среди вариантов 6 А·ч.','Цена Alibaba неизвестна: в обобщённый рейтинг закупки не включён до получения предложения.'),
 's50s':('Бюджетный контрольный вариант','Известная низкая цена позволяет использовать как сравнительный образец.','Принятый длительный ток 20 А не обеспечивает 30 кВт при номинальном напряжении одного блока; для основного проекта предпочтительнее силовые варианты.')
}
METHOD='Сравнение для двух независимых блоков 26S16P, по одному на двигатель 15/30 кВт. Начало 100% заряда и 25 °C; отсечка 2,9 В для ячеек с распределённым токосъёмом, для остальных — условия основной модели; теплоотвод 5 Вт/К на блок. Энергия — умеренная поездка; потери и сохранение мощности — частые разгоны. Цена — лучшее предложение Alibaba для точной модели, только 832 ячейки, без доставки, корпуса и обвязки.'
FORMULA='Оценка до 100 баллов: 35 × минимальная цена / цена; 25 × выданная энергия / максимум; 15 × минимальные тепловые потери / потери; 15 × доля времени без снижения запроса; 5 × минимальная масса ячеек / масса; 5 × полнота данных. Сравнение относительно кандидатов с ценой и расчётом. Полнота данных: 1 для совпадающих кривых, 0,5 для общей зависимости напряжения, 0,75 для смешанных редакций EVE 50PL, 0,25 для Tenpower 60XG с неподтверждённой версией предложения. Это выбранные приоритеты проекта, а не отраслевой стандарт или вероятность безопасности.'

def calculate(data):
 entries=[]
 for r in data['rows']:
  if r['s']!=26 or r['p']!=16:continue
  m=data['models'][r['model']];o=best_offer(m.get('market',{}).get('alibaba',{}).get('offers',[]))
  s=r['simulations']['1_5_mixed_2.9'];a=r['simulations']['1_5_active_2.9']
  cap=cell_limit(r['model'],25)
  nominal_shaft=None if cap is None else (cap*r['p']*r['voltage']/1000-AUX)*ETA
  issues=[]
  if o is None:issues.append('Нет цены Alibaba')
  if not(s and a):issues.append('Недостаточно данных для расчёта')
  if nominal_shaft is None or nominal_shaft<30:issues.append('Нет подтверждённой токоотдачи для 30 кВт при номинальном напряжении')
  evidence=.25 if r['model']=='tp60xg' else .75 if r['model']=='eve50pl' else 1. if 'Оцифрованные' in r['voltage_basis'] else .5
  role,why,risk=NOTES.get(r['model'],('Дополнительный вариант','Характеристики приведены в таблице исходных данных.','Проверить цену, паспорт и применимость для отдельного блока.'))
  entries.append(dict(id=r['id'],model=r['model'],name=r['cell_name'],cost_block=None if o is None else o['price']*r['n'],cost_pair=None if o is None else o['price']*r['n']*2,unit_price=None if o is None else o['price'],price_date=None if o is None else o['observed_at'],price_seller=None if o is None else o['seller'],nominal_pair=2*r['energy'],output_pair=None if s is None else 2*s['output_kwh'],wmtc_equiv=None if s is None else 2*s['wmtc_equiv'],utility_equiv=None if s is None else 2*s['utility_equiv'],heat_W_per_block=None if a is None else a['heat_enclosed_mean'],active_peak_C=None if a is None else a['t_peak'],power_fraction=None if a is None else 1-a['limited_pct']/100,mass_cells=r['mass'],finished_mass=r['finished'],evidence=evidence,rated_current_A=cap,nominal_shaft_kw=nominal_shaft,issues=issues,role=role,why=why,risk=risk,score=None,eligible=not issues))
 eligible=[e for e in entries if e['eligible']]
 lo_cost=min(e['cost_pair'] for e in eligible);hi_energy=max(e['output_pair'] for e in eligible);lo_heat=min(e['heat_W_per_block'] for e in eligible);lo_mass=min(e['mass_cells'] for e in eligible)
 for e in eligible:
  e['components']=dict(cost=WEIGHTS['cost']*lo_cost/e['cost_pair'],energy=WEIGHTS['energy']*e['output_pair']/hi_energy,heat=WEIGHTS['heat']*lo_heat/e['heat_W_per_block'],power=WEIGHTS['power']*e['power_fraction'],mass=WEIGHTS['mass']*lo_mass/e['mass_cells'],evidence=WEIGHTS['evidence']*e['evidence'])
  e['score']=sum(e['components'].values())
 overall=sorted(eligible,key=lambda e:(-e['score'],e['cost_pair']))
 range_order=sorted([e for e in entries if e['output_pair'] is not None],key=lambda e:-e['output_pair'])
 price_order=sorted([e for e in entries if e['cost_pair'] is not None],key=lambda e:e['cost_pair'])
 return dict(method=METHOD,formula=FORMULA,weights=WEIGHTS,entries=entries,orders=dict(overall=[e['id'] for e in overall],range=[e['id'] for e in range_order],price=[e['id'] for e in price_order]),top_five=[e['id'] for e in overall[:5]])

def html_section(rating,esc,num,photos):
 from manufacturer_context import html_context
 def image(key):
  p=photos.get(key)
  if not p:return ""
  return f'<figure class="final-photo"><a href="{esc(p["file"])}" target="_blank" rel="noopener"><img src="{esc(p["file"])}" alt="{esc(p.get("display_name",key))}: {esc(p["caption"])}" loading="lazy"></a></figure>'
 by={e['id']:e for e in rating['entries']}
 cards=''.join(f'<article class="final-cell"><p class="eyebrow">{i+1} · {esc(e["role"])}</p><h3>{esc(e["name"])}</h3>{image(e["model"])}<p><strong>{num(e["cost_pair"],0)} $ за 832 ячейки</strong> · {num(e["output_pair"],2)} кВт·ч выдано двумя блоками.</p><p>{esc(e["why"])}</p><p class="note">{esc(e["risk"])}</p>{html_context(e["model"],esc)}</article>' for i,id in enumerate(rating['top_five']) for e in [by[id]])
 return f'''<section class="section" id="choice"><div class="wrap"><p class="eyebrow">Выбор ячеек для проекта</p><h2>Цена, энергия и запас по мощности</h2><p class="note">{esc(rating['method'])}</p><div class="segmented" aria-label="Рейтинг ячеек"><button data-ranking="overall" aria-pressed="true">Баланс цены и характеристик</button><button data-ranking="range" aria-pressed="false">Максимум выданной энергии</button><button data-ranking="price" aria-pressed="false">Минимальная цена комплекта</button></div><p id="rating-note" class="note"></p><div class="table-wrap"><table><thead id="rating-head"></thead><tbody id="rating-body"></tbody></table></div><details><summary>Как получен обобщённый рейтинг</summary><p>{esc(rating['formula'])}</p><p>В основной рейтинг включены только варианты с ценой, численной моделью и расчётной токоотдачей для 30 кВт при номинальном напряжении отдельного блока. Эту проверку нельзя считать подтверждением полной мощности до конца разряда. <a href="selection_ratings.json">Исходные значения и составляющие оценки</a></p></details><details><summary>Варианты без обобщённой оценки</summary><ul>{''.join('<li>'+esc(e['name'])+': '+esc('; '.join(e['issues']))+'</li>' for e in rating['entries'] if not e['eligible'])}</ul><p>Пакетные варианты Farasis сохранены в каталоге. Без применимой цены, сопротивления и токовой карты их нельзя обоснованно ранжировать для этой закупки. Рейтинг здесь относится к двум блокам 26S16P.</p></details><h3 style="margin-top:36px">Пять наиболее перспективных вариантов</h3><div class="final-grid">{cards}</div><p class="note">Начать с сравнительной проверки образцов этой пятёрки. Great Power и EVE интересны ценой, BAK — потерями, Reliance — массой, Tenpower — сохранением мощности. Linkdata 65P остаётся лидером по энергии, но высокая цена снижает привлекательность общей закупки. Tenpower 60XG — перспективный резерв после подтверждения серийной версии. Цена отсутствующих предложений не считается нулевой.</p></div></section>'''
