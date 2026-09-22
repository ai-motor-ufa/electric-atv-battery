// Regression checks for requested interactive behavior without a browser runtime.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('dist/index.html','utf8');
const json=html.match(/<script type="application\/json" id="report-data">([\s\S]*?)<\/script>/)[1];
const data=JSON.parse(json),nodes=new Map();
function node(id){if(!nodes.has(id))nodes.set(id,{id,innerHTML:'',textContent:'',hidden:false,value:'',handlers:{},dataset:{},addEventListener(k,f){this.handlers[k]=f;},setAttribute(k,v){this[k]=v;}});return nodes.get(id);}
node('report-data').textContent=json;
const metricButtons=['range','runtime','heat'].map(k=>Object.assign(node('metric-'+k),{dataset:{metric:k}}));
const viewButtons=['energy','electrical','modes','cells'].map(k=>Object.assign(node('view-'+k),{dataset:{view:k}}));
const document={getElementById:node,querySelectorAll:s=>s==='[data-metric]'?metricButtons:s==='[data-view]'?viewButtons:[]};
const ctx={document,console};vm.createContext(ctx);vm.runInContext(fs.readFileSync('dist/report.js','utf8'),ctx);
const api=ctx.reportTesting;
const displayed=()=>Array.from(node('table-body').innerHTML.matchAll(/data-row="([^"]+)"/g),m=>m[1]);
const initial=displayed();assert.equal(initial.length,data.rows.length);assert.equal((node('bars').innerHTML.match(/data-select=/g)||[]).length,data.rows.filter(r=>r.candidate).length);
assert.equal(data.rows.filter(r=>r.candidate&&r.format==='21700').length,15);assert.equal(data.rows.filter(r=>r.candidate&&r.format==='Pouch').length,6);
let barIds=Array.from(node('bars').innerHTML.matchAll(/data-select="([^"]+)"/g),m=>m[1]);
let barValues=barIds.map(id=>{const r=data.rows.find(x=>x.id===id),s=r.simulations['2_5_mixed'];return s?s.wmtc_equiv:r.energy_ceiling_wmtc*2;});
assert(barValues.every((v,i)=>!i||v<=barValues[i-1]),'Range chart must be descending');
assert(html.includes('Выбор ячеек для<br>тяговой АКБ 96 В'));assert(!html.includes('Энергия для<br>вашего маршрута.'));assert(!html.includes('Сравните свой запас.'));
function header(key){node('table-head').handlers.click({target:{closest:()=>({dataset:{sort:key}})}});}
function change(id,value){node(id).handlers.change({target:{value}});}
node('view-modes').handlers.click();let modeValues=displayed().map(id=>{const r=data.rows.find(x=>x.id===id),s=r.simulations['2_5_mixed'];return s?.wmtc_equiv??null;}).filter(v=>v!=null);assert(modeValues.every((v,i)=>!i||v<=modeValues[i-1]),'Range table must be descending');
node('view-energy').handlers.click();
header('energy');let seq=displayed().map(id=>data.rows.find(r=>r.id===id).energy);assert(seq.every((v,i)=>!i||v>=seq[i-1]));
header('energy');seq=displayed().map(id=>data.rows.find(r=>r.id===id).energy);assert(seq.every((v,i)=>!i||v<=seq[i-1]));
header('photo');assert.deepStrictEqual(displayed(),initial);
header('mass');header('name');assert.deepStrictEqual(displayed(),initial);
for(const b of viewButtons){b.handlers.click();assert.equal(displayed().length,b.dataset.view==='cells'?Object.keys(data.models).length:data.rows.length);
 for(const c of api.columns()){header(c.key);header(c.key);assert(!node('table-body').innerHTML.includes('undefined'));}
 header('name');assert(node('table-body').innerHTML.includes('group-row'));
}
node('view-electrical').handlers.click();header('dc');header('dc');let unknown=false;
for(const id of displayed()){const dc=data.rows.find(r=>r.id===id).dc_model;if(dc==null)unknown=true;else assert(!unknown,'Unknown DCIR must stay last in descending sort');}
for(const b of [1,2])for(const g of [5,20])for(const p of data.profiles){change('blocks',b);change('cooling',g);change('profile',p.id);
 for(const m of metricButtons){m.handlers.click();assert(!/NaN|undefined|Infinity/.test(node('bars').innerHTML));}
}
change('selection','C17');assert.equal(node('detail').hidden,false);assert.equal((node('detail').innerHTML.match(/<svg/g)||[]).length,3);
change('selection','F02');assert(node('detail').innerHTML.includes('нет DCIR'));assert(!node('detail').innerHTML.includes('<svg'));
node('back-all').handlers.click();assert.equal(node('detail').hidden,true);assert.equal(api.state.selection,'all');
assert(!data.rows.some(r=>r.format.includes('LFP')));for(const k of ['bak50d2','rs50','eve50pl'])assert(data.models[k]);
assert(!Object.values(data.models).some(m=>/LFP|LMFP/i.test(m.type)));
assert.deepStrictEqual([...new Set(data.rows.map(r=>r.model))].sort(),Object.keys(data.models).sort());
for(const k of ['t50xg','e61v','e63b','e66a'])assert(data.models[k]);
for(const k of ['bak50d2','s50s','p42a','p45b','rs60'])assert(data.models[k].market?.nkon?.price!=null,'Missing NKON price for '+k);
for(const k of ['amprius50q','gp50q','link60p','link65p'])assert.equal(data.models[k].market?.nkon?.availability,'not_found_on_nkon');
const anchorIds=new Set(Array.from(html.matchAll(/\bid="([^"]+)"/g),m=>m[1]));
for(const m of html.matchAll(/href="#([^"]+)"/g))assert(anchorIds.has(m[1]),'Missing anchor '+m[1]);
for(const p of Object.values(data.photos))assert(fs.existsSync('dist/'+p.file));
console.log('PASS: all configurations, models and overview candidates; sorts, reset, filters, all mode/cooling combinations, details, source anchors and photos.');
