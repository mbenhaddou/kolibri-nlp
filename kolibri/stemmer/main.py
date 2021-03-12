from kolibri.stemmer import WordStemer

dutch=WordStemer('dutch')

print([dutch.stem(t) for t in "Alle eendjes zwemmen in het water".split()])