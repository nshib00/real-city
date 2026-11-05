package ws

import (
	"bufio"
	"io"
	"log/slog"
	"net"
	"net/http"
	"net/http/httptest"
	"sync"
	"testing"
	"time"

	"real-city/backend/internal/domain/monster"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/service"
)

func TestGatewayCoalescesBurstMovementWithinChunk(t *testing.T) {
	bus := service.NewEventBus(16)
	gateway := NewGateway(nil, bus, slog.New(slog.NewTextHandler(io.Discard, nil)))
	defer gateway.Shutdown()
	for _, chunk := range []string{"dev-world:0:0", "dev-world:0:0", "dev-world:1:0"} {
		if err := bus.Publish(service.Event{Type: service.EventMonsterMoved, ChunkID: chunk, Payload: service.MonsterPayload{Monster: monster.Monster{ID: monster.ID("same")}}}); err != nil {
			t.Fatal(err)
		}
	}
	deadline := time.Now().Add(time.Second)
	for gateway.Stats().EventsSent < 2 && time.Now().Before(deadline) {
		time.Sleep(time.Millisecond)
	}
	stats := gateway.Stats()
	if stats.EventsSent != 2 || stats.Coalesced != 1 {
		t.Fatalf("movement stats: %+v", stats)
	}
}

func TestConnectionRepliesToPingAndKeepsReadingCommands(t *testing.T) {
	server, peer := net.Pipe()
	defer peer.Close()
	conn := NewConnection(server, bufio.NewReader(server), player.ID("ping-player"), 4)
	defer conn.Close("test")
	go conn.WriteLoop()
	commands := make(chan ClientCommand, 1)
	errors := make(chan error, 1)
	go func() {
		command, err := conn.ReadCommand()
		commands <- command
		errors <- err
	}()
	_ = peer.SetDeadline(time.Now().Add(time.Second))
	if err := writeFrame(peer, opPing, []byte("probe")); err != nil {
		t.Fatal(err)
	}
	opcode, payload, err := readFrame(bufio.NewReader(peer))
	if err != nil || opcode != opPong || string(payload) != "probe" {
		t.Fatalf("pong: opcode=%d payload=%q err=%v", opcode, payload, err)
	}
	if err := writeTextFrame(peer, []byte(`{"type":"subscribe","chunk_ids":["dev-world:0:0"]}`)); err != nil {
		t.Fatal(err)
	}
	if command, err := <-commands, <-errors; err != nil || command.Type != "subscribe" {
		t.Fatalf("command after ping: %+v, %v", command, err)
	}
}

func TestConnectionSendsHeartbeat(t *testing.T) {
	server, peer := net.Pipe()
	defer peer.Close()
	conn := NewConnection(server, bufio.NewReader(server), player.ID("heartbeat"), 2)
	conn.pingInterval = 10 * time.Millisecond
	defer conn.Close("test")
	go conn.WriteLoop()
	_ = peer.SetReadDeadline(time.Now().Add(time.Second))
	opcode, _, err := readFrame(bufio.NewReader(peer))
	if err != nil || opcode != opPing {
		t.Fatalf("heartbeat opcode=%d err=%v", opcode, err)
	}
}

func TestGatewayUpgradeFailureMetric(t *testing.T) {
	gateway := NewGateway(nil, service.NewEventBus(1), slog.New(slog.NewTextHandler(io.Discard, nil)))
	defer gateway.Shutdown()
	response := httptest.NewRecorder()
	gateway.ServeHTTP(response, httptest.NewRequest(http.MethodGet, "/api/v1/realtime?token=private", nil))
	if response.Code != http.StatusUnauthorized {
		t.Fatalf("status = %d", response.Code)
	}
	stats := gateway.Stats()
	if stats.Transport.UpgradeAuthFailures != 1 || stats.Transport.UpgradesOK != 0 {
		t.Fatalf("upgrade stats = %+v", stats.Transport)
	}
}

func TestGatewaySubscribesBeforeReturning(t *testing.T) {
	bus := service.NewEventBus(1)
	gateway := NewGateway(nil, bus, slog.New(slog.NewTextHandler(io.Discard, nil)))
	defer gateway.Shutdown()
	if err := bus.Publish(service.Event{Type: service.EventTileChanged}); err != nil {
		t.Fatal(err)
	}
	deadline := time.Now().Add(time.Second)
	for gateway.Stats().EventsSent == 0 && time.Now().Before(deadline) {
		time.Sleep(time.Millisecond)
	}
	if gateway.Stats().EventsSent != 1 {
		t.Fatal("event published immediately after startup was lost")
	}
}

func TestConnectionSequencesOnlyDeliveredEvents(t *testing.T) {
	firstSocket, firstPeer := net.Pipe()
	secondSocket, secondPeer := net.Pipe()
	defer firstPeer.Close()
	defer secondPeer.Close()
	first := NewConnection(firstSocket, nil, player.ID("p1"), 8)
	second := NewConnection(secondSocket, nil, player.ID("p2"), 8)
	defer first.Close("test")
	defer second.Close("test")
	if !first.Enqueue(AckEnvelope(0, nil)) || !first.EnqueueEvent(Envelope{Type: "monster.moved", Seq: 99}) ||
		!first.Enqueue(AckEnvelope(0, nil)) || !first.EnqueueEvent(Envelope{Type: "world.building.updated", Seq: 100}) ||
		!second.EnqueueEvent(Envelope{Type: "monster.moved", Seq: 101}) {
		t.Fatal("failed to enqueue test messages")
	}
	for index, want := range []uint64{0, 1, 0, 2} {
		if got := (<-first.send).Seq; got != want {
			t.Fatalf("first connection message %d seq = %d, want %d", index, got, want)
		}
	}
	if got := (<-second.send).Seq; got != 1 {
		t.Fatalf("second connection seq = %d, want 1", got)
	}
}

func TestUnsubscribeRemovesOldChunkFromGatewayIndex(t *testing.T) {
	gateway := NewGateway(nil, service.NewEventBus(2), slog.New(slog.NewTextHandler(io.Discard, nil)))
	defer gateway.Shutdown()
	socket, peer := net.Pipe()
	defer peer.Close()
	conn := NewConnection(socket, nil, player.ID("p1"), 2)
	defer conn.Close("test")
	before := conn.Subscriptions()
	conn.Apply(ClientCommand{Type: "subscribe", ChunkIDs: []string{"dev-world:0:0"}, Private: true})
	gateway.updateIndexes(conn, before, conn.Subscriptions())
	before = conn.Subscriptions()
	conn.Apply(ClientCommand{Type: "unsubscribe", ChunkIDs: []string{"dev-world:0:0"}})
	conn.Apply(ClientCommand{Type: "subscribe", ChunkIDs: []string{"dev-world:1:0"}, Private: true})
	gateway.updateIndexes(conn, before, conn.Subscriptions())
	if got := gateway.Stats().ChunkSubscriptions; got != 1 {
		t.Fatalf("chunk subscriptions = %d, want 1", got)
	}
	if len(gateway.targetConnections(service.Event{ChunkID: "dev-world:0:0"})) != 0 ||
		len(gateway.targetConnections(service.Event{ChunkID: "dev-world:1:0"})) != 1 {
		t.Fatal("gateway still routes events to the old chunk")
	}
}

func TestBuildingPlacedReachesAnotherPlayerSubscribedToChunk(t *testing.T) {
	bus := service.NewEventBus(8)
	gateway := NewGateway(nil, bus, slog.New(slog.NewTextHandler(io.Discard, nil)))
	defer gateway.Shutdown()
	ownerSocket, ownerPeer := net.Pipe()
	viewerSocket, viewerPeer := net.Pipe()
	defer ownerPeer.Close()
	defer viewerPeer.Close()
	owner := NewConnection(ownerSocket, nil, player.ID("owner"), 8)
	viewer := NewConnection(viewerSocket, nil, player.ID("viewer"), 8)
	defer owner.Close("test")
	defer viewer.Close("test")
	gateway.register(owner)
	gateway.register(viewer)
	for _, conn := range []*Connection{owner, viewer} {
		before := conn.Subscriptions()
		conn.Apply(ClientCommand{Type: "subscribe", ChunkIDs: []string{"dev-world:1:2"}, Private: true})
		gateway.updateIndexes(conn, before, conn.Subscriptions())
	}
	if err := bus.Publish(service.Event{Type: service.EventBuildingPlaced, ChunkID: "dev-world:1:2", PlayerID: player.ID("owner")}); err != nil {
		t.Fatal(err)
	}
	for _, conn := range []*Connection{owner, viewer} {
		select {
		case message := <-conn.send:
			if message.Type != string(service.EventBuildingPlaced) || message.Seq != 1 {
				t.Fatalf("player %s received %#v", conn.PlayerID(), message)
			}
		case <-time.After(time.Second):
			t.Fatalf("player %s did not receive the building", conn.PlayerID())
		}
	}
}

func TestGatewaySignalsResyncAfterEventBusOverflow(t *testing.T) {
	gateway := NewGateway(nil, service.NewEventBus(1), slog.New(slog.NewTextHandler(io.Discard, nil)))
	defer gateway.Shutdown()
	socket, peer := net.Pipe()
	defer peer.Close()
	conn := NewConnection(socket, nil, player.ID("p1"), 2)
	defer conn.Close("test")
	gateway.register(conn)
	gateway.signalResync(service.Event{})
	select {
	case message := <-conn.send:
		if message.Type != "realtime.resync_required" || message.Seq != 1 {
			t.Fatalf("unexpected resync message: %#v", message)
		}
	case <-time.After(time.Second):
		t.Fatal("resync signal was not queued")
	}
}

func TestEventLagMetricCountsGatewayDelay(t *testing.T) {
	var metrics TransportMetrics
	metrics.ObserveEventLag(time.Now().Add(-2 * time.Second))
	stats := metrics.Snapshot()
	if stats.EventLagCount != 1 || stats.EventLagSeconds < 2 || stats.EventLagBuckets[6] != 0 || stats.EventLagBuckets[7] != 1 {
		t.Fatalf("unexpected event lag stats: %+v", stats)
	}
}

func TestFanoutHistogramConcurrentObservations(t *testing.T) {
	var metrics TransportMetrics
	var group sync.WaitGroup
	for range 8 {
		group.Add(1)
		go func() {
			defer group.Done()
			for range 100 {
				metrics.ObserveFanout(3)
				_ = metrics.Snapshot()
			}
		}()
	}
	group.Wait()
	stats := metrics.Snapshot()
	if stats.FanoutBuckets[2] != 0 || stats.FanoutBuckets[3] != 800 || stats.FanoutBuckets[len(stats.FanoutBuckets)-1] != 800 {
		t.Fatalf("fanout buckets = %+v", stats.FanoutBuckets)
	}
}
