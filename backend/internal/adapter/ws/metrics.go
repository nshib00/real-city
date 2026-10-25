package ws

import (
	"sync/atomic"
	"time"
)

var FanoutBuckets = [...]float64{0, 1, 2, 5, 10, 25, 50, 100}
var EventLagBuckets = [...]float64{0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5}

// TransportMetrics counts server events. Reconnects have no distinct server signal.
type TransportMetrics struct {
	upgradesOK               atomic.Uint64
	upgradeAuthFailures      atomic.Uint64
	upgradeHandshakeFailures atomic.Uint64
	upgradeTransportFailures atomic.Uint64
	enqueued                 atomic.Uint64
	delivered                atomic.Uint64
	deliveredBytes           atomic.Uint64
	eventLagCount            atomic.Uint64
	eventLagNanoseconds      atomic.Uint64
	eventLagBuckets          [len(EventLagBuckets)]atomic.Uint64
	writeErrors              atomic.Uint64
	slowConsumers            atomic.Uint64
	fanoutBuckets            [len(FanoutBuckets)]atomic.Uint64
}

type TransportStats struct {
	UpgradesOK               uint64
	UpgradeAuthFailures      uint64
	UpgradeHandshakeFailures uint64
	UpgradeTransportFailures uint64
	Enqueued                 uint64
	Delivered                uint64
	DeliveredBytes           uint64
	EventLagCount            uint64
	EventLagSeconds          float64
	EventLagBuckets          [len(EventLagBuckets)]uint64
	WriteErrors              uint64
	SlowConsumers            uint64
	SendQueueDepth           int
	SendQueueCapacity        int
	FanoutBuckets            [len(FanoutBuckets)]uint64
}

func (m *TransportMetrics) ObserveFanout(size int) {
	for i, bound := range FanoutBuckets {
		if float64(size) <= bound {
			m.fanoutBuckets[i].Add(1)
		}
	}
}

func (m *TransportMetrics) ObserveEventLag(createdAt time.Time) {
	if createdAt.IsZero() {
		return
	}
	lag := time.Since(createdAt)
	if lag < 0 {
		lag = 0
	}
	m.eventLagCount.Add(1)
	m.eventLagNanoseconds.Add(uint64(lag.Nanoseconds()))
	for i, bound := range EventLagBuckets {
		if lag.Seconds() <= bound {
			m.eventLagBuckets[i].Add(1)
		}
	}
}

func (m *TransportMetrics) Snapshot() TransportStats {
	stats := TransportStats{
		UpgradesOK:               m.upgradesOK.Load(),
		UpgradeAuthFailures:      m.upgradeAuthFailures.Load(),
		UpgradeHandshakeFailures: m.upgradeHandshakeFailures.Load(),
		UpgradeTransportFailures: m.upgradeTransportFailures.Load(),
		Enqueued:                 m.enqueued.Load(), Delivered: m.delivered.Load(),
		DeliveredBytes: m.deliveredBytes.Load(),
		EventLagCount:  m.eventLagCount.Load(), EventLagSeconds: float64(m.eventLagNanoseconds.Load()) / 1e9,
		WriteErrors: m.writeErrors.Load(), SlowConsumers: m.slowConsumers.Load(),
	}
	for i := range stats.FanoutBuckets {
		stats.FanoutBuckets[i] = m.fanoutBuckets[i].Load()
	}
	for i := range stats.EventLagBuckets {
		stats.EventLagBuckets[i] = m.eventLagBuckets[i].Load()
	}
	return stats
}
