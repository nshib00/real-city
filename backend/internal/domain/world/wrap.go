package world

const WorldSize = 160
const WorldChunks = WorldSize / ChunkSize

func Wrap(value, size int) int     { return (value%size + size) % size }
func NormalizeCoord(c Coord) Coord { return Coord{X: Wrap(c.X, WorldSize), Y: Wrap(c.Y, WorldSize)} }
func NormalizeChunk(c ChunkCoord) ChunkCoord {
	return ChunkCoord{X: Wrap(c.X, WorldChunks), Y: Wrap(c.Y, WorldChunks)}
}
func WrappedDistance(a, b int) int    { d := Wrap(a-b, WorldSize); return min(d, WorldSize-d) }
func WrappedManhattan(a, b Coord) int { return WrappedDistance(a.X, b.X) + WrappedDistance(a.Y, b.Y) }
func UniqueChunks(coords []ChunkCoord) []ChunkCoord {
	seen := map[ChunkCoord]bool{}
	out := make([]ChunkCoord, 0, len(coords))
	for _, c := range coords {
		c = NormalizeChunk(c)
		if !seen[c] {
			seen[c] = true
			out = append(out, c)
		}
	}
	return out
}
