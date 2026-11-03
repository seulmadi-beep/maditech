import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { collectFacts, siteData, replaceBlock, summarize, validateApproved, START, END } from './sync-projects.mjs';

const approved = JSON.parse(readFileSync(new URL('../projects/approved-projects.json', import.meta.url), 'utf8'));

function fakeFetch(repos) {
  const calls = [];
  const impl = async url => {
    calls.push(url);
    const match = url.match(/repos\/[^/]+\/([^/]+)(\/readme)?$/);
    const repo = repos[match[1]];
    if (!repo) return { status: 404, ok: false };
    if (match[2]) return repo.readme ? { status: 200, ok: true, json: async () => ({ sha: repo.readme }) } : { status: 404, ok: false };
    return { status: 200, ok: true, json: async () => repo.meta };
  };
  return { impl, calls };
}
const meta = (name, extra = {}) => ({ html_url: `https://github.com/seulmadi-beep/${name}`, private: false, visibility: 'public', description: '', homepage: '', language: 'Python', archived: false, default_branch: 'main', pushed_at: '2026-06-25T18:38:48Z', ...extra });

test('approved list is valid', () => validateApproved(approved));

test('only approved repositories are requested', async () => {
  const { impl, calls } = fakeFetch({ 'salon-chatbot': { meta: meta('salon-chatbot') }, 'viral-bot': { meta: meta('viral-bot'), readme: 'abc' }, maditech: { meta: meta('maditech') } });
  await collectFacts(approved, { fetchImpl: impl });
  const repos = new Set(calls.map(u => u.split('/')[5]));
  assert.deepEqual([...repos].sort(), approved.projects.map(p => p.repo).sort());
});

test('private or missing repositories are never published', async () => {
  const { impl } = fakeFetch({ 'salon-chatbot': { meta: meta('salon-chatbot', { private: true, visibility: 'private', description: 'secret' }) }, maditech: { meta: meta('maditech') } });
  const facts = await collectFacts(approved, { fetchImpl: impl });
  assert.deepEqual(facts['salon-chatbot'], { available: false });
  assert.deepEqual(facts['viral-bot'], { available: false });
  const data = siteData(approved, facts);
  assert.deepEqual(data.map(p => p.repo), ['maditech']);
  assert.ok(!JSON.stringify(facts).includes('secret'));
});

test('archived repositories are shown as archived', async () => {
  const { impl } = fakeFetch({ 'salon-chatbot': { meta: meta('salon-chatbot', { archived: true }) } });
  const data = siteData(approved, await collectFacts(approved, { fetchImpl: impl }));
  assert.equal(data[0].status, 'archived');
});

test('API failures stop the sync instead of publishing partial data', async () => {
  await assert.rejects(collectFacts(approved, { fetchImpl: async () => ({ status: 500, ok: false }) }), /GitHub API 500/);
});

test('block replacement is escaped and idempotent', () => {
  const html = `<script>a;${START}\nconst githubProjects=[];\n${END}\nb;</script>`;
  const data = [{ repo: 'x', copy: { en: { name: '</script><b>' } } }];
  const once = replaceBlock(html, data);
  assert.ok(!once.slice(once.indexOf(START), once.indexOf(END)).includes('</script>'));
  assert.equal(replaceBlock(once, data), once);
});

test('no summary when nothing changed; review note when README changes', () => {
  const facts = { 'viral-bot': { available: true, readmeSha: 'a' } };
  assert.equal(summarize(approved, facts, facts), '');
  const text = summarize(approved, facts, { 'viral-bot': { available: true, readmeSha: 'b' } });
  assert.match(text, /viral-bot/);
  assert.match(text, /Needs a human check/);
});
