#Code to try out sense2vec distractor generation.


import spacy
# from sense2vec import Sense2VecComponent
# from sense2vec import Sense2Vec
import sense2vec
from collections import OrderedDict

nlp = spacy.load('en_core_web_sm')
s2v = sense2vec.Sense2Vec().from_disk('../sense2vec_old/s2v_old')
# s2v = Sense2VecComponent('/path/to/reddit_vectors-1.1.0')


def sense2vec_get_words(word, s2v):
    output = []
    word = word.lower()
    word = word.replace(" ", "_")

    sense = s2v.get_best_sense(word)
    most_similar = s2v.most_similar(sense, n=20)

    # print ("most_similar ",most_similar)

    for each_word in most_similar:
        append_word = each_word[0].split("|")[0].replace("_", " ").lower()
        if append_word.lower() != word:
            output.append(append_word.title())

    out = list(OrderedDict.fromkeys(output))
    return out


word = "Natural Language processing"
distractors = sense2vec_get_words(word, s2v)

print("Distractors for ", word, " : ")
print(distractors)
