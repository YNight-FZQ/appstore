## Introduction

**3X-UI** is an open-source, powerful Xray panel that provides an intuitive web interface to manage and monitor the Xray core.

Key features:

- **Multi-protocol support**: Vmess, Vless, Trojan, ShadowSocks, Wireguard, Hysteria, Tunnel, Mixed, HTTP, Tun, MTProto, AmneziaWG, etc.
- **Multi-user management**: Create users, set traffic limits, monitor usage, manage expirations
- **Multi-language UI**: Built-in support for Chinese, English, Russian, Persian, Arabic and 10+ other languages
- **Security**: Built-in Fail2ban, forced VMess AEAD encryption, TLS certificate management
- **Subscription links**: Auto-generated subscription links compatible with major clients

For more information:

- [Official documentation](https://docs.sanaei.dev/)
- [GitHub repository](https://github.com/MHSanaei/3x-ui)

## Usage

1. After installation, open `http://SERVER_IP:panel_port` to access the 3X-UI panel
2. On first visit, you'll be prompted to set an admin username and password
3. Use the panel to create users and inbounds for various proxy protocols
4. The default Xray inbound port is `8443` (configurable during installation)

## Notes

- The panel listens on port `2053` by default; the Xray inbound port is `8443` by default. Make sure your firewall allows traffic on these ports
- Database and certificates are persisted to `data/db` and `data/cert` — back these up regularly
- This project is licensed under **GPL-3.0**
