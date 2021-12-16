from __future__ import print_function
from mailmerge import MailMerge
import plotly.graph_objects as go
from fpdf import FPDF
import PyPDF2 as pypdf
import json
from PyPDF2 import PdfFileMerger, PdfFileReader
import os
from pdf_generator import word_to_pdf


def initialize():
    with open("../json/flip.json") as json_file:
        flip = json.load(json_file)
        flip = flip["data"]["flip"]
    return flip


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


def overlay(infile, over, out):
    with open(f'{infile}.pdf', "rb") as inFile, open(f'{over}.pdf', "rb") as overlay:
        original = pypdf.PdfFileReader(inFile)
        background = original.getPage(1)
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


def wordPopulate(template, out, property_address, pdfFileProperties, flip):
    pageNumber = pdfFileProperties['pageStart']
    pagesTotalNumber = 3
    pdfFileProperties['tableContent'].update(
        {pageNumber: 'Comprehensive Financial Report – Flipping Detailed Financial Analytics',
         pageNumber + 1: 'Comprehensive Financial Report - Flipping Cash Flow Projection',
         pageNumber + 2: 'Comprehensive Financial Report - Flipping Tax Calculation'})
    pdfFileProperties['pageStart'] = pageNumber + pagesTotalNumber

    template = f'{template}.docx'
    document = MailMerge(template)
    document.merge(PG1=page_value(pageNumber),
                   PG2=page_value(pageNumber + 1),
                   PG3=page_value(pageNumber + 2))

    if flip['genericInput']['applyImprovementAllScenarios'] == False:
        flip['genericInput']['improvementCost'] = 0

    loan = flip['financialProjectionSummary']['loanPayments']
    operation = flip['financialProjectionSummary']['operationExpenses']
    BTcashFlow = flip['cashFlowProjection']['cashFlowProjectionPurchased']['beforeTaxCashFlow']
    ATcashFlow = flip['cashFlowProjection']['cashFlowProjectionPurchased']['afterTaxCashFlow']
    document.merge(ADR=property_address)

    cust_1 = {'ADR': property_address,
              'PP': fin_value(flip['genericInput']['purchasePrice']),
              'IC': fin_value(flip['genericInput']['improvementCost']),
              'PE': fin_value(flip['buyingExpenses']),
              'ICAV': fin_value(
                  flip['genericInput']['improvementCost'] * (1 + flip['genericInput']['addedValueRateImprovement'])),
              'GSP': fin_value(flip['sellPrice']),
              'SE': fin_value(flip['sellingExpense']),
              'APT': fin_value(flip['genericInput']['propertyTaxPercentage'] * flip['genericInput']['purchasePrice']),
              'API': fin_value(
                  flip['genericInput']['propertyInsurancePercentage'] * flip['genericInput']['purchasePrice']),
              'AHOA': fin_value(flip['genericInput']['monthlyHOA'] * 12),
              'AOE': fin_value(flip["financialProjectionSummary"]['operationExpenses'][1] * -12),
              'ICA': fin_value(flip['initialCash'] * -1),
              'L1': fin_value(loan[1]), 'L2': fin_value(loan[2]), 'L3': fin_value(loan[3]), 'L4': fin_value(loan[4]),
              'L5': fin_value(loan[5]),
              'OE1': fin_value(operation[1]), 'OE2': fin_value(operation[2]), 'OE3': fin_value(operation[3]),
              'OE4': fin_value(operation[4]), 'OE5': fin_value(operation[5]),
              'BSP': fin_value(flip['beforeTaxEquityReversion']),
              'BT0': fin_value(BTcashFlow[0]), 'BT1': fin_value(BTcashFlow[1]), 'BT2': fin_value(BTcashFlow[2]),
              'BT3': fin_value(BTcashFlow[3]), 'BT4': fin_value(BTcashFlow[4]), 'BT5': fin_value(BTcashFlow[11]),
              'TDS': fin_value(flip['taxProjection']['taxCapitalGain'] * -1),
              'AT0': fin_value(ATcashFlow[0]), 'AT1': fin_value(ATcashFlow[1]), 'AT2': fin_value(ATcashFlow[2]),
              'AT3': fin_value(ATcashFlow[3]), 'AT4': fin_value(ATcashFlow[4]), 'AT5': fin_value(ATcashFlow[11]),
              'BIR': rate_value(flip['beforeTaxIRR']),
              'AIR': rate_value(flip['afterTaxIRR']),
              # tax
              'ESP': fin_value(flip['taxProjection']['estimatedSalePrice']),
              'SEN': fin_value(flip['taxProjection']['sellingExpenses']),
              'NSP': fin_value(flip['taxProjection']['netSalePrice']),
              'PUE': fin_value(flip['buyingExpenses']),
              'REM': fin_value(flip['genericInput']['improvementCost']),
              'PTIN': fin_value(flip['taxProjection']['propertyTaxInsurance']),
              'HOAU': fin_value(flip['taxProjection']['utilities']),
              'PAIN': fin_value(flip['taxProjection']['paidInterest']),
              'AJB': fin_value(flip['taxProjection']['adjustedBasis']),
              'AJBN': fin_value(-1 * flip['taxProjection']['adjustedBasis']),
              'GS': fin_value(flip['gainRecognizedSale']),
              'TCAP': fin_value(-1 * flip['taxProjection']['taxCapitalGain']),
              'TTX': fin_value(-1 * flip['taxProjection']['taxCapitalGain']),
              'CR': rate_value(flip['genericInput']['capitalGainTaxRate']),
              }

    document.merge_pages([cust_1])

    document.write(f'{out}.docx')


def pdfToOut(file):
    os.rename(f'{file}.pdf', f'{file}Out.pdf')


def figuresOnPDF(file, flip):
    waterfall_chart_img = waterfall_chart([round(flip["purchasePrice"] / 1000),
                                           round((flip["sellingExpense"] +
                                                  flip["buyingExpenses"]) / 1000),
                                           round(
                                               flip["totalRemodelingCost"] / 1000),
                                           round(flip["ownershipCosts"] / 1000),
                                           round(flip["gainRecognizedSale"] / 1000),
                                           round(flip["sellPrice"] / 1000)], file)

    pdf = FPDF(orientation='P', unit='in', format='Letter')
    pdf.set_margins(left=1, top=1, right=1)
    pdf.add_page()

    pdf.image(f'{file}.png', x=1, y=6.5, w=6.5, h=3.3)
    pdf.output(f'{file}.pdf')
    os.remove(f'{file}.png')


def waterfall_chart(values, chartName):
    if values[4] > 0:
        x4 = "<b>Gain</b>"
    else:
        x4 = "<b>Loss</b>"
    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["relative", "relative", "relative", "relative", "relative", "total"],
        x=["<b>Buy</b>", "<b>Transaction Cost</b>", "<b>Remodeling Cost</b>", "<b>Ownership Cost</b>", x4,
           "<b>Sell</b>"],
        textposition="outside",
        text=[f"${item}" for item in values],
        y=values,
        connector={"visible": False},
        increasing={"marker": {"color": "#ed6f78"}},
        totals={"marker": {"color": "#4262ff"}},
    ))
    fig.update_layout(
        autosize=False,
        width=900,
        height=400,
        margin=dict(l=0, r=0, b=0, t=0, pad=4),
        yaxis=dict(
            title_text="Thousand Dollars",
            tickfont=dict(
                size=14
            )
        ),
        xaxis=dict(
            tickfont=dict(
                size=14
            )
        ),
        plot_bgcolor='#ffffff',

    )
    fig.add_shape(
        type="rect", fillcolor="#4262ff", line=dict(color="#4262ff"), opacity=1,
        x0=-0.3, x1=0.3, xref="x", y0=0.0, y1=fig.data[0].y[0], yref="y"
    )
    if values[4] > 0:
        fig.add_shape(
            type="rect", fillcolor="#009788", line=dict(color="#009788"), opacity=1,
            x0=3.6, x1=4.4, xref="x",
            y0=fig.data[0].y[-1] - fig.data[0].y[-2], y1=fig.data[0].y[-1], yref="y"
        )
    fig.update_xaxes(showline=True, linewidth=2, linecolor='black')
    fig.update_yaxes(showline=True, linewidth=2, linecolor='black')
    fig.update_traces(
        width=.6,
        textfont=dict(
            size=14
        )
    )

    filename = f"{chartName}.png"
    fig.write_image(f"{filename}", width=900)
    return filename


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
    flip = initialize()
    id = pdfFileProperties['id']
    templateLocation = pdfFileProperties['templateLocation']
    outLocation = pdfFileProperties['outLocation']
    property_address = pdfFileProperties['propertyAddress']

    wordPopulate(f'{templateLocation}flipProjectionTemplate', f'{outLocation}flipProjection{id}', property_address,
                 pdfFileProperties, flip)
    word_to_pdf(f'{outLocation}flipProjection{id}')
    figuresOnPDF(f'{outLocation}flipProjection{id}.png', flip)
    overlay(f'{outLocation}flipProjection{id}', f'{outLocation}flipProjection{id}.png',
            f'{outLocation}flipProjectionOut{id}')
    maregePdf(f'{outLocation}flipProjectionOut{id}', f'{outLocation}out{id}')
