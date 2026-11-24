"""Bygger public/index.html av tools/head.css.html + tools/body.html.

head.css.html och body.html är samma källa som används för förhandsvisningen på claude.ai.
Här läggs ett fullständigt HTML-dokument runt (teckenkodning, viewport, manifest och
service worker för offline).  Kör:  python3 tools/make_index.py
"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
head = open(os.path.join(HERE, "head.css.html"), encoding="utf8").read()
body = open(os.path.join(HERE, "body.html"), encoding="utf8").read()
src = head + body

title = re.search(r"<title>(.*?)</title>", src).group(1)
src = re.sub(r"<title>.*?</title>\n?", "", src, count=1)
src = re.sub(r'<meta name="claude:viewport-fit-sides"[^>]*>\n?', "", src, count=1)

doc = f"""<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0d2a33">
<meta name="description" content="Guidad hop on hop off-tur med vanlig kollektivtrafik i Göteborg och Stockholm.">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icons/icon-192.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>{title}</title>
<style>
:root{{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}
body{{margin:0;font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}}
img{{max-width:100%}}
[hidden]{{display:none!important}}
</style>
</head>
<body>
{src}
<script>
if ("serviceWorker" in navigator) {{
  window.addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {{}}));
}}
</script>
</body>
</html>
"""
open(os.path.join(ROOT, "public", "index.html"), "w", encoding="utf8").write(doc)
print("public/index.html", len(doc), "bytes")
