import spacy
import sense2vec
from collections import OrderedDict

nlp = spacy.load('en_core_web_sm')
s2v = sense2vec.Sense2Vec().from_disk('./s2v_old/')

def sense2vec_get_words(word, s2v, n):
    output = []
    word = word.lower()
    word = word.replace(" ", "_")

    sense = s2v.get_best_sense(word)
    print("SENSE: ", sense)
    #Checking if sense is not None (TypeError: 'NoneType' object is not iterable)
    if sense is not None:
        most_similar = s2v.most_similar(sense, n)
    else:
        most_similar = ['option1', 'option2', 'option3', 'option4']
    print ("most_similar ",most_similar)

    for each_word in most_similar:
        append_word = each_word[0].split("|")[0].replace("_", " ").lower()
        if append_word.lower() != word:
            output.append(append_word.title())

    out = list(OrderedDict.fromkeys(output))
    return out

def get_distractors(word, n=20):
    distractors = sense2vec_get_words(word, s2v, n)
    return distractors

# print(get_distractors('Mumbai'))