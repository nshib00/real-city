package ws

import "sync/atomic"

var FanoutBuckets = [...]float64{0, 1, 2, 5, 10, 25, 50, 100}

// TransportMetrics counts server events. Reconnects have no distinct server signal.
type TransportMetrics struct {
	upgradesOK               atomic.Uint64
	upgradeAuthFailures      atomic.Uint64
	upgradeHandshakeFailures atomic.Uint64
	upgradeTransportFailures atomic.Uint64
	enqueued                 atomic.Uint64
	delivered                atomic.Uint64
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

func (m *TransportMetrics) Snapshot() TransportStats {
	stats := TransportStats{
		UpgradesOK:               m.upgradesOK.Load(),
		UpgradeAuthFailures:      m.upgradeAuthFailures.Load(),
		UpgradeHandshakeFailures: m.upgradeHandshakeFailures.Load(),
		UpgradeTransportFailures: m.upgradeTransportFailures.Load(),
		Enqueued:                 m.enqueued.Load(), Delivered: m.delivered.Load(),
		WriteErrors: m.writeErrors.Load(), SlowConsumers: m.slowConsumers.Load(),
	}
	for i := range stats.FanoutBuckets {
		stats.FanoutBuckets[i] = m.fanoutBuckets[i].Load()
	}
	return stats
}
