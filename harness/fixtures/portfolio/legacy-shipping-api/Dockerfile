# Multi-stage Dockerfile for shipping-rate-api
# Detected: Node.js application (Express 3.4.8) listening on port 8080

# --- Build Stage ---
FROM node:18-alpine AS build

WORKDIR /app

# Copy package descriptor first for dependency caching
COPY package.json ./

# Install production dependencies only
RUN npm install --production --ignore-engines

# Copy application source
COPY server.js ./

# --- Runtime Stage ---
FROM node:18-alpine

WORKDIR /app

# Create non-root user and group
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Copy only the necessary artifacts from build stage
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./
COPY --from=build /app/server.js ./

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE 8080

# Health check - use wget to verify the server is responding (401 means alive)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/rates || exit 1

# Start the application directly (not via forever)
CMD ["node", "server.js"]
