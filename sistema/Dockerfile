# Dockerfile — MAG Sistema Frontend (Next.js)
# Proyecto GCP: magia

# ── Stage 1: Build ──
FROM node:22-alpine AS builder
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

RUN npm run build

# ── Stage 2: Production ──
FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

# Copiar build standalone + assets
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

ENV PORT=3000
EXPOSE 3000

CMD ["node", "server.js"]
