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
for(const m of html.matchAll(/<img[^>]+src="([^"]+)"/g)){if(m[1].startsWith('data:image/')){check(m[1].includes(';base64,'),'Expected embedded base64 image');check(Buffer.from(m[1].split(',')[1],'base64').length>100,'Empty embedded image')}else{check(!m[1].startsWith('/'),'Use relative image paths');check(existsSync(resolve(root,m[1])),`Missing image ${m[1]}`)}}
const main=scripts.find(s=>s.includes('const translations='));check(main,'Missing translation data');
const data=main.slice(main.indexOf('const translations='),main.indexOf('let language='));
const context={};vm.runInNewContext(data+';result=translations;',context,{timeout:1000});
const translations=context.result;
const keys=Object.keys(translations.en);
for(const lang of ['en','fr','fa']){check(translations[lang],`Missing language ${lang}`);for(const key of keys)check(translations[lang][key]!==undefined&&((typeof translations[lang][key]==='string'&&translations[lang][key].length>0)||Array.isArray(translations[lang][key])),`Missing ${lang}.${key}`)}
for(const m of html.matchAll(/data-i="([^"]+)"/g))for(const lang of ['en','fr','fa'])check(m[1] in translations[lang],`Missing translated UI ${lang}.${m[1]}`);
check(html.includes("dir=language==='fa'?'rtl':'ltr'"),'Missing RTL switch');
check(html.includes('maditech-language'),'Missing language persistence');
console.log('Passed: JavaScript syntax, image files, anchor links, IDs, EN/FR/FA translation coverage, RTL and language persistence.');

for(const match of html.matchAll(/<script[^>]+src="([^"]+)"/g)){const path=resolve(root,match[1]);check(existsSync(path),`Missing script ${match[1]}`);const r=spawnSync(process.execPath,["--check",path],{encoding:"utf8"});check(r.status===0,r.stderr)}

// Public GitHub project cards: generated data must be well formed and trilingual.
const projectBlock=html.match(/\/\* GITHUB-PROJECTS:START[^*]*\*\/\nconst githubProjects=(.*);\n\/\* GITHUB-PROJECTS:END \*\//);
check(projectBlock,'Missing GITHUB-PROJECTS block');
const githubProjects=JSON.parse(projectBlock[1]);
const approvedProjects=JSON.parse(readFileSync(resolve(root,'projects/approved-projects.json'),'utf8'));
const approvedRepos=new Set(approvedProjects.projects.map(p=>p.repo));
for(const p of githubProjects){
  check(approvedRepos.has(p.repo),`Project ${p.repo} is not in projects/approved-projects.json`);
  check(['ai','robotics','studio','apps'].includes(p.category),`Bad category for ${p.repo}`);
  check(['live','prototype','concept','archived'].includes(p.status),`Bad status for ${p.repo}`);
  check(p.url===`https://github.com/${approvedProjects.owner}/${p.repo}`,`Bad GitHub URL for ${p.repo}`);
  check(p.demo===null||/^https:\/\//.test(p.demo),`Bad demo URL for ${p.repo}`);
  for(const lang of ['en','fr','fa'])check(p.copy[lang]?.name&&p.copy[lang]?.summary,`Missing ${lang} copy for ${p.repo}`);
}
console.log(`Passed: ${githubProjects.length} approved GitHub project cards with EN/FR/FA copy.`);
