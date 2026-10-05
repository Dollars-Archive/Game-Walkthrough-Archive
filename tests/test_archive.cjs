const test=require('node:test'),assert=require('node:assert/strict');
const archive=require('../docs/archive.js');
const guide=(id='a',changes={})=>({id,patch_repo:'eve-zero-kr-patch',game:'EVE ZERO',title:'분기 공략',category:'분기',format:'MD',platforms:['Dreamcast'],url:'https://dollars-archive.github.io/Game-Walkthrough-Archive/guides/eve/guide.html',updated_at:'2026-10-05T00:00:00Z',...changes});
test('empty archive has an honest empty state and no fake guides',()=>{assert(archive.cards([],0).includes('아직 등록된'));assert(archive.valid({guides:[]}))});
test('guide card replaces source link with a direct download action',()=>{
 const out=archive.cards([guide()],1);
 assert(out.includes(' download>다운로드</a>'));
 assert(!out.includes('>원문</a>'));
});
test('search, game linkage, platform and category filters intersect',()=>{
 const guides=[guide(),guide('b',{patch_repo:'other',platforms:['PS2'],category:'스토리',game:'다른 게임'})];
 assert.equal(archive.filtered(guides,{game:'eve-zero-kr-patch',platform:'Dreamcast',category:'분기',query:'eve'}).length,1);
 assert.equal(archive.filtered(guides,{platform:'PS2',query:'EVE'}).length,0);
 assert.equal(archive.filtered(guides,{game:'missing'}).length,0);
});
test('newer guides sort first, markup is escaped and invalid URLs are rejected',()=>{
 assert.equal(archive.filtered([guide(),guide('new',{updated_at:'2026-10-06T00:00:00Z'})])[0].id,'new');
 assert(archive.cards([guide('a',{title:'<script>x</script>'})],1).includes('&lt;script&gt;'));
 assert.equal(archive.valid({guides:[guide('a',{url:'javascript:alert(1)'})]}),false);
 assert.equal(archive.safeUrl('https://user:secret@example.com'),'');
});
const downloadable=(changes={})=>guide('a',{download_release_tag:'guide-a',download_asset_name:`a-${'a'.repeat(16)}.zip`,download_count:7,...changes});
const asset=(name=`a-${'a'.repeat(16)}.zip`,count=2)=>({name,state:'uploaded',download_count:count,browser_download_url:`https://github.com/Dollars-Archive/Game-Walkthrough-Archive/releases/download/guide-a/${name}`});
test('download counter distinguishes unknown and zero, keeps reading URL and only uses the current ZIP',()=>{
 const g=downloadable({download_count:0,download_url:asset().browser_download_url});
 const out=archive.cards([g],1);
 assert(out.includes('class="download-count">0</div>'));
 assert(out.includes(g.url));assert(out.includes(g.download_url));
 assert(archive.cards([downloadable({download_count:null})],1).includes('class="download-count">—</div>'));
 assert.equal(archive.assetUrl(g,'https://other.example/file.zip'),'');
});
test('release counts include old versions but exclude other guides and incomplete uploads',()=>{
 const current=asset(),old=asset(`a-${'b'.repeat(16)}.zip`,8);
 const stats=archive.releaseStats(downloadable(),[current,old,asset('other.zip',90),{...old,state:'starter'}]);
 assert.equal(stats.download_count,10);assert.equal(stats.download_url,current.browser_download_url);
 assert.equal(archive.releaseStats(downloadable(),[old]),null);
 assert.throws(()=>archive.releaseStats(downloadable(),[{...current,download_count:-1}]));
});
test('rate limiting keeps the last collected count and link',async()=>{
 const g=downloadable({download_url:asset().browser_download_url});
 await assert.rejects(archive.refreshDownloads([g],async()=>({ok:false,status:403})));
 assert.equal(g.download_count,7);assert.equal(g.download_url,asset().browser_download_url);
});
test('live counts page through release and asset lists without truncating totals',async()=>{
 const calls=[],g=downloadable();
 const old=Array.from({length:100},(_,i)=>asset(`a-${i.toString(16).padStart(16,'0')}.zip`,1));
 const fetcher=async url=>{
  calls.push(url);let data;
  if(url.includes('/assets?'))data=url.endsWith('page=1')?old:[asset(undefined,3)];
  else data=url.endsWith('page=1')?Array.from({length:100},(_,i)=>({tag_name:`other-${i}`,assets:[]})):[{id:8,tag_name:'guide-a',draft:false,prerelease:false,assets:old}];
  return {ok:true,json:async()=>data};
 };
 await archive.refreshDownloads([g],fetcher);
 assert.equal(g.download_count,103);assert.equal(calls.length,4);
 assert.equal(g.download_url,asset().browser_download_url);
});
