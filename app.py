import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlsplit

CACHE = Path(os.environ.get('DATA_DIR', '/data')) / 'totals.json'
LOCK = threading.Lock()
STATIC = Path(__file__).parent / 'static' / 'index.html'

def now():
    return datetime.now(timezone.utc).isoformat()

def read_cache():
    try:
        data = json.loads(CACHE.read_text())
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    return {'languages': {}}

def count_cards(language):
    # No pagination parameters: TCGdex returns the full list.
    req = Request(f'https://api.tcgdex.net/v2/{language}/cards', headers={'User-Agent': 'PokemonCardTotals/0.1.0', 'Accept': 'application/json'})
    with urlopen(req, timeout=45) as response:
        cards = json.load(response)
    if not isinstance(cards, list) or not cards:
        raise ValueError('Source returned an empty or invalid card list')
    ids = set()
    for card in cards:
        if not isinstance(card, dict) or not isinstance(card.get('id'), str) or not card['id']:
            raise ValueError('Source returned an invalid card record')
        ids.add(card['id'])
    return len(ids)

def refresh():
    with LOCK:
        data = read_cache()
        data['last_attempt'] = now()
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {lang: pool.submit(count_cards, lang) for lang in ('en', 'ja')}
            for lang, future in futures.items():
                item = data['languages'].setdefault(lang, {})
                try:
                    total = future.result()
                    previous = item.get('total')
                    item.update(total=total, delta=total-previous if isinstance(previous, int) else None, updated_at=now(), error=None)
                except Exception:
                    item['error'] = 'Could not reach or validate TCGdex. Try refreshing again.'
        try:
            CACHE.parent.mkdir(parents=True, exist_ok=True)
            temporary = CACHE.with_suffix('.tmp')
            temporary.write_text(json.dumps(data))
            temporary.replace(CACHE)
        except OSError:
            data['warning'] = 'Could not save totals. Check the data volume permissions.'
        return data

class Handler(BaseHTTPRequestHandler):
    def send(self, status, content, kind):
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        if urlsplit(self.path).path == '/':
            self.send(200, STATIC.read_bytes(), 'text/html; charset=utf-8')
        elif self.path == '/api/totals':
            with LOCK:
                data = read_cache()
            self.send(200, json.dumps(data).encode(), 'application/json')
        elif self.path == '/health':
            self.send(200, b'ok', 'text/plain')
        else:
            self.send(404, b'Not found', 'text/plain')

    def do_POST(self):
        if self.path != '/api/refresh':
            self.send(404, b'Not found', 'text/plain')
            return
        # Browser cross-origin fetches cannot invoke a refresh without preflight.
        if self.headers.get('X-Widget-Refresh') != '1':
            self.send(400, b'Missing refresh header', 'text/plain')
            return
        self.send(200, json.dumps(refresh()).encode(), 'application/json')

if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', int(os.environ.get('PORT', '8080'))), Handler).serve_forever()
