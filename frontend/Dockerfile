# Image légère pour exécuter le build existant
FROM node:20-alpine

WORKDIR /app

# Copier le build standalone déjà généré sur ta machine
COPY .next/standalone ./
COPY .next/static ./.next/static
COPY public ./public

EXPOSE 3000

CMD ["node", "server.js"]