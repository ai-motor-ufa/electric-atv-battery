const {chromium}=require(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES+'/playwright');
const assert=require('assert');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(process.env.REPORT_URL||'http://127.0.0.1:8765/',{waitUntil:'networkidle'});
 assert.equal(await page.locator('#blocks').inputValue(),'2');assert.equal(await page.locator('.brp-reference .bar-value').innerText(),'80 км\nЗаявлено BRP');
 await page.screenshot({path:'/tmp/r15-site.png',fullPage:false});
 assert.equal(await page.locator('#motors').inputValue(),'2');assert.equal(await page.locator('#range-basis').inputValue(),'nominal');
 for(const rank of ['overall','range','price']){await page.click(`[data-ranking="${rank}"]`);assert(await page.locator('#rating-body tr').count()>0);}
 await page.selectOption('#range-basis','delivered');
 await page.selectOption('#range-mode','utility');assert((await page.locator('.brp-reference .bar-value').innerText()).startsWith('50 км'));
 await page.selectOption('#selection','C19');await page.waitForFunction(()=>document.querySelectorAll('#detail svg').length===3);
 const one=await page.locator('#detail').innerText();assert(one.includes('Отсечка 2,9 В'));
 await page.selectOption('#cutoff','2.8');assert((await page.locator('#detail').innerText()).includes('Отсечка 2,8 В'));
 await page.selectOption('#motors','2');assert(await page.locator('#blocks').isDisabled());await page.waitForFunction(()=>document.querySelectorAll('#detail svg').length===3);assert((await page.locator('#detail').innerText()).includes('2 блок(а), 2 двигатель(я)'));
 await page.screenshot({path:'/tmp/r15-detail.png',fullPage:true});
 for(const view of ['modes','electrical','cells','energy']){await page.click(`[data-view="${view}"]`);assert(!/NaN|undefined|Infinity/.test(await page.locator('#table-body').innerText()));}
 await page.selectOption('#selection','all');
 for(const m of ['range','runtime','heat'])for(const g of ['0','5','20']){await page.click(`[data-metric="${m}"]`);await page.selectOption('#cooling',g);assert(!/NaN|undefined|Infinity/.test(await page.locator('#bars').innerText()));}
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:'/tmp/r15-mobile.png',fullPage:false});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
 assert.deepStrictEqual(errors,[]);console.log('PASS browser: controls, BRP modes, trace loading, two motors, all views, thermal scenarios, mobile width, no JS errors');await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
