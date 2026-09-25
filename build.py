"""Build an allowlisted static resolver and scannable URL labels."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
from urllib.parse import urlsplit
from xml.sax.saxutils import escape
import registry
sys.path.insert(0, str(registry.ROOT / '.tools'))
from qrcodegen import QrCode

def label_svg(payload):
    qr = QrCode.encode_text(payload, QrCode.Ecc.MEDIUM)
    border = 4
    size = qr.get_size() + border * 2
    squares = ' '.join(f'M{x+border},{y+border}h1v1h-1z' for y in range(qr.get_size()) for x in range(qr.get_size()) if qr.get_module(x, y))
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size*8}" height="{size*8}" shape-rendering="crispEdges" role="img"><title>{escape(payload)}</title><rect width="100%" height="100%" fill="#fff"/><path d="{squares}" fill="#000"/></svg>\n'

def main():
    root = registry.ROOT
    data = registry.load(root / 'data/registry.json')
    config = json.loads((root / 'config.json').read_text())
    base = config['resolver_base']; registry.https(base)
    parts = urlsplit(base)
    registry.require(not parts.query and not parts.fragment and base.endswith('/'), 'Resolver base must end in / without query or fragment')
    out = root / '_site'
    expected = {'index.html','assets/app.js','assets/style.css','data/registry.json','data/kuiper-index.json','config.json','.nojekyll','build-receipt.json'} | {f"labels/{r['id']}.svg" for r in data['records']}
    unexpected = [str(p.relative_to(out)) for p in out.rglob('*') if p.is_file() and p.relative_to(out).as_posix() not in expected]
    registry.require(not unexpected, 'Unexpected files in build output: ' + ', '.join(unexpected))
    # Known output names only. No recursive deletion or unrelated file copies.
    for name in ('index.html', 'assets/app.js', 'assets/style.css', 'data/registry.json', 'config.json'):
        target = out / name; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, target)
    labels = out / 'labels'; labels.mkdir(exist_ok=True)
    for record in data['records']:
        (labels / f"{record['id']}.svg").write_text(label_svg(base + '#id=' + record['id']), encoding='utf-8', newline='\n')
    kuiper = {'schema': 'globalgrid.kuiper.identity-index.v1', 'authority': base, 'records': [
        {key: record[key] for key in ('id','title','kind','status','demonstration')} | {'resolver_url': base+'#id='+record['id'], 'record_url': record['record_url']}
        for record in data['records']]}
    (out / 'data/kuiper-index.json').write_text(json.dumps(kuiper, indent=2)+'\n', encoding='utf-8')
    (out / '.nojekyll').write_text('')
    receipt = {'schema': 'globalgrid.identity.build.v1', 'status': 'pass', 'records': len(data['records']), 'distinct_ids': len({r['id'] for r in data['records']}), 'events': len(data['events']), 'resolver_base': base,
        'files': {str(p.relative_to(out)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'build-receipt.json'}}
    (out / 'build-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))

if __name__ == '__main__': main()
