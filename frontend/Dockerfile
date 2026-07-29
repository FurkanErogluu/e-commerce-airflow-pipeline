# Dünyanın en popüler web sunucularından Nginx'in hafif versiyonu
FROM nginx:alpine

# Bizim tasarladığımız HTML'i, Nginx'in ana yayın dizinine kopyala
COPY index.html /usr/share/nginx/html/index.html

# İnternet portu
EXPOSE 80

# Nginx'i arka planda çalıştır
CMD ["nginx", "-g", "daemon off;"]