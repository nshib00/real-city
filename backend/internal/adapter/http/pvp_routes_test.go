package httpadapter

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestCombatRoutesReplaceRemovedAttackMode(t *testing.T) {
	router := testRouter()
	for _, method := range []string{http.MethodGet, http.MethodPost} {
		rec := httptest.NewRecorder()
		router.ServeHTTP(rec, httptest.NewRequest(method, "/api/v1/raids", nil))
		if rec.Code != http.StatusNotFound {
			t.Fatalf("removed route %s returned %d", method, rec.Code)
		}
	}
	for _, path := range []string{"/api/v1/buildings/target/weapons", "/api/v1/combat/monsters"} {
		rec := httptest.NewRecorder()
		router.ServeHTTP(rec, httptest.NewRequest(http.MethodPost, path, nil))
		if rec.Code != http.StatusUnauthorized {
			t.Fatalf("unauthed %s returned %d", path, rec.Code)
		}
	}
	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/api/v1/combat/rules", nil))
	if rec.Code != http.StatusOK {
		t.Fatalf("rules returned %d", rec.Code)
	}
}
