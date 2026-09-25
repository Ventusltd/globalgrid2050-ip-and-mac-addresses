(function () {
  'use strict';
  const search = document.getElementById('registrySearch');
  const status = document.getElementById('searchStatus');
  const list = document.getElementById('recordList');
  const panel = document.getElementById('recordPanel');
  const empty = document.getElementById('emptyResults');
  const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
  let records = [];
  let selectedId = null;
  let resolverBase;

  function element(tag, text, className) {
    const result = document.createElement(tag);
    if (text !== undefined) result.textContent = text;
    if (className) result.className = className;
    return result;
  }

  function safeUrl(value) {
    if (typeof value !== 'string' || /[\s\\\u0000-\u001f\u007f]/.test(value)) throw new Error('Invalid record URL');
    const authority = /^https:\/\/([^/?#]+)/i.exec(value)?.[1];
    if (!authority || authority.includes('@') || authority.includes('%')) throw new Error('Invalid record URL');
    const parsed = new URL(value);
    if (parsed.protocol !== 'https:' || parsed.username || parsed.password || parsed.port === '0') throw new Error('Invalid record URL');
    return parsed.href;
  }

  function validateConfig(config) {
    const base = safeUrl(config?.resolver_base);
    if (config.resolver_base.includes('?') || config.resolver_base.includes('#') || !config.resolver_base.endsWith('/')) throw new Error('Invalid resolver base');
    return base;
  }

  function validate(data) {
    if (data.schema !== 'globalgrid.identity.v1' || !Array.isArray(data.records)) throw new Error('Unsupported registry');
    const seen = new Set();
    data.records.forEach(record => {
      if (!record || !uuidPattern.test(record.id) || seen.has(record.id)) throw new Error('Invalid or duplicate identity');
      seen.add(record.id);
      if (!/^\d{39}$/.test(record.barcode_number) || BigInt('0x' + record.id.replaceAll('-', '')).toString().padStart(39, '0') !== record.barcode_number) throw new Error('Identity number mismatch');
      if (!['title', 'kind', 'created_at', 'updated_at'].every(key => typeof record[key] === 'string' && record[key].trim())) throw new Error('Incomplete identity');
      if (!['active', 'retired'].includes(record.status)) throw new Error('Invalid identity status');
      if (typeof record.demonstration !== 'boolean') throw new Error('Invalid demonstration flag');
      safeUrl(record.record_url);
    });
    return data.records;
  }

  function renderList() {
    const query = search.value.trim().toLocaleLowerCase();
    const matching = records.filter(record => [record.title, record.id, record.barcode_number].some(value => value.toLocaleLowerCase().includes(query)));
    const fragment = document.createDocumentFragment();
    matching.forEach(record => {
      const item = element('li');
      const link = element('a', undefined, 'record-link');
      link.href = '#id=' + record.id;
      if (record.id === selectedId) link.setAttribute('aria-current', 'true');
      link.append(element('span', record.title, 'record-name'));
      link.append(element('span', record.kind + ' · ' + record.status + (record.demonstration ? ' · demonstration' : ''), 'record-meta'));
      link.append(element('span', record.id, 'record-id'));
      item.append(link);
      fragment.append(item);
    });
    list.replaceChildren(fragment);
    empty.hidden = matching.length !== 0;
    status.textContent = matching.length + ' of ' + records.length + ' identities' + (query ? ' match your search.' : ' available.');
  }

  function panelMessage(title, message) {
    const heading = element('h2', title);
    heading.id = 'recordHeading';
    panel.replaceChildren(heading, element('p', message, 'muted'));
  }

  function showRecord(record) {
    const heading = element('h2', 'Identity record');
    heading.id = 'recordHeading';
    const badges = element('div', undefined, 'badges');
    badges.append(element('span', record.kind, 'badge'), element('span', record.status, 'badge'));
    if (record.demonstration) badges.append(element('span', 'Demonstration', 'badge badge-demo'));
    panel.replaceChildren(heading, badges, element('h3', record.title));
    if (record.demonstration) panel.append(element('p', 'Example entry for demonstrating the registry and its labels.', 'notice'));
    if (record.status === 'retired') panel.append(element('p', 'This identity is retired. Its permanent ID remains reserved and its record is retained.', 'notice'));
    const fields = element('dl', undefined, 'identity-fields');
    const address = new URL(resolverBase);
    address.hash = 'id=' + record.id;
    [
      ['Permanent ID · UUID v4', record.id],
      ['Barcode number · the same 128-bit identity', record.barcode_number],
      ['Created', record.created_at],
      ['Updated', record.updated_at],
    ].forEach(([label, value]) => fields.append(element('dt', label), element('dd', value)));
    const addressField = element('dd');
    const addressLink = element('a', address.href);
    addressLink.href = address.href;
    addressField.append(addressLink);
    fields.append(element('dt', 'Permanent record address'), addressField);
    const destination = element('dd');
    destination.append(element('span', safeUrl(record.record_url)));
    fields.append(element('dt', 'Linked record'), destination);
    panel.append(fields);
    const launch = element('a', 'Open linked record ↗', 'launch');
    launch.href = safeUrl(record.record_url);
    panel.append(launch);

    const labelArea = element('section', undefined, 'label-area');
    labelArea.append(element('h2', 'Scan this identity'));
    const frame = element('div', undefined, 'label-frame');
    const sheet = element('div', undefined, 'qr-sheet');
    const qr = element('img');
    const labelUrl = new URL('labels/' + record.id + '.svg', document.baseURI).href;
    qr.src = labelUrl;
    qr.alt = 'QR code for the permanent record address of ' + record.title;
    qr.width = 220;
    qr.height = 220;
    qr.addEventListener('error', () => {
      sheet.replaceChildren(element('p', 'The QR label is unavailable. Use the permanent record address above.', 'qr-caption'));
    });
    sheet.append(qr, element('p', record.id, 'qr-caption'));
    frame.append(sheet);
    const controls = element('div', undefined, 'label-controls');
    const pause = element('button', 'Pause frame animation', 'motion-toggle');
    pause.type = 'button';
    pause.setAttribute('aria-pressed', 'false');
    pause.addEventListener('click', () => {
      const paused = frame.classList.toggle('is-paused');
      pause.setAttribute('aria-pressed', String(paused));
      pause.textContent = paused ? 'Resume frame animation' : 'Pause frame animation';
    });
    const openLabel = element('a', 'Open QR label');
    openLabel.href = labelUrl;
    controls.append(pause, openLabel);
    labelArea.append(frame, controls, element('p', 'The QR code and white scanning area stay still. Scanning opens this identity, so you can review its linked record.', 'muted small'));
    panel.append(labelArea);
  }

  function resolve() {
    selectedId = null;
    if (!location.hash || location.hash === '#') {
      panelMessage('Choose a record', 'Select an identity from the list, or follow a scanned label to its permanent address.');
    } else {
      const match = /^#id=([^&]+)$/.exec(location.hash);
      const id = match ? match[1] : '';
      if (!uuidPattern.test(id)) {
        panelMessage('Malformed identity address', 'Use an address ending in #id= followed by a complete lowercase UUID v4. You can also search the registry above.');
      } else {
        const record = records.find(candidate => candidate.id === id);
        if (!record) panelMessage('Identity not found', 'This ID is not in the published registry. Check the label or search for the record above.');
        else {
          selectedId = id;
          showRecord(record);
        }
      }
    }
    renderList();
  }

  function loadJson(path) {
    return fetch(new URL(path, document.baseURI)).then(response => {
      if (!response.ok) throw new Error('Registry unavailable');
      return response.json();
    });
  }
  Promise.all([loadJson('data/registry.json'), loadJson('config.json')]).then(([data, config]) => {
    resolverBase = validateConfig(config);
    records = validate(data);
    search.disabled = false;
    search.addEventListener('input', renderList);
    window.addEventListener('hashchange', resolve);
    resolve();
  }).catch(error => {
    status.textContent = 'The registry could not be loaded or validated.';
    panelMessage('Registry unavailable', 'Try again later. Identity resolution requires a valid published registry.');
    console.error('Identity registry:', error.message);
  });
}());
