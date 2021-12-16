import json
import requests

with open("../json/request_structure.json") as json_file:
    request = json.load(json_file)
with open("../json/request_structure.json") as json_file:
    query = json.load(json_file)

budgetUse = 'http://calculationservice.dev.zillmeterinternal.com/api/v1/IntegrationUnit/BudgetUseExtended'
flip = 'http://calculationservice.dev.zillmeterinternal.com/api/v1/IntegrationUnit/FlipExtended'
privateUse = 'http://calculationservice.dev.zillmeterinternal.com/api/v1/IntegrationUnit/PrivateUseExtended'
rental = 'http://calculationservice.dev.zillmeterinternal.com/api/v1/IntegrationUnit/RentalExtended'
shortTerm = 'http://calculationservice.dev.zillmeterinternal.com/api/v1/IntegrationUnit/ShortTermRentalExtended'
dashboard = 'http://calculationservice.dev.zillmeterinternal.com/api/v1/IntegrationUnit/DashboardExtended'

sensitivity = 0.15

scenarios = [budgetUse, privateUse, rental, shortTerm, flip]
scenarios_str = ['budgetUse', 'privateUse', 'rental', 'shortTerm', 'flip']
rangeValue = ['low', 'high', 'current']
whatif = {}


def call_endpoint(scenario, request_json):
    response = requests.post(url=scenario, json=request_json).json()
    return response


def call_endpoint(scenario, request_json):
    response = requests.post(url=scenario, json=request_json).json()
    return response


def correction_npv_30yr(scenario_url, scenario_str, query, exisitng_json):
    holding_period = query['input']['inputModel']['holdingPeriod']
    query['input']['inputModel']['holdingPeriod'] = 360
    npv_30yr_scenario = call_endpoint(scenario_url, query)
    exisitng_json['data'][scenario_str[0]]['beforeTaxProfit'] = npv_30yr_scenario['data'][scenario_str[0]][
        'beforeTaxProfit']
    exisitng_json['data'][scenario_str[0]]['afterTaxProfit'] = npv_30yr_scenario['data'][scenario_str[0]][
        'afterTaxProfit']
    query['input']['inputModel']['holdingPeriod'] = holding_period

    return exisitng_json


def extended_endpoints(input_json):
    ## create the input model request json.
    input_model = json.loads(input_json.decode('utf-8'))['calculationData']['inputModel']
    request['input']['inputModel'] = input_model
    query = request

    ## call endpoints
    budgetScenario = call_endpoint(budgetUse, request)
    with open('../json/budget.json', 'w') as outfile:
        budgetScenario = correction_npv_30yr(budgetUse, ['budgetUse'], query, budgetScenario)
        json.dump(budgetScenario, outfile, indent=3)

    flipScenario = call_endpoint(flip, request)
    with open('../json/flip.json', 'w') as outfile:
        json.dump(flipScenario, outfile, indent=3)

    primaryScenario = call_endpoint(privateUse, request)
    with open('../json/primary.json', 'w') as outfile:
        primaryScenario = correction_npv_30yr(privateUse, ['privateUse'], query, primaryScenario)
        json.dump(primaryScenario, outfile, indent=3)

    vacationScenario = call_endpoint(shortTerm, request)
    with open('../json/shortTerm.json', 'w') as outfile:
        vacationScenario = correction_npv_30yr(shortTerm, ['shortTerm'], query, vacationScenario)
        json.dump(vacationScenario, outfile, indent=3)

    rentalScenario = call_endpoint(rental, request)
    with open('../json/rental.json', 'w') as outfile:
        rentalScenario = correction_npv_30yr(rental, ['rental'], query, rentalScenario)
        json.dump(rentalScenario, outfile, indent=3)

    dashboardScenario = call_endpoint(dashboard, request)
    with open('../json/dashboard.json', 'w') as outfile:
        json.dump(dashboardScenario, outfile, indent=3)

    return query


##Purchase Price
def purchase_price_sens(query):
    z = {}

    purchasePrice = {
        'low': query['input']['inputModel']['purchasePrice'] * (1 - sensitivity),
        'current': query['input']['inputModel']['purchasePrice'],
        'high': query['input']['inputModel']['purchasePrice'] * (1 + sensitivity)
    }
    for each_scenario in range(len(scenarios)):
        x = {}
        y = {}
        for valueCases in rangeValue:
            query['input']['inputModel']['purchasePrice'] = purchasePrice[valueCases]
            response = call_endpoint(scenarios[each_scenario], query)
            irr = response["data"][scenarios_str[each_scenario]]['beforeTaxIRR']
            npv = response["data"][scenarios_str[each_scenario]]['beforeTaxNetProfit']
            x.update({valueCases: npv})
            y.update({valueCases: irr})
        z.update(
            {scenarios_str[each_scenario]: {'beforeTaxNetProfit': x,
                                            'beforeTaxIRR': y}
             })
    whatif.update({'purchasePrice': z})

    query['input']['inputModel']['purchasePrice'] = purchasePrice['current']


##Holding Period
def holding_period_sens(query):
    z = {}
    holdingPeriod = {
        'low': 12 * round(query['input']['inputModel']['holdingPeriod'] * (1 - sensitivity) / 12),
        'current': query['input']['inputModel']['holdingPeriod'],
        'high': 12 * round(query['input']['inputModel']['holdingPeriod'] * (1 + sensitivity) / 12)
    }
    for each_scenario in range(len(scenarios)):
        x = {}
        y = {}
        for valueCases in rangeValue:
            query['input']['inputModel']['holdingPeriod'] = holdingPeriod[valueCases]
            response = call_endpoint(scenarios[each_scenario], query)
            irr = response["data"][scenarios_str[each_scenario]]['beforeTaxIRR']
            npv = response["data"][scenarios_str[each_scenario]]['beforeTaxNetProfit']
            x.update({valueCases: npv})
            y.update({valueCases: irr})
        z.update(
            {scenarios_str[each_scenario]: {'beforeTaxNetProfit': x,
                                            'beforeTaxIRR': y}
             })
    whatif.update({'holdingPeriodAnnual': z})
    query['input']['inputModel']['holdingPeriodAnnual'] = holdingPeriod['current']


def down_payment_sens(query):
    ##downPayment

    z = {}
    downPaymentRate = {
        'low': query['input']['inputModel']['downPaymentRate'] * (1 - sensitivity),
        'current': query['input']['inputModel']['downPaymentRate'],
        'high': query['input']['inputModel']['downPaymentRate'] * (1 + sensitivity)
    }
    for each_scenario in range(len(scenarios)):
        x = {}
        y = {}
        for valueCases in rangeValue:
            query['input']['inputModel']['downPaymentRate'] = downPaymentRate[valueCases]
            response = call_endpoint(scenarios[each_scenario], query)
            irr = response["data"][scenarios_str[each_scenario]]['beforeTaxIRR']
            npv = response["data"][scenarios_str[each_scenario]]['beforeTaxNetProfit']
            x.update({valueCases: npv})
            y.update({valueCases: irr})

        z.update(
            {scenarios_str[each_scenario]: {'beforeTaxNetProfit': x,
                                            'beforeTaxIRR': y}
             })
    whatif.update({'downPaymentRate': z})
    query['input']['inputModel']['downPaymentRate'] = downPaymentRate['current']
    # query=originalQuery


##Buy& Sell Expesnse:

def buySell_expenses_sens(query):
    z = {}
    buyRate = {
        'low': query['input']['inputModel']['purchaseExpenseRate'] * (1 - sensitivity),
        'current': query['input']['inputModel']['purchaseExpenseRate'],
        'high': query['input']['inputModel']['purchaseExpenseRate'] * (1 + sensitivity)
    }
    sellRate = {
        'low': query['input']['inputModel']['sellingExpensesRate'] * (1 - sensitivity),
        'current': query['input']['inputModel']['sellingExpensesRate'],
        'high': query['input']['inputModel']['sellingExpensesRate'] * (1 + sensitivity)
    }
    for each_scenario in range(len(scenarios)):
        x = {}
        y = {}
        for valueCases in rangeValue:
            query['input']['inputModel']['sellingExpensesRate'] = sellRate[valueCases]
            query['input']['inputModel']['purchaseExpenseRate'] = buyRate[valueCases]

            response = call_endpoint(scenarios[each_scenario], query)
            irr = response["data"][scenarios_str[each_scenario]]['beforeTaxIRR']
            npv = response["data"][scenarios_str[each_scenario]]['beforeTaxNetProfit']
            x.update({valueCases: npv})
            y.update({valueCases: irr})
            # print(f'{x}')

        z.update(
            {scenarios_str[each_scenario]: {'beforeTaxNetProfit': x,
                                            'beforeTaxIRR': y}
             })
    whatif.update({'transActionCost': z})

    query['input']['inputModel']['sellingExpensesRate'] = sellRate['current']
    query['input']['inputModel']['purchaseExpenseRate'] = buyRate['current']


# income&avoided
def incomeAvoivdedCost_sens(query):
    z = {}
    rent = {
        'low': query['input']['inputModel']['estimatedRent'] * (1 - sensitivity),
        'current': query['input']['inputModel']['estimatedRent'],
        'high': query['input']['inputModel']['estimatedRent'] * (1 + sensitivity)
    }
    shortTermRent = {
        'low': query['input']['inputModel']['estimatedShortTermRent'] * (1 - sensitivity),
        'current': query['input']['inputModel']['estimatedShortTermRent'],
        'high': query['input']['inputModel']['estimatedShortTermRent'] * (1 + sensitivity)
    }
    equivalientRent = {
        'low': query['input']['inputModel']['equivalentRentInsteadBuying'] * (1 - sensitivity),
        'current': query['input']['inputModel']['equivalentRentInsteadBuying'],
        'high': query['input']['inputModel']['equivalentRentInsteadBuying'] * (1 + sensitivity)
    }
    rentRoom = {
        'low': query['input']['inputModel']['estimatedRentAirbnbRoom'] * (1 - sensitivity),
        'current': query['input']['inputModel']['estimatedRentAirbnbRoom'],
        'high': query['input']['inputModel']['estimatedRentAirbnbRoom'] * (1 + sensitivity)
    }

    renterInsurnace = {
        'low': query['input']['inputModel']['annualRentersInsurance'] * (1 - sensitivity),
        'current': query['input']['inputModel']['annualRentersInsurance'],
        'high': query['input']['inputModel']['annualRentersInsurance'] * (1 + sensitivity)
    }

    remodeling = {
        'low': query['input']['inputModel']['improvementCost'] * (1 - sensitivity),
        'current': query['input']['inputModel']['improvementCost'],
        'high': query['input']['inputModel']['improvementCost'] * (1 + sensitivity)
    }

    for each_scenario in range(len(scenarios)):
        x = {}
        y = {}
        for valueCases in rangeValue:
            query['input']['inputModel']['estimatedRent'] = rent[valueCases]
            query['input']['inputModel']['estimatedShortTermRent'] = shortTermRent[valueCases]
            query['input']['inputModel']['equivalentRentInsteadBuying'] = equivalientRent[valueCases]
            query['input']['inputModel']['estimatedRentAirbnbRoom'] = rentRoom[valueCases]
            query['input']['inputModel']['annualRentersInsurance'] = renterInsurnace[valueCases]
            if scenarios_str[each_scenario] == 'flip':
                query['input']['inputModel']['improvementCost'] = remodeling[valueCases]
            response = call_endpoint(scenarios[each_scenario], query)
            irr = response["data"][scenarios_str[each_scenario]]['beforeTaxIRR']
            npv = response["data"][scenarios_str[each_scenario]]['beforeTaxNetProfit']
            x.update({valueCases: npv})
            y.update({valueCases: irr})
        z.update(
            {scenarios_str[each_scenario]: {'beforeTaxNetProfit': x,
                                            'beforeTaxIRR': y}
             })
    whatif.update({'incomeAvoidedCosts': z})

    query['input']['inputModel']['estimatedRent'] = rent['current']
    query['input']['inputModel']['estimatedShortTermRent'] = shortTermRent['current']
    query['input']['inputModel']['equivalentRentInsteadBuying'] = equivalientRent['current']
    query['input']['inputModel']['estimatedRentAirbnbRoom'] = rentRoom['current']
    query['input']['inputModel']['annualRentersInsurance'] = renterInsurnace['current']
    query['input']['inputModel']['improvementCost'] = remodeling["current"]


###operationExpenses
def operationExpesne_sens(query):
    cleaning = {
        'low': query['input']['inputModel']['monthlyCleaningFees'] * (1 - sensitivity),
        'current': query['input']['inputModel']['monthlyCleaningFees'],
        'high': query['input']['inputModel']['monthlyCleaningFees'] * (1 + sensitivity)
    }
    hoa = {
        'low': query['input']['inputModel']['monthlyHOA'] * (1 - sensitivity),
        'current': query['input']['inputModel']['monthlyHOA'],
        'high': query['input']['inputModel']['monthlyHOA'] * (1 + sensitivity)
    }
    advertising = {
        'low': query['input']['inputModel']['annualAdvertising'] * (1 - sensitivity),
        'current': query['input']['inputModel']['annualAdvertising'],
        'high': query['input']['inputModel']['annualAdvertising'] * (1 + sensitivity)
    }
    management = {
        'low': query['input']['inputModel']['annualManagementPercentage'] * (1 - sensitivity),
        'current': query['input']['inputModel']['annualManagementPercentage'],
        'high': query['input']['inputModel']['annualManagementPercentage'] * (1 + sensitivity)
    }
    maintenancerepair = {
        'low': query['input']['inputModel']['monthlyMaintenanceRepair'] * (1 - sensitivity),
        'current': query['input']['inputModel']['monthlyMaintenanceRepair'],
        'high': query['input']['inputModel']['monthlyMaintenanceRepair'] * (1 + sensitivity)
    }
    propertytax = {
        'low': query['input']['inputModel']['propertyTaxPercentage'] * (1 - sensitivity),
        'current': query['input']['inputModel']['propertyTaxPercentage'],
        'high': query['input']['inputModel']['propertyTaxPercentage'] * (1 + sensitivity)
    }
    insurance = {
        'low': query['input']['inputModel']['propertyInsurancePercentage'] * (1 - sensitivity),
        'current': query['input']['inputModel']['propertyInsurancePercentage'],
        'high': query['input']['inputModel']['propertyInsurancePercentage'] * (1 + sensitivity)
    }
    utilities = {
        'low': query['input']['inputModel']['monthlyUtilities'] * (1 - sensitivity),
        'current': query['input']['inputModel']['monthlyUtilities'],
        'high': query['input']['inputModel']['monthlyUtilities'] * (1 + sensitivity)
    }

    z = {}
    for each_scenario in range(len(scenarios)):
        x = {}
        y = {}
        for valueCases in rangeValue:
            query['input']['inputModel']['monthlyCleaningFees'] = cleaning[valueCases]
            query['input']['inputModel']['monthlyHOA'] = hoa[valueCases]
            query['input']['inputModel']['annualAdvertising'] = advertising[valueCases]
            query['input']['inputModel']['annualManagementPercentage'] = management[valueCases]
            query['input']['inputModel']['monthlyMaintenanceRepair'] = maintenancerepair[valueCases]
            query['input']['inputModel']['propertyTaxPercentage'] = propertytax[valueCases]
            query['input']['inputModel']['propertyInsurancePercentage'] = insurance[valueCases]
            query['input']['inputModel']['monthlyUtilities'] = utilities[valueCases]

            response = call_endpoint(scenarios[each_scenario], query)
            irr = response["data"][scenarios_str[each_scenario]]['beforeTaxIRR']
            npv = response["data"][scenarios_str[each_scenario]]['beforeTaxNetProfit']
            x.update({valueCases: npv})
            y.update({valueCases: irr})
        z.update(
            {scenarios_str[each_scenario]: {'beforeTaxNetProfit': x,
                                            'beforeTaxIRR': y}
             })
    whatif.update({'operationExpenses': z})
    query['input']['inputModel']['monthlyCleaningFees'] = cleaning['current']
    query['input']['inputModel']['monthlyHOA'] = hoa['current']
    query['input']['inputModel']['annualAdvertising'] = advertising['current']
    query['input']['inputModel']['annualManagementPercentage'] = management['current']
    query['input']['inputModel']['monthlyMaintenanceRepair'] = maintenancerepair['current']
    query['input']['inputModel']['propertyTaxPercentage'] = propertytax['current']
    query['input']['inputModel']['propertyInsurancePercentage'] = insurance['current']
    query['input']['inputModel']['monthlyUtilities'] = utilities['current']


##SellPrice
def sellPrice_sens(query):
    appreciation = {
        'low': query['input']['inputModel']['propertyAppreciation'] * (1 - sensitivity),
        'current': query['input']['inputModel']['propertyAppreciation'],
        'high': query['input']['inputModel']['propertyAppreciation'] * (1 + sensitivity)
    }
    ValueRateImprovement = {
        'low': query['input']['inputModel']['addedValueRateImprovement'] * (1 - sensitivity),
        'current': query['input']['inputModel']['addedValueRateImprovement'],
        'high': query['input']['inputModel']['addedValueRateImprovement'] * (1 + sensitivity)
    }
    z = {}

    for each_scenario in range(len(scenarios)):
        x = {}
        y = {}
        for valueCases in rangeValue:
            query['input']['inputModel']['propertyAppreciation'] = appreciation[valueCases]
            if scenarios_str[each_scenario] == 'flip':
                query['input']['inputModel']['addedValueRateImprovement'] = ValueRateImprovement[valueCases]
            response = call_endpoint(scenarios[each_scenario], query)
            irr = response["data"][scenarios_str[each_scenario]]['beforeTaxIRR']
            npv = response["data"][scenarios_str[each_scenario]]['beforeTaxNetProfit']
            x.update({valueCases: npv})
            y.update({valueCases: irr})
        z.update(
            {scenarios_str[each_scenario]: {'beforeTaxNetProfit': x,
                                            'beforeTaxIRR': y}
             })
    whatif.update({'SellPrice': z})

    query['input']['inputModel']['propertyAppreciation'] = appreciation['current']
    query['input']['inputModel']['addedValueRateImprovement'] = ValueRateImprovement['current']


def main(input_json):
    query = extended_endpoints(input_json)
    purchase_price_sens(query)
    holding_period_sens(query)
    down_payment_sens(query)
    buySell_expenses_sens(query)
    incomeAvoivdedCost_sens(query)
    operationExpesne_sens(query)
    sellPrice_sens(query)

    with open('../json/whatif.json', 'w') as outfile:
        json.dump(whatif, outfile, indent=3)

# def holding_period_check():
#     query= extended_endpoints()
#     ## create the input model request json.
#     input_model = short['calculationData']['inputModel']
#     request['input']['inputModel'] = input_model
#     query['input']['inputModel']['holdingPeriod']=240
#     # call endpoints
#     response= call_endpoint(budgetUse,query)
#     print(response['data']['budgetUse']['beforeTaxNetProfit'])
#     npv_list=response['data']['budgetUse']['beforeTaxProfit']
#     for i in range(len(npv_list)):
#         query['input']['inputModel']['holdingperiod'] = 12*(i+3)
#         response = call_endpoint(budgetUse, query)
#         npv_each_year=response['data']['budgetUse']['beforeTaxNetProfit']
#         print(i+3,npv_each_year,npv_list[i+2])
#
#
# def npv_for_year_30(query):
#     ## create the input model request json.
#     input_model = short['calculationData']['inputModel']
#     request['input']['inputModel'] = input_model
#     query=request
#     query['input']['inputModel']['holdingPeriod']=360
#
#     ##
#     with open("flip.json") as json_file:
#         flip = json.load(json_file)
#         flip = flip["data"]["flip"]
#     with open("primary.json") as json_file:
#         private = json.load(json_file)
#         private = private["data"]["privateUse"]
#     with open("budget.json") as json_file:
#         budget = json.load(json_file)
#         budget = budget["data"]["budgetUse"]
#     with open("rental.json") as json_file:
#         rental = json.load(json_file)
#         rental = rental["data"]["rental"]
#     with open("shortTerm.json") as json_file:
#         shortTerm = json.load(json_file)
#         shortTerm = shortTerm["data"]["shortTerm"]
#     with open("dashboard.json") as json_file:
#         dashboard = json.load(json_file)
#         dashboard = dashboard["data"]["benchmarkExtended"]
#
#     ## call endpoints
#     budgetScenario=call_endpoint(budgetUse,query)
#     with open ('budget.json','w') as outfile:
#         json.dump(budgetScenario,outfile,indent=3)
#
#     flipScenario=call_endpoint(flip,request)
#     with open ('flip.json','w') as outfile:
#         json.dump(flipScenario,outfile,indent=3)
#
#     primaryScenario=call_endpoint(privateUse,request)
#     with open ('primary.json','w') as outfile:
#         json.dump(primaryScenario,outfile,indent=3)
#
#     vacationScenario=call_endpoint(shortTerm,request)
#     with open ('shortTerm.json','w') as outfile:
#         json.dump(vacationScenario,outfile,indent=3)
#
#     rentalScenario=call_endpoint(rental,request)
#     with open ('rental.json','w') as outfile:
#         json.dump(rentalScenario,outfile,indent=3)
#
#     dashboardScenario=call_endpoint(dashboard,request)
#     with open ('dashboard.json','w') as outfile:
#         json.dump(dashboardScenario,outfile,indent=3)
#
#     return (query)
