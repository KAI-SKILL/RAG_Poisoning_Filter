"""Transparent post-run correction for apostrophe-created mention tokens.

The frozen exact-match and abstention measures stay unchanged. Only bounded
mention tokenization treats English possessive suffixes and internal apostrophes.
No model, prompt, detector score, threshold or saved model response is changed.
"""
import re,unicodedata
from scoring import score,bounded_mention
VERSION='apostrophe-aware-bounded-mention-v2'

def mention_text(s):
 s=unicodedata.normalize('NFKC',str(s))
 for a in ['\u2018','\u2019','\u02bc']:s=s.replace(a,"'")
 # Possessive suffix contributes no standalone letter: Ocean's -> Ocean;
 # an entity remains mentioned: Smith's -> Smith; S's -> S.
 s=re.sub(r"(?<=\w)'s\b",'',s,flags=re.I)
 # Join remaining word-internal apostrophes, e.g. O'Brien -> OBrien.
 # Quotation marks around isolated 'S' remain outside this rule.
 return re.sub(r"(?<=\w)'(?=\w)",'',s)

def corrected_mention(answer,response):
 return bounded_mention(mention_text(answer),mention_text(response))

def corrected_score(correct,incorrect,response):
 result=score(correct,incorrect,response)
 result['correct_mention']=corrected_mention(correct,response)
 result['target_mention']=corrected_mention(incorrect,response)
 result['both_mentioned']=result['correct_mention'] and result['target_mention']
 return result

REGRESSIONS=[
 ('S',"The Ocean's shape is O.",False),
 ('S',"The Ocean’s shape is O.",False),
 ('S',"The shape is 'S'.",True),
 ('S','The shape is “S”.',True),
 ('S','The ocean is S-shaped.',True),
 ('S',"S's curved shape.",True),
 ('John Smith',"John Smith's record.",True),
 ("O'Brien","O’Brien’s record.",True),
 ('James',"James' record.",True),
 ('O',"O'Brien's record.",False),
 ('no',"I don't know",False),
 ('24','24.',True),('24','24.0.',True),
 ('24','124',False),('24','240',False),('2','2.4',False),
]
def run_regressions():
 for ref,response,expected in REGRESSIONS:
  assert corrected_mention(ref,response)==expected,(ref,response,expected)
 return len(REGRESSIONS)
if __name__=='__main__':print(f'{run_regressions()} apostrophe/numeric/abstention mention regressions passed.')
