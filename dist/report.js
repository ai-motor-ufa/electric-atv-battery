'use strict';
const DATA=JSON.parse(document.getElementById('report-data').textContent);
const ROWS=DATA.rows, MODELS=DATA.models, PHOTOS=DATA.photos;
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/Pouch|pouch/g,'пакетный').replace(/tabless|full-tab/g,'с распределённым токосъёмом').replace(/Datasheet/g,'Паспорт').replace(/pre-production/g,'предсерия').replace(/no CCC test/g,'испытание без маркировки CCC').replace(/SOC/g,'заряд').replace(/CAD/g,'трёхмерная компоновка').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num=(x,d=1)=>x==null?'—':Number(x).toLocaleString('ru-RU',{minimumFractionDigits:d,maximumFractionDigits:d});
const dim=a=>a.map(v=>num(v,Number.isInteger(v)?0:2)).join('×');
const photo=(r,caption=true)=>{const p=PHOTOS[r.model];const url=p?`${p.file}?v=${(p.original_sha256||'').slice(0,12)}`:'';return p?`<a href="${esc(url)}" target="_blank" rel="noopener"><img src="${esc(url)}" alt="${esc(p.display_name||r.cell_name)}: ${esc(p.caption)}" loading="lazy"></a>${p.caption&&(caption||p.related_model)?`<small>${esc(p.caption)}</small>`:''}`:'<small>Снимка модели в присланном архиве нет</small>'};
const state={metric:'range',blocks:2,motors:2,cutoff:'2.9',rangeMode:'wmtc',rangeBasis:'nominal',ranking:'overall',profile:'mixed',cooling:5,selection:'all',view:'energy',sort:null,ascending:true};
const getSim=r=>{const raw=r.simulations[`${state.motors===2?1:state.blocks}_${state.cooling}_${state.profile}_${state.cutoff}`];if(!raw||state.motors===1)return raw;return {...raw,output_kwh:2*raw.output_kwh,chemical_kwh:2*raw.chemical_kwh,heat_kj:2*raw.heat_kj,line_heat_kj:2*raw.line_heat_kj,wmtc_equiv:2*raw.wmtc_equiv,utility_equiv:2*raw.utility_equiv,rough_range:raw.rough_range.map(v=>2*v),normal_output_kwh:2*raw.normal_output_kwh,turtle_output_kwh:2*raw.turtle_output_kwh,mean_power:2*raw.mean_power,trace:(raw.trace||[]).map(t=>({...t,power:2*t.power}))};};
const visibleRows=()=>state.motors===2?ROWS.filter(r=>r.s===26&&r.p===16):ROWS;
const blockCount=()=>state.motors===2?2:state.blocks;
const rangeValue=s=>state.rangeMode==='wmtc'?s.wmtc_equiv:s.utility_equiv;
const nominalRange=r=>blockCount()*(state.rangeMode==='wmtc'?r.nominal_wmtc:r.nominal_utility);
const sources=Object.fromEntries(DATA.sources.map(s=>[s.id,s]));
const sourceLink=id=>sources[id]?.url?`<a href="${esc(sources[id].url)}" target="_blank" rel="noopener">${esc(id)} ↗</a>`:esc(id);
const metricValue=(r,metric)=>{const s=getSim(r);return metric==='range'?(state.rangeBasis==='nominal'?nominalRange(r):(s?rangeValue(s):null)):metric==='runtime'?(s?s.minutes:null):(s?s.t_peak:null);};
const availabilityLabel=s=>({in_stock:'в наличии',out_of_stock:'нет в наличии',page_allows_add_to_cart:'доступно к заказу',not_found_on_nkon:'точная модель на NKON не найдена'}[s]||(s?.startsWith('expected_')?`ожидается ${s.slice(9).split('-').reverse().join('.')}`:s||'статус не указан'));
const priceAt=(nk,qty)=>{
 if(!nk||nk.price==null)return null;
 let unit=nk.price;
 for(const tier of [...(nk.quantity_tiers||[])].sort((a,b)=>a.min_quantity-b.min_quantity))if(qty>=tier.min_quantity)unit=tier.unit_price;
 return {unit,total:unit*qty};
};
function marketInfo(m){
 const market=m.market;if(!market)return '<span class="unknown">Нет данных в выгрузке 21.09.2026</span>';
 const links=[];
 if(market.cell_saviors_url)links.push(`<a href="${esc(market.cell_saviors_url)}" target="_blank" rel="noopener">CellSaviors ↗</a>`);
 if(market.ecf_url)links.push(`<a href="${esc(market.ecf_url)}" target="_blank" rel="noopener">ECF ↗</a>`);
 if(market.datasheet?.url)links.push(`<a href="${esc(market.datasheet.url)}" target="_blank" rel="noopener">Паспорт ↗</a>`);
 const nk=market.nkon;
 if(nk){
  const price=nk.price==null?'цена не найдена':`${num(nk.price,2)} ${esc(nk.currency||'EUR')}`;
  const title=nk.url?`<a href="${esc(nk.url)}" target="_blank" rel="noopener">NKON: ${price} ↗</a>`:`<span class="unknown">NKON: ${price}</span>`;
  const tiers=(nk.quantity_tiers||[]).map(t=>`от ${t.min_quantity}: ${num(t.unit_price,2)} ${esc(t.currency||nk.currency||'EUR')}`).join(' · ');
  links.push(`${title}<span class="sub">${esc(availabilityLabel(nk.availability))} · снимок ${esc(nk.observed_at||'')}</span>${tiers?`<span class="sub">${tiers}</span>`:''}${nk.note?`<span class="sub">${esc(nk.note)}</span>`:''}`);
 }
 if(market.alibaba)links.push(alibabaInfo(m,416));
 return links.join('<br>')||'<span class="unknown">Ссылки отсутствуют</span>';
}
function marketCost(r){
 const nk=MODELS[r.model].market?.nkon,one=priceAt(nk,r.n),two=priceAt(nk,2*r.n);
 if(!one)return `<span class="unknown">${nk?.availability==='not_found_on_nkon'?'Карточка точной модели не найдена':'Нет цены NKON'}</span>`;
 return `${num(one.total,2)} €<span class="sub">${num(one.unit,2)} €/яч. · ${r.n} шт.</span><span class="sub">Два блока: ${num(two.total,2)} € · ${num(two.unit,2)} €/яч.</span><span class="sub">${esc(availabilityLabel(nk.availability))}; без доставки</span>`;
}

function alibabaInfo(m,qty){
 const offers=m.market?.alibaba?.offers||[],o=offers.filter(o=>o.price!=null&&o.availability!=='out_of_stock').sort((a,b)=>a.price-b.price)[0];
 if(!o)return '<span class="unknown">Нет подтверждаемой цены Alibaba</span>';
 return `<strong>${num(o.price*qty,2)} $</strong><span class="sub">${num(o.price,2)} $/яч. · ${qty} шт.</span><span class="sub">${esc(o.seller)} · ${esc(o.observed_at)}; наличие уточнить</span>`;
}
function sortedRows(rows,key,ascending=true){
 if(!key||key==='photo'||key==='name')return [...rows].sort((a,b)=>a.order-b.order);
 const c=columns().find(x=>x.key===key);if(!c)return [...rows];
 return [...rows].sort((a,b)=>{const x=c.sort(a),y=c.sort(b);if(x==null)return y==null?a.order-b.order:1;if(y==null)return -1;const v=typeof x==='number'?x-y:String(x).localeCompare(String(y),'ru',{numeric:true});return (ascending?1:-1)*v||a.order-b.order;});
}
function setMetric(metric){state.metric=metric;if(state.view==='modes'){state.sort=metric;state.ascending=metric==='heat';}document.querySelectorAll('[data-metric]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.metric===metric)));render();}
function renderChart(){
 const candidates=visibleRows().filter(r=>r.candidate).sort((a,b)=>{const x=metricValue(a,state.metric),y=metricValue(b,state.metric);if(x==null)return y==null?a.order-b.order:1;if(y==null)return -1;return (state.metric==='heat'?x-y:y-x)||a.order-b.order;});
 const rows=state.selection==='all'?candidates:visibleRows().filter(r=>r.id===state.selection);
 const title={range:(state.rangeMode==='wmtc'?'Энергетический эквивалент WMTC':'Энергетический эквивалент средней эксплуатации')+' · '+(state.rangeBasis==='nominal'?'номинальная энергия':'выданная энергия сценария'),runtime:'Время до ограничения и до завершения',heat:'Максимальная средняя температура ячеек, °C'}[state.metric];
 $('chart-title').textContent=title;$('back-all').hidden=state.selection==='all';
 $('chart-note').textContent=state.metric==='range'?`BRP: 8,9 кВт·ч и ${state.rangeMode==='wmtc'?'80 км по WMTC':'50 км в средней эксплуатации'}. ${state.rangeBasis==='nominal'?'Сравнивается номинальная энергия обеих батарей: одинаковая основа. Потери и ограничения выбранного режима здесь не вычитаются.':'Для сборок взята выданная энергия выбранного сценария. Полезная энергия BRP неизвестна: такое сравнение не подтверждает преимущество его батареи.'} Это энергетический эквивалент, а не расчёт прохождения цикла WMTC или обещание пробега. Масса квадроциклов принята равной: 398 кг. ${state.motors===2?'Два независимых блока: энергия суммируется; перенос расхода BRP на два двигателя требует проверки.':''}`:state.metric==='heat'?'Средняя температура ячеек; местные горячие точки не рассчитаны. Теплоотвод выбран условно для каждого блока.':'Цикл 100 с: заданные нагрузки идут последовательно. После первого снижения запрос сохраняется, но доступная тяга может уменьшиться. Время работы относится к выбранному сценарию.';
 $('chart-legend').innerHTML=state.metric==='runtime'?'<span>Без снижения запроса</span><span class="rest">После снижения, до завершения</span>':state.metric==='range'?`<span>${state.rangeBasis==='nominal'?'Номинальная энергия батарей':'Выданная энергия сценария'}</span><span style="color:#aa575d">BRP: заявленный пробег</span>`:'<span>Расчётная средняя температура</span><span class="uncertain">Данных для расчёта нет</span>';
 const vals=rows.map(r=>metricValue(r,state.metric));
 const max=Math.max(...vals.filter(x=>x!=null),state.metric==='range'?(state.rangeMode==='wmtc'?80:50):1)*1.07;
 $('bars').innerHTML=rows.map((r,i)=>{const s=getSim(r),v=vals[i],uncertain=!s;let bar='';
  if(v!=null){if(state.metric==='runtime')bar=`<i class="bar-total" style="width:${v/max*100}%"></i><i class="bar-full" style="width:${s.full_minutes/max*100}%"></i>`;else bar=`<i class="bar-fill ${uncertain?'estimate':''}" style="width:${v/max*100}%"></i>`;}
  const label=state.metric==='runtime'&&s?`${num(s.full_minutes,0)} / ${num(v,0)} <small>мин: полный / всего</small>`:v==null?'—<small>нет данных</small>':state.metric==='range'?`${num(v,1)} км-экв.<small>${state.rangeBasis==='nominal'?num(r.energy*blockCount(),2)+' кВт·ч номинально':num(s.output_kwh,2)+' кВт·ч выдано'}${!s?' · нагрузка не проверена':''}</small>`:`${num(v,0)} °C<small>${num(s.heat_enclosed_mean,0)} Вт / блок</small>`;
  return `<button class="bar-row" data-select="${r.id}" aria-label="Подробно: ${esc(r.name)}"><span class="bar-label">${esc(r.cell_name)}<small>${r.s}S${r.p}P · ${num(r.energy,2)} кВт·ч/блок${r.dc_basis.startsWith('Независимый')?' · DCIR теста':''}</small></span><span class="bar-track">${bar}</span><span class="bar-value">${label}</span></button>`;}).join('');
 if(state.metric==='range'){const v=state.rangeMode==='wmtc'?80:50;$('bars').insertAdjacentHTML('afterbegin',`<div class="bar-row brp-reference"><span class="bar-label">BRP Outlander Electric 2026<small>8,9 кВт·ч · 398 кг · паспортный ориентир</small></span><span class="bar-track"><i class="bar-fill" style="background:#ed9296;width:${v/max*100}%"></i></span><span class="bar-value">${v} км<small>Заявлено BRP</small></span></div>`);}
 $('axis').innerHTML=`<span>0</span><span>${num(max/2,0)}</span><span>${num(max,0)} ${state.metric==='range'?'км':state.metric==='runtime'?'мин':'°C'}</span>`;
 $('detail').hidden=state.selection==='all';if(rows.length===1)renderDetail(rows[0]);
}
function plot(trace,key,label,color,limit){
 const w=420,h=210,left=44,right=12,top=12,bottom=34,xmax=Math.max(trace.at(-1).minute,1);
 const ymax=key==='soc'?100:key==='power'?(state.motors===2?64:32):Math.ceil(Math.max(60,...trace.map(t=>t[key]))/10)*10;
 const x=t=>left+t/xmax*(w-left-right),y=v=>h-bottom-v/ymax*(h-top-bottom);
 let svg=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(label)}">`;
 for(let j=0;j<=3;j++){const v=ymax*j/3;svg+=`<line x1="${left}" y1="${y(v)}" x2="${w-right}" y2="${y(v)}" stroke="#dcdce1"/><text x="${left-8}" y="${y(v)+4}" text-anchor="end" font-size="13" fill="#626269">${num(v,0)}</text>`;}
 if(limit!=null)svg+=`<line x1="${left}" y1="${y(limit)}" x2="${w-right}" y2="${y(limit)}" stroke="#ab6509" stroke-dasharray="4 5"/>`;
 svg+=`<polyline points="${trace.map(t=>`${x(t.minute).toFixed(1)},${y(t[key]).toFixed(1)}`).join(' ')}" fill="none" stroke="${color}" stroke-width="3" stroke-linejoin="round"/>`;
 for(const t of [0,xmax/2,xmax])svg+=`<text x="${x(t)}" y="${h-10}" text-anchor="middle" fill="#626269" font-size="13">${num(t,0)}</text>`;
 return svg+'</svg>';
}
const traceCache={},tracePending={};
function dischargeTests(r){const keys=r.model==='h51'?['h51t']:r.model==='p50b'?['p50b','p50b_sample']:[r.model];const cards=keys.map(k=>DATA.discharge_cards?.[k]).filter(Boolean);return cards.length?`<div class="selected-tests"><h3>Разрядное испытание Mooch</h3>${cards.join('')}</div>`:'<p class="note">В предоставленном архиве нет применимого графика разряда этой модели.</p>';}
function renderDetail(r){const s=getSim(r),m=MODELS[r.model];
 if(s&&(!s.trace||!s.trace.length)){
  if(traceCache[r.id]){for(const [key,points] of Object.entries(traceCache[r.id]))if(r.simulations[key])r.simulations[key].trace=points.map(t=>({minute:t[0],soc:t[1],temp:t[2],power:t[3],turtle:t[4],group_voltage:t[5]}));renderDetail(r);return;}
  $('detail').innerHTML='<p>Загрузка графиков выбранной сборки…</p>';
  if(!tracePending[r.id])tracePending[r.id]=fetch(`traces/${r.id}.json?v=20261004-r18`).then(v=>{if(!v.ok)throw Error('Нет графиков');return v.json();}).then(v=>{traceCache[r.id]=v;delete tracePending[r.id];if(state.selection===r.id)renderDetail(r);}).catch(()=>{$('detail').innerHTML='<p>Графики не загрузились. Перечисленные результаты доступны в таблице.</p>';delete tracePending[r.id];});return;
 }

 $('detail').innerHTML=`<div class="detail-top"><figure class="cell-appearance">${photo(r,false)}</figure><div><p class="eyebrow">${esc(r.format)} · ${r.n} элементов в блоке</p><h3>${esc(r.name)}</h3><span class="muted">${num(r.finished[0])}–${num(r.finished[1])} кг · корпус ${dim(r.box)} мм</span></div></div>`;
 $('detail').innerHTML+=`<p class="note">${blockCount()} блок(а), ${state.motors} двигатель(я): номинальная энергия ${num(r.energy*blockCount(),2)} кВт·ч; номинальный эквивалент ${num(nominalRange(r),0)} км. Масса батарей вместе ${num(r.finished[0]*blockCount())}–${num(r.finished[1]*blockCount())} кг. ${s?`Выдано ${num(s.output_kwh,2)} кВт·ч; эквивалент ${num(rangeValue(s),0)} км. Черепаха при 2,9 В: 3 кВт на двигатель, остановка при 2,65 В; ${esc(s.soc_policy)}.`:''}</p>`;
 if(!s){$('detail').innerHTML+=`<div class="empty">Тепловой прогноз и время сохранения мощности не рассчитаны: ${esc(r.dc_model==null?'нет DCIR':'нет полной применимой карты тока')}. ${esc(m.note)}</div><p class="note">Номинальный энергетический эквивалент для ${blockCount()} блоков: ${num(r.energy_ceiling_wmtc*blockCount(),0)} км по индексу WMTC / ${num(r.energy_ceiling_utility*blockCount(),0)} км по рабочему индексу. Это не подтверждение допустимой нагрузки.</p>`;$('detail').innerHTML+=dischargeTests(r);return;}
 $('detail').innerHTML+=`<div class="kpis"><div class="kpi"><strong>${num(s.full_minutes)}</strong><span>мин без снижения запроса</span></div><div class="kpi"><strong>${num(s.minutes)}</strong><span>мин до завершения</span></div><div class="kpi"><strong>${num(s.utility_equiv,0)} км</strong><span>рабочий энергетический эквивалент</span></div><div class="kpi"><strong>${num(s.heat_mean,0)} Вт</strong><span>среднее тепло ячеек / блок</span></div></div>
 <div class="plots"><div class="plot"><h4>Запас заряда, %</h4>${plot(s.trace,'soc','Заряд по времени','#0071e3',10)}<p>Время, мин. Завершение по напряжению, температуре или доступной ёмкости; для пакетных ячеек сохранена предварительная карта заряда.</p></div><div class="plot"><h4>Температура ячеек, °C</h4>${plot(s.trace,'temp','Сценарная средняя температура по времени','#bc690b',45)}<p>Максимум ${num(s.t_peak,1)} °C; конец ${num(s.t_end,1)} °C. Пунктир — начало снижения потолка при 45 °C. Горячие точки не рассчитаны.</p></div><div class="plot"><h4>Фактическая мощность на валу, кВт</h4>${plot(s.trace,'power','Доступная мощность по времени','#237c55',null)}<p>Последовательные импульсы выбранного цикла; график прорежен. Для двух двигателей показана суммарная мощность.</p></div></div>
 <div class="callout"><strong>Первое ограничение:</strong> ${esc(s.first_limit)}.${s.first_soc!=null?` В модели это происходит около ${num(s.first_soc,0)}% заряда, при ${num(s.first_voltage,1)} В под нагрузкой и средней температуре ${num(s.first_temp,0)} °C.`:''} Максимальный ток одного блока в сценарии: ${num(s.max_current,0)} А / ${num(s.max_current/r.p)} А на ячейку. Завершение: ${esc(s.stop_reason)}. Выдано ${num(s.output_kwh,2)} кВт·ч; средняя мощность на валу ${num(s.mean_power,1)} кВт. Тепло всех подключённых ячеек: ${num(s.heat_kj,0)} кДж.</div>
 <p class="note">Максимальная средняя температура ${num(s.t_peak,1)} °C, конец ${num(s.t_end,1)} °C. Тепло обвязки ${num(s.line_heat_kj,0)} кДж; всё условно отнесено внутрь корпуса. <a href="#thermal-audit">Сопоставление с температурами Mooch</a>. ${esc(s.voltage_basis)}. DCIR: ${num(r.dc_model,2)} мОм/яч. · ${esc(r.dc_basis)}. В тяжёлом условном маршруте 250–400 Вт·ч/км: ${num(s.rough_range[0],0)}–${num(s.rough_range[1],0)} км. Предварительная оценка зависит от принятой карты управления; это не гарантия диапазона.</p>`;
 $('detail').innerHTML+=`<div class="callout turtle-summary"><strong>Режим «черепаха»:</strong> ${s.turtle_start_min==null?'В этом сценарии порог не достигнут.':`Включён через ${num(s.turtle_start_min)} мин при ${num(s.turtle_start_soc)}% заряда. До переключения: ${num(s.normal_minutes)} мин и ${num(s.normal_output_kwh,2)} кВт·ч. После переключения: ${num(s.turtle_minutes)} мин и ${num(s.turtle_output_kwh,2)} кВт·ч.`} Не более ${state.motors===2?6:3} кВт на валу ${state.motors===2?'двух двигателей вместе':'двигателя'}. Остановка при 2,65 В или раньше по температуре/границе измерений; неизмеренная энергия до 2,65 В не включена.</div>`;
 $('detail').innerHTML+=dischargeTests(r);
}
const col=(key,label,render,sort)=>({key,label,render,sort});
function columns(){
 const base=[col('photo','Фото ↺',r=>photo(r,false),r=>r.order),col('name','Элемент / сборка ↺',r=>`<span class="model-name">${esc(r.cell_name)}</span><span class="sub">${r.s}S${r.p}P · ${r.id}</span>`,r=>r.order),col('format','Тип',r=>esc(r.format),r=>r.format),col('brand','Производитель',r=>esc(r.manufacturer),r=>r.manufacturer)];
 if(state.view==='energy')return base.slice(0,2).concat([
 col('energy','Номинальная энергия системы',r=>`${num(r.energy*blockCount(),2)} кВт·ч<span class="sub">${num(r.energy,2)} кВт·ч / блок</span>`,r=>r.energy*blockCount()),
 col('mass','Масса батарей системы',r=>`${num(r.finished[0]*blockCount())}–${num(r.finished[1]*blockCount())} кг<span class="sub">Ячейки: ${num(r.mass*blockCount(),1)} кг</span>`,r=>r.finished[0]*blockCount()),
 col('cell-size','Размер ячейки, мм',r=>dim(MODELS[r.model].dims),r=>MODELS[r.model].dims.reduce((a,b)=>a*b,1)),
 col('alibaba-cost',`Alibaba: ячейки для ${blockCount()} блок(а)`,r=>alibabaInfo(MODELS[r.model],r.n*blockCount()),r=>{const os=MODELS[r.model].market?.alibaba?.offers||[];const ps=os.filter(o=>o.price!=null&&o.availability!=='out_of_stock').map(o=>o.price);return ps.length?Math.min(...ps)*r.n*blockCount():null;}),
 col('fit','Компоновка',r=>`<details><summary>${r.s}S${r.p}P · ${r.n} ячеек</summary>${esc(r.layout)}<br>${esc(r.fit)}<br>Корпус ${dim(r.box)} мм</details>`,r=>r.fit)]);
 if(state.view==='electrical')return base.concat([
  col('volt','Uном / Uзаряд',r=>`${num(r.voltage)} / ${num(r.vmax)} В`,r=>r.voltage),
  col('cell-current','А/яч.: 30 кВт',r=>`${num(34290.909/r.voltage/r.p)}<span class="sub">При Uном ${num(r.voltage)} В; до просадки и ограничений</span>`,r=>34290.909/r.voltage/r.p),
  col('rating','Паспорт тока',r=>rating(MODELS[r.model]),r=>MODELS[r.model].continuous??MODELS[r.model].conditional_current??MODELS[r.model].pulse??null),
  col('dc','DCIR / источник',r=>`${num(r.dc_model,2)} мОм<span class="sub">${esc(r.dc_basis)}</span>`,r=>r.dc_model),
  col('res','Ветвь / вся линия',r=>r.r_total==null?`${r.s}r / ${num(r.s/r.p,3)}r + 1 мОм`:`${num(r.r_string,2)} / ${num(r.r_total,2)} мОм`,r=>r.r_total),
  col('note','Условия и ограничения',r=>esc(MODELS[r.model].note),r=>MODELS[r.model].note),col('source','Источник',r=>sourceLink(r.source),r=>r.source)]);
 if(state.view==='modes')return base.concat([
  col('nominal-range','Номинальный эквивалент',r=>`${num(nominalRange(r),1)} км<span class="sub">Без резерва и потерь</span>`,r=>nominalRange(r)),
  col('output','Выданная энергия',r=>getSim(r)?`${num(getSim(r).output_kwh,2)} кВт·ч<span class="sub">${num(getSim(r).available_fraction*100,1)}% номинала</span>`:'—',r=>getSim(r)?.output_kwh),
  col('turtle-time','Мин в черепахе',r=>num(getSim(r)?.turtle_minutes),r=>getSim(r)?.turtle_minutes),
  col('turtle-energy','Энергия в черепахе',r=>`${num(getSim(r)?.turtle_output_kwh,2)} кВт·ч`,r=>getSim(r)?.turtle_output_kwh),
  col('end-soc','Остаток заряда при остановке',r=>getSim(r)?`${num(getSim(r).end_soc,1)}%`:'—',r=>getSim(r)?.end_soc),
  col('full','Мин без снижения',r=>num(getSim(r)?.full_minutes),r=>getSim(r)?.full_minutes),
  col('total','Мин всего',r=>num(getSim(r)?.minutes),r=>getSim(r)?.minutes),
  col('range',state.rangeMode==='wmtc'?'Эквивалент WMTC':'Средняя эксплуатация',r=>getSim(r)?`${num(rangeValue(getSim(r)),0)} км`:`—`,r=>getSim(r)?rangeValue(getSim(r)):null),
  col('utility','Рабочий эквивалент',r=>getSim(r)?`${num(getSim(r).utility_equiv,0)} км`:'—',r=>getSim(r)?.utility_equiv),
  col('heat','Максимальная температура',r=>`${num(getSim(r)?.t_peak,1)} °C`,r=>getSim(r)?.t_peak),
  col('losses','Тепловые потери / блок',r=>`${num(getSim(r)?.heat_enclosed_mean,0)} Вт`,r=>getSim(r)?.heat_enclosed_mean),
  col('temp','Температура в конце',r=>`${num(getSim(r)?.t_end,0)} °C`,r=>getSim(r)?.t_end),
  col('cause','Первое ограничение',r=>esc(getSim(r)?.first_limit??'Нужны исходные данные'),r=>getSim(r)?.first_limit??null)]);
 return base.concat([
  col('capacity','Ёмкость ячейки',r=>`${num(MODELS[r.model].ah,2)} А·ч`,r=>MODELS[r.model].ah),
  col('cellmass','Масса ячейки',r=>`${num(MODELS[r.model].kg*1000,1)} г`,r=>MODELS[r.model].kg),
  col('dims','Размер ячейки',r=>`${dim(MODELS[r.model].dims)} мм<span class="sub">${esc(MODELS[r.model].dims_label||'Габарит из источника')} ${esc(MODELS[r.model].dimension_source||'')}</span>`,r=>MODELS[r.model].dims.reduce((a,b)=>a*b,1)),
  col('chem','Химия / исполнение',r=>esc(MODELS[r.model].type),r=>MODELS[r.model].type),
  col('passport','Сопротивление в паспорте',r=>esc(MODELS[r.model].res),r=>MODELS[r.model].dc??null),
  col('rating','Ток одного элемента',r=>rating(MODELS[r.model]),r=>MODELS[r.model].continuous??MODELS[r.model].conditional_current??MODELS[r.model].pulse??null),
  col('market','Рынок и источники',r=>marketInfo(MODELS[r.model]),r=>MODELS[r.model].market?.nkon?.price??null),
  col('note','Примечание',r=>esc(MODELS[r.model].note),r=>MODELS[r.model].note),col('source','Документ',r=>sourceLink(r.source),r=>r.source)]);
}
function rating(m){let s=[];if(m.photo_rating)s.push(`${num(m.photo_rating.estimated_CDR_A,0)} А длительного тока по Mooch 27.09.2026; DCIR ${num(m.photo_rating.DCIR_mOhm,1)} мОм`);if(m.continuous)s.push(`${num(m.continuous,0)} А${m.thermal_cut||['P50','M65','P30'].includes(m.source)?' с тепловой отсечкой':' непр.'}`);if(m.conditional_current)s.push(`${m.conditional_current} А / ${m.thermal_cut||80} °C`);if(m.pulse)s.push(`${num(m.pulse,0)} А / ${m.seconds} с`);if(m.reported_current)s.push(`${m.reported_current} А по исследованию`);return esc(s.join('; ')||'Не подтверждён');}
function renderTable(){$('end-charge-note').hidden=state.view!=='modes';let rows=visibleRows();if(state.view==='cells'){const seen=new Set();rows=rows.filter(r=>{if(seen.has(r.model))return false;seen.add(r.model);return true;});}const cs=columns();const sortKey=state.sort||(state.view==='modes'?state.metric:null),ascending=state.sort?state.ascending:state.metric==='heat';rows=sortedRows(rows,sortKey,ascending);
 $('table-head').innerHTML='<tr>'+cs.map(c=>`<th scope="col" aria-sort="${state.sort===c.key?(state.ascending?'ascending':'descending'):'none'}"><button data-sort="${c.key}" ${['name','photo'].includes(c.key)?'title="Вернуть исходный порядок: тип → производитель → модель"':''}>${esc(c.label)}</button></th>`).join('')+'</tr>';
 let group='';$('table-body').innerHTML=rows.map(r=>{let title='';const g=r.format+' · '+r.manufacturer;if(!state.sort&&g!==group){title=`<tr class="group-row"><td colspan="${cs.length}">${esc(g)}</td></tr>`;group=g;}return title+`<tr data-row="${r.id}">`+cs.map(c=>`<td class="${c.key==='photo'?'photo-cell':''}">${c.render(r)}</td>`).join('')+'</tr>';}).join('');
 $('table-state').textContent=`${rows.length} ${state.view==='cells'?'моделей':'сборок'} · ${sortKey?'Сортировка: '+cs.find(c=>c.key===sortKey)?.label+' ('+(ascending?'по возрастанию':'по убыванию')+')':'Исходный порядок: тип → производитель → модель'}${state.view==='modes'?` · ${blockCount()} блок(а), ${state.motors} двигатель(я), ${DATA.profiles.find(p=>p.id===state.profile).name}, G=${state.cooling} Вт/К`:''}`;
}
function renderRanking(){
 const rating=DATA.selection_rating,by=Object.fromEntries(rating.entries.map(e=>[e.id,e])),rows=rating.orders[state.ranking].map(id=>by[id]);
 const notes={overall:'Приоритет цены — 35 баллов; энергии — 25, потерь — 15, сохранения мощности — 15, массы — 5, полноты данных — 5. Более высокий балл лучше. Наличие 30 кВт до конца разряда не гарантируется.',range:'Порядок по выданной энергии двух блоков в умеренной поездке. Цена и пригодность для полной мощности не влияют на место; ограничения указаны в последней колонке. Это энергетический рейтинг, а не измеренный пробег.',price:'Порядок по минимальной известной цене Alibaba за 832 ячейки. Неизвестные цены исключены. Низкая цена сама по себе не подтверждает пригодность для двух двигателей 15/30 кВт.'};
 $('rating-note').textContent=notes[state.ranking];
 $('rating-head').innerHTML='<tr>'+['Место / элемент',...(state.ranking==='overall'?['Оценка / 100']:[]),'Alibaba: 1 / 2 блока','Выдано / номинально, 2 блока','Сценарный эквивалент WMTC / средней эксплуатации','Потери / блок при разгонах','Время без снижения запроса','Условие выбора'].map(x=>'<th>'+esc(x)+'</th>').join('')+'</tr>';
 $('rating-body').innerHTML=rows.map((e,i)=>`<tr><td><strong>${i+1}. ${esc(e.name)}</strong><span class="sub">${esc(e.role)}</span></td>${state.ranking==='overall'?`<td><strong>${num(e.score,1)}</strong></td>`:''}<td>${e.cost_block==null?'Нет цены':`${num(e.cost_block,2)} / ${num(e.cost_pair,2)} $<span class="sub">${num(e.unit_price,2)} $/яч. · ${esc(e.price_date)}</span>`}</td><td>${num(e.output_pair,2)} / ${num(e.nominal_pair,2)} кВт·ч</td><td>${num(e.wmtc_equiv,0)} / ${num(e.utility_equiv,0)} км-экв.</td><td>${num(e.heat_W_per_block,0)} Вт</td><td>${e.power_fraction==null?'—':num(e.power_fraction*100,1)+'%'}<span class="sub">В режиме частых разгонов</span></td><td>${esc(e.risk)}${e.issues.length?`<span class="sub">${esc(e.issues.join('; '))}</span>`:''}</td></tr>`).join('');
}
function render(){if(state.motors===2&&state.selection!=='all'&&!visibleRows().some(r=>r.id===state.selection)){state.selection='all';$('selection').value='all';}for(const opt of $('selection').options)if(opt.value!=='all')opt.disabled=state.motors===2&&!visibleRows().some(r=>r.id===opt.value);renderChart();renderTable();}
document.querySelectorAll('[data-metric]').forEach(b=>b.addEventListener('click',()=>setMetric(b.dataset.metric)));
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>{state.view=b.dataset.view;state.sort=state.view==='modes'?state.metric:null;state.ascending=state.metric==='heat';document.querySelectorAll('[data-view]').forEach(a=>a.setAttribute('aria-pressed',String(a===b)));renderTable();}));
for(const [id,key] of [['motors','motors'],['cutoff','cutoff'],['range-mode','rangeMode'],['range-basis','rangeBasis'],['blocks','blocks'],['profile','profile'],['cooling','cooling'],['selection','selection']])$(id).addEventListener('change',e=>{state[key]=['blocks','cooling','motors'].includes(key)?Number(e.target.value):e.target.value;if(state.motors===2){state.blocks=2;$('blocks').value='2';}$('blocks').disabled=state.motors===2;render();});
$('bars').addEventListener('click',e=>{const row=e.target.closest('[data-select]');if(row){state.selection=row.dataset.select;$('selection').value=state.selection;renderChart();}});
$('back-all').addEventListener('click',()=>{state.selection='all';$('selection').value='all';renderChart();});
$('reset-sort').addEventListener('click',()=>{state.sort=state.view==='modes'?state.metric:null;state.ascending=state.metric==='heat';renderTable();});
$('table-head').addEventListener('click',e=>{const b=e.target.closest('[data-sort]');if(!b)return;const k=b.dataset.sort;if(k==='photo'||k==='name'){state.sort=null;state.ascending=true;}else{state.ascending=state.sort===k?!state.ascending:true;state.sort=k;}renderTable();});
document.querySelectorAll('[data-ranking]').forEach(b=>b.addEventListener('click',()=>{state.ranking=b.dataset.ranking;document.querySelectorAll('[data-ranking]').forEach(a=>a.setAttribute('aria-pressed',String(a===b)));renderRanking();}));
render();renderRanking();
// Small pure sorting surface used by the local regression check.
globalThis.reportTesting={sortedRows,state,columns};
