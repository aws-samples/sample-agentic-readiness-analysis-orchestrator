FROM php:8.2-apache

# Install MySQL extension and other dependencies
RUN apt-get update && apt-get install -y \
    default-mysql-client \
    curl \
    && docker-php-ext-install pdo pdo_mysql \
    && rm -rf /var/lib/apt/lists/*

# Enable Apache mod_rewrite
RUN a2enmod rewrite

# Copy application code
COPY index.php /var/www/html/
COPY .htaccess /var/www/html/

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /var/www/html appuser \
    && chown -R appuser:appuser /var/www/html /var/run/apache2 /var/lock/apache2 /var/log/apache2

# Expose port
EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost/ || exit 1

USER appuser
