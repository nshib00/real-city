"""Двухэтапная приёмка общей карты и социальных данных при рестарте API/worker."""
import argparse
import json
import os
from pathlib import Path
import secrets
import socket
import ssl
import struct
import time
import urllib.parse
import urllib.error
import smoke


def call(method, path, body=None, token=None, key=None):
    return smoke.request(method, '/api/v1' + path, body, token, key)[1]


def inventory(token):
    return {v['resource']: v['amount'] for v in call('GET', '/economy/inventory', token=token)['inventory']['items']}


class Realtime:
    def __init__(self, token):
        url = urllib.parse.urlsplit(smoke.BASE)
        self.socket = socket.create_connection((url.hostname, url.port or (443 if url.scheme == 'https' else 80)), timeout=10)
        if url.scheme == 'https':
            self.socket = ssl.create_default_context().wrap_socket(self.socket, server_hostname=url.hostname)
        self.socket.settimeout(10)
        key = secrets.token_bytes(16)
        import base64
        self.socket.sendall((f'GET /api/v1/realtime HTTP/1.1\r\nHost: {url.netloc}\r\nAuthorization: Bearer {token}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {base64.b64encode(key).decode()}\r\nSec-WebSocket-Version: 13\r\n\r\n').encode())
        header = b''
        while not header.endswith(b'\r\n\r\n'):
            header += self.exact(1)
        assert b' 101 ' in header.split(b'\r\n')[0]
        self.send({'type': 'subscribe', 'private': True, 'chunk_ids': []})
        while True:
            event = self.receive()
            if event['type'] == 'ack' and event.get('payload', {}).get('command') == 'subscribe':
                break

    def exact(self, n):
        data = b''
        while len(data) < n:
            chunk = self.socket.recv(n-len(data))
            if not chunk:
                raise AssertionError('WebSocket disconnected')
            data += chunk
        return data

    def send(self, obj):
        self.send_frame(1, json.dumps(obj).encode())

    def send_frame(self, opcode, body):
        mask = secrets.token_bytes(4)
        size = len(body)
        if size < 126:
            header = bytes([0x80 | opcode, 0x80 | size])
        elif size < 65536:
            header = bytes([0x80 | opcode, 0x80 | 126]) + struct.pack('!H', size)
        else:
            header = bytes([0x80 | opcode, 0x80 | 127]) + struct.pack('!Q', size)
        self.socket.sendall(header + mask + bytes(v ^ mask[i % 4] for i, v in enumerate(body)))

    def receive(self):
        fragments = bytearray()
        fragmented = False
        while True:
            first, length = self.exact(2)
            opcode, final = first & 15, bool(first & 0x80)
            assert first & 0x70 == 0 and length & 0x80 == 0, 'invalid server frame'
            size = length & 127
            if size == 126:
                size = struct.unpack('!H', self.exact(2))[0]
            elif size == 127:
                size = struct.unpack('!Q', self.exact(8))[0]
            if opcode >= 8:
                assert final and size <= 125, 'invalid control frame'
                data = self.exact(size)
                if opcode == 8:
                    raise AssertionError('WebSocket closed by server')
                if opcode == 9:
                    self.send_frame(10, data)
                else:
                    assert opcode == 10, 'unexpected control opcode'
                continue
            assert opcode == (0 if fragmented else 1), 'expected JSON text/continuation frame'
            assert len(fragments) + size < 2**20, 'WebSocket message too large'
            fragments.extend(self.exact(size))
            if final:
                return json.loads(fragments)
            fragmented = True

    def wait_message(self, message_id):
        for _ in range(100):
            event = self.receive()
            if event['type'] == 'chat.message.created' and event.get('payload', {}).get('id') == message_id:
                return
        raise AssertionError('chat event was not delivered')

    def close(self):
        self.socket.close()


def wait_api():
    deadline = time.monotonic() + 60
    while True:
        try:
            smoke.request('GET', '/health')
            return
        except (OSError, AssertionError) as error:
            if time.monotonic() >= deadline:
                raise AssertionError('API did not become ready') from error
            time.sleep(1)


def prepare(path):
    wait_api()
    state = smoke.main()
    token, rival = state['token'], state['rival_token']
    profile = call('POST', '/alliances', {'name': 'Приёмка ' + state['nonce']}, token)['profile']
    state['alliance_id'] = profile['alliance']['id']
    invite = call('POST', '/alliances/invites', {'player_id': state['rival_id']}, token, 'invite-' + state['nonce'])['invite']
    call('PATCH', '/alliances/invites/' + invite['id'], {'accept': True}, rival)
    ws = Realtime(rival)
    try:
        message = call('POST', '/chat/messages', {'channel': 'alliance', 'body': 'Сохранить после рестарта'}, token)['message']
        state['message_id'] = message['id']
        ws.wait_message(message['id'])
    finally:
        ws.close()
    messages = call('GET', '/chat/messages?channel=alliance', token=rival)
    assert messages['read_state']['unread'] >= 1
    call('PATCH', '/chat/read', {'channel': 'alliance', 'message_id': message['id']}, rival)
    call('POST', '/alliances/treasury/donations', {'resource': 'coins', 'amount': 1}, token)
    # Reserve a starting weapon, leave the open order across restart.
    state['before_knives'] = inventory(token)['throwing_knives']
    order = call('POST', '/market/orders', {'side': 'sell', 'resource': 'throwing_knives', 'amount': 2, 'price': 10}, token, 'market-' + state['nonce'])['order']
    state['order_id'] = order['id']
    assert inventory(token)['throwing_knives'] == state['before_knives'] - 2
    # Repair must finish by worker, without a client-completion command.
    quote = call('GET', '/buildings/' + state['target_id'] + '/repair', token=rival)['repair']
    before = inventory(rival)
    for cost in quote['cost']:
        assert before.get(cost['resource'], 0) >= cost['amount'], 'repair fixture has insufficient resources'
    workers = before.get('population', 0)
    assert workers >= quote['workers']
    call('PATCH', '/buildings/' + state['target_id'], {'action': 'repair'}, rival)
    pending = call('GET', '/buildings/' + state['target_id'] + '/repair', token=rival)['repair']
    assert pending['job']['status'] == 'pending'
    state['repair_due_at'] = pending['job']['due_at']
    state['workers_before'] = workers
    state['repaired_max_health'] = call('GET', '/buildings/' + state['target_id'], token=rival)['building']['max_health']
    # No tokens in console; the temporary checkpoint belongs to its creator.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as out:
        json.dump(state, out)
    print('PASS prepare: common map, direct attack, alliance, WS chat, read cursor, treasury, market reserve, repair queue')


def verify(path):
    wait_api()
    state = json.loads(Path(path).read_text())
    token, rival = state['token'], state['rival_token']
    for current in (token, rival):
        assert call('GET', '/alliances/me', token=current)['profile']['alliance']['id'] == state['alliance_id']
    profile = call('GET', '/alliances/me', token=token)['profile']
    assert any(v['kind'] == 'donation' and v['amount'] == 1 for v in profile['treasury'])
    history = call('GET', '/chat/messages?channel=alliance', token=rival)
    assert any(v['id'] == state['message_id'] for v in history['messages'])
    assert history['read_state']['unread'] == 0
    assert inventory(token)['throwing_knives'] == state['before_knives'] - 2
    call('DELETE', '/market/orders/' + state['order_id'], token=token)
    assert inventory(token)['throwing_knives'] == state['before_knives']
    try:
        call('DELETE', '/market/orders/' + state['order_id'], token=token)
        raise AssertionError('duplicate cancellation accepted')
    except AssertionError as error:
        assert 'HTTP 409' in str(error), str(error)
    assert inventory(token)['throwing_knives'] == state['before_knives']
    deadline = time.monotonic() + 120
    while call('GET', '/buildings/' + state['target_id'] + '/repair', token=rival)['repair'].get('job'):
        assert time.monotonic() < deadline, 'worker did not finish repair after restart'
        time.sleep(1)
    restored = call('GET', '/buildings/' + state['target_id'], token=rival)['building']
    assert restored['health'] == state['repaired_max_health']
    assert inventory(rival)['population'] == state['workers_before']
    call('DELETE', '/alliances/members/' + state['rival_id'], token=token)
    try:
        call('GET', '/chat/messages?channel=alliance', token=rival)
        raise AssertionError('kicked member retained chat access')
    except AssertionError as error:
        assert 'HTTP 403' in str(error), str(error)
    call('DELETE', '/alliances/me', token=token)
    assert call('GET', '/alliances/me', token=token)['profile']['alliance'] is None
    print('PASS restart: map/social persistence, cursor, treasury, exactly-once refund, worker repair, kick/access revocation, leave')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare')
    group.add_argument('--verify')
    args = parser.parse_args()
    if args.prepare:
        prepare(args.prepare)
    else:
        verify(args.verify)
