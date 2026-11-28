"""Local MBTI graph lab: python -m mbti_lab.server [--seed] [--demo]."""
import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .data import TYPES, TRAITS, result
from lumi_core.graph.client import get_driver, database as configured_database
from lumi_core.graph.seeds import MBTI_SEED as SEED, MBTI_QUERY as QUERY, trait_rows

ROOT = Path(__file__).resolve().parent




def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', action='store_true')
    parser.add_argument('--demo', action='store_true', help='Use example data without Neo4j')
    parser.add_argument('--port', type=int, default=8016)
    args = parser.parse_args()
    driver = None
    database = None
    if args.demo and args.seed:
        parser.error('--seed requires Neo4j mode')
    if not args.demo:
        database = configured_database()
        driver = get_driver()
        if args.seed:
            rows = trait_rows()
            driver.execute_query(SEED, rows=rows, database_=database)
            print(f'Seeded 16 types into {database}', flush=True)

    class Handler(BaseHTTPRequestHandler):
        def send_json(self, payload, status=200):
            data = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = urlparse(self.path).path
            if path == '/api/health':
                self.send_json({'mode': 'demo' if args.demo else 'neo4j'})
            elif path.startswith('/api/result/'):
                code = path.rsplit('/', 1)[-1].upper()
                if code not in TYPES:
                    self.send_json({'error': '올바른 유형을 선택해주세요.'}, 400)
                    return
                payload = result(code)
                if driver:
                    try:
                        records, _, _ = driver.execute_query(QUERY, code=code, database_=database,
                                                             routing_='r')
                        traits = {r['id']: r.data() for r in records}
                        if set(traits) != set(code):
                            self.send_json({'error': '실습 데이터가 없습니다. --seed로 실행해주세요.'}, 409)
                            return
                        payload['traits'] = [traits[key] for key in code]
                        for node in payload['nodes']:
                            if node['kind'] == 'trait':
                                node['label'] = traits[node['id']]['title']
                            elif node['kind'] == 'tip':
                                node['label'] = traits[node['id'][4:]]['tip']
                    except Exception:
                        self.send_json({'error': 'Neo4j 조회에 실패했습니다. 서버 연결을 확인해주세요.'}, 503)
                        return
                payload['mode'] = 'demo' if args.demo else 'neo4j'
                self.send_json(payload)
            elif path in ('/', '/index.html'):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write((ROOT / 'index.html').read_bytes())
            else:
                self.send_json({'error': 'Not found'}, 404)

    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'http://127.0.0.1:{args.port} — {"DEMO" if args.demo else "NEO4J"}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if driver:
            driver.close()


if __name__ == '__main__':
    main()
