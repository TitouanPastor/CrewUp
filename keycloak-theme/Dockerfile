# Keycloak with CrewUp Custom Theme
FROM quay.io/keycloak/keycloak:23.0

# Copy the theme JAR to providers
COPY build_keycloak/keycloak-theme-for-kc-22-and-above.jar /opt/keycloak/providers/crewup-theme.jar

# Build Keycloak with the custom theme
RUN /opt/keycloak/bin/kc.sh build

# Run Keycloak
ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]
