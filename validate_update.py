"""Regression checks for user-supplied identities, offer conflicts and catalogue removal."""
import hashlib,json,re,zipfile
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).parent
class Visible(HTMLParser):
 def __init__(self):super().__init__();self.hidden=0;self.parts=[];self.images=[]
 def handle_starttag(self,tag,attrs):
  if tag in ['script','style']:self.hidden+=1
  if tag=='img':self.images.append(dict(attrs)['src'])
 def handle_endtag(self,tag):
  if tag in ['script','style']:self.hidden-=1
 def handle_data(self,data):
  if not self.hidden:self.parts.append(data)
p=Visible();p.feed((ROOT/'dist/index.html').read_text());visible=' '.join(p.parts)
for term in ['18650','M35A','P30B','M65A','S45A','LG M50LT','Molicel M50A','Amprius SA112']:assert term not in visible,term
for img in p.images:assert (ROOT/'dist'/img).is_file(),img
photos=json.loads((ROOT/'photos.json').read_text())
assert len(photos)==13
for key,photo in photos.items():
 assert photo['file'].startswith('assets/cells/')
 assert photo['archive']=='21700 Battery Cell.zip'
 assert (ROOT/'dist'/photo['file']).exists()
 assert len(photo['original_sha256'])==64
 if photo.get('alternate'):assert (ROOT/'dist'/photo['alternate']).exists()
assert not list((ROOT/'dist/assets').glob('*.png'))
d=json.loads((ROOT/'calculated.json').read_text());m=d['models']
assert not {'m35a','p30b','m65a','lg','sup'}&set(m)
assert not {'F01','F12','L04'}&{r['id'] for r in d['rows']}
assert all(r['finished'][0]<=40 for r in d['rows'])
assert all(r['box']==[230,400,340] for r in d['rows'])
assert m['rs50']['photo_rating']['DCIR_mOhm']==6.5
assert m['rs50']['dc_test']==6.5
assert m['jp50p1']['name'].startswith('Ampace JP50P1')
assert 'nkon' not in m['jp50p1']['market']
q=json.loads((ROOT/'alibaba_quotes.json').read_text())
a=m['eve50pl']['market']['alibaba'];assert (a['price'],a['price_max'])==(2.7,3.28)
assert sorted(o['price'] for o in a['offers'])==[2.7,2.99,3.28]
a=m['bak50d2']['market']['alibaba'];assert a['price']==3.33
assert any(o['seller_id']=='vapcell' and o['availability']=='out_of_stock' for o in a['offers'])
assert any(o['seller_id']=='alibaba_b' and o['price']==3.33 for o in a['offers'])
assert all(o['seller_url']=='' for o in q['offers'] if o['seller_id'] in ['alibaba_a','alibaba_b'])
assert m['tp60xg']['market']['alibaba']['price']==5.2
assert m['s50s']['market']['alibaba']['price']==2.79
assert 'alibaba' not in m['s50s2'].get('market',{}) # 50S quote is not 50S2 quote.
assert m['jp50p1']['market']['alibaba']['price']==3.98
assert next(o for o in q['offers'] if o['model']=='Ampace JP50')['key'] is None
release=json.loads((ROOT/'dist/release.json').read_text());assert release['release']=='20261001-r13'
for name,entry in release['files'].items():assert hashlib.sha256((ROOT/'dist'/name).read_bytes()).hexdigest()==entry['sha256'],name
print('PASS: current rating, 13 archive photo identities, removal of disqualified configurations, seller/stock conflicts, quote version separation and release fingerprints.')
