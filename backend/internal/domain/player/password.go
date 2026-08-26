package player

import (
	"unicode"

	"golang.org/x/crypto/bcrypt"
	"real-city/backend/pkg/apperror"
)

const (
	MinPasswordLength = 10
	bcryptCost        = 12
)

func ValidatePasswordPolicy(password string) error {
	if len(password) < MinPasswordLength {
		return apperror.WithFields(apperror.Validation, "password does not match policy", map[string]string{
			"password": "must be at least 10 characters",
		})
	}

	var hasLetter, hasNumber bool
	for _, char := range password {
		if unicode.IsLetter(char) {
			hasLetter = true
		}
		if unicode.IsNumber(char) {
			hasNumber = true
		}
	}
	if !hasLetter || !hasNumber {
		return apperror.WithFields(apperror.Validation, "password does not match policy", map[string]string{
			"password": "must include letters and numbers",
		})
	}
	return nil
}

func HashPassword(password string) (string, error) {
	if err := ValidatePasswordPolicy(password); err != nil {
		return "", err
	}
	hash, err := bcrypt.GenerateFromPassword([]byte(password), bcryptCost)
	if err != nil {
		return "", apperror.Wrap(apperror.Internal, "failed to hash password", err)
	}
	return string(hash), nil
}

func ComparePassword(hash string, password string) error {
	if err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password)); err != nil {
		return apperror.New(apperror.Unauthorized, "invalid email or password")
	}
	return nil
}
