import fs from 'node:fs/promises';
const root=new URL('../',import.meta.url),target=new URL('public/data/',root);
await fs.mkdir(target,{recursive:true});
await fs.cp(new URL('data/',root),target,{recursive:true,force:true});
console.log('Copied validated public data to frontend.');
