import json
import math
import pandas as pd


def main(input):
    data = pd.read_csv(input, encoding='latin-1')
    # Convert the DataFrame to a Dictionary
    data_dict = data.to_dict(orient='records')
    # print(data_dict)

    # Opening JSON file
    f = open('tax_rates.json')
    j = open('country_codes.json')
    # returns JSON object as
    # a dictionary
    data = json.load(f)
    country_data = json.load(j)

    f = open("tax_rate_errors.txt", "w")
    print("Forms with Tax Rate Errors:", file=f)
    f.close()

    # BOX3b and BOX4B Evaluation
    for x in data_dict:
        match3b = False
        match4b = False
        for i in data:
            if float(x['BOX3B_TAX RATE']) == float(i):
                match3b = True
            if float(x['BOX4B_TAX RATE']) == float(i):
                match4b = True
        if match3b is False:
            f = open("tax_rate_errors.txt", "a")
            print(str(x['Unique Form Identifier']) + " RECIPIENT NAME - " + x["BOX13A_RECIPIENT NAME1"] +
                  " INCORRECT RATE - " + str(x["BOX3B_TAX RATE"]), file=f)
            f.close()
        if match4b is False:
            f = open("tax_rate_errors.txt", "a")
            print(str(x['Unique Form Identifier']) + " RECIPIENT NAME - " + x["BOX13A_RECIPIENT NAME1"] +
                  " INCORRECT RATE - " + str(x["BOX4B_TAX RATE"]), file=f)
            f.close()

    f = open("BOX7A_Errors.txt", "w")
    print("Forms with BOX7A Errors:", file=f)
    f.close()

    # BOX7A Evaluation
    for x in data_dict:
        if (float(x['BOX3B_TAX RATE']) == 0 and float(x['BOX4B_TAX RATE']) == 0) and (x['BOX7A_FEDERAL TAX WITHHELD']
                                                                                      != 0):
            f = open("BOX7A_Errors.txt", "a")
            print(x['Unique Form Identifier'], file=f)
            f.close()
        if float(x['BOX3B_TAX RATE']) != 0:
            tax_owed = round((float(x['BOX3B_TAX RATE']) * float(x['BOX2_GROSS INCOME'])) / 100)
            if tax_owed != float(x['BOX7A_FEDERAL TAX WITHHELD']):
                f = open("BOX7A_Errors.txt", "a")
                print(str(x['Unique Form Identifier']) + " RECIPIENT NAME - " + x["BOX13A_RECIPIENT NAME1"] +
                      " INCORRECT BOX7A AMOUNT - " + str(x["BOX7A_FEDERAL TAX WITHHELD"]), file=f)
                f.close()
        if float(x['BOX4B_TAX RATE']) != 0:
            tax_owed = round(float(x['BOX4B_TAX RATE']) * float(x['BOX2_GROSS INCOME']) / 100)
            if tax_owed != float(x['BOX7A_FEDERAL TAX WITHHELD']):
                f = open("BOX7A_Errors.txt", "a")
                print(str(x['Unique Form Identifier']) + " RECIPIENT NAME - " + x["BOX13A_RECIPIENT NAME1"] +
                      " INCORRECT BOX7A AMOUNT - " + str(x["BOX7A_FEDERAL TAX WITHHELD"]), file=f)
                f.close()

    f = open("BOX10_Errors.txt", "w")
    print("Forms with BOX10 Errors:", file=f)
    f.close()

    for x in data_dict:
        box7a = float(x['BOX7A_FEDERAL TAX WITHHELD'])
        if math.isnan(box7a):
            box7a = 0
        box8 = float(x['BOX8_TAX WITHHELD OTHER AGENTS'])
        if math.isnan(box8):
            box8 = 0
        box9 = float(x['BOX9_TAX PAID WITHHOLDING AGENT'])
        if math.isnan(box9):
            box9 = 0

        box10_sum = (box7a + box8 + box9)
        if box10_sum != float(x['BOX10_TOTAL WITHHOLDING CREDIT']):
            f = open("BOX10_Errors.txt", "a")
            print(str(x['Unique Form Identifier']) + " RECIPIENT NAME - " + x["BOX13A_RECIPIENT NAME1"] +
                  " INCORRECT BOX10 AMOUNT - " + str(x["BOX10_TOTAL WITHHOLDING CREDIT"]), file=f)
            f.close()

    f = open("BOX13B_Errors.txt", "w")
    print("Forms with BOX13B Errors:", file=f)
    f.close()

    for x in data_dict:
        if not isinstance(x["BOX13D_RECIPIENT COUNTRY"], str):
            continue
        for i in country_data:
            if x["BOX13B_RECIPIENT COUNTRY CODE"] == i["Code"]:
                if not x["BOX13D_RECIPIENT COUNTRY"].casefold() == i["Name"].casefold():
                    f = open("BOX13B_Errors.txt", "a")
                    print(str(x['Unique Form Identifier']) + " RECIPIENT NAME - " + x["BOX13A_RECIPIENT NAME1"] +
                          " COUNTRY CODE - " + str(x["BOX13B_RECIPIENT COUNTRY CODE"] + " COUNTRY - "
                                                   + str(x["BOX13D_RECIPIENT COUNTRY"])), file=f)
                    f.close()


if __name__ == "__main__":
    input = "C:\python files\Python files\TEST_Springer 1042-S_Template_2023_FINAL_02.29.24_Bill.csv"

    main(input)
