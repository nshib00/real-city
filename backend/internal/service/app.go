package service

import (
	"context"
	"log/slog"
)

type App struct {
	log *slog.Logger
}

func NewApp(log *slog.Logger) *App {
	return &App{log: log}
}

func (a *App) Start(ctx context.Context) error {
	a.log.Info("app.start", "event", "app.start")
	return ctx.Err()
}

func (a *App) Stop(ctx context.Context) error {
	a.log.Info("app.stop", "event", "app.stop")
	return ctx.Err()
}
