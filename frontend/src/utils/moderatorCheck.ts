import keycloak from '../keycloak';

/**
 * Check if the current user has the Moderator role.
 *
 * Checks both:
 * 1. realm_access.roles (realm-level roles)
 * 2. resource_access.{client_id}.roles (client-level roles)
 *
 * @returns true if user has Moderator role, false otherwise
 */
export const isModerator = (): boolean => {
  if (!keycloak.authenticated || !keycloak.tokenParsed) {
    return false;
  }

  const tokenParsed = keycloak.tokenParsed as any;

  // Check realm-level roles
  const realmRoles = tokenParsed.realm_access?.roles || [];
  if (realmRoles.includes('Moderator')) {
    return true;
  }

  // Check client-level roles
  const clientId = keycloak.clientId || 'crewup-client';
  const clientRoles = tokenParsed.resource_access?.[clientId]?.roles || [];
  if (clientRoles.includes('Moderator')) {
    return true;
  }

  return false;
};
