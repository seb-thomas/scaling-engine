FROM oven/bun:latest AS builder

WORKDIR /app

# Copy package files and lockfile
COPY package*.json ./
COPY bun.lock* ./
RUN bun install

# Copy source files
COPY . .

# Build Astro app (creates dist/ with server and client)
RUN bunx astro build

# Verify build output
RUN if [ ! -d "dist" ]; then \
      echo "ERROR: dist directory not found after build!"; \
      exit 1; \
    fi && \
    if [ ! -f "dist/server/entry.mjs" ]; then \
      echo "ERROR: dist/server/entry.mjs not found after build!"; \
      ls -la dist/ || echo "dist directory exists but entry.mjs missing"; \
      exit 1; \
    fi && \
    echo "✅ Astro build successful - dist/server/entry.mjs exists"

# Production stage
FROM oven/bun:latest

WORKDIR /app

# Copy package files and lockfile
COPY package*.json ./
COPY bun.lock* ./
RUN bun install --production

# Copy built files from Astro
COPY --from=builder /app/dist ./dist

EXPOSE 3000

# Astro Bun adapter creates dist/server/entry.mjs
CMD ["bun", "run", "dist/server/entry.mjs"]

