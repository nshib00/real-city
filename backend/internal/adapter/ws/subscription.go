package ws

type SubscriptionSet struct {
	chunks          map[string]bool
	private         bool
	allianceChannel string
}

func NewSubscriptionSet() SubscriptionSet {
	return SubscriptionSet{chunks: make(map[string]bool)}
}

func (s *SubscriptionSet) SubscribeChunks(chunkIDs []string) {
	if s.chunks == nil {
		s.chunks = make(map[string]bool)
	}
	for _, id := range chunkIDs {
		if id != "" {
			s.chunks[id] = true
		}
	}
}

func (s *SubscriptionSet) UnsubscribeChunks(chunkIDs []string) {
	for _, id := range chunkIDs {
		delete(s.chunks, id)
	}
}

func (s *SubscriptionSet) SetPrivate(enabled bool) {
	s.private = enabled
}

func (s *SubscriptionSet) SetAlliance(channel string) {
	s.allianceChannel = channel
}

func (s SubscriptionSet) Matches(chunkID string, playerID string, alliance string, ownerID string) bool {
	if chunkID != "" && s.chunks[chunkID] {
		return true
	}
	if s.private && playerID != "" && playerID == ownerID {
		return true
	}
	if s.allianceChannel != "" && alliance != "" && s.allianceChannel == alliance {
		return true
	}
	return chunkID == "" && playerID == "" && alliance == ""
}

func (s SubscriptionSet) ChunkIDs() []string {
	result := make([]string, 0, len(s.chunks))
	for id := range s.chunks {
		result = append(result, id)
	}
	return result
}
