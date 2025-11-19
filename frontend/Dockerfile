FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source files
COPY . .

# Build the app
RUN npm run build
RUN npm run ssr:build:server

# Production stage
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy built files
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/dist-ssr ./dist-ssr
COPY --from=builder /app/index.html ./index.html

EXPOSE 3000

CMD ["node", "dist-ssr/server.js"]

