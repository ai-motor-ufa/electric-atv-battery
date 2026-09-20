'use strict';
const DATA=JSON.parse(document.getElementById('report-data').textContent);
const ROWS=DATA.rows, MODELS=DATA.models, PHOTOS=DATA.photos;
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num=(x,d=1)=>x==null?'—':Number(x).toLocaleString('ru-RU',{minimumFractionDigits:d,maximumFractionDigits:d});
const dim=a=>a.map(v=>num(v,Number.isInteger(v)?0:2)).join('×');
const photo=(r,caption=true)=>{const p=PHOTOS[r.model];return p?`<a href="${esc(p.file)}" target="_blank" rel="noopener"><img src="${esc(p.file)}" alt="${esc(r.cell_name)}: ${esc(p.caption)}" loading="lazy"></a>${caption?`<small>${esc(p.caption)}</small>`:''}`:'<small>Фото точной модели не найдено</small>'};
const state={metric:'range',blocks:2,profile:'mixed',cooling:5,selection:'all',view:'energy',sort:null,ascending:true};
const getSim=r=>r.simulations[`${state.blocks}_${state.cooling}_${state.profile}`];
const sources=Object.fromEntries(DATA.sources.map(s=>[s.id,s]));
const sourceLink=id=>sources[id]?.url?`<a href="${esc(sources[id].url)}" target="_blank" rel="noopener">${esc(id)} ↗</a>`:esc(id);

function sortedRows(rows,key,ascending=true){
 if(!key||key==='photo'||key==='name')return [...rows].sort((a,b)=>a.order-b.order);
 const c=columns().find(x=>x.key===key);if(!c)return [...rows];
 return [...rows].sort((a,b)=>{const x=c.sort(a),y=c.sort(b);if(x==null)return y==null?a.order-b.order:1;if(y==null)return -1;const v=typeof x==='number'?x-y:String(x).localeCompare(String(y),'ru',{numeric:true});return (ascending?1:-1)*v||a.order-b.order;});
}
function setMetric(metric){state.metric=metric;document.querySelectorAll('[data-metric]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.metric===metric)));renderChart();}
function renderChart(){
 const candidates=ROWS.filter(r=>r.candidate), rows=state.selection==='all'?candidates:candidates.filter(r=>r.id===state.selection);
 const title={range:'WMTC: энергетический эквивалент',runtime:'Время до ограничения и до резерва',heat:'Среднее тепло в ячейках одного блока'}[state.metric];
 $('chart-title').textContent=title;$('back-all').hidden=state.selection==='all';
 $('chart-note').textContent=state.metric==='range'?'Километры — пересчёт выданной энергии по индексу BRP, а не моделирование графика скорости WMTC. Штриховка: только граница по энергии, без проверки неизвестных потерь и тока.':'Сценарная модель при 25 °C. Время после снижения мощности не равно работе с прежней тягой. Пустое значение означает нехватку данных, а не нулевой нагрев.';
 $('chart-legend').innerHTML=state.metric==='runtime'?'<span>Без снижения запроса</span><span class="rest">После снижения, до резерва</span>':'<span>Модель с ограничениями</span><span class="uncertain">Только энергетическая граница / данных нет</span>';
 const vals=rows.map(r=>{const s=getSim(r);return state.metric==='range'?(s?s.wmtc_equiv:r.energy_ceiling_wmtc*state.blocks):state.metric==='runtime'?(s?s.minutes:null):(s?s.heat_mean:null);});
 const max=Math.max(...vals.filter(x=>x!=null),1)*1.07;
 $('bars').innerHTML=rows.map((r,i)=>{const s=getSim(r),v=vals[i],uncertain=!s;let bar='';
  if(v!=null){if(state.metric==='runtime')bar=`<i class="bar-total" style="width:${v/max*100}%"></i><i class="bar-full" style="width:${s.full_minutes/max*100}%"></i>`;else bar=`<i class="bar-fill ${uncertain?'estimate':''}" style="width:${v/max*100}%"></i>`;}
  const label=state.metric==='runtime'&&s?`${num(s.full_minutes,0)} / ${num(v,0)} <small>мин: полный / всего</small>`:v==null?'—<small>нет данных</small>':`${uncertain?'≤ ':''}${num(v,0)} ${state.metric==='range'?'км':'Вт'}${uncertain?'<small>граница по энергии</small>':''}`;
  return `<button class="bar-row" data-select="${r.id}" aria-label="Подробно: ${esc(r.name)}"><span class="bar-label">${esc(r.cell_name)}<small>${r.s}S${r.p}P · ${num(r.energy,2)} кВт·ч/блок${r.dc_basis.startsWith('Независимый')?' · DCIR теста':''}</small></span><span class="bar-track">${bar}</span><span class="bar-value">${label}</span></button>`;}).join('');
 $('axis').innerHTML=`<span>0</span><span>${num(max/2,0)}</span><span>${num(max,0)} ${state.metric==='range'?'км':state.metric==='runtime'?'мин':'Вт'}</span>`;
 $('detail').hidden=state.selection==='all';if(rows.length===1)renderDetail(rows[0]);
}
function plot(trace,key,label,color,limit){
 const w=420,h=210,left=44,right=12,top=12,bottom=34,xmax=Math.max(trace.at(-1).minute,1);
 const ymax=key==='soc'?100:key==='power'?32:Math.ceil(Math.max(60,...trace.map(t=>t[key]))/10)*10;
 const x=t=>left+t/xmax*(w-left-right),y=v=>h-bottom-v/ymax*(h-top-bottom);
 let svg=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(label)}">`;
 for(let j=0;j<=3;j++){const v=ymax*j/3;svg+=`<line x1="${left}" y1="${y(v)}" x2="${w-right}" y2="${y(v)}" stroke="#dcdce1"/><text x="${left-8}" y="${y(v)+4}" text-anchor="end" font-size="13" fill="#626269">${num(v,0)}</text>`;}
 if(limit!=null)svg+=`<line x1="${left}" y1="${y(limit)}" x2="${w-right}" y2="${y(limit)}" stroke="#ab6509" stroke-dasharray="4 5"/>`;
 svg+=`<polyline points="${trace.map(t=>`${x(t.minute).toFixed(1)},${y(t[key]).toFixed(1)}`).join(' ')}" fill="none" stroke="${color}" stroke-width="3" stroke-linejoin="round"/>`;
 for(const t of [0,xmax/2,xmax])svg+=`<text x="${x(t)}" y="${h-10}" text-anchor="middle" fill="#626269" font-size="13">${num(t,0)}</text>`;
 return svg+'</svg>';
}
function renderDetail(r){const s=getSim(r),m=MODELS[r.model];
 $('detail').innerHTML=`<div class="detail-top"><div>${photo(r,false)}</div><div><p class="eyebrow">${esc(r.format)} · ${r.n} элементов в блоке</p><h3>${esc(r.name)}</h3><span class="muted">${num(r.finished[0])}–${num(r.finished[1])} кг · корпус ${dim(r.box)} мм</span></div></div>`;
 if(!s){$('detail').innerHTML+=`<div class="empty">Тепловой прогноз и время сохранения мощности не рассчитаны: ${esc(r.dc_model==null?'нет DCIR':'нет полной применимой карты тока')}. ${esc(m.note)}</div><p class="note">Верхняя граница энергетического эквивалента для ${state.blocks} блоков: ${num(r.energy_ceiling_wmtc*state.blocks,0)} км по индексу WMTC / ${num(r.energy_ceiling_utility*state.blocks,0)} км по рабочему индексу. Это не подтверждение допустимой нагрузки.</p>`;return;}
 $('detail').innerHTML+=`<div class="kpis"><div class="kpi"><strong>${num(s.full_minutes)}</strong><span>мин без снижения запроса</span></div><div class="kpi"><strong>${num(s.minutes)}</strong><span>мин всего до резерва</span></div><div class="kpi"><strong>${num(s.utility_equiv,0)} км</strong><span>рабочий энергетический эквивалент</span></div><div class="kpi"><strong>${num(s.heat_mean,0)} Вт</strong><span>среднее тепло ячеек / блок</span></div></div>
 <div class="plots"><div class="plot"><h4>Запас заряда, %</h4>${plot(s.trace,'soc','SOC по времени','#0071e3',10)}<p>Время, мин. Нижний резерв — 10% SOC либо 85% бюджета Eном.</p></div><div class="plot"><h4>Температура ячеек, °C</h4>${plot(s.trace,'temp','Средняя температура по времени','#bc690b',45)}<p>Пунктир — начало снижения потолка при 45 °C. Горячие точки не рассчитаны.</p></div><div class="plot"><h4>Фактическая мощность на валу, кВт</h4>${plot(s.trace,'power','Доступная мощность по времени','#237c55',null)}<p>Для смешанного режима — средняя по долям, не высота отдельных импульсов.</p></div></div>
 <div class="callout"><strong>Первое ограничение:</strong> ${esc(s.first_limit)}.${s.first_soc!=null?` В модели это происходит около ${num(s.first_soc,0)}% SOC, при ${num(s.first_voltage,1)} В под нагрузкой и средней температуре ${num(s.first_temp,0)} °C.`:''} Максимальный ток одного блока в сценарии: ${num(s.max_current,0)} А / ${num(s.max_current/r.p)} А на ячейку. Выдано ${num(s.output_kwh,2)} кВт·ч; средняя мощность на валу ${num(s.mean_power,1)} кВт. Тепло всех подключённых ячеек: ${num(s.heat_kj,0)} кДж.</div>
 <p class="note">DCIR: ${num(r.dc_model,2)} мОм/яч. · ${esc(r.dc_basis)}. В тяжёлом условном маршруте 250–400 Вт·ч/км: ${num(s.rough_range[0],0)}–${num(s.rough_range[1],0)} км. Предварительная оценка зависит от принятой карты управления; это не гарантия диапазона.</p>`;
}
const col=(key,label,render,sort)=>({key,label,render,sort});
function columns(){
 const base=[col('photo','Фото ↺',r=>photo(r),r=>r.order),col('name','Элемент / сборка ↺',r=>`<span class="model-name">${esc(r.cell_name)}</span><span class="sub">${r.s}S${r.p}P · ${r.id}</span>`,r=>r.order),col('format','Тип',r=>esc(r.format),r=>r.format),col('brand','Производитель',r=>esc(r.manufacturer),r=>r.manufacturer)];
 if(state.view==='energy')return base.concat([
  col('count','Элементов',r=>r.n,r=>r.n),col('energy','Энергия / блок',r=>`${num(r.energy,2)} кВт·ч<span class="sub">Два: ${num(2*r.energy,2)}</span>`,r=>r.energy),
  col('mass','Ячейки / готовый',r=>`${num(r.mass,2)} кг<span class="sub">${num(r.finished[0])}–${num(r.finished[1])} кг</span>`,r=>r.finished[0]),
  col('layout','Предлагаемое размещение',r=>esc(r.layout),r=>r.layout),col('fit','В 230×400×340 мм',r=>esc(r.fit),r=>r.fit),
  col('box','Корпус для CAD',r=>`${dim(r.box)} мм<span class="sub">Δ ${r.delta.map(x=>(x>=0?'+':'')+x).join(' / ')} мм</span>`,r=>r.box.reduce((a,b)=>a*b,1)),
  col('reserve','Обвязка до 40 кг',r=>`${num(40-r.mass,2)} кг`,r=>40-r.mass)]);
 if(state.view==='electrical')return base.concat([
  col('volt','Uном / Uзаряд',r=>`${num(r.voltage)} / ${num(r.vmax)} В`,r=>r.voltage),
  col('cell-current','А/яч.: 30 кВт',r=>`${num(34290.909/r.voltage/r.p)}<span class="sub">При Uном ${num(r.voltage)} В; до просадки и ограничений</span>`,r=>34290.909/r.voltage/r.p),
  col('rating','Паспорт тока',r=>rating(MODELS[r.model]),r=>MODELS[r.model].continuous??MODELS[r.model].conditional_current??MODELS[r.model].pulse??null),
  col('dc','DCIR / источник',r=>`${num(r.dc_model,2)} мОм<span class="sub">${esc(r.dc_basis)}</span>`,r=>r.dc_model),
  col('res','Ветвь / вся линия',r=>r.r_total==null?`${r.s}r / ${num(r.s/r.p,3)}r + 1 мОм`:`${num(r.r_string,2)} / ${num(r.r_total,2)} мОм`,r=>r.r_total),
  col('note','Условия и ограничения',r=>esc(MODELS[r.model].note),r=>MODELS[r.model].note),col('source','Источник',r=>sourceLink(r.source),r=>r.source)]);
 if(state.view==='modes')return base.concat([
  col('full','Мин без снижения',r=>num(getSim(r)?.full_minutes),r=>getSim(r)?.full_minutes),
  col('total','Мин всего',r=>num(getSim(r)?.minutes),r=>getSim(r)?.minutes),
  col('range','WMTC-эквивалент',r=>getSim(r)?`${num(getSim(r).wmtc_equiv,0)} км`:`≤ ${num(r.energy_ceiling_wmtc*state.blocks,0)} км*`,r=>getSim(r)?.wmtc_equiv??null),
  col('utility','Рабочий эквивалент',r=>getSim(r)?`${num(getSim(r).utility_equiv,0)} км`:'—',r=>getSim(r)?.utility_equiv),
  col('heat','Среднее тепло / блок',r=>`${num(getSim(r)?.heat_mean,0)} Вт`,r=>getSim(r)?.heat_mean),
  col('temp','T к резерву',r=>`${num(getSim(r)?.t_end,0)} °C`,r=>getSim(r)?.t_end),
  col('cause','Первое ограничение',r=>esc(getSim(r)?.first_limit??'Нужны исходные данные'),r=>getSim(r)?.first_limit??null)]);
 return base.concat([
  col('capacity','Ёмкость ячейки',r=>`${num(MODELS[r.model].ah,2)} А·ч`,r=>MODELS[r.model].ah),
  col('cellmass','Масса ячейки',r=>`${num(MODELS[r.model].kg*1000,1)} г`,r=>MODELS[r.model].kg),
  col('dims','Размер ячейки',r=>`${dim(MODELS[r.model].dims)} мм`,r=>MODELS[r.model].dims.reduce((a,b)=>a*b,1)),
  col('chem','Химия / исполнение',r=>esc(MODELS[r.model].type),r=>MODELS[r.model].type),
  col('passport','Сопротивление в паспорте',r=>esc(MODELS[r.model].res),r=>MODELS[r.model].dc??null),
  col('rating','Ток одного элемента',r=>rating(MODELS[r.model]),r=>MODELS[r.model].continuous??MODELS[r.model].conditional_current??MODELS[r.model].pulse??null),
  col('note','Примечание',r=>esc(MODELS[r.model].note),r=>MODELS[r.model].note),col('source','Документ',r=>sourceLink(r.source),r=>r.source)]);
}
function rating(m){let s=[];if(m.continuous)s.push(`${num(m.continuous,0)} А${m.thermal_cut||['P50','M65','P30'].includes(m.source)?' с тепловой отсечкой':' непр.'}`);if(m.conditional_current)s.push(`${m.conditional_current} А / ${m.thermal_cut||80} °C`);if(m.pulse)s.push(`${num(m.pulse,0)} А / ${m.seconds} с`);if(m.reported_current)s.push(`${m.reported_current} А по исследованию`);return esc(s.join('; ')||'Не подтверждён');}
function renderTable(){let rows=ROWS;if(state.view==='cells'){const seen=new Set();rows=rows.filter(r=>{if(seen.has(r.model))return false;seen.add(r.model);return true;});}const cs=columns();rows=sortedRows(rows,state.sort,state.ascending);
 $('table-head').innerHTML='<tr>'+cs.map(c=>`<th scope="col" aria-sort="${state.sort===c.key?(state.ascending?'ascending':'descending'):'none'}"><button data-sort="${c.key}" ${['name','photo'].includes(c.key)?'title="Вернуть исходный порядок: тип → производитель → модель"':''}>${esc(c.label)}</button></th>`).join('')+'</tr>';
 let group='';$('table-body').innerHTML=rows.map(r=>{let title='';const g=r.format+' · '+r.manufacturer;if(!state.sort&&g!==group){title=`<tr class="group-row"><td colspan="${cs.length}">${esc(g)}</td></tr>`;group=g;}return title+`<tr data-row="${r.id}">`+cs.map(c=>`<td class="${c.key==='photo'?'photo-cell':''}">${c.render(r)}</td>`).join('')+'</tr>';}).join('');
 $('table-state').textContent=`${rows.length} ${state.view==='cells'?'моделей':'сборок'} · ${state.sort?'Сортировка: '+cs.find(c=>c.key===state.sort)?.label:'Исходный порядок: тип → производитель → модель'}${state.view==='modes'?` · ${state.blocks} блок(а), ${DATA.profiles.find(p=>p.id===state.profile).name}, G=${state.cooling} Вт/К`:''}`;
}
function render(){renderChart();renderTable();}
document.querySelectorAll('[data-metric]').forEach(b=>b.addEventListener('click',()=>setMetric(b.dataset.metric)));
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>{state.view=b.dataset.view;state.sort=null;document.querySelectorAll('[data-view]').forEach(a=>a.setAttribute('aria-pressed',String(a===b)));renderTable();}));
for(const [id,key] of [['blocks','blocks'],['profile','profile'],['cooling','cooling'],['selection','selection']])$(id).addEventListener('change',e=>{state[key]=['blocks','cooling'].includes(key)?Number(e.target.value):e.target.value;render();});
$('bars').addEventListener('click',e=>{const row=e.target.closest('[data-select]');if(row){state.selection=row.dataset.select;$('selection').value=state.selection;renderChart();}});
$('back-all').addEventListener('click',()=>{state.selection='all';$('selection').value='all';renderChart();});
$('reset-sort').addEventListener('click',()=>{state.sort=null;renderTable();});
$('table-head').addEventListener('click',e=>{const b=e.target.closest('[data-sort]');if(!b)return;const k=b.dataset.sort;if(k==='photo'||k==='name'){state.sort=null;state.ascending=true;}else{state.ascending=state.sort===k?!state.ascending:true;state.sort=k;}renderTable();});
render();
// Small pure sorting surface used by the local regression check.
globalThis.reportTesting={sortedRows,state,columns};
