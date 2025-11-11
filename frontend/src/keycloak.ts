import Keycloak from 'keycloak-js';

// Keycloak configuration
const keycloakConfig = {
  url: 'https://keycloak.ltu-m7011e-3.se',
  realm: 'crewup',
  clientId: 'crewup-frontend',
  // clientId: 'crewup-test', // For local testing
};

// Initialize Keycloak instance
const keycloak = new Keycloak(keycloakConfig);

export default keycloak;
