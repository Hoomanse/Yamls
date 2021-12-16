from __future__ import print_function
from mailmerge import MailMerge
import plotly.graph_objects as go
from fpdf import FPDF
import PyPDF2 as pypdf
import json
import numpy_financial as npf
from PyPDF2 import PdfFileMerger, PdfFileReader

import os
from pdf_generator import word_to_pdf


def initialize():
    with open("../json/flip.json") as json_file:
        flip = json.load(json_file)
        flip = flip["data"]["flip"]
    with open("../json/primary.json") as json_file:
        private = json.load(json_file)
        private = private["data"]["privateUse"]
    with open("../json/budget.json") as json_file:
        budget = json.load(json_file)
        budget = budget["data"]["budgetUse"]
    with open("../json/rental.json") as json_file:
        rental = json.load(json_file)
        rental = rental["data"]["rental"]
    with open("../json/shortTerm.json") as json_file:
        shortTerm = json.load(json_file)
        shortTerm = shortTerm["data"]["shortTerm"]
    with open("../json/dashboard.json") as json_file:
        dashboard = json.load(json_file)
        dashboard = dashboard["data"]["benchmarkExtended"]
    return flip, private, budget, rental, shortTerm, dashboard


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


def wordPopulate(template, out, property_address, pdfFileProperties, rental, budget, shortTerm, flip, dashboard,
                 private, property):
    pageNumber = pdfFileProperties['pageStart']
    pagesTotalNumber = 5
    pdfFileProperties['tableContent'].update({pageNumber: 'Zillmeter’s Approach',
                                              pageNumber + 3: 'What is the Benchmark Investment?',
                                              pageNumber + 4: ' Key Financial Metrics in this investment'
                                              })
    pdfFileProperties['pageStart'] = pageNumber + pagesTotalNumber

    template = f'{template}.docx'
    document = MailMerge(template)
    document.merge(PG1=page_value(pageNumber),
                   PG2=page_value(pageNumber + 1),
                   PG3=page_value(pageNumber + 2),
                   PG4=page_value(pageNumber + 3),
                   PG5=page_value(pageNumber + 4)
                   )

    hp = rental['genericInput']['holdingPeriodAnnual']
    yr = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}
    principal = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}
    interest = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}
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
        years = [1, round(hp * 2 / 5), round(hp * 3 / 5), round(hp * 4 / 5), round(hp)]
    benchamrkCollectedInterest = rental['initialCash'] * (1 + rental['genericInput']['benchmark']) ** hp - rental[
        'initialCash']
    becnhamrkIncomeTax = benchamrkCollectedInterest * rental['genericInput']['capitalGainTaxRate']
    ##Currently our model only supprts the case for intertest to be reinvetsed
    for item in range(len(arrays)):
        yr[arrays[item]] = f'Year {years[item]}'

    BenchmarkATarrays = benchmarkCalculation(rental, flip, rental)

    ##filling up the word template
    formatteAddress = str(property['address']['formattedStreetAddress'][0]) + ', ' + str(
        property['address']['city']) + ', ' + str(property['address']['state']) + ', ' + str(
        property['address']['zipCode'])
    document.merge(ADR=property_address,
                   HP=str(rental['genericInput']['holdingPeriodAnnual']),
                   DISR=rate_value(rental['genericInput']['discountRate']),
                   ADRS=formatteAddress,
                   ###Benchmark tables values
                   IC=fin_value(rental['initialCash'] * -1),
                   BR=rate_value(rental['genericInput']['benchmark']),
                   YR1=yr[1], YR2=yr[2], YR3=yr[3], YR4=yr[4], YR5=yr[5],
                   IN1='-', IN2='-', IN3='-', IN4='-', IN5=fin_value(rental['initialCash']),
                   OE1='-', OE2='-', OE3='-', OE4='-', OE5=fin_value(benchamrkCollectedInterest),
                   IT1='-', IT2='-', IT3='-', IT4='-', IT5=fin_value(becnhamrkIncomeTax * -1),
                   OF1='-', OF2='-', OF3='-', OF4='-',
                   OF5=fin_value(rental['initialCash'] + benchamrkCollectedInterest - becnhamrkIncomeTax),
                   ## Yeild table
                   BBR=rate_value(rental['genericInput']['benchmark']),
                   ABR=rate_value(BenchmarkATarrays['AfterTaxIRR'][rental['genericInput']['holdingPeriodAnnual']]),
                   BBRR=rate_value(budget['beforeTaxIRR']),
                   ABRR=rate_value(budget['afterTaxIRR']),
                   BPRR=rate_value(private['beforeTaxIRR']),
                   APRR=rate_value(private['afterTaxIRR']),
                   BRR=rate_value(rental['beforeTaxIRR']),
                   ARR=rate_value(rental['afterTaxIRR']),
                   BVRR=rate_value(shortTerm['beforeTaxIRR']),
                   AVRR=rate_value(shortTerm['afterTaxIRR']),
                   BFR=rate_value(flip['beforeTaxIRR']),
                   AFR=rate_value(flip['afterTaxIRR']),

                   ## profit table
                   BBPV=fin_value(dashboard['benchmarkDto']['benchmarkProfit']),
                   ABPV=fin_value(BenchmarkATarrays['AfterTaxNPV'][rental['genericInput']['holdingPeriodAnnual']]),
                   BVRPV=fin_value(shortTerm['beforeTaxNetProfit']),
                   AVRPV=fin_value(shortTerm['cashFlowProjection']['netProfitAfterTax']),
                   BRPV=fin_value(rental['beforeTaxNetProfit']),
                   ARPV=fin_value(rental['cashFlowProjection']['netProfitAfterTax']),
                   BPPV=fin_value(private['beforeTaxNetProfit']),
                   APPV=fin_value(private['cashFlowProjection']['netProfitAfterTax']),
                   BBRPV=fin_value(budget['beforeTaxNetProfit']),
                   ABRPV=fin_value(budget['cashFlowProjection']['netProfitAfterTax']),
                   BSBPV=fin_value(BenchmarkATarrays['BeforeTaxOneYearNPV']),
                   ASBPV=fin_value(BenchmarkATarrays['AfterTaxOneYearNPV']),
                   BFPV=fin_value(flip['beforeTaxNetProfit']),
                   AFPV=fin_value(flip['afterTaxNetProfit']))

    document.write(f'{out}.docx')


def lineFigure(file, befortax, aftertax):
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
        height=500,
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

    fig.write_image(f"{file}.png", width=900, height=500)


def benchmarkCalculation(rentalJSON, flip, rental):
    capitalGainTaxRate = rentalJSON['genericInput']['capitalGainTaxRate']
    initialCash = rentalJSON['initialCash']
    benchmarkRate = rentalJSON['genericInput']['benchmark']
    discountRate = rentalJSON['genericInput']['discountRate']
    flipCash = flip['initialCash']
    AfterTaxIRR = []
    AfterTaxNPV = []
    BeforeTaxNPV = []
    BeforeTaxIRR = []
    ATcashFlow = [initialCash * (1 + benchmarkRate) ** item - capitalGainTaxRate * (
            initialCash * (1 + benchmarkRate) ** item - initialCash) for item in range(0, 31)]

    for item in range(0, 31):
        BeforeTaxNPV.append(initialCash * (1 + benchmarkRate) ** item / (1 + discountRate) ** item - initialCash)
        BeforeTaxIRR.append(benchmarkRate)
        AfterTaxNPV.append((initialCash * (1 + benchmarkRate) ** item - (
                initialCash * (1 + benchmarkRate) ** item - initialCash) * (capitalGainTaxRate)) / (
                                   1 + discountRate) ** item - initialCash)
        AfterTaxIRR.append((1 + benchmarkRate) / (1 + discountRate) - 1)

    BenchmarkATarrays = {'AfterTaxIRR': AfterTaxIRR,
                         'AfterTaxNPV': AfterTaxNPV,
                         'BeforeTaxIRR': BeforeTaxIRR,
                         'BeforeTaxNPV': BeforeTaxNPV,
                         'BeforeTaxOneYearNPV': flipCash * (1 + benchmarkRate) / (1 + discountRate) - flipCash,
                         'AfterTaxOneYearNPV': ((flipCash * (1 + benchmarkRate) - (
                                 flipCash * (1 + benchmarkRate) - flipCash) * (
                                                     rental['genericInput']['taxRate'])) / (
                                                        1 + discountRate) - flipCash)}

    return BenchmarkATarrays


def npv_chart(values, filename):
    befortax = values['befortax']
    aftertax = values['aftertax']
    holding_period = values['holding_period']
    afterTax_profit = values['afterTax_profit']

    # find number of arrays to be shown
    x = [f"Year <br>{i + 1}<br>" for i in range((len(befortax)))]
    ##Values to be shown on the Y ax

    numberGap = 5
    maxYtickValue = (round(max(max(befortax), max(aftertax)) / 50000)) * 50000
    if maxYtickValue < 500000:
        yTickGap = round(maxYtickValue / (numberGap * 5000) + 1) * 5000
    elif maxYtickValue < 1000000:
        yTickGap = round(maxYtickValue / (numberGap * 10000) + 1) * 10000
    else:
        yTickGap = round(maxYtickValue / (numberGap * 50000) + 1) * 50000

    yTickValues = [yTickGap * item for item in range(0, numberGap + 1)]

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
    fig.update_yaxes(showgrid=True, gridwidth=.75, gridcolor='#dddddd')
    fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor='#dddddd')

    ## Add anotations

    fig.add_annotation(text=f'<b>Before and After Tax Generated Profit* (Adjusted for Inflation)<b>',
                       xref="paper", yref="paper", align='left',
                       x=-.05, y=.95, showarrow=False,
                       font=headerFont)
    fig.add_annotation(
        text=f'The after tax profit from the benchmark investment could be about {afterTax_profit}k in the year {holding_period[0]}.',
        xref="paper", yref="paper", align='left',
        x=-.05, y=.88, showarrow=False,
        font=headerFont2)

    fig.write_image(f"{filename}.png")


def figuresOnPDF(file, flip, rental):
    BenchmarkATarrays = benchmarkCalculation(rental, flip, rental)
    beforTaxNPV = BenchmarkATarrays['BeforeTaxNPV']
    afterTaxNPV = BenchmarkATarrays['AfterTaxNPV']
    afterTax_profit = fin_value(BenchmarkATarrays['AfterTaxNPV'][rental['genericInput']['holdingPeriodAnnual']] / 1000)

    netPresentValues = {'befortax': beforTaxNPV,
                        'aftertax': afterTaxNPV,
                        'holding_period': [rental['genericInput']['holdingPeriodAnnual']],
                        'afterTax_profit': afterTax_profit,
                        }
    ## calling the chart
    npv_chart(netPresentValues, file)

    pdf = FPDF(orientation='P', unit='in', format='Letter')
    pdf.set_margins(left=1, top=1, right=1)
    pdf.add_page()
    pdf.image(f'{file}.png', x=1, y=5.8, w=6.5, h=3.61)
    pdf.output(f'{file}.png.pdf')
    os.remove(f'{file}.png')


def overlay(infile, over, out):
    with open(f'{infile}.pdf', "rb") as inFile, open(f'{over}.pdf', "rb") as overlay:
        original = pypdf.PdfFileReader(inFile)
        background = original.getPage(3)
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


#

def maregePdf(inFile, outFile):
    pdf_file1 = PdfFileReader(f'{inFile}.pdf')
    pdf_file2 = PdfFileReader(f'{outFile}.pdf')
    output = PdfFileMerger()
    output.append(pdf_file2)
    output.append(pdf_file1)
    with open(f'{outFile}.pdf', "wb") as output_stream:
        output.write(output_stream)

    os.remove(f'{inFile}.pdf')


def main(pdfFileProperties, property):
    flip, private, budget, rental, shortTerm, dashboard = initialize()
    id = pdfFileProperties['id']
    templateLocation = pdfFileProperties['templateLocation']
    outLocation = pdfFileProperties['outLocation']
    property_address = pdfFileProperties['propertyAddress']

    wordPopulate(f'{templateLocation}zillmeterApproachTemplate', f'{outLocation}zillmeterApproach{id}',
                 property_address, pdfFileProperties, rental, budget, shortTerm, flip, dashboard, private, property)
    word_to_pdf(f'{outLocation}zillmeterApproach{id}')
    figuresOnPDF(f'{outLocation}zillmeterApproach{id}', flip, rental)
    overlay(f'{outLocation}zillmeterApproach{id}', f'{outLocation}zillmeterApproach{id}.png',
            f'{outLocation}zillmeterApproachOut{id}')
    maregePdf(f'{outLocation}zillmeterApproachOut{id}', f'{outLocation}out{id}')
