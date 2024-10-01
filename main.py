from src.scrape_tweets import scrape_and_analyze_stock_tweet_sentiment
from src.scrape_reddit import scrape_and_analyze_stock_sentiment
from src.clean_data import round_column_values
# scrape_and_analyze_stock_tweet_sentiment(
#     ticker='MSFT',
#     company='Microsoft',
#     tweet_count=1000)

# scrape_and_analyze_stock_sentiment(
#     ticker='MSFT',
#     company='Microsoft',
#     post_count=100,
#     comment_count=20)

round_column_values('data/reddit_sentiment_MSFT_2024-09-30_21-42-45.csv', 'Sentiment')