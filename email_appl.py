#!/usr/bin/env python

import os

from flask import Flask
from flask import url_for
from flask import render_template
from flask import jsonify
from flask import request

import MySQLdb
import facebook
import operator

from flask.ext.mail import Message
from flask.ext.mail import Mail

import math

from flask import session,redirect
from flask_oauth import OAuth

import re

# administrator list
ADMINS = ['your-email']

CLIENT_ID = 'yourappid'
CLIENT_SECRET = 'yourappsecret'
SECRET_KEY = 'development key'

app = Flask(__name__)

# email server
app.config.update(
	DEBUG=True,
	#EMAIL SETTINGS
	MAIL_SERVER='smtp.gmail.com',
	MAIL_PORT=465,
	MAIL_USE_SSL=True,
	MAIL_USERNAME = 'myfbdigest@gmail.com',
	MAIL_PASSWORD = 'yourpasswd'
	)

mail=Mail(app)


online_token=""

db = MySQLdb.connect("","root","yourpasswd","db_name")
cursor = db.cursor()

cursor.execute("SELECT * FROM Friends")
FriendsList = cursor.fetchall()


##login facebook
app.secret_key = SECRET_KEY
oauth = OAuth()

EXTENDED_PERMS = [ 'user_about_me','friends_about_me', 'user_activities', 'friends_activities', 'user_birthday', 'friends_birthday', 'user_education_history', 'friends_education_history', 'user_events', 'friends_events', 'user_groups', 'friends_groups', 'user_hometown', 'friends_hometown', 'user_interests', 'friends_interests', 'user_likes', 'friends_likes', 'user_location', 'friends_location', 'user_notes', 'friends_notes', 'user_online_presence', 'friends_online_presence', 'user_photo_video_tags', 'friends_photo_video_tags', 'user_photos', 'friends_photos', 'user_relationships', 'friends_relationships', 'user_religion_politics', 'friends_religion_politics', 'user_status', 'friends_status', 'user_videos', 'friends_videos', 'user_website', 'friends_website', 'user_work_history', 'friends_work_history', 'email','read_friendlists', 'read_requests', 'read_stream', 'user_checkins', 'friends_checkins', ]
facebook = oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=CLIENT_ID,
    consumer_secret=CLIENT_SECRET,
    request_token_params={'scope': ','.join(EXTENDED_PERMS)}
)

@facebook.tokengetter
def get_facebook_token():
    return session.get('facebook_token')

def pop_login_session():
    session.pop('logged_in', None)
    session.pop('facebook_token', None)

@app.route('/')
def main():
    return render_template('container-subscribe-classifier.html')

@app.route('/about')
def about():
    return render_template('about.html') 

@app.route('/authenticated')
def authenticated():
    print  session['facebook_token']  

    return render_template('container-subscribe-auth.html')


@app.route('/FacebookLogin')
def FacebookLogin():
    return facebook.authorize(callback=url_for('facebook_authorized',
        next=request.args.get('next'), _external=True))

@app.route("/facebook_authorized")
@facebook.authorized_handler
def facebook_authorized(resp):
    next_url = request.args.get('next') or url_for('authenticated')
    if resp is None or 'access_token' not in resp:
        return redirect(next_url)

    session['logged_in'] = True
    session['facebook_token'] = (resp['access_token'], '')

    return redirect(next_url)


@app.route('/subscriptionConfirm',methods=['POST'])
def subscriptionConfirm():

    timeFrame=request.form["EmailFrequency"]
    print timeFrame

    emailaddress=[]
    emailaddress.append(request.form["EmailAddress"])
    print emailaddress

    PreferredTopic =  request.form["topics"]
    print PreferredTopic

#closeness weight
    listWeights=[] 
    cursor.execute("SELECT user_id,COUNT(*) FROM Comments GROUP BY user_id;")
    aggregate1=cursor.fetchall()
    cursor.execute("SELECT Comments.user_id,COUNT(*) FROM Comments,Friends WHERE Friends.user_id = Comments.sender_id AND Comments.sender_id!=Comments.user_id GROUP BY Comments.user_id;") 
    aggregate2=cursor.fetchall()
    cursor.execute("SELECT Comments.user_id,COUNT(*),MAX(EXTRACT(YEAR_MONTH FROM time)),EXTRACT(YEAR_MONTH FROM NOW()) FROM Comments,Friends WHERE Friends.user_id = Comments.sender_id AND Comments.sender_id=501326469 GROUP BY Comments.user_id;") 
    aggregate2_mycomments=cursor.fetchall()
#reweight more closer interaction in time
    for elem in aggregate2_mycomments:
      if abs(elem[2]-elem[3])<25: elem[1]=10*elem[1] 
      elif abs(elem[2]-elem[3])<75:  elem[1]=8*elem[1]
      elif abs(elem[2]-elem[3])<125:  elem[1]=5*elem[1]
      elif abs(elem[2]-elem[3])<175:  elem[1]=2*elem[1]
# reweight more for my comments
    for elem in aggregate2:
      for elem_my in aggregate2_mycomments:
        if elem[0]==elem_my[0]: elem[1]=elem[1]+9*elem_my[1]
# build ratio
    for denom in aggregate1:
      for numer in aggregate2:
        if numer[0]==denom[0]: 
	  print numer[0],numer[1]/float(denom[1]),"+/-",numer[1]/float(denom[1])*math.sqrt(1/float(numer[1])+1/float(denom[1]))  
          listWeights.append([numer[0],numer[1]/float(denom[1]),numer[1]/float(denom[1])*math.sqrt(1/float(numer[1])+1/float(denom[1]))])

# avg #of comments for user in different categories
    cursor.execute("SELECT user_id,AVG(NofComments) FROM Newsfeed GROUP BY user_id;")
    avgCommFeed = cursor.fetchall()
    cursor.execute("SELECT user_id,AVG(NofComments) FROM Photos GROUP BY user_id;")
    avgCommPhotos = cursor.fetchall()
    cursor.execute("SELECT user_id,AVG(NofComments) FROM StatusUpdate GROUP BY user_id;")
    avgCommStatus = cursor.fetchall()
    cursor.execute("SELECT user_id,AVG(NofComments) FROM Links GROUP BY user_id;")
    avgCommLinks = cursor.fetchall()

    cursor.execute("SELECT * FROM Newsfeed WHERE time>=DATE_ADD(NOW(), INTERVAL -%s DAY) ORDER BY NofComments DESC", timeFrame)
    recommend = cursor.fetchall()
# news_id, user_id, news, time, #comments    
    #print recommend
    cursor.execute("SELECT * FROM Photos WHERE time>=DATE_ADD(NOW(), INTERVAL -%s DAY) ORDER BY NofComments DESC;", timeFrame)
    recommend2 = cursor.fetchall()
# photo_id, user_id, text, place, link, date, #comments, #likes, #tags 
#    print recommend2
    cursor.execute("SELECT * FROM StatusUpdate WHERE time>=DATE_ADD(NOW(), INTERVAL -%s DAY) ORDER BY NofComments DESC;", timeFrame)
    recommend3 = cursor.fetchall()
# status_id, user_id, text, time, #comments, #likes
    cursor.execute("SELECT * FROM Links WHERE time>=DATE_ADD(NOW(), INTERVAL -%s DAY) ORDER BY NofComments DESC;", timeFrame)
    recommend4 = cursor.fetchall()
# link_id, user_id, message, text, html_link, time, #comments

    def weightFunc(user_id,listWeights):
      weight=0
      for weightObj in listWeights:
        if weightObj[0]==user_id: weight= weightObj[1] 
      return 5.*weight

    def normalizeFunc(user_id,avgList):
      avgComm=0
      for user in avgList:
        if user[0]==user_id: avgComm= user[1] 
      if avgComm!=0: return float(avgComm)
      else: return 1.

#closeness weight
    listWeights=[] 
    cursor.execute("SELECT user_id,COUNT(*) FROM Comments GROUP BY user_id;")
    aggregate1=cursor.fetchall()
    cursor.execute("SELECT Comments.user_id,COUNT(*) FROM Comments,Friends WHERE Friends.user_id = Comments.sender_id GROUP BY Comments.user_id;") 
    aggregate2=cursor.fetchall()
    for denom in aggregate1:
      for numer in aggregate2:
        if numer[0]==denom[0]: 
	  print numer[0],numer[1]/float(denom[1]),"+/-",numer[1]/float(denom[1])*math.sqrt(1/float(numer[1])+1/float(denom[1]))  
          listWeights.append([numer[0],numer[1]/float(denom[1]),numer[1]/float(denom[1])*math.sqrt(1/float(numer[1])+1/float(denom[1]))])

# avg #of comments for user in different categories
    cursor.execute("SELECT user_id,AVG(NofComments) FROM Newsfeed GROUP BY user_id;")
    avgCommFeed = cursor.fetchall()
    cursor.execute("SELECT user_id,AVG(NofComments) FROM Photos GROUP BY user_id;")
    avgCommPhotos = cursor.fetchall()
    cursor.execute("SELECT user_id,AVG(NofComments) FROM StatusUpdate GROUP BY user_id;")
    avgCommStatus = cursor.fetchall()
    cursor.execute("SELECT user_id,AVG(NofComments) FROM Links GROUP BY user_id;")
    avgCommLinks = cursor.fetchall()

    cursor.execute("SELECT * FROM Newsfeed WHERE time>=DATE_ADD(NOW(), INTERVAL -%s DAY) ORDER BY NofComments DESC", timeFrame)
    recommend = cursor.fetchall()
# news_id, user_id, news, time, #comments, classP, classR, classS    
    #print recommend
    cursor.execute("SELECT * FROM Photos WHERE time>=DATE_ADD(NOW(), INTERVAL -%s DAY) ORDER BY NofComments DESC;", timeFrame)
    recommend2 = cursor.fetchall()
# photo_id, user_id, text, place, link, date, #comments, #likes, #tags, classP, classR, classS 
#    print recommend2
    cursor.execute("SELECT * FROM StatusUpdate WHERE time>=DATE_ADD(NOW(), INTERVAL -%s DAY) ORDER BY NofComments DESC;", timeFrame)
    recommend3 = cursor.fetchall()
# status_id, user_id, text, time, #comments, #likes, classP, classR, classS
    cursor.execute("SELECT * FROM Links WHERE time>=DATE_ADD(NOW(), INTERVAL -%s DAY) ORDER BY NofComments DESC;", timeFrame)
    recommend4 = cursor.fetchall()
# link_id, user_id, message, text, html_link, time, #comments, classP, classR, classS

    def weightFunc(user_id,listWeights):
      weight=0
      for weightObj in listWeights:
        if weightObj[0]==user_id: weight= weightObj[1] 
      return 5.*weight

    def normalizeFunc(user_id,avgList):
      avgComm=0
      for user in avgList:
        if user[0]==user_id: avgComm= user[1] 
      if avgComm!=0: return float(avgComm)
      else: return 1.

#preferred topic Weight
    topicWeight=[1.,1.,1.,1.,1.,1.,1.] # all, news, photos, status
    if PreferredTopic=="news": topicWeight[0]=10
    elif PreferredTopic=="photos": topicWeight[1]=10
    elif PreferredTopic=="shared links/likes": topicWeight[2]=10
    elif PreferredTopic=="politics": topicWeight[3]=30
    elif PreferredTopic=="relationships": topicWeight[4]=30
    elif PreferredTopic=="sports": topicWeight[5]=30
    
    def modifyRecommend(recommend):
      newRecommend=[]
      for elem in recommend:
        newlist=list(elem)
        if newlist[2]!=0 and (re.search(r'[cC]ompleanno',newlist[2]) or
	re.search(r'[aA]ugur\w+',newlist[2])):
          tempP=newlist[-3]
          newlist[-3]=newlist[-2]
          newlist[-2]=tempP    
        newRecommend.append(newlist)
      return newRecommend
  
##workaround for birthday classifier -italian case
    recommendN = modifyRecommend(recommend) 
    recommend2N = modifyRecommend(recommend2) 
    recommend3N = modifyRecommend(recommend3) 
    recommend4N = modifyRecommend(recommend4) 

    RecommendationList=[]
# user_id,text, link, time, #comments, #likes, weightfactor
    if PreferredTopic=="news" or PreferredTopic=="photos" or PreferredTopic=="shared links/likes" or PreferredTopic=="Everything":
      for elem in recommend:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommFeed)
         RecommendationList.append([elem[1],elem[2],"",elem[3],elem[4],"",topicWeight[0]*weight*elem[4]/avgNofComm])
      for elem in recommend2:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommPhotos)
         RecommendationList.append([elem[1],elem[2],elem[4],elem[5],elem[6],elem[7],topicWeight[1]*weight*elem[6]/avgNofComm])
      for elem in recommend3:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommStatus)
         RecommendationList.append([elem[1],elem[2],"",elem[3],elem[4],elem[5],topicWeight[2]*weight*elem[4]/avgNofComm])
      for elem in recommend4:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommLinks)
         RecommendationList.append([elem[1],elem[2],elem[4],elem[5],elem[6],"",topicWeight[2]*weight*elem[6]/avgNofComm])
    elif PreferredTopic=="politics": 
      for elem in recommendN:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommFeed)
         if elem[-3]>0.5: RecommendationList.append([elem[1],elem[2],"",elem[3],elem[4],"",elem[-3]])
      for elem in recommend2N:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommPhotos)
         if elem[-3]>0.5: RecommendationList.append([elem[1],elem[2],elem[4],elem[5],elem[6],elem[7],elem[-3]])
      for elem in recommend3N:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommStatus)
         if elem[-3]>0.5: RecommendationList.append([elem[1],elem[2],"",elem[3],elem[4],elem[5],elem[-3]])
      for elem in recommend4N:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommLinks)
         if elem[-3]>0.5: RecommendationList.append([elem[1],elem[2],elem[4],elem[5],elem[6],"",elem[-3]])
    elif PreferredTopic=="relationships": 
      for elem in recommendN:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommFeed)
         if elem[-2]>0.5: RecommendationList.append([elem[1],elem[2],"",elem[3],elem[4],"",elem[-2]])
      for elem in recommend2N:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommPhotos)
         if elem[-2]>0.5: RecommendationList.append([elem[1],elem[2],elem[4],elem[5],elem[6],elem[7],elem[-2]])
      for elem in recommend3N:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommStatus)
         if elem[-2]>0.5: RecommendationList.append([elem[1],elem[2],"",elem[3],elem[4],elem[5],elem[-2]])
      for elem in recommend4N:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommLinks)
         if elem[-2]>0.5: RecommendationList.append([elem[1],elem[2],elem[4],elem[5],elem[6],"",elem[-2]])
    elif PreferredTopic=="sports": 
      for elem in recommend:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommFeed)
         if elem[-1]>0.5: RecommendationList.append([elem[1],elem[2],"",elem[3],elem[4],"",elem[-1]])
      for elem in recommend2:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommPhotos)
         if elem[-1]>0.5: RecommendationList.append([elem[1],elem[2],elem[4],elem[5],elem[6],elem[7],elem[-1]])
      for elem in recommend3:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommStatus)
         if elem[-1]>0.5: RecommendationList.append([elem[1],elem[2],"",elem[3],elem[4],elem[5],elem[-1]])
      for elem in recommend4:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommLinks)
         if elem[-1]>0.5: RecommendationList.append([elem[1],elem[2],elem[4],elem[5],elem[6],"",elem[-1]])

    RecommendationList.sort(key=operator.itemgetter(6),reverse=True)
    #print  RecommendationList
    for elem in RecommendationList: print elem[0],elem[4],elem[6]
    
#associate picture url from facebook profile, last field in each list in recommendationList becomes picture_url
    for elem in RecommendationList[:10]: 
      for friend in  FriendsList:
        if str(elem[0])==str(friend[1]): elem.append(friend[2])
    print  RecommendationList[:10] 
#formatting for html display
    suggestionText=[] 
    count=0
    for elem in RecommendationList[:10]:
      if elem[2]=="": suggestionText.append([elem[7],'{0} on {1} with {2} comments. <a href="www.facebook.com/{3}"> Connect! </a>'.format(elem[1],elem[3][0:10],elem[4],elem[0])])
      else: 
        photolink='Posted a <a href="{0}">Photo</a> on {1} with {2} comments. <a href="www.facebook.com/{3}"> Connect! </a>'.format(elem[2],elem[3][0:10],elem[4], elem[0])
        suggestionText.append([elem[7],photolink])  
    print suggestionText 
    
###send the e-mail
    msg = Message('Facebook e-mail Digest', sender = ADMINS[0], recipients = emailaddress)
    msg.body = ''
    msg.html = render_template("results-app.html",suggestion=suggestionText)
    mail.send(msg)

    return render_template('subscriptionConfirm.html')
    
@app.route('/results-app',methods=['POST'])
def results_app():

    
    return render_template('results-app.html')


@app.route('/demo_auth')
def demo_auth():


    timeFrame="15";
    PreferredTopic="relationships"

#closeness weight
    listWeights=[] 
    cursor.execute("SELECT user_id,COUNT(*) FROM Comments GROUP BY user_id;")
    aggregate1=cursor.fetchall()
    cursor.execute("SELECT Comments.user_id,COUNT(*) FROM Comments,Friends WHERE Friends.user_id = Comments.sender_id GROUP BY Comments.user_id;") 
    aggregate2=cursor.fetchall()
    for denom in aggregate1:
      for numer in aggregate2:
        if numer[0]==denom[0]: 
	  print numer[0],numer[1]/float(denom[1]),"+/-",numer[1]/float(denom[1])*math.sqrt(1/float(numer[1])+1/float(denom[1]))  
          listWeights.append([numer[0],numer[1]/float(denom[1]),numer[1]/float(denom[1])*math.sqrt(1/float(numer[1])+1/float(denom[1]))])

# avg #of comments for user in different categories
    cursor.execute("SELECT user_id,AVG(NofComments) FROM Newsfeed GROUP BY user_id;")
    avgCommFeed = cursor.fetchall()
    cursor.execute("SELECT user_id,AVG(NofComments) FROM Photos GROUP BY user_id;")
    avgCommPhotos = cursor.fetchall()
    cursor.execute("SELECT user_id,AVG(NofComments) FROM StatusUpdate GROUP BY user_id;")
    avgCommStatus = cursor.fetchall()
    cursor.execute("SELECT user_id,AVG(NofComments) FROM Links GROUP BY user_id;")
    avgCommLinks = cursor.fetchall()

    cursor.execute("SELECT * FROM Newsfeed WHERE time>=DATE_ADD(NOW(), INTERVAL -%s DAY) ORDER BY NofComments DESC", timeFrame)
    recommend = cursor.fetchall()
# news_id, user_id, news, time, #comments    
    #print recommend
    cursor.execute("SELECT * FROM Photos WHERE time>=DATE_ADD(NOW(), INTERVAL -%s DAY) ORDER BY NofComments DESC;", timeFrame)
    recommend2 = cursor.fetchall()
# photo_id, user_id, text, place, link, date, #comments, #likes, #tags 
#    print recommend2
    cursor.execute("SELECT * FROM StatusUpdate WHERE time>=DATE_ADD(NOW(), INTERVAL -%s DAY) ORDER BY NofComments DESC;", timeFrame)
    recommend3 = cursor.fetchall()
# status_id, user_id, text, time, #comments, #likes
    cursor.execute("SELECT * FROM Links WHERE time>=DATE_ADD(NOW(), INTERVAL -%s DAY) ORDER BY NofComments DESC;", timeFrame)
    recommend4 = cursor.fetchall()
# link_id, user_id, message, text, html_link, time, #comments

    def weightFunc(user_id,listWeights):
      weight=0
      for weightObj in listWeights:
        if weightObj[0]==user_id: weight= weightObj[1] 
      return 5.*weight

    def normalizeFunc(user_id,avgList):
      avgComm=0
      for user in avgList:
        if user[0]==user_id: avgComm= user[1] 
      if avgComm!=0: return float(avgComm)
      else: return 1.

#closeness weight
    listWeights=[] 
    cursor.execute("SELECT user_id,COUNT(*) FROM Comments GROUP BY user_id;")
    aggregate1=cursor.fetchall()
    cursor.execute("SELECT Comments.user_id,COUNT(*) FROM Comments,Friends WHERE Friends.user_id = Comments.sender_id GROUP BY Comments.user_id;") 
    aggregate2=cursor.fetchall()
    for denom in aggregate1:
      for numer in aggregate2:
        if numer[0]==denom[0]: 
	  print numer[0],numer[1]/float(denom[1]),"+/-",numer[1]/float(denom[1])*math.sqrt(1/float(numer[1])+1/float(denom[1]))  
          listWeights.append([numer[0],numer[1]/float(denom[1]),numer[1]/float(denom[1])*math.sqrt(1/float(numer[1])+1/float(denom[1]))])

# avg #of comments for user in different categories
    cursor.execute("SELECT user_id,AVG(NofComments) FROM Newsfeed GROUP BY user_id;")
    avgCommFeed = cursor.fetchall()
    cursor.execute("SELECT user_id,AVG(NofComments) FROM Photos GROUP BY user_id;")
    avgCommPhotos = cursor.fetchall()
    cursor.execute("SELECT user_id,AVG(NofComments) FROM StatusUpdate GROUP BY user_id;")
    avgCommStatus = cursor.fetchall()
    cursor.execute("SELECT user_id,AVG(NofComments) FROM Links GROUP BY user_id;")
    avgCommLinks = cursor.fetchall()

    cursor.execute("SELECT * FROM Newsfeed WHERE time>=DATE_ADD(NOW(), INTERVAL -%s DAY) ORDER BY NofComments DESC", timeFrame)
    recommend = cursor.fetchall()
# news_id, user_id, news, time, #comments, classP, classR, classS    
    #print recommend
    cursor.execute("SELECT * FROM Photos WHERE time>=DATE_ADD(NOW(), INTERVAL -%s DAY) ORDER BY NofComments DESC;", timeFrame)
    recommend2 = cursor.fetchall()
# photo_id, user_id, text, place, link, date, #comments, #likes, #tags, classP, classR, classS 
#    print recommend2
    cursor.execute("SELECT * FROM StatusUpdate WHERE time>=DATE_ADD(NOW(), INTERVAL -%s DAY) ORDER BY NofComments DESC;", timeFrame)
    recommend3 = cursor.fetchall()
# status_id, user_id, text, time, #comments, #likes, classP, classR, classS
    cursor.execute("SELECT * FROM Links WHERE time>=DATE_ADD(NOW(), INTERVAL -%s DAY) ORDER BY NofComments DESC;", timeFrame)
    recommend4 = cursor.fetchall()
# link_id, user_id, message, text, html_link, time, #comments, classP, classR, classS

    def weightFunc(user_id,listWeights):
      weight=0
      for weightObj in listWeights:
        if weightObj[0]==user_id: weight= weightObj[1] 
      return 5.*weight

    def normalizeFunc(user_id,avgList):
      avgComm=0
      for user in avgList:
        if user[0]==user_id: avgComm= user[1] 
      if avgComm!=0: return float(avgComm)
      else: return 1.

#preferred topic Weight
    topicWeight=[1.,1.,1.,1.,1.,1.,1.] # all, news, photos, status
    if PreferredTopic=="news": topicWeight[0]=10
    elif PreferredTopic=="photos": topicWeight[1]=10
    elif PreferredTopic=="shared links/likes": topicWeight[2]=10
    elif PreferredTopic=="politics": topicWeight[3]=30
    elif PreferredTopic=="relationships": topicWeight[4]=30
    elif PreferredTopic=="sports": topicWeight[5]=30
    
    def modifyRecommend(recommend):
      newRecommend=[]
      for elem in recommend:
        newlist=list(elem)
        if newlist[2]!=0 and (re.search(r'[cC]ompleanno',newlist[2]) or
	re.search(r'[aA]ugur\w+',newlist[2])):
          tempP=newlist[-3]
          newlist[-3]=newlist[-2]
          newlist[-2]=tempP    
        newRecommend.append(newlist)
      return newRecommend
  
##workaround for birthday classifier
    recommendN = modifyRecommend(recommend) 
    recommend2N = modifyRecommend(recommend2) 
    recommend3N = modifyRecommend(recommend3) 
    recommend4N = modifyRecommend(recommend4) 

    RecommendationList=[]
# user_id,text, link, time, #comments, #likes, weightfactor
    if PreferredTopic=="news" or PreferredTopic=="photos" or PreferredTopic=="shared links/likes" or PreferredTopic=="Everything":
      for elem in recommend:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommFeed)
         RecommendationList.append([elem[1],elem[2],"",elem[3],elem[4],"",topicWeight[0]*weight*elem[4]/avgNofComm])
      for elem in recommend2:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommPhotos)
         RecommendationList.append([elem[1],elem[2],elem[4],elem[5],elem[6],elem[7],topicWeight[1]*weight*elem[6]/avgNofComm])
      for elem in recommend3:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommStatus)
         RecommendationList.append([elem[1],elem[2],"",elem[3],elem[4],elem[5],topicWeight[2]*weight*elem[4]/avgNofComm])
      for elem in recommend4:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommLinks)
         RecommendationList.append([elem[1],elem[2],elem[4],elem[5],elem[6],"",topicWeight[2]*weight*elem[6]/avgNofComm])
    elif PreferredTopic=="politics": 
      for elem in recommendN:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommFeed)
         if elem[-3]>0.5: RecommendationList.append([elem[1],elem[2],"",elem[3],elem[4],"",elem[-3]])
      for elem in recommend2N:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommPhotos)
         if elem[-3]>0.5: RecommendationList.append([elem[1],elem[2],elem[4],elem[5],elem[6],elem[7],elem[-3]])
      for elem in recommend3N:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommStatus)
         if elem[-3]>0.5: RecommendationList.append([elem[1],elem[2],"",elem[3],elem[4],elem[5],elem[-3]])
      for elem in recommend4N:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommLinks)
         if elem[-3]>0.5: RecommendationList.append([elem[1],elem[2],elem[4],elem[5],elem[6],"",elem[-3]])
    elif PreferredTopic=="relationships": 
      for elem in recommendN:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommFeed)
         if elem[-2]>0.5: RecommendationList.append([elem[1],elem[2],"",elem[3],elem[4],"",elem[-2]])
      for elem in recommend2N:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommPhotos)
         if elem[-2]>0.5: RecommendationList.append([elem[1],elem[2],elem[4],elem[5],elem[6],elem[7],elem[-2]])
      for elem in recommend3N:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommStatus)
         if elem[-2]>0.5: RecommendationList.append([elem[1],elem[2],"",elem[3],elem[4],elem[5],elem[-2]])
      for elem in recommend4N:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommLinks)
         if elem[-2]>0.5: RecommendationList.append([elem[1],elem[2],elem[4],elem[5],elem[6],"",elem[-2]])
    elif PreferredTopic=="sports": 
      for elem in recommend:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommFeed)
         if elem[-1]>0.5: RecommendationList.append([elem[1],elem[2],"",elem[3],elem[4],"",elem[-1]])
      for elem in recommend2:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommPhotos)
         if elem[-1]>0.5: RecommendationList.append([elem[1],elem[2],elem[4],elem[5],elem[6],elem[7],elem[-1]])
      for elem in recommend3:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommStatus)
         if elem[-1]>0.5: RecommendationList.append([elem[1],elem[2],"",elem[3],elem[4],elem[5],elem[-1]])
      for elem in recommend4:
         weight=weightFunc(elem[1],listWeights)
         avgNofComm=normalizeFunc(elem[1],avgCommLinks)
         if elem[-1]>0.5: RecommendationList.append([elem[1],elem[2],elem[4],elem[5],elem[6],"",elem[-1]])

    RecommendationList.sort(key=operator.itemgetter(6),reverse=True)
    #print  RecommendationList
    for elem in RecommendationList: print elem[0],elem[4],elem[6]
    
#associate picture url from facebook profile, last field in each list in recommendationList becomes picture_url
    for elem in RecommendationList[:10]: 
      for friend in  FriendsList:
        if str(elem[0])==str(friend[1]): elem.append(friend[2])
    print  RecommendationList[:10] 
#formatting for html display
    suggestionText=[] 
    count=0
    for elem in RecommendationList[:10]:
      if elem[2]=="": suggestionText.append([elem[7],'{0} on {1} with {2} comments. <a href="www.facebook.com/{3}"> Connect! </a>'.format(elem[1],elem[3][0:10],elem[4],elem[0])])
      else: 
        photolink='Posted a <a href="{0}">Photo</a> on {1} with {2} comments. <a href="www.facebook.com/{3}"> Connect! </a>'.format(elem[2],elem[3][0:10],elem[4], elem[0])
        suggestionText.append([elem[7],photolink])  
    print suggestionText 

    return render_template('results-app-demo.html',suggestion=suggestionText)
      
@app.route('/demo_noauth')
def demo_noauth():
    return render_template('notAuthenticated.html')


if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port)
