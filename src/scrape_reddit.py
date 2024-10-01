import os
import time
from datetime import datetime, timedelta
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import yfinance as yf
import praw
from prawcore import ResponseException, TooManyRequests
from dotenv import load_dotenv
load_dotenv()

# Get Reddit API credentials from environment variables
# client_id = os.getenv('REDDIT_CLIENT_ID')
# Reddit API credentials
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)

# Initialize VADER sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

def analyze_sentiment(text):
    """Analyze sentiment of a given text using VADER."""
    score = analyzer.polarity_scores(text)
    return score['compound']

def get_stock_closing_price(ticker: str, date: datetime):
    """Fetch the closest stock closing price to the given date.
    
    If the market is closed on that date, it fetches the previous closing price.
    """
    try:
        # Download stock data for a range of 3 days before the given date to account for weekends/holidays
        start_date = (date - timedelta(days=3)).strftime('%Y-%m-%d')
        end_date = date.strftime('%Y-%m-%d')
        
        stock_data = yf.download(ticker, start=start_date, end=end_date)
        
        # If we have data, find the closest previous available closing price
        if not stock_data.empty:
            # Find the row that is closest to the target date
            closest_price = stock_data.loc[:date.strftime('%Y-%m-%d'), 'Close'].iloc[-1]
            return closest_price
        else:
            return None
    except Exception as e:
        print(f"Error fetching stock data for {ticker} on {date}: {e}")
        return None
    
def fetch_reddit_posts_with_headers(subreddit_name, query, limit=100, retry_delay=1):
    """Fetch Reddit posts and handle rate limits based on Reddit's response headers."""
    subreddit = reddit.subreddit(subreddit_name)
    posts_data = []
    
    try:
        for post in subreddit.search(query, limit=limit, sort="top"):
            posts_data.append(post)
        return posts_data
    
    except TooManyRequests as e:
        # Check for 'Retry-After' or 'X-Ratelimit-Reset' in headers
        if e.response.headers.get('Retry-After'):
            retry_delay = int(e.response.headers['Retry-After'])
        print(f"Rate limit hit. Sleeping for {retry_delay} seconds.")
        time.sleep(retry_delay)
        return fetch_reddit_posts_with_headers(subreddit_name, query, limit, retry_delay)
    
def process_post_comments(post, from_date, comment_count, min_score=10, retry_delay=1):
    """
    Process Reddit posts' comments, ensuring that only comments with
    at least `min_score` (combined upvotes + downvotes) are included.
    Rate limit handling is included.
    """
    try:
        # Get the top upvoted/downvoted comments from the post
        post.comments.replace_more(limit=None)  # Fetch all comments
        comments = post.comments.list()

        # Sort comments by the highest combined upvotes and downvotes (score)
        sorted_comments = sorted(comments, key=lambda c: c.score, reverse=True)
        
        # Filter comments with at least `min_score` (upvotes + downvotes)
        filtered_comments = [comment for comment in sorted_comments 
                                if comment.ups + comment.downs >= min_score]

        # Select the top `comment_count` comments based on interaction
        selected_comments = filtered_comments[:comment_count]

        return selected_comments

    except TooManyRequests as e:
        # Handle rate limit error (HTTP 429)
        if e.response.headers.get('Retry-After'):
            retry_delay = int(e.response.headers['Retry-After'])
        print(f"Rate limit hit. Sleeping for {retry_delay} seconds.")
        time.sleep(retry_delay)
        # Retry the same post after sleeping
        return process_post_comments([post], from_date, comment_count, min_score, retry_delay)

def scrape_and_analyze_stock_sentiment(
    ticker: str,
    company: str,
    subreddit_name: str = "wallstreetbets",
    post_count: int = 50,
    comment_count: int = 20,
    from_date: datetime = datetime(2024, 1, 1)
):
    """Scrape Reddit posts mentioning the ticker/company and analyze sentiment of comments."""
    query = f"{company} OR {ticker}"
    posts_data = []
    
    # Fetch top Reddit posts mentioning the ticker/company from the given subreddit    
    posts = fetch_reddit_posts_with_headers(subreddit_name, query, limit=post_count)
    
    for post in posts:
        post_date = datetime.utcfromtimestamp(post.created_utc)
        if post_date < from_date:
            continue
        
        selected_comments = process_post_comments(post, from_date, comment_count)
        
        for comment in selected_comments:
            # print(comment)
            comment_text = comment.body
            comment_date = datetime.utcfromtimestamp(comment.created_utc)
            sentiment = analyze_sentiment(comment_text)
            comment_upvotes = comment.ups
            comment_downvotes = comment.downs
            post_upvotes = post.ups
            post_downvotes = post.downs
            
            # Fetch stock closing price on the comment date
            closing_price = get_stock_closing_price(ticker, comment_date)
            
            # Append data to the list
            posts_data.append({
                'Comment Text': comment_text,
                'Sentiment': sentiment,
                'Comment Upvotes': comment_upvotes,
                'Comment Downvotes': comment_downvotes,
                'Post Upvotes': post_upvotes,
                'Post Downvotes': post_downvotes,
                'Comment Date': comment_date,
                'Stock Closing Price': closing_price
            })

    # Create a DataFrame from the collected data
    df = pd.DataFrame(posts_data)
    
    # Get current datetime for CSV filename
    current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    
    # Save the final dataset to a CSV file
    filename = f'data/reddit_sentiment_{ticker}_{current_datetime}.csv'
    df.to_csv(filename, index=False)
    
    print(f"Data saved to {filename}")

# Example usage

