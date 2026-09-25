'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM, VirtualConsole } = require('jsdom');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const source = fs.readFileSync(path.join(root, 'assets/app.js'), 'utf8');
const registry = JSON.parse(fs.readFileSync(path.join(root, 'data/registry.json'), 'utf8'));
const config = JSON.parse(fs.readFileSync(path.join(root, 'config.json'), 'utf8'));
const record = registry.records[0];
const site = 'https://preview.example.test/registry/';

async function boot(t, options = {}) {
  const data = structuredClone(options.data || registry);
  const settings = structuredClone(options.config || config);
  const requests = [];
  const errors = [];
  const console = new VirtualConsole();
  console.on('jsdomError', error => errors.push(error.message));
  // Only repository-owned HTML/JS runs. Resource fetching is disabled; every
  // application fetch is a local fixture stub. No browser process is launched.
  const dom = new JSDOM(html, {
    url: site + (options.hash || ''),
    runScripts: 'dangerously',
    virtualConsole: console,
    beforeParse(window) {
      window.fetch = async url => {
        const address = String(url);
        requests.push(address);
        if (options.failFetch) return { ok: false };
        if (address === site + 'data/registry.json') return { ok: true, json: async () => data };
        if (address === site + 'config.json') return { ok: true, json: async () => settings };
        throw new Error('Unexpected network request: ' + address);
      };
    },
  });
  t.after(() => dom.window.close());
  dom.window.eval(source);
  await new Promise(resolve => setImmediate(resolve));
  return { window: dom.window, document: dom.window.document, requests, errors };
}

test('loads the registry and searches title, UUID and the full decimal identity', async t => {
  const { window, document, requests } = await boot(t);
  assert.deepEqual(requests.sort(), [site + 'config.json', site + 'data/registry.json'].sort());
  assert.equal(document.querySelectorAll('.record-link').length, registry.records.length);
  const search = document.getElementById('registrySearch');
  assert.equal(search.disabled, false);
  for (const query of [record.title.toUpperCase(), record.id, record.barcode_number]) {
    search.value = query;
    search.dispatchEvent(new window.Event('input'));
    assert.equal(document.querySelectorAll('.record-link').length, 1);
    assert.equal(document.querySelector('.record-link').getAttribute('href'), '#id=' + record.id);
  }
  search.value = 'there is no matching asset';
  search.dispatchEvent(new window.Event('input'));
  assert.equal(document.querySelectorAll('.record-link').length, 0);
  assert.equal(document.getElementById('emptyResults').hidden, false);
  search.value = '';
  search.dispatchEvent(new window.Event('input'));
  assert.equal(document.querySelectorAll('.record-link').length, registry.records.length);
});

test('exact hash selects the record, local QR and configured permalink without redirecting', async t => {
  const resolver = 'https://identity.example.test/permanent/';
  const hash = '#id=' + record.id;
  const { window, document, errors, requests } = await boot(t, { hash, config: { resolver_base: resolver } });
  assert.equal(document.querySelector('#recordPanel h3').textContent, record.title);
  assert.equal(document.querySelector('.record-link[aria-current="true"]').hash, hash);
  assert.equal(document.querySelector('.qr-sheet img').src, site + 'labels/' + record.id + '.svg');
  assert.equal(document.querySelector('.identity-fields a').href, resolver + hash);
  assert.equal(document.querySelector('.launch').href, record.record_url);
  assert.equal(document.querySelector('.badge-demo').textContent, 'Demonstration');
  assert.equal(window.location.href, site + hash);
  assert.equal(requests.length, 2);
  assert.deepEqual(errors, []);
});

test('hash changes resolve independently of the current search', async t => {
  const { window, document } = await boot(t);
  document.getElementById('registrySearch').value = 'no match';
  document.getElementById('registrySearch').dispatchEvent(new window.Event('input'));
  window.location.hash = 'id=' + record.id;
  window.dispatchEvent(new window.HashChangeEvent('hashchange'));
  assert.equal(document.querySelector('#recordPanel h3').textContent, record.title);
  window.location.hash = '';
  window.dispatchEvent(new window.HashChangeEvent('hashchange'));
  assert.equal(document.getElementById('recordHeading').textContent, 'Choose a record');
});

test('unknown and malformed addresses never resolve a different identity', async t => {
  const unknown = '#id=00000000-0000-4000-8000-000000000000';
  for (const hash of [unknown, '#id=short', '#id=' + record.id + '&extra=1', '#id=' + record.id.toUpperCase(), '#other=' + record.id]) {
    await t.test(hash, async t => {
      const { document, window } = await boot(t, { hash });
      assert.equal(document.getElementById('recordHeading').textContent, hash === unknown ? 'Identity not found' : 'Malformed identity address');
      assert.equal(document.querySelector('.launch'), null);
      assert.equal(document.querySelector('.qr-sheet img'), null);
      assert.equal(window.location.href, site + hash);
    });
  }
});

test('invalid registry identities, destinations and demonstration flags fail closed', async t => {
  const mutations = {
    duplicate: data => data.records.push(structuredClone(data.records[0])),
    mismatch: data => { data.records[0].barcode_number = '0'.repeat(39); },
    missingDemo: data => { delete data.records[0].demonstration; },
    wrongDemo: data => { data.records[0].demonstration = 'true'; },
    emptyCredentials: data => { data.records[0].record_url = 'https://@example.com/'; },
    credentials: data => { data.records[0].record_url = 'https://user:secret@example.com/'; },
    encodedHost: data => { data.records[0].record_url = 'https://%65xample.com/'; },
    scriptUrl: data => { data.records[0].record_url = 'javascript:alert(1)'; },
    zeroPort: data => { data.records[0].record_url = 'https://example.com:0/'; },
  };
  for (const [name, mutate] of Object.entries(mutations)) {
    await t.test(name, async t => {
      const data = structuredClone(registry);
      mutate(data);
      const { document } = await boot(t, { data, hash: '#id=' + record.id });
      assert.equal(document.getElementById('recordHeading').textContent, 'Registry unavailable');
      assert.equal(document.getElementById('registrySearch').disabled, true);
      assert.equal(document.querySelector('.launch'), null);
    });
  }
});

test('resolver configuration rejects insecure, credentialed, queried and incomplete bases', async t => {
  for (const base of ['http://example.com/', 'https://@example.com/', 'https://%65xample.com/', 'https://example.com/path', 'https://example.com/?', 'https://example.com/#', 'https://example.com/?x=1', 'https://example.com/#id=a']) {
    await t.test(base, async t => {
      const { document } = await boot(t, { config: { resolver_base: base } });
      assert.equal(document.getElementById('recordHeading').textContent, 'Registry unavailable');
      assert.equal(document.getElementById('registrySearch').disabled, true);
    });
  }
});

test('retired records retain their identity and show their status', async t => {
  const data = structuredClone(registry);
  data.records[0].status = 'retired';
  const { document } = await boot(t, { data, hash: '#id=' + record.id });
  assert.match(document.getElementById('recordPanel').textContent, /identity is retired/);
  assert.match(document.getElementById('recordPanel').textContent, new RegExp(record.id));
  assert.equal(document.querySelector('.launch').href, record.record_url);
});

test('pause only changes the exterior frame and a missing QR offers the permalink', async t => {
  const { document, window } = await boot(t, { hash: '#id=' + record.id });
  const pause = document.querySelector('.motion-toggle');
  const frame = document.querySelector('.label-frame');
  const qr = document.querySelector('.qr-sheet img');
  const sourceBefore = qr.src;
  pause.click();
  assert.equal(pause.getAttribute('aria-pressed'), 'true');
  assert.equal(frame.classList.contains('is-paused'), true);
  assert.equal(qr.src, sourceBefore);
  pause.click();
  assert.equal(pause.getAttribute('aria-pressed'), 'false');
  assert.equal(frame.classList.contains('is-paused'), false);
  qr.dispatchEvent(new window.Event('error'));
  assert.match(document.querySelector('.qr-sheet').textContent, /QR label is unavailable/);
  assert.ok(document.querySelector('.identity-fields a'));
});

test('a failed fetch reports an unavailable registry', async t => {
  const { document } = await boot(t, { failFetch: true });
  assert.equal(document.getElementById('recordHeading').textContent, 'Registry unavailable');
  assert.equal(document.getElementById('registrySearch').disabled, true);
});
