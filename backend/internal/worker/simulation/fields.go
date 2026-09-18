package simulation

import (
	"time"

	"real-city/backend/internal/domain/economy"
)

type FieldProgress struct {
	Crop  economy.FieldCrop
	Stage economy.FieldStage
	Ready bool
}

func WindleafProgress(plantedAt time.Time, now time.Time) FieldProgress {
	crop := economy.WindleafCrop()
	elapsed := now.Sub(plantedAt)
	var total time.Duration
	stage := crop.Growth[len(crop.Growth)-1]
	for _, candidate := range crop.Growth {
		total += candidate.Duration
		stage = candidate
		if candidate.Ready || elapsed < total {
			break
		}
	}
	return FieldProgress{Crop: crop, Stage: stage, Ready: stage.Ready}
}
