#!/bin/sh

# Replace environment variables in config.js
envsubst < /usr/share/nginx/html/config.template.js > /usr/share/nginx/html/config.js

# Start nginx
nginx -g 'daemon off;'
