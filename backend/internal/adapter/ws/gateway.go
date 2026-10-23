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

var errInvalidUpgrade = errors.New("invalid websocket upgrade")

type Gateway struct {
	tokens       *jwtadapter.Manager
	events       *service.EventBus
	log          *slog.Logger
	connections  map[string]*Connection
	chunkSubs    map[string]map[string]*Connection
	privateSubs  map[player.ID]map[string]*Connection
	allianceSubs map[string]map[string]*Connection
	mu           sync.RWMutex
	seq          atomic.Uint64
	eventsSent   atomic.Uint64
	fanoutTotal  atomic.Uint64
	drops        atomic.Uint64
	transport    TransportMetrics
	ctx          context.Context
	cancel       context.CancelFunc
}

func NewGateway(tokens *jwtadapter.Manager, events *service.EventBus, log *slog.Logger) *Gateway {
	ctx, cancel := context.WithCancel(context.Background())
	g := &Gateway{
		tokens:       tokens,
		events:       events,
		log:          log,
		connections:  make(map[string]*Connection),
		chunkSubs:    make(map[string]map[string]*Connection),
		privateSubs:  make(map[player.ID]map[string]*Connection),
		allianceSubs: make(map[string]map[string]*Connection),
		ctx:          ctx,
		cancel:       cancel,
	}
	go g.forwardEvents()
	return g
}

func (g *Gateway) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	playerID, err := g.authenticate(r)
	if err != nil {
		g.transport.upgradeAuthFailures.Add(1)
		g.log.Warn("ws.auth_failed", "event", "ws.auth_failed", "error", err.Error())
		http.Error(w, "unauthorized", http.StatusUnauthorized)
		return
	}
	conn, reader, err := upgrade(w, r)
	if err != nil {
		if errors.Is(err, errInvalidUpgrade) {
			g.transport.upgradeHandshakeFailures.Add(1)
		} else {
			g.transport.upgradeTransportFailures.Add(1)
		}
		g.log.Warn("ws.upgrade_failed", "event", "ws.upgrade_failed", "player_id", playerID, "error", err.Error())
		return
	}
	g.transport.upgradesOK.Add(1)
	client := NewConnection(conn, reader, playerID, 64)
	client.transport = &g.transport
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
	connections := connectionSlice(g.connections)
	g.mu.RUnlock()
	for _, conn := range connections {
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
		before := client.Subscriptions()
		client.Apply(command)
		after := client.Subscriptions()
		g.updateIndexes(client, before, after)
		g.log.Info("ws.command", "event", "ws.command", "connection_id", client.ID(), "player_id", client.PlayerID(), "command", command.Type, "chunks", len(command.ChunkIDs))
		client.Enqueue(AckEnvelope(g.nextSeq(), map[string]any{"command": command.Type, "chunk_ids": command.ChunkIDs}))
	}
}

func (g *Gateway) forwardEvents() {
	for event := range g.events.Subscribe(g.ctx) {
		envelope := EventEnvelope(event, g.nextSeq())
		targets := g.targetConnections(event)
		g.eventsSent.Add(1)
		g.fanoutTotal.Add(uint64(len(targets)))
		g.transport.ObserveFanout(len(targets))
		for _, conn := range targets {
			if !conn.Enqueue(envelope) {
				g.drops.Add(1)
				g.log.Warn("ws.message_dropped", "event", "ws.message_dropped", "connection_id", conn.ID(), "player_id", conn.PlayerID(), "message_type", envelope.Type)
			}
		}
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
	g.removeIndexedLocked(client, client.Subscriptions())
}

func (g *Gateway) updateIndexes(client *Connection, before SubscriptionSet, after SubscriptionSet) {
	g.mu.Lock()
	defer g.mu.Unlock()
	g.removeIndexedLocked(client, before)
	g.addIndexedLocked(client, after)
}

func (g *Gateway) addIndexedLocked(client *Connection, subs SubscriptionSet) {
	for _, chunkID := range subs.ChunkIDs() {
		addConnectionIndex(g.chunkSubs, chunkID, client)
	}
	if subs.Private() {
		if _, ok := g.privateSubs[client.PlayerID()]; !ok {
			g.privateSubs[client.PlayerID()] = make(map[string]*Connection)
		}
		g.privateSubs[client.PlayerID()][client.ID()] = client
	}
	if alliance := subs.AllianceChannel(); alliance != "" {
		addConnectionIndex(g.allianceSubs, alliance, client)
	}
}

func (g *Gateway) removeIndexedLocked(client *Connection, subs SubscriptionSet) {
	for _, chunkID := range subs.ChunkIDs() {
		removeConnectionIndex(g.chunkSubs, chunkID, client.ID())
	}
	if subs.Private() {
		if conns, ok := g.privateSubs[client.PlayerID()]; ok {
			delete(conns, client.ID())
			if len(conns) == 0 {
				delete(g.privateSubs, client.PlayerID())
			}
		}
	}
	if alliance := subs.AllianceChannel(); alliance != "" {
		removeConnectionIndex(g.allianceSubs, alliance, client.ID())
	}
}

func (g *Gateway) targetConnections(event service.Event) []*Connection {
	g.mu.RLock()
	defer g.mu.RUnlock()
	if event.ChunkID == "" && event.PlayerID == "" && event.Alliance == "" {
		return connectionSlice(g.connections)
	}
	targets := make(map[string]*Connection)
	for id, conn := range g.chunkSubs[event.ChunkID] {
		targets[id] = conn
	}
	for id, conn := range g.privateSubs[event.PlayerID] {
		targets[id] = conn
	}
	for id, conn := range g.allianceSubs[event.Alliance] {
		targets[id] = conn
	}
	return connectionSlice(targets)
}

type Stats struct {
	Connections           int
	ChunkSubscriptions    int
	PrivateSubscriptions  int
	AllianceSubscriptions int
	EventsSent            uint64
	FanoutTotal           uint64
	Drops                 uint64
	Transport             TransportStats
}

func (g *Gateway) Stats() Stats {
	g.mu.RLock()
	defer g.mu.RUnlock()
	transport := g.transport.Snapshot()
	for _, conn := range g.connections {
		transport.SendQueueDepth += len(conn.send)
		transport.SendQueueCapacity += cap(conn.send)
	}
	return Stats{
		Connections:           len(g.connections),
		ChunkSubscriptions:    indexedSubscriptionCount(g.chunkSubs),
		PrivateSubscriptions:  indexedSubscriptionCount(g.privateSubs),
		AllianceSubscriptions: indexedSubscriptionCount(g.allianceSubs),
		EventsSent:            g.eventsSent.Load(),
		FanoutTotal:           g.fanoutTotal.Load(),
		Drops:                 g.drops.Load(),
		Transport:             transport,
	}
}

func addConnectionIndex[K comparable](index map[K]map[string]*Connection, key K, conn *Connection) {
	if _, ok := index[key]; !ok {
		index[key] = make(map[string]*Connection)
	}
	index[key][conn.ID()] = conn
}

func removeConnectionIndex[K comparable](index map[K]map[string]*Connection, key K, connectionID string) {
	if conns, ok := index[key]; ok {
		delete(conns, connectionID)
		if len(conns) == 0 {
			delete(index, key)
		}
	}
}

func indexedSubscriptionCount[K comparable](index map[K]map[string]*Connection) int {
	total := 0
	for _, conns := range index {
		total += len(conns)
	}
	return total
}

func connectionSlice(connections map[string]*Connection) []*Connection {
	items := make([]*Connection, 0, len(connections))
	for _, conn := range connections {
		items = append(items, conn)
	}
	return items
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
		return nil, nil, errInvalidUpgrade
	}
	key := r.Header.Get("Sec-WebSocket-Key")
	if key == "" {
		http.Error(w, "websocket key required", http.StatusBadRequest)
		return nil, nil, errInvalidUpgrade
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
