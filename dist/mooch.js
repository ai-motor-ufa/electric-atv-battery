'use strict';
(() => {
  const data=JSON.parse(document.getElementById('mooch-data').textContent);
  const body=document.getElementById('mooch-body');
  const initial=Array.from(body.rows);
  function render(){
    const search=document.getElementById('mooch-search').value.trim().toLocaleLowerCase();
    const current=Number(document.getElementById('mooch-current').value);
    const sort=document.getElementById('mooch-sort').value;
    const rows=data.combined.map((r,i)=>({r,i})).filter(({r})=>r.model.toLocaleLowerCase().includes(search)&&(!current||r.estimated_CDR_A>=current));
    rows.sort((a,b)=>{
      if(sort==='name')return a.r.model.localeCompare(b.r.model);
      const x=a.r[sort],y=b.r[sort];
      if(x==null)return y==null?a.i-b.i:1;
      if(y==null)return -1;
      return (sort==='DCIR_mOhm'?x-y:y-x)||a.i-b.i;
    });
    body.replaceChildren(...rows.map(({i})=>initial[i]));
    document.getElementById('mooch-count').textContent=`Показано ${rows.length} из ${data.combined.length}. Полная выгрузка доступна выше.`;
  }
  document.getElementById('mooch-search').addEventListener('input',render);
  document.getElementById('mooch-current').addEventListener('change',render);
  document.getElementById('mooch-sort').addEventListener('change',render);
  render();
})();
