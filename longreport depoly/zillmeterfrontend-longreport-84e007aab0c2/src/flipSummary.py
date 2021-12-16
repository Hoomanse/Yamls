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


def wordPopulate(template, out, property_address, pdfFileProperties, flip):
    pageNumber = pdfFileProperties['pageStart']
    pagesTotalNumber = 1
    pdfFileProperties['tableContent'].update({pageNumber: 'Financial Projection Summary – Flipping '})
    pdfFileProperties['pageStart'] = pageNumber + pagesTotalNumber

    template = f'{template}.docx'
    document = MailMerge(template)
    document.merge(PG=page_value(pageNumber))

    hp = flip['genericInput']['holdingPeriodAnnual']
    yr = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}
    income = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}
    oe = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}
    loan = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}
    itax = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}
    opcash = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}
    if hp == 2:
        arrays = [1, 5]
        years = [1, 2]
    elif hp == 3:
        arrays = [1, 3, 5]
        years = [1, 2, 3]
    elif hp == 4:
        arrays = [1, 2, 3, 5]
        years = [1, 2, 3, 4]
    else:
        arrays = [1, 2, 3, 4, 5]
        years = [1, 2, 3, 4, 11]

    for item in range(len(arrays)):
        yr[arrays[item]] = f'Month {years[item]}'
        # income[arrays[item]]=fin_value(flip['financialProjectionSummary']['income'][item])
        oe[arrays[item]] = fin_value(flip['financialProjectionSummary']['operationExpenses'][item + 1])
        loan[arrays[item]] = fin_value(flip['financialProjectionSummary']['loanPayments'][item + 1])
        # itax[arrays[item]]=fin_value(flip["cashFlowProjection"]['cashFlowProjectionPurchased']['incomeTax'][item+1])
        opcash[arrays[item]] = fin_value(flip['financialProjectionSummary']['operationNetCashFlow'][item + 1])
    document.merge(ADR=property_address,
                   DP=fin_value(flip['genericInput']['downPaymentRate'] * flip['genericInput']['purchasePrice'] * -1),
                   PE=fin_value(
                       flip['genericInput']['purchaseExpenseRate'] * flip['genericInput']['purchasePrice'] * -1),
                   RE=fin_value(flip['genericInput']['improvementCost'] * -1),
                   IC=fin_value(flip['initialCash'] * -1), YR1=yr[1], YR2=yr[2], YR3=yr[3], YR4=yr[4], YR5=yr[5],

                   OE1=oe[1], OE2=oe[2], OE3=oe[3], OE4=oe[4], OE5=oe[5],
                   L1=loan[1], L2=loan[2], L3=loan[3], L4=loan[4], L5=loan[5],

                   OF1=opcash[1], OF2=opcash[2], OF3=opcash[3], OF4=opcash[4], OF5=opcash[5],
                   NSP=fin_value(flip["financialProjectionSummary"]['netSalePrice']),
                   LB=fin_value(-1 * flip['mortgageBalanceRemaining']),
                   TDS=fin_value(flip['taxDueSale'] * -1),
                   TSP=fin_value(flip['afterTaxEquityReversion']),
                   ATP=fin_value(round(flip['afterTaxNetProfit'])),
                   BTP=fin_value(round(flip['beforeTaxNetProfit'])),
                   COI=fin_value(round(flip['costInvestmentBeforeTax'])),
                   BROI=rate_value((flip['beforeTaxIRR'])),
                   AROI=rate_value((flip['afterTaxIRR']))
                   )
    document.write(f'{out}.docx')


def figuresOnPDF(file, flip):
    befortax = flip["beforeTaxProfit"]
    aftertax = flip["afterTaxProfit"]
    x = [f"Year{i + 1}" for i in range((len(befortax)))]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=befortax,
                             mode='lines', name='Before Tax Profit',
                             line=dict(color='Green', width=6)
                             ))
    fig.add_trace(go.Scatter(x=x, y=aftertax,
                             mode='lines', name="After Tax Profit",
                             line=dict(color='royalblue', width=6)))

    if len(befortax) > 15:
        tickvals = [i for i, item in enumerate(befortax) if i % 2 == 0]
    else:
        tickvals = [i for i, item in enumerate(befortax)]

    fig.update_layout(
        autosize=False,
        width=900,
        height=450,
        margin=dict(l=0, r=0, b=0, t=0, pad=2),
        yaxis=dict(
            title_text="Dollars",
            showline=True,
            showgrid=True,
        ),
        plot_bgcolor='#ffffff',
        xaxis=dict(
            showline=True,
            showgrid=True,
            showticklabels=True,
            linecolor='rgb(204, 204, 204)',
            linewidth=2,
            ticks='outside',
            tickfont=dict(
                family='Arial',
                size=12,
                color='rgb(82, 82, 82)',
            ),
            tickmode='array',
            tickvals=tickvals,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        )
    )
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#dddddd')

    fig.write_image(f"{file}.png", width=900)

    pdf = FPDF(orientation='P', unit='in', format='Letter')
    pdf.set_margins(left=1, top=1, right=1)
    pdf.add_page()
    pdf.image(f'{file}.png', x=1, y=6.45, w=6.6, h=2.9)
    pdf.output(f'{file}.pdf')
    os.remove(f'{file}.png')


def pdfToOut(file):
    os.rename(f'{file}.pdf', f'{file}Out.pdf')


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

    wordPopulate(f'{templateLocation}flipSummaryTemplate', f'{outLocation}flipSummary{id}', property_address,
                 pdfFileProperties, flip)
    word_to_pdf(f'{outLocation}flipSummary{id}')
    pdfToOut(f'{outLocation}flipSummary{id}')
    # figuresOnPDF(f'{outLocation}flipSummary{id}', flip)
    # overlay(f'{outLocation}budgetWhatIf{id}',f'{outLocation}budgetWhatIf{id}.png',f'{outLocation}budgetWhatIfOut{id}')
    maregePdf(f'{outLocation}flipSummary{id}Out', f'{outLocation}out{id}')
