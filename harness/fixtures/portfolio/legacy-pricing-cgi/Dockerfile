# =============================================================================
# Multi-stage Dockerfile for legacy-pricing-cgi
# Builds the C++ CGI binary and serves it via Apache httpd with mod_cgi
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Build
# ---------------------------------------------------------------------------
FROM gcc:12 AS builder

WORKDIR /build

# Copy source and Makefile
COPY Makefile pricing.cpp ./

# Compile the CGI binary
RUN make all

# ---------------------------------------------------------------------------
# Stage 2: Runtime
# ---------------------------------------------------------------------------
FROM httpd:2.4-alpine

# Install curl for healthcheck
RUN apk add --no-cache curl

# Enable CGI module in Apache configuration
RUN sed -i 's/#LoadModule cgid_module/LoadModule cgid_module/' /usr/local/apache2/conf/httpd.conf && \
    sed -i 's/#LoadModule cgi_module/LoadModule cgi_module/' /usr/local/apache2/conf/httpd.conf && \
    echo 'Listen 8080' >> /usr/local/apache2/conf/httpd.conf && \
    sed -i 's/Listen 80/# Listen 80/' /usr/local/apache2/conf/httpd.conf && \
    echo 'ScriptAlias /cgi-bin/ "/usr/local/apache2/cgi-bin/"' >> /usr/local/apache2/conf/httpd.conf && \
    echo '<Directory "/usr/local/apache2/cgi-bin">' >> /usr/local/apache2/conf/httpd.conf && \
    echo '    AllowOverride None' >> /usr/local/apache2/conf/httpd.conf && \
    echo '    Options +ExecCGI' >> /usr/local/apache2/conf/httpd.conf && \
    echo '    Require all granted' >> /usr/local/apache2/conf/httpd.conf && \
    echo '</Directory>' >> /usr/local/apache2/conf/httpd.conf && \
    echo 'ServerName localhost' >> /usr/local/apache2/conf/httpd.conf

# Copy the compiled CGI binary from the build stage
COPY --from=builder /build/pricing.cgi /usr/local/apache2/cgi-bin/pricing.cgi
RUN chmod +x /usr/local/apache2/cgi-bin/pricing.cgi

# Create pricing rules directory and a sample rules file
RUN mkdir -p /etc/pricing && \
    echo "SAMPLE-SKU|9.99" > /etc/pricing/rules.dat

# Create a non-root user and adjust permissions
RUN addgroup -S appgroup && adduser -S appuser -G appgroup && \
    chown -R appuser:appgroup /usr/local/apache2/logs && \
    chown -R appuser:appgroup /usr/local/apache2/cgi-bin && \
    chown -R appuser:appgroup /etc/pricing

# Switch to non-root user
USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/cgi-bin/pricing.cgi?sku=HEALTH&qty=1 || exit 1

CMD ["httpd-foreground"]
