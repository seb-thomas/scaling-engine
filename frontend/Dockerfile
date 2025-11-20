FROM oven/bun:latest AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN bun install

# Copy source files
COPY . .

# Build the app (client)
RUN npm run build

# Build SSR server with Bun
RUN bun build server.tsx --outdir dist-ssr --target bun --minify && \
    if [ ! -d "dist-ssr" ] || [ ! -f "dist-ssr/server.js" ]; then \
      echo "ERROR: dist-ssr/server.js not found after build!"; \
      ls -la dist-ssr/ || echo "dist-ssr directory does not exist"; \
      exit 1; \
    fi && \
    echo "✅ SSR build successful - dist-ssr/server.js exists"

# Production stage
FROM oven/bun:latest

WORKDIR /app

# Copy package files and lockfile
COPY package*.json ./
COPY bun.lock* ./
RUN bun install --frozen-lockfile --production

# Copy built files - React Router v7 builds to build/client/
COPY --from=builder /app/build ./build
COPY --from=builder /app/dist-ssr ./dist-ssr
# Copy index.html from root (React Router v7 uses the root index.html)
COPY --from=builder /app/index.html ./index.html

EXPOSE 3000

CMD ["bun", "run", "dist-ssr/server.js"]

