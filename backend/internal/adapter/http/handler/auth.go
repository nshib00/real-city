package handler

import (
	"net"
	"net/http"

	"real-city/backend/internal/adapter/http/dto"
	"real-city/backend/internal/adapter/http/middleware"
	"real-city/backend/internal/service"
	"real-city/backend/pkg/apperror"
)

type AuthHandler struct {
	auth *service.AuthService
}

func NewAuthHandler(auth *service.AuthService) *AuthHandler {
	return &AuthHandler{auth: auth}
}

func (h *AuthHandler) Register(w http.ResponseWriter, r *http.Request) {
	var req dto.RegisterRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, err)
		return
	}
	if err := req.Validate(); err != nil {
		writeError(w, err)
		return
	}
	result, err := h.auth.Register(r.Context(), service.RegisterInput{
		Email: req.Email, Name: req.Name, Password: req.Password,
		UserAgent: r.UserAgent(), IP: remoteIP(r),
	})
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusCreated, dto.AuthResult(result))
}

func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
	var req dto.LoginRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, err)
		return
	}
	if err := req.Validate(); err != nil {
		writeError(w, err)
		return
	}
	result, err := h.auth.Login(r.Context(), service.LoginInput{
		Email: req.Email, Password: req.Password,
		UserAgent: r.UserAgent(), IP: remoteIP(r),
	})
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, dto.AuthResult(result))
}

func (h *AuthHandler) Refresh(w http.ResponseWriter, r *http.Request) {
	var req dto.RefreshRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, err)
		return
	}
	result, err := h.auth.Refresh(r.Context(), req.RefreshToken, r.UserAgent(), remoteIP(r))
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, dto.AuthResult(result))
}

func (h *AuthHandler) Logout(w http.ResponseWriter, r *http.Request) {
	var req dto.LogoutRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, err)
		return
	}
	if req.AllDevices {
		playerID, ok := middleware.PlayerID(r.Context())
		if !ok {
			writeError(w, apperror.New(apperror.Unauthorized, "authenticated player is required"))
			return
		}
		if err := h.auth.LogoutAll(r.Context(), playerID); err != nil {
			writeError(w, err)
			return
		}
		writeJSON(w, http.StatusOK, envelope{"status": "ok"})
		return
	}
	if err := h.auth.Logout(r.Context(), req.RefreshToken); err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, envelope{"status": "ok"})
}

func remoteIP(r *http.Request) string {
	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		return r.RemoteAddr
	}
	return host
}
