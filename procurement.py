"""Offer ranges are commercial alternatives, never a common seller or stock pool."""
def summarize(offers):
 prices=[o['price'] for o in offers if o['price'] is not None]
 return dict(price=min(prices) if prices else None,price_max=max(prices) if prices else None,
             offers=offers,availability='quoted' if prices else offers[-1]['availability'],
             observed_at=max(o['observed_at'] for o in offers),note='Партия, продавец и наличие проверяются для каждого предложения отдельно.')
def attach_offers(models,quotes):
 for key,m in models.items():
  offers=[o for o in quotes['offers'] if o['key']==key]
  if offers:m.setdefault('market',{})['alibaba']=summarize(offers)
def price_range(summary,multiplier=1):
 if summary['price'] is None:return '—'
 fmt=lambda n:f'{n*multiplier:.2f}'.replace('.',',')
 return fmt(summary['price']) if summary['price']==summary['price_max'] else fmt(summary['price'])+'–'+fmt(summary['price_max'])

def best_offer(offers):
    usable=[o for o in offers if o.get('price') is not None and o.get('availability')!='out_of_stock']
    return min(usable,key=lambda o:o['price']) if usable else None
