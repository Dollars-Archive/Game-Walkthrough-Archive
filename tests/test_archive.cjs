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
