// Original worker, native Request/Response, synthetic cache and transport only.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('static/sw.js', 'utf8');
const version = source.match(/const VERSION = '([^']+)'/)[1];
const current = `gourmen-static-v${version}`;
const offline = source.match(/'\/static\/offline\.[a-f0-9]+\.html'/)[0].slice(1,-1);
const publicResponse = body => new Response(body, {headers: {'Cache-Control':'public, max-age=3600'}});
function fixture() {
    const handlers = {}, stores = new Map(), calls = [], lifecycle = [];
    const key = r => new URL(typeof r === 'string' ? r : r.url, 'https://audit.invalid').href;
    const caches = {
        async open(name) {
            if (!stores.has(name)) stores.set(name, new Map());
            const store = stores.get(name);
            return {
                async put(r, response) {store.set(key(r), response.clone());},
                async match(r) {return store.get(key(r))?.clone();},
                async delete(r) {return store.delete(key(r));}
            };
        },
        async keys() {return [...stores.keys()];},
        async delete(name) {return stores.delete(name);},
        async match() {throw Error('Global cache lookup forbidden');}
    };
    let transport = async () => publicResponse('static');
    const context = vm.createContext({URL, Response, Request, Headers, console: {log(){},warn(){},error(){}},
        caches, fetch: async (r, options) => {calls.push({r, options}); return transport(r, options);},
        self: {location: {origin:'https://audit.invalid'}, addEventListener: (name, fn) => handlers[name] = fn,
            skipWaiting: () => lifecycle.push('skip'),
            registration: {navigationPreload: {disable: async () => lifecycle.push('disable')}},
            clients: {claim: async () => lifecycle.push('claim'), matchAll: async () => []}}
    });
    vm.runInContext(source, context);
    return {stores, calls, lifecycle, caches, setFetch(fn) {transport=fn;},
        async seed(name, url, response) {await (await caches.open(name)).put(url, response);},
        async event(name) {let done; handlers[name]({waitUntil(p) {done=p;}}); await done;},
        async dispatch(url, headers={}) {
            let result; const waits=[];
            handlers.fetch({request: new Request(new URL(url,'https://audit.invalid'), {headers}),
                respondWith(p) {result=p;}, waitUntil(p) {waits.push(p);}});
            return {response:await result, waits};
        }
    };
}
for (const url of ['/api/push/subscription-status','/docs/files/synthetic/download','/calendar/synthetic.ics','/auth/activate?token=synthetic','/member/profile']) {
    test('account transition and legacy cache exclusion: '+url.split('?')[0], async () => {
        const f=fixture(); let account='A';
        await f.seed('gourmen-dynamic-v3.16.7',url,new Response('PRIVATE-A'));
        await f.seed('unrelated-cache',url,new Response('PRIVATE-A'));
        f.setFetch(async (_, options) => {
            assert.equal(options.cache,'no-store');
            return new Response(account || 'anonymous', {headers:{'Cache-Control':'private, no-store'}});
        });
        assert.equal(await (await f.dispatch(url)).response.text(),'A');
        account=null;
        assert.equal(await (await f.dispatch(url)).response.text(),'anonymous');
        f.setFetch(async () => {throw Error('offline');});
        assert.equal((await f.dispatch(url)).response.status,503);
        account='B'; f.setFetch(async () => new Response(account));
        assert.equal(await (await f.dispatch(url)).response.text(),'B');
        f.setFetch(async () => {throw Error('offline');});
        const response=(await f.dispatch(url)).response;
        assert.equal(response.status,503);
        assert.ok(!(await response.text()).includes('PRIVATE-A'));
        assert.equal(f.stores.has(current),false);
    });
}
test('activation deletes known old app caches and preserves foreign caches', async () => {
    const f=fixture();
    for (const name of ['gourmen-v3.16.7','gourmen-dynamic-v3.16.7','gourmen-static-v3.16.7','unrelated-cache','gourmen-other',current]) await f.caches.open(name);
    await f.event('activate');
    assert.deepEqual(await f.caches.keys(),['unrelated-cache','gourmen-other',current]);
    assert.deepEqual(f.lifecycle,['disable','claim']);
});
for (const header of ['private','no-store','public, PRIVATE="Set-Cookie"','public, no-store','']) {
    test('static forbidden response is neither stored nor replayed: '+header, async () => {
        const f=fixture(), url='/static/css/test.1234abcd.css';
        await f.seed(current,url,new Response('private stale',{headers:{'Cache-Control':header}}));
        f.setFetch(async () => new Response('fresh',{headers:{'Cache-Control':header}}));
        assert.equal(await (await f.dispatch(url)).response.text(),'fresh');
        f.setFetch(async () => {throw Error('offline');});
        assert.equal((await f.dispatch(url)).response.status,503);
    });
}
test('static install and offline resources survive; HTML fallback scoped to current cache',async () => {
    const f=fixture(); await f.event('install');
    assert.ok(f.lifecycle.includes('skip'));
    assert.ok(f.stores.get(current).size > 10);
    f.setFetch(async () => {throw Error('offline');});
    assert.equal(await (await f.dispatch('/static/css/main-v2.fa47ba3e.css')).response.text(),'static');
    assert.equal(await (await f.dispatch('/dashboard/',{Accept:'text/html'})).response.text(),'static');
    const api=(await f.dispatch('/api/example')).response;
    assert.equal(api.status,503); assert.equal((await api.json()).error,'offline');
});
test('old offline page is never used, complete install failure stays defined',async () => {
    const f=fixture(); await f.seed('unrelated-cache',offline,publicResponse('foreign'));
    f.setFetch(async () => {throw Error('offline');});
    await f.event('install');
    assert.equal((await f.dispatch('/dashboard/',{Accept:'text/html'})).response.status,503);
});
test('mutable static refresh is bound to event lifetime',async () => {
    const f=fixture(),url='/static/js/v2/tabs.js?v=3.16.8';
    await f.seed(current,url,publicResponse('old'));
    let release; f.setFetch(() => new Promise(resolve => {release=resolve;}));
    const result=await f.dispatch(url);
    assert.equal(await result.response.text(),'old'); assert.equal(result.waits.length,1);
    release(publicResponse('new')); await Promise.all(result.waits);
    assert.equal(await (await (await f.caches.open(current)).match(url)).text(),'new');
});
for (const [url,headers] of [
    ['/static/test.js?token=synthetic',{}],['https://other.invalid/static/test.js',{}],
    ['/static/test.js',{Authorization:'synthetic'}],['/static/test.js',{Range:'bytes=0-5'}]
]) test('excluded static request does not read or write cache',async () => {
    const f=fixture(); await f.seed(current,url,publicResponse('old'));
    f.setFetch(async () => {throw Error('offline');});
    assert.equal((await f.dispatch(url,headers)).response.status,503);
});
test('HTTP error, redirect and download response are not cached', async () => {
    for (const response of [new Response('error',{status:403}),new Response('download',{headers:{'Cache-Control':'public','Content-Disposition':'attachment'}})]) {
        const f=fixture(); f.setFetch(async()=>response);
        assert.equal((await f.dispatch('/static/test.1234abcd.js')).response.status,response.status);
        assert.equal(f.stores.get(current).size,0);
    }
    const f=fixture(), response=publicResponse('redirect');
    Object.defineProperty(response,'redirected',{value:true}); f.setFetch(async()=>response);
    await f.dispatch('/static/test.1234abcd.js'); assert.equal(f.stores.get(current).size,0);
});
