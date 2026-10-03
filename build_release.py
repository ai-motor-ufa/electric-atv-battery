"""Write a reproducible release manifest for the published dist directory."""
import hashlib
import json
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
PDF = "AKB_96V_Comparative_Study_2026-10-04.pdf"
FILES = [
    "index.html", "report.js", "report.css", "mooch.js", "mooch_data.json",
    "mooch_21700_photo.csv", "mooch_21700_forum.csv", "mooch_21700_comparison.csv",
    PDF,
    "assets/mooch-21700-2026-09-27.jpg", "discharge_tests.json", "discharge_energy_temperature.csv", "alibaba_quotes.json", "alibaba_quotes_2026-10-01.csv",
]


FILES.append("calculation_audit.json")
FILES.append("selection_ratings.json")
FILES.append("manufacturer_profiles.json")
FILES.extend(str(p.relative_to(DIST)) for p in sorted((DIST/"traces").glob("*.json")))
FILES.extend(str(p.relative_to(DIST)) for p in sorted((DIST/'assets/cells').glob('*.jpg')))
FILES.extend(str(p.relative_to(DIST)) for p in sorted((DIST/"tests").glob("*.jpg")))

def fingerprint(relative):
    content = (DIST / relative).read_bytes()
    return {"bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}


calculated = json.loads((ROOT / "calculated.json").read_text())
mooch = json.loads((DIST / "mooch_data.json").read_text())
payload = {
    "release": "20261004-r17",
    "date": "2026-10-04",
    "numeric_model_revision": "20261002-r14a",
    "default_motors": 2,
    "default_blocks": 2,
    "range_default_basis": "nominal",
    "selection_ratings": "selection_ratings.json",
    "models": len(calculated["models"]),
    "configurations": len(calculated["rows"]),
    "overview_21700": sum(r["candidate"] and r["format"] == "21700" for r in calculated["rows"]),
    "overview_pouch": sum(r["candidate"] and r["format"] == "Пакетный" for r in calculated["rows"]),
    "photo_rows": len(mooch["photo"]),
    "comparison_rows": len(mooch["combined"]),
    "forum_threads": len(mooch["forum"]),
    "full_text_articles": sum(r.get("status") == "Текст статьи прочитан" for r in mooch["forum"]),
    "forum_archive_complete": False,
    "pdf_pages": len(PdfReader(DIST / PDF).pages),
    "files": {name: fingerprint(name) for name in FILES},
    "discharge_charts": 23,
    "calculation_audit": "calculation_audit.json",
    "wmtc_index_kwh_km": calculated["assumptions"]["wmtc_index_kwh_km"],
    "initial_cell_temperature_C": 25,
    "product_photo_files": len(list((DIST/"assets/cells").glob("*.jpg"))), "product_photo_models": len(json.loads((ROOT/"photos.json").read_text())),
    "related_model_photos": 1,
    "manufacturer_profiles": 5,
    "manufacturer_context_checked_at": "2026-10-03",
    "commercial_offers": 24, "photo_rating_date": "2026-09-27",
    "disqualified_configurations_removed": 9,
    "thermal_model_status": "scenario_only_not_validated_sealed_pack",
    "conclusion": {
        "top_21700": 5,
        "attention_21700": 3,
        "top_pouch": 0,
        "sealed_immersion_cooling": True,
        "farasis_dimensions_checked": True,
    },
}
(DIST / "release.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
print({k: payload[k] for k in ["release", "models", "configurations", "overview_21700", "overview_pouch", "forum_threads", "full_text_articles", "pdf_pages"]})
