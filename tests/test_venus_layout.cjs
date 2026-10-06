const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const html = fs.readFileSync(path.join(__dirname, '../guides/venus-and-braves-guide/venus-and-braves-guide.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
function load(saved = {}) {
  const storage = new Map(Object.entries(saved));
  const element = () => ({dataset: {},style: {},textContent: '',innerHTML: '',classList: {toggle() {}},setAttribute(k,v) {this[k]=v},addEventListener(k,fn) {this[k]=fn}});
  const elements = new Map();
  const buttons = ['auto','desktop','mobile'].map(mode => Object.assign(element(),{dataset:{layoutMode:mode}}));
  const document = {documentElement:element(),getElementById(id) {if(!elements.has(id))elements.set(id,element());return elements.get(id)},querySelectorAll(q) {return q==='[data-layout-mode]'?buttons:[]}};
  const context = vm.createContext({document,localStorage:{getItem(k){return storage.get(k)||null},setItem(k,v){storage.set(k,v)},removeItem(k){storage.delete(k)}},confirm(){return false}});
  vm.runInContext(script,context);
  return {storage,buttons,document,context};
}
test('manual layout persists across reloads without clearing checks or current view', () => {
  const saved = {vb_flow_checks:'{"r001":true}',vb_flow_view:'flow',vb_flow_filter:'all'};
  const app=load(saved);
  app.buttons[2].click();
  assert.equal(app.document.documentElement.dataset.layout,'mobile');
  assert.equal(app.buttons[2]['aria-pressed'],'true');
  assert.equal(app.storage.get('vb_flow_checks'),saved.vb_flow_checks);
  assert.equal(app.storage.get('vb_flow_filter'),'all');
  assert.equal(app.storage.get('vb_flow_view'),'flow');
  const reloaded=load(Object.fromEntries(app.storage));
  assert.equal(reloaded.document.documentElement.dataset.layout,'mobile');
  reloaded.buttons[1].click();
  assert.equal(reloaded.document.documentElement.dataset.layout,'desktop');
  reloaded.buttons[0].click();
  assert.equal(reloaded.storage.get('vb_flow_layout'),'auto');
});
test('invalid saved layout falls back to automatic and guide data remains available', () => {
  const app=load({vb_flow_layout:'invalid'});
  assert.equal(app.document.documentElement.dataset.layout,'auto');
  assert.equal(vm.runInContext('DATA.items368.length',app.context),368);
  assert.ok(vm.runInContext('DATA.chapters.length',app.context)>0);
});
