"""
run.py — Application entry point. Starts uvicorn server and prints URLs.

- main(): starts server, prints Local/Network/Public URLs
"""

import socket
import subprocess
import sys
import os
import threading


def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def check_dependencies():
    missing = []
    required = ["fastapi", "uvicorn", "pdfminer", "docx", "multipart"]
    for pkg in required:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt\n")
        sys.exit(1)


def start_tunnel(port):
    try:
        from pyngrok import ngrok
        url = ngrok.connect(port).public_url
        print(f"   Public:   {url}  (via ngrok)")
    except Exception:
        try:
            result = subprocess.run(
                ["lt", "--port", str(port)],
                capture_output=True, text=True, timeout=8
            )
            if result.stdout.strip():
                print(f"   Public:   {result.stdout.strip()}  (via localtunnel)")
        except Exception:
            print("   Public:   (install pyngrok or localtunnel for public URL)")


def main():
    check_dependencies()
    port = int(os.getenv("PORT", 8000))
    lan_ip = get_lan_ip()

    print("\n" + "=" * 50)
    print("  🎯 ATS Scorer")
    print("  Free resume ATS compatibility checker")
    print("=" * 50)
    print(f"\n🚀 Server starting...")
    print(f"   Local:    http://localhost:{port}")
    print(f"   Network:  http://{lan_ip}:{port}")

    threading.Thread(target=start_tunnel, args=(port,), daemon=True).start()

    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
