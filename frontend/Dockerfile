FROM node:22-alpine

WORKDIR /app

ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

COPY package.json package-lock.json* ./

RUN npm install

COPY . .

RUN npm run build

EXPOSE 4173

CMD ["npm", "run", "preview"]
