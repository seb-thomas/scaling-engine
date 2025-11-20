FROM nginx:1.19.0-alpine

RUN rm /etc/nginx/conf.d/default.conf
# Use React config for frontend routing (routes / to React, /api/ to Django)
COPY nginx.conf.react /etc/nginx/conf.d/