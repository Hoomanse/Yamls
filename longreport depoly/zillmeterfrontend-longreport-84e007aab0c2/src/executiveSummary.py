from __future__ import print_function
from mailmerge import MailMerge
import plotly.graph_objects as go
from fpdf import FPDF
import PyPDF2 as pypdf
from PyPDF2 import PdfFileMerger, PdfFileReader
import numpy_financial as npf
import json
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

    return flip, private, budget, rental, shortTerm


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


def wordPopulate(template, out, property_address, pdfFileProperties, shortTerm, rental, budget, private, flip):
    pageNumber = pdfFileProperties['pageStart']
    pagesTotalNumber = 1
    pdfFileProperties['tableContent'].update({pageNumber: 'Financial Executive Summary'})
    pdfFileProperties['pageStart'] = pageNumber + pagesTotalNumber

    template = f'{template}.docx'

    ##finding the maximum profitable scenario
    scenarios = [shortTerm, rental, budget, private, flip]
    scenarios_str = ['Vacation Rental', 'Rental', 'Budget Residence', 'Primary Residence', 'Flip']
    beforeTaxIrr = [item['beforeTaxIRR'] for item in scenarios]
    irrMax = max(beforeTaxIrr)

    ##filling up the word template
    benchmarkArrays = benchmarkCalculation(rental, rental, flip)

    bennchmarkAfterTaxNPV = benchmarkArrays['AfterTaxNPV']
    bennchmarkBeforeTaxNPV = benchmarkArrays['BeforeTaxNPV']

    document = MailMerge(template)
    document.merge(PG=page_value(pageNumber))

    document.merge(ADR=property_address,
                   IC=fin_value(rental['initialCash']),
                   BR=rate_value(rental['genericInput']['benchmark']),
                   HP=str(rental['genericInput']['holdingPeriodAnnual']),
                   MIRR=rate_value(irrMax),
                   MSC=scenarios_str[beforeTaxIrr.index(irrMax)],
                   BBPV=fin_value(bennchmarkBeforeTaxNPV[int(rental['genericInput']['holdingPeriodAnnual'] - 1)]),
                   ABPV=fin_value(bennchmarkAfterTaxNPV[int(rental['genericInput']['holdingPeriodAnnual'] - 1)]),
                   BVRPV=fin_value(shortTerm['beforeTaxNetProfit']),
                   AVRPV=fin_value(shortTerm['cashFlowProjection']['netProfitAfterTax']),
                   BRPV=fin_value(rental['beforeTaxNetProfit']),
                   ARPV=fin_value(rental['cashFlowProjection']['netProfitAfterTax']),
                   BPPV=fin_value(private['beforeTaxNetProfit']),
                   APPV=fin_value(private['cashFlowProjection']['netProfitAfterTax']),
                   BBRPV=fin_value(budget['beforeTaxNetProfit']),
                   ABRPV=fin_value(budget['cashFlowProjection']['netProfitAfterTax']),
                   BSBPV=fin_value(benchmarkArrays['BeforeTaxOneYearNPV']),
                   ASBPV=fin_value(benchmarkArrays['AfterTaxOneYearNPV']),
                   BFPV=fin_value(flip['beforeTaxNetProfit']),
                   AFPV=fin_value(flip['afterTaxNetProfit']),
                   ICR=fin_value(flip['initialCash'])
                   )
    document.write(f'{out}.docx')


def bar_chart(file, values):
    # top_labels = ['Down Payment', 'Transaction Cost', 'Remodeling']

    colors = ['rgba(180, 199, 231, 0.8)', 'rgba(255, 163, 163, 0.8)',
              'rgba(165, 165, 165, 0.8)']
    names = ['Down Payment', 'Purchase Expenses', 'Remodeling']
    y_data = ['']
    fig = go.Figure()

    if values[2] == 0:
        values = values[0:2]
        names = names[0:2]
        fig.add_trace(
            go.Bar(y=y_data, x=[values[0]], width=0.6, text=f'${values[0]}K', textposition='inside', orientation='h',
                   name=names[0], marker=dict(color=colors[0])))
        fig.add_trace(
            go.Bar(y=y_data, x=[values[1]], width=0.6, text=f'${values[1]}K', textposition='inside', orientation='h',
                   name=names[1], marker=dict(color=colors[1])))
    else:
        fig.add_trace(
            go.Bar(y=y_data, x=[values[0]], width=0.6, text=f'${values[0]}K', textposition='inside', orientation='h',
                   name=names[0], marker=dict(color=colors[0])))
        fig.add_trace(
            go.Bar(y=y_data, x=[values[1]], width=0.6, text=f'${values[1]}K', textposition='inside', orientation='h',
                   name=names[1], marker=dict(color=colors[1])))
        fig.add_trace(
            go.Bar(y=y_data, x=[values[2]], width=0.6, text=f'${values[2]}K', textposition='inside', orientation='h',
                   name=names[2], marker=dict(color=colors[2])))

    fig.update_layout(
        xaxis=dict(
            showgrid=False,
            showline=False,
            showticklabels=False,
            zeroline=False,
            domain=[0, 1]
        ),
        yaxis=dict(
            showgrid=False,
            showline=False,
            showticklabels=False,
            zeroline=False,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1,
            xanchor="right",
            x=.95,
            font=dict(
                size=22)

        ),
        barmode='stack',
        paper_bgcolor='rgb(260, 260, 260,0)',
        plot_bgcolor='rgb(260, 260, 260,0)',

        showlegend=True,
    )
    fig.update_layout(uniformtext_minsize=22, uniformtext_mode='show', barmode='stack', margin=dict(l=0, r=0, t=0, b=0),
                      legend={'traceorder': 'normal'})
    # fig.show()
    fig.write_image(f'{file}.png', width=1300, height=100)


def bar_chart_2nd(file, values):
    # top_labels = ['Down Payment', 'Transaction Cost', 'Remodeling']

    colors = ['rgba(180, 199, 231, 0.8)', 'rgba(255, 163, 163, 0.8)',
              'rgba(165, 165, 165, 0.8)']
    names = ['Down Payment', 'Purchase Expenses', 'Remodeling']
    y_data = ['']
    fig = go.Figure()

    if values[2] == 0:
        values = values[0:2]
        names = names[0:2]
        fig.add_trace(
            go.Bar(y=y_data, x=[values[0]], width=0.6, text=f'${values[0]}K', textposition='inside', orientation='h',
                   name=names[0], marker=dict(color=colors[0])))
        fig.add_trace(
            go.Bar(y=y_data, x=[values[1]], width=0.6, text=f'${values[1]}K', textposition='inside', orientation='h',
                   name=names[1], marker=dict(color=colors[1])))
    else:
        fig.add_trace(
            go.Bar(y=y_data, x=[values[0]], width=0.6, text=f'${values[0]}K', textposition='inside', orientation='h',
                   name=names[0], marker=dict(color=colors[0])))
        fig.add_trace(
            go.Bar(y=y_data, x=[values[1]], width=0.6, text=f'${values[1]}K', textposition='inside', orientation='h',
                   name=names[1], marker=dict(color=colors[1])))
        fig.add_trace(
            go.Bar(y=y_data, x=[values[2]], width=0.6, text=f'${values[2]}K', textposition='inside', orientation='h',
                   name=names[2], marker=dict(color=colors[2])))

    fig.update_layout(
        xaxis=dict(
            showgrid=False,
            showline=False,
            showticklabels=False,
            zeroline=False,
            domain=[0, 1]
        ),
        yaxis=dict(
            showgrid=False,
            showline=False,
            showticklabels=False,
            zeroline=False,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1,
            xanchor="right",
            x=.95,
            font=dict(
                size=22)

        ),
        barmode='stack',
        paper_bgcolor='rgb(260, 260, 260,0)',
        plot_bgcolor='rgb(260, 260, 260,0)',

        showlegend=True,
    )
    fig.update_layout(uniformtext_minsize=22, uniformtext_mode='show', barmode='stack', margin=dict(l=0, r=0, t=0, b=0),
                      legend={'traceorder': 'normal'})
    # fig.show()
    fig.write_image(f'{file}2nd.png', width=1300, height=100)


def figuresOnPDF(file, rental, flip):
    # values are ['Down Payment', 'Purchase Expense', 'Remodeling']
    values = [round(rental['downPayment'] / 1000), round(rental['purchaseExpense'] / 1000),
              round(rental['genericInput']['improvementCost'] / 1000)]
    bar_chart(file, values)
    pdf = FPDF(orientation='P', unit='in', format='Letter')
    pdf.set_margins(left=1, top=1, right=1)
    pdf.add_page()
    if flip['genericInput']['applyImprovementAllScenarios'] == True:
        pdf.image(f'{file}.png', x=1, y=2, w=6.825, h=.525)
        pdf.output(f'{file}.png.pdf')
        os.remove(f'{file}.png')
    else:
        pdf.image(f'{file}.png', x=1, y=1.65, w=6.825, h=.525)
        # pdf.output(f'{file}.png.pdf')
        os.remove(f'{file}.png')

        ## 2nd bar chart
        # values are ['Down Payment', 'Purchase Expense', 'Remodeling']

        values = [round(rental['downPayment'] / 1000), round(rental['purchaseExpense'] / 1000),
                  round(flip['genericInput']['improvementCost'] / 1000)]
        bar_chart_2nd(file, values)

        pdf.image(f'{file}2nd.png', x=1, y=2.45, w=6.825, h=.525)
        os.remove(f'{file}2nd.png')
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


# def benchmarkCalculation(rentalJSON):
#
#     capitalGainTaxRate=rentalJSON['genericInput']['capitalGainTaxRate']
#     initialCash=rentalJSON['initialCash']
#     benchmarkRate=rentalJSON['genericInput']['benchmark']
#     intertestEndYear=[initialCash*(1+benchmarkRate)**item-initialCash for item in range (0,31)]
#     BTcashFlow=[initialCash*(1+benchmarkRate)**item for item in range (0,31)]
#     ATcashFlow=[initialCash*(1+benchmarkRate)**item-capitalGainTaxRate*(initialCash*(1+benchmarkRate)**item-initialCash) for item in range (0,31)]
#     TAXcashFlow=[capitalGainTaxRate*(initialCash*(1+benchmarkRate)**item-initialCash) for item in range (0,31)]
#     AfterTaxIRR=[]
#     AfterTaxNPV=[]
#     discountRate=rentalJSON['genericInput']['discountRate']
#
#
#     for item in range(1,31):
#         AfterTaxCashFlow=[0*each_value for each_value in range(0,item+1)]
#         AfterTaxCashFlow[0]=initialCash*-1
#         AfterTaxCashFlow[-1]=ATcashFlow[item]
#         AfterTaxIRR.append(npf.irr(AfterTaxCashFlow))
#         AfterTaxNPV.append(npf.npv(discountRate,AfterTaxCashFlow))
#
#     BenchmarkATarrays= {'AfterTaxIRR':AfterTaxIRR,'AfterTaxNPV':AfterTaxNPV}
#
#     return BenchmarkATarrays

def benchmarkCalculation(rentalJSON, rental, flip):
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

    for item in range(1, 31):
        BeforeTaxNPV.append(initialCash * (1 + benchmarkRate) ** item / (1 + discountRate) ** item - initialCash)
        BeforeTaxIRR.append(benchmarkRate)
        AfterTaxNPV.append((initialCash * (1 + benchmarkRate) ** item - (
                initialCash * (1 + benchmarkRate) ** item - initialCash) * (capitalGainTaxRate)) / (
                                   1 + discountRate) ** item - initialCash)
        AfterTaxCashFlow = [0 * each_value for each_value in range(0, item + 1)]
        AfterTaxIRR.append(npf.irr(AfterTaxCashFlow))

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


def maregePdf(inFile, outFile):
    pdf_file1 = PdfFileReader(f'{inFile}.pdf')
    pdf_file2 = PdfFileReader(f'{outFile}.pdf')
    output = PdfFileMerger()
    output.append(pdf_file2)
    output.append(pdf_file1)
    with open(f'{outFile}.pdf', "wb") as output_stream:
        output.write(output_stream)

    os.remove(f'{inFile}.pdf')


def template_selector(templateLocation, flip):
    if flip['genericInput']['applyImprovementAllScenarios'] == True:
        return f'{templateLocation}executiveSummaryTemplate'
    else:
        return f'{templateLocation}executiveSummaryNotRemodeledTemplate'


def main(pdfFileProperties):
    flip, private, budget, rental, shortTerm = initialize()
    id = pdfFileProperties['id']
    templateLocation = pdfFileProperties['templateLocation']
    outLocation = pdfFileProperties['outLocation']
    property_address = pdfFileProperties['propertyAddress']
    word_template = template_selector(templateLocation, flip)

    wordPopulate(word_template, f'{outLocation}executiveSummary{id}', property_address, pdfFileProperties, shortTerm,
                 rental, budget, private, flip)
    word_to_pdf(f'{outLocation}executiveSummary{id}')
    figuresOnPDF(f'{outLocation}executiveSummary{id}', rental, flip)
    overlay(f'{outLocation}executiveSummary{id}', f'{outLocation}executiveSummary{id}.png',
            f'{outLocation}executiveSummaryOut{id}')
    maregePdf(f'{outLocation}executiveSummaryOut{id}', f'{outLocation}out{id}')
