import Keycloak from 'keycloak-js';

// Runtime configuration interface
declare global {
  interface Window {
    __RUNTIME_CONFIG__?: {
      VITE_KEYCLOAK_URL: string;
      VITE_KEYCLOAK_REALM: string;
      VITE_KEYCLOAK_CLIENT_ID: string;
    };
  }
}

// Get config from runtime (injected by entrypoint.sh) or fallback to build-time env vars
const getRuntimeConfig = () => {
  if (typeof window !== 'undefined' && window.__RUNTIME_CONFIG__) {
    return window.__RUNTIME_CONFIG__;
  }
  return {
    VITE_KEYCLOAK_URL: import.meta.env.VITE_KEYCLOAK_URL || 'https://keycloak.ltu-m7011e-3.se',
    VITE_KEYCLOAK_REALM: import.meta.env.VITE_KEYCLOAK_REALM || 'crewup',
    VITE_KEYCLOAK_CLIENT_ID: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'crewup-client',
  };
};

const config = getRuntimeConfig();

// Keycloak configuration from environment variables
const keycloakConfig = {
  url: import.meta.env.VITE_KEYCLOAK_URL || 'https://keycloak.ltu-m7011e-3.se',
  realm: import.meta.env.VITE_KEYCLOAK_REALM || 'crewup',
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'crewup-test',
};

// Initialize Keycloak instance
const keycloak = new Keycloak(keycloakConfig);

export default keycloak;
