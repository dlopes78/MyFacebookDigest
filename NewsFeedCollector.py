# -*- coding: utf-8 -*-

import os
import sys
import urllib2
import json
import webbrowser
import nltk
from cgi import escape
import re

import facebook

from VectorSpace import VectorSpace
from pprint import pprint

from gensim import corpora, models, similarities
import time
import pickle


# Loop through the pages of connection data and build up messages
# write on text file to be used in classification
#also test performance of LSA from gensim


messages = []

#DLP 501326469
#Zoe 681720165
for user_id in ["501326469"]: 
  if user_id=="501326469": token = "yourtoken"
  elif user_id=="681720165": token= "yourtoken"
  graph = facebook.GraphAPI(token) 
  friends = graph.get_connections(user_id, "friends")
  friend_NameId = [[friend['name'],friend['id']] for friend in friends['data']]
  count=0
  for id in friend_NameId:
    count +=1
    if count%10==0: time.sleep(100)
    BASE_URL = 'https://graph.facebook.com/%s/feed?access_token='%id[1]
    url = BASE_URL + ACCESS_TOKEN
    print id[1]
    current_page = 0
    while current_page < NUM_PAGES:
      print url
      data = json.loads(urllib2.urlopen(url).read())
      messages += [d['story'] for d in data['data'] if d.get('story')]
      messages += [d['message'] for d in data['data'] if d.get('message')]
      messages += [d['text'] for d in data['data'] if d.get('text')]
      messages += [d['description'] for d in data['data'] if d.get('description')]
      messages += [d['caption'] for d in data['data'] if d.get('caption')]
      for d in data['data']:
        if d.get('comments') and d['comments'].get('data'):
          if d['comments']['count']<4:
            messages += [comm['message'] for comm in d['comments']['data']]
          elif d['comments']['count']>=4:
	    if "id" in d:
	      comm_id =  d["id"]
	      print comm_id
	      if comm_id != '721885598_121718987938201' and comm_id!='1549970621_10150869057568623' and comm_id!='206642_335521153190994' and comm_id!="206642_10150906770864185":
  	        commdata= graph.get_connections(comm_id,"")   
	        if "comments" in commdata and "data" in commdata["comments"]:
	          messages += [comm['message'] for comm in commdata["comments"]["data"]]         
      if "paging" in data: 
        url = data['paging']['next']
        current_page += 1
      else: current_page=15
      print len(messages)

print len(messages)


stop_words = nltk.corpus.stopwords.words('english')
stop_words += nltk.corpus.stopwords.words('italian')
stop_words += ['&', '.', '?', '!']

print stop_words;

texts = [[word for word in message.lower().split() if word not in stop_words]
          for message in messages]

all_tokens = sum(texts, [])
tokens_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
texts = [[word for word in text if word not in tokens_once]
          for text in texts]

#print texts

dictionary = corpora.Dictionary(texts)
dictionary.save('data_feb11.dict') # store the dictionary, for future reference
#print dictionary

corpus = [dictionary.doc2bow(text) for text in texts]
corpora.MmCorpus.serialize('data_feb11.mm', corpus) 
#print corpus

tfidf = models.TfidfModel(corpus)
corpus_tfidf = tfidf[corpus]
lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=200) # initialize an LSI transformation
corpus_lsi = lsi[corpus_tfidf]

#prepare for queries
index = similarities.MatrixSimilarity(lsi[corpus])

doc = "photo"
vec_bow = dictionary.doc2bow(doc.lower().split())
vec_lsi = lsi[vec_bow] # convert the query to LSI space

sims = index[vec_lsi] 

sims = sorted(enumerate(sims), key=lambda item: -item[1])
print sims[:10]

doc_number = [elem[0] for elem in sims[:10]]

for n in doc_number: print messages[n]

thefile = open('testMessage_feb11.txt', 'w')
pickle.dump(messages, thefile)
thefile.close()

