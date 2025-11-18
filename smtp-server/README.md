# CrewUp SMTP Server

A simple, self-hosted Postfix SMTP server for sending verification emails from Keycloak.

## Features

- Based on Alpine Linux (minimal and secure)
- Postfix SMTP server
- Support for direct sending or SMTP relay
- Configurable via environment variables
- No external dependencies

## Building the Image

Build the Docker image:

```bash
cd smtp-server
docker build -t crewup-smtp:latest .
```

## Tagging and Pushing to GitHub Container Registry

1. Tag the image for GitHub Container Registry:

```bash
docker tag crewup-smtp:latest ghcr.io/titouanpastor/crewup-smtp:latest
```

2. Login to GitHub Container Registry (requires a GitHub Personal Access Token with `write:packages` permission):

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u titouanpastor --password-stdin
```

3. Push the image:

```bash
docker push ghcr.io/titouanpastor/crewup-smtp:latest
```

4. Make the package public (optional):
   - Go to https://github.com/TitouanPastor?tab=packages
   - Click on the `crewup-smtp` package
   - Go to "Package settings"
   - Scroll down to "Danger Zone" and click "Change visibility"
   - Select "Public"

## Environment Variables

The container accepts the following environment variables:

- `HOSTNAME` - SMTP server hostname (default: smtp.example.com)
- `DOMAIN` - Domain for outgoing emails (default: example.com)
- `RELAYHOST` - Optional SMTP relay host (e.g., `[smtp.gmail.com]:587`)
- `RELAYHOST_USERNAME` - Username for relay authentication
- `RELAYHOST_PASSWORD` - Password for relay authentication
- `MYNETWORKS` - Allowed networks (default: local and private networks)

## Testing Locally

Run the container locally for testing:

```bash
docker run -d \
  -p 1025:25 \
  -p 1587:587 \
  -e HOSTNAME=smtp.test.local \
  -e DOMAIN=test.local \
  --name smtp-test \
  crewup-smtp:latest
```

Send a test email:

```bash
# Install swaks if not already installed
# apt-get install swaks  # Debian/Ubuntu
# brew install swaks     # macOS

swaks --to test@example.com \
  --from noreply@test.local \
  --server localhost:1025 \
  --body "Test email"
```

Check logs:

```bash
docker logs smtp-test
```

Cleanup:

```bash
docker stop smtp-test
docker rm smtp-test
```

## Security Notes

- This image runs Postfix without TLS/SSL for internal cluster communication
- If using SMTP relay, credentials are passed as environment variables
- The image is designed to be used within a Kubernetes cluster
- For production use, consider:
  - Using SMTP relay (Gmail, SendGrid, AWS SES, etc.) for better deliverability
  - Implementing proper monitoring and logging
  - Setting up SPF, DKIM, and DMARC records for your domain

## Files

- `Dockerfile` - Container image definition
- `entrypoint.sh` - Configuration script that runs on container startup
- `README.md` - This file
