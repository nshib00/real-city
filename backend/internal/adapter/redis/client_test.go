package redis

import "testing"

func TestKeyUsesNamespace(t *testing.T) {
	client := &Client{}
	got := client.Key(NamespaceSession, "player-1")
	if got != "real-city:session:player-1" {
		t.Fatalf("unexpected key: %q", got)
	}
}
