// Keep the supplied artwork intact; publish a consistent, self-contained SVG frame.
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const source=path.join(root,'docs/images/tarot');
const output=path.join(source,'designed');
mkdirSync(output,{recursive:true});
const {cards}=JSON.parse(readFileSync(path.join(source,'major-arcana.json'),'utf8'));
const numerals=['0','I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII','XIII','XIV','XV','XVI','XVII','XVIII','XIX','XX','XXI'];
for(const card of cards){
 const data=readFileSync(path.join(source,card.slug+'.png')).toString('base64');
 const size=card.name_en.length>17?47:59;
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1024" height="1536" viewBox="0 0 1024 1536" role="img" aria-label="${card.name_en}">
<title>${numerals[card.number]} · ${card.name_en}</title>
<defs><clipPath id="card"><rect x="16" y="16" width="992" height="1504" rx="38"/></clipPath><linearGradient id="gold"><stop stop-color="#b87833"/><stop offset=".45" stop-color="#fff0ab"/><stop offset="1" stop-color="#d99848"/></linearGradient></defs>
<rect width="1024" height="1536" rx="46" fill="#101329"/>
<image x="16" y="16" width="992" height="1504" preserveAspectRatio="xMidYMid meet" clip-path="url(#card)" xlink:href="data:image/png;base64,${data}"/>
<path d="M20 1330 Q512 1294 1004 1330 V1482 Q1004 1516 968 1516 H56 Q20 1516 20 1482Z" fill="#11132e" stroke="url(#gold)" stroke-width="4"/>
<path d="M80 1352 H418 M606 1352 H944 M80 1484 H944" stroke="url(#gold)" stroke-width="2"/>
<text x="512" y="1373" text-anchor="middle" fill="#f5d58d" font-family="Georgia,Times New Roman,serif" font-size="42">${numerals[card.number]}</text>
<text x="512" y="1451" text-anchor="middle" fill="#ffe6a5" font-family="Georgia,Times New Roman,serif" font-style="italic" font-size="${size}">${card.name_en}</text>
<rect x="16" y="16" width="992" height="1504" rx="38" fill="none" stroke="url(#gold)" stroke-width="7"/>
</svg>`;
 writeFileSync(path.join(output,card.slug+'.svg'),svg);
}
console.log(`Designed ${cards.length} Major Arcana with matching 2:3 frames and inset titles`);
