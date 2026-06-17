FROM node:20-alpine AS base

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=development

EXPOSE 3000

CMD ["npm", "run", "dev"]
