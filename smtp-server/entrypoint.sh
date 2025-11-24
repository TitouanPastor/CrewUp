#!/bin/bash
set -e

# Default values
HOSTNAME=${HOSTNAME:-smtp.example.com}
DOMAIN=${DOMAIN:-example.com}
RELAYHOST=${RELAYHOST:-}
RELAYHOST_USERNAME=${RELAYHOST_USERNAME:-}
RELAYHOST_PASSWORD=${RELAYHOST_PASSWORD:-}
MYNETWORKS=${MYNETWORKS:-127.0.0.0/8 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16}

echo "Configuring Postfix..."

# Create main.cf
cat > /etc/postfix/main.cf <<EOF
# Basic settings
smtpd_banner = \$myhostname ESMTP
biff = no
append_dot_mydomain = no
readme_directory = no
compatibility_level = 3.6

# TLS parameters
smtpd_tls_cert_file=/etc/ssl/certs/ssl-cert-snakeoil.pem
smtpd_tls_key_file=/etc/ssl/private/ssl-cert-snakeoil.key
smtpd_tls_security_level=may
smtp_tls_security_level=may
smtp_tls_session_cache_database = btree:\${data_directory}/smtp_scache

# Network settings
myhostname = ${HOSTNAME}
mydomain = ${DOMAIN}
myorigin = \$mydomain
mydestination = localhost
mynetworks = ${MYNETWORKS}
relayhost = ${RELAYHOST}
inet_interfaces = all
inet_protocols = ipv4

# Size limits
mailbox_size_limit = 0
message_size_limit = 10240000

# Other settings
recipient_delimiter = +
alias_maps = hash:/etc/postfix/aliases
alias_database = hash:/etc/postfix/aliases
EOF

# Configure relay authentication if credentials provided
if [ -n "$RELAYHOST_USERNAME" ] && [ -n "$RELAYHOST_PASSWORD" ]; then
    echo "Configuring SMTP relay authentication..."

    # Add SASL configuration to main.cf
    cat >> /etc/postfix/main.cf <<EOF

# SMTP relay authentication
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = lmdb:/etc/postfix/sasl_passwd
smtp_sasl_security_options = noanonymous
smtp_sasl_tls_security_options = noanonymous
EOF

    # Create sasl_passwd file
    echo "${RELAYHOST} ${RELAYHOST_USERNAME}:${RELAYHOST_PASSWORD}" > /etc/postfix/sasl_passwd

    # Run postmap and check if it succeeds
    if postmap /etc/postfix/sasl_passwd; then
        echo "SASL password map created successfully"

        # List files to debug
        ls -la /etc/postfix/sasl_passwd* || echo "No sasl_passwd files found"

        # Set permissions on files that exist
        chmod 600 /etc/postfix/sasl_passwd
        # Handle both .db and .lmdb formats
        if [ -f /etc/postfix/sasl_passwd.db ]; then
            chmod 600 /etc/postfix/sasl_passwd.db
        elif [ -f /etc/postfix/sasl_passwd.lmdb ]; then
            chmod 600 /etc/postfix/sasl_passwd.lmdb
        else
            echo "WARNING: Neither sasl_passwd.db nor .lmdb found!"
        fi
    else
        echo "ERROR: Failed to create SASL password map"
        exit 1
    fi
fi

# Create aliases file
echo "postmaster: root" > /etc/postfix/aliases
postalias /etc/postfix/aliases

# Set permissions
chown -R postfix:postfix /var/spool/postfix
chmod 755 /var/spool/postfix

echo "Postfix configuration complete"
echo "Hostname: ${HOSTNAME}"
echo "Domain: ${DOMAIN}"
echo "Relayhost: ${RELAYHOST:-none (direct sending)}"
echo "Networks: ${MYNETWORKS}"

# Execute the command passed as arguments
exec "$@"
