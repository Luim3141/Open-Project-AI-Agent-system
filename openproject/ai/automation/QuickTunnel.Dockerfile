# Autonomous Self-Healing Quick Tunnel Image
# Combines official cloudflared binary with minimal alpine base
# Includes supervisor script that self-terminates on persistent unhealthy status,
# triggering Docker's native restart: unless-stopped without needing Docker socket.

FROM cloudflare/cloudflared:2026.10.0@sha256:9b49eed8f62806d5d45ddf59ecefb5710429598ea6d3fcccd2af938f621b2b07 AS cf_binary

FROM caddy:2-alpine@sha256:d8542f48d34a9cf4e4c11a478865229840e87e4c96ea3f439101f31a5d35f75f

# Install ca-certificates and wget for healthchecks
RUN apk add --no-cache ca-certificates wget

# Copy cloudflared binary from official image
COPY --from=cf_binary /usr/local/bin/cloudflared /usr/local/bin/cloudflared

# Copy self-healing supervisor script
COPY quick_tunnel_supervisor.sh /usr/local/bin/quick_tunnel_supervisor.sh
RUN chmod +x /usr/local/bin/quick_tunnel_supervisor.sh

EXPOSE 2000

ENTRYPOINT ["/usr/local/bin/quick_tunnel_supervisor.sh"]
