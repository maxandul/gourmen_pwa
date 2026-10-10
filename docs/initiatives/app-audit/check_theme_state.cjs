// Execute original theme controllers with a minimal DOM/storage model, not a browser.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../../..');
const checks = [];
function fixture(saved = null) {
  const storage = new Map(saved ? [['theme', saved]] : []);
  const listeners = {};
  const attrs = {};
  const buttonAttrs = {};
  const button = {querySelector: () => null, setAttribute: (k,v) => buttonAttrs[k]=v,
    addEventListener: () => {}};
  const html = {setAttribute: (k,v) => attrs[k]=v,
    addEventListener: (k,f) => listeners[k]=f,
    dispatchEvent: e => listeners[e.type]?.(e),
    classList: {add(){}, remove(){}}};
  let systemChange;
  const media = {matches:false, addEventListener: (_,f) => systemChange=f};
  const context = vm.createContext({window:{matchMedia:()=>media},
    document:{documentElement:html, readyState:'complete',
      querySelector:()=>({setAttribute(){}}), querySelectorAll:()=>[button]},
    localStorage:{getItem:k=>storage.get(k)||null, setItem:(k,v)=>storage.set(k,v), removeItem:k=>storage.delete(k)},
    CustomEvent:class {constructor(type,opts){this.type=type;this.detail=opts.detail;}},
    setTimeout:()=>0, console});
  for (const name of ['theme.js','theme-toggle.js']) {
    vm.runInContext(fs.readFileSync(path.join(root,'static/js/v2',name),'utf8'),context);
  }
  return {context, attrs, buttonAttrs, media,
    change(matches){media.matches=matches;systemChange({matches});},
    snapshot(){return {dom:attrs['data-theme'],reported:context.window.themeManager.getCurrentTheme(),
      button:buttonAttrs['data-theme-state'],checked:buttonAttrs['aria-checked']};}};
}
let f=fixture();
checks.push({scenario:'initial_default',actual:f.snapshot()});
f.change(true);
checks.push({scenario:'system_changes_to_dark_without_saved_choice',actual:f.snapshot()});
f.context.window.themeManager.toggle();
checks.push({scenario:'toggle_after_system_change',actual:f.snapshot()});
f=fixture('light');f.change(true);
checks.push({scenario:'manual_light_ignores_system_change',actual:f.snapshot()});
f.context.window.themeManager.resetToSystem();
checks.push({scenario:'reset_to_dark_system',actual:f.snapshot()});
const result={method:'Original JS in Node VM with minimal synthetic DOM; no browser layout, storage exceptions or real OS events.',checks};
fs.writeFileSync(path.join(__dirname,'THEME_STATE_CHECKS.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify(result,null,2));
