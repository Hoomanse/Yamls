from __future__ import print_function
from mailmerge import MailMerge
from fpdf import FPDF
import PyPDF2 as pypdf
import json
from matplotlib import pyplot as plt
from PyPDF2 import PdfFileMerger, PdfFileReader
import os
from pdf_generator import word_to_pdf


def initialize():
    with open("../json/rental.json") as json_file:
        rental = json.load(json_file)
        rental = rental["data"]["rental"]

    with open("../json/budget.json") as json_file:
        budget = json.load(json_file)
        budget = budget["data"]["budgetUse"]
    return rental, budget


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


def wordPopulate(template, out, property_address, pdfFileProperties, rental, budget):
    pageNumber = pdfFileProperties['pageStart']
    pagesTotalNumber = 4
    pdfFileProperties['tableContent'].update({pageNumber: 'Appendix 1- A Guide to Tax Calculation'})
    pdfFileProperties['pageStart'] = pageNumber + pagesTotalNumber

    template = f'{template}.docx'
    document = MailMerge(template)
    document.merge(PG1=page_value(pageNumber),
                   PG2=page_value(pageNumber + 1),
                   PG3=page_value(pageNumber + 2),
                   PG4=page_value(pageNumber + 3))

    ##there is an issue on the backend with the tax calc (it's passing the item # 0 instead of #1 so it's always null
    interestPaid = rental['mortgage']['interest'][0]
    hp = rental['genericInput']['holdingPeriodAnnual']

    taxableIncome = rental['taxProjection']['netOperatingIncome'] + rental['taxProjection'][
        'taxDepreciationRecapture'] / rental['genericInput']['depreciationRecaptureRate'] / hp * -1 + interestPaid
    taxPayable = rental['genericInput']['taxRate'] * taxableIncome
    taxableIncome = max(taxableIncome, 0)
    taxPayable = min(0, taxPayable * -1)

    document.merge(ADR=property_address)
    if taxableIncome == 0:
        passiveLoss = fin_value(
            -1 * rental['mortgage']['interest'][0] + rental['depreciationRecapture'] / rental['genericInput'][
                'holdingPeriodAnnual'] - rental['taxProjection']['netOperatingIncome'])
        taxNote = f'In the first year of renting this property, deductions surpluses income which it means the taxable income would be $0 and the passive loss would be {passiveLoss}. Zillmeter assumes the passive loss could be carried over to the next years'
    else:
        taxNote = ''
    adjustedBasis = rental['genericInput']['purchasePrice'] * (1 + rental['genericInput']['purchaseExpenseRate']) + \
                    rental['genericInput']['improvementCost'] - rental['taxProjection']['taxDepreciationRecapture'] / \
                    rental['genericInput']['depreciationRecaptureRate']

    cust_1 = {'ADR': property_address,
              'DEPYR': fin_value(rental['depreciationRecapture'] / rental['genericInput']['holdingPeriodAnnual']),
              'DEPBU': fin_value(budget['taxProjection']['depreciation'] * -1),
              'RENTC': fin_value(rental['cashFlowProjection']['cashFlowProjectionPurchased']['netIncome'][1]),
              'OPRC': fin_value(
                  rental['cashFlowProjection']['cashFlowProjectionPurchased']['operatingExpenses'][1] * -1),
              'TAXB': fin_value(27.5 * rental['depreciationRecapture'] / rental['genericInput']['holdingPeriodAnnual']),
              'INTR': fin_value(rental['mortgage']['interest'][0]),
              'GI': fin_value(rental['taxProjection']['income']),
              'OE': fin_value(rental['taxProjection']['operatingExpenses']),
              'NOI': fin_value(rental['taxProjection']['netOperatingIncome']),
              # 'PT':fin_value(rental['taxProjection']['propertyTax']),
              'DEP': fin_value(rental['taxProjection']['taxDepreciationRecapture'] / rental['genericInput'][
                  'depreciationRecaptureRate'] / rental['genericInput']['holdingPeriodAnnual'] * -1),
              'IN': fin_value(rental['mortgage']['interest'][0]),
              'TI': fin_value(taxableIncome),
              'MTR': rate_value(rental['genericInput']['taxRate']),
              'TAX': fin_value(taxPayable),
              'NOTE': taxNote,
              'CAPR': rate_value(rental['genericInput']['capitalGainTaxRate']),
              'DPCR': rate_value(rental['genericInput']['depreciationRecaptureRate']),
              'PP': fin_value(rental['genericInput']['purchasePrice']),
              'HP': str(rental['genericInput']['holdingPeriodAnnual']),
              'SLD': fin_value(rental['taxProjection']['estimatedSalePrice']),
              'SLEX': fin_value(rental['sellingExpense']),
              'PUREX': fin_value(rental['taxProjection']['purchaseExpenses']),
              'ACCDEP': fin_value(rental['depreciationRecapture']),
              'ESP': fin_value(rental['taxProjection']['estimatedSalePrice']),
              'NSP': fin_value(rental['taxProjection']['netSalePrice']),
              'PPI': fin_value(rental['genericInput']['improvementCost'] + rental['purchaseExpense']),
              'ACDP': fin_value(-1 * rental['taxProjection']['taxDepreciationRecapture'] / rental['genericInput'][
                  'depreciationRecaptureRate']),
              'AJB': fin_value(adjustedBasis),
              'SEN': fin_value(-1 * rental['sellingExpense']),
              'AJBN': fin_value(-1 * adjustedBasis),
              'GRS': fin_value(rental['gainRealizedSale']),
              'DEPR': fin_value(-1 * rental['taxProjection']['taxDepreciationRecapture'] / rental['genericInput'][
                  'depreciationRecaptureRate']),
              'GS': fin_value(rental['gainRecognizedSale']),
              'TDRE': fin_value(-1 * rental['taxProjection']['taxDepreciationRecapture'] / rental['genericInput'][
                  'depreciationRecaptureRate']),
              'TCAP': fin_value(-1 * rental['taxProjection']['taxCapitalGain']),
              'TTX': fin_value(-1 * rental['taxProjection']['totalTaxDue']),
              'DR': rate_value(rental['genericInput']['depreciationRecaptureRate']),
              'CR': rate_value(rental['genericInput']['capitalGainTaxRate']),
              'ACCDP': fin_value(rental['taxProjection']['taxDepreciationRecapture'] / rental['genericInput'][
                  'depreciationRecaptureRate']),

              }

    document.merge_pages([cust_1])
    document.write(f'{out}.docx')


def pie_chart(file, lables, sizeLable):
    # create data
    names = lables
    size = sizeLable
    color = ['#8FAADC', '#FFC000', '#A5A5A5', '#F4B183']

    # Create a circle at the center of the plot
    my_circle = plt.Circle((0, 0), 1.05, color='white')

    # margin adjustments
    # plt.subplots(constrained_layout=True)
    # plt.margins(0,0,tight=True)

    # Label distance: gives the space between labels and the center of the pie
    plt.pie(size, labels=names, labeldistance=1.1, radius=1.3, colors=color,
            wedgeprops={'linewidth': 7, 'edgecolor': 'white'})

    p = plt.gcf()
    p.gca().add_artist(my_circle)

    plt.savefig(f'{file}.png')
    # plt.show()


def figuresOnPDF(file):
    pdf = FPDF(orientation='P', unit='in', format='Letter')
    pdf.set_margins(left=1, top=1, right=1)
    pdf.add_page()

    # set the location where picture is to added
    pdf.image(f'{file}.png', x=3, y=7.8, w=2.75, h=2.5)
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
    rental, budget = initialize()
    id = pdfFileProperties['id']
    templateLocation = pdfFileProperties['templateLocation']
    outLocation = pdfFileProperties['outLocation']
    property_address = pdfFileProperties['propertyAddress']

    wordPopulate(f'{templateLocation}taxAppendixTemplate', f'{outLocation}taxAppendix{id}', property_address,
                 pdfFileProperties, rental, budget)
    word_to_pdf(f'{outLocation}taxAppendix{id}')
    maregePdf(f'{outLocation}taxAppendix{id}', f'{outLocation}out{id}')
