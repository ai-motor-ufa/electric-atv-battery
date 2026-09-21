"""Write a reproducible release manifest for the published dist directory."""
import hashlib
import json
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
PDF = "AKB_96V_Comparative_Study_2026-09-21.pdf"
FILES = [
    "index.html", "report.js", "report.css", "mooch.js", "mooch_data.json",
    "mooch_21700_photo.csv", "mooch_21700_forum.csv", "mooch_21700_comparison.csv",
    "Mooch_21700_2026-09-21.xlsx", PDF,
    "assets/t50xg.png", "assets/p73d.jpg",
]


def fingerprint(relative):
    content = (DIST / relative).read_bytes()
    return {"bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}


calculated = json.loads((ROOT / "calculated.json").read_text())
mooch = json.loads((DIST / "mooch_data.json").read_text())
payload = {
    "release": "20260921-r8",
    "date": "2026-09-21",
    "models": len(calculated["models"]),
    "configurations": len(calculated["rows"]),
    "overview_21700": sum(r["candidate"] and r["format"] == "21700" for r in calculated["rows"]),
    "overview_pouch": sum(r["candidate"] and r["format"] == "Pouch" for r in calculated["rows"]),
    "photo_rows": len(mooch["photo"]),
    "comparison_rows": len(mooch["combined"]),
    "forum_threads": len(mooch["forum"]),
    "full_text_articles": sum(r.get("status") == "Текст статьи прочитан" for r in mooch["forum"]),
    "forum_archive_complete": False,
    "pdf_pages": len(PdfReader(DIST / PDF).pages),
    "files": {name: fingerprint(name) for name in FILES},
    "conclusion": {
        "top_21700": 5,
        "attention_21700": 3,
        "top_pouch": 5,
        "sealed_immersion_cooling": True,
        "farasis_dimensions_checked": True,
    },
}
(DIST / "release.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
print({k: payload[k] for k in ["release", "models", "configurations", "overview_21700", "overview_pouch", "forum_threads", "full_text_articles", "pdf_pages"]})
