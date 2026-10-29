import {test} from 'node:test';
import assert from 'node:assert/strict';
import {runInNewContext} from 'node:vm';
import {readFileSync} from 'node:fs';

const script=readFileSync(new URL('../static/assets/visits.js',import.meta.url),'utf8');
async function run({endpoint='https://counter.example/api/site-views',provider='custom',fail=false,total=114,iframe=false,protocol='https:',prerender=false,apiSuccess=true,href='https://wentaochen.cn/project/example/?utm_source=test#section',canonical='https://wentaochen.cn/project/example/'}={}){
  const box={title:''},counter={textContent:'…',closest(){return box;}};
  const calls=[],listeners={};
  const window={};window.top=window;window.self=iframe?{}:window;
  const metadata={'site-views-endpoint':endpoint,'site-views-provider':provider,'site-views-started-at':'2026-10-29','site-views-timeout':'8000'};
  const context={window,location:{protocol,href},document:{prerendering:prerender,
    querySelector(selector){
      if(selector==='[data-site-views]')return counter;
      if(selector==='link[rel="canonical"]')return {href:canonical};
      const name=selector.match(/^meta\[name="([^"]+)"\]$/)?.[1];
      return name in metadata?{content:metadata[name]}:null;
    },
    addEventListener(name,callback){listeners[name]=callback;},
  },URL,Intl,AbortController,setTimeout,clearTimeout,
  async fetch(url,options){calls.push({url,options});if(fail)throw new Error('network');return {ok:true,async json(){return provider==='busuanzi'?{success:apiSuccess,data:{site_pv:total,page_pv:2,site_uv:1}}:{total,startedAt:'2026-10-27T12:38:42.956Z'};}};}};
  runInNewContext(script,context);
  await new Promise(resolve=>setImmediate(resolve));
  return {counter,box,calls,listeners};
}
test('one real write, no cookies/referrer, safe formatting',async()=>{
  const result=await run();
  assert.equal(result.counter.textContent,'114');assert.equal(result.calls.length,1);
  assert.equal(result.calls[0].options.credentials,'omit');
  assert.equal(result.calls[0].options.referrerPolicy,'no-referrer');
});
test('offline, unconfigured, invalid endpoint, iframe, and failed storage do not invent counts',async()=>{
  for(const [options,text] of [[{endpoint:''},'Not connected'],[{endpoint:'http://unsafe.example'},'Unavailable'],[{protocol:'file:'},'Online only']]){
    const result=await run(options);assert.equal(result.counter.textContent,text);assert.equal(result.calls.length,0);
  }
  assert.equal((await run({iframe:true})).calls.length,0);
  const failed=await run({fail:true});assert.equal(failed.counter.textContent,'Unavailable');assert.equal(failed.calls.length,1);
  assert.equal((await run({total:-1})).counter.textContent,'Unavailable');
});
test('prerendering defers the write and repeated events do not duplicate it',async()=>{
  for(const provider of ['custom','busuanzi']){
    const result=await run({prerender:true,provider});assert.equal(result.calls.length,0);
    await result.listeners.prerenderingchange();await result.listeners.prerenderingchange();
    assert.equal(result.calls.length,1);assert.equal(result.counter.textContent,'114');
  }
});
test('Busuanzi displays the shared site total and sends a clean canonical URL without identifiers',async()=>{
  const result=await run({provider:'busuanzi'});
  assert.equal(result.counter.textContent,'114');
  assert.equal(result.calls.length,1);
  const {options}=result.calls[0];
  assert.equal(options.method,'POST');
  assert.equal(options.credentials,'omit');
  assert.equal(options.referrerPolicy,'no-referrer');
  assert.equal(options.headers['x-bsz-referer'],'https://wentaochen.cn/project/example/');
  assert.equal(Object.keys(options.headers).length,1);
  assert.match(result.box.title,/2026-10-29/);
});
test('Busuanzi skips previews, shares the canonical host across aliases, and rejects failed or invalid totals',async()=>{
  const preview=await run({provider:'busuanzi',href:'https://preview.example/project/'});
  assert.equal(preview.counter.textContent,'Preview');assert.equal(preview.calls.length,0);
  const alias=await run({provider:'busuanzi',href:'https://www.wentaochen.cn/project/example/'});
  assert.equal(alias.calls[0].options.headers['x-bsz-referer'],'https://wentaochen.cn/project/example/');
  for(const options of [{apiSuccess:false},{total:-1},{total:'114'},{total:Number.MAX_SAFE_INTEGER+1}]){
    const result=await run({provider:'busuanzi',...options});
    assert.equal(result.counter.textContent,'Unavailable');assert.equal(result.calls.length,1);
  }
});
