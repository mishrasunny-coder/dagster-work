# import json
# import os
import dagster
import requests
import pandas as pd
from dagster import get_dagster_logger, AssetExecutionContext, MetadataValue
import base64
from io import BytesIO
from typing import Dict, List

import matplotlib.pyplot as plt


@dagster.asset
def topstories_ids() -> List:
    newstories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    top_new_story_ids = requests.get(newstories_url).json()[:100]
    return (
        top_new_story_ids
    )

    # os.makedirs("data", exist_ok=True)
    # with open("data/topstory_ids.json", "w") as f:
    #     json.dump(top_new_story_ids, f)


# @dagster.asset(deps=[topstories_ids])
@dagster.asset
def topstories(context: AssetExecutionContext,
               topstories_ids: List) -> pd.DataFrame:
    logger = get_dagster_logger()

    # with open("data/topstory_ids.json", "r") as f:
    #     topstory_ids = json.load(f)

    results = []
    for item_id in topstories_ids:
        item = requests.get(
            f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        ).json()
        results.append(item)

        if len(results) % 20 == 0:
            logger.info(f"Got {len(results)} items so far.")

    df = pd.DataFrame(results)
    # df.to_csv("data/topstories.csv")

    context.add_output_metadata(
        metadata={
            "num_records": len(df),  # Metadata can be any key-value pair
            "preview": MetadataValue.md(df.head().to_markdown()),
            # The `MetadataValue` class has useful static methods to build Metadata
        }
    )
    return df

# @dagster.asset(deps=[topstories])
@dagster.asset
def most_frequent_words(context: AssetExecutionContext,
                        topstories: pd.DataFrame) -> Dict:
    stopwords = ["a", "the", "an", "of", "to", "in", "for", "and", "with", "on", "is"]

    # topstories = pd.read_csv("data/topstories.csv")

    # loop through the titles and count the frequency of each word
    word_counts = {}
    for raw_title in topstories["title"]:
        title = raw_title.lower()
        for word in title.split():
            cleaned_word = word.strip(".,-!?:;()[]'\"-")
            if cleaned_word not in stopwords and len(cleaned_word) > 0:
                word_counts[cleaned_word] = word_counts.get(cleaned_word, 0) + 1

    # Get the top 25 most frequent words
    top_words = {
        pair[0]: pair[1]
        for pair in sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:25]
    }

    # Make a bar chart of the top 25 words
    plt.figure(figsize=(10, 6))
    plt.bar(top_words.keys(), top_words.values())
    plt.xticks(rotation=45, ha="right")
    plt.title("Top 25 Words in Hacker News Titles")
    plt.tight_layout()

    # Convert the image to a saveable format
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    image_data = base64.b64encode(buffer.getvalue())

    # Convert the image to Markdown to preview it within Dagster
    md_content = f"![img](data:image/png;base64,{image_data.decode()})"

    # with open("data/most_frequent_words.json", "w") as f:
    #     json.dump(top_words, f)

    # Attach the Markdown content as metadata to the asset
    context.add_output_metadata(metadata={"plot": MetadataValue.md(md_content)})

    return top_words

