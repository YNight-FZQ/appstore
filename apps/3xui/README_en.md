# 3X-UI one-click six-protocol local app

Select 3.11.0-local.2. The OnePanel installation hook starts the managed official 3.11.0 container, safely generates administrator/node credentials, creates six inbounds and their public Hosts, enables subscriptions, configures the existing matching OpenResty HTTPS site, and exports client profiles.

Keep the prefilled hostnames and ports for this server. Administrator credentials may be left blank for secure runtime generation. Read data/INSTALL-RESULT.md in the installed app directory after installation. It contains credentials and must remain private.

Restarts preserve the database and generated identities. The proxy container does not mount Docker's socket. Only the application's managed proxy file is installed or removed, with configuration validation and rollback.

The existing HTTPS site, DNS and cloud firewall are prerequisites. OCI/Cloudflare control-plane rules cannot be changed without their management access. The existing independent WireGuard stays running; the new inbound defaults to UDP 51821.

See CONFIGURATION.md for field definitions, lifecycle behavior and validation boundaries. Prior local.1 and 3.8.5 templates remain as references. Upstream: https://github.com/MHSanaei/3x-ui . License: GPL-3.0.

## Upgrade and validation boundary

Cross-version upgrades are disabled: older installations do not have the one-click state and readiness marker, and the supplied upgrade hook does not migrate them. Back up existing databases and plan migration separately.

The default domains come from the supplied archive and must match the deployment. Automatic proxy configuration requires an existing HTTPS site with a matching valid certificate and a host-networked 1Panel OpenResty container. The host needs Python 3, Docker Compose, OpenSSL, ss and nsenter, with a root installation hook.

This repository import does not perform server installation. The archive's integration reports are historical evidence supplied with the attachment, not tests rerun here. See VALIDATION.md for the checks performed during this import.
