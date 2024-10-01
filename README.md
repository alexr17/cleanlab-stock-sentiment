# Setup
```
pip install -r requirements.txt
```

Quick notes:
- twitter api is blocked now, and snscrape only supports python <= 3.10
- The dataset is pretty bad, because apparently reddit comments on wsb are not good indicators of sentiment, all they do is make jokes!

There's a lot of noise though, and this is probably something cleanlab would be helpful for.

A better approach could be to analyze sentiment in the week prior to an earnings call. Add special sentiment indicators like ("call" or "put"), and build a model to classify either bullish or bearish.
