const fs=require('fs'),vm=require('vm'),assert=require('assert');
const d=JSON.parse(fs.readFileSync('dist/mooch_data.json'));
assert.equal(d.photo.length,41);assert.equal(d.forum.length,51);assert.equal(d.forum.filter(r=>r.status==='Текст статьи прочитан').length,48);assert.equal(d.combined.length,43);
for(const r of d.photo){assert((r.rated_mAh??r.tested_mAh)>4000);assert.equal(r.cutoff_energy_V,2.8);assert.equal(r.E50_Wh,null);}
assert.equal(d.photo.find(r=>r.model==='Tenpower 50XG').E20_Wh,16.1);
assert.equal(d.photo.find(r=>r.model==='Reliance RS50 (CCC logo, batch G3E)').DCIR_mOhm,6.5);
assert.equal(d.photo.find(r=>r.model==='LG H50').rated_mAh,null);
const s50=d.forum.find(r=>r.model==='Samsung 50S');assert.equal(s50.sample1_mAh,5049);assert.equal(s50.sample2_mAh,5071);assert.equal(s50.estimated_CDR_A,20);
const s50s2=d.forum.find(r=>r.model==='Samsung 50S2');assert.equal(s50s2.sample1_mAh,5111);assert.equal(s50s2.sample2_mAh,5143);assert.equal(s50s2.dc1_mOhm,12.9);assert.equal(s50s2.dc2_mOhm,13.8);assert.equal(s50s2.estimated_CDR_A,25);
const nodes=new Map();const node=id=>{if(!nodes.has(id))nodes.set(id,{value:'',textContent:'',rows:[],handlers:{},addEventListener(k,f){this.handlers[k]=f},replaceChildren(...rows){this.rows=rows}});return nodes.get(id)};
node('mooch-data').textContent=JSON.stringify(d);node('mooch-body').rows=d.combined.map((_,i)=>i);node('mooch-current').value='0';node('mooch-sort').value='name';
vm.runInNewContext(fs.readFileSync('dist/mooch.js','utf8'),{document:{getElementById:node}});
node('mooch-search').value='tenpower';node('mooch-search').handlers.input();assert.equal(node('mooch-body').rows.length,3);
node('mooch-current').value='40';node('mooch-current').handlers.change();assert.equal(node('mooch-body').rows.length,1);assert.equal(d.combined[node('mooch-body').rows[0]].model,'Tenpower 50XG');
node('mooch-search').value='';node('mooch-current').value='0';node('mooch-sort').value='E20_Wh';node('mooch-sort').handlers.change();
let empty=false;let prev=Infinity;for(const i of node('mooch-body').rows){const v=d.combined[i].E20_Wh;if(v==null)empty=true;else{assert(!empty);assert(v<=prev);prev=v;}}
node('mooch-search').value='not-a-cell';node('mooch-search').handlers.input();assert.equal(node('mooch-body').rows.length,0);
console.log('PASS: provenance, strict capacity filter, missing values, search, CDR filter and sorting.');
