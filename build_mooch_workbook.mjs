import fs from 'node:fs/promises';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const root=process.argv[2];
const d=JSON.parse(await fs.readFile(`${root}/dist/mooch_data.json`,'utf8'));
const wb=Workbook.create();
const columns=[['Модель / версия','model'],['Rated, мА·ч','rated_mAh'],['Tested, мА·ч','tested_mAh'],['Rated CDR, А','rated_CDR_A'],['Rated TL, А','rated_TL_A'],['CDR Mooch, А','estimated_CDR_A'],['TL Mooch, А','estimated_TL_A'],['DCIR, мОм','DCIR_mOhm'],...([5,10,15,20,30,40,50].map(a=>[`${a} А, Вт·ч`,`E${a}_Wh`])),['Дата испытания','test_date'],['Отсечка E, В','cutoff_energy_V'],['Условия / замечания','note'],['Источник','source'],['Статья','url'],['Статус статьи','article_status'],['Основание отбора','capacity_basis']];
function make(name,cols,records,tableName){
 const s=wb.worksheets.add(name);s.showGridLines=false;
 const matrix=[cols.map(c=>c[0]),...records.map(r=>cols.map(([_,key])=>r[key]??null))];
 s.getRangeByIndexes(0,0,matrix.length,cols.length).values=matrix;
 s.getRangeByIndexes(0,0,matrix.length,cols.length).format.font={name:'Arial',size:11};
 s.getRangeByIndexes(0,0,matrix.length,cols.length).format.rowHeight=23;
 s.getRangeByIndexes(0,0,matrix.length,cols.length).format.columnWidth=14;
 s.getRangeByIndexes(0,0,1,cols.length).format={fill:'#16324F',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:42,verticalAlignment:'center'};
 s.getRangeByIndexes(0,0,matrix.length,1).format.columnWidth=44;
 s.tables.add(s.getRangeByIndexes(0,0,matrix.length,cols.length),true,tableName);
 s.freezePanes.freezeRows(1);s.freezePanes.freezeColumns(1);
 for(let i=0;i<cols.length;i++){
  const k=cols[i][1];
  if(/mAh|_A$|mOhm|_Wh|_V$/.test(k))s.getRangeByIndexes(1,i,records.length,1).setNumberFormat(/mAh/.test(k)?'0':'0.00');
  if(k==='date'||k==='test_date'){
   const rg=s.getRangeByIndexes(1,i,records.length,1);
   rg.values=records.map(r=>[r[k]?new Date(r[k]+'T00:00:00Z'):null]);rg.setNumberFormat('yyyy-mm-dd');
  }
  if(['model','note','status','article_status','source','url','title','capacity_basis'].includes(k)){
   if(k!=='model')s.getRangeByIndexes(0,i,matrix.length,1).format.columnWidth=k==='note'?90:55;
   s.getRangeByIndexes(1,i,records.length,1).format.wrapText=true;
  }
 }
 s.getRangeByIndexes(1,0,records.length,cols.length).format.autofitRows();
 return s;
}
const photo=make('Фото 11.08.2026',columns,d.photo,'PhotoTests');
const forumColumns=[['Модель / версия','model'],['Ёмкость в заголовке, мА·ч','rated_mAh'],['Публикация','date'],['Образец 1, мА·ч','sample1_mAh'],['Образец 2, мА·ч','sample2_mAh'],['DCIR 1 / min, мОм','dc1_mOhm'],['DCIR 2 / max, мОм','dc2_mOhm'],['CDR Mooch, А','estimated_CDR_A'],['TL по статье, А','rated_TL_A'],['Статус извлечения','status'],['Условия / замечания','note'],['URL статьи','url'],['Исходный заголовок','title'],['Дата сбора','accessed']];
const forum=make('Форум',forumColumns,d.forum,'ForumTests');
const method=wb.worksheets.add('Методика');method.showGridLines=false;
method.getRange('A1:B13').values=[['Поле','Определение'],...d.method];
method.getRange('A1:B13').format.font={name:'Arial',size:11};
method.getRange('A1:A13').format.columnWidth=29;method.getRange('B1:B13').format.columnWidth=110;
method.getRange('A1:B13').format.wrapText=true;method.getRange('A1:B13').format.verticalAlignment='center';
method.getRange('A1:B13').format.rowHeight=58;
method.getRange('A1:B1').format={fill:'#16324F',font:{name:'Arial',size:11,color:'#FFFFFF',bold:true},rowHeight:28};
wb.recalculate();
console.log((await wb.inspect({kind:'table',range:"'Фото 11.08.2026'!A1:H4",include:'values',tableMaxRows:4,tableMaxCols:8})).ndjson);
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?',options:{useRegex:true,maxResults:20}})).ndjson);
for(const [sheetName,range,file] of [['Фото 11.08.2026','A1:H12','photo'],['Фото 11.08.2026','I1:Q12','energy'],['Форум','A1:I10','forum'],['Методика','A1:B13','method']]){
 const blob=await wb.render({sheetName,range,scale:1.5});await fs.writeFile(`/tmp/battery-workbook/${file}.png`,new Uint8Array(await blob.arrayBuffer()));
}
const file=await SpreadsheetFile.exportXlsx(wb);await file.save(`${root}/dist/Mooch_21700_2026-09-21.xlsx`);
