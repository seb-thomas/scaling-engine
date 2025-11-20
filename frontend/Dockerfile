FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source files
COPY . .

# Build the app
RUN npm run build
# Build SSR server (with verification)
RUN npm run ssr:build:server && \
    if [ ! -d "dist-ssr" ] || [ ! -f "dist-ssr/server.js" ]; then \
      echo "ERROR: dist-ssr/server.js not found after build!"; \
      ls -la dist-ssr/ || echo "dist-ssr directory does not exist"; \
      exit 1; \
    fi && \
    echo "✅ SSR build successful - dist-ssr/server.js exists"

# Production stage
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy built files - React Router v7 builds to build/client/
COPY --from=builder /app/build ./build
COPY --from=builder /app/dist-ssr ./dist-ssr
# Copy index.html from root (React Router v7 uses the root index.html)
COPY --from=builder /app/index.html ./index.html

EXPOSE 3000

CMD ["node", "dist-ssr/server.js"]

