export type Page = 'today' | 'week' | 'bookmarks' | 'status';
export type News = {title:string;url:string;publisher:string};
export type Topic = {id:string;title:string;keywords:string[];category:string;source:string;source_url:string;source_published_at:string|null;trend_started_at:null;first_seen_at:string;last_seen_at:string;collected_at:string;status:string;search_volume_label:string|null;rank:null;related_posts:unknown[];related_news:News[];snapshot_count:number};
export type SourceStatus = {enabled:boolean;state:string;last_attempt_at?:string;last_success_at:string|null;count?:number;message:string};
export type Status = {schema_version:number;checked_at:string;timezone:string;schedule_local:string[];sources:Record<string,SourceStatus>};
export type Bookmark = {id:string;title:string;source:string;source_url:string;note:string;saved_at:string;topic:Topic|null};
export type Personal = {version:1;bookmarks:Bookmark[];preferences:{source:string;category:string}};
export type RadarData = {topics:Topic[];latestIds:string[];status:Status;weeklyCounts:Record<string,number>;historyDates:string[]};
