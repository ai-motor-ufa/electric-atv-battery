const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('dist/index.html','utf8'),json=html.match(/<script type="application\/json" id="report-data">([\s\S]*?)<\/script>/)[1],data=JSON.parse(json),nodes=new Map();
function node(id){if(!nodes.has(id))nodes.set(id,{id,innerHTML:'',textContent:'',hidden:false,value:'',disabled:false,handlers:{},dataset:{},options:[],addEventListener(k,f){this.handlers[k]=f;},setAttribute(k,v){this[k]=v;},insertAdjacentHTML(p,v){this.innerHTML=p==='afterbegin'?v+this.innerHTML:this.innerHTML+v;}});return nodes.get(id);}
node('report-data').textContent=json;node('selection').options=[{value:'all'},...data.rows.map(r=>({value:r.id}))];
const mb=['range','runtime','heat'].map(k=>Object.assign(node('metric-'+k),{dataset:{metric:k}})),vb=['energy','electrical','modes','cells'].map(k=>Object.assign(node('view-'+k),{dataset:{view:k}}));
const rb=['overall','range','price'].map(k=>Object.assign(node('rank-'+k),{dataset:{ranking:k}}));
const document={getElementById:node,querySelectorAll:s=>s==='[data-metric]'?mb:s==='[data-view]'?vb:s==='[data-ranking]'?rb:[]};
const ctx={document,console,fetch:async path=>({ok:true,json:async()=>JSON.parse(fs.readFileSync('dist/'+path.split('?')[0],'utf8'))})};vm.createContext(ctx);vm.runInContext(fs.readFileSync('dist/report.js','utf8'),ctx);
const api=ctx.reportTesting;
function change(id,value){node(id).handlers.change({target:{value}});}
async function flush(){for(let i=0;i<5;i++)await new Promise(r=>setImmediate(r));}
(async()=>{
for(const k of ['s50s','p45b','p42a','h52a','lrle','t50sg','h51','p50b','rs60','s50u','s50s2'])assert(node('table-body').innerHTML.includes(data.photos[k].file));assert(!node('table-body').innerHTML.includes('На фото LG H51T'));
assert.equal(api.state.blocks,2);assert.equal(api.state.motors,2);assert.equal(api.state.rangeBasis,'nominal');assert(node('bars').innerHTML.includes('80 км'));assert(node('bars').innerHTML.includes('#ed9296'));
const link=data.rows.find(r=>r.model==='link65p');const nominal=2*link.nominal_wmtc;assert(node('bars').innerHTML.includes(nominal.toLocaleString('ru-RU',{minimumFractionDigits:1,maximumFractionDigits:1})+' км-экв.'));
change('range-basis','delivered');assert.equal(api.state.rangeBasis,'delivered');assert(node('chart-note').textContent.includes('Полезная энергия BRP неизвестна'));
for(const b of rb){b.handlers.click();const first=data.selection_rating.orders[b.dataset.ranking][0],e=data.selection_rating.entries.find(e=>e.id===first);assert(node('rating-body').innerHTML.includes('1. '+e.name));assert(!/NaN|undefined|Infinity/.test(node('rating-body').innerHTML));}
change('range-mode','utility');assert(node('bars').innerHTML.includes('50 км'));
change('selection','C19');await flush();assert(node('detail').innerHTML.includes('tests/t50xg.jpg'));assert(node('detail').innerHTML.includes('≈Вт·ч до 2,8 В'));assert(node('detail').innerHTML.indexOf('tests/t50xg.jpg')>node('detail').innerHTML.indexOf('это не гарантия диапазона.'));assert.equal((node('detail').innerHTML.match(/<svg/g)||[]).length,3);assert(node('detail').innerHTML.includes('Черепаха при 2,9 В'));
for(const [model,keys] of [['link65p',['link65p']],['p50b',['p50b','p50b_sample']],['h51',['h51t']]]){change('selection',data.rows.find(r=>r.model===model&&r.p===16).id);await flush();for(const k of keys)assert(node('detail').innerHTML.includes(`data-test="${k}"`));}change('selection','C19');await flush();
assert(node('detail').innerHTML.includes('остановка при 2,65 В'));
change('motors',2);await flush();assert(node('blocks').disabled);assert(node('detail').innerHTML.includes('2 блок(а), 2 двигатель(я)'));assert.equal((node('detail').innerHTML.match(/<svg/g)||[]).length,3);
const r=data.rows.find(r=>r.id==='C19'),s=r.simulations['1_5_mixed_2.9'];assert(node('detail').innerHTML.includes((2*s.output_kwh).toLocaleString('ru-RU',{minimumFractionDigits:2,maximumFractionDigits:2})));
for(const motors of [1,2]){change('motors',motors);if(motors===1)change('blocks',1);await flush();const factor=motors===2?2:1;for(const route of data.turtle_routes){const [lo,hi]=route.wh_km,wh=factor*s.turtle_output_kwh*1000;const fmt=v=>v.toLocaleString('ru-RU',{minimumFractionDigits:1,maximumFractionDigits:1});assert(node('detail').innerHTML.includes(route.name));assert(node('detail').innerHTML.includes(`${fmt(wh/hi)}–${fmt(wh/lo)} км`));}assert(!/NaN|undefined|Infinity/.test(node('detail').innerHTML));}
for(const opt of node('selection').options){if(opt.value==='all')continue;const r=data.rows.find(r=>r.id===opt.value);assert.equal(opt.disabled,r.s!==26||r.p!==16);}
change('selection','all');
for(const motors of [1,2])for(const b of [1,2])for(const g of [0,5,20])for(const p of data.profiles)for(const c of ['2.9']){change('motors',motors);change('blocks',b);change('cooling',g);change('profile',p.id);change('cutoff',c);for(const m of mb){m.handlers.click();assert(!/NaN|undefined|Infinity/.test(node('bars').innerHTML));}}
for(const b of vb){b.handlers.click();for(const c of api.columns()){node('table-head').handlers.click({target:{closest:()=>({dataset:{sort:c.key}})}});assert(!/NaN|undefined|Infinity/.test(node('table-body').innerHTML));}}
change('motors',1);change('selection',data.rows.find(r=>r.model==='s50s').id);await flush();assert(node('detail').innerHTML.includes('нет применимого графика'));assert(node('detail').innerHTML.includes('Пробег в «черепахе» не определён'));change('selection','F02');await flush();assert(node('detail').innerHTML.includes('нет DCIR'));
const ids=new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]));for(const m of html.matchAll(/href="#([^"]+)"/g))assert(ids.has(m[1]),m[1]);
console.log('PASS: BRP references, motor/block/cutoff/profile/thermal controls, loaded traces, energy doubling, sorted views, missing data and anchors.');
})().catch(e=>{console.error(e);process.exit(1)});
