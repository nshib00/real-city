package handler

import "testing"
import "strconv"

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
