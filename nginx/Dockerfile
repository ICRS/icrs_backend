FROM nginx:latest

COPY nginx-prod.conf /etc/nginx/nginx.conf
COPY directory.html /usr/share/nginx/html/index.html

CMD ["nginx", "-g", "daemon off;"]
