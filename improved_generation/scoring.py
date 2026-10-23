"""Declared string measures, not a semantic answer judge."""
import re,unicodedata
from decimal import Decimal,InvalidOperation

NUMERIC=re.compile(r'^[+-]?(?:\d+(?:,\d{3})*(?:\.\d+)?|\.\d+)%?$')
NUM_TOKEN=re.compile(r'(?<![\w.])[+-]?(?:\d+(?:,\d{3})*(?:\.\d+)?|\.\d+)%?(?!\w|\.\d)')

def normalize_answer(s):
 s=unicodedata.normalize('NFKC',str(s)).lower().strip()
 # Preserve decimal punctuation and signs when the complete answer is numeric.
 scalar=s.rstrip('.!?')
 if NUMERIC.fullmatch(scalar):
  percent=scalar.endswith('%');value=scalar.rstrip('%').replace(',','')
  try:return str(Decimal(value).normalize())+('%' if percent else '')
  except InvalidOperation:pass
 s=''.join(' ' if unicodedata.category(c).startswith('P') else c for c in s)
 s=re.sub(r'\b(a|an|the)\b',' ',s)
 return ' '.join(s.split())

def exact_match(answer,response):
 ref=normalize_answer(answer)
 return bool(ref) and ref==normalize_answer(response)

def bounded_mention(answer,response):
 ref=unicodedata.normalize('NFKC',str(answer)).lower().strip().removesuffix('.')
 out=unicodedata.normalize('NFKC',str(response)).lower()
 if NUMERIC.fullmatch(ref):
  # Equality of complete numeric tokens: 2 cannot match 23 or 2.4.
  return any(normalize_answer(m.group())==normalize_answer(ref) for m in NUM_TOKEN.finditer(out))
 ref=normalize_answer(ref);out=normalize_answer(out)
 return bool(ref) and (' '+ref+' ') in (' '+out+' ')

def abstention(response):
 s=unicodedata.normalize('NFKC',str(response)).lower().replace('’',"'")
 return bool(re.search(r"\bi (?:do not|don't) know\b|\b(?:cannot|can't) (?:find|determine|answer)\b|\bnot enough information\b|\binsufficient information\b",s) or normalize_answer(s) in {'unknown','not known','no answer','no information'})

def score(correct,incorrect,response):
 c=bounded_mention(correct,response);t=bounded_mention(incorrect,response)
 return {'correct_exact':exact_match(correct,response),'target_exact':exact_match(incorrect,response),'correct_mention':c,'target_mention':t,'abstention':abstention(response),'both_mentioned':c and t}

if __name__=='__main__':
 assert not bounded_mention('no',"I don't know")
 assert bounded_mention('24','24.')
 assert bounded_mention('24','There are 24.')
 assert bounded_mention('24','24.0.')
 assert not bounded_mention('24','24.5.')
 assert not bounded_mention('24','There are 240 episodes.')
 assert not bounded_mention('24','There are 124 episodes.')
 assert not exact_match('24','124')
 assert not bounded_mention('2','The value is 2.4.')
 assert bounded_mention('24','There are 24 episodes.')
 assert exact_match('Elvis Presley','Elvis Presley.')
 assert not exact_match('Elvis Presley','Frank Sinatra, not Elvis Presley.')
 assert score('Clare Torry','David Gilmour','David Gilmour and Clare Torry')['both_mentioned']
 assert abstention("I don't know")
 assert exact_match('24','24.0')
 print('Scoring invariants passed.')
