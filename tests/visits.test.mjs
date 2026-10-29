import {test} from 'node:test';
import assert from 'node:assert/strict';
import {runInNewContext} from 'node:vm';
import {readFileSync} from 'node:fs';

const script=readFileSync(new URL('../static/assets/visits.js',import.meta.url),'utf8');
async function run({endpoint='https://counter.example/api/site-views',fail=false,total=114,iframe=false,protocol='https:',prerender=false}={}){
  const box={title:''},counter={textContent:'…',closest(){return box;}};
  const calls=[],listeners={};
  const window={};window.top=window;window.self=iframe?{}:window;
  const context={window,location:{protocol},document:{prerendering:prerender,
    querySelector(selector){return selector==='[data-site-views]'?counter:{content:endpoint};},
    addEventListener(name,callback){listeners[name]=callback;},
  },URL,Intl,AbortController,setTimeout,clearTimeout,
  async fetch(url,options){calls.push({url,options});if(fail)throw new Error('network');return {ok:true,async json(){return {total,startedAt:'2026-10-27T12:38:42.956Z'};}};}};
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
  const result=await run({prerender:true});assert.equal(result.calls.length,0);
  await result.listeners.prerenderingchange();await result.listeners.prerenderingchange();
  assert.equal(result.calls.length,1);assert.equal(result.counter.textContent,'114');
});
