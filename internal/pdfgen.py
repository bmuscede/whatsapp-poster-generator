from weasyprint import HTML

import os
import sys
import subprocess
import json
from os import path
from distutils.dir_util import copy_tree

templateLocation = "internal/templates/"
templateJSON = templateLocation + "templates.json"
outputName = "index.html"

# Headless chrome arguments.
chromeArgs = (
    '{chrome_exec}',
    '--headless',
    '--disable-gpu',
    '--no-margins',
    '--print-to-pdf={output_file}',
    '{input_file}'
)

#####################################
# This determnines which PDF generator to use.
# 0: Weasyprint
# 1: Chrome (Supported by Linux only)
PDF_ENGINE=0
#####################################

def findExecutable(executable, path=None):
    """Find if 'executable' can be run. Looks for it in 'path'
    (string that lists directories separated by 'os.pathsep';
    defaults to os.environ['PATH']). Checks for all executable
    extensions. Returns full path or None if no command is found.
    """
    if path is None:
        path = os.environ['PATH']
    paths = path.split(os.pathsep)
    extlist = ['']
    if os.name == 'os2':
        (base, ext) = os.path.splitext(executable)
        if not ext:
            executable = executable + ".exe"
    elif sys.platform == 'win32':
        pathext = os.environ['PATHEXT'].lower().split(os.pathsep)
        (base, ext) = os.path.splitext(executable)
        if ext.lower() not in pathext:
            extlist = pathext
    for ext in extlist:
        execname = executable + ext
        if os.path.isfile(execname):
            return execname
        else:
            for p in paths:
                f = os.path.join(p, execname)
                if os.path.isfile(f):
                    return f
    else:
        return None

def TranslateTemplateName(templateName):
    # Check for the template.
    if not path.exists(templateJSON):
        return ""
    
    with open(templateJSON, 'r') as file:
        jsonContents = json.load(file)
        for curTemplate in jsonContents['Templates']:
            if curTemplate['Name'] == templateName:
                return curTemplate['Path']

    return ""
    
def ListTemplates(shortList):
    # Check for the template.
    if not path.exists(templateJSON):
        return ""

    posterTemplates = "Poster Templates:\n"
    rangeTemplates = "Range-Based Templates:\n"
    if shortList is True:
        posterTemplates += "\t"
        rangeTemplates += "\t"

    # Build the template list.
    with open(templateJSON, 'r') as file:
        jsonContents = json.load(file)
        for curTemplate in jsonContents['Templates']:
            if shortList is True:
                if curTemplate['Type'] == "Poster":
                    posterTemplates += curTemplate['Name'] + ", "
                elif curTemplate['Type'] == "Range":
                    rangeTemplates += curTemplate['Name'] + ", "
            else:
                curStr = "\t- " + curTemplate['Name'] + ":\n\t\tPath: " + curTemplate['Path'] + "\n\t\tDescription: " + curTemplate['Description'] + "\n"
                if curTemplate['Type'] == "Poster":
                    posterTemplates += curStr
                elif curTemplate['Type'] == "Range":
                    rangeTemplates += curStr
    
    return posterTemplates, rangeTemplates


def PrepareHTML(templateName, values, outputDir):
    # Translate the template name.
    templateFileName = TranslateTemplateName(templateName)
    if templateFileName == "":
        return False

    # Start by taking the selected template and moving it over.
    filename = templateLocation + templateFileName 
    if not path.exists(filename):
        return False

    # Read in the file
    with open(filename, 'r') as file:
        htmlContents = file.read()

    # Do a find and replace for all dictionary values.
    for key, value in values.items():
        htmlContents = htmlContents.replace(":" + key + ":", value)

    # Write the file out again
    with open(outputDir + "/" + outputName, 'w') as file:
        file.write(htmlContents)

    # Copy the image directory.
    copy_tree(templateLocation + "internal-images", outputDir + "/internal-images")
    return True

def ConvertHTMLToPDF(inputDir, outputFileName):
    if PDF_ENGINE == 0:
        # Start by opening the temporary file.
        tempPoster = HTML(filename=inputDir + "/" + outputName)

        # Write the object.
        tempPoster.write_pdf(outputFileName)
    elif PDF_ENGINE == 1:
        # Find the Chrome installation.
        chromeLoc = findExecutable('google-chrome-stable')
        if chromeLoc is None:
            return False

        # Prepare to print the PDF.
        with open(outputFileName, 'w') as outputFile:
            printCommand = ' '.join(chromeArgs).format(
                chrome_exec=chromeLoc,
                input_file=inputDir + "/" + outputName,
                output_file=outputFile.name
            )

            isNotWindows = not sys.platform.startswith('win32')
            try:
                # execute the shell command to generate PDF
                subprocess.run(printCommand, shell=isNotWindows, check=True)
            except subprocess.CalledProcessError:
                return False
    else:
        return False

    return True
