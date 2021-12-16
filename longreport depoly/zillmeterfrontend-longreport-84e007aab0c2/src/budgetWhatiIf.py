from __future__ import print_function
from mailmerge import MailMerge
import plotly.graph_objects as go
from fpdf import FPDF
import PyPDF2 as pypdf
from pdf_generator import word_to_pdf
import json
from matplotlib import pyplot as plt
from PyPDF2 import PdfFileMerger, PdfFileReader
import os


def initialize():
    with open("../json/budget.json") as json_file:
        budget = json.load(json_file)
        budget = budget["data"]["budgetUse"]

    with open("../json/whatif.json") as json_file:
        whatif_json = json.load(json_file)
    return budget, whatif_json


def fin_value(dollar_value):
    if dollar_value < 0:
        tor = f'{round(-1 * dollar_value):,}'
        tor = f'$({tor})'
    elif dollar_value > 0:
        tor = f'${round(dollar_value):,}'
    else:
        tor = '-'
    return tor


def rate_value(rate):
    tor = round(rate * 100)
    return str(f'{tor}%')


def whatif(criteria, range, whatif_json):
    if range == 'low':
        return fin_value(min(whatif_json[criteria]['budgetUse']['beforeTaxNetProfit']['low'],
                             whatif_json[criteria]['budgetUse']['beforeTaxNetProfit']['high']))
    else:
        return fin_value(max(whatif_json[criteria]['budgetUse']['beforeTaxNetProfit']['low'],
                             whatif_json[criteria]['budgetUse']['beforeTaxNetProfit']['high']))


def highValue(parameter, sens, Isyear):
    if Isyear != 't':
        parameter = fin_value(parameter * (1 + sens))
    if Isyear == 't':
        parameter = f'{round(parameter * (1 + sens) / 12)} Year'
    return parameter


def lowValue(parameter, sens, Isyear):
    if Isyear != 't':
        parameter = fin_value(parameter * (1 - sens))
    if Isyear == 't':
        parameter = f'{round(parameter * (1 - sens) / 12)} Year'
    return parameter


def overlay(infile, over, out):
    with open(f'{infile}.pdf', "rb") as inFile, open(f'{over}.pdf', "rb") as overlay:
        original = pypdf.PdfFileReader(inFile)
        background = original.getPage(0)
        foreground = pypdf.PdfFileReader(overlay).getPage(0)

        # merge the first two pages
        background.mergePage(foreground)

        # add all pages to a writer
        writer = pypdf.PdfFileWriter()
        for i in range(original.getNumPages()):
            page = original.getPage(i)
            writer.addPage(page)

        # write everything in the writer to a file
        with open(f'{out}.pdf', "wb") as outFile:
            writer.write(outFile)

        # delete files
        inFile.close()
        overlay.close()
        os.remove(f'{infile}.pdf')
        os.remove(f'{over}.pdf')


def page_value(pageNum):
    return f'Page {pageNum}'


def wordPopulate(template, out, property_address, pdfFileProperties, budget, whatif_json, sensitivity):
    pageNumber = pdfFileProperties['pageStart']
    pagesTotalNumber = 1
    pdfFileProperties['tableContent'].update({pageNumber: 'What if Analysis – Budget Residence'})
    pdfFileProperties['pageStart'] = pageNumber + pagesTotalNumber

    template = f'{template}.docx'
    document = MailMerge(template)
    document.merge(ADR=property_address)
    document.merge(PG=page_value(pageNumber))

    cust_1 = {
        'ADR': property_address,
        'SENS': rate_value(sensitivity),
        'SNSN': rate_value(sensitivity * -1),
        ## what if  Purchase Price
        'PPIN': lowValue(budget['genericInput']['purchasePrice'], sensitivity, 'f'),
        'PP': fin_value(budget['genericInput']['purchasePrice']),
        'PPAX': highValue(budget['genericInput']['purchasePrice'], sensitivity, 'f'),
        'PPVI': whatif('purchasePrice', 'low', whatif_json),
        'PPV': fin_value(budget['beforeTaxNetProfit']),
        'PPVX': whatif('purchasePrice', 'high', whatif_json),

        ## what if Rental Income
        'RMIN': lowValue(budget['financialProjectionSummary']['income'][1] / 12, sensitivity, 'f'),
        'R': fin_value(budget['financialProjectionSummary']['income'][1] / 12),
        'RMAX': highValue(budget['financialProjectionSummary']['income'][1] / 12, sensitivity, 'f'),
        'RPVI': whatif('incomeAvoidedCosts', 'low', whatif_json),
        'RPVX': whatif('incomeAvoidedCosts', 'high', whatif_json),

        ## what if Opertaion Expense
        'OMIN': lowValue(budget['financialProjectionSummary']['operationExpenses'][1] / -12, sensitivity, 'f'),
        'O': fin_value(budget['financialProjectionSummary']['operationExpenses'][1] / -12),
        'OMAX': highValue(budget['financialProjectionSummary']['operationExpenses'][1] / -12, sensitivity, 'f'),
        'OPVI': whatif('operationExpenses', 'low', whatif_json),
        'OPVX': whatif('operationExpenses', 'high', whatif_json),

        ## what if SELLING PRICE
        'SMIN': lowValue(budget['taxProjection']['estimatedSalePrice'], sensitivity, 'f'),
        'S': fin_value(budget['taxProjection']['estimatedSalePrice']),
        'SMAX': highValue(budget['taxProjection']['estimatedSalePrice'], sensitivity, 'f'),
        'SPVI': whatif('SellPrice', 'low', whatif_json),
        'SPVX': whatif('SellPrice', 'high', whatif_json),

        ## what if Holding Period
        'HMIN': lowValue(budget['genericInput']['holdingPeriodAnnual'] * 12, sensitivity, 't'),
        'H': str(budget['genericInput']['holdingPeriodAnnual']),
        'HMAX': highValue(budget['genericInput']['holdingPeriodAnnual'] * 12, sensitivity, 't'),
        'HPVI': whatif('holdingPeriodAnnual', 'low', whatif_json),
        'HPVX': whatif('holdingPeriodAnnual', 'high', whatif_json),

        ## what if Buy&SellExpense
        'BMIN': lowValue(budget['sellingExpense'] + budget['purchaseExpense'], sensitivity, 'f'),
        'B': fin_value(budget['sellingExpense'] + budget['purchaseExpense']),
        'BMAX': highValue(budget['sellingExpense'] + budget['purchaseExpense'], sensitivity, 'f'),
        'BPVI': whatif('transActionCost', 'low', whatif_json),
        'BPVX': whatif('transActionCost', 'high', whatif_json),

        ## what if DownPayment
        'DMIN': lowValue(budget['genericInput']['downPaymentRate'] * budget['genericInput']['purchasePrice'],
                         sensitivity, 'f'),
        'D': fin_value(budget['genericInput']['downPaymentRate'] * budget['genericInput']['purchasePrice']),
        'DMAX': highValue(budget['genericInput']['downPaymentRate'] * budget['genericInput']['purchasePrice'],
                          sensitivity, 'f'),
        'DPVI': whatif('downPaymentRate', 'low', whatif_json),
        'DPVX': whatif('downPaymentRate', 'high', whatif_json),

    }

    ## tornado data
    lows = []
    highs = []
    scenarios = ['purchasePrice', 'incomeAvoidedCosts', 'operationExpenses', 'SellPrice', 'holdingPeriodAnnual',
                 'transActionCost', 'downPaymentRate']

    ## create a list of highs and lows NPV
    for item in scenarios:
        npv = budget['beforeTaxNetProfit']
        lownpv = whatif_json[item]['budgetUse']['beforeTaxNetProfit']['low']
        highnpv = whatif_json[item]['budgetUse']['beforeTaxNetProfit']['high']
        low_npv = min(lownpv, highnpv, npv)
        high_npv = max(lownpv, highnpv, npv)
        low_npv = (low_npv - npv) / npv
        high_npv = (high_npv - npv) / npv
        lows.append(low_npv)
        highs.append(high_npv)
    ##converts lows and highs to rounded %
    lows = [round(100 * item) for item in lows]
    highs = [round(100 * item) for item in highs]

    for item in range(len(highs)):
        highs[item] = -lows[item] + highs[item]

    # sort data based on the highest value for the tordano chart
    variables = [
        'Purchase Price',
        'Rental Income',
        'Operation Expenses',
        'Selling Price',
        'Holding Period',
        'Buy and Sell Expenses',
        'Down Payment',
    ]
    ## Bubble Sort Variables
    for secondItem in range(len(highs) - 1):
        for firstItem in range(len(highs)):
            if abs(highs[firstItem]) < abs(highs[secondItem + 1]):
                temp_highs = highs[firstItem]
                temp_lows = lows[firstItem]
                temp_var = variables[firstItem]
                highs[firstItem] = highs[secondItem + 1]
                lows[firstItem] = lows[secondItem + 1]
                variables[firstItem] = variables[secondItem + 1]
                highs[secondItem + 1] = temp_highs
                lows[secondItem + 1] = temp_lows
                variables[secondItem + 1] = temp_var

    tornado_chart(out, lows, highs, variables)
    ## finding the most impactful variable
    cust_1['HSF'] = variables[0]

    document.merge_pages([cust_1])
    document.write(f'{out}.docx')


def tornado_chart(file, lows, highs, variables):
    # The data
    base = 0

    lows = lows

    values = highs

    ##find Set the max portion of the x-  to show
    maxPercntage = round(10 * (max(abs(max(highs)), abs(min(highs)))
                               - max(abs(max(lows)), abs(min(lows))))) / 10

    portion_to_show = maxPercntage + 5 + 3 * round(maxPercntage / 10)

    # margin adjustments
    plt.subplots(constrained_layout=True)

    # The y position for each variable
    ys = range(len(values))[::-1]  # top to bottom

    # Plot the bars, one by one
    for y, low, value in zip(ys, lows, values):
        # The width of the 'low' and 'high' pieces
        low_width = base - low
        high_width = low + value - base

        # Each bar is a "broken" horizontal bar chart
        plt.broken_barh(
            [(low, low_width), (base, high_width)],
            (y - 0.4, 0.8),
            facecolors=['#FFB3B3', '#A9D18E'],
            edgecolors=['white', 'white'],
            linewidth=1,
        )

        # Display the value as text. It should be positioned in the center of
        # the 'high' bar, except if there isn't any room there, then it should be
        # next to bar instead.
        ## set the locations of % outside of the bar:
        # low values
        if base + high_width > 0:
            x = base + high_width + portion_to_show / 10
            plt.text(x, y, str(value + low) + '%', va='center', ha='center')
        else:
            x = base + high_width - portion_to_show / 10
            plt.text(x, y, str(value + low) + '%', va='center', ha='center')
        # high values
        if base + low > 0:
            x = base + low + portion_to_show / 10
            plt.text(x, y, str(low) + '%', va='center', ha='center')
        else:
            x = base + low - portion_to_show / 10
            plt.text(x, y, str(low) + '%', va='center', ha='center')

    # Draw a vertical line down the middle
    plt.axvline(base, color='black', linewidth=.5)

    # Position the x-axis on the top, hide all the other spines (=axis lines)
    axes = plt.gca()  # (gca = get current axes)
    axes.spines['left'].set_visible(False)
    axes.spines['right'].set_visible(False)
    axes.spines['bottom'].set_visible(False)
    axes.spines['top'].set_visible(False)

    # axes.xaxis.set_ticks_position('top')
    # hide x axis values

    axes.xaxis.set_visible(False)

    # Make the y-axis display the variables
    plt.yticks(ys, variables)

    # Set the portion of the x- and y-axes to show
    plt.xlim(base - portion_to_show, base + portion_to_show)
    plt.ylim(-1, len(variables))

    plt.savefig(f'{file}.png', transparent=True)
    # plt.show()


def figuresOnPDF(file):
    pdf = FPDF(orientation='P', unit='in', format='Letter')
    pdf.set_margins(left=1, top=1, right=1)
    pdf.add_page()
    pdf.image(f'{file}.png', x=1.325, y=5.8, w=5.85, h=4.5)
    pdf.output(f'{file}.png.pdf')
    os.remove(f'{file}.png')


def maregePdf(inFile, outFile):
    pdf_file1 = PdfFileReader(f'{inFile}.pdf')
    pdf_file2 = PdfFileReader(f'{outFile}.pdf')
    output = PdfFileMerger()
    output.append(pdf_file2)
    output.append(pdf_file1)
    with open(f'{outFile}.pdf', "wb") as output_stream:
        output.write(output_stream)

    os.remove(f'{inFile}.pdf')


def main(pdfFileProperties):
    budget, whatif_json = initialize()
    sensitivity = 0.15
    id = pdfFileProperties['id']
    templateLocation = pdfFileProperties['templateLocation']
    outLocation = pdfFileProperties['outLocation']
    property_address = pdfFileProperties['propertyAddress']

    wordPopulate(f'{templateLocation}budgetWhatIfTemplate', f'{outLocation}budgetWhatIf{id}', property_address,
                 pdfFileProperties, budget, whatif_json, sensitivity)
    word_to_pdf(f'{outLocation}budgetWhatIf{id}')
    figuresOnPDF(f'{outLocation}budgetWhatIf{id}')
    overlay(f'{outLocation}budgetWhatIf{id}', f'{outLocation}budgetWhatIf{id}.png', f'{outLocation}budgetWhatIfOut{id}')
    maregePdf(f'{outLocation}budgetWhatIfOut{id}', f'{outLocation}out{id}')
