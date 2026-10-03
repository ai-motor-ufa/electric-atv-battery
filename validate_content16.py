"""Check supplied image identity, visible caveats and factual-source coverage."""
import json,hashlib,re,html as html_tools
from pathlib import Path
from pypdf import PdfReader
photos=json.loads(Path('photos.json').read_text());profiles=json.loads(Path('manufacturer_profiles.json').read_text())
keys=['s50s','p45b','p42a','h52a','lrle','t50sg','h51','p50b','rs60']
for key in keys:
 p=photos[key];uploaded=Path('/workspace/scratch/3919adda5846/upload')/p['source_filename'];published=Path('dist')/p['file']
 if uploaded.exists():assert published.read_bytes()==uploaded.read_bytes()
 assert hashlib.sha256(published.read_bytes()).hexdigest()==p['original_sha256']
 assert p['added_at']=='2026-10-03'
assert photos['h51']['related_model'] and photos['h51']['display_name']=='LG H51T'
assert 'идентичность' in photos['h51']['caption']
assert set(profiles['profiles'])=={'gp50q','eve50pl','bak50d2','rs50','t50xg'}
assert json.loads(Path('dist/manufacturer_profiles.json').read_text())==profiles
for key,p in profiles['profiles'].items():
 ids={s['id'] for s in p['sources']}
 for item in p['partners']+p['incidents']:assert set(item['sources'])<=ids
 assert all(s['url'].startswith('https://') for s in p['sources'])
 assert p['company'] and p['partners'] and p['incidents']
html=Path('dist/index.html').read_text();cards=re.findall(r'<article class="final-cell">([\s\S]*?)</article>',html)
assert len(cards)==5
for card in cards:
 assert 'class="maker-context"' in card and re.search(r'<figure class="final-photo">[\s\S]*?<img ',card)
 assert 'Производитель:' in card and 'Публичные случаи:' in card
 assert re.search(r'<details>[\s\S]*?<a href="https://',card)
for phrase in ['26120','не 21700 50Q','не рассматриваемые аккумуляторы 21700 50Q','патентный','14,4 В','Power X-Change']:assert phrase in html_tools.unescape(re.sub(r'<script[\s\S]*?</script>','',html)),phrase
pdf=PdfReader('dist/AKB_96V_Comparative_Study_2026-10-03.pdf');text=' '.join(' '.join(page.extract_text().split()) for page in pdf.pages)
for p in profiles['profiles'].values():assert p['company'] in text
for phrase in ['LG H51T','Идентичность H51 и H51T','337-TA-1518','21700 50Q']:assert phrase in text,phrase
release=json.loads(Path('dist/release.json').read_text())
assert release['release']=='20261003-r16' and release['product_photo_files']==24 and release['product_photo_models']==23
assert release['default_motors']==2 and release['default_blocks']==2
for path,meta in release['files'].items():
 b=(Path('dist')/path).read_bytes();assert len(b)==meta['bytes'] and hashlib.sha256(b).hexdigest()==meta['sha256']
print('PASS: nine exact attachments, H51T caveat, five source-based manufacturer cards, unchanged two-block defaults, PDF contents and manifest hashes.')
