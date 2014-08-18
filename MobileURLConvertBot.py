#####################################################################
#####################################################################
### MobileURLConvertBot 1.0                                       ###
### Scans reddit posts that link to the domain en.m.wikipedia.org ###
### and adds a comment to those posts, containing a link to the   ###
### corresponding non-mobile/normal wikipedia page                ###
#####################################################################
#####################################################################
### Made by /u/plork-odol                                         ###
### Based on ReplyBot by /u/GoldenSights                          ###
### (https://github.com/voussoir/reddit/tree/master/ReplyBot)     ###
#####################################################################
#####################################################################

import praw
import time
import sqlite3
import re
from urlparse import urlparse

'''USER CONFIGURATION'''

USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = ""
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
REQUESTLIMIT = 5
#This is how many submissions you want to retrieve all at once.
WAIT = 10 * 60
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.
#Mobile wikipedia links aren't posted that often, so 10 minutes is fine for now. You could speed it up, but i
#don't recommend to make it less then 30, because of the rate limit

'''All done!'''


WAITS = str(WAIT)
try:
  import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
  USERNAME = bot.getu()
  PASSWORD = bot.getp()
  USERAGENT = bot.geta()
except ImportError:
  pass

# Get database
sql = sqlite3.connect('MobileURLConvertBot.db')
print('Loaded SQL Database')
cur = sql.cursor()

# Create table in database
cur.execute('CREATE TABLE IF NOT EXISTS oldsubmissions(ID TEXT)')
print('Loaded Completed table')

sql.commit()

# Login
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD) 

# Scans reddit for posts that link to a mobile wikipedia site
# and adds a comment to those
def scanDomains():
  submissions = r.get_domain_listing('en.m.wikipedia.org', sort='new', limit=REQUESTLIMIT)

  for submission in submissions:
    sid = submission.id

    cur.execute('SELECT * FROM oldsubmissions WHERE ID=?', [sid])
    
    # Check whether the post is already checked in a previous run
    if not cur.fetchone():
      # When adding a comment fails, retry 2 times
      for attempt in range(3):
        try:
          addComment(submission)

        except praw.errors.RateLimitExceeded as e:
          print("Rate limit exceeded. Sleeping for {0} seconds").format(e.sleep_time)
          time.sleep(e.sleep_time)

        except Exception as e:
          print("Couldn't add comment. Error:", e)

      # Add post to database when comment is added or it has failed multiple times    
      cur.execute('INSERT INTO oldsubmissions VALUES(?)', [sid])

def addComment(submission):
  # Remove the '.m'
  normalURL = submission.url.replace('en.m.', 'en.', 1)
  # Reddit's markup can't handle closing parenthesis in urls, so we must escape them
  normalURL = normalURL.replace(')', '\)')
  
  # The url http://en.m.wikipedia.org/wiki/Reddit will get the urlDescription
  # Wikipedia/Reddit
  parser = urlparse(normalURL)
  urlDescription = parser.path
  if urlDescription.startswith('/wiki'):
    urlDescription = urlDescription[5:]

  comment = ( "Please avoid using mobile sites.  \n"
          "**This is the non-mobile url:** *[Wikipedia{0}]({1})*  \n\n"
          "This bot is still in test phase. Please PM me for suggestions, complaints or questions.").format(urlDescription, normalURL)
  submission.add_comment(comment)

  print "Added comment to:", submission.permalink

while True:
  try:
    scanDomains()
  except Exception as e:
    print('An error has occured:', e)

  print('Running again in ' + WAITS + ' seconds')
  sql.commit()
  time.sleep(WAIT)