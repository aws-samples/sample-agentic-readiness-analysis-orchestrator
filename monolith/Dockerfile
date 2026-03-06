FROM php:8.2-apache

# Install MySQL extension and other dependencies
RUN apt-get update && apt-get install -y \
    default-mysql-client \
    && docker-php-ext-install pdo pdo_mysql \
    && rm -rf /var/lib/apt/lists/*

# Enable Apache mod_rewrite
RUN a2enmod rewrite

# Copy application code
COPY index.php /var/www/html/
COPY .htaccess /var/www/html/

# Expose port
EXPOSE 80
