from weasyprint import HTML
from os import path
from distutils.dir_util import copy_tree

templateLocation = "internal/templates/"
tempLocation = templateLocation + "Temp.html"

def PrepareHTML(templateName, values, imageDir):
    # Start by taking the selected template and moving it over.
    filename = templateLocation + templateName + ".html"
    if not path.exists(filename):
        return False

    # Read in the file
    with open(filename, 'r') as file:
        htmlContents = file.read()

    # Do a find and replace for all dictionary values.
    for key, value in values.items():
        htmlContents = htmlContents.replace(":" + key + ":", value)

    # Write the file out again
    with open(tempLocation, 'w') as file:
        file.write(htmlContents)

    # Copy the image directory.
    copy_tree(imageDir, templateLocation + "images")
    return True

def ConvertHTMLToPDF(outputFileName):
    # Start by opening the temporary file.
    tempPoster = HTML(filename=tempLocation)

    # Write the object.
    tempPoster.write_pdf(outputFileName)