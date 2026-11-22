"""Integration check using a temporary local demo server."""
import json
import subprocess
import sys
import time
import urllib.request
from .data import TYPES


def main():
    process = subprocess.Popen([sys.executable, '-m', 'mbti_lab.server', '--demo',
                                '--port', '8017'], stdout=subprocess.DEVNULL)
    try:
        base = 'http://127.0.0.1:8017'
        for attempt in range(30):
            try:
                with urllib.request.urlopen(base, timeout=2) as response:
                    assert response.status == 200
                break
            except OSError:
                if attempt == 29:
                    raise
                time.sleep(.2)
        for code in TYPES:
            with urllib.request.urlopen(base + '/api/result/' + code, timeout=3) as response:
                data = json.load(response)
                assert data['type'] == code and len(data['traits']) == 4
                assert len(data['edges']) == 8 and data['mode'] == 'demo'
                assert len(data['interpretations']) == 10
                assert all(card['subject'] == code for card in data['interpretations'])
        print('PASS: page and all 16 result endpoints')
    finally:
        process.terminate()
        process.wait(timeout=5)


if __name__ == '__main__':
    main()
