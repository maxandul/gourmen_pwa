// Original service worker in an isolated VM: synthetic Fetch/Cache API only.
// This checks algorithmic paths, not a browser's worker lifetime or cookie behavior.
const fs=require('node:fs'), path=require('node:path'), vm=require('node:vm');
const root=path.resolve(__dirname,'../../..');
const source=fs.readFileSync(path.join(root,'static/sw.js'),'utf8');
function fixture(){
  const handlers={}, stores=new Map(), calls=[];
  const key=r=>typeof r==='string'?new URL(r,'https://audit.invalid').href:r.url;
  const caches={async open(n){if(!stores.has(n))stores.set(n,new Map()); const s=stores.get(n);return {
    async put(r,v){s.set(key(r),v.clone());},async match(r){return s.get(key(r))?.clone();}};},
    async match(r){for(const s of stores.values()){if(s.has(key(r)))return s.get(key(r)).clone();}},
    async keys(){return [...stores.keys()];},async delete(n){return stores.delete(n);}};
  let fetchImpl=async()=>new Response('online');
  const context=vm.createContext({URL,Response,Request,Headers,Set,Promise,
    console:{log(){},warn(){},error(){}},caches,
    fetch:async(...args)=>{calls.push(key(args[0]));return fetchImpl(...args);},
    self:{location:{origin:'https://audit.invalid'},addEventListener:(n,f)=>handlers[n]=f,
      skipWaiting:()=>Promise.resolve(),registration:{navigationPreload:{enable:async()=>{}}},
      clients:{claim:async()=>{},matchAll:async()=>[]}}});
  vm.runInContext(source,context);
  return {stores,calls,caches,context,handlers,setFetch(fn){fetchImpl=fn;},
    async dispatch(url,accept='*/*'){
      const waits=[];let response;
      handlers.fetch({request:new Request(new URL(url,'https://audit.invalid'),{headers:{Accept:accept}}),
        respondWith(p){response=p;},waitUntil(p){waits.push(p);}});
      return {response:await response,waits:waits.length};
    }};
}
(async()=>{
  const results=[];let f=fixture();
  const offline='/static/offline.4ebb2a42.html';
  const staticName='gourmen-static-v3.16.0';
  const dynamicName='gourmen-dynamic-v3.16.0';
  async function seedOffline(f){await (await f.caches.open(staticName)).put(offline,new Response('<html>offline</html>',{headers:{'Content-Type':'text/html'}}));}
  await f.dispatch('/dashboard/','text/html');
  results.push({id:'SW-01',scenario:'online_navigation_not_cached',cache_entries:[...f.stores.values()].reduce((n,s)=>n+s.size,0)});
  await seedOffline(f);f.setFetch(async()=>{throw Error('offline');});
  let r=await f.dispatch('/dashboard/','text/html');
  results.push({id:'SW-02',scenario:'offline_navigation',status:r.response.status,type:r.response.headers.get('content-type'),body:await r.response.text()});
  r=await f.dispatch('/api/push/subscription-status');let parseFailed=false;
  try{await r.response.clone().json();}catch{parseFailed=true;}
  results.push({id:'SW-03',scenario:'uncached_api_offline',status:r.response.status,type:r.response.headers.get('content-type'),json_parse_failed:parseFailed});
  f=fixture();f.setFetch(async()=>new Response(JSON.stringify({synthetic_user:'A'}),{headers:{'Content-Type':'application/json','Cache-Control':'private, no-store'}}));
  await f.dispatch('/api/audit-private');f.setFetch(async()=>{throw Error('offline');});
  r=await f.dispatch('/api/audit-private');
  results.push({id:'SW-04',scenario:'same_url_fallback_no_account_key',body:await r.response.json(),cache_names:await f.caches.keys(),limitation:'Synthetic response, no actual account switch, cookies or Vary matching; extends A-010 algorithm evidence only.'});
  f=fixture();await (await f.caches.open(staticName)).put('/static/css/main-v2.fa47ba3e.css',new Response('cached css'));
  r=await f.dispatch('/static/css/main-v2.fa47ba3e.css');
  results.push({id:'SW-05',scenario:'hashed_static_cache_hit',body:await r.response.text(),network_calls:f.calls.length});
  f=fixture();await (await f.caches.open(staticName)).put('/static/js/v2/tabs.js?v=3.16.0',new Response('old js'));
  let release;f.setFetch(()=>new Promise(resolve=>{release=resolve;}));
  r=await f.dispatch('/static/js/v2/tabs.js?v=3.16.0');
  results.push({id:'SW-06',scenario:'mutable_static_background_lifetime',body:await r.response.text(),network_pending:true,event_wait_until_calls:r.waits,limitation:'Does not simulate worker termination; no measured update loss.'});
  release(new Response('new js'));
  f=fixture();await f.caches.open('unrelated-cache');await f.caches.open(dynamicName);
  let activation;f.handlers.activate({waitUntil(p){activation=p;}});await activation;
  results.push({id:'SW-07',scenario:'activation_cache_deletion',remaining:await f.caches.keys(),limitation:'No unrelated production cache was accessed or removed.'});
  f=fixture();f.setFetch(async()=>{throw Error('all assets unavailable');});
  let install;f.handlers.install({waitUntil(p){install=p;}});await install;
  results.push({id:'SW-08',scenario:'install_all_asset_fetches_fail',install_promise_resolved:true,fetch_calls:f.calls.length,cached_entries:[...f.stores.values()].reduce((n,s)=>n+s.size,0)});
  const pwaSource=fs.readFileSync(path.join(root,'static/js/pwa.df1b3f63.js'),'utf8');
  for(const initiallyControlled of [false,true]){
    let change, reloads=0;
    const model={waitForServiceWorker:()=>new Promise(()=>{})};
    const pwaContext=vm.createContext({document:{addEventListener(){}},
      navigator:{serviceWorker:{controller:initiallyControlled?{}:null,addEventListener:(name,fn)=>{if(name==='controllerchange')change=fn;}}},
      window:{location:{reload:()=>reloads++}},console:{log(){}},model});
    vm.runInContext(pwaSource+'\nPWA.prototype.setupUpdateDetection.call(model);',pwaContext);
    change();const afterFirst=reloads;change();const afterSecond=reloads;change();
    results.push({id:initiallyControlled?'SW-10':'SW-09',scenario:'controller_change_reload',initially_controlled:initiallyControlled,
      reloads_after_first:afterFirst,reloads_after_second:afterSecond,reloads_after_third:reloads,
      limitation:'Actual shipped PWA handler executed; reload is a spy, no real page or unsaved form destroyed.'});
  }
  const out={method:'Original SW in Node VM with URL-keyed Cache mock and native Request/Response; no browser, no network, no production.',results};
  fs.writeFileSync(path.join(__dirname,'SW_STRATEGY_CHECKS.json'),JSON.stringify(out,null,2));
  console.log(JSON.stringify(out,null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
