package ws

import (
	"bufio"
	"crypto/rand"
	"encoding/binary"
	"encoding/json"
	"errors"
	"io"
	"net"
	"sync"
	"time"

	"real-city/backend/internal/domain/player"
)

const (
	opText  = 1
	opClose = 8
)

type Connection struct {
	id            string
	playerID      player.ID
	conn          net.Conn
	reader        *bufio.Reader
	send          chan Envelope
	subs          SubscriptionSet
	rate          *RateLimiter
	mu            sync.RWMutex
	closeOnce     sync.Once
	closed        chan struct{}
	disconnectLog func(reason string)
}

func NewConnection(conn net.Conn, reader *bufio.Reader, playerID player.ID, sendQueue int) *Connection {
	if sendQueue <= 0 {
		sendQueue = 64
	}
	return &Connection{
		id:       randomID(),
		playerID: playerID,
		conn:     conn,
		reader:   reader,
		send:     make(chan Envelope, sendQueue),
		subs:     NewSubscriptionSet(),
		rate:     NewRateLimiter(20, time.Second),
		closed:   make(chan struct{}),
	}
}

func (c *Connection) ID() string {
	return c.id
}

func (c *Connection) PlayerID() player.ID {
	return c.playerID
}

func (c *Connection) Enqueue(message Envelope) bool {
	select {
	case c.send <- message:
		return true
	default:
		c.Close("send_queue_full")
		return false
	}
}

func (c *Connection) Matches(eventPlayerID player.ID, chunkID string, alliance string) bool {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.subs.Matches(chunkID, string(eventPlayerID), alliance, string(c.playerID))
}

func (c *Connection) Apply(command ClientCommand) {
	c.mu.Lock()
	defer c.mu.Unlock()
	switch command.Type {
	case "subscribe":
		c.subs.SubscribeChunks(command.ChunkIDs)
		c.subs.SetPrivate(command.Private)
		c.subs.SetAlliance(command.AllianceChannel)
	case "unsubscribe":
		c.subs.UnsubscribeChunks(command.ChunkIDs)
	}
}

func (c *Connection) ReadCommand() (ClientCommand, error) {
	if !c.rate.Allow(time.Now()) {
		return ClientCommand{}, errors.New("rate limit exceeded")
	}
	opcode, data, err := readFrame(c.reader)
	if err != nil {
		return ClientCommand{}, err
	}
	if opcode == opClose {
		return ClientCommand{}, io.EOF
	}
	var command ClientCommand
	if err := json.Unmarshal(data, &command); err != nil {
		return ClientCommand{}, err
	}
	return command, nil
}

func (c *Connection) WriteLoop() {
	for {
		select {
		case message := <-c.send:
			data, err := json.Marshal(message)
			if err != nil {
				continue
			}
			_ = c.conn.SetWriteDeadline(time.Now().Add(5 * time.Second))
			if err := writeTextFrame(c.conn, data); err != nil {
				c.Close("write_failed")
				return
			}
		case <-c.closed:
			return
		}
	}
}

func (c *Connection) Close(reason string) {
	c.closeOnce.Do(func() {
		if c.disconnectLog != nil {
			c.disconnectLog(reason)
		}
		close(c.closed)
		_ = c.conn.Close()
	})
}

func readFrame(reader *bufio.Reader) (byte, []byte, error) {
	first, err := reader.ReadByte()
	if err != nil {
		return 0, nil, err
	}
	second, err := reader.ReadByte()
	if err != nil {
		return 0, nil, err
	}
	opcode := first & 0x0f
	masked := second&0x80 != 0
	length := uint64(second & 0x7f)
	switch length {
	case 126:
		var buf [2]byte
		if _, err := io.ReadFull(reader, buf[:]); err != nil {
			return 0, nil, err
		}
		length = uint64(binary.BigEndian.Uint16(buf[:]))
	case 127:
		var buf [8]byte
		if _, err := io.ReadFull(reader, buf[:]); err != nil {
			return 0, nil, err
		}
		length = binary.BigEndian.Uint64(buf[:])
	}
	var mask [4]byte
	if masked {
		if _, err := io.ReadFull(reader, mask[:]); err != nil {
			return 0, nil, err
		}
	}
	if length > 1<<20 {
		return 0, nil, errors.New("websocket frame too large")
	}
	payload := make([]byte, length)
	if _, err := io.ReadFull(reader, payload); err != nil {
		return 0, nil, err
	}
	if masked {
		for i := range payload {
			payload[i] ^= mask[i%4]
		}
	}
	return opcode, payload, nil
}

func writeTextFrame(writer io.Writer, payload []byte) error {
	header := []byte{0x80 | opText}
	switch {
	case len(payload) < 126:
		header = append(header, byte(len(payload)))
	case len(payload) <= 65535:
		header = append(header, 126, byte(len(payload)>>8), byte(len(payload)))
	default:
		header = append(header, 127)
		var buf [8]byte
		binary.BigEndian.PutUint64(buf[:], uint64(len(payload)))
		header = append(header, buf[:]...)
	}
	if _, err := writer.Write(header); err != nil {
		return err
	}
	_, err := writer.Write(payload)
	return err
}

func randomID() string {
	var b [8]byte
	if _, err := rand.Read(b[:]); err != nil {
		return uintToString(uint64(time.Now().UnixNano()))
	}
	return uintToString(binary.BigEndian.Uint64(b[:]))
}
