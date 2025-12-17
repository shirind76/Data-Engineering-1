"""
DE1_HW_AWS_Script.py

Full AWS pipeline for DE1 Homework:
- Scrape text articles
- Translate German article
- Analyze sentiment using AWS Comprehend
- Transcribe YouTube audio
- Save transcripts, sentiment results, and AWS costs
- Upload outputs to S3
"""

# -----------------------------
# 1. IMPORTS
# -----------------------------
import boto3
import csv
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os



# -----------------------------
# 2. LOAD AWS CREDENTIALS
# -----------------------------
with open("accessKeys.csv") as f:
    reader = csv.DictReader(f)
    keys = list(reader)[0]

AWS_ACCESS_KEY = keys["\ufeffAccess key ID"] if "\ufeffAccess key ID" in keys else keys["Access key ID"]
AWS_SECRET_KEY = keys["Secret access key"]

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name="eu-west-1"
)

s3 = session.client("s3")
translate = session.client("translate")
comprehend = session.client("comprehend")
transcribe = session.client("transcribe")

# -----------------------------
# 3. STATIC AWS PRICING
# -----------------------------
PRICE_TRANSLATE_PER_CHAR = 0.000015
PRICE_COMPREHEND_PER_CALL = 0.0001
PRICE_TRANSCRIBE_PER_SEC = 0.0004

AWS_USAGE = {
    "translate_chars": 0,
    "comprehend_calls": 0,
    "transcribe_seconds": 0
}

# -----------------------------
# 4. DATA SOURCES
# -----------------------------
ARTICLES = {
    "cnn": "https://edition.cnn.com/2025/12/10/economy/fed-december-rate-decision",
    "cnbc": "https://www.cnbc.com/2025/12/10/fed-interest-rate-decision-december-2025-.html",
    "reuters": "https://www.reuters.com/business/view-divided-fed-cuts-rates-expected-sees-only-one-reduction-2026-2025-12-10/",
    "bbc": "https://www.bbc.com/news/articles/cx257k3n2g1o",
    "german": "https://www.derstandard.at/story/3000000300108/us-notenbank-fed-senkt-leitzins-zum-dritten-mal-heuer"
}

YOUTUBE_VIDEOS = {
    "fox_news": "audio/fox.mp3",
    "cnn_news": "audio/cnn.mp3",
    "cnbc_fast_money": "audio/cnbc1.mp3",
    "cnbc_news": "audio/cnbc2.mp3",
    "reuters_powell": "audio/reuters.mp3"
}

bucket_name = "2404422-news-sentiment"

# -----------------------------
# 5. SCRAPE FUNCTION
# -----------------------------
def scrape_article(url):
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    return " ".join(p.get_text(strip=True) for p in soup.find_all("p"))

#-----------------------------
# 6. ARTICLE 
# -----------------------------
results = []

# Ensure txt output folder exists
os.makedirs("output/txt", exist_ok=True)

for name, url in ARTICLES.items():
    print(f"\nScraping article: {name}")
    raw_text = scrape_article(url)

    # Translate German article
    if name == "german":
        print("Translating German → English...")
        response = translate.translate_text(
            Text=raw_text[:4500],
            SourceLanguageCode="auto",
            TargetLanguageCode="en"
        )
        final_text = response["TranslatedText"]
        AWS_USAGE["translate_chars"] += len(raw_text)
    else:
        final_text = raw_text

    # Save article text to txt
    article_txt_path = f"output/txt/{name}_article.txt"
    with open(article_txt_path, "w", encoding="utf-8") as f:
        f.write(final_text)

    # Upload article text to S3
    s3.upload_file(
        article_txt_path,
        bucket_name,
        f"output/txt/{name}_article.txt"
    )

    print("Running sentiment analysis...")
    sentiment = comprehend.detect_sentiment(
        Text=final_text[:4500],
        LanguageCode="en"
    )
    AWS_USAGE["comprehend_calls"] += 1

    scores = sentiment["SentimentScore"]
    results.append({
        "source": name,
        "content_type": "article",
        "sentiment": sentiment["Sentiment"],
        "positive": scores["Positive"],
        "negative": scores["Negative"],
        "neutral": scores["Neutral"],
        "mixed": scores["Mixed"]
    })

# -----------------------------
# 7. TRANSCRIBE FUNCTION
# -----------------------------
def transcribe_audio(s3_uri, job_name):
    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={"MediaFileUri": s3_uri},
        MediaFormat="mp3",
        LanguageCode="en-US"
    )

    while True:
        job = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        status = job["TranscriptionJob"]["TranscriptionJobStatus"]
        if status in ["COMPLETED", "FAILED"]:
            break
        time.sleep(5)

    if status == "FAILED":
        raise RuntimeError("Transcription failed")

    return job["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]

# -----------------------------
# 8. YOUTUBE 
# -----------------------------
for name, filepath in YOUTUBE_VIDEOS.items():
    print(f"\nProcessing YouTube audio: {name}")

    s3.upload_file(
        filepath,
        bucket_name,
        f"audio/{os.path.basename(filepath)}"
    )

    s3_uri = f"s3://{bucket_name}/audio/{os.path.basename(filepath)}"
    job_name = f"transcribe-{name}-{int(time.time())}"

    transcript_url = transcribe_audio(s3_uri, job_name)
    transcript_text = requests.get(transcript_url).json()["results"]["transcripts"][0]["transcript"]

    # Ensure folder exists (safe to repeat)
    os.makedirs("output/txt", exist_ok=True)

    # Save transcript locally
    transcript_path = f"output/txt/{name}_transcript.txt"
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(transcript_text)

    # Upload transcript to S3
    s3.upload_file(
        transcript_path,
        bucket_name,
        f"output/txt/{name}_transcript.txt"
    )

    print("Running sentiment on transcript...")
    sent = comprehend.detect_sentiment(Text=transcript_text[:4500], LanguageCode="en")
    AWS_USAGE["comprehend_calls"] += 1
    AWS_USAGE["transcribe_seconds"] += 180

    scores = sent["SentimentScore"]
    results.append({
        "source": name,
        "content_type": "youtube",
        "sentiment": sent["Sentiment"],
        "positive": scores["Positive"],
        "negative": scores["Negative"],
        "neutral": scores["Neutral"],
        "mixed": scores["Mixed"]
    })


# -----------------------------
# 9. SAVE SENTIMENT RESULTS
# -----------------------------
df = pd.DataFrame(results)
os.makedirs("output/csv", exist_ok=True)

df.to_csv("output/csv/sentiment_results.csv", index=False)

s3.upload_file(
    "output/csv/sentiment_results.csv",
    bucket_name,
    "output/csv/sentiment_results.csv"
)

# -----------------------------
# 10. COST CALCULATION
# -----------------------------
translate_cost = AWS_USAGE["translate_chars"] * PRICE_TRANSLATE_PER_CHAR
comprehend_cost = AWS_USAGE["comprehend_calls"] * PRICE_COMPREHEND_PER_CALL
transcribe_cost = AWS_USAGE["transcribe_seconds"] * PRICE_TRANSCRIBE_PER_SEC
total_cost = translate_cost + comprehend_cost + transcribe_cost

# -----------------------------
# 11. SAVE AWS COST RESULTS
# -----------------------------
cost_rows = [
    {"service": "Amazon Translate", "usage": AWS_USAGE["translate_chars"], "cost_usd": translate_cost},
    {"service": "Amazon Comprehend", "usage": AWS_USAGE["comprehend_calls"], "cost_usd": comprehend_cost},
    {"service": "Amazon Transcribe", "usage": AWS_USAGE["transcribe_seconds"], "cost_usd": transcribe_cost},
    {"service": "TOTAL", "usage": "", "cost_usd": total_cost}
]

df_cost = pd.DataFrame(cost_rows)
df_cost.to_csv("output/csv/aws_costs.csv", index=False)

s3.upload_file(
    "output/csv/aws_costs.csv",
    bucket_name,
    "output/csv/aws_costs.csv"
)

print("\nSentiment Analysis completed successfully.")
print(f"Estimated total AWS cost: ${total_cost:.4f}")
