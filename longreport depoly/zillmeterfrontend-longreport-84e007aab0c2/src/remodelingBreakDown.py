from __future__ import print_function
from mailmerge import MailMerge
import plotly.graph_objects as go
from fpdf import FPDF
import PyPDF2 as pypdf
from pdf_generator import word_to_pdf
import json
from matplotlib import pyplot as plt
from PyPDF2 import PdfFileMerger, PdfFileReader
import os


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


def remodeling_dictionary(improvement):
    matreial_level = {3: "Budget Friendly", 2: "Major Retailer's Best Seller", 1: "Deluxe"}

    # These groups creates backend customized groups (each group automatically calls some line items)
    group_lineItems = {1: [1001, 2019, 3015, 4001, 5001, 6001, 13007, 14011, 15009],
                       2: [1011, 4022, 5014, 6013, 14009, 15011], 3: [1005, 4021, 5005, 6005, 13006, 14006, 15005],
                       4: [1012, 2020, 3016, 4024, 5015, 6014, 13013, 14012, 15013],
                       5: [1004, 4004, 5004, 6004, 14004, 15010, 2001, 1002, 1003, 2004, 3001, 3003, 4002, 4003, 5002,
                           5003, 6002, 6003, 13008, 13010, 14002, 14003, 15001, 15002],
                       6: [1007, 4006, 5006, 6008, 13005, 14005, 15008],
                       8: [1008, 4008, 5008, 6008, 13005, 14005, 15008],
                       9: [1007, 4006, 5006, 6007, 13003, 14008, 15007],
                       10: [2017, 3014, 2003, 3005, 2002, 2005, 3002, 3004], 11: [2008, 2007],
                       12: [2006, 2007], 13: [2010, 2011, 2012, 2013, 2016, 3006, 3007, 3008, 3009, 3012, 2014, 3010],
                       14: [4007], 15: [4009, 4010, 4005, 4013, 4011, 4014, 4016],
                       16: [4012, 4015, 4017, 4018, 4019, 4025, 13001, 13002],
                       17: [1009, 5009, 6009], 18: [1014, 2018, 3013, 4020, 5012, 6012, 13011, 15003],
                       19: [11003, 11001, 11004], 20: [14001, 14010], 21: [8004], 22: [8003],
                       23: [1010, 2015, 3011, 4023, 5010, 6010, 10004, 13009, 14013, 15004],
                       24: [9003], 25: [9001, 9003], 26: [7001, 7002, 7003, 7004], 27: [10001, 10002, 10003],
                       28: [11002], 29: [1013, 5011, 6011, 12001], 30: [8006], 31: [8001]}

    # Scopes are to select an improvement work from the UI
    scope_dict = {1: "Paint & Wallpaper", 2: "Replace Flooring", 3: "Bathroom", 4: "Kitchen Cabinets",
                  5: "Kitchen Appliances",
                  6: "Mechanical Systems Upgrade", 7: "Refresh Landscape", 8: "Electrical Systems and Fixtures Upgrade",
                  9: "Garage Upgrade",
                  10: "Washer & Dryer", 11: "Closet Upgrade", 12: "Upgrade Doors", 13: "Exterior Windows",
                  14: "Exterior Paint and/or Sidings", 15: "Roofing"}

    # Each of these 'Scope Codes' corresponds to one or a group of 'Customized Groups'
    scope_code = {1: [1, 2, 4, 5], 2: [3, 6, 7, 8], 3: [10, 11, 12, 9], 4: [14, 13], 5: [15], 6: [18, 27], 7: [26],
                  8: [22, 28], 9: [25],
                  10: [31, 32], 11: [16], 12: [19, 17], 13: [30, 29], 14: [20, 21], 15: [23, 24]}

    ###Adjustor : (on the UI, user may change the price of a scope and that scope may contain multiple line items so all those line items are to be adjusted)
    remodelingScope = []  # remodelingScope is the list of all selected scopes from the "Scope Dict"
    line_item_multiplier = {}  # line_item_multiplier is a dictionary including an 'adjsutor' for 'every line item' that it's price may been affected by the overrides
    for each_category in improvement["lineItemGroups"]:
        if each_category["isSelected"] == True:
            for each in scope_code:
                if each_category["groupType"] in scope_code[each] and scope_dict[each] not in remodelingScope:
                    remodelingScope.append(scope_dict[each])
            try:
                adjustor = each_category["price"] / each_category["totalCost"]
            except Exception:
                adjustor = 0
            for each_id in each_category["lineItemIdCollection"]:
                line_item_multiplier[each_id] = adjustor
        else:
            pass
    remodelingScope.sort()

    selected_ids = []  # line item ids that have been used in this remodeling
    for each_group in improvement['lineItemGroups']:
        try:
            [selected_ids.append(each_item) for each_item in each_group["lineItemIdCollection"]]

        except:
            pass

    # id cost_labor= Adjusted etsimated cost of each line item id
    id_cost_labor = {1000: 0, 2000: 0, 3000: 0, 4000: 0, 5000: 0, 6000: 0, 7000: 0, 8000: 0, 9000: 0, 10000: 0,
                     11000: 0,
                     12000: 0, 13000: 0, 14000: 0, 15000: 0, 16000: 0}
    id_cost_material = {1000: 0, 2000: 0, 3000: 0, 4000: 0, 5000: 0, 6000: 0, 7000: 0, 8000: 0, 9000: 0, 10000: 0,
                        11000: 0,
                        12000: 0, 13000: 0, 14000: 0, 15000: 0, 16000: 0}
    sectionNamelaborMaterail = {}
    scopeNamelaborMaterail = {}

    for each_id in improvement['lineItemPriceCollection']:
        if "estimatedQuantity" in each_id:
            if each_id['lineItemId'] in selected_ids and each_id["estimatedQuantity"] != -1:
                labor = each_id['estimatedQuantity'] * (each_id["laborPrice"]) * line_item_multiplier[
                    each_id['lineItemId']]
                material = each_id['estimatedQuantity'] * (each_id["materialPrice"]) * line_item_multiplier[
                    each_id['lineItemId']]
                scopeid = each_id['scopeId']
                id_cost_labor[scopeid] = id_cost_labor[scopeid] + labor
                id_cost_material[scopeid] = id_cost_material[scopeid] + material

                if each_id['scopeName'] in scopeNamelaborMaterail:
                    scopeNamelaborMaterail[each_id['scopeName']]['material'] = material + scopeNamelaborMaterail[
                        each_id['scopeName']]['material']
                    scopeNamelaborMaterail[each_id['scopeName']]['labor'] = labor + scopeNamelaborMaterail[
                        each_id['scopeName']]['labor']
                else:
                    scopeNamelaborMaterail.update({each_id['scopeName']: {'labor': labor, 'material': material}})

                if each_id['sectionName'] in sectionNamelaborMaterail:
                    sectionNamelaborMaterail[each_id['sectionName']]['material'] = material + sectionNamelaborMaterail[
                        each_id['sectionName']]['material']
                    sectionNamelaborMaterail[each_id['sectionName']]['labor'] = labor + sectionNamelaborMaterail[
                        each_id['sectionName']]['labor']
                else:
                    sectionNamelaborMaterail.update({each_id['sectionName']: {'labor': labor, 'material': material,
                                                                              'division': each_id['sectionId']}})

    return [sectionNamelaborMaterail, scopeNamelaborMaterail]


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


def wordPopulate(template, out, property_address, pdfFileProperties, rental, improvement, flip):
    pageNumber = pdfFileProperties['pageStart']
    pagesTotalNumber = 2
    pdfFileProperties['tableContent'].update({pageNumber: 'Remodeling Budget Break Down'})
    pdfFileProperties['pageStart'] = pageNumber + pagesTotalNumber

    template = f'{template}.docx'
    document = MailMerge(template)

    document.merge(PG1=page_value(pageNumber), PG2=page_value(pageNumber + 1))

    cust_1 = {'ADR': property_address,
              'PV': fin_value(rental['genericInput']['purchasePrice']),
              'RC': fin_value(rental['genericInput']['improvementCost']),
              'ARV': fin_value(rental['genericInput']['purchasePrice'] + flip['genericInput']['improvementCost'] * (
                          1 + flip['genericInput']['addedValueRateImprovement'])),
              'TC': fin_value(flip['genericInput']['improvementCost']),
              'GCR': rate_value(improvement['generalContractorCost'] / 100),
              'CR': rate_value(improvement['contingency'] / 100)
              }
    sectionName_laborMaterail = remodeling_dictionary(improvement)[0]  # is a dict object

    ##filling up the table
    subMaterial = 0
    subLabor = 0
    subtotal = 0
    iterator = 1
    subtotal = 0
    for each_key in sectionName_laborMaterail:
        cust_1[f'R{iterator}'] = str(sectionName_laborMaterail[each_key]['division'].split('-')[0]) + '-' + str(
            sectionName_laborMaterail[each_key]['division'].split('-')[1]) + '-' + str(
            sectionName_laborMaterail[each_key]['division'].split('-')[2])
        cust_1[f'M{iterator}'] = str(each_key)
        cust_1[f'C{iterator}'] = fin_value(
            sectionName_laborMaterail[each_key]['material'] + sectionName_laborMaterail[each_key]['labor'])
        iterator += 1
        subMaterial = subMaterial + sectionName_laborMaterail[each_key]['material']
        subLabor = subLabor + sectionName_laborMaterail[each_key]['labor']
        subtotal = subtotal + sectionName_laborMaterail[each_key]['material'] + sectionName_laborMaterail[each_key][
            'labor']
    cust_1['MSUB'] = fin_value(subMaterial)
    cust_1['LSUB'] = fin_value(subLabor)
    cust_1['SUB'] = fin_value(subtotal)
    cust_1['C'] = fin_value(subtotal * improvement['generalContractorCost'] / 100)
    cust_1['GC'] = fin_value(subtotal * improvement['contingency'] / 100)
    cust_1['TC'] = fin_value(
        subtotal * (1 + improvement['contingency'] / 100 + improvement['generalContractorCost'] / 100))

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


def main(pdfFileProperties, improvement):
    rental, flip = initialize()
    id = pdfFileProperties['id']
    templateLocation = pdfFileProperties['templateLocation']
    outLocation = pdfFileProperties['outLocation']
    property_address = pdfFileProperties['propertyAddress']

    wordPopulate(f'{templateLocation}remodelingBreakDownTemplate', f'{outLocation}remodelingBreakDown{id}',
                 property_address, pdfFileProperties, rental, improvement, flip)
    word_to_pdf(f'{outLocation}remodelingBreakDown{id}')
    maregePdf(f'{outLocation}remodelingBreakDown{id}', f'{outLocation}out{id}')
