import requests
import json

with open("../json/request_structure.json") as json_file:
    query = json.load(json_file)

originalQuery=query
budgetUse= 'http://calculationservice.dev.zillmeterinternal.com/api/v1/IntegrationUnit/BudgetUseExtended'
flip= 'http://calculationservice.dev.zillmeterinternal.com/api/v1/IntegrationUnit/FlipExtended'
privateUse='http://calculationservice.dev.zillmeterinternal.com/api/v1/IntegrationUnit/PrivateUseExtended'
rental='http://calculationservice.dev.zillmeterinternal.com/api/v1/IntegrationUnit/RentalExtended'
shortTerm='http://calculationservice.dev.zillmeterinternal.com/api/v1/IntegrationUnit/ShortTermRentalExtended'
sensitivity=0.15

def call_endpoint(scenario,request_json):
    response = requests.post(url=scenario, json=request_json).json()
    return response


scenarios= [budgetUse,privateUse,rental,shortTerm,flip]
scenarios_str= ['budgetUse','privateUse','rental','shortTerm','flip']
rangeValue=['low','high','current']
whatif={}


##Purchase Price

z={}

purchasePrice={
    'low':query['input']['inputModel']['purchasePrice']*(1-sensitivity),
    'current':query['input']['inputModel']['purchasePrice'],
    'high':query['input']['inputModel']['purchasePrice']*(1+sensitivity)
}
for each_scenario in range(len(scenarios)):
    x = {}
    y = {}
    for valueCases in rangeValue:
        query['input']['inputModel']['purchasePrice'] = purchasePrice[valueCases]
        response = call_endpoint(scenarios[each_scenario],query)
        irr= response["data"][scenarios_str[each_scenario]]['beforeTaxIRR']
        npv= response["data"][scenarios_str[each_scenario]]['beforeTaxNetProfit']
        x.update({valueCases:npv})
        y.update({valueCases:irr})
    z.update(
         {scenarios_str[each_scenario]: {'beforeTaxNetProfit': x,
                            'beforeTaxIRR': y}
          })
whatif.update({'purchasePrice':z})

query['input']['inputModel']['purchasePrice'] = purchasePrice['current']

##Holding Period

z={}
holdingPeriod={
    'low':12*round(query['input']['inputModel']['holdingperiod']*(1-sensitivity)/12),
    'current':query['input']['inputModel']['holdingperiod'],
    'high':12*round(query['input']['inputModel']['holdingperiod']*(1+sensitivity)/12)
}
for each_scenario in range(len(scenarios)):
    x = {}
    y = {}
    for valueCases in rangeValue:
        query['input']['inputModel']['holdingPeriod'] = holdingPeriod[valueCases]
        response = call_endpoint(scenarios[each_scenario],query)
        irr= response["data"][scenarios_str[each_scenario]]['beforeTaxIRR']
        npv= response["data"][scenarios_str[each_scenario]]['beforeTaxNetProfit']
        x.update({valueCases:npv})
        y.update({valueCases:irr})
    z.update(
         {scenarios_str[each_scenario]: {'beforeTaxNetProfit': x,
                            'beforeTaxIRR': y}
          })
whatif.update({'holdingPeriod':z})
query['input']['inputModel']['holdingPeriod'] = holdingPeriod['current']

##downPayment


z={}
DownPaymentRate={
    'low':query['input']['inputModel']['DownPaymentRate']*(1-sensitivity),
    'current':query['input']['inputModel']['DownPaymentRate'],
    'high':query['input']['inputModel']['DownPaymentRate']*(1+sensitivity)
}
for each_scenario in range(len(scenarios)):
    x = {}
    y = {}
    for valueCases in rangeValue:
        query['input']['inputModel']['DownPaymentRate'] = DownPaymentRate[valueCases]
        response = call_endpoint(scenarios[each_scenario],query)
        irr= response["data"][scenarios_str[each_scenario]]['beforeTaxIRR']
        npv= response["data"][scenarios_str[each_scenario]]['beforeTaxNetProfit']
        x.update({valueCases:npv})
        y.update({valueCases:irr})

    z.update(
         {scenarios_str[each_scenario]: {'beforeTaxNetProfit': x,
                            'beforeTaxIRR': y}
          })
whatif.update({'DownPaymentRate':z})
query['input']['inputModel']['DownPaymentRate'] = DownPaymentRate['current']

# query=originalQuery

##Buy& Sell Expesnse:

z={}
buyRate={
    'low':query['input']['inputModel']['purchaseExpenseRate']*(1-sensitivity),
    'current':query['input']['inputModel']['purchaseExpenseRate'],
    'high':query['input']['inputModel']['purchaseExpenseRate']*(1+sensitivity)
}
sellRate={
    'low':query['input']['inputModel']['sellingExpensesRate']*(1-sensitivity),
    'current':query['input']['inputModel']['sellingExpensesRate'],
    'high':query['input']['inputModel']['sellingExpensesRate']*(1+sensitivity)
}
for each_scenario in range(len(scenarios)):
    x = {}
    y = {}
    for valueCases in rangeValue:
        query['input']['inputModel']['sellingExpensesRate'] = sellRate[valueCases]
        query['input']['inputModel']['purchaseExpenseRate'] = buyRate[valueCases]

        response = call_endpoint(scenarios[each_scenario],query)
        irr= response["data"][scenarios_str[each_scenario]]['beforeTaxIRR']
        npv= response["data"][scenarios_str[each_scenario]]['beforeTaxNetProfit']
        x.update({valueCases:npv})
        y.update({valueCases:irr})
        # print(f'{x}')

    z.update(
         {scenarios_str[each_scenario]: {'beforeTaxNetProfit': x,
                            'beforeTaxIRR': y}
          })
whatif.update({'transActionCost':z})

query['input']['inputModel']['sellingExpensesRate'] = sellRate['current']
query['input']['inputModel']['purchaseExpenseRate'] = buyRate['current']


#income&avoided

z={}
rent={
    'low':query['input']['inputModel']['EstimatedRent']*(1-sensitivity),
    'current':query['input']['inputModel']['EstimatedRent'],
    'high':query['input']['inputModel']['EstimatedRent']*(1+sensitivity)
}
shortTermRent={
    'low':query['input']['inputModel']['estimatedshorttermrent']*(1-sensitivity),
    'current':query['input']['inputModel']['estimatedshorttermrent'],
    'high':query['input']['inputModel']['estimatedshorttermrent']*(1+sensitivity)
}
equivalientRent={
    'low':query['input']['inputModel']['equivalentRentInsteadBuying']*(1-sensitivity),
    'current':query['input']['inputModel']['equivalentRentInsteadBuying'],
    'high':query['input']['inputModel']['equivalentRentInsteadBuying']*(1+sensitivity)
}
rentRoom={
    'low':query['input']['inputModel']['estimatedRentAirbnbRoom']*(1-sensitivity),
    'current':query['input']['inputModel']['estimatedRentAirbnbRoom'],
    'high':query['input']['inputModel']['estimatedRentAirbnbRoom']*(1+sensitivity)
}

renterInsurnace={
    'low':query['input']['inputModel']['annualRentersInsurance']*(1-sensitivity),
    'current':query['input']['inputModel']['annualRentersInsurance'],
    'high':query['input']['inputModel']['annualRentersInsurance']*(1+sensitivity)
}

remodeling={
    'low':query['input']['inputModel']['ImprovementCost']*(1-sensitivity),
    'current':query['input']['inputModel']['ImprovementCost'],
    'high':query['input']['inputModel']['ImprovementCost']*(1+sensitivity)
}


for each_scenario in range(len(scenarios)):
    x = {}
    y = {}
    for valueCases in rangeValue:
        query['input']['inputModel']['EstimatedRent'] = rent[valueCases]
        query['input']['inputModel']['estimatedshorttermrent'] = shortTermRent[valueCases]
        query['input']['inputModel']['equivalentRentInsteadBuying'] = equivalientRent[valueCases]
        query['input']['inputModel']['estimatedRentAirbnbRoom'] = rentRoom[valueCases]
        query['input']['inputModel']['annualRentersInsurance'] = renterInsurnace[valueCases]
        if scenarios_str[each_scenario] == 'flip':
            query['input']['inputModel']['ImprovementCost'] = remodeling[valueCases]
        response = call_endpoint(scenarios[each_scenario],query)
        irr= response["data"][scenarios_str[each_scenario]]['beforeTaxIRR']
        npv= response["data"][scenarios_str[each_scenario]]['beforeTaxNetProfit']
        x.update({valueCases:npv})
        y.update({valueCases:irr})
    z.update(
         {scenarios_str[each_scenario]: {'beforeTaxNetProfit': x,
                            'beforeTaxIRR': y}
          })
whatif.update({'incomeAvoidedCosts':z})

query['input']['inputModel']['EstimatedRent'] = rent['current']
query['input']['inputModel']['estimatedshorttermrent'] = shortTermRent['current']
query['input']['inputModel']['equivalentRentInsteadBuying'] = equivalientRent['current']
query['input']['inputModel']['estimatedRentAirbnbRoom'] = rentRoom['current']
query['input']['inputModel']['annualRentersInsurance'] = renterInsurnace['current']
query['input']['inputModel']['ImprovementCost'] = remodeling["current"]


###operationExpenses

cleaning={
    'low':query['input']['inputModel']['monthlycleaningfees']*(1-sensitivity),
    'current':query['input']['inputModel']['monthlycleaningfees'],
    'high':query['input']['inputModel']['monthlycleaningfees']*(1+sensitivity)
}
hoa={
    'low':query['input']['inputModel']['monthlyhoa']*(1-sensitivity),
    'current':query['input']['inputModel']['monthlyhoa'],
    'high':query['input']['inputModel']['monthlyhoa']*(1+sensitivity)
}
advertising={
    'low':query['input']['inputModel']['annualadvertising']*(1-sensitivity),
    'current':query['input']['inputModel']['annualadvertising'],
    'high':query['input']['inputModel']['annualadvertising']*(1+sensitivity)
}
management={
    'low':query['input']['inputModel']['annualmanagementpercentage']*(1-sensitivity),
    'current':query['input']['inputModel']['annualmanagementpercentage'],
    'high':query['input']['inputModel']['annualmanagementpercentage']*(1+sensitivity)
}
maintenancerepair={
    'low':query['input']['inputModel']['monthlymaintenancerepair']*(1-sensitivity),
    'current':query['input']['inputModel']['monthlymaintenancerepair'],
    'high':query['input']['inputModel']['monthlymaintenancerepair']*(1+sensitivity)
}
propertytax={
    'low':query['input']['inputModel']['propertytaxpercentage']*(1-sensitivity),
    'current':query['input']['inputModel']['propertytaxpercentage'],
    'high':query['input']['inputModel']['propertytaxpercentage']*(1+sensitivity)
}
insurance={
    'low':query['input']['inputModel']['propertyinsurancepercentage']*(1-sensitivity),
    'current':query['input']['inputModel']['propertyinsurancepercentage'],
    'high':query['input']['inputModel']['propertyinsurancepercentage']*(1+sensitivity)
}
utilities={
    'low':query['input']['inputModel']['monthlyutilities']*(1-sensitivity),
    'current':query['input']['inputModel']['monthlyutilities'],
    'high':query['input']['inputModel']['monthlyutilities']*(1+sensitivity)
}

query=originalQuery

z={}
for each_scenario in range(len(scenarios)):
    x = {}
    y = {}
    for valueCases in rangeValue:
        query['input']['inputModel']['monthlycleaningfees'] = cleaning[valueCases]
        query['input']['inputModel']['monthlyhoa'] = hoa[valueCases]
        query['input']['inputModel']['annualadvertising'] = advertising[valueCases]
        query['input']['inputModel']['annualmanagementpercentage'] = management[valueCases]
        query['input']['inputModel']['monthlymaintenancerepair'] = maintenancerepair[valueCases]
        query['input']['inputModel']['propertytaxpercentage'] = propertytax[valueCases]
        query['input']['inputModel']['propertyinsurancepercentage'] = insurance[valueCases]
        query['input']['inputModel']['monthlyutilities'] = utilities[valueCases]

        response = call_endpoint(scenarios[each_scenario],query)
        irr= response["data"][scenarios_str[each_scenario]]['beforeTaxIRR']
        npv= response["data"][scenarios_str[each_scenario]]['beforeTaxNetProfit']
        x.update({valueCases:npv})
        y.update({valueCases:irr})
    z.update(
         {scenarios_str[each_scenario]: {'beforeTaxNetProfit': x,
                            'beforeTaxIRR': y}
          })
whatif.update({'operationExpenses':z})
query['input']['inputModel']['monthlycleaningfees'] = cleaning['current']
query['input']['inputModel']['monthlyhoa'] = hoa['current']
query['input']['inputModel']['annualadvertising'] = advertising['current']
query['input']['inputModel']['annualmanagementpercentage'] = management['current']
query['input']['inputModel']['monthlymaintenancerepair'] = maintenancerepair['current']
query['input']['inputModel']['propertytaxpercentage'] = propertytax['current']
query['input']['inputModel']['propertyinsurancepercentage'] = insurance['current']
query['input']['inputModel']['monthlyutilities'] = utilities['current']

##SellPrice


appreciation={
    'low':query['input']['inputModel']['propertyappreciation']*(1-sensitivity),
    'current':query['input']['inputModel']['propertyappreciation'],
    'high':query['input']['inputModel']['propertyappreciation']*(1+sensitivity)
}
ValueRateImprovement={
    'low':query['input']['inputModel']['AddedValueRateImprovement']*(1-sensitivity),
    'current':query['input']['inputModel']['AddedValueRateImprovement'],
    'high':query['input']['inputModel']['AddedValueRateImprovement']*(1+sensitivity)
}
z={}

for each_scenario in range(len(scenarios)):
    x = {}
    y = {}
    for valueCases in rangeValue:
        query['input']['inputModel']['propertyappreciation'] = appreciation[valueCases]
        if scenarios_str[each_scenario] == 'flip':
            query['input']['inputModel']['AddedValueRateImprovement'] = ValueRateImprovement[valueCases]
        response = call_endpoint(scenarios[each_scenario],query)
        irr= response["data"][scenarios_str[each_scenario]]['beforeTaxIRR']
        npv= response["data"][scenarios_str[each_scenario]]['beforeTaxNetProfit']
        x.update({valueCases:npv})
        y.update({valueCases:irr})
    z.update(
         {scenarios_str[each_scenario]: {'beforeTaxNetProfit': x,
                            'beforeTaxIRR': y}
          })
whatif.update({'SellPrice':z})

query['input']['inputModel']['propertyappreciation'] = appreciation['current']
query['input']['inputModel']['AddedValueRateImprovement'] = ValueRateImprovement['current']

with open ('../json/whatif.json', 'w') as outfile:
    json.dump(whatif,outfile,indent=3)

