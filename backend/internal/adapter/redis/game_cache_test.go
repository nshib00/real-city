package redis

import (
	"bufio"
	"net"
	"testing"
)

func TestRedisCommandReadsFragmentedBulkValue(t *testing.T) {
	client, server := net.Pipe()
	defer client.Close()
	defer server.Close()
	go func() {
		reader := bufio.NewReader(server)
		for i := 0; i < 5; i++ {
			_, _ = reader.ReadString('\n')
		}
		_, _ = server.Write([]byte("$5\r\nhe"))
		_, _ = server.Write([]byte("llo\r\n"))
	}()
	value, err := redisCommand(client, bufio.NewReader(client), "GET", "key")
	if err != nil || string(value) != "hello" {
		t.Fatalf("value=%q err=%v", value, err)
	}
}
