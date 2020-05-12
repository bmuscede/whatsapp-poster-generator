# Load all necessary libraries.
import numpy as np
import pandas as pd

from textblob import TextBlob 
import re 

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from csv import reader, writer

def CleanMessage(message): 
    return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t]) |(\w+:\/\/\S+)", " ", message).replace("\\n", " ").replace("\\t", "").split()) 

def LoadCommonWords():
    # In the current directory. check for a common words file.
    wordList = ['n']

    try:
        wordFile = open('internal/common-words.txt', "r")
    except IOError:
        return wordList

    for line in wordFile:
        line = line.strip()
        if len(line) == 0:
            continue

        wordList.append(line)

    wordFile.close()
    return wordList


def GetMessageSentiment(message):
    # Create TextBlob object of passed message
    message = CleanMessage(message)
    analysis = TextBlob(message) 
    return analysis.sentiment.polarity

def GenerateTextingFrequency(df, outputDirectory):
    df.time = pd.to_datetime(df.time)
    mFreq = df.set_index('time').groupby([pd.Grouper(freq='60Min')]).count()

    # Create the plot.
    plt.figure(figsize=(30,5), frameon=False)
    plt.box(on=False)
    mFreq.sort_values(by="time", ascending=[False])["message"].plot.line(linewidth="7.0")

    # Remove the tick markers.
    ax = plt.gca()
    ax.tick_params(axis='both', length=0)
    ax.set_xlabel('')
    ax.set_ylabel('')

    # Set the major tick here to be invisible.
    xticks = ax.xaxis.get_major_ticks()
    xticks[0].label1.set_visible(False)

    # Set all minor ticks to be large.
    # For some reason, the time other than the first is considered to be minor.
    ax.tick_params(which='minor', length=0)
    for tick in ax.xaxis.get_minor_ticks():
        tick.label1.set_color('white')
        tick.label1.set_fontsize(16)

    # Now remove all but the second highest y axis tick.
    curTick = -1
    yticks = ax.yaxis.get_major_ticks()
    ylabels=ax.get_yticks().tolist()
    for tick in yticks:
        curTick += 1
        if curTick + 3 == len(yticks):
            plt.axhline(y=int(ylabels[curTick]), color='w', linestyle='-', linewidth=3, visible=True)
            tick.label1.set_visible(True)
            tick.label1.set_color('white')
            tick.label1.set_fontsize(16)
            continue
        tick.label1.set_visible(False)

    # Output the diagram.
    plt.tight_layout(pad=0)
    plt.savefig(outputDirectory+"/TextFrequency.png", transparent=True)
    return True

def GenerateMessageProportion(df, outputDirectory):
    persons = df.groupby("person").count()

    plt.figure(figsize=(15,10))
    plt.ylabel("Number of Messages")
    persons.plot.pie(y='message')
    plt.savefig(outputDirectory+"/TextProportions.png")

    return True

def GenerateMessageSentimateProportion(df, outputDirectory):
    goodSentiment = df['goodSentiment'].sum()
    badSentiment = df['badSentiment'].sum()
    neutralSentiment = df['neutralSentiment'].sum()
    total = goodSentiment + badSentiment + neutralSentiment

    # Get percentages.
    goodPercentage = "{:.2f}".format((goodSentiment / total) * 100)
    badPercentage = "{:.2f}".format(badSentiment / total * 100)
    neutralPercentage = "{:.2f}".format((neutralSentiment / total) * 100)

    labelIndex = ['Positive (' + goodPercentage + '%)', 'Negative (' + badPercentage + '%)', 'Neutral (' + neutralPercentage + '%)']
    sentimentDF = pd.DataFrame({'sentiment': [goodSentiment, badSentiment, neutralSentiment]},
                               index=labelIndex)

    # Create the initial pie chart.
    plt.figure(figsize=(20,20), frameon=False)
    ax = sentimentDF.plot.pie(y='sentiment', fontsize=0, wedgeprops={"edgecolor":"k", 'linewidth': 1.25, 'linestyle': 'solid', 'antialiased': True})

    # Configure the legend.
    patches, labels = ax.get_legend_handles_labels()
    ax.legend(patches, labels, loc=10)
    ax.set_ylabel('')

    # Create a donut.
    plt.setp(ax.patches, width=0.25)
    ax.set_aspect("equal")

    # Output the diagram.
    plt.tight_layout(pad=0)
    plt.savefig(outputDirectory+"/SentimentProportions.png", transparent=True)
    return True

def GenerateSentimentFrequency(df, outputDirectory):
    # Drop all but the sentiment.
    df = df.drop('date', 1).drop('person', 1).drop('message', 1)
    df.time = pd.to_datetime(df.time)
    mFreq = df.set_index('time').groupby([pd.Grouper(freq='60Min')]).agg('sum')

    # Create the plot.
    plt.figure(figsize=(15,10))
    mFreq.sort_values(by="time", ascending=[False]).plot.bar()
    plt.xticks(rotation=50)

    plt.xlabel("Time")
    plt.ylabel("Number of Messages")
    plt.savefig(outputDirectory+"/SentimentFrequency.png")

    return True

def GenerateWordUseFrequency(df, outputDirectory):
    commonWords = LoadCommonWords()

    # First, tokenize by line.
    df['words'] = df.message.str.strip().str.split('[\W_]+')

    # Now create a new data frame with persons and words.
    rows = list()
    for row in df[['person', 'words']].iterrows():
        r = row[1]
        for word in r.words:
            rows.append((r.person, word))
    words = pd.DataFrame(rows, columns=['person', 'word'])
    words = words[words.word.str.len() > 0]
    words['word'] = words.word.str.lower()

    # Now count the words per person.
    counts = words.groupby('person') \
        .word.value_counts() \
        .to_frame() \
        .rename(columns={'word': 'count'})

    # Remove the counts for common words. Get a total count.
    counts = counts.drop(index=commonWords, level=1)
    totalCount = counts.groupby(level=1).sum().nlargest(30, columns='count')

    # Generate the person data.
    names = []
    data = []

    # Generate data for our words.
    topWords = list(totalCount.index.values)
    for person in counts.groupby('person'):
        names.append(person[0])
        curData = list()

        pD = person[1].reset_index(level=0, drop=True)
        for top in topWords:
            item = pD.loc[top]
            curData.append(item['count'])

        data.append(curData)

    # Generate the figure.
    plt.figure(figsize=(20,40))
    wordDf = pd.DataFrame({names[0]: data[0], names[1]: data[1]}, index=topWords)
    wordDf.plot.barh()

    # Output the diagram.
    plt.tight_layout(pad=0)
    plt.savefig(outputDirectory+"/WordFrequency.png")
    return True