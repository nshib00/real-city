package ws

import (
	"bufio"
	"context"
	"crypto/sha1"
	"encoding/base64"
	"errors"
	"log/slog"
	"net"
	"net/http"
	"strings"
	"sync"
	"sync/atomic"

	jwtadapter "real-city/backend/internal/adapter/jwt"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/service"
	"real-city/backend/pkg/apperror"
)

const websocketGUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

type Gateway struct {
	tokens      *jwtadapter.Manager
	events      *service.EventBus
	log         *slog.Logger
	connections map[string]*Connection
	mu          sync.RWMutex
	seq         atomic.Uint64
	ctx         context.Context
	cancel      context.CancelFunc
}

func NewGateway(tokens *jwtadapter.Manager, events *service.EventBus, log *slog.Logger) *Gateway {
	ctx, cancel := context.WithCancel(context.Background())
	g := &Gateway{
		tokens:      tokens,
		events:      events,
		log:         log,
		connections: make(map[string]*Connection),
		ctx:         ctx,
		cancel:      cancel,
	}
	go g.forwardEvents()
	return g
}

func (g *Gateway) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	playerID, err := g.authenticate(r)
	if err != nil {
		g.log.Warn("ws.auth_failed", "event", "ws.auth_failed", "error", err.Error())
		http.Error(w, "unauthorized", http.StatusUnauthorized)
		return
	}
	conn, reader, err := upgrade(w, r)
	if err != nil {
		g.log.Warn("ws.upgrade_failed", "event", "ws.upgrade_failed", "player_id", playerID, "error", err.Error())
		return
	}
	client := NewConnection(conn, reader, playerID, 64)
	client.disconnectLog = func(reason string) {
		g.unregister(client)
		g.publishPresence(playerID, false)
		g.log.Info("ws.disconnect", "event", "ws.disconnect", "connection_id", client.ID(), "player_id", playerID, "reason", reason)
	}
	g.register(client)
	g.publishPresence(playerID, true)
	g.log.Info("ws.connect", "event", "ws.connect", "connection_id", client.ID(), "player_id", playerID)
	client.Enqueue(AckEnvelope(g.nextSeq(), map[string]any{"connection_id": client.ID(), "protocol_version": ProtocolVersion}))
	go client.WriteLoop()
	g.readLoop(client)
}

func (g *Gateway) Shutdown() {
	g.cancel()
	g.mu.RLock()
	defer g.mu.RUnlock()
	for _, conn := range g.connections {
		conn.Close("gateway_shutdown")
	}
}

func (g *Gateway) authenticate(r *http.Request) (player.ID, error) {
	header := r.Header.Get("Authorization")
	if header == "" {
		if token := r.URL.Query().Get("token"); token != "" {
			header = "Bearer " + token
		}
	}
	if header == "" {
		return "", apperror.New(apperror.Unauthorized, "websocket token is required")
	}
	return AuthenticateBearer(g.tokens, header)
}

func (g *Gateway) readLoop(client *Connection) {
	defer client.Close("read_loop_closed")
	for {
		command, err := client.ReadCommand()
		if err != nil {
			if !errors.Is(err, net.ErrClosed) {
				g.log.Warn("ws.read_failed", "event", "ws.read_failed", "connection_id", client.ID(), "player_id", client.PlayerID(), "error", err.Error())
			}
			return
		}
		client.Apply(command)
		g.log.Info("ws.command", "event", "ws.command", "connection_id", client.ID(), "player_id", client.PlayerID(), "command", command.Type, "chunks", len(command.ChunkIDs))
		client.Enqueue(AckEnvelope(g.nextSeq(), map[string]any{"command": command.Type, "chunk_ids": command.ChunkIDs}))
	}
}

func (g *Gateway) forwardEvents() {
	for event := range g.events.Subscribe(g.ctx) {
		envelope := EventEnvelope(event, g.nextSeq())
		g.mu.RLock()
		for _, conn := range g.connections {
			if conn.Matches(event.PlayerID, event.ChunkID, event.Alliance) {
				if !conn.Enqueue(envelope) {
					g.log.Warn("ws.message_dropped", "event", "ws.message_dropped", "connection_id", conn.ID(), "player_id", conn.PlayerID(), "message_type", envelope.Type)
				}
			}
		}
		g.mu.RUnlock()
	}
}

func (g *Gateway) register(client *Connection) {
	g.mu.Lock()
	defer g.mu.Unlock()
	g.connections[client.ID()] = client
}

func (g *Gateway) unregister(client *Connection) {
	g.mu.Lock()
	defer g.mu.Unlock()
	delete(g.connections, client.ID())
}

func (g *Gateway) publishPresence(playerID player.ID, online bool) {
	g.events.Publish(service.Event{
		Type:     service.EventPresenceChanged,
		PlayerID: playerID,
		Payload:  service.PresencePayload{PlayerID: playerID, Online: online},
	})
}

func (g *Gateway) nextSeq() uint64 {
	return g.seq.Add(1)
}

func upgrade(w http.ResponseWriter, r *http.Request) (net.Conn, *bufio.Reader, error) {
	if !strings.EqualFold(r.Header.Get("Upgrade"), "websocket") || !strings.Contains(strings.ToLower(r.Header.Get("Connection")), "upgrade") {
		http.Error(w, "websocket upgrade required", http.StatusBadRequest)
		return nil, nil, errors.New("websocket upgrade required")
	}
	key := r.Header.Get("Sec-WebSocket-Key")
	if key == "" {
		http.Error(w, "websocket key required", http.StatusBadRequest)
		return nil, nil, errors.New("websocket key required")
	}
	hijacker, ok := w.(http.Hijacker)
	if !ok {
		http.Error(w, "websocket unsupported", http.StatusInternalServerError)
		return nil, nil, errors.New("hijacker unsupported")
	}
	conn, readWriter, err := hijacker.Hijack()
	if err != nil {
		return nil, nil, err
	}
	accept := acceptKey(key)
	response := "HTTP/1.1 101 Switching Protocols\r\n" +
		"Upgrade: websocket\r\n" +
		"Connection: Upgrade\r\n" +
		"Sec-WebSocket-Accept: " + accept + "\r\n\r\n"
	if _, err := conn.Write([]byte(response)); err != nil {
		_ = conn.Close()
		return nil, nil, err
	}
	return conn, readWriter.Reader, nil
}

func acceptKey(key string) string {
	sum := sha1.Sum([]byte(strings.TrimSpace(key) + websocketGUID))
	return base64.StdEncoding.EncodeToString(sum[:])
}
