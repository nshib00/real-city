package ws

import "real-city/backend/pkg/apperror"

type ErrorEnvelope struct {
	Type    string        `json:"type"`
	Code    apperror.Kind `json:"code"`
	Message string        `json:"message"`
}

func ErrorFrom(err *apperror.Error) ErrorEnvelope {
	return ErrorEnvelope{
		Type:    "error",
		Code:    err.Kind,
		Message: err.Message,
	}
}
