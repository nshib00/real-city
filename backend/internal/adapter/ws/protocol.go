package ws

import (
	"encoding/json"
	"time"

	"real-city/backend/internal/adapter/http/dto"
	"real-city/backend/internal/service"
)

const ProtocolVersion = 1

type Envelope struct {
	Type            string          `json:"type"`
	EventID         string          `json:"event_id"`
	Seq             uint64          `json:"seq"`
	SentAt          time.Time       `json:"sent_at"`
	ChunkID         string          `json:"chunk_id,omitempty"`
	PayloadVersion  int             `json:"payload_version"`
	Payload         any             `json:"payload,omitempty"`
	RawPayload      json.RawMessage `json:"-"`
	PlayerID        string          `json:"player_id,omitempty"`
	AllianceChannel string          `json:"alliance_channel,omitempty"`
}

type ClientCommand struct {
	Type            string   `json:"type"`
	ChunkIDs        []string `json:"chunk_ids,omitempty"`
	Private         bool     `json:"private,omitempty"`
	AllianceChannel string   `json:"alliance_channel,omitempty"`
}

func EventEnvelope(event service.Event, seq uint64) Envelope {
	return Envelope{
		Type:            string(event.Type),
		EventID:         EventID(event, seq),
		Seq:             seq,
		SentAt:          time.Now().UTC(),
		ChunkID:         event.ChunkID,
		PayloadVersion:  ProtocolVersion,
		Payload:         normalizePayload(event.Payload),
		PlayerID:        string(event.PlayerID),
		AllianceChannel: event.Alliance,
	}
}

func normalizePayload(payload any) any {
	switch value := payload.(type) {
	case service.TileChangedPayload:
		return map[string]any{"tile": dto.Tile(value.Tile)}
	case service.BuildingPayload:
		return map[string]any{"building": dto.Building(value.Building)}
	case service.BuildingRemovedPayload:
		return map[string]any{"building_id": string(value.BuildingID)}
	case service.ResourceChangedPayload:
		return map[string]any{"node": dto.ResourceNode(value.Node)}
	case service.PresencePayload:
		return map[string]any{"player_id": string(value.PlayerID), "online": value.Online}
	default:
		return payload
	}
}

func AckEnvelope(seq uint64, payload any) Envelope {
	return Envelope{
		Type:           "ack",
		EventID:        EventID(service.Event{Type: "ack"}, seq),
		Seq:            seq,
		SentAt:         time.Now().UTC(),
		PayloadVersion: ProtocolVersion,
		Payload:        payload,
	}
}

func EventID(event service.Event, seq uint64) string {
	return event.CreatedAt.Format("20060102150405.000000000") + ":" + string(event.Type) + ":" + uintToString(seq)
}

func uintToString(value uint64) string {
	if value == 0 {
		return "0"
	}
	var buf [20]byte
	i := len(buf)
	for value > 0 {
		i--
		buf[i] = byte('0' + value%10)
		value /= 10
	}
	return string(buf[i:])
}
