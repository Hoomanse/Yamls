import logging
import uuid
import time
import json
import os

import firstPage
import executiveSummary
import remodelingSummary
import equitySummary
import rentalSummary
import rentalWhatiIf
import shortTermSummary
import shortTermWhatIf
import primarySummary
import primaryWhatiIf
import budgetSummary
import budgetWhatiIf
import flipSummary
import flipWhatIf
import zillmeterApproach
import remodelingDeepDive
import remodelingAssumption
import remodelingBreakDown
import marketMomentum
import saleProceeds
import generalAssumptions
import budgetProjection
import primaryProjection
import rentalProjection
import shortTermProjection
import flipProjection
import taxAppendix
import tableContent
import extendedCall
import config_loader

def clean_address_field(property):
    if not 'formattedStreetAddress' in property['address']:
        property['address']['formattedStreetAddress'][0] = '-'
    if not 'city' in property['address']:
        property['address']['city'] = '-'
    if not 'state' in property['address']:
        property['address']['state'] = '-'
    if not 'zipCode' in property['address']:
        property['address']['zipCode'] = '-'


# def run_report_v1(pdfFileProperties, json):
#     firstPage.main(pdfFileProperties, json)
#
#     # summary & ZM Approach
#     executiveSummary.main(pdfFileProperties, json)
#     zillmeterApproach.main(pdfFileProperties, json)
#     marketMomentum.main(pdfFileProperties, json)
#     saleProceeds.main(pdfFileProperties, json)
#     equitySummary.main(pdfFileProperties, json)
#     generalAssumptions.main(pdfFileProperties, json)
#
#     # Remodeling
#     remodelingSummary.main(pdfFileProperties, json)
#     remodelingDeepDive.main(pdfFileProperties, json)
#     remodelingAssumption.main(pdfFileProperties, json)
#     remodelingBreakDown.main(pdfFileProperties, json)
#     #
#     # # Scenarios
#     rentalSummary.main(pdfFileProperties, json)
#     rentalWhatiIf.main(pdfFileProperties, json)
#     rentalProjection.main(pdfFileProperties, json)
#     #
#     shortTermSummary.main(pdfFileProperties, json)
#     shortTermWhatIf.main(pdfFileProperties, json)
#     shortTermProjection.main(pdfFileProperties, json)
#
#     primarySummary.main(pdfFileProperties, json)
#     primaryWhatiIf.main(pdfFileProperties, json)
#     primaryProjection.main(pdfFileProperties, json)
#     #
#     budgetSummary.main(pdfFileProperties, json)
#     budgetWhatiIf.main(pdfFileProperties, json)
#     budgetProjection.main(pdfFileProperties, json)
#     #
#     flipSummary.main(pdfFileProperties, json)
#     flipWhatIf.main(pdfFileProperties, json)
#     flipProjection.main(pdfFileProperties, json)
#
#     # # Market Data
#     taxAppendix.main(pdfFileProperties, json)
#     tableContent.main(pdfFileProperties, json)


def run_report_v2(pdfFileProperties, property, improvement, thirdPartyData):
    firstPage.main(pdfFileProperties, property, thirdPartyData)

    executiveSummary.main(pdfFileProperties)
    remodelingSummary.main(pdfFileProperties, improvement)
    equitySummary.main(pdfFileProperties)

    rentalSummary.main(pdfFileProperties)
    rentalWhatiIf.main(pdfFileProperties)
    shortTermSummary.main(pdfFileProperties)
    shortTermWhatIf.main(pdfFileProperties)
    primarySummary.main(pdfFileProperties)
    primaryWhatiIf.main(pdfFileProperties)
    budgetSummary.main(pdfFileProperties)
    budgetWhatiIf.main(pdfFileProperties)
    flipSummary.main(pdfFileProperties)
    flipWhatIf.main(pdfFileProperties)

    zillmeterApproach.main(pdfFileProperties, property)
    remodelingDeepDive.main(pdfFileProperties, improvement, property)
    remodelingAssumption.main(pdfFileProperties, improvement, property)
    remodelingBreakDown.main(pdfFileProperties, improvement)

    marketMomentum.main(pdfFileProperties, property)
    saleProceeds.main(pdfFileProperties)

    generalAssumptions.main(pdfFileProperties)

    rentalProjection.main(pdfFileProperties)
    shortTermProjection.main(pdfFileProperties)
    primaryProjection.main(pdfFileProperties)
    budgetProjection.main(pdfFileProperties)
    flipProjection.main(pdfFileProperties)
    taxAppendix.main(pdfFileProperties)
    tableContent.main(pdfFileProperties)


def clean_the_workspace():
    os.remove('../json/dashboard.json')
    os.remove('../json/budget.json')
    os.remove('../json/primary.json')
    os.remove('../json/rental.json')
    os.remove('../json/flip.json')
    os.remove('../json/shortTerm.json')
    os.remove('../json/whatif.json')


def load_property(input_json):
    loaded_json = json.loads(input_json.decode('utf-8'))
    property = loaded_json["property"]
    improvement = loaded_json["improvement"]
    thirdPartyData = loaded_json["thirdPartyData"]
    clean_address_field(property)
    return property, improvement, thirdPartyData


def load_request():
    with open("../json/request_structure.json") as json_file:
        return json.load(json_file)


def create_report(pdfFileProperties, property, improvement, thirdPartyData):
    logging.info(f'Report creation started')
    startTime = time.time()
    # run_report_v1(pdfFileProperties, json)
    run_report_v2(pdfFileProperties, property, improvement, thirdPartyData)  # summary first, detailed then
    clean_the_workspace()
    executionTime = (time.time() - startTime)
    logging.info(f'Report created in {executionTime} sec')

    return 'out' + pdfFileProperties['id'] + '.pdf'


def create_long_report(input_json):
    property, improvement, thirdPartyData = load_property(input_json)
    ##values
    authentication_key = config_loader.parse_config('../config.yml').get('authentication-key')
    id = uuid.uuid1()
    templateLocation = '../template/'
    outLocation = '../out/'
    propertyImageLocation = '../img/'

    sensitivity = 0.15
    propertyAddress = f"{property['address']['formattedStreetAddress'][0]}, {property['address']['city']}, {property['address']['state']}, {property['address']['zipCode']}"
    pageStart = 1
    houseHoldIncome = None
    taxFilled = None
    id = propertyAddress

    pdfFileProperties = {'id': id,
                         'templateLocation': templateLocation,
                         'outLocation': outLocation,
                         'propertyImageLocation': propertyImageLocation,
                         'authenticationKey': authentication_key,
                         'propertyAddress': propertyAddress,
                         'sensitivity': sensitivity,
                         'pageStart': pageStart,
                         'tableContent': {},
                         'houseHoldIncome': houseHoldIncome,
                         'taxFilled': taxFilled
                         }

    extendedCall.main(input_json)

    return create_report(pdfFileProperties, property, improvement, thirdPartyData)
