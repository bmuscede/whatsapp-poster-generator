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
from internal.converter import GenerateEmojiCSVByDate

from internal.pdfgen import ConvertHTMLToPDF
from internal.pdfgen import PrepareHTML

from internal.wordcloud import GenerateWordCloud
from internal.wordcloud import GenerateEmojiWordCloud
from internal.canalysis import GenerateTextingFrequency
from internal.canalysis import GenerateMessageSentimateProportion
from internal.canalysis import GenerateWordUseFrequency
import pandas as pd
import matplotlib.pyplot as plt
import warnings

# Perform inital setup.
locale.setlocale(locale.LC_ALL, 'en_US.utf8')
pd.options.mode.chained_assignment = None
params = {"ytick.color" : "w",
          "xtick.color" : "w",
          "axes.labelcolor" : "w",
          "axes.edgecolor" : "w"}
plt.rcParams.update(params)
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

##########################################################################################################

def GetNextBest(df, date, back):
    dateFormat = '%Y-%m-%d'
    minDate = datetime.strptime(df['date'].min(), dateFormat)
    maxDate = datetime.strptime(df['date'].max(), dateFormat)

    noGoodDate = True
    while noGoodDate:
        # First, check if we've surpassed the limits.
        if date < minDate:
            date = minDate
            noGoodDate = False
            continue
        elif date > maxDate:
            date = maxDate
            noGoodDate = False
            continue

        # Next, look and see if we have data for the current date.
        dateStr = date.strftime(dateFormat)
        if df.date.str.contains(dateStr).any():
            noGoodDate = False
            continue

        # Check if we're processing a back or forward date.
        if back:
            date = date - relativedelta(days=1)
        else:
            date = date + relativedelta(days=1)

    return date

def CreateValueDictionary(df, masterDF=None):
    if masterDF is None:
        masterDF = df

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
    minDate = datetime.strptime(masterDF['date'].min(), dateFormat)
    maxDate = datetime.strptime(masterDF['date'].max(), dateFormat)
    years = relativedelta(maxDate, minDate).years
    months = relativedelta(maxDate, minDate).months
    if months >= 5:
        years += 1
    valueDict['Years'] = str(years)

    # State the maximum current date.
    valueDict['Date'] = df['date'].max()
    curDate = maxDate

    # Print the associated back URLs.
    backDay = GetNextBest(masterDF, curDate - relativedelta(days=1), True)
    backMonth = GetNextBest(masterDF, curDate - relativedelta(months=1), True)
    backYear = GetNextBest(masterDF, curDate - relativedelta(years=1), True)
    valueDict['DayBack'] = backDay.strftime(dateFormat)
    valueDict['MonthBack'] = backMonth.strftime(dateFormat)
    valueDict['YearBack'] = backYear.strftime(dateFormat)

    # Print the associated forward URLs.
    forwardDay = GetNextBest(masterDF, curDate + relativedelta(days=1), False)
    forwardMonth = GetNextBest(masterDF, curDate + relativedelta(months=1), False)
    forwardYear = GetNextBest(masterDF, curDate + relativedelta(years=1), False)
    valueDict['DayForward'] = forwardDay.strftime(dateFormat)
    valueDict['MonthForward'] = forwardMonth.strftime(dateFormat)
    valueDict['YearForward'] = forwardYear.strftime(dateFormat)

    # Get the number of years the chat is.
    return valueDict

def DoAnalysis(args, df, verbose = True):
    if verbose:
        print()
        print("--2) Running Analysis Tasks--")

    # Generate the word cloud.
    if verbose:
        print("Creating wordclouds for " + str(len(df.person.unique())) + " people and for emojis...")
    status = GenerateWordCloud(df, args.temp)
    if not status:
        print("Failure generating word cloud! Please try again.", file=sys.stderr)
        exit(2)
    status = GenerateEmojiWordCloud(args.temp + "/emoji.csv", args.temp)
    if not status:
        print("Failure generating emoji-based word cloud! Please try again.", file=sys.stderr)
        exit(2)

    if verbose:
        print("Generating the number of times the most common words are used...")
    GenerateWordUseFrequency(df, args.temp)
    if not status:
        print("Failure generating word use graph! Please try again.", file=sys.stderr)
        exit(2)

    # Do text time analysis.
    if verbose:
        print("Determining frequency of messages sent on an hourly basis...")
    status = GenerateTextingFrequency(df, args.temp)
    if not status:
        print("Failure generating text frequency! Please try again.", file=sys.stderr)
        exit(2)

    # Run other misc statistics.
    if verbose:
        print("Determining the sentiment breakdown...")
    status = GenerateMessageSentimateProportion(df, args.temp)
    if not status:
        print("Failure generating sentiment breakdown! Please try again.", file=sys.stderr)
        exit(2)

    # Close all generated figures.
    plt.close('all')

def DoOutput(args, dataframe, verbose = True, masterDF = None):
    if verbose:
        print()
        print("--3) Running PDF Generation Tasks--")

    if verbose:
        print("Generating PDF of poster with semantic analysis...")
        print()
    valueDict = CreateValueDictionary(dataframe, masterDF)
    status = PrepareHTML(args.template, valueDict, args.temp)
    if not status:
        print("Failure creating template for poster. Please check the poster template exists.", file=sys.stderr)
    ConvertHTMLToPDF(args.temp, args.output)

##########################################################################################################

# Set up our argument parser to handle the user 
parser = argparse.ArgumentParser(description='Converts a flat WhatsApp file into a poster used to express interesting information about messages.')
parser.add_argument('-i', '--input', dest='input', help='input CSV file of WhatsApp conversation', required=True)
parser.add_argument('-o', '--output', dest='output', help='output PDF filename or existing directory (if range) showing WhatsApp stats', required=True)
parser.add_argument('-t', '--temp', dest="temp", help='intermediate folder used to store images and CSV files creatd during analysis', default="temp-output")
parser.add_argument('-r', '--range', dest="range", help='generate multiple figures over a range')
parser.add_argument('-a', '--alias', dest='alias', help='alias for name in the form of old-name:new-name', nargs='*')
parser.add_argument('-e', '--template', dest='template', help='the name of the template in the templates folder to use', default='Template1')

# Parse the arguments.
args = parser.parse_args()

# Check if the temp directory exists.
if path.exists(args.temp) is not True:
    try:
        os.mkdir(args.temp)
    except OSError:
        print("Error: Could not create directory for temporary files.", file=sys.stderr)
        exit(1)

# Next, checks if we are doing range calculation.
# Also checks if the output is valid.
if args.range is not None and len(args.range):
    if args.range != 'year' and args.range != 'month' and args.range != 'day':
        print("Error: When using range either specify \"year\", \"month\", or \"day\".", file=sys.stderr)
        exit(1)
    if not os.path.isdir(args.output):
        print("Error: When in range mode, you must select an output directory that exists!", file=sys.stderr)
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

# Only do the emoji conversion if we aren't doing range analysis.
if args.range is None:
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

# Note the aliases and change the dataframe.
if args.alias is not None:
    for person in df.person.unique():
        for alias in args.alias:
            aSplit = alias.split(':')
            if aSplit[0] == person:
                print("Changing " + aSplit[0] + " to " + aSplit[1] + " in the final poster...")
                df['person'] = df['person'].replace(aSplit[0], aSplit[1])

# Check if we're doing a range calculation.
if args.range is not None and len(args.range):
    print()
    print("--2) Running Bulk Output Tasks--")

    print("Output will be created for each " + args.range + "! This may take a while...")
    masterTemp = args.temp
    masterOutput = args.output

    # Get the lowest date.
    dateFormat = '%Y-%m-%d'
    minDate = datetime.strptime(df['date'].min(), dateFormat)
    maxDate = datetime.strptime(df['date'].max(), dateFormat)
    curDate = minDate

    # Loop until we're beyond the current date.
    curPos = 0
    oldRows = 0
    while curDate <= maxDate:
        # Generate the dataframe.
        if args.range == 'month':
            curDate = curDate + relativedelta(months=1)
        elif args.range == 'year':
            curDate = curDate + relativedelta(years=1)
        curDF = df[df['date'] <= curDate.strftime(dateFormat)]

        curDateStr = curDate.strftime(dateFormat)

        # Ensure we have different data.
        curRows = len(curDF.index)
        if curRows == oldRows:
            if args.range == 'day':
                curDate = curDate + relativedelta(days=1)
            continue
        oldRows = curRows

        args.temp = masterTemp + "/" + curDateStr
        if path.exists(args.temp) is not True:
            try:
                os.mkdir(args.temp)
            except OSError:
                print("Error: Could not create directory for temporary files.", file=sys.stderr)
                exit(1)

        # Last do the analysis.
        print( "Analysis #" + str(curPos + 1) + ": Up to date " + curDate.strftime(dateFormat) + "...")
        GenerateEmojiCSVByDate(args.input, args.temp + "/emoji.csv", curDate)
        DoAnalysis(args, curDF, False)

        # Last, do the PDF generation.
        args.output = masterOutput + "/" + curDateStr + ".pdf"
        DoOutput(args, curDF, False, df)

        # If we're doing days now, we increment.
        curPos += 1
        if args.range == 'day':
            curDate = curDate + relativedelta(days=1)

    args.temp = masterTemp
    args.output = masterOutput
else:
    # Simply do a basic run of the program.
    DoAnalysis(args, df, True)
    DoOutput(args, df, True)

print("All tasks completed successfully. See "+args.output+" for the generated PDF and "+args.temp+" for temp artifacts created!")
print("Goodbye!")