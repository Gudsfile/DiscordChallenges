import spacy
import numpy as np
import nltk
from nltk.corpus import stopwords

nlp = spacy.load("fr_core_news_sm")
nltk.download('stopwords')
stopWords = set(stopwords.words('french'))

def return_clean(doc):
    clean_words = list()
    for token in doc:
        if token.text not in stopWords:
            clean_words.append(token)
    return clean_words


def return_mean_embedding(sentence):
    doc = nlp(sentence)
    clean = return_clean(doc)
    return np.mean([(x.vector) for x in clean], axis=0)


def get_simili(new_sentence, sentences):
    new_sentence_mean_vect = return_mean_embedding(new_sentence)
    simili = list()
    for sentence in sentences:
        sentence_descr = sentence['description']
        sentence_mean_vect = return_mean_embedding(sentence_descr)
        delta = np.linalg.norm(new_sentence_mean_vect - sentence_mean_vect)
        if delta < 20:
            print(
                f'+++ {delta} `{sentence_descr}` et `{new_sentence}` sont très proches.')
            simili.append(sentence)
        else:
            print(f'--- {delta} `{sentence_descr}` et `{new_sentence}` sont éloignées.')
    return simili
