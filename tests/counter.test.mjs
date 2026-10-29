import {test} from 'node:test';
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {mkdtempSync,readFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {handleSiteViews} from '../counter/worker.mjs';

const site='https://wentaochen.cn';
const request=(method='GET',headers={},path='/api/site-views')=>new Request('https://counter.example'+path,{method,headers});
function binding(sqlite) {
  return {prepare(sql) {
    let parameters=[];
    return {bind(...values){parameters=values;return this;},async first(){return sqlite.prepare(sql).get(...parameters)??null;}};
  }};
}
function open(filename=':memory:') {
  const db=new DatabaseSync(filename);
  db.exec(readFileSync(new URL('../counter/migrations/0001_site_views.sql',import.meta.url),'utf8'));
  return db;
}

test('imports real historical count; GET read-only; 50 atomic writes persist across restart',async()=>{
  const folder=mkdtempSync(join(tmpdir(),'wentao-counter-'));
  let db=open(join(folder,'counter.sqlite'));
  try {
    const snapshot=JSON.parse(readFileSync(new URL('../migration/counter-snapshot.json',import.meta.url),'utf8'));
    db.prepare("INSERT INTO site_views VALUES('global',?,?)").run(snapshot.total,snapshot.startedAt);
    let env={DB:binding(db),ALLOWED_ORIGINS:site};
    assert.equal((await (await handleSiteViews(request(),env)).json()).total,snapshot.total);
    const responses=await Promise.all(Array.from({length:50},()=>handleSiteViews(request('POST',{Origin:site}),env)));
    const totals=await Promise.all(responses.map(async r=>{
      assert.equal(r.headers.get('Access-Control-Allow-Origin'),site);
      assert.equal(r.headers.get('Cache-Control'),'private, no-store');
      return (await r.json()).total;
    }));
    assert.deepEqual(totals.sort((a,b)=>a-b),Array.from({length:50},(_,i)=>snapshot.total+i+1));
    db.close();db=open(join(folder,'counter.sqlite'));
    env={DB:binding(db),ALLOWED_ORIGINS:site};
    for(let i=0;i<2;i++)assert.deepEqual(await (await handleSiteViews(request(),env)).json(),{total:snapshot.total+50,startedAt:snapshot.startedAt});
  }finally{db.close();rmSync(folder,{recursive:true,force:true});}
});

test('CORS accepts only configured origins; rejects missing-origin writes and wrong paths/methods',async()=>{
  const db=open();
  const env={DB:binding(db),ALLOWED_ORIGINS:site+',https://example.github.io'};
  try {
    for(const headers of [{},{Origin:'https://unrelated.example'},{Origin:site+'.attacker.example'}]){
      assert.equal((await handleSiteViews(request('POST',headers),env)).status,403);
    }
    assert.equal((await handleSiteViews(request('DELETE',{Origin:site}),env)).status,405);
    assert.equal((await handleSiteViews(request('POST',{Origin:site},'/wrong'),env)).status,404);
    assert.equal((await handleSiteViews(request('GET',{Origin:'https://unrelated.example'}),env)).status,403);
    assert.equal((await (await handleSiteViews(request(),env)).json()).total,0);
    const options=await handleSiteViews(request('OPTIONS',{Origin:site,'Access-Control-Request-Method':'POST'}),env);
    assert.equal(options.status,204);
    assert.equal(options.headers.get('Access-Control-Allow-Origin'),site);
    assert.equal((await handleSiteViews(request('OPTIONS',{Origin:site,'Access-Control-Request-Method':'DELETE'}),env)).status,403);
    assert.equal((await handleSiteViews(request('POST',{Origin:'https://example.github.io'}),env)).status,200);
  }finally{db.close();}
});

test('missing or failed database returns unavailable with CORS, without fabricated totals',async()=>{
  for(const DB of [undefined,{prepare(){throw new Error('database error');}}]){
    const response=await handleSiteViews(request('POST',{Origin:site}),{DB,ALLOWED_ORIGINS:site});
    assert.equal(response.status,503);
    assert.equal(response.headers.get('Access-Control-Allow-Origin'),site);
    assert.deepEqual(await response.json(),{error:'counter_unavailable'});
  }
});
