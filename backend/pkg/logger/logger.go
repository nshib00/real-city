package logger

import (
	"context"
	"log/slog"
	"os"
)

func New(env string, level string) *slog.Logger {
	opts := &slog.HandlerOptions{Level: parseLevel(level)}
	if env == "production" {
		return slog.New(slog.NewJSONHandler(os.Stdout, opts))
	}
	return slog.New(slog.NewTextHandler(os.Stdout, opts))
}

func ErrorAttr(err error) slog.Attr {
	if err == nil {
		return slog.Any("error", nil)
	}
	return slog.String("error", err.Error())
}

func WithRequestID(ctx context.Context, log *slog.Logger) *slog.Logger {
	if requestID, ok := ctx.Value(requestIDKey{}).(string); ok && requestID != "" {
		return log.With("request_id", requestID)
	}
	return log
}

type requestIDKey struct{}

func ContextWithRequestID(ctx context.Context, requestID string) context.Context {
	return context.WithValue(ctx, requestIDKey{}, requestID)
}

func parseLevel(level string) slog.Level {
	switch level {
	case "debug":
		return slog.LevelDebug
	case "warn":
		return slog.LevelWarn
	case "error":
		return slog.LevelError
	default:
		return slog.LevelInfo
	}
}
