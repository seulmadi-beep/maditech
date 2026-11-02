import { readFileSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';
import { spawnSync } from 'node:child_process';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const html=readFileSync(resolve(root,'index.html'),'utf8');
function check(condition,message){if(!condition)throw new Error(message)}
const scripts=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]);
for(const source of scripts){const result=spawnSync(process.execPath,['--check','--input-type=commonjs'],{input:source,encoding:'utf8'});check(result.status===0,result.stderr)}
const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);
check(new Set(ids).size===ids.length,'Duplicate element IDs');
for(const m of html.matchAll(/href="#([^"]+)"/g))check(ids.includes(m[1]),`Missing anchor ${m[1]}`);
for(const m of html.matchAll(/<img[^>]+src="([^"]+)"/g)){check(!m[1].startsWith('/'),'Use relative image paths');check(existsSync(resolve(root,m[1])),`Missing image ${m[1]}`)}
const main=scripts.find(s=>s.includes('const translations='));check(main,'Missing translation data');
const data=main.slice(main.indexOf('const translations='),main.indexOf('let language='));
const context={};vm.runInNewContext(data+';result=translations;',context,{timeout:1000});
const translations=context.result;
const keys=Object.keys(translations.en);
for(const lang of ['en','fr','fa']){check(translations[lang],`Missing language ${lang}`);for(const key of keys)check(typeof translations[lang][key]==='string'&&translations[lang][key].length>0,`Missing ${lang}.${key}`)}
for(const m of html.matchAll(/data-i="([^"]+)"/g))for(const lang of ['en','fr','fa'])check(m[1] in translations[lang],`Missing translated UI ${lang}.${m[1]}`);
check(html.includes("dir=language==='fa'?'rtl':'ltr'"),'Missing RTL switch');
check(html.includes('maditech-language'),'Missing language persistence');
console.log('Passed: JavaScript syntax, image files, anchor links, IDs, EN/FR/FA translation coverage, RTL and language persistence.');
