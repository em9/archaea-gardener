#!/usr/bin/env python3
import sys
import os
import json
import base64
import hashlib
import subprocess
import getpass

def encrypt_html(input_path, output_path, password):
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        sys.exit(1)

    with open(input_path, "rb") as f:
        plaintext = f.read()

    # Generate random 16-byte salt and 16-byte IV
    salt = os.urandom(16)
    iv = os.urandom(16)

    # Derive 256-bit AES key using PBKDF2 with SHA-256 (100,000 iterations)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000, 32)

    # Encrypt with openssl AES-256-CBC
    proc = subprocess.Popen(
        [
            "openssl", "enc", "-aes-256-cbc",
            "-K", key.hex(),
            "-iv", iv.hex()
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    ciphertext, err = proc.communicate(plaintext)
    if proc.returncode != 0:
        print("Encryption error:", err.decode("utf-8", errors="ignore"))
        sys.exit(1)

    payload = {
        "salt": base64.b64encode(salt).decode("ascii"),
        "iv": base64.b64encode(iv).decode("ascii"),
        "cipher": base64.b64encode(ciphertext).decode("ascii")
    }

    payload_json = json.dumps(payload)

    # Generate lock screen HTML
    lock_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Protected · Archaea Gardener Tracker</title>
  <style>
    :root {{
      --bg: #0f1117;
      --surface: #181c27;
      --card: #1e2333;
      --border: #2d3348;
      --fg: #e8eaf0;
      --fg-muted: #7a83a0;
      --accent: #5b7fff;
      --accent-hover: #486df8;
      --danger: #ef4444;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--fg);
      font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }}
    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 36px 32px;
      width: 100%;
      max-width: 420px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.5);
      text-align: center;
    }}
    .icon {{
      width: 56px;
      height: 56px;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 18px;
      color: var(--accent);
    }}
    .icon svg {{ width: 26px; height: 26px; fill: none; stroke: currentColor; stroke-width: 2; }}
    h1 {{
      font-size: 20px;
      font-weight: 700;
      margin-bottom: 8px;
      letter-spacing: -0.3px;
    }}
    p.subtitle {{
      font-size: 13px;
      color: var(--fg-muted);
      margin-bottom: 24px;
    }}
    form {{
      display: flex;
      flex-direction: column;
      gap: 14px;
    }}
    .input-wrap {{
      position: relative;
      text-align: left;
    }}
    input[type="password"] {{
      width: 100%;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px 14px;
      font-size: 14px;
      color: var(--fg);
      outline: none;
      transition: border-color 0.15s, box-shadow 0.15s;
    }}
    input[type="password"]:focus {{
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(91, 127, 255, 0.2);
    }}
    .remember-row {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      color: var(--fg-muted);
      user-select: none;
      cursor: pointer;
    }}
    .remember-row input {{
      cursor: pointer;
      accent-color: var(--accent);
    }}
    button {{
      background: var(--accent);
      color: #fff;
      border: none;
      border-radius: 8px;
      padding: 12px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s, transform 0.05s;
    }}
    button:hover {{
      background: var(--accent-hover);
    }}
    button:active {{
      transform: scale(0.99);
    }}
    #error {{
      font-size: 12px;
      color: var(--danger);
      margin-top: 4px;
      min-height: 18px;
    }}
    .shake {{
      animation: shake 0.35s cubic-bezier(.36,.07,.19,.97) both;
    }}
    @keyframes shake {{
      10%, 90% {{ transform: translate3d(-1px, 0, 0); }}
      20%, 80% {{ transform: translate3d(2px, 0, 0); }}
      30%, 50%, 70% {{ transform: translate3d(-3px, 0, 0); }}
      40%, 60% {{ transform: translate3d(3px, 0, 0); }}
    }}
  </style>
</head>
<body>
  <div class="card" id="card">
    <div class="icon">
      <svg viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
    </div>
    <h1>Protected Project Tracker</h1>
    <p class="subtitle">Enter the password to view Archaea Gardener.</p>
    <form id="unlock-form" onsubmit="event.preventDefault(); tryUnlock();">
      <div class="input-wrap">
        <input type="password" id="pass" placeholder="Enter password" autofocus autocomplete="current-password" required />
      </div>
      <label class="remember-row">
        <input type="checkbox" id="remember" checked />
        <span>Remember password on this device</span>
      </label>
      <button type="submit" id="unlock-btn">Unlock Tracker</button>
      <div id="error"></div>
    </form>
  </div>

  <script id="encrypted-payload" type="application/json">
{payload_json}
  </script>

  <script>
    const STORAGE_KEY = "archaea_garden_auth";

    async function decryptPayload(password) {{
      const raw = document.getElementById("encrypted-payload").textContent.trim();
      const {{ salt: saltB64, iv: ivB64, cipher: cipherB64 }} = JSON.parse(raw);

      const enc = new TextEncoder();
      const salt = Uint8Array.from(atob(saltB64), c => c.charCodeAt(0));
      const iv = Uint8Array.from(atob(ivB64), c => c.charCodeAt(0));
      const ciphertext = Uint8Array.from(atob(cipherB64), c => c.charCodeAt(0));

      const keyMaterial = await window.crypto.subtle.importKey(
        "raw",
        enc.encode(password),
        {{ name: "PBKDF2" }},
        false,
        ["deriveKey"]
      );

      const key = await window.crypto.subtle.deriveKey(
        {{
          name: "PBKDF2",
          salt: salt,
          iterations: 100000,
          hash: "SHA-256"
        }},
        keyMaterial,
        {{ name: "AES-CBC", length: 256 }},
        false,
        ["decrypt"]
      );

      const decrypted = await window.crypto.subtle.decrypt(
        {{ name: "AES-CBC", iv: iv }},
        key,
        ciphertext
      );

      return new TextDecoder().decode(decrypted);
    }}

    async function tryUnlock(storedPass = null) {{
      const passInput = document.getElementById("pass");
      const password = storedPass || passInput.value;
      const errorEl = document.getElementById("error");
      const btn = document.getElementById("unlock-btn");
      const card = document.getElementById("card");
      const remember = document.getElementById("remember").checked;

      errorEl.textContent = "";
      btn.textContent = "Decrypting...";
      btn.disabled = true;

      try {{
        const html = await decryptPayload(password);
        if (remember || storedPass) {{
          try {{ localStorage.setItem(STORAGE_KEY, password); }} catch(e) {{}}
        }}
        document.open();
        document.write(html);
        document.close();
      }} catch (err) {{
        btn.textContent = "Unlock Tracker";
        btn.disabled = false;
        if (storedPass) {{
          try {{ localStorage.removeItem(STORAGE_KEY); }} catch(e) {{}}
        }} else {{
          errorEl.textContent = "Incorrect password. Please try again.";
          card.classList.remove("shake");
          void card.offsetWidth; // re-trigger animation
          card.classList.add("shake");
          passInput.focus();
          passInput.select();
        }}
      }}
    }}

    // Check if password was saved previously on this device
    window.addEventListener("DOMContentLoaded", () => {{
      try {{
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) tryUnlock(saved);
      }} catch(e) {{}}
    }});
  </script>
</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(lock_html)

    print(f" Successfully encrypted '{input_path}' -> '{output_path}'")

if __name__ == "__main__":
    src = "archaea_gardener_tracker.html"
    dst = "index.html"

    if len(sys.argv) > 1:
        pwd = sys.argv[1]
    else:
        pwd = getpass.getpass("Enter password to protect the tracker: ")
        confirm = getpass.getpass("Confirm password: ")
        if pwd != confirm:
            print("Error: Passwords did not match.")
            sys.exit(1)

    if not pwd:
        print("Error: Password cannot be empty.")
        sys.exit(1)

    encrypt_html(src, dst, pwd)
