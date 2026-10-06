const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const html = fs.readFileSync(path.join(__dirname, '../guides/radiata-stories-177-guide/radiata-stories-177-guide.html'), 'utf8');
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
  const saved = {radiata177_checks:'{"r001":true}',radiata177_view:'complex',radiata177_route:'human'};
  const app=load(saved);
  app.buttons[2].click();
  assert.equal(app.document.documentElement.dataset.layout,'mobile');
  assert.equal(app.buttons[2]['aria-pressed'],'true');
  assert.equal(app.storage.get('radiata177_checks'),saved.radiata177_checks);
  assert.equal(app.storage.get('radiata177_route'),'human');
  assert.equal(app.storage.get('radiata177_view'),'complex');
  const reloaded=load(Object.fromEntries(app.storage));
  assert.equal(reloaded.document.documentElement.dataset.layout,'mobile');
  reloaded.buttons[1].click();
  assert.equal(reloaded.document.documentElement.dataset.layout,'desktop');
  reloaded.buttons[0].click();
  assert.equal(reloaded.storage.get('radiata177_layout'),'auto');
});
test('invalid saved layout falls back to automatic and all 177 characters still render', () => {
  const app=load({radiata177_layout:'invalid'});
  assert.equal(app.document.documentElement.dataset.layout,'auto');
  assert.equal(vm.runInContext('recruits.length',app.context),177);
  assert.equal((app.document.getElementById('content').innerHTML.match(/<details class="recruit /g)||[]).length,177);
});
