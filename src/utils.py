# Copyright 2020 The `Kumar Nityan Suman` (https://github.com/nityansuman/). All Rights Reserved.
#
#
#                     GNU GENERAL PUBLIC LICENSE
#                        Version 3, 29 June 2007
#  Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>
#  Everyone is permitted to copy and distribute verbatim copies
#  of this license document, but changing it is not allowed.
# ==============================================================================


# Import packages
from src.pipelines import pipeline
from nltk.corpus import wordnet as wn
from pywsd.lesk import cosine_lesk
from pywsd.lesk import simple_lesk
from pywsd.lesk import adapted_lesk
from pywsd.similarity import max_similarity
import random
import json
import requests
from flashtext import KeywordProcessor
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
import string
import pke
import re
import itertools
import pprint
from summarizer import Summarizer
import os
import csv
import numpy as np
import pandas as pd
import nltk
import sqlite3 as sql

# add your path for nltk data
nltk.data.path.append('/home/girish/softwares/nltk_data')


def generate_qa(text):
    # our function
    '''take in text, return questions and answers using google t5 model'''
    nlp = pipeline("question-generation")
    return nlp(text)


def backup(session):
    # Process username and subject information
    username = "_".join([x.upper() for x in session["username"].split()])
    subject_name = session["subject_name"].strip().upper()
    subject_id = session["subject_id"].strip()
    test_type = ["Objective" if session["test_id"] == "0" else "Subjective"][0]
    test_id = session["test_id"]
    # Process timestamp
    timestamp = session["date"]
    # Construct loggin data
    row = [
        timestamp,
        username,
        subject_name,
        subject_id,
        test_type,
        test_id,
        session["score"],
        session["result"]
    ]
    # Database user information log path
    filepath = session["database_path"]
    file_exists = os.path.isfile(filepath)
    if file_exists:
        # If file exists, open file in append mode
        try:
            with open(filepath, mode="a") as fp:
                fp_writer = csv.writer(fp)
                # Backup data
                fp_writer.writerow(row)
                status = True
        except Exception as e:
            print("Exception raised at `utils.__backup`:", e)
    else:
        print("Database placeholder nott found!")
        status = False
    return status


def relative_ranking(session):
    """Method to compute relative ranking of user on a particular subject.

    Arguments:
        subjectname {str} -- Name of the test subject.
        type {str} -- Denoting the type of the test taken

    Returns:
        int, float, int -- Maximum, Minimum and Average score obtained by the user in a paarticular subject test
    """
    max_score = 100.0
    min_score = 0.0
    mean_score = "None"
    try:
        df = pd.read_csv(session["database_path"])
    except Exception as e:
        print("Exception raised at `utils__relative_ranking`:", e)
    else:
        df = df[(df["SUBJECT_ID"] == int(session["subject_id"]))
                & (df["TEST_ID"] == int(session["test_id"]))]
        if df.shape[0] >= 1:
            max_score = np.round(df["SCORE"].max(), decimals=2)
            min_score = np.round(df["SCORE"].min(), decimals=2)
            mean_score = np.round(df["SCORE"].mean(), decimals=2)
    finally:
        return max_score, min_score, mean_score

    # MCQ GENERATION

    # Summarizer


def summarizer(filepath):
    '''input: filepath, output: summarized text'''
    #TODO: get minimum length, maximum length and ratio as method arguments
    f = open(filepath, "r")
    full_text = f.read()
    f.close()
    model = Summarizer()
    result = model(full_text, min_length=60, max_length=500, ratio=0.4)
    summarized_text = ''.join(result)
    return full_text, summarized_text


def get_nouns_multipartite(text):
    '''input: text, output: get selected nouns (max: 20)'''
    #TODO: get no. of nouns to return (n) as method argument
    out = []

    extractor = pke.unsupervised.MultipartiteRank()
    extractor.load_document(input=text)
    #    not contain punctuation marks or stopwords as candidates.
    pos = {'PROPN'}
    #pos = {'VERB', 'ADJ', 'NOUN'}
    stoplist = list(string.punctuation)
    stoplist += ['-lrb-', '-rrb-', '-lcb-', '-rcb-', '-lsb-', '-rsb-']
    stoplist += stopwords.words('english')
    extractor.candidate_selection(pos=pos, stoplist=stoplist)
    # 4. build the Multipartite graph and rank candidates using random walk,
    #    alpha controls the weight adjustment mechanism, see TopicRank for
    #    threshold/method parameters.
    extractor.candidate_weighting(alpha=1.1,
                                  threshold=0.75,
                                  method='average')
    keyphrases = extractor.get_n_best(n=20)

    for key in keyphrases:
        out.append(key[0])

    return out


def tokenize_sentences(text):
    '''input: text, output: list of sentences with more than 20 letters'''
    sentences = [sent_tokenize(text)]
    print(sentences)
    sentences = [y for x in sentences for y in x]
    print("adkhj: ", sentences)
    # Remove any short sentences less than 20 letters.
    sentences = [sentence.strip()
                 for sentence in sentences if len(sentence) > 20]
    print(sentences)
    return sentences


def get_sentences_for_keyword(keywords, sentences):
    '''input: keywords, list of all sentences. output: dictionary that maps keywords with their sentences'''
    keyword_processor = KeywordProcessor()
    keyword_sentences = {}
    for word in keywords:
        keyword_sentences[word] = []
        keyword_processor.add_keyword(word)
    for sentence in sentences:
        keywords_found = keyword_processor.extract_keywords(sentence)
        for key in keywords_found:
            keyword_sentences[key].append(sentence)

    for key in keyword_sentences.keys():
        values = keyword_sentences[key]
        values = sorted(values, key=len, reverse=True)
        keyword_sentences[key] = values
    return keyword_sentences

# Distractors from Wordnet


def get_distractors_wordnet(syn, word):
    distractors = []
    word = word.lower()
    orig_word = word
    if len(word.split()) > 0:
        word = word.replace(" ", "_")
    hypernym = syn.hypernyms()
    if len(hypernym) == 0:
        return distractors
    for item in hypernym[0].hyponyms():
        name = item.lemmas()[0].name()
        #print ("name ",name, " word",orig_word)
        if name == orig_word:
            continue
        name = name.replace("_", " ")
        name = " ".join(w.capitalize() for w in name.split())
        if name is not None and name not in distractors:
            distractors.append(name)
    return distractors


def get_wordsense(sent, word):
    word = word.lower()

    if len(word.split()) > 0:
        word = word.replace(" ", "_")

    synsets = wn.synsets(word, 'n')
    if synsets:
        wup = max_similarity(sent, word, 'wup', pos='n')
        adapted_lesk_output = adapted_lesk(sent, word, pos='n')
        lowest_index = min(synsets.index(
            wup), synsets.index(adapted_lesk_output))
        return synsets[lowest_index]
    else:
        return None

# Distractors from http://conceptnet.io/


def get_distractors_conceptnet(word):
    '''Get distractors from conceptnet api'''
    word = word.lower()
    original_word = word
    if (len(word.split()) > 0):
        word = word.replace(" ", "_")
    distractor_list = []
    url = "http://api.conceptnet.io/query?node=/c/en/%s/n&rel=/r/PartOf&start=/c/en/%s&limit=5" % (
        word, word)
    obj = requests.get(url).json()

    for edge in obj['edges']:
        link = edge['end']['term']

        url2 = "http://api.conceptnet.io/query?node=%s&rel=/r/PartOf&end=%s&limit=10" % (
            link, link)
        obj2 = requests.get(url2).json()
        for edge in obj2['edges']:
            word2 = edge['start']['label']
            if word2 not in distractor_list and original_word.lower() not in word2.lower():
                distractor_list.append(word2)

    return distractor_list


def FetchMCQfromDB(filename):
    con = sql.connect("database.db")
    con.row_factory = sql.Row

    cur = con.cursor()
    cur.execute("select * from mcqs where filename =" + "'" + filename + "'")

    rows = cur.fetchall()
    print(rows)
    data = []
    columns = [column[0] for column in cur.description]
    for row in rows:
        data.append(dict(zip(columns, row)))
    for index, row in enumerate(rows):
        choices = []
        choices.append(row['option1'])
        choices.append(row['option2'])
        choices.append(row['option3'])
        choices.append(row['option4'])
        data[index]["choices"] = choices
    return data


def FetchTests():
    con = sql.connect("database.db")
    con.row_factory = sql.Row

    cur = con.cursor()
    cur.execute("select distinct filename from mcqs")
    data = []
    rows = cur.fetchall()
    for row in rows:
        data.append(list(row))
    for i in range(len(data)):
        data[i] = data[i][0]
    return data


def fileToText(filepath):
    '''input: filepath, output: text in file'''
    #TODO : Handle all file formats
    # method to read file and output text
    try:
        with open(filepath, mode="r") as fp:
            text = fp.read()
        return text
    except FileNotFoundError as e:
        print("Exception raised in fileToText()", e)
