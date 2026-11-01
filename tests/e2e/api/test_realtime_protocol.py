"""Проверки WS-клиента приёмки без запущенного игрового сервера."""
import json
import struct
import unittest

from gameplay_restart import Realtime


class MemorySocket:
    def __init__(self, incoming):
        self.incoming = bytearray(incoming)
        self.sent = bytearray()

    def recv(self, size):
        # Deliberately split reads, as a real TCP connection may do.
        size = min(size, 3)
        result = bytes(self.incoming[:size])
        del self.incoming[:size]
        return result

    def sendall(self, data):
        self.sent.extend(data)


def frame(opcode, body=b'', final=True):
    first = opcode | (0x80 if final else 0)
    if len(body) < 126:
        return bytes([first, len(body)]) + body
    return bytes([first, 126]) + struct.pack('!H', len(body)) + body


def client(data):
    result = Realtime.__new__(Realtime)
    result.socket = MemorySocket(data)
    return result


class RealtimeProtocolTest(unittest.TestCase):
    def test_ping_between_fragments_gets_masked_pong(self):
        ws = client(frame(1, b'{"type":', False) + frame(9, b'heartbeat') + frame(0, b'"ack"}'))
        self.assertEqual(ws.receive(), {'type': 'ack'})
        sent = ws.socket.sent
        self.assertEqual(sent[:2], bytes([0x8a, 0x80 | 9]))
        mask = sent[2:6]
        self.assertEqual(bytes(v ^ mask[i % 4] for i, v in enumerate(sent[6:])), b'heartbeat')

    def test_pong_is_not_a_game_event(self):
        ws = client(frame(10) + frame(1, b'{"type":"ack"}'))
        self.assertEqual(ws.receive()['type'], 'ack')

    def test_long_message_and_partial_reads(self):
        message = {'body': 'x' * 500}
        self.assertEqual(client(frame(1, json.dumps(message).encode())).receive(), message)

    def test_close_reports_disconnect(self):
        with self.assertRaisesRegex(AssertionError, 'closed by server'):
            client(frame(8)).receive()

    def test_invalid_control_fragment_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'control frame'):
            client(frame(9, b'', False)).receive()

    def test_unexpected_continuation_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'continuation'):
            client(frame(0, b'{}')).receive()

    def test_aggregate_message_size_is_limited(self):
        ws = client(bytes([0x81, 127]) + struct.pack('!Q', 2**20))
        with self.assertRaisesRegex(AssertionError, 'too large'):
            ws.receive()


if __name__ == '__main__':
    unittest.main()
