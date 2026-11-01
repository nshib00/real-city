"""Проверка сохранности оружия и сессии после сбоя хранилища на тестовом стенде."""
import argparse
import json
from pathlib import Path
import time
import urllib.error
import urllib.request
import smoke


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['before', 'database-down', 'after'])
    parser.add_argument('state', type=Path)
    args = parser.parse_args()
    if args.phase == 'before':
        nonce = str(time.time_ns())
        _, auth, _ = smoke.request('POST', '/api/v1/auth/register', {'email': f'outage-{nonce}@example.invalid', 'name': 'Outage'+nonce, 'password': 'TestOutage123!'})
        _, response, _ = smoke.request('GET', '/api/v1/economy/inventory', token=auth['access_token'])
        # The file contains a live test token: private and outside version control.
        args.state.touch(mode=0o600, exist_ok=False)
        args.state.write_text(json.dumps(dict(token=auth['access_token'], inventory=response['inventory']['items'])))
    else:
        state = json.loads(args.state.read_text())
        if args.phase == 'database-down':
            for endpoint in ['/ready', '/api/v1/economy/inventory']:
                req = urllib.request.Request(smoke.BASE + endpoint, headers={'Authorization': 'Bearer '+state['token']})
                try:
                    with urllib.request.urlopen(req, timeout=10):
                        raise AssertionError('Unavailable database returned success')
                except urllib.error.HTTPError as error:
                    assert error.code == 503, f'{endpoint}: expected 503, got {error.code}'
        else:
            _, response, _ = smoke.request('GET', '/api/v1/economy/inventory', token=state['token'])
            before = {i['resource']: i['amount'] for i in state['inventory']}
            after = {i['resource']: i['amount'] for i in response['inventory']['items']}
            assert after['throwing_knives'] == before['throwing_knives']
            assert after['coins'] == before['coins']
            smoke.websocket_handshake(state['token'])
    print('PASS storage outage: ' + args.phase)


if __name__ == '__main__':
    main()
