export const STORAGE_KEY='social-radar.personal.v1';
export const emptyPersonal=()=>({version:1,bookmarks:[],preferences:{source:'all',category:'all'}});
export function safeUrl(value){try{const u=new URL(String(value));return ['http:','https:'].includes(u.protocol)&&!u.username&&!u.password?u.href:null;}catch{return null;}}
export function validatePersonal(value){
 if(!value||value.version!==1||!Array.isArray(value.bookmarks)||value.bookmarks.length>2000)throw Error('這不是支援的收藏備份（最多 2000 筆）。');
 const ids=new Set();
 const bookmarks=value.bookmarks.map(b=>{
  if(!b||typeof b.id!=='string'||ids.has(b.id)||typeof b.title!=='string'||!b.title.trim()||b.title.length>300||typeof b.note!=='string'||b.note.length>10000||!safeUrl(b.source_url)||!['google_trends','threads','instagram','other'].includes(b.source)||!Number.isFinite(Date.parse(b.saved_at)))throw Error('收藏資料格式不完整或連結不安全。');
  ids.add(b.id);
  // Imported nested topic data is never trusted as a source of factual statistics.
  return {id:b.id,title:b.title,source:b.source,source_url:safeUrl(b.source_url),note:b.note,saved_at:b.saved_at,topic:null};
 });
 return {version:1,bookmarks,preferences:{source:['all','google_trends','threads','instagram'].includes(value.preferences?.source)?value.preferences.source:'all',category:typeof value.preferences?.category==='string'?value.preferences.category:'all'}};
}
export function mergePersonal(current,incoming){const map=new Map(current.bookmarks.map(b=>[b.id,b]));for(const b of incoming.bookmarks)if(!map.has(b.id))map.set(b.id,b);if(map.size>2000)throw Error('匯入後超過 2000 筆，請先整理收藏。');return {...current,bookmarks:[...map.values()]};}
export function filterTopics(topics,{query='',source='all',category='all',days=1,now=Date.now()}={}){
 const q=query.trim().toLocaleLowerCase();return topics.filter(t=>Date.parse(t.last_seen_at)>=now-days*86400000&&(source==='all'||t.source===source)&&(category==='all'||t.category===category)&&(!q||[t.title,t.category,...t.keywords].join(' ').toLocaleLowerCase().includes(q))).sort((a,b)=>Date.parse(b.last_seen_at)-Date.parse(a.last_seen_at)||a.title.localeCompare(b.title,'zh-Hant'));
}
export function health(source,now=Date.now()){
 if(!source?.enabled)return {kind:'off',label:source?.state==='manual_only'?'手動收藏':'尚未接入'};
 if(!source.last_success_at)return {kind:'error',label:'尚無成功資料'};
 const age=now-Date.parse(source.last_success_at);
 if(age>86400000)return {kind:'error',label:'資料已過期'};
 if(age>43200000)return {kind:'warn',label:'超過 12 小時未更新'};
 if(source.state==='error')return {kind:'warn',label:'更新失敗・保留舊資料'};
 return {kind:'ok',label:'資料來源正常'};
}
export function nextUpdate(now=Date.now()){
 const local=new Date(now+8*3600000),day=Date.UTC(local.getUTCFullYear(),local.getUTCMonth(),local.getUTCDate());
 for(const h of [5,11,17,23]){const next=day+(h-8)*3600000+17*60000;if(next>now)return new Date(next).toISOString();}
 return new Date(day+86400000+(5-8)*3600000+17*60000).toISOString();
}
export function sourceLabel(source){return ({google_trends:'Google Trends',threads:'Threads',instagram:'Instagram',other:'公開連結'})[source]||'公開連結';}
export function analysisPrompt(topic){return `請分析以下觀測資料，提供社群文案靈感。\n\n話題：${topic.title}\n來源：${sourceLabel(topic.source)}\n原始連結：${topic.source_url}\n觀測時間：${topic.collected_at||topic.saved_at||'未提供'}\n搜尋量級：${topic.search_volume_label||'未提供'}（搜尋量並非社群互動數）\n${topic.related_news?.length?'RSS 附帶的相關新聞標題及連結（尚未閱讀內文）：\n'+topic.related_news.map(n=>`- ${n.title}\n  ${n.url}`).join('\n'):'沒有提供文章內文或互動數。'}\n\n請先查核原始來源，再說明背景，區分確定事實、推測及無法查核的資訊。提供值得討論的角度與三個社群文案靈感。不要捏造熱門原因、互動數或未讀取的文章內容；若無法開啟來源，請明確說明。若用於龜啤王或個人啤酒分享，請判斷是否適合連結到啤酒情境，不要勉強蹭不相關的事件。`;}
