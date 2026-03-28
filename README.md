# Cloudflare WARP – Python Desktop Client

A Python/Qt (PySide6) desktop application that replicates the **Cloudflare WARP** Windows client UI and functionality with pixel-perfect fidelity.

## Features

| Feature | Description |
|---------|-------------|
| **Connect / Disconnect** | Toggle WARP with an animated circular power button |
| **Live status** | QPainter-rendered glow ring (orange = disconnected, blue = connected, pulsing = in-progress) |
| **Click effects** | Press-shrink animation on the toggle button, hover highlights on all interactive elements |
| **Screen positioning** | Window appears in the bottom-right corner of the screen (near system tray) matching real Cloudflare WARP |
| **Connection info card** | Shows your tunnelled IP, location and Cloudflare data-centre once connected |
| **Settings dialog** | General preferences, DNS mode, split-tunnel IP list, account type with custom-styled tabs and controls |
| **System-tray icon** | Qt QSystemTrayIcon; double-click to show, right-click menu for quick connect/disconnect/quit |
| **Real warp-cli support** | Calls the official `warp-cli` binary when it is installed |
| **Simulation fallback** | Works fully in demo mode when warp-cli is absent |

## Requirements

- Python 3.10+
- [PySide6](https://doc.qt.io/qtforpython/) ≥ 6.5
- [Pillow](https://python-pillow.org/) ≥ 10.0

## Installation

```bash
# Clone the repository
git clone https://github.com/microshark2024/cloudflareWrapPython.git
cd cloudflareWrapPython

# Install dependencies
pip install -r requirements.txt

# Run
python run.py
# or after pip install -e .
cloudflare-warp-py
```

## Project structure

```
cloudflare_warp/
├── __init__.py
├── app.py                  # Application coordinator
├── main.py                 # Entry point
├── core/
│   ├── config.py           # JSON-based persistent configuration
│   └── warp_service.py     # warp-cli wrapper + simulation fallback
└── ui/
    ├── main_window.py      # Main window (toggle button, status, info card)
    ├── settings_dialog.py  # Settings modal dialog
    ├── tray_icon.py        # System-tray icon (Qt QSystemTrayIcon)
    └── theme.py            # Design tokens (colours, fonts, sizes, utilities)
run.py                      # Top-level launcher
requirements.txt
setup.py
```

## Real warp-cli integration

When the official Cloudflare WARP client is installed the app detects
`warp-cli.exe` (Windows) or `/usr/bin/warp-cli` (Linux) and delegates
all connect/disconnect/status operations to it.

Expected CLI paths:
- **Windows** – `C:\Program Files\Cloudflare\Cloudflare WARP\warp-cli.exe`
- **Linux** – `/usr/bin/warp-cli` or `/usr/local/bin/warp-cli`

## Configuration

Settings are stored in `~/.config/cloudflare-warp-py/config.json`:

```json
{
  "theme": "dark",
  "start_minimized": false,
  "start_on_login": false,
  "dns_mode": "warp",
  "split_tunnel_mode": "exclude",
  "split_tunnel_ips": [],
  "account_type": "free",
  "show_notifications": true
}
```

## License

MIT