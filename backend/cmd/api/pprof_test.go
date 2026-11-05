package main

import "testing"

func TestPprofOnlyBindsLoopback(t *testing.T) {
	for _, addr := range []string{"127.0.0.1:6060", "[::1]:6060", "localhost:6060"} {
		if !loopbackAddress(addr) {
			t.Errorf("rejected %q", addr)
		}
	}
	for _, addr := range []string{":6060", "0.0.0.0:6060", "192.168.1.2:6060", "example.com:6060"} {
		if loopbackAddress(addr) {
			t.Errorf("accepted %q", addr)
		}
	}
}
