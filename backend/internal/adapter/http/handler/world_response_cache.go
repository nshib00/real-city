package handler

import "sync"

const worldResponseCacheLimit = 8 << 20
const worldResponseCacheEntries = 64

// worldResponseCache bounds the retained JSON for repeated unconditional reads.
// Chunk versions are part of the ETag key, so tile changes select a new entry.
type worldResponseCache struct {
	mu    sync.Mutex
	items map[string][]byte
	order []string
	bytes int
}

func newWorldResponseCache() *worldResponseCache {
	return &worldResponseCache{items: make(map[string][]byte)}
}

func (c *worldResponseCache) get(key string) ([]byte, bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	data, ok := c.items[key]
	return data, ok
}

func (c *worldResponseCache) put(key string, data []byte) {
	if len(data) > worldResponseCacheLimit/2 {
		return
	}
	c.mu.Lock()
	defer c.mu.Unlock()
	if _, exists := c.items[key]; exists {
		return
	}
	for (c.bytes+len(data) > worldResponseCacheLimit || len(c.order) >= worldResponseCacheEntries) && len(c.order) > 0 {
		oldest := c.order[0]
		c.order = c.order[1:]
		c.bytes -= len(c.items[oldest])
		delete(c.items, oldest)
	}
	c.items[key] = data
	c.order = append(c.order, key)
	c.bytes += len(data)
}
