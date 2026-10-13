import fs from 'node:fs/promises';
const root=new URL('../',import.meta.url),output=new URL('../../outputs/',root);
let html=await fs.readFile(new URL('dist/index.html',root),'utf8');
const script=html.match(/<script[^>]+src="([^"]+)"[^>]*><\/script>/);
const stylesheet=html.match(/<link[^>]+href="([^"]+\.css)"[^>]*>/);
if(!script||!stylesheet)throw Error('Expected a single Vite script and stylesheet');
const js=await fs.readFile(new URL(script[1],new URL('dist/',root)),'utf8');
const css=await fs.readFile(new URL(stylesheet[1],new URL('dist/',root)),'utf8');
const read=async path=>JSON.parse(await fs.readFile(new URL('data/'+path,root),'utf8'));
const index=await read('topics.json'),latest=await read('latest.json'),status=await read('status.json');
const weeklyCounts={},historyDates=[];
for(const day of await fs.readdir(new URL('data/history/',root))){const history=await read('history/'+day);let used=false;for(const snap of history.snapshots){if(Date.parse(snap.collected_at)<Date.now()-7*86400000)continue;used=true;for(const t of snap.topics)weeklyCounts[t.id]=(weeklyCounts[t.id]||0)+1;}if(used)historyDates.push(history.date);}
const snapshot={topics:index.topics,latestIds:latest.topics.map(t=>t.id),status,weeklyCounts,historyDates:historyDates.sort()};
const embedded=JSON.stringify(snapshot).replaceAll('<','\\u003c');
html=html.replace(script[0],()=>'<script>window.__RADAR_DATA__='+embedded+';</script><script type="module">'+js.replaceAll('</script','<\\/script')+'</script>').replace(stylesheet[0],()=>'<style>'+css+'</style>');
await fs.mkdir(output,{recursive:true});await fs.writeFile(new URL('Social-Radar.html',output),html);
console.log('Standalone local Social-Radar.html prepared with actual collected snapshot.');
