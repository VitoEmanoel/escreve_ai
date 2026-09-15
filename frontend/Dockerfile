FROM node:20-alpine AS build

WORKDIR /app

# Instalar dependências
COPY package*.json ./
RUN npm install

# Copiar código fonte e buildar
COPY . .
RUN npm run build

# Etapa 2: Nginx
FROM nginx:alpine

# Remover a configuração default do Nginx
RUN rm /etc/nginx/conf.d/default.conf

# Copiar nova configuração do nginx com proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar os arquivos buildados do React
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
