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
        ["BOX13A_RECIPIENT NAME1", "BOX13B_RECIPIENT COUNTRY CODE", "BOX13D_RECIPIENT COUNTRY", "REASON"],
        validate_box13b(data_dict, country_data),
    )
    _write_csv(
        outputfilepath + "_BOX13D_errors.csv",
        ["BOX13A_RECIPIENT NAME1", "BOX13B_RECIPIENT STATE", "BOX13B_RECIPIENT PROVINCE",
         "BOX13D_RECIPIENT COUNTRY", "REASON"],
        validate_box13d(data_dict, state_data, prov_data),
    )


if __name__ == "__main__":

    import threading

    logging.basicConfig(
        filename="1042-S-" + str(date.today()) + ".log",
        format="%(asctime)s %(message)s",
        encoding="utf-8",
        level=logging.DEBUG,
    )
    logger = logging.getLogger()

    # ── Brand constants (matches state_filing_gui.py) ──────────────────────
    sg.theme("LightGrey1")
    BG        = "#FFFFFF"
    FG        = "#5F6A27"
    FONT      = ("Arial Bold", 12)
    FONT_TITLE = ("Arial Bold", 16)
    BTN_RUN   = "#5F6A27"
    BTN_CLOSE = "#8E111C"

    logo_path = resource_path("spsgz.png")

    layout = [
        [
            (sg.Image(logo_path) if os.path.exists(logo_path) else sg.Text("")),
            sg.Text(
                "Select input file to begin evaluation.",
                font=FONT_TITLE,
                size=20,
                expand_x=True,
                justification="center",
                background_color=BG,
                text_color=FG,
            ),
        ],
        [
            sg.Text(
                "Enter file path for input data:",
                font=FONT,
                background_color=BG,
                text_color=FG,
            ),
            sg.InputText(key="-FILE-", enable_events=True),
            sg.FileBrowse(
                target="-FILE-",
                button_color=FG,
                size=(10, 2),
                file_types=(("CSV Files", "*.csv"), ("All files", "*.*")),
            ),
        ],
        [
            sg.Button("Run", key="-RUN-", button_color=BTN_RUN, pad=((200, 0), 0), size=10),
            sg.Button("Close", button_color=BTN_CLOSE, size=10),
        ],
    ]

    window = sg.Window(
        "1042-S Error Checker",
        layout,
        background_color=BG,
        finalize=True,
    )

    # ── Custom popup (matches state_filing_gui.py style) ───────────────────
    def _popup(message: str, title: str, btn_color: str):
        popup_layout = [
            [sg.Text(message, font=("Arial", 11), background_color=BG,
                     text_color=FG, pad=(16, 16))],
            [sg.Button("OK", button_color=btn_color, size=(8, 1),
                       pad=(0, (0, 12)))],
        ]
        pop = sg.Window(
            title, popup_layout,
            background_color=BG,
            keep_on_top=True,
            modal=True,
            element_justification="center",
            margins=(8, 8),
        )
        pop.read(close=True)

    # ── Background worker ──────────────────────────────────────────────────
    def run_process(file_path: str):
        try:
            logger.debug("Processing: " + file_path)
            main(file_path)
            base = os.path.basename(file_path.rsplit(".", 1)[0])
            msg = (
                "Processing complete!\n\nError report files:\n"
                + "\n".join([
                    base + "_tax_rate_errors.csv",
                    base + "_BOX7A_errors.csv",
                    base + "_BOX10_errors.csv",
                    base + "_BOX13B_errors.csv",
                    base + "_BOX13D_errors.csv",
                ])
            )
            window.write_event_value("-DONE-", (True, msg))
        except Exception as exc:
            logger.exception("Error processing file.")
            window.write_event_value("-DONE-", (False, str(exc)))

    # ── Event loop ─────────────────────────────────────────────────────────
    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, "Close"):
            break

        if event == "-FILE-":
            window["-RUN-"].update(disabled=not values["-FILE-"])

        if event == "-RUN-":
            file_path = values["-FILE-"].strip()
            if not os.path.isfile(file_path):
                _popup(f"File does not exist:\n{file_path}", "Error", BTN_CLOSE)
                continue
            window["-RUN-"].update(disabled=True, text="Running…")
            threading.Thread(target=run_process, args=(file_path,), daemon=True).start()

        if event == "-DONE-":
            success, message = values[event]
            window["-RUN-"].update(disabled=False, text="Run")
            if success:
                _popup(message, "Complete", BTN_RUN)
            else:
                _popup(message, "Error", BTN_CLOSE)

    window.close()
