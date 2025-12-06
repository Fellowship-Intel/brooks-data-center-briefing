# Dockerfile for Node.js API service
FROM node:20-slim

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy package files
COPY server/package.json server/package-lock.json* ./

# Install all dependencies (including dev dependencies for build)
RUN npm ci

# Copy source code
COPY server/src ./src
COPY server/tsconfig.json ./

# Build TypeScript
RUN npm run build

# Remove dev dependencies after build
RUN npm prune --production

# Cloud Run expects the service to listen on $PORT (default 8000)
ENV PORT=8000
ENV NODE_ENV=production

# Expose port
EXPOSE 8000

# Start server
CMD ["node", "dist/index.js"]

