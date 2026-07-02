import csv
import difflib
import json
import math
import logging
import os
import sys

import numpy
import pandas as pd
import FreeSimpleGUI as sg

from datetime import date


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def main(input):
    data = pd.read_csv(input, encoding="latin-1",on_bad_lines='warn')
    # Convert the DataFrame to a Dictionary
    data_dict = data.to_dict(orient="records")

    outputfilepath = input.rsplit(".", 1)[0]

    # Opening JSON file
    j = open(resource_path("country_codes.json"))
    f = open(resource_path("tax_rates.json"))
    s = open(resource_path("state_codes.json"))
    c = open(resource_path("can_provinces.json"))
    # returns JSON object as
    # a dictionary
    tax_data = json.load(f)
    country_data = json.load(j)
    state_data = json.load(s)
    prov_data = json.load(c)

    # BOX3b and BOX4B Evaluation
    filename = outputfilepath + "_tax_rate_errors.csv"
    tax_rate_fields = ["BOX13A_RECIPIENT NAME1", "BOX3B_TAX RATE", "BOX4B_TAX RATE", "REASON"]
    rows=[]
    for x in data_dict:
        match3b = False
        match4b = False
        for i in tax_data:
            if float(x["BOX3B_TAX RATE"]) == float(i):
                match3b = True
            if float(x["BOX4B_TAX RATE"]) == float(i):
                match4b = True
        if match3b is False or match4b is False:
            row = [x["BOX13A_RECIPIENT NAME1"], x["BOX3B_TAX RATE"], x["BOX4B_TAX RATE"], "Not a valid tax rate."]
            rows.append(row)

    with open(filename, 'w', encoding="utf-8", newline='') as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile)

        # writing the fields
        csvwriter.writerow(tax_rate_fields)

        # writing the data rows
        csvwriter.writerows(rows)

    # BOX7A Evaluation
    filename = outputfilepath + "_BOX7A_errors.csv"
    tax_rate_fields = ["BOX13A_RECIPIENT NAME1", "BOX7A_FEDERAL TAX WITHHELD", "REASON"]
    rows = []
    for x in data_dict:
        if (float(x["BOX3B_TAX RATE"]) == 0 and float(x["BOX4B_TAX RATE"]) == 0) and (
            x["BOX7A_FEDERAL TAX WITHHELD"] != 0
        ):
            row = [x["BOX13A_RECIPIENT NAME1"], str(x["BOX7A_FEDERAL TAX WITHHELD"]), "Tax rate is 0, but tax withheld."]
            rows.append(row)
        if math.isnan(float(x["BOX3B_TAX RATE"])):
            row = [x["BOX13A_RECIPIENT NAME1"], str(x["BOX7A_FEDERAL TAX WITHHELD"]), "Not valid tax rate."]
            rows.append(row)
        if float(x["BOX3B_TAX RATE"]) != 0 and not math.isnan(float(x["BOX3B_TAX RATE"])):
            tax_owed = round(
                (float(x["BOX3B_TAX RATE"]) * float(x["BOX2_GROSS INCOME"])) / 100
            )
            if tax_owed != float(x["BOX7A_FEDERAL TAX WITHHELD"]):
                row = [x["BOX13A_RECIPIENT NAME1"], str(x["BOX7A_FEDERAL TAX WITHHELD"]),
                       "Tax withheld is not correct amount(Tax rate x Gross Income)."]
                rows.append(row)
        if math.isnan(float(x["BOX4B_TAX RATE"])):
            row = [x["BOX13A_RECIPIENT NAME1"], str(x["BOX7A_FEDERAL TAX WITHHELD"]), "Not valid tax rate."]
            rows.append(row)
        if float(x["BOX4B_TAX RATE"]) != 0 and not math.isnan(float(x["BOX4B_TAX RATE"])):
            tax_owed = round(
                float(x["BOX4B_TAX RATE"]) * float(x["BOX2_GROSS INCOME"]) / 100
            )
            if tax_owed != float(x["BOX7A_FEDERAL TAX WITHHELD"]):
                row = [x["BOX13A_RECIPIENT NAME1"], str(x["BOX7A_FEDERAL TAX WITHHELD"]),
                       "Tax withheld is not correct amount(Tax rate x Gross Income)."]
                rows.append(row)

    with open(filename, 'w', encoding="utf-8", newline='') as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile)

        # writing the fields
        csvwriter.writerow(tax_rate_fields)

        # writing the data rows
        csvwriter.writerows(rows)

    # BOX10 Evaluation
    filename = outputfilepath + "_BOX10_errors.csv"
    tax_rate_fields = ["BOX13A_RECIPIENT NAME1", "BOX10_TOTAL WITHHOLDING CREDIT", "REASON"]
    rows = []
    for x in data_dict:
        box7a = float(x["BOX7A_FEDERAL TAX WITHHELD"])
        if math.isnan(box7a):
            box7a = 0
        box8 = float(x["BOX8_TAX WITHHELD OTHER AGENTS"])
        if math.isnan(box8):
            box8 = 0
        box9 = float(x["BOX9_AMOUNT REPAID RECIPIENT"])
        if math.isnan(box9):
            box9 = 0

        box10_sum = box7a + box8 + box9
        if box10_sum != float(x["BOX10_TOTAL WITHHOLDING CREDIT"]):
            row = [x["BOX13A_RECIPIENT NAME1"], str(x["BOX10_TOTAL WITHHOLDING CREDIT"]), "Box10 not correct amount."]
            rows.append(row)

    with open(filename, 'w', encoding="utf-8", newline='') as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile)

        # writing the fields
        csvwriter.writerow(tax_rate_fields)

        # writing the data rows
        csvwriter.writerows(rows)

    # BOX13B Evaluation
    filename = outputfilepath + "_BOX13B_errors.csv"
    tax_rate_fields = ["BOX13A_RECIPIENT NAME1", "BOX13B_RECIPIENT COUNTRY CODE", "BOX13D_RECIPIENT FOREIGN COUNTRY", "REASON"]
    rows = []
    for x in data_dict:
        print(x["BOX13B_RECIPIENT COUNTRY CODE"])
        x["BOX13B_RECIPIENT COUNTRY CODE"] = x["BOX13B_RECIPIENT COUNTRY CODE"].rstrip()
        x["BOX13D_RECIPIENT FOREIGN COUNTRY"] = str(x["BOX13D_RECIPIENT FOREIGN COUNTRY"]).rstrip()
        if x["BOX13D_RECIPIENT FOREIGN COUNTRY"] == "nan":
            x["BOX13D_RECIPIENT FOREIGN COUNTRY"] = 'Null'
        if not isinstance(x["BOX13D_RECIPIENT FOREIGN COUNTRY"], str):
            continue
        for i in country_data:
            if x["BOX13B_RECIPIENT COUNTRY CODE"].casefold() == i["Code"].casefold():
                if not x["BOX13D_RECIPIENT FOREIGN COUNTRY"].casefold() == i["Name"].casefold():
                    row = [x["BOX13A_RECIPIENT NAME1"], str(x["BOX13B_RECIPIENT COUNTRY CODE"]),
                           str(x["BOX13D_RECIPIENT FOREIGN COUNTRY"]), "Country name does not match country code."]
                    rows.append(row)

    with open(filename, 'w', encoding="utf-8", newline='') as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile)

        # writing the fields
        csvwriter.writerow(tax_rate_fields)

        # writing the data rows
        csvwriter.writerows(rows)

    # BOX13D Evaluation
    filename = outputfilepath + "_BOX13D_errors.csv"
    tax_rate_fields = ["BOX13A_RECIPIENT NAME1", "BOX13B_RECIPIENT STATE", "BOX13B_RECIPIENT PROVINCE",
                       "BOX13D_RECIPIENT FOREIGN COUNTRY", "REASON"]
    rows = []
    for x in data_dict:
        match = True
        x["BOX13D_RECIPIENT FOREIGN COUNTRY"] = str(x["BOX13D_RECIPIENT FOREIGN COUNTRY"]).rstrip()
        if not isinstance(x["BOX13D_RECIPIENT FOREIGN COUNTRY"], str):
            x["BOX13D_RECIPIENT FOREIGN COUNTRY"] = 'null'
            if not isinstance(x["BOX13D_RECIPIENT STATE(2LetterCode)"], str):
                x["BOX13D_RECIPIENT STATE(2LetterCode)"] = 'null'
            row = [x["BOX13A_RECIPIENT NAME1"], str(x["BOX13D_RECIPIENT STATE(2LetterCode)"]), "",
                   str(x["BOX13D_RECIPIENT FOREIGN COUNTRY"]), "No country code and no state code provided."]
            rows.append(row)
            continue
        if (x["BOX13D_RECIPIENT FOREIGN COUNTRY"].casefold() == "United States".casefold()
                and isinstance(x["BOX13D_RECIPIENT STATE(2LetterCode)"], str)):
            match = False
            for i in state_data:
                if (
                    x["BOX13D_RECIPIENT STATE(2LetterCode)"].casefold()
                    == i["Code"].casefold()
                ):
                    match = True
        elif x["BOX13D_RECIPIENT FOREIGN COUNTRY"].casefold() == "United States".casefold():
            if not (isinstance(x["BOX13D_RECIPIENT STATE(2LetterCode)"], str)):
                x["BOX13D_RECIPIENT STATE(2LetterCode)"] = 'null'
                match = False
        if not match:
            row = [x["BOX13A_RECIPIENT NAME1"], str(x["BOX13D_RECIPIENT STATE(2LetterCode)"]), "",
                   str(x["BOX13D_RECIPIENT FOREIGN COUNTRY"]), "Country is USA but state code does not match"]
            rows.append(row)

    # BOX13D Evaluation
    for x in data_dict:
        x["BOX13D_RECIPIENT PROVINCE(2LetterCode)"] = str(x["BOX13D_RECIPIENT PROVINCE(2LetterCode)"]).replace("    ", "")
        if x["BOX13D_RECIPIENT PROVINCE(2LetterCode)"] == "nan":
            x["BOX13D_RECIPIENT PROVINCE(2LetterCode)"] = "Null"
        match = True
        if (str(
            x["BOX13D_RECIPIENT FOREIGN COUNTRY"]).casefold() != "Canada".casefold()
                and x["BOX13D_RECIPIENT PROVINCE(2LetterCode)"] != ""):
            if not (x["BOX13D_RECIPIENT PROVINCE(2LetterCode)"]) == "Null":
                row = [x["BOX13A_RECIPIENT NAME1"], "", str(x["BOX13D_RECIPIENT PROVINCE(2LetterCode)"]),
                       str(x["BOX13D_RECIPIENT FOREIGN COUNTRY"]), "Country is not Canada but province fild not empty"]
                rows.append(row)
                continue
        if str(x["BOX13D_RECIPIENT FOREIGN COUNTRY"]).casefold() == "Canada".casefold():
            match = False
            for i in prov_data:
                if (
                    x["BOX13D_RECIPIENT PROVINCE(2LetterCode)"].casefold()
                    == i["Code"].casefold()
                ):
                    match = True
        if not match:
            row = [x["BOX13A_RECIPIENT NAME1"], "", str(x["BOX13D_RECIPIENT PROVINCE(2LetterCode)"]),
                   str(x["BOX13D_RECIPIENT FOREIGN COUNTRY"]), "Country is Canada but province code does not match"]
            rows.append(row)

    with open(filename, 'w', encoding="utf-8", newline='') as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile)

        # writing the fields
        csvwriter.writerow(tax_rate_fields)

        # writing the data rows
        csvwriter.writerows(rows)


if __name__ == "__main__":

    # Logging
    logging.basicConfig(
        filename=r"1042-S-" + str(date.today()) + ".log",
        format="%(asctime)s %(message)s",
        encoding="utf-8",
        level=logging.DEBUG,
    )
    logger = logging.getLogger()

    # layout of window.
    layout = [
        [
            sg.Image(resource_path("../../../../../PycharmProjects/State_filing/spsgz.png")),
            sg.Text(
                "Select input file to begin evaluation.",
                font=("Arial Bold", 16),
                size=20,
                expand_x=True,
                justification="center",
                background_color="#FFFFFF",
                text_color="#5F6A27",
            ),
        ],
        [
            sg.Text(
                "Enter file path for input data (Comma Separated file(.csv): ",
                font=("Arial Bold", 12),
                size=(25, 2),
                background_color="#FFFFFF",
                text_color="#5F6A27",
            ),
            sg.InputText(key="-inputfile-"),
            sg.FileBrowse(
                target="-inputfile-",
                button_color="#5F6A27",
                size=(10),
            ),
        ],
        [
            sg.Button("Ok", button_color="#5F6A27", pad=(200, 0), size=10),
            sg.Button("Close", button_color="#8E111C", size=10),
        ],
    ]
    # Create the Window
    window = sg.Window(
        "1042-S Data Input ",
        layout,
        background_color="#FFFFFF",
        titlebar_icon=resource_path("spsgz.ico"),
    )

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Close"):
            break
        elif event == "-BROWSE-":
            file = sg.popup_get_file("", no_window=True)
            window["_INPUT_"].update(file)
        elif event == "Ok":
            if values["-inputfile-"]:
                inputcsvfilepath = values["-inputfile-"]
                logger.debug("You entered input : " + inputcsvfilepath + ".")
                main(inputcsvfilepath)
            else:
                ch = sg.popup_ok(
                    "Input path required. Please re-enter path for input.",
                    title="Ok",
                    background_color="#FFFFFF",
                    text_color="#5F6A27",
                    button_color="#5F6A27",
                )
            ch = sg.popup_ok(
                "Process Complete",
                title="Ok",
                background_color="#FFFFFF",
                text_color="#5F6A27",
                button_color="#5F6A27",
            )

    window.close()
