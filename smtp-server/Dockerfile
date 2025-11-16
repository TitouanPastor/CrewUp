FROM alpine:3.19

# Install Postfix and required packages
RUN apk add --no-cache \
    postfix \
    postfix-pcre \
    libsasl \
    cyrus-sasl \
    cyrus-sasl-login \
    cyrus-sasl-crammd5 \
    ca-certificates \
    bash \
    && rm -rf /var/cache/apk/*

# Create necessary directories
RUN mkdir -p /var/spool/postfix \
    && mkdir -p /var/mail \
    && mkdir -p /etc/postfix

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose SMTP ports
EXPOSE 25 587

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]
CMD ["postfix", "start-fg"]
