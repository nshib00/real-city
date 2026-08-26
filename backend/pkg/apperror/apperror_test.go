package apperror

import "testing"

func TestErrorStringIncludesKind(t *testing.T) {
	err := New(NotFound, "tile not found")
	if got := err.Error(); got != "not_found: tile not found" {
		t.Fatalf("unexpected error string: %q", got)
	}
}
