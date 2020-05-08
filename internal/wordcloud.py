# Load all necessary libraries.
import numpy as np
import pandas as pd
import string
from os import path
from os import getcwd
from PIL import Image
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator

import urllib
import requests

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from internal.converter import CleanMessage

# The maximum emojis in a file.
MAX_EMOJI = 15

def GenerateWordCloud(df, outputDirectory):
    persons = df.groupby("person")
    for curPerson in persons:
        allText = ""
        for curMessage in curPerson[1].message:
            allText += CleanMessage(curMessage)

        strippedName = curPerson[0].replace(" ", "")

        # Get a mask to use.
        mask = np.array(Image.open(requests.get('https://clipartart.com/images/clipart-gold-heart-1.png', stream=True).raw))

        # Create and generate a word cloud image.
        wordcloud = WordCloud(width=400, height=400, mask=mask, background_color=None, mode="RGBA").generate(allText)

        # Display the generated image.
        plt.figure( figsize=(20,20) )
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        plt.tight_layout(pad=0)
        plt.savefig(outputDirectory+"/"+strippedName+"WordCloud.png", transparent=True)

    return True

def GenerateEmojiWordCloud(emjoiCSV, outputDirectory):
    # get data directory (using getcwd() is needed to support running example in generated IPython notebook)
    d = path.dirname(__file__) if "__file__" in locals() else getcwd()

    # Start by taking the emjoi CSV and reading it in.
    try:
        emojiFile = open(emjoiCSV, "r", encoding='utf-16')
    except IOError:
        print("Could not open output file"+emjoiCSV+" for writing! Please select a proper input file.")
        return False

    emojiText = ""
    lineCount = 0
    contents = emojiFile.readlines()
    for line in reversed(contents):
        items = line.split('\t')
        if len(items) != 2:
            continue

        occ = 0
        try:
            occ = int(items[1])
        except ValueError:
            continue

        for i in range(occ):
            emojiText += items[0]

        # Last, if we hit he max line count, we're done.
        lineCount += 1
        if lineCount == MAX_EMOJI:
            break

    # Generate an emoji regex so the wordcloud can detect.
    emoji = r"(?:[^\s])(?<![\w{ascii_printable}])".format(ascii_printable=string.printable)

    # With the emojis in place, create the word cloud.
    font = path.join(d, 'fonts', 'Symbola', 'Symbola.ttf')
    wordcloud = WordCloud(width=400, height=400, background_color=None, mode="RGBA", font_path=font, regexp=emoji, collocations=False).generate(emojiText)

    # Display the generated image.
    plt.figure(figsize=(20, 20))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.savefig(outputDirectory + "/EmojiWordCloud.png", transparent=True)
    return True
