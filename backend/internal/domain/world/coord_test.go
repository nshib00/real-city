package world

import "testing"

func TestChunkForTile(t *testing.T) {
	tests := []struct {
		name string
		tile Coord
		want ChunkCoord
	}{
		{name: "origin", tile: Coord{X: 0, Y: 0}, want: ChunkCoord{X: 0, Y: 0}},
		{name: "positive", tile: Coord{X: 33, Y: 63}, want: ChunkCoord{X: 1, Y: 1}},
		{name: "negative", tile: Coord{X: -1, Y: -33}, want: ChunkCoord{X: -1, Y: -2}},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := ChunkForTile(tt.tile); got != tt.want {
				t.Fatalf("expected %+v, got %+v", tt.want, got)
			}
		})
	}
}
