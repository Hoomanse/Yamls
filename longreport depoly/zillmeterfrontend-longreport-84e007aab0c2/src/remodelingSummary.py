from __future__ import print_function
from mailmerge import MailMerge
from fpdf import FPDF
import PyPDF2 as pypdf
from pdf_generator import word_to_pdf
import json
from PyPDF2 import PdfFileMerger, PdfFileReader
from matplotlib import pyplot as plt
import plotly.graph_objects as go

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
                    sectionNamelaborMaterail.update({each_id['sectionName']: {'labor': labor, 'material': material}})
    ## remodelingSummaryTable
    # create a dictionary of labor and material of each room (e.g. bed, bath, kitchen, electrical..)
    #     remodeledArea={'Bedroom(s)':[1000],
    #                    'Kitchen':[4000],
    #                    'Half Bathroom(s)':[3000],
    #                    'Full Bathroom(s)':[2000],
    #                    'Living Room and Foyer':[5000, 14000],
    #                    'Hallways and Other':[15000],
    #                    'Laundry Area':[13000],
    #                    'Basement':[6000],
    #                    'Exterior Work':[9000, 8000, 7000, 10000],
    #                    'Mechanical & Electrical':[11000,12000]
    #                    }
    #     scopeLaborMaterail={}
    #     for each_key in remodeledArea.keys():
    #         laborCost = sum(labor for labor in [id_cost_labor[each] for each in remodeledArea[each_key]])
    #         materialCost = sum(material for material in [id_cost_material[each] for each in remodeledArea[each_key]])
    #         if laborCost + materialCost !=0:
    #             scopeLaborMaterail.update({each_key:{'labor':laborCost,'material':materialCost,'total':materialCost+laborCost}})

    ## create a dictionary of labor and material cost of each 'sectionName'
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


def wordPopulate(template, out, property_address, pdfFileProperties, rental, flip, improvement):
    pageNumber = pdfFileProperties['pageStart']
    pagesTotalNumber = 1
    pdfFileProperties['tableContent'].update({pageNumber: 'Remodeling Estimate Summary'})
    pdfFileProperties['pageStart'] = pageNumber + pagesTotalNumber

    template = f'{template}.docx'
    document = MailMerge(template)
    document.merge(ADR=property_address, PG=page_value(pageNumber))

    cust_1 = {'ADR': property_address,
              'AFRR': fin_value(
                  flip['genericInput']['improvementCost'] * (1 + flip['genericInput']['addedValueRateImprovement'])),
              'PV': fin_value(rental['genericInput']['purchasePrice']),
              'RC': fin_value(flip['genericInput']['improvementCost']),
              'ARV': fin_value(rental['genericInput']['purchasePrice'] + flip['genericInput']['improvementCost'] * (
                      1 + flip['genericInput']['addedValueRateImprovement'])),
              'TC': fin_value(flip['genericInput']['improvementCost']),
              'GCR': rate_value(improvement['generalContractorCost'] / 100),
              'CR': rate_value(improvement['contingency'] / 100)
              }
    scopeName_laborMaterail = remodeling_dictionary(improvement)[1]  # is a dict object

    ##filling up the table
    subMaterial = 0
    subLabor = 0
    subtotal = 0
    iterator = 1
    for each_key in scopeName_laborMaterail:
        cust_1[f'R{iterator}'] = each_key
        cust_1[f'M{iterator}'] = fin_value(scopeName_laborMaterail[each_key]['material'])
        cust_1[f'L{iterator}'] = fin_value(scopeName_laborMaterail[each_key]['labor'])
        cust_1[f'C{iterator}'] = fin_value(
            scopeName_laborMaterail[each_key]['material'] + scopeName_laborMaterail[each_key]['labor'])
        iterator += 1
        subMaterial = subMaterial + scopeName_laborMaterail[each_key]['material']
        subLabor = subLabor + scopeName_laborMaterail[each_key]['labor']
        subtotal = subMaterial + subLabor
    cust_1['MSUB'] = fin_value(subMaterial)
    cust_1['LSUB'] = fin_value(subLabor)
    cust_1['SUB'] = fin_value(subtotal)
    cust_1['GC'] = fin_value(subtotal * improvement['generalContractorCost'] / 100)
    cust_1['C'] = fin_value(subtotal * improvement['contingency'] / 100)
    cust_1['TC'] = fin_value(
        subtotal * (1 + improvement['contingency'] / 100 + improvement['generalContractorCost'] / 100))
    #### Calling Pie Chart
    lables = ['Labor', 'Contingency', 'Material', 'Contractor Fee']
    pieValues = [subLabor, subtotal * improvement['contingency'] / 100, subMaterial,
                 subtotal * improvement['generalContractorCost'] / 100]
    # Delete zeros from the list of values
    for item in pieValues:
        if item == 0:
            lables.pop(pieValues.index(0))
            pieValues.pop(pieValues.index(0))
    ##rounding percentage of pieValues:
    total_pieValues = sum([item for item in pieValues])

    for item in range(len(pieValues)):
        if total_pieValues == 0:
            pieValues[item] = 0
        else:
            pieValues[item] = round(pieValues[item] / total_pieValues, 2)

    total_pieValues = sum([item for item in pieValues])
    pieValues[0] = pieValues[0] + 1 - total_pieValues

    pie_chart(out, lables, pieValues)

    document.merge_pages([cust_1])
    document.write(f'{out}.docx')


def pie_chart(file, lables, sizeLable):
    # hedearfont:
    headerFont = dict(color='black', size=36, family='Arial')
    headerFont2 = dict(color='black', size=26, family='Arial')
    axesFont = dict(color='black', size=25, family='Arial')

    # create data
    names = lables
    size = sizeLable
    color = ['#8FAADC', '#FFC000', '#A5A5A5', '#F4B183']

    # Create a circle at the center of the plot
    fig = go.Figure(data=[go.Pie(labels=names, values=size, hole=.72,
                                 marker_colors=color, textfont=axesFont,
                                 insidetextorientation='horizontal')])
    fig.update_traces(textinfo='none', textposition='inside', textfont=axesFont)
    # textinfo='percent' if % to be shown

    fig.update_layout(

        legend=dict(

            y=0,
            yanchor="top",
            xanchor="center",

            font=headerFont2,
            orientation="h"
        ),
        showlegend=True,
        margin=dict(l=40, r=40, t=40, b=40),
        paper_bgcolor="white",
        plot_bgcolor='rgba(0,0,0,0)',
        width=600,
        height=600)

    # table header annotations
    fig.add_annotation(text=f'<br>Remodeling<br>Expense<br>Distribution',
                       xref="paper", yref="paper", align='center',
                       x=0.5, y=.5, showarrow=False,
                       font=headerFont)

    fig.write_image(f'{file}.png')

    # plt.show()


def figuresOnPDF(file):
    pdf = FPDF(orientation='P', unit='in', format='Letter')
    pdf.set_margins(left=1, top=1, right=1)
    pdf.add_page()

    # set the location where picture is to added
    pdf.image(f'{file}.png', x=2.75, y=7.9, w=2.7, h=2.7)
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

    wordPopulate(f'{templateLocation}remodelingSummaryTemplate', f'{outLocation}remodelingSummary{id}',
                 property_address, pdfFileProperties, rental, flip, improvement)
    word_to_pdf(f'{outLocation}remodelingSummary{id}')
    figuresOnPDF(f'{outLocation}remodelingSummary{id}')
    overlay(f'{outLocation}remodelingSummary{id}', f'{outLocation}remodelingSummary{id}.png',
            f'{outLocation}remodelingSummaryOut{id}')
    maregePdf(f'{outLocation}remodelingSummaryOut{id}', f'{outLocation}out{id}')
