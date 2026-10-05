(function(root){
'use strict';
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function safeUrl(s){try{const u=new URL(s);return u.protocol==='https:'&&!u.username&&!u.password?u.href:''}catch(e){return ''}}
function valid(data){return data&&Array.isArray(data.guides)&&data.guides.every(g=>typeof g.id==='string'&&typeof g.patch_repo==='string'&&typeof g.game==='string'&&typeof g.title==='string'&&typeof g.category==='string'&&Array.isArray(g.platforms)&&g.platforms.every(p=>typeof p==='string')&&safeUrl(g.url)&&Number.isFinite(Date.parse(g.updated_at)))}
function filtered(guides,{game='',platform='전체',category='전체',query=''}={}){
 const q=query.trim().toLowerCase();
 return guides.filter(g=>(!game||g.patch_repo===game)&&(platform==='전체'||g.platforms.includes(platform))&&(category==='전체'||g.category===category)&&(!q||[g.game,g.title,g.category].join(' ').toLowerCase().includes(q))).sort((a,b)=>Date.parse(b.updated_at)-Date.parse(a.updated_at)||a.id.localeCompare(b.id));
}
function cards(guides,total){
 if(!guides.length)return `<div class="empty"><h2>${total?'조건에 맞는 공략이 없습니다.':'아직 등록된 공략집이 없습니다.'}</h2><p>${total?'검색어와 필터를 바꾸거나 전체 공략을 확인해 보세요.':'직접 만든 첫 공략을 등록하면 이곳에 표시됩니다.'}</p></div>`;
 return guides.map(g=>{
  const cover=safeUrl(g.cover),source=safeUrl(g.cover_source),url=safeUrl(g.url);
  const image=cover?`<img src="${esc(cover)}" alt="${esc(g.game)} 표지" loading="lazy">`:'표지 준비 중';
  const date=new Date(g.updated_at).toLocaleDateString('ko-KR',{timeZone:'Asia/Seoul'});
  return `<article class="row" data-guide="${esc(g.id)}">${source?`<a class="cover" href="${esc(source)}" target="_blank" rel="noopener">${image}</a>`:`<div class="cover">${image}</div>`}<div><h2 class="game">${esc(g.game)}</h2><div class="platforms">${g.platforms.map(esc).join(' · ')}</div><div class="guide-title">${esc(g.title)}</div><div class="tags"><span class="tag">${esc(g.category)}</span><span class="tag format">${esc(g.format)}</span></div><div class="links"><a href="${esc(url)}" target="_blank" rel="noopener">${g.format==='PDF'?'PDF 열기':'공략 읽기'} ↗</a><a href="${esc(url)}" download>다운로드</a></div></div><div class="updated">최근 수정<br>${esc(date)}</div></article>`;
 }).join('');
}
async function start(){
 const node=id=>root.document.getElementById(id);
 try{
  const response=await root.fetch('data/guides.json',{cache:'no-store',credentials:'omit'});if(!response.ok)throw new Error('Unavailable');
  const data=await response.json();if(!valid(data))throw new Error('Invalid catalogue');
  const guides=data.guides,game=new URL(root.location.href).searchParams.get('game')||'';
  node('guide-count').textContent=guides.length.toLocaleString('ko-KR');node('game-count').textContent=new Set(guides.map(g=>g.patch_repo||g.game)).size.toLocaleString('ko-KR');
  for(const [id,values] of [['platform',guides.flatMap(g=>g.platforms)],['category',guides.map(g=>g.category)]]){
   node(id).innerHTML=['전체',...new Set(values)].map(v=>`<option value="${esc(v)}">${esc(v)}</option>`).join('');
  }
  node('selection').hidden=!game;
  const render=()=>{node('list').innerHTML=cards(filtered(guides,{game,platform:node('platform').value,category:node('category').value,query:node('search').value}),guides.length)};
  node('platform').addEventListener('change',render);node('category').addEventListener('change',render);node('search').addEventListener('input',render);render();
 }catch(e){node('list').innerHTML='<div class="empty"><h2>공략집 목록을 불러오지 못했습니다.</h2><p>잠시 후 새로고침하거나 상단 저장소에서 확인해 주세요.</p></div>'}
}
if(typeof module!=='undefined'&&module.exports)module.exports={filtered,cards,valid,safeUrl};
if(root.document)void start();
})(globalThis);
