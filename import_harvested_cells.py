"""Import the reviewed high-power 21700 subset from the 2026-09-21 harvest.

The source file is kept as collected evidence.  This script deliberately uses
reviewed CDR/TL values instead of treating every current printed in a product
title as a continuous rating.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "research_input" / "cell_market_data_2026-09-21.json"
NKON_CANDIDATES = ROOT / "research_input" / "nkon_candidate_prices_2026-09-21.json"
OUTPUT = ROOT / "harvested_cells.json"

SELECTION = {
    "ampace-jp50p1": dict(key="jp50p1", variant="C20", continuous=40, conditional=60, thermal=80),
    "amprius-inr21700-50q": dict(key="amprius50q", variant="C21", continuous=40, conditional=100, thermal=75),
    "great-power-50q": dict(key="gp50q", variant="C22", continuous=40, conditional=100, thermal=76),
    "linkdata-60p": dict(key="link60p", variant="C23", continuous=30, conditional=60, thermal=80),
    "linkdata-65p": dict(key="link65p", variant="C24", continuous=25, conditional=52, thermal=70,
                         fallback_dims=[21.7, 21.7, 71.0]),
    "reliance-rs60": dict(key="rs60", variant="C25", continuous=30, conditional=50, thermal=80),
    "tenpower-60xg": dict(key="tp60xg", variant="C26", continuous=35, conditional=60, thermal=75),
}
EXISTING_MARKET_MATCHES = {
    "lg": "lg-m50lt",
    "p50b": "molicel-p50b",
    "bak50d2": "bak-n21700-50d2",
    "rs50": "reliance-rs50",
    "eve50pl": "eve-inr21700-50pl",
    "t50xg": "tenpower-50xg",
}


def source_note(cell):
    parts = ["CellSaviors: " + cell["sources"]["cellsaviors"]]
    datasheet = cell.get("datasheet") or {}
    if datasheet.get("url"):
        parts.append("Datasheet: " + datasheet["url"] + " (" + datasheet.get("provenance", "не классифицирован") + ")")
    nkon = cell.get("nkon") or {}
    if nkon.get("url"):
        price = "нет подтверждённой цены" if nkon.get("price") is None else f"{nkon['price']:.2f} {nkon.get('currency', 'EUR')}"
        parts.append("NKON: " + price + "; " + str(nkon.get("availability") or "статус не указан") + "; " + nkon["url"])
    return " ".join(parts)


def model_note(cell, spec, dcir):
    test = cell.get("test") or {}
    status = "статья ECF сохранена и разобрана" if test.get("status") == "manual_html_extracted" else "доступна только ссылка"
    pre = " Предсерийные образцы; перенос на закупаемую партию требует проверки." if "pre-production" in test.get("verdict_flags", []) else ""
    return (
        f"Mooch: оценка CDR {spec['continuous']} А; {spec['conditional']} А только с температурным контролем "
        f"до {spec['thermal']} °C. DCIR теста {dcir:.2f} мОм; {status}.{pre}"
    )


def build():
    raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    nkon_snapshot = json.loads(NKON_CANDIDATES.read_text(encoding="utf-8"))
    candidate_offers = nkon_snapshot["offers"]
    cells = {cell["id"]: cell for cell in raw["cells"]}
    models, variants, sources = {}, [], []
    for cell_id, spec in SELECTION.items():
        cell = cells[cell_id]
        test = cell.get("test") or {}
        samples = test.get("dcir_mohm_samples") or []
        assert samples, f"No reviewed DCIR samples for {cell_id}"
        assert cell.get("weight_g"), cell_id
        dims = ([cell["diameter_mm"], cell["diameter_mm"], cell["length_mm"]]
                if cell.get("diameter_mm") and cell.get("length_mm") else spec.get("fallback_dims"))
        assert dims, f"No dimensions or reviewed conservative envelope for {cell_id}"
        dcir = sum(samples) / len(samples)
        source_id = "H" + spec["variant"]
        models[spec["key"]] = {
            "name": ("Ampace JP50 (NKON) / JP50P1 (тест)"
                     if spec["key"] == "jp50p1" else f"{cell['manufacturer']} {cell['model']}"),
            "type": "21700 Li-ion",
            "ah": cell["capacity_mAh"] / 1000,
            "v": cell["nominal_V"],
            "vmax": cell["max_V"],
            "wh": cell["capacity_mAh"] / 1000 * cell["nominal_V"],
            "kg": cell["weight_g"] / 1000,
            "dims": dims,
            "dims_label": ("Консервативный габаритный конверт формата 21700; точный чертёж не получен"
                           if spec.get("fallback_dims") else "Размер из CellSaviors"),
            "continuous": spec["continuous"],
            "conditional_current": spec["conditional"],
            "thermal_cut": spec["thermal"],
            "dc_test": round(dcir, 3),
            "source": source_id,
            "res": f"DCIR Mooch: {', '.join(str(x).replace('.', ',') for x in samples)} мОм; среднее {dcir:.2f} мОм",
            "note": model_note(cell, spec, dcir),
            "market": {
                "cell_saviors_url": cell["sources"]["cellsaviors"],
                "ecf_url": test.get("url"),
                "datasheet": cell.get("datasheet"),
                "nkon": cell.get("nkon"),
                "harvested_at": raw["generated_at"],
            },
        }
        if spec["key"] in candidate_offers:
            models[spec["key"]]["market"]["nkon"] = candidate_offers[spec["key"]]
        variants.append({"id": spec["variant"], "model": spec["key"]})
        sources.append({
            "id": source_id,
            "title": test.get("title") or f"Battery Mooch: {models[spec['key']]['name']}",
            "url": test.get("url") or cell["sources"]["ecf"],
            "note": source_note(cell),
        })
    existing_market = {}
    for model_key, cell_id in EXISTING_MARKET_MATCHES.items():
        cell = cells.get(cell_id)
        if not cell:
            continue
        existing_market[model_key] = {
            "cell_saviors_url": cell["sources"]["cellsaviors"],
            "ecf_url": (cell.get("test") or {}).get("url"),
            "datasheet": cell.get("datasheet"),
            "nkon": cell.get("nkon"),
            "harvested_at": raw["generated_at"],
        }
    # The candidate price snapshot also covers models sourced from data.json and
    # new_cells.json, which are not necessarily present in the harvested cell list.
    for model_key, offer in candidate_offers.items():
        if model_key in models:
            continue
        market = existing_market.setdefault(model_key, {
            "harvested_at": nkon_snapshot["observed_at"],
        })
        market["nkon"] = offer
    payload = {
        "source": str(SOURCE.relative_to(ROOT)),
        "nkon_source": str(NKON_CANDIDATES.relative_to(ROOT)),
        "generated_at": raw["generated_at"],
        "selection_rule": "26S16P; capacity >= 4.8 Ah; known mass and 21700 envelope; reviewed CDR >= 25 A; DCIR from extracted ECF article",
        "models": models,
        "variants": variants,
        "sources": sources,
        "existing_market": existing_market,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print({"models": len(models), "variants": len(variants), "output": str(OUTPUT)})


if __name__ == "__main__":
    build()
