package redis

import (
	"bufio"
	"context"
	"fmt"
	"net"
	"strconv"
	"strings"
	"time"
)

const (
	NamespaceCache    = "cache"
	NamespaceSession  = "session"
	NamespaceRealtime = "realtime"
)

type Client struct {
	addr     string
	password string
	db       int
	conn     net.Conn
}

func Dial(ctx context.Context, addr string, password string, db int) (*Client, error) {
	dialer := net.Dialer{Timeout: 3 * time.Second}
	conn, err := dialer.DialContext(ctx, "tcp", addr)
	if err != nil {
		return nil, err
	}
	client := &Client{addr: addr, password: password, db: db, conn: conn}
	if password != "" {
		if err := client.command("AUTH", password); err != nil {
			_ = conn.Close()
			return nil, err
		}
	}
	if db > 0 {
		if err := client.command("SELECT", strconv.Itoa(db)); err != nil {
			_ = conn.Close()
			return nil, err
		}
	}
	if err := client.Ping(); err != nil {
		_ = conn.Close()
		return nil, err
	}
	return client, nil
}

func (c *Client) Ping() error {
	return c.command("PING")
}

func (c *Client) Close() error {
	if c == nil || c.conn == nil {
		return nil
	}
	return c.conn.Close()
}

func (c *Client) Key(namespace string, parts ...string) string {
	return "real-city:" + namespace + ":" + strings.Join(parts, ":")
}

func (c *Client) command(args ...string) error {
	if c.conn == nil {
		return fmt.Errorf("redis connection is closed")
	}
	if _, err := fmt.Fprintf(c.conn, "*%d\r\n", len(args)); err != nil {
		return err
	}
	for _, arg := range args {
		if _, err := fmt.Fprintf(c.conn, "$%d\r\n%s\r\n", len(arg), arg); err != nil {
			return err
		}
	}
	line, err := bufio.NewReader(c.conn).ReadString('\n')
	if err != nil {
		return err
	}
	if strings.HasPrefix(line, "-") {
		return fmt.Errorf("redis error: %s", strings.TrimSpace(line[1:]))
	}
	return nil
}
