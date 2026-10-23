package observability

import (
	"sync"
	"time"
)

var simulation = struct {
	sync.Mutex
	ticks          map[string]uint64
	lastSuccess    map[string]float64
	stages         map[string]*durationSample
	stageItems     map[string]uint64
	stageSaturated map[string]uint64
	actions        map[string]uint64
	dispatch       map[string]*durationSample
	outbox         map[string]uint64
	heartbeat      float64
	enabled        bool
}{ticks: map[string]uint64{}, lastSuccess: map[string]float64{}, stages: map[string]*durationSample{}, stageItems: map[string]uint64{}, stageSaturated: map[string]uint64{}, actions: map[string]uint64{}, dispatch: map[string]*durationSample{}, outbox: map[string]uint64{}}

var tickDurations = map[string]*durationSample{}

func EnableSimulation() { simulation.Lock(); simulation.enabled = true; simulation.Unlock() }

// TickMode is one of scheduled or catch_up; callers use fixed names only.
func Tick(mode string, started time.Time, result string, successful bool) {
	observe(tickDurations, mode+"|"+result, time.Since(started))
	simulation.Lock()
	simulation.ticks[mode+"|"+result]++
	if successful {
		simulation.lastSuccess[mode] = float64(time.Now().UnixNano()) / 1e9
	}
	if mode == "scheduled" {
		simulation.heartbeat = float64(time.Now().UnixNano()) / 1e9
	}
	simulation.Unlock()
}

func Stage(name string, started time.Time, processed, failed, limit int, err error) {
	ObserveStage(name, started, err)
	simulation.Lock()
	simulation.stageItems[name+"|processed"] += uint64(max(0, processed))
	simulation.stageItems[name+"|failed"] += uint64(max(0, failed))
	if limit > 0 && processed >= limit {
		simulation.stageSaturated[name]++
	}
	simulation.Unlock()
}

func ObserveStage(name string, started time.Time, err error) {
	observe(simulation.stages, name+"|"+Result(err), time.Since(started))
}

func Action(result string) { simulation.Lock(); simulation.actions[result]++; simulation.Unlock() }

func Dispatch(component string, started time.Time, err error) {
	observe(simulation.dispatch, component+"|"+Result(err), time.Since(started))
}
func Outbox(result string) { simulation.Lock(); simulation.outbox[result]++; simulation.Unlock() }

func WriteSimulation(w Writer) {
	writeDurations(w, "real_city_simulation_tick_duration_seconds", "Duration of simulation ticks by invocation mode.", "mode", tickDurations)
	writeDurations(w, "real_city_simulation_stage_duration_seconds", "Duration of named simulation stages.", "component", simulation.stages)
	writeDurations(w, "real_city_outbox_dispatch_duration_seconds", "Duration of outbox fetch, publish and total dispatch.", "component", simulation.dispatch)
	simulation.Lock()
	defer simulation.Unlock()
	w.Family("real_city_simulation_enabled", "One if this process owns a scheduled simulation runner.", "gauge")
	if simulation.enabled {
		w.Sample("real_city_simulation_enabled", nil, 1)
	} else {
		w.Sample("real_city_simulation_enabled", nil, 0)
	}
	w.Family("real_city_simulation_ticks_total", "Simulation ticks by mode and result, including recovered panics.", "counter")
	for _, mode := range []string{"scheduled", "catch_up"} {
		for _, result := range []string{"ok", "error", "panic"} {
			w.Sample("real_city_simulation_ticks_total", map[string]string{"mode": mode, "result": result}, float64(simulation.ticks[mode+"|"+result]))
		}
	}
	w.Family("real_city_simulation_last_success_timestamp_seconds", "Unix time of last successful tick by mode.", "gauge")
	for _, mode := range []string{"scheduled", "catch_up"} {
		w.Sample("real_city_simulation_last_success_timestamp_seconds", map[string]string{"mode": mode}, simulation.lastSuccess[mode])
	}
	w.Family("real_city_simulation_heartbeat_timestamp_seconds", "Unix time of last finished scheduled tick, including failures.", "gauge")
	w.Sample("real_city_simulation_heartbeat_timestamp_seconds", nil, simulation.heartbeat)
	w.Family("real_city_simulation_stage_items_total", "Items handled per stage; failures include per-item errors.", "counter")
	w.Family("real_city_simulation_stage_saturated_total", "Stages returning at least the configured batch limit.", "counter")
	for _, stage := range []string{"actions", "buildings", "production", "resources", "monster_spawning", "monster_ai"} {
		for _, result := range []string{"processed", "failed"} {
			w.Sample("real_city_simulation_stage_items_total", map[string]string{"component": stage, "result": result}, float64(simulation.stageItems[stage+"|"+result]))
		}
		w.Sample("real_city_simulation_stage_saturated_total", map[string]string{"component": stage}, float64(simulation.stageSaturated[stage]))
	}
	w.Family("real_city_action_items_total", "Action queue outcomes.", "counter")
	for _, result := range []string{"fetched", "processed", "retried", "failed"} {
		w.Sample("real_city_action_items_total", map[string]string{"result": result}, float64(simulation.actions[result]))
	}
	w.Family("real_city_outbox_items_total", "Outbox delivery outcomes.", "counter")
	for _, result := range []string{"fetched", "sent", "retried", "dead", "failed"} {
		w.Sample("real_city_outbox_items_total", map[string]string{"result": result}, float64(simulation.outbox[result]))
	}
}
