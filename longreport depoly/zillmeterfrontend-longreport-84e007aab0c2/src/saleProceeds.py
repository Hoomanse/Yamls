from __future__ import print_function
from mailmerge import MailMerge
import plotly.graph_objects as go
from fpdf import FPDF
import PyPDF2 as pypdf
import json
from PyPDF2 import PdfFileMerger, PdfFileReader
from datetime import date

from pdf_generator import word_to_pdf

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
    pdfFileProperties['tableContent'].update({pageNumber: 'Understand the Sale Proceeds'})
    pdfFileProperties['pageStart'] = pageNumber + pagesTotalNumber

    template = f'{template}.docx'
    document = MailMerge(template)
    document.merge(PG=page_value(pageNumber))

    todays_date = date.today()
    todays_year = todays_date.year
    ##filling up the word template
    document.merge(ADR=property_address,
                   HP=str(rental['genericInput']['holdingPeriodAnnual']),
                   PP=fin_value(rental['genericInput']['purchasePrice']),
                   IMPAD=fin_value(rental['genericInput']['improvementCost'] * (
                           1 + rental['genericInput']['addedValueRateImprovement'])),
                   ARV=fin_value(rental['genericInput']['purchasePrice'] + rental['genericInput']['improvementCost'] * (
                           1 + rental['genericInput']['addedValueRateImprovement'])),
                   UHR=rate_value(rental['genericInput']['propertyAppreciation']),
                   SP=fin_value(rental['taxProjection']['estimatedSalePrice']),
                   SE=fin_value(rental['taxProjection']['sellingExpenses'] * -1),
                   NSP=fin_value(rental['taxProjection']['netSalePrice']),
                   MRB=fin_value(rental['mortgageBalanceRemaining'] * -1),
                   BTSP=fin_value(rental['beforeTaxEquityReversion']),
                   SER=rate_value(rental['genericInput']['sellingExpensesRate']),
                   APRT=rate_value((1 + rental['genericInput']['propertyAppreciation']) ** rental['genericInput'][
                       'holdingPeriodAnnual'])
                   )
    document.write(f'{out}.docx')


def barChart(values, filename, rental):
    ## Chart Variables
    years = values['years']
    equity = values['equity']
    salePrice = values['salePrice']
    mortgageBalance = values['mortgageBalance']

    # hedearfont:
    headerFont = dict(color='black', size=36, family='Arial')
    headerFont2 = dict(color='black', size=30, family='Arial')
    axesFont = dict(color='black', size=26, family='Arial')

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=years,
        y=equity,
        name='Cash Contribution',
        orientation='v',
        fill='tonexty',
        mode='lines',
        marker=dict(
            color='#B4C7E7',
            line=dict(color='white', width=0)
        )

    ))
    fig.add_trace(go.Scatter(
        x=years,
        y=salePrice,
        name='Estimated Sale Price',
        orientation='v',
        mode='lines',
        line=dict(color='#C5E0B4', width=8),

    ))

    fig.add_trace(go.Scatter(
        x=years,
        y=mortgageBalance,
        name='Mortgage Balance',
        orientation='v',
        mode='lines',
        line=dict(color='#FF4343', width=8)
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
            domain=[0, 0.8],
            tickprefix="$",
            tickangle=0,
            tickfont=axesFont,
            title='',
            titlefont=axesFont
        ),
        legend=dict(

            y=.81,
            xanchor="right",
            yanchor="bottom",
            x=1,
            font=axesFont,
            orientation="v"
        ),
        # barmode='stack',
        showlegend=True,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="white",
        plot_bgcolor='rgba(0,0,0,0)',
        width=1300,
        height=800
    )

    # table header annotations
    addedEquity = fin_value(rental['beforeTaxEquityReversion'] - rental['initialCash'])

    fig.add_annotation(text=f'<b>Home Liquidation<b>',
                       xref="paper", yref="paper", align='left',
                       x=0, y=.97, showarrow=False,
                       font=headerFont)
    fig.add_annotation(text=f"Investor's Equity at the end of holding period is increased by {addedEquity}",
                       xref="paper", yref="paper", align='left',
                       x=0, y=.9, showarrow=False,
                       font=axesFont)

    fig.write_image(f'{filename}.png')

    # fig.show()


def figuresOnPDF(file, rental):
    pdf = FPDF(orientation='P', unit='in', format='Letter')
    pdf.set_margins(left=1, top=1, right=1)
    pdf.add_page()

    ### find arrays of equity, mortgageBlance, and Sale Price

    years = [year for year in range(0, rental['genericInput']['mortgageTerm'] + 1)]
    equity = [(rental['initialCash'] - rental['mortgage']['principal'][year]) for year in years[:-1]]
    equity.insert(0, rental['initialCash'])
    mortgageBalance = [(rental['genericInput']['purchasePrice'] * (1 - rental['genericInput']['downPaymentRate'])
                        + rental['mortgage']['principal'][year]) for year in years[:-1]]
    mortgageBalance.insert(0, rental['genericInput']['purchasePrice'] * (1 - rental['genericInput']['downPaymentRate']))
    salePrice = [(rental['genericInput']['purchasePrice'] +
                  ((rental['genericInput']['improvementCost'] * (
                          1 + rental['genericInput']['addedValueRateImprovement'])))) *
                 (1 + rental['genericInput']['propertyAppreciation']) ** year for year in years[:-1]]
    salePrice.insert(0, (rental['genericInput']['purchasePrice'] +
                         ((rental['genericInput']['improvementCost'] * (
                                 1 + rental['genericInput']['addedValueRateImprovement'])))))

    ##  show maxmimum 15 arrays on the bar Chart
    if rental['genericInput']['mortgageTerm'] != 15:
        for item in range(0, rental['genericInput']['mortgageTerm'] + 1):
            if item % 2 != 0:
                salePrice.pop(rental['genericInput']['mortgageTerm'] - item)
                mortgageBalance.pop(rental['genericInput']['mortgageTerm'] - item)
                equity.pop(rental['genericInput']['mortgageTerm'] - item)
                years.pop(rental['genericInput']['mortgageTerm'] - item)

    values = {'years': years, 'equity': equity,
              'salePrice': salePrice,
              'mortgageBalance': mortgageBalance}
    barChart(values, file, rental)
    pdf.image(f'{file}.png', x=1, y=5, w=6.5, h=4)
    os.remove(f'{file}.png')
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
    rental = initialize()
    id = pdfFileProperties['id']
    templateLocation = pdfFileProperties['templateLocation']
    outLocation = pdfFileProperties['outLocation']
    property_address = pdfFileProperties['propertyAddress']

    wordPopulate(f'{templateLocation}saleProceedsTemplate', f'{outLocation}saleProceeds{id}', property_address,
                 pdfFileProperties, rental)
    word_to_pdf(f'{outLocation}saleProceeds{id}')
    figuresOnPDF(f'{outLocation}saleProceeds{id}', rental)
    overlay(f'{outLocation}saleProceeds{id}', f'{outLocation}saleProceeds{id}.png', f'{outLocation}saleProceedsOut{id}')
    maregePdf(f'{outLocation}saleProceedsOut{id}', f'{outLocation}out{id}')
