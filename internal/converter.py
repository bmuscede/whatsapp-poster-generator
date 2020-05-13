# Load all necessary libraries.
import sys
import argparse
import re
from dateutil.parser import parse

from internal.canalysis import GetMessageSentiment
from internal.canalysis import CleanMessage

from emoji import UNICODE_EMOJI

def isEmoji(s):
    return s in UNICODE_EMOJI

def isDate(string, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    try: 
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False

def sanitizeStringForCSV(inputString):
    """
    Remove all emojis and escapes certain characters from an input string.

    :param string: inputString, string to convert
    """
    return "\""+inputString.encode('ascii', 'ignore').decode('ascii').replace("\n",r"\n").replace("\t",r"\t").replace("\"","\"\"")+"\""

def ConvertToTextualCSV(inputPath, outputPath):
    """
    Converts a Flat WhatsApp file to a textual CSV file used
    for semantic analysis.

    :param string: inputPath, path of input flat file
    :param string: outputPath, path to output CSV file
    """
    try:
        waFile = open(inputPath, "r", encoding='utf-8')
    except IOError:
        print("Could not open file "+inputPath+"! Please select a proper file for reading.")
        return False

    try:
        waOut = open(outputPath, "w", encoding='utf-8')
    except IOError:
        print("Could not open output file"+outputPath+" for writing! Please select a proper output file.")
        return False

    contents = waFile.readlines()

    count = 0
    currentPerson = ""
    currentDate = ""
    currentTime = ""
    currentMessage = ""

    # Write the header to the output.
    waOut.write("index,person,date,time,message,goodSentiment,neutralSentiment,badSentiment\n")

    for line in contents:
        # Check if the line is a new message or a previous message.
        split = line.split(' - ', 1)
        if len(split) == 2 and isDate(split[0]):
            # Check if we have a previous conversation.
            if count > 0:
                # Flush the line.
                if currentMessage != "\n" and currentMessage != "<Media omitted>\n":
                    currentMessage = sanitizeStringForCSV(currentMessage)
                    currentSentiment = GetMessageSentiment(currentMessage)

                    goodSentiment = 0
                    badSentiment = 0
                    neutralSentiment = 0
                    if currentSentiment > 0:
                        goodSentiment = 1
                    elif currentSentiment < 0:
                        badSentiment = 1
                    else:
                        neutralSentiment = 1

                    waOut.write(str(count)+","+currentPerson+","+currentDate+","+currentTime+","+currentMessage+","+str(goodSentiment)+","+str(neutralSentiment)+","+str(badSentiment)+"\n")

            # We have a new conversation.
            split = line.split(': ', 1)
            if len(split) == 1:
                # This likely isn't a valid line.
                continue

            headerSplit = split[0].split(' - ', 1)
            dateSplit = headerSplit[0].split(', ', 1)

            # Populate the proper fields.
            count += 1
            currentPerson = headerSplit[1]
            currentDate = dateSplit[0]
            currentTime = dateSplit[1]
            currentMessage = split[1]
        else:
            currentMessage += line

    # Do one final flush.
    if count != 0 and currentMessage != "\n" and currentMessage != "<Media omitted>\n":
        currentMessage = sanitizeStringForCSV(currentMessage)

        currentSentiment = GetMessageSentiment(currentMessage)
        goodSentiment = 0
        badSentiment = 0
        neutralSentiment = 0
        if currentSentiment > 0:
            goodSentiment = 1
        elif currentSentiment < 0:
            badSentiment = 1
        else:
            neutralSentiment = 1
        
        waOut.write(str(count)+","+currentPerson+","+currentDate+","+currentTime+","+currentMessage+","+str(goodSentiment)+","+str(neutralSentiment)+","+str(badSentiment)+"\n")

    # Close for reading/writing.
    waOut.close()
    waFile.close()

    return True

def GenerateEmojiCSVFromDF(df, outputPath):
    try:
        waOut = open(outputPath, "w", encoding='utf-16')
    except IOError:
        print("Could not open output file"+outputPath+" for writing! Please select a proper output file.")
        return False

    # Generate contents.
    allText = ""
    for curMessage in df.message:
        allText += curMessage

    # Write the header to the output.
    waOut.write("emoji\tfrequency\n")

    emojiMap = {}

    # Iterate and find the emojis.
    for c in allText:
        if isEmoji(c):
            if c in emojiMap:
                emojiMap[c] += 1
            else:
                emojiMap[c] = 1

    # Sort map by incidence number.
    emojiMap = {k: v for k, v in sorted(emojiMap.items(), key=lambda item: item[1])}

    # Iterate through our emoji map and write out.
    for emojiItem in emojiMap:
        waOut.write(emojiItem + "\t" + str(emojiMap[emojiItem]) + "\n")

    # Close for writing.
    waOut.close()
    return True

def ConvertToEmojiCSV(inputPath, outputPath):
    try:
        waFile = open(inputPath, "r", encoding='utf-8')
    except IOError:
        print("Could not open file "+inputPath+"! Please select a proper file for reading.")
        return False

    try:
        waOut = open(outputPath, "w", encoding='utf-16')
    except IOError:
        print("Could not open output file"+outputPath+" for writing! Please select a proper output file.")
        return False

    contents = waFile.readlines()

    # Write the header to the output.
    waOut.write("emoji\tfrequency\n")

    emojiMap = {}
    for line in contents:
        message = ""

        # Check if the line is a new message or a previous message.
        split = line.split(' - ', 1)
        if len(split) == 2 and isDate(split[0]):
            # We have a new line.
            split = line.split(': ', 1)
            if len(split) == 1:
                continue
            message = split[1]
        else:
            message = line

        # Iterate and find the emojis.
        for c in message:
            if isEmoji(c):
                if c in emojiMap:
                    emojiMap[c] += 1
                else:
                    emojiMap[c] = 1
    
    # Sort map by incidence number.
    emojiMap={k: v for k, v in sorted(emojiMap.items(), key=lambda item: item[1])}

    # Iterate through our emoji map and write out.
    for emojiItem in emojiMap:
        waOut.write(emojiItem + "\t" + str(emojiMap[emojiItem]) + "\n")
    
    # Close for reading/writing.
    waOut.close()
    waFile.close()

    return True