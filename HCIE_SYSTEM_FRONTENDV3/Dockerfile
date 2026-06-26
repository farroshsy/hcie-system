# HCIE Frontend V3 — multi-stage Next.js (standalone) image.
#
# Fix history: the original Dockerfile used ``npm ci --only=production``
# in the builder stage, which strips devDependencies (typescript, postcss,
# tailwindcss, eslint-config-next) that ``next build`` requires. The
# replacement installs all deps in the builder, then carries only the
# standalone bundle into the runtime image.
#
# Build context: HCIE_SYSTEM_FRONTENDV3/ (next.config.js, package.json, src/).

############################
# 1) deps — full install   #
############################
FROM node:20-alpine AS deps
WORKDIR /app

# Native deps for some packages (sharp, native bindings on alpine)
RUN apk add --no-cache libc6-compat python3 make g++

COPY package.json package-lock.json* ./
# Use ``npm install`` (not ``npm ci``) because the lockfile is occasionally
# updated by package upgrades; CI environments override this with ``npm ci``.
RUN npm install --no-audit --no-fund

############################
# 2) builder — next build  #
############################
FROM node:20-alpine AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Allow the build step to inline NEXT_PUBLIC_* envs if provided.
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_WS_URL
ARG NEXT_PUBLIC_APP_ENV
ARG NEXT_PUBLIC_BACKEND_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_WS_URL=${NEXT_PUBLIC_WS_URL}
ENV NEXT_PUBLIC_APP_ENV=${NEXT_PUBLIC_APP_ENV}
ENV NEXT_PUBLIC_BACKEND_URL=${NEXT_PUBLIC_BACKEND_URL}

RUN npm run build

############################
# 3) runner — minimal      #
############################
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

RUN addgroup --system --gid 1001 nodejs \
 && adduser --system --uid 1001 nextjs

# ``public/`` carries the sealed paper artifacts (e.g. baseline_comparison.json,
# r12_ablation.json, topology_taxonomy.json) that /review/* loads at runtime,
# plus any other static assets. Standalone Next.js does NOT auto-include this
# directory, so we copy it explicitly. Previously the runner only created an
# empty ./public and the JSONs were docker-cp'd in after each rebuild — that
# pattern silently broke every image rebuild and left /review/ablation etc.
# stuck on "Loading…".
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000

CMD ["node", "server.js"]
