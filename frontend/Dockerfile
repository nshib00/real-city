FROM node:22-alpine AS build
WORKDIR /src
COPY frontend/package.json frontend/package-lock.json ./frontend/
RUN cd frontend && npm ci
COPY frontend ./frontend
COPY shared ./shared
COPY data ./data
WORKDIR /src/frontend
RUN npm run build

FROM golang:1.26.11-alpine3.24 AS caddy-build
RUN go install github.com/caddyserver/xcaddy/cmd/xcaddy@v0.4.5
RUN xcaddy build v2.11.9 \
    --replace golang.org/x/net=golang.org/x/net@v0.62.0 \
    --output /out/caddy

FROM alpine:3.24.3
RUN apk add --no-cache ca-certificates libcap \
    && addgroup -S caddy \
    && adduser -S -G caddy caddy \
    && mkdir -p /data /config /srv \
    && chown -R caddy:caddy /data /config /srv
ENV XDG_DATA_HOME=/data XDG_CONFIG_HOME=/config
COPY --from=caddy-build /out/caddy /usr/bin/caddy
RUN setcap 'cap_net_bind_service=+ep' /usr/bin/caddy
COPY deploy/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /src/frontend/dist /srv
EXPOSE 80 443
USER caddy
ENTRYPOINT ["/usr/bin/caddy"]
CMD ["run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
