# Load specific libraries.
import argparse
import sys
import os
from os import path
import locale
from dateutil.relativedelta import relativedelta
from datetime import datetime

from internal.converter import ConvertToTextualCSV
from internal.converter import ConvertToEmojiCSV

from internal.pdfgen import ConvertHTMLToPDF
from internal.pdfgen import PrepareHTML

from internal.wordcloud import GenerateWordCloud
from internal.wordcloud import GenerateEmojiWordCloud
from internal.canalysis import GenerateTextingFrequency
from internal.canalysis import GenerateMessageProportion
from internal.canalysis import GenerateMessageSentimateProportion
from internal.canalysis import GenerateSentimentFrequency
import pandas as pd

locale.setlocale(locale.LC_ALL, 'en_US.utf8')

def CreateValueDictionary(df):
    valueDict = {}

    # First, get the two names.
    count = 1
    for name in df.person.unique():
        strippedName = name.replace(" ", "")
        name = name.split(' ', 1)[0]

        valueDict['Name' + str(count)] = name
        valueDict['FullName' + str(count)] = strippedName

        count += 1

    # Get the number of messages.
    numMessages = df.shape[0]
    valueDict['Messages'] = str(f'{numMessages:n}')

    # Get the number of years the messages take place over.
    dateFormat = '%Y-%m-%d'
    minDate = datetime.strptime(df['date'].min(), dateFormat)
    maxDate = datetime.strptime(df['date'].max(), dateFormat)
    years = relativedelta(maxDate, minDate).years
    months = relativedelta(maxDate, minDate).months
    if months >= 5:
        years += 1
    valueDict['Years'] = str(years)

    # Get the number of years the chat is.
    return valueDict

# Set up our argument parser to handle the user 
parser = argparse.ArgumentParser(description='Converts a flat WhatsApp file into a poster used to express interesting information about messages.')
parser.add_argument('-i', '--input', dest='input', help='input CSV file of WhatsApp conversation', required=True)
parser.add_argument('-o', '--output', dest='output', help='output PDF of poster showing WhatsApp stats', required=True)
parser.add_argument('-t', '--temp', dest="temp", help='intermediate folder used to store images and CSV files creatd during analysis', default="temp-output")

# Parse the arguments.
args = parser.parse_args()

# Check if the temp directory exists.
if path.exists(args.temp) is not True:
    try:
        os.mkdir(args.temp)
    except OSError:
        print("Error: Could not create directory for temporary files.", file=sys.stderr)
        exit(1)

print("----------------------------------------")
print("WhatsApp Poster/Conversation Analyzer\n")
print("By: Bryan Muscedere")
print("----------------------------------------")

print("--1) Running Load Tasks--")

# Convert to a textual file.
print("Converting file " + args.input + " to a CSV file...")
status = ConvertToTextualCSV(args.input, args.temp + "/textual.csv")
if not status:
    print("Failure processing file! Please try again.", file=sys.stderr)
    exit(2)
print("Converting file " + args.input + " to an emoji-based CSV file...")
status = ConvertToEmojiCSV(args.input, args.temp + "/emoji.csv")
if not status:
    print("Failure processing file! Please try again.", file=sys.stderr)
    exit(2)
print()

# Next, create a dataset for reading.
df = pd.read_csv(args.temp + "/textual.csv", index_col=0, encoding='utf-8')
print("There are {} messages in the chat!".format(df.shape[0]))
print("Found {} people in this chat including {}...".format(len(df.person.unique()),
                                                                ", ".join(df.person.unique()[0:2])))
print()
print("--2) Running Analysis Tasks--")

# Generate the word cloud.
print("Creating a word cloud for " + str(len(df.person.unique())) + " people...")
status = GenerateWordCloud(df, args.temp)
if not status:
    print("Failure generating word cloud! Please try again.", file=sys.stderr)
    exit(2)
status = GenerateEmojiWordCloud(args.temp + "/emoji.csv", args.temp)
if not status:
    print("Failure generating emoji-based word cloud! Please try again.", file=sys.stderr)
    exit(2)

# Do text time analysis.
print("Determining frequency of messages sent on an hourly basis...")
status = GenerateTextingFrequency(df, args.temp)
if not status:
    print("Failure generating text frequency! Please try again.", file=sys.stderr)
    exit(2)

# Do sentiment analysis.
print("Determining sentiment of messages sent at different hours...")
status = GenerateSentimentFrequency(df, args.temp)
if not status:
    print("Failure generating sentiment frequency! Please try again.", file=sys.stderr)
    exit(2)

# Run other misc statistics.
print("Determining other simple statistics...")
status = GenerateMessageProportion(df, args.temp)
status &= GenerateMessageSentimateProportion(df, args.temp)
if not status:
    print("Failure generating additional statistics! Please try again.", file=sys.stderr)
    exit(2)

print()
print("--3) Running PDF Generation Tasks--")

print("Generating PDF of poster with semantic analysis...")
print()
valueDict = CreateValueDictionary(df)
status = PrepareHTML("Template1", valueDict, args.temp)
if not status:
    print("Failure creating template for poster. Please check the poster template exists.", file=sys.stderr)
ConvertHTMLToPDF(args.output)

print("All tasks completed successfully. See "+args.output+" for the generated PDF and "+args.temp+" for temp artifacts created!")
print("Goodbye!")