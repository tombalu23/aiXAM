import src.utils as utils
import re
import random

def fetchMCQ(filepath):
    '''Get filepath as input, return list of mcqs'''
    full_text, summarized_text = utils.summarizer(filepath)
    keywords = utils.get_nouns_multipartite(full_text) 
    filtered_keys=[]
    for keyword in keywords:
        if keyword.lower() in summarized_text.lower():
            filtered_keys.append(keyword)       

    sentences = utils.tokenize_sentences(summarized_text)
    keyword_sentence_mapping = utils.get_sentences_for_keyword(filtered_keys, sentences)

    key_distractor_list = {}

    for keyword in keyword_sentence_mapping:
        wordsense = utils.get_wordsense(keyword_sentence_mapping[keyword][0],keyword)
        if wordsense:
            distractors = utils.get_distractors_wordnet(wordsense,keyword)
            if len(distractors) ==0:
                distractors = utils.get_distractors_conceptnet(keyword)
            if len(distractors) != 0:
                key_distractor_list[keyword] = distractors
        else:
            
            distractors = utils.get_distractors_conceptnet(keyword)
            if len(distractors) != 0:
                key_distractor_list[keyword] = distractors

    mcqs = []

    for each in key_distractor_list:
        mcq= {}
        sentence = keyword_sentence_mapping[each][0]
        pattern = re.compile(each, re.IGNORECASE)
        output = pattern.sub( " _______ ", sentence)
        mcq['question'] = output
        choices = [each.capitalize()] + key_distractor_list[each]
        if len(choices) >= 4:
            mcq['answer'] = each.capitalize()
            top4choices = choices[:4]
            mcq['choices'] = top4choices
            random.shuffle(top4choices)
            mcqs.append(mcq)
    return mcqs




    
