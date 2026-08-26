package player

import "testing"

func TestHashAndComparePassword(t *testing.T) {
	hash, err := HashPassword("frontier123")
	if err != nil {
		t.Fatalf("HashPassword() error = %v", err)
	}
	if hash == "frontier123" {
		t.Fatal("HashPassword() returned plaintext")
	}
	if err := ComparePassword(hash, "frontier123"); err != nil {
		t.Fatalf("ComparePassword() error = %v", err)
	}
	if err := ComparePassword(hash, "wrong12345"); err == nil {
		t.Fatal("ComparePassword() expected error for wrong password")
	}
}

func TestValidatePasswordPolicy(t *testing.T) {
	tests := []string{"short1", "longpassword", "1234567890"}
	for _, password := range tests {
		if err := ValidatePasswordPolicy(password); err == nil {
			t.Fatalf("ValidatePasswordPolicy(%q) expected error", password)
		}
	}
}
