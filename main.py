import csv
import json
import logging
import os
import sys

import pandas as pd
import FreeSimpleGUI as sg

from datetime import date
from validators import (
    validate_tax_rates,
    validate_box7a,
    validate_box10,
    validate_box13b,
    validate_box13d,
)


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def _write_csv(filename, fields, rows):
    with open(filename, 'w', encoding="utf-8", newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(fields)
        csvwriter.writerows(rows)


def main(input):
    data = pd.read_csv(input, encoding="latin-1", on_bad_lines='warn')
    data_dict = data.to_dict(orient="records")

    outputfilepath = input.rsplit(".", 1)[0]

    with open(resource_path("tax_rates.json")) as f:
        tax_data = json.load(f)
    with open(resource_path("country_codes.json")) as j:
        country_data = json.load(j)
    with open(resource_path("state_codes.json")) as s:
        state_data = json.load(s)
    with open(resource_path("can_provinces.json")) as c:
        prov_data = json.load(c)

    _write_csv(
        outputfilepath + "_tax_rate_errors.csv",
        ["BOX13A_RECIPIENT NAME1", "BOX3B_TAX RATE", "BOX4B_TAX RATE", "REASON"],
        validate_tax_rates(data_dict, tax_data),
    )
    _write_csv(
        outputfilepath + "_BOX7A_errors.csv",
        ["BOX13A_RECIPIENT NAME1", "BOX7A_FEDERAL TAX WITHHELD", "REASON"],
        validate_box7a(data_dict),
    )
    _write_csv(
        outputfilepath + "_BOX10_errors.csv",
        ["BOX13A_RECIPIENT NAME1", "BOX10_TOTAL WITHHOLDING CREDIT", "REASON"],
        validate_box10(data_dict),
    )
    _write_csv(
        outputfilepath + "_BOX13B_errors.csv",
        ["BOX13A_RECIPIENT NAME1", "BOX13B_RECIPIENT COUNTRY CODE", "BOX13D_RECIPIENT FOREIGN COUNTRY", "REASON"],
        validate_box13b(data_dict, country_data),
    )
    _write_csv(
        outputfilepath + "_BOX13D_errors.csv",
        ["BOX13A_RECIPIENT NAME1", "BOX13B_RECIPIENT STATE", "BOX13B_RECIPIENT PROVINCE",
         "BOX13D_RECIPIENT FOREIGN COUNTRY", "REASON"],
        validate_box13d(data_dict, state_data, prov_data),
    )


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
