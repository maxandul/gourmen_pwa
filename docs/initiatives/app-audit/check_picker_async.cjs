// Audit-only controller probes: synthetic DOM and deferred fetch, no network.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
class Element {
  constructor() { this.children = []; this.attrs = {}; this.events = {}; this.className = ''; this.style = {}; this.text = ''; this.open = false; }
  set textContent(v) { this.children = []; this.text = v; }
  get textContent() { return this.text + this.children.map(c => c.textContent).join(''); }
  set innerHTML(v) { assert.equal(v, ''); this.children.forEach(c => c.parent = null); this.children = []; this.text = ''; }
  setAttribute(k, v) { this.attrs[k] = v; }
  getAttribute(k) { return this.attrs[k] ?? null; }
  removeAttribute(k) { delete this.attrs[k]; }
  appendChild(c) { c.parent = this; this.children.push(c); }
  remove() { if (this.parent) this.parent.children = this.parent.children.filter(c => c !== this); this.parent = null; }
  get classList() { return {add: s => this.className += ' ' + s, remove: s => this.className = this.className.split(' ').filter(x => x !== s).join('')}; }
  querySelectorAll(selector) {
    const match = e => selector.startsWith('.') ? e.className.split(' ').includes(selector.slice(1)) : (() => {
      const m = selector.match(/^\[([^=\]]+)(?:="([^"]*)")?\]$/);
      assert.ok(m, selector); return m[2] === undefined ? m[1] in e.attrs : e.attrs[m[1]] === m[2];
    })();
    return this.children.flatMap(c => [...(match(c) ? [c] : []), ...c.querySelectorAll(selector)]);
  }
  querySelector(s) { return this.querySelectorAll(s)[0] || null; }
  addEventListener(k, f) { (this.events[k] ||= []).push(f); }
  click() { for (const f of this.events.click || []) f({stopPropagation() {}}); }
  showModal() { this.open = true; }
  close() { this.open = false; }
}
const source = fs.readFileSync(path.resolve(__dirname, '../../../static/js/v2/docs-folder-picker.js'), 'utf8');
function setup() {
  const tree = new Element(), dialog = new Element(), apply = new Element(), opener = new Element(), close = new Element();
  const pending = [];
  const document = {
    getElementById: () => dialog, createElement: () => new Element(),
    querySelector: s => s === '[data-docs-folder-picker-tree]' ? tree : s === '[data-docs-folder-picker-apply]' ? apply : null,
    querySelectorAll: s => s === '[data-docs-folder-picker-close]' ? [close] : s === '[data-docs-folder-picker-open]' ? [opener] : []
  };
  vm.runInNewContext(source, {document, fetch: url => new Promise(resolve => pending.push({url, resolve})), encodeURIComponent});
  const respond = async (i, data) => { pending[i].resolve({ok: true, json: () => Promise.resolve(data)}); await new Promise(r => setImmediate(r)); };
  const row = id => tree.querySelector('[data-folder-id="' + id + '"]');
  const rows = () => tree.querySelectorAll('[data-folder-id]').map(e => e.getAttribute('data-folder-id'));
  return {tree, dialog, opener, close, pending, respond, row, rows};
}
async function opened() { const h = setup(); h.opener.click(); await h.respond(0, {id:'root',name:'Root'}); return h; }
(async () => {
  const results = [];
  {
    const h = await opened(); h.row('root').children[0].click();
    await h.respond(1, {folders:[{id:'a',name:'A'},{id:'b',name:'B'}]});
    h.row('a').children[0].click(); h.row('b').children[0].click();
    await h.respond(3, {folders:[{id:'b1',name:'B1'}]});
    await h.respond(2, {folders:[{id:'a1',name:'A1'}]});
    assert.deepEqual(h.rows(), ['root','a','b','a1','b1']);
    h.row('a').children[0].click(); assert.deepEqual(h.rows(), ['root','a','b','b1']);
    results.push({id:'PICK-01', result:'Two populated sibling branches survive reversed response order; collapse A retains B1. Existing A-129 ordering reproduced.'});
  }
  {
    const h = await opened(); h.row('root').children[0].click(); h.row('root').children[0].click(); h.row('root').children[0].click();
    await h.respond(2, {folders:[{id:'fresh',name:'Fresh'}]});
    await h.respond(1, {folders:[{id:'stale',name:'Stale'}]});
    assert.deepEqual(h.rows(), ['root','fresh']);
    results.push({id:'PICK-02', result:'Late children response renders only into detached container; reopened branch retains fresh content without duplicates.'});
  }
  {
    const h = setup(); h.opener.click(); h.opener.click();
    await h.respond(1, {id:'root',name:'Root'}); await h.respond(0, {id:'root',name:'Root'});
    assert.deepEqual(h.rows(), ['root','root']);
    results.push({id:'PICK-03', result:'Two pending opener clicks produce duplicate root rows.', rootRows:h.rows().length});
  }
  {
    const h = setup(); h.opener.click(); h.opener.click();
    await h.respond(0, {id:'root',name:'Root'}); h.close.click(); assert.equal(h.dialog.open, false);
    await h.respond(1, {id:'root',name:'Root'}); assert.equal(h.dialog.open, true);
    results.push({id:'PICK-04', result:'Second pending root response calls showModal after user closed picker.', reopened:h.dialog.open});
  }
  const output = {date:'2026-09-20', method:'Original controller in Node VM with minimal synthetic DOM and manually resolved fetch promises. No browser, layout, native modal/focus or real network verification.', results};
  fs.writeFileSync(path.join(__dirname, 'PICKER_ASYNC_CHECKS.json'), JSON.stringify(output, null, 2) + '\n');
  console.log(JSON.stringify(output, null, 2));
})().catch(e => {console.error(e); process.exitCode = 1;});
