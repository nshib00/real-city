package handler

import (
	"strconv"
	"sync"
	"testing"
)

func TestWorldResponseCacheBoundsMemory(t *testing.T) {
	cache := newWorldResponseCache()
	for i := 0; i < 5; i++ {
		cache.put(string(rune('a'+i)), make([]byte, 2<<20))
	}
	if cache.bytes > worldResponseCacheLimit {
		t.Fatalf("cache grew to %d bytes", cache.bytes)
	}
	if _, ok := cache.get("a"); ok {
		t.Fatal("oldest response was not evicted")
	}
	if _, ok := cache.get("e"); !ok {
		t.Fatal("newest response is absent")
	}
	cache.put("oversized", make([]byte, worldResponseCacheLimit/2+1))
	if _, ok := cache.get("oversized"); ok {
		t.Fatal("oversized response was cached")
	}
	for i := 0; i < worldResponseCacheEntries+1; i++ {
		cache.put("small-"+strconv.Itoa(i), []byte("{}"))
	}
	if len(cache.items) > worldResponseCacheEntries {
		t.Fatalf("cache retained %d entries", len(cache.items))
	}
}

func TestWorldResponseCacheConcurrentReadsAndWrites(t *testing.T) {
	cache := newWorldResponseCache()
	var workers sync.WaitGroup
	for worker := 0; worker < 8; worker++ {
		workers.Add(1)
		go func(worker int) {
			defer workers.Done()
			for index := 0; index < 200; index++ {
				key := "version-" + strconv.Itoa((worker+index)%80)
				cache.put(key, []byte("{}"))
				if body, ok := cache.get(key); ok && string(body) != "{}" {
					t.Errorf("corrupt cached response for %s: %q", key, body)
				}
			}
		}(worker)
	}
	workers.Wait()
	if cache.bytes > worldResponseCacheLimit || len(cache.items) > worldResponseCacheEntries {
		t.Fatalf("cache limits exceeded: bytes=%d entries=%d", cache.bytes, len(cache.items))
	}
}
