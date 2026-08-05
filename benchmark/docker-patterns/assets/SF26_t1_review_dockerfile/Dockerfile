# Insecure Dockerfile with multiple anti-patterns
# This is a real-world-style Dockerfile for a Node.js Express API

FROM node:latest

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy everything
COPY . .

# Install dependencies
RUN npm install

# Set environment variables including secrets
ENV NODE_ENV=production
ENV DATABASE_URL=postgres://admin:s3cretP@ssw0rd@db:5432/myapp
ENV JWT_SECRET=super-secret-jwt-key-do-not-share
ENV API_KEY=sk-proj-abc123def456

EXPOSE 3000

CMD ["node", "server.js"]
