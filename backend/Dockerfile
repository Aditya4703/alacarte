# ────────────────────────────────────────────────────────────
# Stage 1: Frontend build (Vite → backend/public)
# package*.json copied first so npm install is cached unless deps change.
# ────────────────────────────────────────────────────────────
FROM node:22-bookworm-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund
COPY frontend ./
RUN npm run build
# Build output is now at /app/backend/public

# ────────────────────────────────────────────────────────────
# Stage 2: Backend deps (cached unless package*.json changes)
# ────────────────────────────────────────────────────────────
FROM node:22-bookworm-slim AS node-deps
WORKDIR /app
COPY backend/package*.json ./
RUN npm install --omit=dev --no-audit --no-fund

# ────────────────────────────────────────────────────────────
# Stage 3: Assemble app (backend source + deps + frontend bundle)
# This is a cheap COPY-only stage — rebuilds instantly on code changes.
# ────────────────────────────────────────────────────────────
FROM node:22-bookworm-slim AS node-build
WORKDIR /app
COPY --from=node-deps /app/node_modules ./node_modules
COPY backend/server.mjs ./
COPY backend/routes ./routes
COPY backend/lib ./lib
COPY --from=frontend-build /app/backend/public ./public

# Source stage for Node 22 runtime binaries
FROM node:22-bookworm-slim AS node-runtime

# ────────────────────────────────────────────────────────────
# Stage 4: Runtime — upstream amdp image + Node 22 + our app
# The apt-get layer is cached unless the base image changes.
# ────────────────────────────────────────────────────────────
FROM ghcr.io/zhaarey/apple-music-downloader:latest

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      ca-certificates \
      tini \
      curl \
      && rm -rf /var/lib/apt/lists/*

# Inject Node 22 runtime from the official Node image.
COPY --from=node-runtime /usr/local/bin/node /usr/local/bin/node
COPY --from=node-runtime /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -sf /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm && \
    ln -sf /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

# App
WORKDIR /app
COPY --from=node-build /app /app

# Build-time sanity checks so regressions are caught early.
RUN MP4Box -version 2>&1 | grep -q 'GPAC version' || (echo 'MP4Box runtime check failed' && exit 1)
RUN command -v apple-music-dl >/dev/null

EXPOSE 7373
ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["node","server.mjs"]
