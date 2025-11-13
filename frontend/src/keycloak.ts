import Keycloak from 'keycloak-js';

// Keycloak configuration from environment variables
const keycloakConfig = {
  url: import.meta.env.VITE_KEYCLOAK_URL || 'https://keycloak.ltu-m7011e-3.se',
  realm: import.meta.env.VITE_KEYCLOAK_REALM || 'crewup',
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'crewup-client',
};

// Initialize Keycloak instance
const keycloak = new Keycloak(keycloakConfig);

export default keycloak;
