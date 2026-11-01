package service

import (
	"context"
	"log/slog"
	"testing"
	"time"

	"real-city/backend/internal/adapter/memory"
	"real-city/backend/internal/domain/chat"
	"real-city/backend/internal/domain/player"
)

func TestAdminModerationRequiresRoleAndPersistsReason(t *testing.T) {
	ctx := context.Background()
	players := memory.NewPlayerRepo()
	repo := memory.NewSocialRepo()
	for _, p := range []player.Player{{ID: "admin", Name: "Admin", Email: "admin@example.invalid", Role: player.RoleAdmin, Status: player.StatusActive}, {ID: "user", Name: "User", Email: "user@example.invalid", Role: player.RoleUser, Status: player.StatusActive}, {ID: "suspended", Name: "Suspended", Email: "suspended@example.invalid", Role: player.RoleAdmin, Status: player.StatusSuspended}} {
		if err := players.Create(ctx, p); err != nil {
			t.Fatal(err)
		}
	}
	chatService := NewChatService(repo, repo, slog.Default())
	admin := NewAdminService(NewPlayerService(players, memory.NewSessionStore(), slog.Default()), chatService)
	m := chat.Message{ID: "message", AuthorID: "user", Channel: chat.ChannelGlobal, Body: "https://example.invalid", Flagged: true, CreatedAt: time.Now().UTC()}
	if err := repo.AddMessage(ctx, m); err != nil {
		t.Fatal(err)
	}
	for _, actor := range []player.ID{"user", "suspended"} {
		if _, err := admin.Flagged(ctx, actor, 100); err == nil {
			t.Fatal("non-admin read moderation queue")
		}
		if err := admin.Moderate(ctx, actor, m.ID, "reject", "Причина"); err == nil {
			t.Fatal("non-admin moderated")
		}
	}
	if err := admin.Moderate(ctx, "admin", m.ID, "reject", ""); err == nil {
		t.Fatal("decision without reason accepted")
	}
	if err := admin.Moderate(ctx, "admin", m.ID, "reject", "Нарушение правил чата"); err != nil {
		t.Fatal(err)
	}
	queue, _ := admin.Flagged(ctx, "admin", 100)
	if len(queue) != 0 {
		t.Fatal("moderated message still pending")
	}
	messages, _ := chatService.List(ctx, "user", chat.ChannelGlobal, 100)
	if len(messages) != 1 || messages[0].Body != "Сообщение удалено модератором" {
		t.Fatal("rejected text still public")
	}
	audit, err := admin.Audit(ctx, "admin", 100)
	if err != nil || len(audit) != 1 || audit[0].Reason != "Нарушение правил чата" || audit[0].ActorID != "admin" {
		t.Fatalf("audit %+v %v", audit, err)
	}
	if err := admin.Moderate(ctx, "admin", "missing", "approve", "Проверено"); err == nil {
		t.Fatal("missing message approved")
	}
	audit, _ = admin.Audit(ctx, "admin", 100)
	if len(audit) != 1 {
		t.Fatal("failed moderation added audit")
	}
}
