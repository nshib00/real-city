FROM golang:1.24-alpine AS build
WORKDIR /src
COPY go.mod ./
COPY . .
RUN go build -o /out/api ./cmd/api
RUN go build -o /out/migrate ./cmd/migrate

FROM alpine:3.20
WORKDIR /app
COPY --from=build /out/api /app/api
COPY --from=build /out/migrate /app/migrate
COPY --from=build /src/db/migrations /app/db/migrations
EXPOSE 8080
CMD ["/app/api"]
