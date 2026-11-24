import {cpSync,mkdirSync,readdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const source=path.join(root,'docs/images/tarot');
const target=path.join(root,'frontend/public/tarot/assets');
mkdirSync(target,{recursive:true});
cpSync(path.join(source,'designed'),path.join(target,'designed'),{recursive:true});
for(const name of readdirSync(source)){
 if(name.endsWith('.png')||name==='major-arcana.json')cpSync(path.join(source,name),path.join(target,name));
}
console.log('Prepared tarot preview artwork');
