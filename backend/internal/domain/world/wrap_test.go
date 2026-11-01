package world

import "testing"

func TestToroidalCoordinatesAndUniqueChunks(t *testing.T) {
	if got := NormalizeCoord(Coord{X: -1, Y: 320}); got != (Coord{X: 159, Y: 0}) {
		t.Fatal(got)
	}
	if WrappedManhattan(Coord{X: 159, Y: 159}, Coord{}) != 2 {
		t.Fatal("not shortest seam distance")
	}
	if got := NormalizeChunk(ChunkCoord{X: -1, Y: 5}); got != (ChunkCoord{X: 4, Y: 0}) {
		t.Fatal(got)
	}
	if n := len(UniqueChunks(ChunksAround(ChunkCoord{}, 3))); n != 25 {
		t.Fatal(n)
	}
}
