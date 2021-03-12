import numpy as np

language='en'
word_embeddings = {}
# f = open('/Users/mbenhaddou/Documents/Mentis/Developement/Python/Kolibri/kolibri/features/word2vec/model/en-glove.6B.100d.txt', encoding='utf-8')
#
# for line in f:
#     values = line.split()
#     word = values[0]
#     coefs = np.asarray(values[1:], dtype='float32')
#     word_embeddings[word] = coefs
# f.close()

def get_embedding(sentennce):

    if len(sentennce) != 0:
        v = sum([word_embeddings.get(w, np.zeros((100,))) for w in sentennce.split()])/(len(sentennce.split())+0.001)
    else:
        v = np.zeros((100,))
    return v