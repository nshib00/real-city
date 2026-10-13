package httpadapter

func OpenAPISpec() map[string]any {
	return map[string]any{
		"openapi": "3.0.3",
		"info": map[string]any{
			"title":   "Real City API",
			"version": "0.12.0",
		},
		"servers": []map[string]any{{"url": "/api/v1"}},
		"paths": map[string]any{
			"/auth/register":                path("post", "Register player"),
			"/auth/login":                   path("post", "Login player"),
			"/auth/refresh":                 path("post", "Refresh tokens"),
			"/auth/logout":                  path("post", "Logout current session"),
			"/players/me":                   map[string]any{"get": operation("Current player profile"), "patch": operation("Update current player profile"), "delete": operation("Delete current player")},
			"/players/me/password":          path("patch", "Change password"),
			"/world":                        path("get", "Current world summary"),
			"/world/chunks":                 path("get", "Visible chunks"),
			"/world/viewport":               path("get", "Viewport snapshot"),
			"/world/tiles/chop-forest":      path("post", "Chop forest tile"),
			"/buildings/catalog":            path("get", "Building catalog"),
			"/buildings":                    map[string]any{"get": operation("List player buildings"), "post": idempotentOperation("Place building")},
			"/buildings/{id}":               map[string]any{"get": operation("Get building"), "patch": operation("Update building"), "delete": operation("Delete building")},
			"/economy/inventory":            path("get", "Inventory"),
			"/economy/transactions":         path("get", "Economy transactions"),
			"/economy/population":           path("get", "Population summary"),
			"/resources/nodes":              path("get", "Resource nodes"),
			"/resources/nodes/{id}":         path("patch", "Claim or harvest resource node"),
			"/production/recipes":           path("get", "Production recipes"),
			"/production/jobs":              map[string]any{"get": operation("List production jobs"), "post": operation("Start production")},
			"/production/jobs/{id}":         path("patch", "Patch production job"),
			"/fields/advance":               path("post", "Advance configured field stage"),
			"/fields/harvest":               path("post", "Harvest configured field"),
			"/fields/windleaf/advance":      path("post", "Advance windleaf field stage"),
			"/fields/windleaf/harvest":      path("post", "Harvest windleaf field"),
			"/monsters/catalog":             path("get", "Monster catalog"),
			"/monsters":                     path("get", "List monsters"),
			"/monster-loot":                 path("get", "List public monster loot drops"),
			"/monster-loot/{id}/claim":      path("post", "Claim public monster loot drop"),
			"/monsters/{id}":                path("get", "Monster details"),
			"/monsters/{id}/attack":         path("post", "Attack monster"),
			"/threats":                      path("get", "Threats"),
			"/raids":                        path("get", "Raid list placeholder"),
			"/admin/status":                 path("get", "Admin status placeholder"),
			"/alliances/me":                 path("get", "Alliance profile"),
			"/alliances":                    path("post", "Create alliance"),
			"/alliances/invites":            path("post", "Create alliance invite"),
			"/alliances/invites/{id}":       path("patch", "Accept or decline invite"),
			"/alliances/roles":              path("patch", "Set alliance role"),
			"/alliances/treasury/donations": path("post", "Donate to alliance treasury"),
			"/alliances/buffs":              path("post", "Upgrade alliance buff"),
			"/alliances/territory-aid":      path("post", "Add alliance territory aid"),
			"/chat/messages":                map[string]any{"get": operation("List chat messages"), "post": operation("Send chat message")},
			"/market/orders":                map[string]any{"get": operation("List market orders"), "post": idempotentOperation("Create market order")},
			"/market/orders/{id}":           path("delete", "Cancel market order"),
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
			"500": map[string]any{"description": "Internal error"},
		},
	}
}

func idempotentOperation(summary string) map[string]any {
	item := operation(summary)
	item["parameters"] = []map[string]any{{
		"name":        "Idempotency-Key",
		"in":          "header",
		"required":    true,
		"description": "Required for unsafe POST operations that create durable gameplay state.",
		"schema":      map[string]any{"type": "string", "minLength": 8},
	}}
	return item
}
