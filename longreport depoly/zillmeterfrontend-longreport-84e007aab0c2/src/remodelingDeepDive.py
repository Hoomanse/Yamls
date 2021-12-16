from __future__ import print_function
from mailmerge import MailMerge
import plotly.graph_objects as go
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

    ##wrap up the results
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


def wordPopulate(template, out, property_address, pdfFileProperties, improvement, property):
    pageNumber = pdfFileProperties['pageStart']
    pagesTotalNumber = 1
    pdfFileProperties['tableContent'].update({pageNumber: 'Deep Dive into the Remodeling Estimate'})
    pdfFileProperties['pageStart'] = pageNumber + pagesTotalNumber

    template = f'{template}.docx'
    document = MailMerge(template)

    document.merge(PG=page_value(pageNumber))

    try:
        bedsCount = str(property['structure']['bedsCount'])
    except Exception:
        bedsCount = '-'
    try:
        bathsCount = str(property['structure']['bathsCount'])
    except Exception:
        bathsCount = '-'
    try:
        partialBathsCount = str(property['structure']['partialBathsCount'])
    except Exception:
        partialBathsCount = '-'
    try:
        totalAreaSqFt = str(property['structure']['totalAreaSqFt']) + ' sqft'
    except Exception:
        totalAreaSqFt = '-'
    try:
        yearBuilt = str(property['structure']['yearBuilt'])
    except Exception:
        yearBuilt = '-'
    try:
        lotSize = str(property['parcel']['areaSqFt']) + ' sqft'
    except Exception:
        lotSize = '-'
    try:
        basementType = str(property['structure']['basementType'])
    except Exception:
        basementType = '-'
    try:
        parkingSpacesCount = str(property['structure']['parkingSpacesCount'])
    except Exception:
        parkingSpacesCount = '-'
    try:
        propertyType = str(property['parcel']['standardizedLandUseType'])
    except Exception:
        propertyType = '-'

    document.merge(ADR=property_address)

    cust_1 = {'ADR': property_address,
              'SF': totalAreaSqFt,
              'BD': bedsCount,
              'FBR': bathsCount,
              'HBR': partialBathsCount,
              'PT': propertyType,
              'GRG': parkingSpacesCount,
              'YR': yearBuilt,
              'LOT': lotSize,
              'BSM': basementType
              }
    sectionName_laborMaterail = remodeling_dictionary(improvement)[0]  # is a dict object

    ##filling up the table
    ##Qty take offs of Bedrooms, Kitchen, Dining & Living, Full Bathroom, Half Bathroom, Hallways & Other, Foyer, Landscape, Roof
    qtyTablePopulate('Bedroom', ['bedroom'], 1, cust_1, improvement)
    qtyTablePopulate('Kitchen', ['kitchen'], 2, cust_1, improvement)
    qtyTablePopulate('Dining & Living Room', ['dining_living', 'foyer'], 3, cust_1, improvement)
    qtyTablePopulate('Full Bathroom', ['bathroom_full'], 4, cust_1, improvement)
    qtyTablePopulate('Half Bathroom', ['bathroom_half'], 5, cust_1, improvement)
    qtyTablePopulate('Hallways & Other', ['hallway_and_others', 'laundry_room'], 6, cust_1, improvement)
    qtyTablePopulate('Basement', ['basement'], 7, cust_1, improvement)
    qtyTablePopulate('Landscape', ['Landscape'], 8, cust_1, improvement)
    qtyTablePopulate('Roof', ['roof'], 9, cust_1, improvement)

    document.merge_pages([cust_1])
    document.write(f'{out}.docx')


def qtyTablePopulate(roomTitle, listRooms, rowNumber, cust_1, improvement):
    dic = {}
    dic[f'A{rowNumber}'] = str(roomTitle)
    dic[f'Q{rowNumber}'] = str(qtyTakeOffs(listRooms, improvement)['quantity'])
    dic[f'F{rowNumber}'] = str(qtyTakeOffs(listRooms, improvement)['floorArea'])
    dic[f'P{rowNumber}'] = str(qtyTakeOffs(listRooms, improvement)['perimeter'])
    dic[f'W{rowNumber}'] = str(qtyTakeOffs(listRooms, improvement)['wallArea'])
    dic[f'F{rowNumber}'] = str(qtyTakeOffs(listRooms, improvement)['floorArea'])

    if roomTitle == 'Dining & Living Room' or roomTitle == 'Hallways & Other':
        dic[f'Q{rowNumber}'] = '1'
    cust_1.update(dic)
    return cust_1


def qtyTakeOffs(roomList, improvement):
    try:
        area = str(sum([item['floorArea'] for item in improvement['estimatedQuantities'] if
                        item['name'] in roomList])) + ' sqft'
    except Exception:
        area = '-'

    try:
        quantity = sum([item['quantity'] for item in improvement['estimatedQuantities'] if
                        item['name'] in roomList])
    except Exception:
        quantity = '-'

    try:
        perimeter = str(sum([item['perimeter'] for item in improvement['estimatedQuantities'] if
                             item['name'] in roomList])) + ' ft'
    except Exception:
        perimeter = '-'

    try:
        wallArea = str(sum([item['wallArea'] for item in improvement['estimatedQuantities'] if
                            item['name'] in roomList])) + ' sqft'
    except Exception:
        wallArea = '-'

    return {'floorArea': area, 'quantity': quantity, 'perimeter': perimeter, 'wallArea': wallArea}


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


def main(pdfFileProperties, improvement, property):
    id = pdfFileProperties['id']
    templateLocation = pdfFileProperties['templateLocation']
    outLocation = pdfFileProperties['outLocation']
    property_address = pdfFileProperties['propertyAddress']

    wordPopulate(f'{templateLocation}remodelingDeepDiveTemplate', f'{outLocation}remodelingDeepDive{id}',
                 property_address, pdfFileProperties, improvement, property)
    word_to_pdf(f'{outLocation}remodelingDeepDive{id}')
    maregePdf(f'{outLocation}remodelingDeepDive{id}', f'{outLocation}out{id}')
