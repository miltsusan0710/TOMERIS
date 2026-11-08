import sys
sys.path.insert(0,'outputs')
from tomeris_search_methods import wikipedia_search,wikipedia_page
for name in ('KUN','桝太一'):
 print('QUERY',name,flush=True)
 rows=wikipedia_search(name)
 for row in rows: print(row['title'],row['wiki_id'])
 for row in rows:
  if row['title'].replace(' ','').casefold().startswith(name.casefold()):
   page=wikipedia_page(row);print(page['title'],repr(page['text'][:1600]),flush=True)
