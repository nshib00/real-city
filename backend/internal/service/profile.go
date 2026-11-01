package service

import (
	"context"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/catalog"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
)

func (s *PlayerService) SetProfileSources(buildings BuildingRepository, alliances AllianceRepository) {
	s.buildings = buildings
	s.alliances = alliances
}
func (s *PlayerService) enrichProfile(ctx context.Context, p player.Player) (player.Player, error) {
	p.Profile.GroupID = ""
	p.Profile.Scores = map[string]int{"economy": 0, "production": 0, "storage": 0, "defense": 0}
	if s.alliances != nil {
		a, _, err := s.alliances.FindByPlayer(ctx, p.ID)
		if err != nil && !isNotFound(err) {
			return p, err
		}
		if err == nil {
			p.Profile.GroupID = string(a.ID)
		}
	}
	if s.buildings == nil {
		return p, nil
	}
	owned, err := s.buildings.ListByPlayer(ctx, p.ID)
	if err != nil {
		return p, err
	}
	selected := p.Profile.HomeCenterID
	p.Profile.HomeCenterID = ""
	for _, b := range owned {
		if b.State == building.StateRuined || b.State == building.StateBuilding {
			continue
		}
		if b.Type == building.TypeTownHall && (p.Profile.HomeCenterID == "" || string(b.ID) == selected) {
			p.Profile.HomeCenterID = string(b.ID)
		}
		spec, ok := catalog.GetBuilding(b.Type)
		if !ok {
			continue
		}
		category := spec.Category
		score := max(1, b.Level) * 10
		switch category {
		case "industry", "fields":
			p.Profile.Scores["production"] += score
		case "storage":
			p.Profile.Scores["storage"] += score
		case "defense":
			p.Profile.Scores["defense"] += score
		}
		p.Profile.Scores["economy"] += score
	}
	return p, nil
}
func (s *PlayerService) PublicProfile(ctx context.Context, id player.ID) (player.PublicProfile, error) {
	p, err := s.players.FindByID(ctx, id)
	if err != nil {
		return player.PublicProfile{}, err
	}
	p, err = s.enrichProfile(ctx, p)
	if err != nil {
		return player.PublicProfile{}, err
	}
	view := player.PublicProfile{PlayerID: p.ID, DisplayName: p.Profile.DisplayName, AvatarID: p.Profile.AvatarID, BannerID: p.Profile.BannerID, Title: p.Profile.Title, Level: p.Profile.Level, GroupID: p.Profile.GroupID, Scores: p.Profile.Scores}
	if s.buildings != nil && p.Profile.HomeCenterID != "" {
		b, e := s.buildings.FindByID(ctx, building.ID(p.Profile.HomeCenterID))
		if e != nil {
			return view, e
		}
		coord := world.NormalizeCoord(b.Tile)
		view.SettlementRegion = &player.SettlementRegion{DistrictX: coord.X / world.ChunkSize, DistrictY: coord.Y / world.ChunkSize}
	}
	return view, nil
}
