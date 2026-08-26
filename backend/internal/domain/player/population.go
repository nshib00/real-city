package player

type Population struct {
	Total      int
	Free       int
	Builders   int
	Production int
	Fields     int
	Defense    int
	Repair     int
}

func NewPopulation(total int, busy Population) Population {
	used := busy.Builders + busy.Production + busy.Fields + busy.Defense + busy.Repair
	if used > total {
		used = total
	}
	busy.Total = total
	busy.Free = total - used
	return busy
}
