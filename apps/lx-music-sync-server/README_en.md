## Introduction

**LX Music Sync Server (Enhanced Edition)** is an enhanced fork of [lyswhut/lx-music-sync-server](https://github.com/lyswhut/lx-music-sync-server). In addition to data sync with the LX Music desktop client, it bundles a powerful **Web player**.

Key features:

- **LX Music data sync**: Sync playlists, queues and settings with the LX Music desktop client
- **Web player**: Modern UI with aggregated multi-source search (NetEase, QQ, Kugou, Kuwo, Migu, Bilibili, etc.)
- **Auto cache**: Auto-cache lyrics, links and audio files for smooth playback on weak networks
- **Lyrics card sharing**: Generate beautiful lyrics posters (vertical / horizontal / square, dark / light / album theme)
- **Multiple themes**: Forest, Deep Shark, Warm Sun, Crimson Moon, etc. with auto dark mode
- **Subsonic protocol**: Compatible with Subsonic clients (Substreamer, Symfonium, DSub, etc.)
- **Multi-user management**: Fine-grained control over admins, public users, traffic / upload / delete limits
- **Cross-platform desktop client**: Windows / macOS / Linux desktop builds available

More info:

- [Project site](https://xcq0607.github.io/lxserver/)
- [GitHub repository](https://github.com/XCQ0607/lxserver)
- [Changelog](https://github.com/XCQ0607/lxserver/blob/main/changelog.md)

## Usage

1. After installation, visit:
   - **Web player**: `http://SERVER_IP:port/`
   - **Admin panel**: `http://SERVER_IP:port{ADMIN_PATH}`
2. Log in with the admin password to manage users and configure LX sync accounts
3. To enable LX Music desktop sync, configure the desktop client with:
   - Sync server: `http://SERVER_IP:port`
   - Account: `admin`
   - Password: the `LX Sync Admin Account Password` you set during installation

## Notes

- **CHANGE THE DEFAULT PASSWORDS** after installation (admin panel, Web player, LX sync)
- Leaving `LX Sync Admin Account Password` empty disables the LX desktop sync, but the Web player still works
- Data, logs and cache are persisted to `data`, `logs`, `cache` — back them up regularly
- The `music` directory is for local audio files — drop files in when you need them
- Anonymous telemetry and update notifications are disabled by default
- This project is licensed under **Apache-2.0**
