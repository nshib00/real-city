package world

import "testing"

func TestTileLocalCoordHandlesNegativeTiles(t *testing.T) {
	got := TileLocalCoord(Coord{X: -1, Y: -33})
	if got != (Coord{X: 31, Y: 31}) {
		t.Fatalf("local coord = %+v", got)
	}
}

func TestChunksAround(t *testing.T) {
	got := ChunksAround(ChunkCoord{X: 2, Y: -1}, 1)
	if len(got) != 9 {
		t.Fatalf("chunks len = %d", len(got))
	}
	if got[0] != (ChunkCoord{X: 1, Y: -2}) || got[8] != (ChunkCoord{X: 3, Y: 0}) {
		t.Fatalf("unexpected bounds: first=%+v last=%+v", got[0], got[8])
	}
}
