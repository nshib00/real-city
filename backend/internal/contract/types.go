package contract

type Coord struct {
	X int `json:"x"`
	Y int `json:"y"`
}

type ChunkCoord struct {
	X int `json:"x"`
	Y int `json:"y"`
}

type ObjectRef struct {
	ID   string `json:"id"`
	Type string `json:"type"`
}

type APIError struct {
	Kind    string            `json:"kind"`
	Message string            `json:"message"`
	Fields  map[string]string `json:"fields,omitempty"`
}
