FROM node:22-bookworm-slim@sha256:83f487e0a63425e5b4d146fb5e5be574bcbe1b7b843d3ebafdd95eaf7767a7e5 AS build
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build && node server/build-manifest.mjs

FROM node:22-bookworm-slim@sha256:83f487e0a63425e5b4d146fb5e5be574bcbe1b7b843d3ebafdd95eaf7767a7e5
ENV NODE_ENV=production HOST=0.0.0.0 PORT=4173
WORKDIR /app
COPY --from=build /build/dist ./dist
COPY --from=build /build/build-manifest.json ./build-manifest.json
COPY server/index.mjs server/scenarios.mjs ./server/
COPY INTER-LICENSE.txt ./INTER-LICENSE.txt
USER node
EXPOSE 4173
CMD ["node", "server/index.mjs"]
