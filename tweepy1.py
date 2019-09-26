'''
TODO:
Test file
Set it up so that multiple accounts can use, then the db is cleared semi-regularly?
Check for updates on running, and update rather than skip existing entries
Add content based filters?
'''

import os
import tweepy
import time
import datetime
import sqlalchemy
from textblob import TextBlob
from sqlalchemy import Table, Column, String, Integer, ForeignKey, Float, BIGINT

passw = os.environ.get("DATABASEPW")
newdb = "TwitterCapstone"

engine = sqlalchemy.create_engine(f'mysql+pymysql://root:{passw}@localhost/{newdb}?charset=utf8mb4')
connection = engine.connect()
meta = sqlalchemy.MetaData()

consumerkey = os.environ.get("TWTKEY")
secretkey = os.environ.get("TWTKEYSEC")
authtoken = os.environ.get("AUTHKEY")
authsecret = os.environ.get("AUTHKEYSEC")

auth = tweepy.OAuthHandler(consumerkey, secretkey)
auth.set_access_token(authtoken, authsecret)

api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

# initialize the tables in the db which stores the unique id, name, and sentiment score for users
accounts = Table(
    'accounts',
    meta,
    Column('id', BIGINT, primary_key=True),
    Column('name', String(100)),
    Column('description', String(500)),
    Column('age_weeks', Integer),
    Column('numfollowers', Integer),
    Column('numfriends', Integer),
    Column('numtweets', Integer),
    Column('avgtweetchars', Float),
    Column('sentiment_polarity', Float),
    Column('sentiment_objectivity', Float)
)

relationships = Table(
    'relationships',
    meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('followerid', BIGINT, ForeignKey(accounts.columns.id, ondelete='CASCADE', onupdate='CASCADE')),
    Column('followedid', BIGINT, ForeignKey(accounts.columns.id, ondelete='CASCADE', onupdate='CASCADE'))
)

meta.create_all(engine)
print('>Tables Connected')


def avgtweet(accname):
    '''
    takes an account id, and returns the average length in characters of the past 20 tweets
    '''

    tweets = api.user_timeline(screen_name=accname)
    tweettext = []
    tweetchars = 0

    for tweet in tweets:
        text = tweet.text
        tweettext.append(text)
        tweetchars += len(str(text))

    try:
        avg = tweetchars / len(tweettext)
    except ZeroDivisionError:
        avg = 0
    return avg


def ageinweeks(accname):
    '''
    takes an account id, and returns the account age (in weeks) as an integer
    '''

    date = str(api.get_user(screen_name=accname).created_at)[:10]
    strippedaccdate = time.strptime(date, "%Y-%m-%d")

    current = datetime.date.today()
    strippedcurrent = time.strptime(str(current), "%Y-%m-%d")

    diffy = ((strippedcurrent.tm_year - strippedaccdate.tm_year) * 52)
    diffm = ((strippedcurrent.tm_mon - strippedaccdate.tm_mon) * 4)
    diffd = ((strippedcurrent.tm_mday - strippedaccdate.tm_mday) / 7)

    diff = int(diffy + diffm + diffd)

    return diff


def accsentiment(accname, senttype):
    '''
    takes an account name, and type (either 'pol' or 'sub') as a string and returns
    either the polarity mean score between -1 and 1 or the subjectivity mean score between 0 and 1
    '''

    tweets = api.user_timeline(screen_name=accname)

    tweetscores = []
    tweettext = [tweet.text for tweet in tweets]

    if senttype == 'pol':
        for tweet in tweettext:
            tweetscores.append(TextBlob(tweet).sentiment.polarity)
        try:
            accountscore = sum(tweetscores) / len(tweetscores)
        except ZeroDivisionError:
            accountscore = 0

    elif senttype == 'sub':
        for tweet in tweettext:
            tweetscores.append(TextBlob(tweet).sentiment.subjectivity)
        try:
            accountscore = sum(tweetscores) / len(tweetscores)
        except ZeroDivisionError:
            accountscore = 0

    return accountscore


def writefollowers(accname):
    '''
    takes an account name as a string, and writes to the accounts table the information of all followers, and to
    the relationships table the relationship
    '''

    accid = api.get_user(screen_name=accname).id
    writeaccount(accid)

    followerids = api.followers_ids(accid)

    for followerid in followerids:
        try:
            writeaccount(followerid)
        except tweepy.TweepError:
            print("User Raised Error, not writing.")

        writerelationship(followerid, accid)

    print(f"Successfully added followers of {accname} to db")


def writefriends(accname):
    '''
    takes an account name as a string, and writes to the accounts table the information of all followers, and to
    the relationships table the relationship
    '''

    accid = api.get_user(screen_name=accname).id
    writeaccount(accid)

    friendids = api.friends_ids(accid)

    for friendid in friendids:
        try:
            writeaccount(friendid)
        except tweepy.TweepError:
            print("User Raised Error, not writing.")
        writerelationship(accid, friendid)

    print(f"Successfully added friends of {accname} to db")


def writeaccount(accid):
    '''
    takes an account id, and writes to the database all of the details on that account, including
    id, name, bio, count of followers, count of friends (follows), count of tweets,
    avg length of tweets, and age of account (in weeks).
    '''

    id = accid
    f = api.get_user(accid)
    name = f.screen_name

    request = accounts.insert().values(
        id=id,
        name=name,
        description=f.description,
        numfollowers=f.followers_count,
        numfriends=f.friends_count,
        numtweets=f.statuses_count,
        avgtweetchars=avgtweet(name),
        age_weeks=ageinweeks(name),
        sentiment_polarity=accsentiment(name, 'pol'),
        sentiment_objectivity=accsentiment(name, 'sub'),
    ).prefix_with("IGNORE")

    connection.execute(request)
    print(f"{name} added to db")

    print(f"Successfully added {name} to db")


def writerelationship(follower, followed):
    '''
    takes 2 account ids, and writes to the database the relationship between the accounts
    '''

    name1 = api.get_user(follower).screen_name
    name2 = api.get_user(followed).screen_name

    relaterequest = relationships.insert().values(
        followerid=follower,
        followedid=followed
    ).prefix_with("IGNORE")

    connection.execute(relaterequest)
    print(f"Recorded that: {name1} follows {name2}")


def writefriendsoffriends(accname):
    '''
    takes an account name as a string, and writes to the accounts table the information of all those followed
    by the friends of the original account, and to the relationships table those relationships
    '''

    writefriends(accname)

    accid = api.get_user(screen_name=accname).id
    friendids = api.friends_ids(accid)

    secondary_friends_dict = {}

    for friendid in friendids:
        secondary_friends = api.friends_ids(friendid)
        secondary_friends_dict[friendid]: secondary_friends

    for friend, secondaryfriends in secondary_friends_dict:
        try:
            for secondfriend in secondaryfriends:
                writeaccount(secondfriend)
                writerelationship(friend, secondfriend)
        except tweepy.TweepError:
            print("User Raised Error, not writing.")

    print(f"Successfully added friends of friends of {accname} to db")