# Multi-stage build: compile the Vite app, then serve the static output with
# a minimal nginx. Not run in this session (no Docker daemon available here —
# see docker-compose.yml's top-of-file note) but written to the same standard
# as apps/api/Dockerfile, which was verified to build and run.
FROM node:22-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_DEMO_BUSINESS_SLUG=atelier
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_DEMO_BUSINESS_SLUG=$VITE_DEMO_BUSINESS_SLUG
RUN npm run build

FROM nginx:1.27-alpine AS serve
COPY --from=build /app/dist /usr/share/nginx/html
# SPA fallback: client-side routes (e.g. /book/:serviceId) must resolve to
# index.html rather than a 404 from nginx.
RUN printf 'server {\n\
    listen 80;\n\
    root /usr/share/nginx/html;\n\
    location / {\n\
        try_files $uri /index.html;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf
EXPOSE 80
