import csv

from flask import Flask, jsonify, redirect, render_template, request
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError

# Configure application
application = Flask(__name__)

# Reload templates when they are changed
application.config["TEMPLATES_AUTO_RELOAD"] = True

# Disable caching
@application.after_request
def after_request(response):
    """Disable caching"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@application.route("/search", methods=["GET"])
def search():
    """Search and return necessary fields from HTS csv"""
    parent = request.args.get("number").replace(".", "")
    results = []

    # If no input, automatically search by section
    if len(parent) == 0:
        with open("HTS_Sections.csv", newline = '', encoding = "latin-1") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                results.append('<button type="button" class="list-group-item list-group-item-action"'
                                + 'onClick="sectionSearch(' + "'" + row["hts_number"] + "'" + ')"' + '>'
                                + row["hts_number"] + " - " + row["Parsed Description"] + '</button>')

    # If not complete code, search by chapter
    elif len(parent) < 2:
        with open("HTS_Chapters.csv", newline = '', encoding = "latin-1") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row["hts_number"][:len(parent)] == parent:
                    results.append(constructButton(row))

    # Otherwise search the master code sheet
    else:
        with open("HTS_Data.csv", newline = '', encoding = "latin-1") as csvfile:
            reader = csv.DictReader(csvfile)

            if len(parent) < 4:
                for row in reader:
                    if row["Indent"] == "0" and parent == str(row["hts_number"])[:len(parent)]:
                        results.append(constructButton(row))
            else:
                # Detect if code is complete (minus parents)
                if len(parent) % 2 == 0:
                    # If so, find all whose direct parent is code
                    for row in reader:
                        if row["Direct Parent"].replace(".", "") == parent:
                            # Account only for non-blank codes
                            if row["hts_number"] != "":
                                results.append(constructButton(row))
                # If not, return all codes whose direct parent is 1 digit longer using hts_number
                else:
                    for row in reader:
                        # First check if direct parent starts the same
                        tempCode = row["hts_number"].replace(".", "")
                        if parent == tempCode[:len(parent)]:
                            # Then check if direct parent is correct length
                            if len(tempCode) == len(parent) + 1:
                                # Account only for non-blank codes
                                if row["hts_number"] != "":
                                    results.append(constructButton(row))
    return jsonify(results)

@application.route("/sectionSearch", methods=["GET"])
def sectionSearch():
    """Search and return necessary fields from HTS csv when searched through section"""
    parent = request.args.get("number")
    results = []
    with open("HTS_Chapters.csv", newline = '', encoding = "latin-1") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row["Section"] == parent:
                    results.append(constructButton(row))
    return jsonify(results)

@application.route("/describer", methods=["GET"])
def describer():
    """Constructs information dictionary based off of a searched code"""
    descriptions = []

    # Recursive describer function
    def describe(code):
        if len(code) == 2:
            with open("HTS_Chapters.csv", newline = '', encoding = "latin-1") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if code == row["hts_number"]:
                        descriptions.append(dict(description = "Chapter " + row["hts_number"] + ": "
                                                 + row["Parsed Description"],
                                                 rate = "", special_rate = ""))
                        descriptions.append(dict(description = "Section " + row["Section"] + ": "
                                                 + row["Section Description"],
                                                 rate = "", special_rate = ""))
                        break
        if len(code) > 3:
            with open("HTS_Data.csv", newline = '', encoding = "latin-1") as csvfile:
                reader = csv.DictReader(csvfile)

                # Base case is 4-digit code (highest up parent)
                if len(code) == 4:
                    for row in reader:
                        if code == str(row["hts_number"].replace(".", "")):
                            descriptions.append(dict(description = row["hts_number"] + ": " + row["Parsed Description"],
                                                     rate = row["General Rate of Duty"], special_rate = row["Special Rate of Duty"]))
                            describe(code[:-2])
                            break
                else:
                    # Detect if code is complete (minus parents)
                    if len(code) % 2 == 0:
                        for row in reader:
                            if code == str(row["hts_number"].replace(".", "")):
                                descriptions.append(dict(description = row["hts_number"] + ": " + row["Parsed Description"],
                                                         rate = row["General Rate of Duty"], special_rate = row["Special Rate of Duty"]))
                                break
                        describe(code[:-2])
                    else:
                        describe(code[:-1])

    describe(request.args.get("number").replace(".", ""))

    return jsonify(descriptions)

def constructButton(row):
    """Constructs HTML button to be sent to frontend"""
    return ('<button type="button" class="list-group-item list-group-item-action"'
            + 'onClick="fillText(' + "'" + row["hts_number"] + "'" + ')"' + '>'
            + row["hts_number"] + " - " + row["Parsed Description"] + '</button>')

@application.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")