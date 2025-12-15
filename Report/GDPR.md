# GDPR Compliance Documentation

## Overview

CrewUp processes personal data of EU users and must comply with the General Data Protection Regulation (GDPR). This document outlines our compliance measures and identifies areas for improvement.

## Data We Collect

| Data Category | Purpose | Legal Basis |
|--------------|---------|-------------|
| Email address | Account identification, notifications | Contract performance |
| Name (first, last) | Profile display, social features | Consent |
| Profile picture URL | User identification | Consent |
| Interests | Event recommendations | Consent |
| Location (lat/lng) | Event discovery, safety alerts | Consent |
| Chat messages | Group communication | Contract performance |
| Reputation score | Trust system | Legitimate interest |

## GDPR Article Compliance

### Art. 5 - Principles (Data Security)
**Status**: ✅ Implemented

- **Integrity & Confidentiality**: All data encrypted in transit (TLS 1.3)
- **Storage Security**: PostgreSQL with access controls, Kubernetes Secrets
- **Access Logging**: All API requests logged with user ID for audit
- **Minimization**: Only essential data collected for each feature

### Art. 8 - Conditions for Child's Consent
**Status**: ⚠️ Requires Implementation

CrewUp targets nightlife/event coordination for adults. We should:
- [ ] Add age verification during registration (minimum 18 years)
- [ ] Display terms requiring user confirmation of legal age
- [ ] Block accounts if underage use is suspected

**Recommendation**: Implement age gate in Keycloak registration flow.

### Art. 12 - Transparent Information
**Status**: ⚠️ Requires Implementation

Users must be informed about data processing. Required actions:
- [ ] Create Privacy Policy page in frontend
- [ ] Display data collection notice at registration
- [ ] Provide clear explanation of each data field's purpose

### Art. 15-20 - Data Subject Rights
**Status**: ⚠️ Requires Implementation

Users have rights to access, rectify, and delete their data:

| Right | Article | Implementation Status |
|-------|---------|----------------------|
| Access | Art. 15 | ⚠️ Need data export endpoint |
| Rectification | Art. 16 | ✅ Profile update via `/api/v1/users/me` |
| Erasure | Art. 17 | ⚠️ Need account deletion endpoint |
| Portability | Art. 20 | ⚠️ Need data export in machine-readable format |

**Recommended Endpoints**:
```
GET  /api/v1/users/me/data-export  → Download all user data (JSON)
DELETE /api/v1/users/me            → Delete account and all associated data
```

### Art. 25 - Data Protection by Design
**Status**: ✅ Implemented

- **Default Privacy**: Events can be marked private
- **Minimal Data**: Only required fields are mandatory
- **Pseudonymization**: Internal UUIDs used instead of email for references

### Art. 32 - Security of Processing
**Status**: ✅ Implemented

- Authentication via Keycloak (industry standard)
- JWT tokens with short expiration
- Database access restricted to services
- No public database exposure

## Data Retention

| Data Type | Retention Period | Deletion Trigger |
|-----------|-----------------|------------------|
| User profiles | Account lifetime | Account deletion |
| Chat messages | 1 year | Group deletion or user request |
| Safety alerts | 30 days | Automatic cleanup |
| Event data | Until event end + 30 days | Creator deletion |

## Third-Party Data Sharing

CrewUp does not share personal data with third parties except:
- **Keycloak**: Authentication provider (self-hosted, no external transfer)
- **Map tiles**: OpenStreetMap (no personal data sent)

## Contact

For GDPR-related inquiries:
- Data Controller: CrewUp Development Team
- Email: titouan.pastor@gmail.com
