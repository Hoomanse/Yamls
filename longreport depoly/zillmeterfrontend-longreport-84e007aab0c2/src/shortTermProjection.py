from __future__ import print_function
from mailmerge import MailMerge
import plotly.graph_objects as go
from fpdf import FPDF
import PyPDF2 as pypdf
import json
from PyPDF2 import PdfFileMerger, PdfFileReader
import os
from pdf_generator import word_to_pdf


def initialize():
    with open("../json/shortTerm.json") as json_file:
        shortTerm = json.load(json_file)
        shortTerm = shortTerm["data"]["shortTerm"]
    return shortTerm


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


def overlay(infile, over, out):
    with open(f'{infile}.pdf', "rb") as inFile, open(f'{over}.pdf', "rb") as overlay:
        original = pypdf.PdfFileReader(inFile)
        background = original.getPage(2)
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


def wordPopulate(template, out, property_address, pdfFileProperties, shortTerm):
    pageNumber = pdfFileProperties['pageStart']
    pagesTotalNumber = 4
    pdfFileProperties['tableContent'].update(
        {pageNumber: 'Comprehensive Financial Report – Vacation Rental Detailed Financial Analytics',
         pageNumber + 1: 'Comprehensive Financial Report - Vacation Rental Cash Flow Projection',
         pageNumber + 3: 'Comprehensive Financial Report - Rental Tax Calculation'})
    pdfFileProperties['pageStart'] = pageNumber + pagesTotalNumber

    if shortTerm['genericInput']['applyImprovementAllScenarios'] == False:
        shortTerm['genericInput']['improvementCost'] = 0

    template = f'{template}.docx'
    document = MailMerge(template)
    hp = shortTerm['genericInput']['holdingPeriodAnnual']
    yr = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}
    rentpayment = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}
    utility = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}
    rentInsuarnce = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}
    subBTCash = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}
    subIncomeTax = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}
    subATCash = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}
    loan = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}
    income = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}
    operation = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}
    BTcashFlow = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}
    incometax = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}
    taxCredit = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}
    ATcashFlow = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}
    BTAdvantage = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}
    ATAdvantage = {1: '-', 2: '-', 3: '-', 4: '-', 5: '-'}

    if hp == 2:
        arrays = [1, 5]
        years = [1, 2]

    elif hp == 3:
        arrays = [1, 3, 5]
        years = [1, 2, 3]
    elif hp == 4:
        arrays = [1, 2, 3, 5]
        years = [1, 2, 3, 4]
    else:
        arrays = [1, 2, 3, 4, 5]
        years = [1, round(hp * 2 / 5), round(hp * 3 / 5), round(hp * 4 / 5), round(hp)]

    for item in range(len(arrays)):
        yr[arrays[item]] = f'Year {years[item]}'
        # # rentpayment[arrays[item]]=fin_value(shortTerm['cashFlowProjection']['financialProjectionSummary']['income'][item])
        # utility[arrays[item]]=fin_value(shortTerm['cashFlowProjection']['cashFlowProjectionSubstitution']['utility'][item+1])
        # rentInsuarnce[arrays[item]]=fin_value(shortTerm['cashFlowProjection']['cashFlowProjectionSubstitution']['rentersInsurance'][item+1])
        # subBTCash[arrays[item]]=fin_value(shortTerm['cashFlowProjection']['cashFlowProjectionSubstitution']['beforeTaxCashFlow'][item+1])
        # subIncomeTax[arrays[item]]=fin_value(shortTerm['cashFlowProjection']['cashFlowProjectionSubstitution']['incomeTax'][item+1])
        # subATCash[arrays[item]]=fin_value(shortTerm['cashFlowProjection']['cashFlowProjectionSubstitution']['afterTaxCashFlow'][item+1])
        loan[arrays[item]] = fin_value(shortTerm['financialProjectionSummary']['loanPayments'][item])
        income[arrays[item]] = fin_value(shortTerm['financialProjectionSummary']['income'][item])
        operation[arrays[item]] = fin_value(shortTerm['financialProjectionSummary']['operationExpenses'][item])
        BTcashFlow[arrays[item]] = fin_value(
            shortTerm['cashFlowProjection']['cashFlowProjectionPurchased']['beforeTaxCashFlow'][item + 1])
        ATcashFlow[arrays[item]] = fin_value(
            shortTerm['cashFlowProjection']['cashFlowProjectionPurchased']['afterTaxCashFlow'][item + 1])
        incometax[arrays[item]] = fin_value(
            min(shortTerm['cashFlowProjection']['cashFlowProjectionPurchased']['incomeTax'][item + 1], 0))
        # taxCredit[arrays[item]]=fin_value(max(shortTerm['cashFlowProjection']['cashFlowProjectionPurchased']['taxSaving'][item+1],0))
        # BTAdvantage[arrays[item]]=fin_value(shortTerm['beforeTaxNetAdvantage'][item+1])
        # ATAdvantage[arrays[item]]=fin_value(shortTerm['afterTaxNetAdvantage'][item+1])

    interestPaid = shortTerm['mortgage']['interest'][0]
    adjustedBasis = shortTerm['genericInput']['purchasePrice'] * (
                1 + shortTerm['genericInput']['purchaseExpenseRate']) + shortTerm['genericInput']['improvementCost'] - \
                    shortTerm['taxProjection']['taxDepreciationRecapture'] / shortTerm['genericInput'][
                        'depreciationRecaptureRate']

    # for the case with 0% down payement:
    if 'beforeTaxEquityDividendRate' in shortTerm and shortTerm['beforeTaxEquityDividendRate'] != None:
        beforeTaxEquityDividendRate = rate_value(shortTerm['beforeTaxEquityDividendRate'])
        afterTaxEquityDividendRate = rate_value(shortTerm['afterTaxEquityDividendRate'])
    else:
        beforeTaxEquityDividendRate = '-'
        afterTaxEquityDividendRate = '-'

    document.merge(ADR=property_address,
                   PG1=page_value(pageNumber), PG2=page_value(pageNumber + 1), PG3=page_value(pageNumber + 2),
                   PG4=page_value(pageNumber + 3))

    ##there is an issue on the backend with the tax calc (it's passing the item # 0 instead of #1 so it's always null
    taxableIncome = shortTerm['taxProjection']['netOperatingIncome'] + shortTerm['taxProjection'][
        'taxDepreciationRecapture'] / shortTerm['genericInput']['depreciationRecaptureRate'] / hp * -1 + interestPaid
    taxPayable = shortTerm['genericInput']['taxRate'] * taxableIncome

    taxableIncome = max(taxableIncome, 0)
    taxPayable = min(0, taxPayable * -1)

    cust_1 = {'PG1': property_address, 'PG2': page_value(pageNumber + 1), 'PG3': page_value(pageNumber + 2),
              'PG4': page_value(pageNumber + 3),
              'ADR': property_address,
              # 'EQR':fin_value(shortTerm['genericInput']['equivalentRentInsteadBuying']),
              'STRENT': fin_value(shortTerm['genericInput']['estimatedShortTermRent']),
              # 'ROM':str(shortTerm['genericInput']['numberRoomsPartiallyRented']),
              'STVR': rate_value(shortTerm['genericInput']['estimatedShortTermVacancy']),
              'HP': str(shortTerm['genericInput']['holdingPeriodAnnual']),
              'PP': fin_value(shortTerm['genericInput']['purchasePrice']),
              'IC': fin_value(shortTerm['genericInput']['improvementCost']),
              'PE': fin_value(shortTerm['purchaseExpense']),
              'ICAV': fin_value(shortTerm['genericInput']['improvementCost'] * (
                          1 + shortTerm['genericInput']['addedValueRateImprovement'])),
              'GSP': fin_value(shortTerm['sellPrice']),
              'SE': fin_value(shortTerm['sellingExpense']),
              'SEN': fin_value(-1 * shortTerm['sellingExpense']),
              'NSE': fin_value(shortTerm["financialProjectionSummary"]['netSalePrice']),
              'APT': fin_value(
                  shortTerm['genericInput']['propertyTaxPercentage'] * shortTerm['genericInput']['purchasePrice']),
              'API': fin_value(shortTerm['genericInput']['propertyInsurancePercentage'] * shortTerm['genericInput'][
                  'purchasePrice']),
              'ACF': fin_value(shortTerm['advertisingFee'] * 12),
              'AHOA': fin_value(shortTerm['genericInput']['monthlyHOA'] * 12),
              'AU': fin_value(shortTerm['managementFee'] * 12),
              'ANUT': fin_value(shortTerm['utility'] * 12),
              'ANCF': fin_value(shortTerm['genericInput']['monthlyCleaningFees'] * 12),
              'ANAC': fin_value(shortTerm['commission'] * 12),
              'ARM': fin_value(shortTerm['repairMaintenance'] * 12),
              'AOE': fin_value(shortTerm["taxProjection"]['operatingExpenses'] * -1),
              'ASD': fin_value(shortTerm['genericInput']['renterSecurityDeposit']),
              'ARI': fin_value(shortTerm['genericInput']['annualRentersInsurance']),
              'ACR': rate_value(shortTerm['genericInput']['airbnbCommissionRate']),
              'EMI': fin_value(shortTerm['taxProjection']['income'] / 12),
              'MOE': fin_value(shortTerm['taxProjection']['operatingExpenses'] / -12),
              'NMI': fin_value(shortTerm['taxProjection']['netOperatingIncome'] / 12),
              'P': str(hp),
              'YR1': yr[1], 'YR2': yr[2], 'YR3': yr[3], 'YR4': yr[4], 'YR5': yr[5],
              'RP1': rentpayment[1], 'RP2': rentpayment[2], 'RP3': rentpayment[3], 'RP4': rentpayment[4],
              'RP5': rentpayment[5],
              'UT1': utility[1], 'UT2': utility[2], 'UT3': utility[3], 'UT4': utility[4], 'UT5': utility[5],
              'SD': fin_value(shortTerm['genericInput']['renterSecurityDeposit'] * -1),
              'RIN1': rentInsuarnce[1], 'RIN2': rentInsuarnce[2], 'RIN3': rentInsuarnce[3], 'RIN4': rentInsuarnce[4],
              'RIN5': rentInsuarnce[5],
              'RCI': fin_value(0),
              'SBT1': subBTCash[1], 'SBT2': subBTCash[2], 'SBT3': subBTCash[3], 'SBT4': subBTCash[4],
              'SBT5': subBTCash[5],
              'SBT0': fin_value(0),
              'SIC': fin_value(0),
              'SAT1': subATCash[1], 'SAT2': subATCash[2], 'SAT3': subATCash[3], 'SAT4': subATCash[4],
              'SAT5': subATCash[5],
              'SAT0': fin_value(0),
              'ICA': fin_value(shortTerm['initialCash'] * -1),
              'L1': loan[1], 'L2': loan[2], 'L3': loan[3], 'L4': loan[4], 'L5': loan[5],
              'RI1': income[1], 'RI2': income[2], 'RI3': income[3], 'RI4': income[4], 'RI5': income[5],
              'OE1': operation[1], 'OE2': operation[2], 'OE3': operation[3], 'OE4': operation[4], 'OE5': operation[5],
              'BSP': fin_value(shortTerm['beforeTaxEquityReversion']),
              'BT0': fin_value(shortTerm['cashFlowProjection']['cashFlowProjectionPurchased']['beforeTaxCashFlow'][0]),
              'BT1': BTcashFlow[1], 'BT2': BTcashFlow[2], 'BT3': BTcashFlow[3], 'BT4': BTcashFlow[4],
              'BT5': BTcashFlow[5],
              'TDS': fin_value(shortTerm['taxProjection']['totalTaxDue'] * -1),
              'AT0': fin_value(shortTerm['cashFlowProjection']['cashFlowProjectionPurchased']['afterTaxCashFlow'][0]),
              'AT1': ATcashFlow[1], 'AT2': ATcashFlow[2], 'AT3': ATcashFlow[3], 'AT4': ATcashFlow[4],
              'AT5': ATcashFlow[5],
              'BTA0': fin_value(0),
              'ATA0': fin_value(0),
              'BTA1': BTAdvantage[1], 'BTA2': BTAdvantage[2], 'BTA3': BTAdvantage[3], 'BTA4': BTAdvantage[4],
              'BTA5': BTAdvantage[5],
              'IT1': incometax[1], 'IT2': incometax[2], 'IT3': incometax[3], 'IT4': incometax[4], 'IT5': incometax[5],
              'ITS1': taxCredit[1], 'ITS2': taxCredit[2], 'ITS3': taxCredit[3], 'ITS4': taxCredit[4],
              'ITS5': taxCredit[5],
              'ATA1': ATAdvantage[1], 'ATA2': ATAdvantage[2], 'ATA3': ATAdvantage[3], 'ATA4': ATAdvantage[4],
              'ATA5': ATAdvantage[5],
              'BIR': rate_value(shortTerm['beforeTaxIRR']),
              'AIR': rate_value(shortTerm['afterTaxIRR']),
              'BPV': fin_value(shortTerm['beforeTaxNetProfit']),
              'ATV': fin_value(shortTerm['cashFlowProjection']['netProfitAfterTax']),
              'GI': fin_value(shortTerm['taxProjection']['income']),
              'OE': fin_value(shortTerm['taxProjection']['operatingExpenses']),
              'NOI': fin_value(shortTerm['taxProjection']['netOperatingIncome']),
              # 'PT':fin_value(shortTerm['taxProjection']['propertyTax']),
              'DEP': fin_value(shortTerm['taxProjection']['taxDepreciationRecapture'] / shortTerm['genericInput'][
                  'depreciationRecaptureRate'] / hp * -1),
              'IN': fin_value(interestPaid),
              'TI': fin_value(taxableIncome),
              'MTR': rate_value(shortTerm['genericInput']['taxRate']),
              'TAX': fin_value(taxPayable),
              # 'TAXS':fin_value(shortTerm['taxProjection']['taxSavings']),
              'ESP': fin_value(shortTerm['taxProjection']['estimatedSalePrice']),
              'NSP': fin_value(shortTerm['taxProjection']['netSalePrice']),
              'PPI': fin_value(shortTerm['genericInput']['improvementCost'] + shortTerm['purchaseExpense']),
              'ACDP': fin_value(-1 * shortTerm['taxProjection']['taxDepreciationRecapture'] / shortTerm['genericInput'][
                  'depreciationRecaptureRate']),
              'AJB': fin_value(adjustedBasis),
              'AJBN': fin_value(-1 * adjustedBasis),
              'GRS': fin_value(shortTerm['gainRealizedSale']),
              'DEPR': fin_value(-1 * shortTerm['taxProjection']['taxDepreciationRecapture'] / shortTerm['genericInput'][
                  'depreciationRecaptureRate']),
              'GS': fin_value(shortTerm['gainRecognizedSale']),
              'TDRE': fin_value(-1 * shortTerm['taxProjection']['taxDepreciationRecapture']),
              'TCAP': fin_value(-1 * shortTerm['taxProjection']['taxCapitalGain']),
              'TTX': fin_value(-1 * shortTerm['taxProjection']['totalTaxDue']),
              'DR': rate_value(shortTerm['genericInput']['depreciationRecaptureRate']),
              'CR': rate_value(shortTerm['genericInput']['capitalGainTaxRate']),
              'ACCDP': fin_value(shortTerm['taxProjection']['taxDepreciationRecapture'] / shortTerm['genericInput'][
                  'depreciationRecaptureRate']),
              'CRATE': rate_value(shortTerm['capitalizationRate']),
              'BTDR': beforeTaxEquityDividendRate,
              'ATDR': afterTaxEquityDividendRate,
              'OER': rate_value(shortTerm['operatingExpenseRatio']),
              'BER': rate_value(shortTerm['breakEvenRatio']),
              'DCR': rate_value(shortTerm['debtCoverageRatio']),
              'LVR': rate_value(shortTerm['loanValueRatio']),
              'INRA': rate_value(shortTerm['incomeRatio'])

              }

    document.merge_pages([cust_1])

    document.write(f'{out}.docx')


def pdfToOut(file):
    os.rename(f'{file}.pdf', f'{file}Out.pdf')


def figuresOnPDF(file, shortTerm):
    sankey_data = {"rent": round(shortTerm["genericInput"]["estimatedShortTermRent"]),
                   "avoidedCosts": round(0),
                   "principalInterest": round(shortTerm["monthlyDebtService"] * -1),
                   "propertyTax": round(shortTerm["propertyTax"]),
                   "insurance": round(shortTerm["propertyInsurance"]),
                   "hoa": round(shortTerm["hoa"]),
                   "utility": round(shortTerm['utility']),
                   "managementCosts": round(shortTerm["managementFee"]),
                   "repairsCapEx": round(shortTerm["repairMaintenance"]),
                   "cleaningFee": round(shortTerm['genericInput']["monthlyCleaningFees"]),
                   "advertisingCost": round(0),
                   "commission": round(shortTerm['commission']),
                   "vacancy": round(shortTerm["monthlyVacancy"])}
    sankey_chart(sankey_data, file)
    pdf = FPDF(orientation='P', unit='in', format='Letter')
    pdf.set_margins(left=1, top=1, right=1)
    pdf.add_page()

    pdf.image(f'{file}.png', x=1, y=2, w=6.6, h=2.9)
    pdf.output(f'{file}.pdf')
    os.remove(f'{file}.png')


def sankey_chart(data, chartName):
    v0 = data["rent"]  # 0
    # v1 = data["contribution"]   # 1
    v2 = data["avoidedCosts"]  # 2
    # v3 = v0 + v1 + v2 # 3
    v5 = data["principalInterest"]  # 5
    v6 = data["propertyTax"]  # 6
    v7 = data["insurance"]  # 7
    # v4 = v5 + v6 + v7 # 4
    # v8 = data["cashOut"] # 8
    v9 = data["hoa"]  # 9
    v10 = data["utility"]  # 10
    v11 = data["managementCosts"]  # 11
    v12 = data["repairsCapEx"]  # 12
    v13 = data["cleaningFee"]  # 13
    v14 = data["advertisingCost"]  # 14
    v15 = data["commission"]  # 15
    v16 = data["vacancy"]  # 16
    cash_in = v0 + v2
    cash_out = v5 + v6 + v7 + v9 + v10 + v11 + v12 + v13 + v14 + v15 + v16
    if cash_in > cash_out:
        v1 = 0
        v8 = cash_in - cash_out
    else:
        v8 = 0
        v1 = cash_out - cash_in
    v3 = v0 + v1 + v2  # 3
    v4 = v5 + v6 + v7  # 4
    colors = [
        "#cae3c6",
        "#cce8e9",
        "#fdbbc7",
        "#e2ecc9",
        "#d4d4bc",
        "#e5b9ec",
        "#f9fab8",
        "#fee1b7",
        "#babfc5",
        "#FFD54F",
        "#B0BEC5",
        "#039BE5",
        "#66BB6A",
        "#D7CCC8",
        "#FFF9C4",
        "#4DB6AC",
        "#CDDC39"]

    rest = v8 + v9 + v10 + v11 + v12 + v13 + v14 + v15 + v16
    inflow = v3 + v4 + rest

    inflow_nodes_x = [0 for i in [v0, v1, v2] if i != 0]
    inflow_nodes_y = [.5 for i in [v0, v1, v2] if i != 0]

    if len(inflow_nodes_x) > 1:
        node4_y = v4 / (inflow * 2) + 0.12
    else:
        node4_y = v4 / (inflow * 2) + 0.15

    fig = go.Figure(go.Sankey(
        arrangement="freeform",
        node={
            "label": [
                f"Rental income ${round(v0)}", f"Contribution ${round(v1)}", f"Avoided Costs ${round(v2)}", "", "",
                f"Debt Service ${round(v5)}", f"Property Tax ${round(v6)}", f"Property Insurance ${round(v7)}",
                f"Cash out ${round(v8)}", f"HOA ${round(v9)}", f"Utilities ${round(v10)}",
                f"Management Costs ${round(v11)}", f"Maintenance ${round(v12)}", f"Cleaning fees ${round(v13)}",
                f"Advertising Costs ${round(v14)}", f"Airbnb Commissions ${round(v15)}", f"Vacancy ${round(v16)}"
            ],
            "x": inflow_nodes_x + [0, .6],
            "y": inflow_nodes_y + [0.42, node4_y],
            "pad": 20,
            "color": colors
        },
        link={
            "source": [0, 1, 2, 3, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            "target": [3, 3, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
            "value": [v0, v1, v2, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14, v15, v16],
            "color": [colors[3], colors[3], colors[3], colors[4], colors[5], colors[6], colors[7], colors[8], colors[9],
                      colors[10], colors[11], colors[12], colors[13]
                , colors[14], colors[15], colors[16]]
        })
    )

    fig.update_layout(
        height=400,
        width=1100,
        margin=dict(l=0, r=0, b=10, t=0, pad=4),
        plot_bgcolor='#ffffff',
        font_size=18
    )

    filename = f"{chartName}.png"
    fig.write_image(f"{filename}", width=1100)
    return filename


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
    shortTerm = initialize()
    id = pdfFileProperties['id']
    templateLocation = pdfFileProperties['templateLocation']
    outLocation = pdfFileProperties['outLocation']
    property_address = pdfFileProperties['propertyAddress']

    wordPopulate(f'{templateLocation}shortTermProjectionTemplate', f'{outLocation}shortTermProjection{id}',
                 property_address, pdfFileProperties, shortTerm)
    word_to_pdf(f'{outLocation}shortTermProjection{id}')
    figuresOnPDF(f'{outLocation}shortTermProjection{id}.png', shortTerm)
    overlay(f'{outLocation}shortTermProjection{id}', f'{outLocation}shortTermProjection{id}.png',
            f'{outLocation}shortTermProjectionOut{id}')
    maregePdf(f'{outLocation}shortTermProjectionOut{id}', f'{outLocation}out{id}')
