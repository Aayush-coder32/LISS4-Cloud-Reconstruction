FROM node:20-alpine

ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
ARG NEXT_PUBLIC_MAPBOX_TOKEN=

ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}
ENV NEXT_PUBLIC_MAPBOX_TOKEN=${NEXT_PUBLIC_MAPBOX_TOKEN}

WORKDIR /app

COPY frontend/package.json /app/package.json
RUN npm install

COPY frontend /app
RUN npm run build

CMD ["npm", "run", "start"]
