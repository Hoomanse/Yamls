from __future__ import print_function
from mailmerge import MailMerge
import plotly.graph_objects as go
from fpdf import FPDF
import PyPDF2 as pypdf
import json
from PyPDF2 import PdfFileMerger, PdfFileReader
from pdf_generator import word_to_pdf

import os


def initialize():
    with open("../json/budget.json") as json_file:
        budget = json.load(json_file)
        budget = budget["data"]["budgetUse"]
    with open("../json/rental.json") as json_file:
        rental = json.load(json_file)
        rental = rental["data"]["rental"]
    return budget, rental

def fin_value(dollar_value):
    if dollar_value < 0:
        tor = f'{round(-1 * dollar_value):,}'
        tor = f'$({tor})'
    else:
        tor = f'${round(dollar_value):,}'
    return tor


def rate_value(rate):
    tor = round(rate * 100)
    return str(f'{tor}%')


def page_value(pageNum):
    return f'Page {pageNum}'


def wordPopulate(template, out, property_address, pdfFileProperties, rental):
    pageNumber = pdfFileProperties['pageStart']
    pagesTotalNumber = 1
    pdfFileProperties['tableContent'].update({pageNumber: 'Equity Build up Summary'})
    pdfFileProperties['pageStart'] = pageNumber + pagesTotalNumber

    template = f'{template}.docx'

    ##filling up the word template
    document = MailMerge(template)

    document.merge(PG=page_value(pageNumber))
    document.merge(ADR=property_address,
                   MA=fin_value(
                       rental['genericInput']['purchasePrice'] * (1 - rental['genericInput']['downPaymentRate'])),
                   HP=str(rental['genericInput']['holdingPeriodAnnual']),
                   MP=rate_value(1 - rental['mortgageBalanceRemaining'] / (rental['genericInput']['purchasePrice'] * (
                           1 - rental['genericInput']['downPaymentRate']))),
                   MT=str(rental['genericInput']['mortgageTerm']),
                   MIR=rate_value(rental['genericInput']['mortgageInterest']),
                   DS=fin_value(-1 * rental['monthlyDebtService'])),

    document.write(f'{out}.docx')


def mortage_table(interst, principal, start_year, filename):
    principal_value = principal
    interest_value = interst

    if start_year == 1:
        y = [i for i in range(1, 16)]
    else:
        y = [i for i in range(16, 31)]
        principal_value = principal[15:30]
        interest_value = interst[15:30]
        p = principal
        principal = interst[15:30]
        interst = p[15:30]
        principal.reverse()
        interst.reverse()

    # hedearfont:
    headerFont = dict(color='black', size=54, family='Arial')
    tableFont = dict(color='black', size=48, family='Arial')

    # headerOffset
    headerOffSet = 0.05

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=y,
        x=principal,
        name='principal',
        orientation='h',
        opacity=.4,
        marker=dict(
            color='#FFB3B3',
            line=dict(color='white', width=0)
        )
    ))
    fig.add_trace(go.Bar(
        y=y,
        x=interst,
        name='interst',
        orientation='h',
        opacity=.4,
        marker=dict(
            color='#B4C7E7',
            line=dict(color='white', width=0)
        )
    ))

    fig.update_layout(
        xaxis=dict(
            showgrid=False,
            showline=False,
            showticklabels=False,
            zeroline=False,
            domain=[.15, 1]
        ),
        yaxis=dict(
            showgrid=False,
            showline=False,
            showticklabels=False,
            zeroline=False,
            domain=[0, 1 - headerOffSet]
        ),
        barmode='stack',
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="white",
        plot_bgcolor='rgba(0,0,0,0)',
        width=1200,
        height=1600
    )
    vertical_location = [round((.98 - headerOffSet - (0.96 - headerOffSet) * (item) / (14)), 3) for item in range(15)]
    # print(vertical_location)
    vertical_location = [0.93, 0.865, 0.8, 0.739, 0.673, 0.605, 0.54, 0.475, 0.41, 0.35, 0.265, 0.205, 0.145, 0.085,
                         0.02]  ##Manualy adjusted!

    for item in range(15):
        fig.add_annotation(text=f'${round(interest_value[item]):,}',  # interst
                           xref="paper", yref="paper",
                           x=.25, y=vertical_location[item], showarrow=False,
                           font=tableFont)

        fig.add_annotation(text=f'${round(principal_value[item]):,}',  # principal
                           xref="paper", yref="paper",
                           x=.8, y=vertical_location[item], showarrow=False,
                           font=tableFont)

        fig.add_annotation(text=f'{y[item]}',  # Year
                           xref="paper", yref="paper",
                           x=0.02, y=vertical_location[item], showarrow=False,
                           font=tableFont)

    ##table header
    fig.add_annotation(text='<b>Year<b>',  # Year
                       xref="paper", yref="paper",
                       x=0, y=1, showarrow=False,
                       font=headerFont)
    fig.add_annotation(text='<b>Interest<b>',  # Interest
                       xref="paper", yref="paper",
                       x=0.25, y=1, showarrow=False,
                       font=headerFont)
    fig.add_annotation(text='<b>Principal<b>',  # Principal
                       xref="paper", yref="paper",
                       x=0.8, y=1, showarrow=False,
                       font=headerFont)

    fig.write_image(f'{filename}.png')


def equityBarChart(values, filename):
    years = values['years']
    debtValues = values['debtValues']
    contribution = values['contribution']
    sellingPrice = values['sellingPrice']
    apprecaition = values['apprecaition']
    apprRate = values['apprRate']
    imporvemntAddedValue = values['imporvemntAddedValue']
    improvementAllScenarios = values['improvementAllScenarios']
    holdingPeriod = values['holdingPeriod']

    # set number of arrays to be shown based on the holding period
    if holdingPeriod < 16:
        years = years[:16]
        debtValues = debtValues[:16]
        apprecaition = apprecaition[:16]
        sellingPrice = sellingPrice[:16]
    else:
        for item in range(30):
            if (30 - item) % 2 != 0:
                years.pop(30 - item)
                debtValues.pop(30 - item)
                contribution.pop(30 - item)
                apprecaition.pop(30 - item)
                sellingPrice.pop(30 - item)

    ## Chart Variables
    x = years
    y = debtValues
    z = contribution
    w = apprecaition

    ##Values to be shown on the Y ax

    numberGap = 5
    maxYtickValue = (round(max(sellingPrice) / 50000)) * 50000
    if maxYtickValue < 500000:
        yTickGap = round(maxYtickValue / (numberGap * 5000) + 1) * 5000
    elif maxYtickValue < 1000000:
        yTickGap = round(maxYtickValue / (numberGap * 10000) + 1) * 10000
    else:
        yTickGap = round(maxYtickValue / (numberGap * 50000) + 1) * 50000

    yTickValues = [yTickGap * item for item in range(0, numberGap + 1)]

    # hedearfont:
    headerFont = dict(color='black', size=36, family='Arial')
    headerFont2 = dict(color='black', size=30, family='Arial')
    axesFont = dict(color='black', size=26, family='Arial')

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=years,
        y=sellingPrice,
        name='Selling Price',
        mode='lines',
        line=dict(
            color='#7F7F7F', width=10
        )
    ))

    fig.add_trace(go.Bar(
        x=years,
        y=debtValues,
        name='Debt',
        orientation='v',
        marker=dict(
            color='#FFB3B3',
            line=dict(color='white', width=0)
        )
    ))
    fig.add_trace(go.Bar(
        x=years,
        y=contribution,
        name='Contributed Equity',
        orientation='v',
        marker=dict(
            color='#B4C7E7',
            line=dict(color='white', width=0.05)
        )
    ))

    fig.add_trace(go.Bar(
        x=years,
        y=apprecaition,
        name='Appreciation',
        orientation='v',
        marker=dict(
            color='#C5E0B4',
            line=dict(color='white', width=0.05)
        )
    ))
    fig.update_layout(
        xaxis=dict(
            showgrid=True,
            showline=True,
            showticklabels=True,
            linewidth=3,
            linecolor='#BFBFBF',
            zeroline=True,
            ticktext=[f'Year <br>{item}<br>' for item in years],
            tickvals=years,
            domain=[0, 1],
            tickangle=0,
            tickfont=axesFont,

        ),

        yaxis=dict(
            showgrid=False,
            showline=True,
            linewidth=3,
            linecolor='#BFBFBF',
            showticklabels=True,
            zeroline=True,
            domain=[0, 0.7],
            ticktext=[f'${int(round(item / 1000, 0)):,}' for item in yTickValues],
            tickvals=yTickValues,
            tickangle=0,
            tickfont=axesFont,
            title='Value are in Thousands',
            titlefont=axesFont
        ),
        legend=dict(
            yanchor="top",
            y=0.93,
            xanchor="left",
            x=0.7,
            font=axesFont
        ),
        barmode='stack',
        showlegend=True,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="white",
        plot_bgcolor='rgba(0,0,0,0)',
        width=1300,
        height=800
    )

    # table header annotations
    fig.add_annotation(text=f'<b>Home Liquiditation<b>',
                       xref="paper", yref="paper", align='left',
                       x=0.01, y=.9, showarrow=False,
                       font=headerFont)

    if values['improvementAllScenarios'] == True:
        fig.add_annotation(text=f'Assumptions:'
                                f'<br>1) Remodeling adds to {fin_value(imporvemntAddedValue)} home value<br>'
                                f'2) Home value appreciates {rate_value(apprRate)} annualy',
                           xref="paper", yref="paper", align='left',
                           x=0.01, y=.85, showarrow=False,
                           font=headerFont2)
    else:
        fig.add_annotation(text=f'Assumption:'
                                f'<br>1) Home value apprecaites {rate_value(apprRate)} annualy',
                           xref="paper", yref="paper", align='left',
                           x=0.01, y=.85, showarrow=False,
                           font=headerFont2)

    fig.write_image(f'{filename}bottom.png')

    # fig.show()


def figuresOnPDF(file, budget, rental):
    #
    interest = budget['mortgage']['interest']
    principal = budget['mortgage']['principal']
    intersetPaid = []
    principalPaid = []
    for item in range(len(interest)):
        if item == 0:
            intersetPaid.append(interest[0] * -1)
            principalPaid.append(principal[0] * -1)
        else:
            intersetPaid.append(interest[item] * -1 + interest[item - 1])
            principalPaid.append(principal[item] * -1 + principal[item - 1])

    mortage_table(intersetPaid, principalPaid, 1, file)
    pdf = FPDF(orientation='P', unit='in', format='Letter')
    pdf.set_margins(left=1, top=1, right=1)
    pdf.add_page()
    pdf.image(f'{file}.png', x=1, y=2.5, w=3, h=4)
    # pdf.output(f'{file}.png.pdf')
    os.remove(f'{file}.png')

    if rental['genericInput']['mortgageTerm'] == 30:
        mortage_table(intersetPaid, principalPaid, 15, file + '30')
        pdf.image(f'{file}30.png', x=4.5, y=2.5, w=3, h=4)
        # pdf.output(f'{file}.png.pdf')
        os.remove(f'{file}30.png')

    ## Bottom graph

    ## Add a slice for the year=0 to every array
    years = [item for item in range(0, 31)]
    debtValues = [(1 - rental['genericInput']['downPaymentRate']) * (rental['genericInput']['purchasePrice'])] + \
                 rental['mortgage']['mortgageBalance']
    contribution = [(rental['initialCash'] - item) for item in ([0] + rental['mortgage']['principal'])]

    ## Check if selling price should be estimated based on the improvemenet for all scenarios
    if rental['genericInput']['applyImprovementAllScenarios'] == True:
        sellingPrice = [((rental['genericInput']['purchasePrice'] + rental['genericInput']['improvementCost'] * (
                1 + rental['genericInput']['addedValueRateImprovement']))
                         * (1 + rental['genericInput']['propertyAppreciation']) ** (item)) for item in years]
    else:
        sellingPrice = [((rental['genericInput']['purchasePrice'])
                         * (1 + rental['genericInput']['propertyAppreciation']) ** (item)) for item in years]
    ## Find the list of added values to the property price over time
    apprecaition = []
    for item in range(len(years)):
        apprecaition.append(sellingPrice[item] - contribution[item] - debtValues[item])

    EquityChartvalues = {'years': years,
                         'debtValues': debtValues,
                         'contribution': contribution,
                         'sellingPrice': sellingPrice,
                         'apprRate': (rental['genericInput']['propertyAppreciation']),
                         'apprecaition': apprecaition,
                         'imporvemntAddedValue': round(
                             rental['genericInput']['improvementCost'] * (
                                     1 + rental['genericInput']['addedValueRateImprovement'])),
                         'improvementAllScenarios': rental['genericInput']['applyImprovementAllScenarios'],
                         'holdingPeriod': rental['genericInput']['holdingPeriodAnnual']
                         }
    equityBarChart(EquityChartvalues, file)
    pdf.image(f'{file}bottom.png', x=1.1625, y=6.47, w=6.175, h=3.8)
    os.remove(f'{file}bottom.png')
    pdf.output(f'{file}.png.pdf')


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
    budget, rental = initialize()
    id = pdfFileProperties['id']
    templateLocation = pdfFileProperties['templateLocation']
    outLocation = pdfFileProperties['outLocation']
    property_address = pdfFileProperties['propertyAddress']

    wordPopulate(f'{templateLocation}equitySummaryTemplate', f'{outLocation}equitySummary{id}', property_address,
                 pdfFileProperties, rental)
    word_to_pdf(f'{outLocation}equitySummary{id}')
    figuresOnPDF(f'{outLocation}equitySummary{id}', budget, rental)
    overlay(f'{outLocation}equitySummary{id}', f'{outLocation}equitySummary{id}.png',
            f'{outLocation}equitySummaryOut{id}')
    maregePdf(f'{outLocation}equitySummaryOut{id}', f'{outLocation}out{id}')
