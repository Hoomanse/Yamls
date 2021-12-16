from __future__ import print_function
from mailmerge import MailMerge
from fpdf import FPDF
import PyPDF2 as pypdf
import json
from matplotlib import pyplot as plt
from PyPDF2 import PdfFileMerger, PdfFileReader
import os
from pdf_generator import word_to_pdf


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


def wordPopulate(template, out, property_address, pdfFileProperties):
    template = f'{template}.docx'
    document = MailMerge(template)

    document.merge(ADR=property_address)
    cust_1 = {'ADR': property_address}
    iterator = 1
    for item in pdfFileProperties['tableContent']:
        cust_1.update({f'R{iterator}': pdfFileProperties['tableContent'][item],
                       f'C{iterator}': str(item)})
        iterator = iterator + 1

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


def maregePdf(inFile, outFile, pdfFileProperties):
    pdf_file1 = PdfFileReader(f'{inFile}.pdf')
    pdf_file2 = PdfFileReader(f'{outFile}.pdf')
    output = PdfFileMerger()
    output.append(pdf_file2)

    # insert table of conetnt into the 2nd page of the input pdf
    output.merge(1, pdf_file1)

    # add bookmark
    offset = 2
    for item in pdfFileProperties['tableContent']:
        output.addBookmark(pdfFileProperties['tableContent'][item], int(item + offset))

    with open(f'{outFile}.pdf', "wb") as output_stream:
        output.write(output_stream)

    os.remove(f'{inFile}.pdf')


def main(pdfFileProperties):
    id = pdfFileProperties['id']
    templateLocation = pdfFileProperties['templateLocation']
    outLocation = pdfFileProperties['outLocation']
    property_address = pdfFileProperties['propertyAddress']

    wordPopulate(f'{templateLocation}tableContentTemplate', f'{outLocation}tableContent{id}', property_address,
                 pdfFileProperties)
    word_to_pdf(f'{outLocation}tableContent{id}')
    maregePdf(f'{outLocation}tableContent{id}', f'{outLocation}out{id}', pdfFileProperties)
