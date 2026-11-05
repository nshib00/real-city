package httpadapter

import "strings"

func OpenAPISpec() map[string]any {
	spec := map[string]any{
		"openapi": "3.0.3",
		"info": map[string]any{
			"title":   "Real City API",
			"version": "0.12.0",
		},
		"servers": []map[string]any{{"url": "/api/v1"}},
		"security": []map[string][]string{{"bearerAuth": {}}},
		"paths": map[string]any{
			"/health":                           map[string]any{"get": rootOperation("Liveness probe")},
			"/healthz":                          map[string]any{"get": rootOperation("Liveness probe (legacy alias)")},
			"/ready":                            map[string]any{"get": rootOperation("Readiness probe; checks database connectivity when configured")},
			"/metrics":                          map[string]any{"get": rootOperation("Prometheus metrics")},
			"/swagger/openapi.json":             map[string]any{"get": rootOperation("OpenAPI contract document")},
			"/alliances/me":                      map[string]any{"delete": operation("Leave alliance; last leader dissolves it"), "get": operation("Alliance profile")},
			"/alliances/members/{id}":            map[string]any{"delete": operation("Kick a lower-ranked alliance member")},
			"/buildings/{id}":                    map[string]any{"delete": operation("Delete building"), "get": operation("Get building"), "patch": operation("Update building")},
			"/market/orders/{id}":                map[string]any{"delete": operation("Cancel market order")},
			"/players/me":                        map[string]any{"delete": operation("Delete current player"), "get": operation("Current player profile"), "patch": operation("Update current player profile")},
			"/admin/accounts/audit":              map[string]any{"get": operation("GET /admin/accounts/audit")},
			"/admin/audit":                       map[string]any{"get": operation("GET /admin/audit")},
			"/admin/chat/messages":               map[string]any{"get": operation("GET /admin/chat/messages")},
			"/admin/players":                     map[string]any{"get": operation("GET /admin/players")},
			"/admin/status":                      map[string]any{"get": operation("Administrator-only process diagnostics")},
			"/buildings":                         map[string]any{"get": operation("List player buildings or visible world buildings"), "post": idempotentOperation("Place building")},
			"/buildings/catalog":                 map[string]any{"get": operation("Building catalog; scope=all includes every type and level")},
			"/buildings/{id}/repair":             map[string]any{"get": operation("Repair price, worker reservation, duration and pending job")},
			"/chat/messages":                     map[string]any{"get": operation("List chat messages"), "post": operation("Send chat message")},
			"/combat/attacks":                    map[string]any{"get": operation("List pending weapon attacks")},
			"/combat/history":                    map[string]any{"get": operation("GET /combat/history")},
			"/combat/rules":                      map[string]any{"get": operation("PvP rules and monster creation cost")},
			"/economy/inventory":                 map[string]any{"get": operation("Inventory")},
			"/economy/population":                map[string]any{"get": operation("Population summary")},
			"/economy/transactions":              map[string]any{"get": operation("Economy transactions")},
			"/market/orders":                     map[string]any{"get": operation("List market orders"), "post": idempotentOperation("Create market order")},
			"/monster-loot":                      map[string]any{"get": operation("List public monster loot drops")},
			"/monsters":                          map[string]any{"get": operation("List monsters")},
			"/monsters/catalog":                  map[string]any{"get": operation("Monster catalog")},
			"/monsters/{id}":                     map[string]any{"get": operation("Monster details")},
			"/players/levels":                    map[string]any{"get": operation("Shared catalog of player levels and planned unlocks")},
			"/players/nearby":                    map[string]any{"get": operation("GET /players/nearby")},
			"/players/{id}":                      map[string]any{"get": operation("Public player profile")},
			"/players/{id}/profile":              map[string]any{"get": operation("Public profile with approximate settlement and aggregate scores")},
			"/production/jobs":                   map[string]any{"get": operation("List production jobs"), "post": operation("Start production")},
			"/production/recipes":                map[string]any{"get": operation("Production recipes")},
			"/resources/nodes":                   map[string]any{"get": operation("Resource nodes")},
			"/threats":                           map[string]any{"get": operation("Threats")},
			"/world":                             map[string]any{"get": operation("Current world summary")},
			"/world/chunks":                      map[string]any{"get": operation("Visible chunks")},
			"/world/viewport":                    map[string]any{"get": operation("Viewport snapshot")},
			"/admin/chat/messages/{id}":          map[string]any{"patch": operation("PATCH /admin/chat/messages/{id}")},
			"/admin/players/{id}":                map[string]any{"patch": operation("PATCH /admin/players/{id}")},
			"/alliances/invites/{id}":            map[string]any{"patch": operation("Accept or decline invite")},
			"/alliances/roles":                   map[string]any{"patch": operation("Set alliance role")},
			"/chat/read":                         map[string]any{"patch": operation("Advance own visible channel read cursor")},
			"/players/me/password":               map[string]any{"patch": operation("Change password")},
			"/production/jobs/{id}":              map[string]any{"patch": operation("Patch production job")},
			"/resources/nodes/{id}":              map[string]any{"patch": operation("Claim or harvest resource node")},
			"/alliances":                         map[string]any{"post": operation("Create alliance")},
			"/alliances/buffs":                   map[string]any{"post": operation("Upgrade alliance buff")},
			"/alliances/invites":                 map[string]any{"post": idempotentOperation("Create alliance invite")},
			"/alliances/members/{id}/leadership": map[string]any{"post": operation("Transfer alliance leadership")},
			"/alliances/territory-aid":           map[string]any{"post": operation("Add alliance territory aid")},
			"/alliances/treasury/donations":      map[string]any{"post": operation("Donate to alliance treasury")},
			"/alliances/treasury/spend":          map[string]any{"post": idempotentOperation("Transfer treasury resources to a member")},
			"/auth/login":                        map[string]any{"post": operation("Login player")},
			"/auth/logout":                       map[string]any{"post": operation("Logout current session")},
			"/auth/refresh":                      map[string]any{"post": operation("Refresh tokens")},
			"/auth/register":                     map[string]any{"post": operation("Register player")},
			"/buildings/{id}/weapons":            map[string]any{"post": idempotentOperation("Use inventory weapon against rival building")},
			"/combat/monsters":                   map[string]any{"post": idempotentOperation("Create monster against rival buildings")},
			"/fields/advance":                    map[string]any{"post": operation("POST /fields/advance")},
			"/fields/harvest":                    map[string]any{"post": operation("POST /fields/harvest")},
			"/fields/windleaf/advance":           map[string]any{"post": operation("POST /fields/windleaf/advance")},
			"/fields/windleaf/harvest":           map[string]any{"post": operation("Harvest windleaf field")},
			"/monster-loot/{id}/claim":           map[string]any{"post": operation("Claim public monster loot drop")},
			"/monsters/{id}/weapons":             map[string]any{"post": idempotentOperation("Use weapon against monster")},
			"/players/me/presence":               map[string]any{"post": operation("POST /players/me/presence")},
			"/world/tiles/chop-forest":           map[string]any{"post": operation("Chop forest tile")},
		},
		"components": map[string]any{
			"securitySchemes": map[string]any{
				"bearerAuth": map[string]any{"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
			},
			"schemas": map[string]any{
				"Error": map[string]any{
					"type":     "object",
					"required": []string{"kind", "message"},
					"properties": map[string]any{
						"kind":    map[string]any{"type": "string"},
						"message": map[string]any{"type": "string"},
						"fields":  map[string]any{"type": "object", "additionalProperties": map[string]any{"type": "string"}},
					},
				},
			},
		},
	}
	// These operations are intentionally reachable without a player session.
	publicOperations := map[string][]string{
		"/auth/register": {"post"}, "/auth/login": {"post"}, "/auth/refresh": {"post"},
		"/world": {"get"}, "/world/chunks": {"get"}, "/world/viewport": {"get"},
		"/buildings/catalog": {"get"}, "/resources/nodes": {"get"},
		"/production/recipes": {"get"}, "/monsters/catalog": {"get"},
		"/monsters": {"get"}, "/monster-loot": {"get"}, "/threats": {"get"},
		"/combat/rules": {"get"}, "/players/levels": {"get"}, "/market/orders": {"get"},
	}
	paths := spec["paths"].(map[string]any)
	for path, raw := range paths {
		if !strings.Contains(path, "{id}") {
			continue
		}
		for _, rawOperation := range raw.(map[string]any) {
			operation := rawOperation.(map[string]any)
			parameters, _ := operation["parameters"].([]map[string]any)
			operation["parameters"] = append(parameters, map[string]any{
				"name": "id", "in": "path", "required": true,
				"schema": map[string]any{"type": "string"},
			})
		}
	}
	for path, methods := range publicOperations {
		operations := paths[path].(map[string]any)
		for _, method := range methods {
			operations[method].(map[string]any)["security"] = []map[string][]string{}
		}
	}
	return spec
}

func path(method string, summary string) map[string]any {
	return map[string]any{method: operation(summary)}
}

func operation(summary string) map[string]any {
	return map[string]any{
		"summary": summary,
		"responses": map[string]any{
			"200": map[string]any{"description": "OK"},
			"400": map[string]any{"description": "Bad request"},
			"401": map[string]any{"description": "Unauthorized"},
			"409": map[string]any{"description": "Conflict"},
			"429": map[string]any{"description": "Rate limit exceeded"},
			"500": map[string]any{"description": "Internal error"},
		},
	}
}

func rootOperation(summary string) map[string]any {
	item := operation(summary)
	item["servers"] = []map[string]any{{"url": "/"}}
	item["security"] = []map[string][]string{}
	return item
}

func idempotentOperation(summary string) map[string]any {
	item := operation(summary)
	item["parameters"] = []map[string]any{{
		"name":        "Idempotency-Key",
		"in":          "header",
		"required":    true,
		"description": "Required for unsafe POST operations that create durable gameplay state.",
		"schema":      map[string]any{"type": "string", "minLength": 8, "maxLength": 128},
	}}
	return item
}
