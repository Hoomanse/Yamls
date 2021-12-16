from __future__ import print_function
from mailmerge import MailMerge
import plotly.graph_objects as go
from fpdf import FPDF
import PyPDF2 as pypdf
import json
import pendulum as pn
import requests
import os
import random

from pdf_generator import word_to_pdf


def initialize():
    with open("../json/rental.json") as json_file:
        rental = json.load(json_file)
        rental = rental["data"]["rental"]

    return rental


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


def school_avg(thirdPartyData):
    avg_rate = 0
    n = 0
    if "nearBySchools" in thirdPartyData:
        for each_school in thirdPartyData["nearBySchools"]["school"]:
            try:
                avg_rate = int(each_school["gsRating"]) + avg_rate
                n = n + 1
            except Exception:
                pass
        if n == 0:
            n = 1
        else:
            pass
        return int(round((avg_rate / n), 0))


def google_map(file, property, api_key):
    # Google Map (450 X 300 pixels)
    lat = property["address"]["latitude"]
    long = property["address"]["longitude"]
    response = requests.get(
        f'https://maps.googleapis.com/maps/api/staticmap?center={lat},{long}&zoom=14&size=450x300&maptype=roadmap%20&markers=blue%7C{lat},{long}&key={api_key}')
    file = open(f'{file}.png', "wb")
    file.write(response.content)
    file.close()


def load_property_image(property_image_path, zm_id):
    request_data = {
        "records": 1,
        "start": 0,
        "input": {
            "zmId": f'{zm_id}'
        },
        "base": {
            "correlationId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "userHostAddress": "string",
            "userAgent": "string",
            "requestChain": [
                {
                    "serviceId": 0,
                    "serviceName": "string",
                    "methodName": "string",
                    "sourceLineNumber": 0,
                    "callingAssembly": "string",
                    "requestUtcDate": "2021-12-09T09:16:54.180Z",
                    "exceptionList": [
                        None
                    ]
                }
            ],
            "rawJsonRequest": "string"
        },
        "raiseError": True
    }
    response = requests.post(
        'http://mlsservice.dev.zillmeterinternal.com/api/v1/Mls/PropertyImages?api-version=1.0',
        json.dumps(request_data),
        headers={"Content-Type": "application/json-patch+json", "accept": "application/json"}
    )
    image_url = json.loads(response.content.decode('utf-8'))['data'][0]['mediaUrl']
    image_format = image_url.rsplit('.')[-1]
    image_name = f'{zm_id}.{image_format}'
    image_location = f'{property_image_path}/{image_name}'
    image = requests.get(image_url).content
    file = open(image_location, "wb")
    file.write(image)
    file.close()
    return image_location


def wordPopulate(template, out, property_address, rental, thirdPartyData, property):
    template = f'{template}.docx'

    # 3rd party APIs
    try:
        if 'soundScore' in thirdPartyData:
            soundScore = f'{thirdPartyData["soundScore"]["result"][0]["score"]}'
    except Exception:
        soundScore = '-'
    if 'walkScore' in thirdPartyData:
        walkScore = f'{thirdPartyData["walkScore"]["walkscore"]}'

    schoolAvg = str(school_avg(thirdPartyData))
    # Home Facts

    standardizedLandUseType = property["parcel"]["standardizedLandUseType"]
    if standardizedLandUseType == None:
        standardizedLandUseType = "-"
    elif standardizedLandUseType == "SINGLE FAMILY":
        standardizedLandUseType = "Single Family"
    else:
        pass

    propertyAddress = property_address

    if "yearBuilt" in property["structure"]:
        yearBuilt = str(property["structure"]["yearBuilt"])

    if "sales" in property:
        lastSoldPrice = fin_value(property["sales"][0]["salePrice"])
        soldOn = pn.parse(property["sales"][0]["saleDate"]).format("MM/DD/YYYY")
    else:
        lastSoldPrice = '-'
        soldOn = '-'
    if "assessments" in property:
        assessedValueYear = f'{(property["assessments"][0]["taxYear"])}'
        assessedValue = fin_value(property["assessments"][0]["assessedTotalValue"])
        propertyTaxYear = str(property["assessments"][0]["taxYear"])
    else:
        assessedValueYear = '-'
        assessedValue = '-'
        propertyTaxYear = '-'

    if "bedsCount" in property['structure']:
        bedroom = property['structure']['bedsCount']
    else:
        bedroom = '-'
    if 'bathsCount' in property['structure']:
        fullbath = property['structure']['bathsCount']
    else:
        fullbath = '-'
    if 'partialBathsCount' in property['structure']:
        halfbath = fullbath = property['structure']['partialBathsCount']
    else:
        halfbath = '-'
    if 'parcel' in property:
        lotsize = property['parcel']['areaSqFt']
        neighborhood = property["parcel"]["municipality"]
    else:
        lotsize = '-'
        neighborhood = '-'

    propertyTax = fin_value(rental["genericInput"]["propertyTaxPercentage"] * rental["genericInput"]["purchasePrice"])

    ##filling up the word template

    document = MailMerge(template)
    document.merge(ADR=propertyAddress,
                   PRC=fin_value(rental['genericInput']['purchasePrice']),
                   ZPRC=fin_value(rental['genericInput']['purchasePrice']),
                   DPR=rate_value(rental['genericInput']['downPaymentRate']),
                   DPD=fin_value((rental['genericInput']['downPaymentRate']) * rental['genericInput']['purchasePrice']),
                   PRSF=f"{fin_value(rental['genericInput']['purchasePrice'] / rental['genericInput']['propertyGrossArea'])}/sf",
                   TR=str(rental['genericInput']['mortgageTerm']),
                   APR=rate_value(rental['genericInput']['mortgageInterest']),
                   PTY=standardizedLandUseType,
                   SF=f"{int(round(rental['genericInput']['propertyGrossArea'], 0))} sf",
                   YR=yearBuilt,
                   HOA=fin_value(rental['genericInput']['monthlyHOA']),
                   LSLD=lastSoldPrice,
                   ASYR=assessedValueYear,
                   ASV=assessedValue,
                   BD=str(bedroom),
                   FBR=str(fullbath),
                   HBR=f'& {halfbath} Half',
                   LOT=f'{lotsize} sf',
                   SLD=str(soldOn),
                   TXY=propertyTaxYear,
                   TAX=propertyTax,
                   NBR=str(neighborhood),
                   HP=str(rental['genericInput']['holdingPeriodAnnual']),
                   AR=rate_value(rental['genericInput']['propertyAppreciation']),
                   TRNS=f'{schoolAvg} / 10',
                   WLK=f'{walkScore} / 10',
                   SND=f'{soundScore} / 100',
                   PG=str(1)
                   )
    document.write(f'{out}.docx')


def bar_chart(file, values):
    # top_labels = ['Down Payment', 'Transaction Cost', 'Remodeling']

    colors = ['rgba(180, 199, 231, 0.8)', 'rgba(255, 163, 163, 0.8)',
              'rgba(165, 165, 165, 0.8)']
    names = ['Down Payment', 'Purchase Expenses', 'Remodeling']

    y_data = ['']
    fig = go.Figure()

    fig.add_trace(
        go.Bar(y=y_data, x=[values[0]], width=0.6, text=f'${values[0]}K', textposition='inside', orientation='h',
               name=names[0], marker=dict(color=colors[0])))
    fig.add_trace(
        go.Bar(y=y_data, x=[values[1]], width=0.6, text=f'${values[1]}K', textposition='inside', orientation='h',
               name=names[1], marker=dict(color=colors[1])))
    fig.add_trace(
        go.Bar(y=y_data, x=[values[2]], width=0.6, text=f'${values[2]}K', textposition='inside', orientation='h',
               name=names[2], marker=dict(color=colors[2])))
    fig.update_layout(
        xaxis=dict(
            showgrid=False,
            showline=False,
            showticklabels=False,
            zeroline=False,
            domain=[0, 1]
        ),
        yaxis=dict(
            showgrid=False,
            showline=False,
            showticklabels=False,
            zeroline=False,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1,
            xanchor="right",
            x=.95,
            font=dict(
                size=22)

        ),
        barmode='stack',
        paper_bgcolor='rgb(260, 260, 260,0)',
        plot_bgcolor='rgb(260, 260, 260,0)',

        showlegend=True,
    )
    fig.update_layout(uniformtext_minsize=22, uniformtext_mode='show', barmode='stack', margin=dict(l=0, r=0, t=0, b=0),
                      legend={'traceorder': 'normal'})
    # fig.show()
    fig.write_image(f'{file}.png', width=1300, height=100)


def figuresOnPDF(file, property_image_location):
    pdf = FPDF(orientation='P', unit='in', format='Letter')
    pdf.set_margins(left=1, top=1, right=1)
    pdf.add_page()

    # property picture
    pdf.image(property_image_location, x=1, y=2, w=4.5 / 2 * 1.3, h=1.5 * 1.3)
    # map picture
    pdf.image(f'{file}.png', x=4.57, y=2, w=4.5 / 2 * 1.3, h=1.5 * 1.3)
    pdf.output(f'{file}.png.pdf')
    os.remove(f'{file}.png')


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


def main(pdfFileProperties, property, thirdPartyData):
    rental = initialize()
    id = pdfFileProperties['id']
    templateLocation = pdfFileProperties['templateLocation']
    outLocation = pdfFileProperties['outLocation']
    property_image_path = pdfFileProperties['propertyImageLocation']
    authentication_key = pdfFileProperties['authenticationKey']
    property_address = pdfFileProperties['propertyAddress']

    google_map(f'{outLocation}firstPage{id}', property, authentication_key)
    property_image_location = load_property_image(property_image_path, property['zmId'])

    wordPopulate(f'{templateLocation}firstPageTemplate', f'{outLocation}firstPage{id}', property_address, rental,
                 thirdPartyData, property)
    word_to_pdf(f'{outLocation}firstPage{id}')
    figuresOnPDF(f'{outLocation}firstPage{id}', property_image_location)
    overlay(f'{outLocation}firstPage{id}', f'{outLocation}firstPage{id}.png', f'{outLocation}out{id}')
