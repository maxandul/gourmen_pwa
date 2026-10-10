// Original shipped offline script, synthetic DOM/timers; no browser or network.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../../..');
const sw=fs.readFileSync(path.join(root,'static/sw.js'),'utf8');
const asset=sw.match(/\/static\/offline\.[a-f0-9]+\.html/)[0];
const html=fs.readFileSync(path.join(root,asset.slice(1)),'utf8');
const source=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].at(-1)[1];
function fixture(online){
  const nodes={'connection-status':{textContent:''},'last-sync':{textContent:'—'}},handlers={},timers=[],intervals=[],navigations=[];
  let probes=0;const navigator={onLine:online};
  const location={set href(v){navigations.push(v);}};
  vm.runInNewContext(source,{navigator,document:{getElementById:id=>nodes[id]},Date,
    window:{location,addEventListener:(name,fn)=>handlers[name]=fn},
    setTimeout:(fn,ms)=>{timers.push({fn,ms});},setInterval:(fn,ms)=>intervals.push({fn,ms}),
    fetch:()=>{probes++;throw Error('unreachable');}});
  return {nodes,handlers,timers,intervals,navigations,navigator,get probes(){return probes;},fire(){for(const t of timers.splice(0))t.fn();}};
}
const results=[];let f=fixture(false);
assert.equal(f.timers.length,0);results.push({id:'OFF-01',scenario:'offline_initial',redirect_timers:f.timers.length,status:f.nodes['connection-status'].textContent});
f=fixture(true);f.fire();assert.deepEqual(f.navigations,['/']);assert.equal(f.probes,0);
results.push({id:'OFF-02',scenario:'network_flag_online_without_app_probe',navigations:f.navigations,reachability_probes:f.probes,last_sync_set:f.nodes['last-sync'].textContent!=='—'});
f=fixture(true);f.navigator.onLine=false;f.handlers.offline();f.fire();assert.deepEqual(f.navigations,['/']);
results.push({id:'OFF-03',scenario:'offline_again_before_timer',status:f.nodes['connection-status'].textContent,navigations:f.navigations});
const attempts=[];for(let i=0;i<3;i++){f=fixture(true);f.fire();attempts.push(...f.navigations);}
assert.equal(attempts.length,3);results.push({id:'OFF-04',scenario:'three_simulated_fallback_document_loads',navigations:attempts,assumption:'Each navigation receives the offline document again; browser not simulated.'});
f=fixture(false);f.navigator.onLine=true;f.handlers.online();f.fire();assert.deepEqual(f.navigations,['/']);
results.push({id:'OFF-05',scenario:'online_event',navigations:f.navigations,reachability_probes:f.probes});
fs.writeFileSync(path.join(__dirname,'OFFLINE_RETURN_CHECKS.json'),JSON.stringify({asset,method:'5 original-script VM probes; synthetic timers/DOM; no actual browser reconnect',results},null,2));
console.log('5 offline-return probes verified');
