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

    # Prepare the label.
    plt.xticks(rotation=50, color='white', fontsize=24)
    ax = plt.gca()
    ax.tick_params(axis='both', length=0)
    ax.set_xlabel('')
    ax.set_ylabel('')
    plt.axhline(y=1500, color='w', linestyle='-', linewidth=3, visible=True)
    
    # Remove the first time (since that will be 00:00)
    #xticks = ax.xaxis.get_major_ticks()
    #xticks[0].label1.set_visible(False)
    for tick in ax.get_xticklabels():
        tick.set_color('white')
        tick.set_fontsize(24)

    # Now remove all but the second highest y axis tick.
    curTick=-1
    yticks = ax.yaxis.get_major_ticks()
    for tick in yticks:
        curTick += 1
        if curTick + 3 == len(yticks):
            tick.label1.set_visible(True)
            tick.label1.set_color('white')
            tick.label1.set_fontsize(16)

            continue
        tick.label1.set_visible(False)

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

    sentimentDF = pd.DataFrame({'sentiment': [goodSentiment, badSentiment, neutralSentiment]},
                               index=['Positive', 'Negative', 'Neutral'])

    # Create the initial pie chart.
    plt.figure(figsize=(15,10))
    plt.ylabel("Number of Messages")
    sentimentDF.plot.pie(y='sentiment')

    # Add a circle in the middle to plot.
    centreCircle = plt.Circle((0, 0), 0.75, color='black', fc='white', linewidth=1.25)
    fig = plt.gcf()
    fig.gca().add_artist(centreCircle)

    plt.savefig(outputDirectory+"/SentimentProportions.png")

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