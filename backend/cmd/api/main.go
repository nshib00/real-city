package main

import (
	"context"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"real-city/backend/pkg/config"
	"real-city/backend/pkg/logger"
)

func main() {
	cfg := config.Load()
	log := logger.New(cfg.AppEnv, cfg.Observability.LogLevel)
	slog.SetDefault(log)

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	application, err := newApp(cfg, log)
	if err != nil {
		log.Error("app.startup_failed", "event", "app.startup_failed", logger.ErrorAttr(err))
		os.Exit(1)
	}
	if err := application.run(ctx); err != nil {
		log.Error("app.failed", "event", "app.failed", logger.ErrorAttr(err))
		os.Exit(1)
	}
}
