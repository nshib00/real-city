package main

import (
	"encoding/json"
	"log"
	"os"
	"path/filepath"

	httpadapter "real-city/backend/internal/adapter/http"
)

func main() {
	data, err := json.MarshalIndent(httpadapter.OpenAPISpec(), "", "  ")
	if err != nil {
		log.Fatal(err)
	}
	data = append(data, '\n')
	path := filepath.Join("docs", "swagger", "openapi.json")
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		log.Fatal(err)
	}
	if err := os.WriteFile(path, data, 0o644); err != nil {
		log.Fatal(err)
	}
	log.Printf("generated %s", path)
}
