import re
from datetime import datetime
import snscrape.modules.twitter as sntwitter
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import yfinance as yf

def scrape_and_analyze_stock_tweet_sentiment(
    ticker: str,
    company: str,
    tweet_count: int = 1000,
    from_date: datetime = datetime(2023, 1, 1)):
    # List to hold tweet data
    tweets = []
    from_date_str = from_date.strftime('%Y-%m-%d')
    today_date_str = datetime.now().strftime('%Y-%m-%d')
    query = f"{ticker} OR {company} Stock OR ${ticker} since:{from_date_str} until:{today_date_str}"
    # Scraping tweets
    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
        if i >= tweet_count:  # Limit the number of tweets to scrape
            break
        tweets.append([tweet.date, tweet.user.username, tweet.content])

    # Creating a DataFrame to store the data
    df = pd.DataFrame(tweets, columns=['Date', 'Username', 'Tweet'])

    # Function to clean tweets
    def clean_tweet(tweet):
        # Super basic, not meant to be comprehensive
        # Remove links, special characters, and hashtags
        tweet = re.sub(r'http\S+|www\S+|https\S+', '', tweet, flags=re.MULTILINE)
        tweet = re.sub(r'\@\w+|\#', '', tweet)
        tweet = re.sub(r'[^A-Za-z0-9 ]+', '', tweet)
        return tweet

    # Apply the cleaning function to the tweets
    df['Cleaned_Tweet'] = df['Tweet'].apply(clean_tweet)

    # Initialize VADER sentiment analyzer
    analyzer = SentimentIntensityAnalyzer()

    # Function to analyze sentiment
    def analyze_sentiment(tweet):
        score = analyzer.polarity_scores(tweet)
        if score['compound'] >= 0.05:
            return 'Positive'
        elif score['compound'] <= -0.05:
            return 'Negative'
        else:
            return 'Neutral'

    # Apply sentiment analysis
    df['Sentiment'] = df['Cleaned_Tweet'].apply(analyze_sentiment)

    # Download stock data
    stock_data = yf.download(company, start=from_date_str, end=today_date_str)

    # Merge with tweet data (assuming you want to analyze by date)
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    stock_data['Date'] = stock_data.index.date
    merged_df = pd.merge(df, stock_data[['Date', 'Close']], on='Date', how='left')

    # Get the current datetime
    current_datetime = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Save the final dataset
    merged_df.to_csv(f'data/{company}/sentiment_with_stock_{current_datetime}.csv', index=False)
