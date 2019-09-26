<h2>Twitter Bot (WIP)</h2>

(Using Tweepy, sqlalchemy, Bokeh and Textblob)

<u>Overview:</u>

<p> Look to collect basic information about an account, and the accounts following or followed by that account, as well as
the second degree network. Then add this into a database which stores the account information, and 
information concerning the relationships between accounts. 

Info collected: <br>
Name <br>
Description <br> 
Account age in weeks <br> 
Number followers <br> 
Number following <br> 
Number of tweets <br>
Average tweet length <br>
Sentiment score - Polarity (using Textblob) <br>
Sentiment score - Objectivity (using Textblob) <br>

Then, based on the information collected, provide a scatter plot visualisation to compare any of the given columns.

In addition, write functions to allow users to unfollow accounts based on the data collected 
(for example the most negative accounts, based on their Sentiment score)

<u> tweepy1.py </u> : is used for all of the functions which enter data into the db
<u> app.py </u>  : is used for visualization and accessing/using the data. 