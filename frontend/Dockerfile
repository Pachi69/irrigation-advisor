# Etapa 1: build del frontend con Vite
FROM node:22-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Vite hornea estas variables en build-time
ARG VITE_API_URL
ARG VITE_VAPID_PUBLIC_KEY
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_VAPID_PUBLIC_KEY=$VITE_VAPID_PUBLIC_KEY

RUN npm run build

# Etapa 2: servir el dist/ estatico con nginx
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
