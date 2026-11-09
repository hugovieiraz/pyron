import threading
import functools
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

ART = r"C:\Users\gabri\.gemini\antigravity\brain\e134b1db-cabe-4904-a703-b88fa9900654"
ROOT = r"d:\hd_central\Antigravity projetos\brain\Obisidian_G\04 - Machine Learning\Projetos\Pyron---Embrapii\apresentacao_mvp"

handler = functools.partial(SimpleHTTPRequestHandler, directory=ROOT)
httpd = HTTPServer(("127.0.0.1", 8139), handler)
thread = threading.Thread(target=httpd.serve_forever, daemon=True)
thread.start()

with sync_playwright() as p:
    try:
        browser = p.chromium.launch(channel="msedge", headless=True)
    except Exception:
        browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
    page.goto("http://127.0.0.1:8139/mira_personagem_3d.html", wait_until="networkidle")
    page.wait_for_timeout(350)

    # 1. Full Swiss Editorial + Mira-3D Stage (Hero Pose)
    page.screenshot(path=f"{ART}\\pyron_mira3d_swiss_hero.png")

    # 2. Crop just the right-hand 3D card for clean insertion or inspect
    card = page.locator(".mira-3d-card")
    card.screenshot(path=f"{ART}\\pyron_mira3d_card_only.png")

    # 3. Switch to Scan IR Mode and capture
    page.click("#btn-mode-scan")
    page.wait_for_timeout(450)
    page.screenshot(path=f"{ART}\\pyron_mira3d_swiss_scan.png")

    # 4. Switch to Dark Mode + Logo Emblem Mode and capture
    page.click("#btn-theme")
    page.click("#btn-mode-logo")
    page.wait_for_timeout(450)
    page.screenshot(path=f"{ART}\\pyron_mira3d_dark_logo.png")

    browser.close()

httpd.shutdown()
print("Captured WebGL 3D renders successfully!")
