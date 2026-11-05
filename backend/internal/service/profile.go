package service

import (
	"context"
	"real-city/backend/internal/domain/building"
	"real-city/backend/internal/domain/player"
	"real-city/backend/internal/domain/world"
)

func (s *PlayerService) SetProfileSources(buildings BuildingRepository, alliances AllianceRepository) {
	s.buildings = buildings
	s.alliances = alliances
}
func (s *PlayerService) enrichProfile(ctx context.Context, p player.Player) (player.Player, error) {
	p.Profile.GroupID = ""
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
		if b.State == building.StateRuined || b.State == building.StateBuilding || b.State == building.StateRepairing {
			continue
		}
		if b.Type == building.TypeTownHall && (p.Profile.HomeCenterID == "" || string(b.ID) == selected) {
			p.Profile.HomeCenterID = string(b.ID)
		}
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
	view := player.PublicProfile{PlayerID: p.ID, DisplayName: p.Profile.DisplayName, AvatarID: p.Profile.AvatarID, BannerID: p.Profile.BannerID, Title: p.Profile.Title, Level: p.Profile.Level, GroupID: p.Profile.GroupID}
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
