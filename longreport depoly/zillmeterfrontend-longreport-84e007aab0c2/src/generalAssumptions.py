from __future__ import print_function
from mailmerge import MailMerge
from fpdf import FPDF
import PyPDF2 as pypdf
import json
from PyPDF2 import PdfFileMerger, PdfFileReader
import os
from pdf_generator import word_to_pdf


def initialize():
    with open("../json/rental.json") as json_file:
        rental = json.load(json_file)
        rental = rental["data"]["rental"]

    with open("../json/flip.json") as json_file:
        flip = json.load(json_file)
        flip = flip["data"]["flip"]
    return rental, flip


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


def wordPopulate(template, out, property_address, pdfFileProperties, flip, rental):
    pageNumber = pdfFileProperties['pageStart']
    pagesTotalNumber = 1
    pdfFileProperties['tableContent'].update(
        {pageNumber: 'Comprehensive Financial Report - Summary of General Assumptions'})
    pdfFileProperties['pageStart'] = pageNumber + pagesTotalNumber

    template = f'{template}.docx'
    document = MailMerge(template)

    document.merge(PG=page_value(pageNumber))
    document.merge(ADR=property_address)

    houseHoldIncome_status = '-'
    taxFilled_status = '-'
    if 'houseHoldIncome' in pdfFileProperties:
        if pdfFileProperties['houseHoldIncome'] and pdfFileProperties['taxFilled'] != None:
            houseHoldIncome_status = fin_value(pdfFileProperties['houseHoldIncome'])
            taxFilled_status = pdfFileProperties['taxFilled']
    else:
        pass

    if rental['genericInput']['applyImprovementAllScenarios'] == True:
        remodelingAppliedScenarios = 'All Investment Scenarios'
    else:
        remodelingAppliedScenarios = 'Only Flipping'

    cust_1 = {
        'BCH': rate_value(rental['genericInput']['benchmark']),
        'HP': str(rental['genericInput']['holdingPeriodAnnual']),
        'HHINC': houseHoldIncome_status,
        'TAXF': taxFilled_status,
        'TXR': rate_value(rental['genericInput']['taxRate']),
        'CAPR': rate_value(rental['genericInput']['capitalGainTaxRate']),
        'DEPR': rate_value(rental['genericInput']['depreciationRecaptureRate']),
        'APR': rate_value(rental['genericInput']['propertyAppreciation']),
        'RENT': rate_value(rental['genericInput']['rentIncrease']),
        'INFR': rate_value(rental['genericInput']['discountRate']),
        'IMPC': fin_value(flip['genericInput']['improvementCost']),
        'ADVC': fin_value(
            flip['genericInput']['improvementCost'] * (flip['genericInput']['addedValueRateImprovement'] + 1)),
        'ARV': fin_value(flip['genericInput']['purchasePrice'] + flip['genericInput']['improvementCost'] * (
                flip['genericInput']['addedValueRateImprovement'] + 1)),
        'RMDS': remodelingAppliedScenarios,
        'DPR': rate_value(rental['genericInput']['downPaymentRate']),
        'DP': fin_value((rental['genericInput']['downPaymentRate']) * rental['genericInput']['purchasePrice']),
        'MRTG': fin_value((1 - rental['genericInput']['downPaymentRate']) * rental['genericInput']['purchasePrice']),
        'MRGT': str(rental['genericInput']['mortgageTerm']),
        'MRGR': rate_value(rental['genericInput']['mortgageInterest']),
        'DS': fin_value(rental['monthlyDebtService'] * -1)

    }

    document.merge_pages([cust_1])
    document.write(f'{out}.docx')


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
    rental, flip = initialize()
    id = pdfFileProperties['id']
    templateLocation = pdfFileProperties['templateLocation']
    outLocation = pdfFileProperties['outLocation']
    property_address = pdfFileProperties['propertyAddress']

    wordPopulate(f'{templateLocation}generalAssumptionsTemplate', f'{outLocation}generalAssumptions{id}',
                 property_address, pdfFileProperties, flip, rental)
    word_to_pdf(f'{outLocation}generalAssumptions{id}')
    maregePdf(f'{outLocation}generalAssumptions{id}', f'{outLocation}out{id}')
