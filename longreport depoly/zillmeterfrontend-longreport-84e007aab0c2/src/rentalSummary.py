from __future__ import print_function
from mailmerge import MailMerge
import plotly.graph_objects as go
from fpdf import FPDF
import PyPDF2 as pypdf
from pdf_generator import word_to_pdf
import json
from PyPDF2 import PdfFileMerger, PdfFileReader
import os


def initialize():
    with open("../json/rental.json") as json_file:
        rental = json.load(json_file)
        rental = rental["data"]["rental"]
    return rental


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


def page_value(pageNum):
    return f'Page {pageNum}'


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


def wordPopulate(template, out, property_address, pdfFileProperties, rental):
    pageNumber = pdfFileProperties['pageStart']
    pagesTotalNumber = 1
    pdfFileProperties['tableContent'].update({pageNumber: 'Financial Projection Summary – Rental'})
    pdfFileProperties['pageStart'] = pageNumber + pagesTotalNumber

    template = f'{template}.docx'
    document = MailMerge(template)
    hp = rental['genericInput']['holdingPeriodAnnual']
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
        years = [1, round(hp * 2 / 5), round(hp * 3 / 5), round(hp * 4 / 5), round(hp * 5 / 5)]

    for item in range(len(arrays)):
        yr[arrays[item]] = f'Year {years[item]}'
        income[arrays[item]] = fin_value(rental['financialProjectionSummary']['income'][item])
        oe[arrays[item]] = fin_value(rental['financialProjectionSummary']['operationExpenses'][item])
        loan[arrays[item]] = fin_value(rental['financialProjectionSummary']['loanPayments'][item])
        itax[arrays[item]] = fin_value(
            rental["cashFlowProjection"]['cashFlowProjectionPurchased']['incomeTax'][item + 1])
        opcash[arrays[item]] = fin_value(rental['financialProjectionSummary']['operationNetCashFlow'][item + 1])
    document.merge(PG=page_value(pageNumber),
                   ADR=property_address,
                   HP=str(hp),
                   IC=fin_value(rental['initialCash'] * -1), YR1=yr[1], YR2=yr[2], YR3=yr[3], YR4=yr[4], YR5=yr[5],
                   IN1=income[1], IN2=income[2], IN3=income[3], IN4=income[4], IN5=income[5],
                   OE1=oe[1], OE2=oe[2], OE3=oe[3], OE4=oe[4], OE5=oe[5],
                   L1=loan[1], L2=loan[2], L3=loan[3], L4=loan[4], L5=loan[5],
                   IT1=itax[1], IT2=itax[2], IT3=itax[3], IT4=itax[4], IT5=itax[5],
                   OF1=opcash[1], OF2=opcash[2], OF3=opcash[3], OF4=opcash[4], OF5=opcash[5],
                   NSP=fin_value(rental["financialProjectionSummary"]['netSalePrice']),
                   LB=fin_value(-1 * rental['mortgageBalanceRemaining']),
                   TDS=fin_value(rental['taxProjection']['totalTaxDue'] * -1),
                   TSP=fin_value(rental['afterTaxEquityReversion'])
                   )
    document.write(f'{out}.docx')


def npv_chart(values, filename):
    befortax = values['befortax']
    aftertax = values['aftertax']
    afterTax_profit = values['afterTax_profit']
    holding_period = values['holding_period']

    # find number of arrays to be shown
    x = [f"Year <br>{i + 1}<br>" for i in range((len(befortax)))]
    ##Values to be shown on the Y ax

    numberGap = 5
    maxYtickValue = (round(max(max(befortax), max(aftertax)) / 50000)) * 50000
    minYtickValue = (round(min(min(befortax), min(aftertax)) / 50000)) * 50000
    minYtickValue = min(0, minYtickValue)

    if max(abs(maxYtickValue), abs(minYtickValue)) < 500000:
        yTickGap = round((maxYtickValue - minYtickValue) / (numberGap * 5000) + 1) * 5000
    elif maxYtickValue < 1000000:
        yTickGap = round((maxYtickValue - minYtickValue) / (numberGap * 10000) + 1) * 10000
    else:
        yTickGap = round((maxYtickValue - minYtickValue) / (numberGap * 50000) + 1) * 50000
    yTickValues = [((yTickGap * item) + minYtickValue) for item in range(0, numberGap + 1)]

    # Fonts:
    headerFont = dict(color='black', size=36, family='Arial')
    headerFont2 = dict(color='black', size=30, family='Arial')
    axesFont = dict(color='black', size=26, family='Arial')
    afterTaxColor = '#A9D18E'
    beforeTaxColor = '#C55A11'

    ## Figure, plotly scatter chart

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=befortax,
                             mode='lines', name='Before Tax Profit',
                             line=dict(color=beforeTaxColor, width=6)
                             ))
    fig.add_trace(go.Scatter(x=x, y=aftertax,
                             mode='lines', name="After Tax Profit",
                             line=dict(color=afterTaxColor, width=6)))

    if len(befortax) > 15:
        tickvals = [i for i, item in enumerate(befortax) if i % 2 == 1]
    else:
        tickvals = [i for i, item in enumerate(befortax)]

    fig.update_layout(
        autosize=False,
        width=1300,
        height=764,
        margin=dict(l=0, r=0, b=0, t=0, pad=0),
        paper_bgcolor="white",
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(
            title_text="Value are in Thousands",
            showline=True,
            linewidth=3,
            linecolor='#BFBFBF',
            showgrid=True,
            tickfont=axesFont,
            domain=[0, 0.78],
            titlefont=axesFont,
            tickvals=yTickValues,
            ticktext=[f'${int(round(item / 1000, 0)):,}' for item in yTickValues],

        ),
        xaxis=dict(
            showline=True,
            showgrid=True,
            showticklabels=True,
            linewidth=3,
            linecolor='#BFBFBF',
            ticks='outside',
            tickfont=axesFont,
            tickmode='array',
            tickvals=tickvals,
            titlefont=axesFont

        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=.75,
            xanchor="right",
            x=1,
            font=axesFont
        )
    )
    fig.update_yaxes(showgrid=True, gridwidth=.5, gridcolor='#dddddd')
    fig.update_yaxes(zeroline=True, zerolinewidth=2.5, zerolinecolor='#dddddd')

    ## Add anotations

    fig.add_annotation(text=f'<b>Before and After Tax Generated Profit* (Adjusted for Inflation)<b>',
                       xref="paper", yref="paper", align='left',
                       x=-.05, y=.95, showarrow=False,
                       font=headerFont)
    fig.add_annotation(
        text=f'The after tax profit from the investment is about {afterTax_profit}k in the year {holding_period}.',
        xref="paper", yref="paper", align='left',
        x=-.05, y=.88, showarrow=False,
        font=headerFont2)

    fig.write_image(f"{filename}.png")


def figuresOnPDF(file, rental):
    befortax = rental["beforeTaxProfit"]
    aftertax = rental["afterTaxProfit"]
    afterTax_profit = fin_value(2 * round(rental['beforeTaxNetProfit'] / 2000))
    holding_period = rental['genericInput']['holdingPeriodAnnual']

    netPresentValues = {'befortax': befortax,
                        'aftertax': aftertax,
                        'afterTax_profit': afterTax_profit,
                        'holding_period': holding_period
                        }
    ## calling the chart
    npv_chart(netPresentValues, file)

    pdf = FPDF(orientation='P', unit='in', format='Letter')
    pdf.set_margins(left=1, top=1, right=1)
    pdf.add_page()
    pdf.image(f'{file}.png', x=1, y=5.55, w=6.5, h=3.82)
    pdf.output(f'{file}.pdf')
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
    rental = initialize()
    id = pdfFileProperties['id']
    templateLocation = pdfFileProperties['templateLocation']
    outLocation = pdfFileProperties['outLocation']
    property_address = pdfFileProperties['propertyAddress']

    wordPopulate(f'{templateLocation}rentalSummaryTemplate', f'{outLocation}rentalSummary{id}', property_address,
                 pdfFileProperties, rental)
    word_to_pdf(f'{outLocation}rentalSummary{id}')
    figuresOnPDF(f'{outLocation}rentalSummary{id}.png', rental)
    overlay(f'{outLocation}rentalSummary{id}', f'{outLocation}rentalSummary{id}.png',
            f'{outLocation}rentalSummaryOut{id}')
    maregePdf(f'{outLocation}rentalSummaryOut{id}', f'{outLocation}out{id}')
