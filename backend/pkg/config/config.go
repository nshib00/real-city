package config

import (
	"os"
	"strconv"
	"time"
)

type Config struct {
	AppEnv        string
	Server        ServerConfig
	Postgres      PostgresConfig
	Redis         RedisConfig
	Session       SessionConfig
	WebSocket     WebSocketConfig
	Simulation    SimulationConfig
	Storage       StorageConfig
	Observability ObservabilityConfig
}

type ServerConfig struct {
	Addr            string
	ReadTimeout     time.Duration
	WriteTimeout    time.Duration
	ShutdownTimeout time.Duration
}

type PostgresConfig struct {
	DSN    string
	Driver string
}

type RedisConfig struct {
	Addr     string
	Password string
	DB       int
}

type SessionConfig struct {
	Secret     string
	AccessTTL  time.Duration
	RefreshTTL time.Duration
}

type WebSocketConfig struct {
	PingInterval time.Duration
	WriteTimeout time.Duration
}

type SimulationConfig struct {
	TickInterval time.Duration
	BatchSize    int
}

type StorageConfig struct {
	PublicURL string
}

type ObservabilityConfig struct {
	LogLevel string
}

func Load() Config {
	return Config{
		AppEnv: env("APP_ENV", "development"),
		Server: ServerConfig{
			Addr:            env("SERVER_ADDR", ":8080"),
			ReadTimeout:     duration("SERVER_READ_TIMEOUT", 5*time.Second),
			WriteTimeout:    duration("SERVER_WRITE_TIMEOUT", 10*time.Second),
			ShutdownTimeout: duration("SERVER_SHUTDOWN_TIMEOUT", 10*time.Second),
		},
		Postgres: PostgresConfig{
			DSN:    env("POSTGRES_DSN", ""),
			Driver: env("POSTGRES_DRIVER", "postgres"),
		},
		Redis: RedisConfig{
			Addr:     env("REDIS_ADDR", "localhost:6379"),
			Password: env("REDIS_PASSWORD", ""),
			DB:       integer("REDIS_DB", 0),
		},
		Session: SessionConfig{
			Secret:     env("SESSION_SECRET", "dev-secret"),
			AccessTTL:  duration("JWT_ACCESS_TTL", 15*time.Minute),
			RefreshTTL: duration("JWT_REFRESH_TTL", 30*24*time.Hour),
		},
		WebSocket: WebSocketConfig{
			PingInterval: duration("WS_PING_INTERVAL", 25*time.Second),
			WriteTimeout: duration("WS_WRITE_TIMEOUT", 5*time.Second),
		},
		Simulation: SimulationConfig{
			TickInterval: duration("SIMULATION_TICK_INTERVAL", time.Second),
			BatchSize:    integer("SIMULATION_BATCH_SIZE", 100),
		},
		Storage: StorageConfig{
			PublicURL: env("STORAGE_PUBLIC_URL", "http://localhost:8080/assets"),
		},
		Observability: ObservabilityConfig{
			LogLevel: env("LOG_LEVEL", "info"),
		},
	}
}

func env(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}

func duration(key string, fallback time.Duration) time.Duration {
	value := os.Getenv(key)
	if value == "" {
		return fallback
	}
	parsed, err := time.ParseDuration(value)
	if err != nil {
		return fallback
	}
	return parsed
}

func integer(key string, fallback int) int {
	value := os.Getenv(key)
	if value == "" {
		return fallback
	}
	parsed, err := strconv.Atoi(value)
	if err != nil {
		return fallback
	}
	return parsed
}
