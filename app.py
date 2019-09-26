'''
TODO:
set filter on visualisation request to handle multiple people (rather than total db)
finish the function to recommend top accounts which aren't followed, but followed by followers.
'''

import os
import tweepy
from bokeh.plotting import figure, output_file, show
from bokeh.models import ColumnDataSource
import sqlalchemy

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

accounts = sqlalchemy.Table(
    'accounts',
    meta,
    autoload=True,
    autoload_with=engine)

relationships = sqlalchemy.Table(
    'relationships',
    meta,
    autoload=True,
    autoload_with=engine)

join = accounts.join(relationships, accounts.columns.id == relationships.columns.followerid)


def getorderedaccounts(name, column, type, num):
    '''
    takes an account name, column data, and number of users requested, and returns a list of the type (ASC or DESC)
    (by column requested) x number of users which follow that account.
    '''

    accid = api.get_user(screen_name=name).id

    result = connection.execute(
        f"SELECT accounts.name, accounts.{column}\
            FROM accounts\
            JOIN relationships\
            ON accounts.id = relationships.followerid\
            WHERE relationships.followedid = {accid}\
            ORDER BY accounts.{column} {type}\
            LIMIT {num}")

    topaccounts = result.fetchall()

    print(f"The {type} {num} accounts by {column} are {topaccounts}")
    return topaccounts


def visualizetwitterdata(x, y):
    '''
    takes two columns and returns a visualization of all of the followers in the db by those two columns
    '''

    output_file(f"graph{x}and{y}.html")

    result = connection.execute("SELECT * FROM accounts")
    set = result.fetchall()

    ids = []
    names = []
    numfollowers = []
    numfriends = []
    numtweets = []
    avgtweetchars = []
    age_weeks = []
    sentiment_polarity = []
    sentiment_objectivity = []

    for n in range(len(set)):
        ids.append(set[n][0])
        names.append(set[n][1])
        numfollowers.append(set[n][3])
        numfriends.append(set[n][4])
        numtweets.append(set[n][5])
        avgtweetchars.append(set[n][6])
        age_weeks.append(set[n][7])
        sentiment_polarity.append(set[n][8])
        sentiment_objectivity.append(set[n][9])

    data = {'id': ids,
            'name':names,
            'numfollowers':numfollowers,
            'numfriends': numfriends,
            'numtweets': numtweets,
            'avgtweetchars': avgtweetchars,
            'age_weeks': age_weeks,
            'polarity': sentiment_polarity,
            'objectivity': sentiment_objectivity}

    source = ColumnDataSource(data=data)

    TOOLTIPS = [
        ("name", "@name"),
        ("id:", "@id"),
        (f"{x}", f"@{x}"),
        (f"{y}", f"@{y}")]

    # create a new plot with a title and axis labels
    p = figure(title="Twitter Correlations",
               x_axis_label=x,
               y_axis_label=y,
               tooltips=TOOLTIPS)

    p.circle(x=f'{x}',
             y=f"{y}",
             source=source,
             size=10,
             line_color="#FFFFFF",
             fill_alpha=0.85,
             fill_color='#6F00AC')

    p.background_fill_color = "#EEEEEE"

    # show the results
    show(p)


def getfollowerratio(accname):
    '''
    takes an account name and returns the followers to following ratio for the account
    '''

    request = sqlalchemy.select([accounts.columns.numfollowers, accounts.columns.numfriends]
                                ).where(accounts.columns.name == accname)

    result = connection.execute(request)
    set = result.fetchall()

    accfollowers = set[0][0]
    accfriends = set[0][1]

    ratio = accfollowers / accfriends

    print(ratio)


def unfollowaccounts(name, column, num):
    '''
    takes an account name and unfollows the bottom [num] accounts based on that the desired column
    '''

    negativenacies = getorderedaccounts(name, column, 'bottom', num)
    print(negativenacies)

    for account in negativenacies:
        print(f"Unfollow {account}?")
        if input("Y/N?:") == "y" or "Y":
            api.destroy_friendship(account)
        else:
            pass
