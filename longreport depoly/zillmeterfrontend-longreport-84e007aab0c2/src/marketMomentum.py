from __future__ import print_function
from mailmerge import MailMerge
import plotly.graph_objects as go
from fpdf import FPDF
import PyPDF2 as pypdf
from pdf_generator import word_to_pdf
import json
from PyPDF2 import PdfFileMerger, PdfFileReader
from datetime import date

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


def wordPopulate(template, out, property_address, pdfFileProperties, rental, property):
    pageNumber = pdfFileProperties['pageStart']
    pagesTotalNumber = 1
    pdfFileProperties['tableContent'].update({pageNumber: 'The Market Momentum (Future Projection)'})
    pdfFileProperties['pageStart'] = pageNumber + pagesTotalNumber

    template = f'{template}.docx'
    document = MailMerge(template)
    document.merge(PG=page_value(pageNumber))

    todays_date = date.today()
    todays_year = todays_date.year
    ##filling up the word template
    document.merge(ADR=property_address,
                   HP=str(rental['genericInput']['holdingPeriodAnnual']),
                   SYR=str(todays_year - 1 - rental['genericInput']['holdingPeriodAnnual']),
                   FYR=str(todays_year - 1),
                   ZP=str(property['address']['zipCode']),
                   TOWN=str(property['address']['city']),
                   HPR=rate_value(rental['genericInput']['propertyAppreciation']),
                   RPR=rate_value(rental['genericInput']['rentIncrease']),
                   GR=rate_value(rental['genericInput']['rentIncrease']),
                   BR=rate_value(rental['genericInput']['benchmark']),
                   UHR=rate_value(rental['genericInput']['propertyAppreciation']),
                   URR=rate_value(rental['genericInput']['rentIncrease']),
                   UIR=rate_value(rental['genericInput']['rentIncrease']),
                   UBR=rate_value(rental['genericInput']['benchmark'])
                   )
    document.write(f'{out}.docx')


def BarChart(values, filename):
    # set number of arrays to be shown based on the holding period

    ## Chart Variables
    years = values['years']
    appreciation = values['appreciation']
    rentIncrease = values['rentIncrease']
    infaltion = values['infaltion']

    ##Values to be shown on the Y ax

    # hedearfont:
    headerFont = dict(color='black', size=36, family='Arial')
    headerFont2 = dict(color='black', size=32, family='Arial')
    axesFont = dict(color='black', size=26, family='Arial')

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=years,
        y=rentIncrease,
        name='Rent Increase',
        orientation='v',
        marker=dict(
            color='#B4C7E7',
            line=dict(color='white', width=30 / len(years))
        )

    ))
    fig.add_trace(go.Bar(
        x=years,
        y=appreciation,
        name='Appreciation',
        orientation='v',
        marker=dict(
            color='#C5E0B4',
            line=dict(color='white', width=30 / len(years))
        )
    ))

    fig.add_trace(go.Bar(
        x=years,
        y=infaltion,
        name='Inflation',
        orientation='v',
        marker=dict(
            color='#FFB3B3',
            line=dict(color='white', width=30 / len(years))
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
            domain=[0, 0.8],
            ticksuffix="%",
            tickangle=0,
            tickfont=axesFont,
            title='Price Change',
            titlefont=axesFont
        ),
        legend=dict(

            y=.81,
            xanchor="right",
            yanchor="bottom",
            x=1,
            font=headerFont2,
            orientation="h"
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
    fig.add_annotation(text=f'<b>Anticipated Price Change<b>',
                       xref="paper", yref="paper", align='center',
                       x=0.5, y=.95, showarrow=False,
                       font=headerFont)

    fig.write_image(f'{filename}.png')

    # fig.show()


def figuresOnPDF(file, rental):
    pdf = FPDF(orientation='P', unit='in', format='Letter')
    pdf.set_margins(left=1, top=1, right=1)
    pdf.add_page()

    ## Bottom graph: find the number of years to be shown in the figure:
    hp = rental['genericInput']['holdingPeriodAnnual']

    if hp > 10:
        if hp % 2 == 0:
            years = [year * 2 for year in range(0, int(hp / 2) + 1)]
        else:
            years = [year * 2 + 1 for year in range(0, round(hp / 2) + 1)]
    else:
        years = [year for year in range(0, hp + 1)]
    appreciation = [((1 + rental['genericInput']['propertyAppreciation']) ** year - 1) * 100 for year in years]
    rentIncrease = [((1 + rental['genericInput']['rentIncrease']) ** year - 1) * 100 for year in years]
    infaltion = [((1 + rental['genericInput']['discountRate']) ** year - 1) * 100 for year in years]
    values = {'years': years, 'appreciation': appreciation,
              'rentIncrease': rentIncrease,
              'infaltion': infaltion}

    BarChart(values, file)
    pdf.image(f'{file}.png', x=1.40625, y=5.75, w=5.6, h=3.5)
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


def main(pdfFileProperties, property):
    rental = initialize()
    id = pdfFileProperties['id']
    templateLocation = pdfFileProperties['templateLocation']
    outLocation = pdfFileProperties['outLocation']
    property_address = pdfFileProperties['propertyAddress']

    wordPopulate(f'{templateLocation}marketMomentumTemplate', f'{outLocation}marketMomentum{id}', property_address,
                 pdfFileProperties, rental, property)
    word_to_pdf(f'{outLocation}marketMomentum{id}')
    figuresOnPDF(f'{outLocation}marketMomentum{id}', rental)
    overlay(f'{outLocation}marketMomentum{id}', f'{outLocation}marketMomentum{id}.png',
            f'{outLocation}marketMomentumOut{id}')
    maregePdf(f'{outLocation}marketMomentumOut{id}', f'{outLocation}out{id}')
