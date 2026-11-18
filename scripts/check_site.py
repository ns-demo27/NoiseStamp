"""Check all curated audio, hashes, durations, links, and public-site hygiene."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
from collections import Counter
import hashlib
import json
import re
import wave

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "data/samples.json").read_text(encoding="utf-8"))
assert len(data["listening"]) == 14
assert len(data["preview"]) == 0
assert Counter(p["language"] for p in data["listening"]) == {"en": 10, "zh": 4}
for model in data["models"]:
    for language in ("en", "zh"):
        assert sum(p["model"] == model and p["method"] == "NoiseStamp" and p["language"] == language for p in data["listening"]) == 1
for method in data["methods"]:
    assert sum(p["model"] == "IndexTTS2" and p["method"] == method and p["language"] == "en" for p in data["listening"]) == 1
paths = set()
for pair in data["listening"] + data["preview"]:
    assert pair["transcript"]
    expected = {"full"}
    for state in ("reference", "watermarked"):
        assert set(pair[state]) == expected
        for length, asset in pair[state].items():
            src = asset["src"]
            assert not src.startswith(("/", "http")) and ".." not in Path(src).parts
            path = ROOT / src
            assert path.is_file(), src
            assert hashlib.sha256(path.read_bytes()).hexdigest() == asset["sha256"], src
            with wave.open(str(path)) as audio:
                duration = audio.getnframes() / audio.getframerate()
                assert audio.getsampwidth() == 2 and audio.getnchannels() == 1
                assert audio.getframerate() == asset["sampleRate"]
                assert abs(duration - asset["duration"]) < 0.0001
            paths.add(src)
assert len(paths) == data["counts"]["audioFiles"] == 28
assert {p.relative_to(ROOT).as_posix() for p in (ROOT / "assets/audio").rglob("*.wav")} == paths

class PageCheck(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        for attribute in ("href", "src"):
            if attribute in attrs:
                self.links.append(attrs[attribute])

page = PageCheck()
html = (ROOT / "index.html").read_text(encoding="utf-8")
page.feed(html)
assert len(page.ids) == len(set(page.ids)), "Duplicate HTML ids"
for link in page.links:
    parsed = urlsplit(link)
    if parsed.scheme or parsed.netloc:
        continue
    assert not parsed.path.startswith("/"), link
    if parsed.path:
        assert (ROOT / unquote(parsed.path)).is_file(), link
    if parsed.fragment:
        assert parsed.fragment in page.ids, link
for filename in ("index.html", "styles.css", "app.js", "data/samples.json", "README.md"):
    text = (ROOT / filename).read_text(encoding="utf-8")
    assert not re.search(r"BackdoorLALM|anonsubmission2027|Haiyun|haiyun|D:\\\\|C:\\\\|google-analytics|googletagmanager|fonts.googleapis", text), filename
assert not re.search(r"[\u4e00-\u9fff]", html), "Interface copy must be English"
assert 'audio.preload = "none"' in (ROOT / "app.js").read_text(encoding="utf-8")
assert html.index('id="listen"') < html.index('id="compare"') < html.index('id="method"') < html.index('id="results"')
assert 'id="preview-' not in html and 'renderPreview' not in (ROOT / "app.js").read_text(encoding="utf-8")
assert 'class="hero-facts"' not in html
assert re.search(r'href="styles\.css\?v=', html) and re.search(r'src="app\.js\?v=', html)
assert (ROOT / "assets/method-overview.svg").is_file()
size = sum((ROOT / p).stat().st_size for p in paths)
print(f"PASS: 14 curated listening pairs, 28 byte-verified WAV files ({size / 1048576:.2f} MiB).")
print("PASS: durations, model/method coverage, native transcripts, local links, English interface, and public-file hygiene.")
