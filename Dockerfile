# Stage 1: Build frontend
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python app + built frontend
FROM python:3.12-slim
WORKDIR /app

# Install system dependencies for psycopg2-binary, lxml, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy built frontend from stage 1
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Alembic config + migrations need to be in place
# (already copied with COPY . . above)

EXPOSE 8080

COPY start.sh ./
RUN chmod +x start.sh

CMD ["./start.sh"]
