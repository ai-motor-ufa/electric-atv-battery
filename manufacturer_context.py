"""Source-based manufacturer context shared by the site and PDF; no score changes."""
import json
from pathlib import Path

def load():return json.loads((Path(__file__).parent/'manufacturer_profiles.json').read_text())

def html_context(key,esc):
 audit=load();p=audit['profiles'][key];by={s['id']:s for s in p['sources']}
 def links(ids):return ' '.join(f'<a href="{esc(by[id]["url"])}" target="_blank" rel="noopener">{esc(by[id]["title"])} ↗</a>' for id in ids)
 detailed=''.join(f'<p>{esc(item["text"])}<span class="sub">{links(item["sources"])}</span></p>' for item in p['partners'])
 detailed+='<h4>Публичные случаи и их применимость</h4>'
 detailed+=''.join(f'<p><strong>{esc(item["kind"])}.</strong> {esc(item["text"])}<span class="sub">{links(item["sources"])}</span></p>' for item in p['incidents'])
 return f'<div class="maker-context"><p><strong>Производитель:</strong> {esc(p["company"])} · {esc(p["location"])}. {esc(p["summary"])}</p><p><strong>Партнёры и применение:</strong> {esc(p["partners_summary"])}</p><p><strong>Публичные случаи:</strong> {esc(p["incident_summary"])}</p><details><summary>Подробности и первичные источники</summary>{detailed}<p class="note">Проверено {esc(audit["checked_at"])}. {esc(audit["scope"])}</p><p class="note">{esc(audit["interpretation"])}</p><p class="source-list">'+links([s['id'] for s in p['sources']])+ '</p></details></div>'
