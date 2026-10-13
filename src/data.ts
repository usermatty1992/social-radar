import type {RadarData,Topic,Status} from './types';
const localDate=(date:Date)=>new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Taipei',year:'numeric',month:'2-digit',day:'2-digit'}).format(date);
async function json(path:string){const r=await fetch(import.meta.env.BASE_URL+'data/'+path,{cache:'no-store'});if(!r.ok)throw Error('資料載入失敗');return r.json();}
export async function loadRadar():Promise<RadarData>{
 // The downloadable local HTML embeds a truthful snapshot. Online deployments fetch current JSON.
 const embedded=(window as unknown as {__RADAR_DATA__?:RadarData}).__RADAR_DATA__;
 if(location.protocol==='file:'&&embedded)return embedded;
 const [index,latest,status]=await Promise.all([json('topics.json'),json('latest.json'),json('status.json')]);
 if(index.schema_version!==1||latest.schema_version!==1||status.schema_version!==1||!Array.isArray(index.topics)||!Array.isArray(latest.topics)||!status.sources)throw Error('公開資料格式不相容，請稍後重新載入。');
 const weeklyCounts:Record<string,number>={},historyDates:string[]=[];
 const cutoff=Date.now()-7*86400000;
 await Promise.all(Array.from({length:8},(_,i)=>localDate(new Date(Date.now()-i*86400000))).map(async day=>{
  try{const history=await json('history/'+day+'.json');if(!Array.isArray(history.snapshots))return;let used=false;
   for(const snapshot of history.snapshots){if(Date.parse(snapshot.collected_at)<cutoff)continue;used=true;const seen=new Set<string>();for(const topic of snapshot.topics||[])if(typeof topic.id==='string'&&!seen.has(topic.id)){seen.add(topic.id);weeklyCounts[topic.id]=(weeklyCounts[topic.id]||0)+1;}}
   if(used)historyDates.push(day);
  }catch{/* Missing days are expected for a new deployment; do not synthesize history. */}
 }));
 return {topics:index.topics as Topic[],latestIds:latest.topics.map((t:Topic)=>t.id),status:status as Status,weeklyCounts,historyDates:historyDates.sort()};
}
