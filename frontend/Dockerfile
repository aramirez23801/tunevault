# TuneVault Frontend — Nginx
FROM nginx:alpine

# Copy frontend files to Nginx's default serve directory
COPY . /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Nginx runs automatically
CMD ["nginx", "-g", "daemon off;"]
