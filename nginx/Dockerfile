FROM nginx:1.19.0-alpine

RUN rm /etc/nginx/conf.d/default.conf
# Use React config for frontend routing
COPY nginx.conf.react /etc/nginx/conf.d/default.conf