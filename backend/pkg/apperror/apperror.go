package apperror

import "fmt"

type Kind string

const (
	BadRequest   Kind = "bad_request"
	Validation   Kind = "validation"
	Unauthorized Kind = "unauthorized"
	Forbidden    Kind = "forbidden"
	NotFound     Kind = "not_found"
	Conflict     Kind = "conflict"
	RateLimited  Kind = "rate_limited"
	Internal     Kind = "internal"
)

type Error struct {
	Kind    Kind              `json:"kind"`
	Message string            `json:"message"`
	Fields  map[string]string `json:"fields,omitempty"`
	Cause   error             `json:"-"`
}

func (e *Error) Error() string {
	if e.Cause == nil {
		return string(e.Kind) + ": " + e.Message
	}
	return fmt.Sprintf("%s: %s: %v", e.Kind, e.Message, e.Cause)
}

func (e *Error) Unwrap() error {
	return e.Cause
}

func New(kind Kind, message string) *Error {
	return &Error{Kind: kind, Message: message}
}

func Wrap(kind Kind, message string, cause error) *Error {
	return &Error{Kind: kind, Message: message, Cause: cause}
}

func WithFields(kind Kind, message string, fields map[string]string) *Error {
	return &Error{Kind: kind, Message: message, Fields: fields}
}
