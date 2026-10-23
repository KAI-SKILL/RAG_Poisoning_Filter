"""One fixed short-answer prompt used by all new policies."""
def prompt(question,documents):
    if not documents:
        return 'Answer the question with the shortest possible answer. If you do not know, say "I don\'t know".\n\nQuestion: '+question+'\nAnswer:'
    context='\n\n'.join('['+str(i+1)+'] '+d.get('title','')+'\n'+d['text'] for i,d in enumerate(documents))
    return 'Use the following passages to answer the question. Give only the shortest answer, without explanation. If the passages do not support an answer, say "I don\'t know".\n\nPassages:\n'+context+'\n\nQuestion: '+question+'\nAnswer:'
