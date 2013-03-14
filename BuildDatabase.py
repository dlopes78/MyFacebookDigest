import facebook
import urllib
import urlparse
import subprocess
import warnings
import re
import MySQLdb

import sys

import urllib2
import json
import webbrowser

import pickle
from nltk.probability import DictionaryProbDist
from training import Classifier

# Hide deprecation warnings. The facebook module isn't that up-to-date (facebook.GraphAPIError).
warnings.filterwarnings('ignore', category=DeprecationWarning)

token = "your token"
graph = facebook.GraphAPI(token)

verbose_printout=0

db = MySQLdb.connect("","root","yourpwd")
cursor = db.cursor()
cursor.execute("CREATE DATABASE facebook_extended;")

infile = open('classifier_feb12.txt', 'r')
classifier = pickle.load(infile)
infile.close()

def encode_str(string):
  if string != 0:
    return string.encode(sys.getdefaultencoding(), 'ignore')
  else: return string 

def get_feeds(userid):
  """
  provides as ouput a list of dictionaries that include feed, time, # of comments,
  and list of comments (as another list of dict) when #>0
  """
  listFeeds=[]
  BASE_URL = 'https://graph.facebook.com/%s/feed?access_token='%userid
  url = BASE_URL + token
  max_pages=5
  current_page=0
  while current_page <= max_pages: 
    feeds = json.loads(urllib2.urlopen(url).read())
    print "doing page: ",current_page 
    for elem in feeds["data"]:
      print elem["id"]
      if "story" in elem: 
        match = re.search(r"on his own status",elem["story"])
        if not match: 
          if verbose_printout: print elem["story"], " time: ", elem["updated_time"], " comments: ", elem["comments"]["count"]
          if "likes" in elem: 
	    if verbose_printout:  print " likes: ", elem["likes"]["count"]
          dict={}
	  dict["Fbid"]= elem["id"]
	  dict["feed"]= elem["story"]
	  dict["time"]= elem["updated_time"]
	  dict["NofComments"]= elem["comments"]["count"]
	  if "likes" in elem: dict["NofLikes"]= elem["likes"]["count"]
#not strictly necessary, can just do >0 and forget the part with >=4 
          if elem["comments"]["count"]>0 and elem["comments"]["count"]<4:
	    count =1
            dict["comments"]=[]
	    for comment in elem["comments"]["data"]:        
              if verbose_printout: print count, " ", comment["message"], " time: ", comment["created_time"], " from: ", comment["from"]["name"]  
	      count +=1
	      dict_comments={}
	      dict_comments["text"]=comment["message"]
	      dict_comments["time"]=comment["created_time"]
	      dict_comments["from"]=comment["from"]["name"]  
	      dict_comments["from_userid"]=comment["from"]["id"]  
	      dict["comments"].append(dict_comments)
          if elem["comments"]["count"]>=4:
            dict["comments"]=[]
	    count =1
            elem_id =  elem["id"]
	    elemdata= graph.get_connections(elem_id,"") 
	    if "comments" in elemdata and "data" in elemdata["comments"]:
  	      for comment in elemdata["comments"]["data"]:        
                if verbose_printout: print count, " ", comment["message"], " time: ", comment["created_time"], " from: ", comment["from"]["name"]  
	        count +=1
	        dict_comments={}
	        dict_comments["text"]=comment["message"]
	        dict_comments["time"]=comment["created_time"]
	        dict_comments["from"]=comment["from"]["name"]  
	        dict_comments["from_userid"]=comment["from"]["id"]  
	        dict["comments"].append(dict_comments)
          listFeeds.append(dict)
#if we want add friends name
        match2 = re.search(r"is now friends with",elem["story"])
        if match2: 
          elem_id =  elem["id"]
	  elemdata= graph.get_connections(elem_id,"") 
          for key in elemdata["story_tags"].keys(): 
	    if not key=="0": 
	      if verbose_printout:
	        for contact in elemdata["story_tags"][key]: print contact["name"] 
    if "paging" in feeds: 
      url = feeds['paging']['next']
      current_page += 1
    else: current_page=6

  return listFeeds  
  	    
def get_status(userid):
  """
  provides as ouput a list of dictionaries that include status update, time, # of comments,
  and list of comments (as another list of dict) when #>0
  """
#  status = graph.get_connections(userid, "statuses")
  listStatus=[]
  BASE_URL = 'https://graph.facebook.com/%s/statuses?access_token='%userid
  url = BASE_URL + token
  max_pages=5
  current_page=0
  while current_page <= max_pages: 
    try:
      status = json.loads(urllib2.urlopen(url).read())
      print "doing page: ",current_page 
      for elem in status["data"]:
        if verbose_printout: 
          print "status update:"
          if "message" in elem: print  elem["message"],elem["updated_time"]
        dict={}
        dict["Fbid"]= elem["id"]
        if "message" in elem: 
          dict["status_update"]= elem["message"]
        else: dict["status_update"]=0
        dict["time"]= elem["updated_time"]
        if "likes" in elem: dict["NofLikes"]= len(elem["likes"]["data"]) 
        else: dict["NofLikes"]=0
        if "comments" in elem:
          dict["NofComments"]= len(elem["comments"]["data"])
          count = 1
          dict["comments"]=[]
          for comment in elem["comments"]["data"]: 
            if verbose_printout: print "comment: ", count, " ", comment["message"], " from: ", comment["from"]["name"] 
   	    count +=1    
	    dict_comments={}
	    dict_comments["text"]=comment["message"]
  	    dict_comments["time"]=comment["created_time"]
	    dict_comments["from"]=comment["from"]["name"]  
	    dict_comments["from_userid"]=comment["from"]["id"]  
	    dict["comments"].append(dict_comments)
        else: dict["NofComments"]= 0
        listStatus.append(dict)
      if "paging" in status: 
        url = status['paging']['next']
        current_page += 1
      else: current_page=6
    except: 
      current_page=6
#      if "paging" in status: 
#        url = status['paging']['next']
#        current_page += 1
#      else: current_page=6

  return listStatus 

def get_tagged(userid):
  """
  provides as ouput a list of dictionaries that include tagged messages, time, # of comments,
  and list of comments (as another list of dict) when #>0
  """
#  tagged = graph.get_connections(userid, "tagged")
  listTagged=[]
  BASE_URL = 'https://graph.facebook.com/%s/tagged?access_token='%userid
  url = BASE_URL + token
  max_pages=5
  current_page=0
  while current_page <= max_pages: 
    tagged = json.loads(urllib2.urlopen(url).read())
    print "doing page: ",current_page 
    for elem in tagged["data"]:
      dict={}
      if "message" in elem.keys():
        dict["Fbid"]= elem["id"]
        dict["tagged_message"]= elem["message"]
        dict["time"]= elem["updated_time"]
        dict["from"]= elem["from"]["name"]
        dict["from_userid"]=elem["from"]["id"]  
        listTagged.append(dict)
      else:
        dict["Fbid"]= elem["id"]
        dict["tagged_message"]= elem["name"]
        dict["time"]= elem["updated_time"]
        dict["from"]= elem["from"]["name"]
        dict["from_userid"]=elem["from"]["id"]  
        listTagged.append(dict)
    if "paging" in tagged: 
      url = tagged['paging']['next']
      current_page += 1
    else: current_page=6
      
  return listTagged 
    
def get_photos(userid):
  """
  provides as ouput a list of dictionaries that include photos, time, # of comments,
  and list of comments (as another list of dict) when #>0
  """
#  photos = graph.get_connections(userid, "photos")
  listPhotos=[]
  BASE_URL = 'https://graph.facebook.com/%s/photos?access_token='%userid
  url = BASE_URL + token
  max_pages=5
  current_page=0
  while current_page <= max_pages: 
    try:
      photos = json.loads(urllib2.urlopen(url).read())
      print "doing page: ",current_page 
      for elem in photos["data"]:
        dict={}
        if "name" in elem: dict["description"]= elem["name"]
        else: dict["description"]=0
        dict["Fbid"]= elem["id"]
        if "images" in elem: dict["link_to_html"]= elem["images"][0]["source"]
        else: dict["link_to_html"]=0
        dict["time"]= elem["updated_time"]
        if "tags" in elem: dict["NofTags"]= len(elem["tags"]["data"]) 
        else: dict["NofTags"]=0
        if "likes" in elem: dict["NofLikes"]= len(elem["likes"]["data"])
        else: dict["NofLikes"]=0
        if "place" in elem: dict["place"]= elem["place"]["name"]
        else: dict["place"]=0
        if "comments" in elem:
          dict["NofComments"]= len(elem["comments"]["data"])
          count = 1
          dict["comments"]=[]
          for comment in elem["comments"]["data"]: 
	    count +=1    
	    dict_comments={}
	    dict_comments["text"]=comment["message"]
	    dict_comments["time"]=comment["created_time"]
	    dict_comments["from"]=comment["from"]["name"]  
	    dict_comments["from_userid"]=comment["from"]["id"]  
	    dict["comments"].append(dict_comments)
        else: dict["NofComments"]=0 	
        listPhotos.append(dict)
      if "paging" in photos: 
        url = photos['paging']['next']
        current_page += 1
      else: current_page=6
    except: 
      if "paging" in photos: 
        url = photos['paging']['next']
        current_page += 1
      else: current_page=6
      
  return listPhotos

def get_links(userid):
  """
  provides as ouput a list of dictionaries that include links, time, # of comments,
  and list of comments (as another list of dict) when #>0
  """
#  links = graph.get_connections(userid, "links")
  listLinks=[]
  BASE_URL = 'https://graph.facebook.com/%s/links?access_token='%userid
  url = BASE_URL + token
  max_pages=5
  current_page=0
  while current_page <= max_pages: 
    links = json.loads(urllib2.urlopen(url).read())
    print "doing page: ",current_page 
    for elem in links["data"]:
      dict={}
      dict["Fbid"]= elem["id"]
      if "message" in elem: dict["message"]= elem["message"]
      else: dict["message"]=0
      if "text" in elem: dict["text"]= elem["text"]
      else: dict["text"]=0
      if "link" in elem: dict["link_to_html"]= elem["link"]
      else: dict["link_to_html"]=0
      if "created_time" in elem: dict["time"]= elem["created_time"]
      else: dict["time"]="2000-01-01"
#    if "tags" in elem: dict["NofTags"]= len(elem["tags"]["data"])
      if "comments" in elem:
        dict["NofComments"]= len(elem["comments"]["data"])
        count = 1
        dict["comments"]=[]
        for comment in elem["comments"]["data"]: 
	  count +=1    
	  dict_comments={}
	  dict_comments["text"]=comment["message"]
	  dict_comments["time"]=comment["created_time"]
	  dict_comments["from"]=comment["from"]["name"]  
	  dict_comments["from_userid"]=comment["from"]["id"]  
	  dict["comments"].append(dict_comments)
      else: dict["NofComments"]=0 	
      listLinks.append(dict)
    if "paging" in links and 'next' in links['paging']: 
      url = links['paging']['next']
      current_page += 1
    else: current_page=6

  return listLinks

	     
def main():


  friends = graph.get_connections("501326469", "friends")
#  friend_NameId = [[friend['name'],friend['id']] for friend in friends['data']]

  friends_NameIdPicture=[]
  for friend in friends['data']:
    picture = graph.get_connections(friend["id"], "picture")
    if "url" in picture: 
      friends_NameIdPicture.append([friend['name'],friend['id'],picture["url"]])
    else:
      friends_NameIdPicture.append([friend['name'],friend['id'],"no picture"])


#  cursor.execute("SELECT * FROM Newsfeed ORDER BY NofComments DESC")
#  print cursor.fetchone()

## SQL section

  cursor.execute("CREATE TABLE IF NOT EXISTS Friends(Name VARCHAR(50), user_id BIGINT PRIMARY KEY, picture_url VARCHAR(500))")
##  for elem in friends_NameIdPicture:
##    cursor.execute("INSERT INTO Friends(Name, user_id, picture_url) VALUES (%s, %s, %s);", (elem[0], elem[1], elem[2]) ) 
#  cursor.execute("INSERT INTO Friends(Name, user_id) VALUES (%s, %s);", (friend_NameId[110][0], friend_NameId[110][1]) ) 

  cursor.execute("CREATE TABLE IF NOT EXISTS Newsfeed(news_id VARCHAR(500) PRIMARY KEY, user_id BIGINT, feed VARCHAR(500), time VARCHAR(100), NofComments INT, ClassifierP FLOAT, ClassifierR FLOAT, ClassifierS FLOAT, FOREIGN KEY (user_id) REFERENCES Friends(user_id))")

  cursor.execute("CREATE TABLE IF NOT EXISTS StatusUpdate(status_id VARCHAR(500) PRIMARY KEY, user_id BIGINT, status_update VARCHAR(3000), time VARCHAR(100), NofComments INT, NofLikes INT, ClassifierP FLOAT, ClassifierR FLOAT, ClassifierS FLOAT, FOREIGN KEY (user_id) REFERENCES Friends(user_id))")

  cursor.execute("CREATE TABLE IF NOT EXISTS Photos(photos_id VARCHAR(500), user_id BIGINT, description VARCHAR(1500), place VARCHAR(100), link_to_html VARCHAR(500), time VARCHAR(100), NofComments INT, NofLikes INT, NofTags INT, ClassifierP FLOAT, ClassifierR FLOAT, ClassifierS FLOAT, PRIMARY KEY (photos_id, user_id), FOREIGN KEY (user_id) REFERENCES Friends(user_id))")

  cursor.execute("CREATE TABLE IF NOT EXISTS Links(link_id VARCHAR(500) PRIMARY KEY, user_id BIGINT, message VARCHAR(1000), text VARCHAR(500), link_to_html VARCHAR(500), time VARCHAR(100), NofComments INT, ClassifierP FLOAT, ClassifierR FLOAT, ClassifierS FLOAT, Classifier2P FLOAT, Classifier2R FLOAT, Classifier2S FLOAT, FOREIGN KEY (user_id) REFERENCES Friends(user_id))")

#  cursor.execute("SELECT friend_id FROM Friends WHERE user_id=%s","1549970621")  
#  friend_id= cursor.fetchone()
#  print friend_id

  cursor.execute("CREATE TABLE IF NOT EXISTS Comments(news_id VARCHAR(500) NOT NULL DEFAULT 0, status_id VARCHAR(500) NOT NULL DEFAULT 0, photos_id VARCHAR(500) NOT NULL DEFAULT 0, link_id VARCHAR(500) NOT NULL DEFAULT 0, user_id BIGINT, text VARCHAR(2500), sender VARCHAR(50), sender_id BIGINT, time VARCHAR(100), FOREIGN KEY (news_id) REFERENCES Newsfeed(news_id), FOREIGN KEY (status_id) REFERENCES StatusUpdate(status_id), FOREIGN KEY (photos_id) REFERENCES Photos(photos_id), FOREIGN KEY (link_id) REFERENCES Links(link_id), FOREIGN KEY (user_id) REFERENCES Newsfeed(user_id))")
  cursor.execute("SET foreign_key_checks = 0")

#  user_Fbid=["628401352","1549970621","1236828","1272032175","100000452109060"]
#  for user in user_Fbid:

  for elem in friends_NameIdPicture[130:]:

    user=elem[1]   
    print "running for user ",user 
 
#  get_feeds("1549970621") 
#  get_status("1549970621")
#  print get_feeds("1549970621") 
    Feed_dict= get_feeds(user)
#  print Feed_dict 
    Status_dict= get_status(user)
#  print get_status("1549970621")
#  print get_tagged("1549970621")
    Photos_dict=get_photos(user)
#  for elem in Photos_dict: print elem
    Links_dict=get_links(user)
#  for elem in dictLinks: print elem

  
    for elem in Feed_dict: 
      outcome_1=0
      outcome_2=0
      outcome_3=0
      if elem["feed"]!=0:
        outcome = classifier.prob_classify(encode_str(elem["feed"]))
        outcome_1 = outcome.prob('politics')       
        outcome_2 = outcome.prob('relationship')       
        outcome_3 = outcome.prob('sports')       
      cursor.execute("INSERT INTO Newsfeed(news_id, user_id, feed, time, NofComments, ClassifierP, ClassifierR, ClassifierS) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);", (elem["Fbid"], user, encode_str(elem["feed"]),elem["time"][:10],elem["NofComments"], outcome_1, outcome_2, outcome_3) ) 
      if "comments" in elem: 
        for comm in elem["comments"]:
          cursor.execute("INSERT INTO Comments(news_id, status_id, photos_id, link_id, user_id, text, sender, sender_id, time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);", (elem["Fbid"], "0", "0", "0", user, encode_str(comm["text"]), encode_str(comm["from"]),comm["from_userid"],comm["time"][:10]) ) 

    for elem in Status_dict:       
      outcome_1=0
      outcome_2=0
      outcome_3=0
      if elem["status_update"] !=0:
        outcome = classifier.prob_classify(encode_str(elem["status_update"]))
        outcome_1 = outcome.prob('politics')       
        outcome_2 = outcome.prob('relationship')       
        outcome_3 = outcome.prob('sports')       
      cursor.execute("INSERT INTO StatusUpdate(status_id, user_id, status_update, time, NofComments, NofLikes, ClassifierP, ClassifierR, ClassifierS) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);", (elem["Fbid"], user, encode_str(elem["status_update"]), elem["time"][:10],elem["NofComments"],elem["NofLikes"], outcome_1, outcome_2, outcome_3) ) 
      if "comments" in elem: 
        for comm in elem["comments"]:
          cursor.execute("INSERT INTO Comments(news_id, status_id, photos_id, link_id, user_id, text, sender, sender_id, time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);", ("0", elem["Fbid"], "0", "0", user, encode_str(comm["text"]), encode_str(comm["from"]),comm["from_userid"],comm["time"][:10]) ) 

    for elem in Photos_dict:       
      outcome_1=0
      outcome_2=0
      outcome_3=0
      if elem["description"] != 0: 
        outcome = classifier.prob_classify(encode_str(elem["description"]))
        outcome_1 = outcome.prob('politics')       
        outcome_2 = outcome.prob('relationship')       
        outcome_3 = outcome.prob('sports')       
      cursor.execute("INSERT INTO Photos(photos_id, user_id, description, place, link_to_html, time, NofComments, NofLikes, NofTags, ClassifierP, ClassifierR, ClassifierS) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);", (elem["Fbid"], user, encode_str(elem["description"]), encode_str(elem["place"]), elem["link_to_html"],elem["time"][:10],elem["NofComments"],elem["NofLikes"],elem["NofTags"], outcome_1, outcome_2, outcome_3) ) 
      if "comments" in elem: 
        for comm in elem["comments"]:
          cursor.execute("INSERT INTO Comments(news_id, status_id, photos_id, link_id, user_id, text, sender, sender_id, time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);", ("0","0", elem["Fbid"], "0", user, encode_str(comm["text"]), encode_str(comm["from"]),comm["from_userid"],comm["time"][:10]) ) 

    for elem in Links_dict:
      outcome_1=0
      outcome_2=0
      outcome_3=0
      outcome2_1=0
      outcome2_2=0
      outcome2_3=0
      if elem["message"]!=0:       
        outcome = classifier.prob_classify(encode_str(elem["message"]))
        outcome_1 = outcome.prob('politics')       
        outcome_2 = outcome.prob('relationship')       
        outcome_3 = outcome.prob('sports')       
      if elem["text"]!=0:
        outcome2 = classifier.prob_classify(encode_str(elem["text"]))
        outcome2_1 = outcome2.prob('politics')       
        outcome2_2 = outcome2.prob('relationship')       
        outcome2_3 = outcome2.prob('sports')       
      cursor.execute("INSERT INTO Links(link_id, user_id, message, text, link_to_html, time, NofComments, ClassifierP, ClassifierR, ClassifierS, Classifier2P, Classifier2R, Classifier2S) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);", (elem["Fbid"], user, encode_str(elem["message"]), encode_str(elem["text"]), encode_str(elem["link_to_html"]), elem["time"][:10], elem["NofComments"], outcome_1, outcome_2, outcome_3, outcome2_1, outcome2_2, outcome2_3) ) 
      if "comments" in elem: 
        for comm in elem["comments"]:
          cursor.execute("INSERT INTO Comments(news_id, status_id, photos_id, link_id, user_id, text, sender, sender_id, time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);", ("0", "0", "0", elem["Fbid"], user, encode_str(comm["text"]), encode_str(comm["from"]),comm["from_userid"],comm["time"][:10]) ) 


    db.commit()
#  cursor.execute("SELECT * FROM Friends")
#  print cursor.fetchall()

 
if __name__ == '__main__':
  main()
