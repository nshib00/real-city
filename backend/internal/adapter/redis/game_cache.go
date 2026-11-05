package redis

import (
	"bufio"
	"context"
	"errors"
	"fmt"
	"io"
	"net"
	"strconv"
	"strings"
	"sync/atomic"
	"time"
)

// GameCache uses independent bounded connections so concurrent HTTP requests never
// interleave RESP commands. Redis is optional: callers may fall back to SQL.
type GameCache struct {
	Addr       string
	Password   string
	DB         int
	retryAfter atomic.Int64
}

func (c *GameCache) Get(ctx context.Context, key string) ([]byte, bool, error) {
	value, err := c.query(ctx, "GET", key)
	return value, value != nil, err
}

func (c *GameCache) Set(ctx context.Context, key string, value []byte, ttl time.Duration) error {
	if ttl <= 0 {
		return errors.New("cache TTL must be positive")
	}
	_, err := c.query(ctx, "SET", key, string(value), "PX", strconv.FormatInt(ttl.Milliseconds(), 10))
	return err
}

func (c *GameCache) Delete(ctx context.Context, key string) error {
	_, err := c.query(ctx, "DEL", key)
	return err
}

func (c *GameCache) GetMany(ctx context.Context, keys []string) (map[string][]byte, error) {
	result := make(map[string][]byte)
	if len(keys) == 0 { return result, nil }
	if len(keys) > 64 { return nil, errors.New("too many Redis keys") }
	conn, reader, err := c.connect(ctx)
	if err != nil { return nil, err }
	defer conn.Close()
	args := append([]string{"MGET"}, keys...)
	if err := writeRedisCommand(conn, args...); err != nil { return nil, err }
	line, err := reader.ReadString('\n')
	if err != nil { return nil, err }
	count, err := strconv.Atoi(strings.TrimSpace(strings.TrimPrefix(line, "*")))
	if err != nil || !strings.HasPrefix(line, "*") || count != len(keys) { return nil, errors.New("invalid Redis array response") }
	for _, key := range keys {
		value, err := readRedisValue(reader)
		if err != nil { return nil, err }
		if value != nil { result[key] = value }
	}
	return result, nil
}

func (c *GameCache) query(ctx context.Context, args ...string) ([]byte, error) {
	conn, reader, err := c.connect(ctx)
	if err != nil { return nil, err }
	defer conn.Close()
	return redisCommand(conn, reader, args...)
}

func (c *GameCache) connect(ctx context.Context) (net.Conn, *bufio.Reader, error) {
	if time.Now().UnixNano() < c.retryAfter.Load() {
		return nil, nil, errors.New("Redis cache temporarily unavailable")
	}
	dialer := net.Dialer{Timeout: 200 * time.Millisecond}
	conn, err := dialer.DialContext(ctx, "tcp", c.Addr)
	if err != nil {
		c.retryAfter.Store(time.Now().Add(5 * time.Second).UnixNano())
		return nil, nil, err
	}
	deadline := time.Now().Add(500 * time.Millisecond)
	if d, ok := ctx.Deadline(); ok && d.Before(deadline) {
		deadline = d
	}
	if err := conn.SetDeadline(deadline); err != nil {
		conn.Close()
		return nil, nil, err
	}
	reader := bufio.NewReader(conn)
	if c.Password != "" {
		if _, err := redisCommand(conn, reader, "AUTH", c.Password); err != nil {
			conn.Close()
			return nil, nil, err
		}
	}
	if c.DB != 0 {
		if _, err := redisCommand(conn, reader, "SELECT", strconv.Itoa(c.DB)); err != nil {
			conn.Close()
			return nil, nil, err
		}
	}
	return conn, reader, nil
}

func redisCommand(conn net.Conn, reader *bufio.Reader, args ...string) ([]byte, error) {
	if err := writeRedisCommand(conn, args...); err != nil { return nil, err }
	return readRedisValue(reader)
}

func writeRedisCommand(conn net.Conn, args ...string) error {
	var b strings.Builder
	fmt.Fprintf(&b, "*%d\r\n", len(args))
	for _, arg := range args {
		fmt.Fprintf(&b, "$%d\r\n%s\r\n", len(arg), arg)
	}
	if _, err := conn.Write([]byte(b.String())); err != nil {
		return err
	}
	return nil
}

func readRedisValue(reader *bufio.Reader) ([]byte, error) {
	line, err := reader.ReadString('\n')
	if err != nil {
		return nil, err
	}
	if len(line) < 3 {
		return nil, errors.New("invalid Redis response")
	}
	switch line[0] {
	case '-':
		return nil, errors.New(strings.TrimSpace(line[1:]))
	case '+', ':':
		return []byte(strings.TrimSpace(line[1:])), nil
	case '$':
		size, err := strconv.Atoi(strings.TrimSpace(line[1:]))
		if err != nil {
			return nil, err
		}
		if size == -1 {
			return nil, nil
		}
		if size < 0 || size > 4<<20 {
			return nil, errors.New("invalid Redis bulk length")
		}
		value := make([]byte, size+2)
		if _, err := io.ReadFull(reader, value); err != nil {
			return nil, err
		}
		if string(value[size:]) != "\r\n" {
			return nil, errors.New("invalid Redis bulk terminator")
		}
		return value[:size], nil
	default:
		return nil, errors.New("unsupported Redis response")
	}
}
