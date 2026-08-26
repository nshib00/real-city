package logger

import "testing"

func TestErrorAttr(t *testing.T) {
	attr := ErrorAttr(nil)
	if attr.Key != "error" {
		t.Fatalf("expected error key, got %q", attr.Key)
	}
}
