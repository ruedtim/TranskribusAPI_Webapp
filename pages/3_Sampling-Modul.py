import random
from io import BytesIO
import requests
import shutil
import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import os
import xlwings as xw
import xlsxwriter
import xml.etree.ElementTree as et
from bs4 import BeautifulSoup
from itertools import chain
import utils.utility_functions as uf

def app():
    """
    This function prepares the tab which lets us submit transcription jobs for certain trained models and
    evaluate those models.
    """

    uf.check_session_state(st)
    uf.set_header('Sampling-Modul', st)

    # Set the instruction title
    st.markdown("Bitte die Parameter für das Sampling definieren:")

    textentryColId = st.text_input("Collection id:")

    # Models
    st.text('Modelle:')

    # Model load button
    if st.button('Modelle abrufen'):
        models, modelIdMap, modelProvMap = loadModelNames(textentryColId)
        st.session_state['models'] = models  # Store models in session state
        st.session_state['modelsIdMap'] = modelIdMap
        st.session_state['modelProvMap'] = modelProvMap

    # check if models is in session state
    if 'models' in st.session_state and st.session_state['models']:
        st.session_state['model'] = st.selectbox("Wählen Sie ein Modell", st.session_state['models'])

    # Image export checkbox
    imgExport = st.checkbox("Bilder der Linien mit dem besten und schlechtesten CER-Wert exportieren", value=True)


    # Submit job button
    if st.button('Check Collection'):
        with st.spinner('Collection wird geprüft...'):
            file_download, user_file_name = evaluateSelectedModels(textentryColId, imgExport, 0, "-")
        
    # Attempt to provide a download button for the file, if available.
    try:
        with open(file_download, 'rb') as file:
            st.download_button(
                label='Download Export',
                data=file,
                file_name=user_file_name,
                mime='application/vnd.ms-excel',
                on_click=remove_file(file_download)
            )
            
    except Exception as e:
        # Silently pass if there is any exception (like file not found).
        # This code causes an exception but it still works somehow. It says the used variables are not defined, but they are. May be worth looking into it at a later time
        pass
# Function to remove the temporary file after download.
# Gets called as a callback when the download button is clicked.
def remove_file(file_path):
    def remove_action():
        new_path = os.path.dirname(file_path)
        shutil.rmtree(new_path)
    return remove_action

def loadModelNames(textentryColId):
    """
    This function loads the names of all available models into the select box.
    """

    try:
        colId = str(textentryColId)
        sampleCol = colId

        modelList, modelsIdMap, modelProvMap = get_models_list(colId)

        return modelList, modelsIdMap, modelProvMap

    except Exception as e:
        st.error(f'Fehler: {str(e)}')

def evaluateSelectedModels(colId, imgExport, startPage, endPage):
    """
    This function starts the evaluation process by using the selected model for transcription,
    if no transcription is available. Note: If docId is == "" then the process is applied to all
    documents inside the defined collection.

    Parameters:
    - colId (str): The ID of the collection.
    - docId (str): The ID of the document. If empty, the process is applied to all documents in the collection.
    - imgExport (bool): Flag indicating whether to export images during evaluation.
    - startPage (int): The starting page for evaluation.
    - endPage (int): The ending page for evaluation.
    """
    output_path = "data/samplings/download" + st.session_state.sessionId + '/'
    image_folder = 'data/samplings/tempImgs/' + st.session_state.sessionId + '/'
    
    # Create a folder for personal excel download if it doesn't exist.
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    # generate a random number between 1 and 1000 to avoid overwriting of files
    random_number = str(random.randint(1, 1000))

    workbook_name = f"{output_path}{random_number}.xlsx"
    file_name = f"ModelEvaluation.xlsx"

    # Create and configure an Excel workbook and worksheet.
    wb = xlsxwriter.Workbook(workbook_name)
    sht1 = wb.add_worksheet()
    # Initialize column names based on whether images will be exported.
    if not imgExport:
        columns = ['Dokument Name',  'CER','Model','Best CER','Worst CER']
    else:
        columns = ['Dokument Name',  'CER','Model', 'Best CER', 'Worst CER','Image best CER','Image worst CER']
        sht1.set_default_row(40)
        sht1.set_row(0,20)
        sht1.set_column(2,2,30)
        sht1.set_column(5,6,50)


    # Write the column headers into the Excel sheet.
    for i, col in enumerate(columns):
        sht1.write(0, i, col)

    # Define a text wrap format for cells.
    wrap = wb.add_format({'text_wrap': True})
    
    # Create a folder for temporary images if it doesn't exist.
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)


    docIds = getDocIdsList(st.session_state.sessionId, colId)
    docNames = []
    CERs = []
    worstcers = []
    bestcers = []
    imgsBest = []
    imgsWorst = []
    for c, docId in enumerate(docIds):
        docName, CER, bestcer,worstcer,imgBest, imgWorst,model = evaluateModels(c,len(docIds),colId, docId,imgExport, startPage, endPage)
        docNames.append(docName)
        CERs.append(CER)
        bestcers.append(bestcer)
        worstcers.append(worstcer)
        imgsBest.append(imgBest)
        imgsWorst.append(imgWorst)
        
    row = 1
    for c in range(len(docNames)):
        sht1.write(row, 0, str(docNames[c]))
        sht1.write(row, 1, str(CERs[c]))
        sht1.write(row, 2, str(model))
        sht1.write(row, 3, str(bestcers[c]))
        sht1.write(row, 4, str(worstcers[c]))
        if imgExport:
            imgsBest[c].save(image_folder + '/tempImgBest_{}.jpg'.format(c))
            sht1.insert_image(row, 5, image_folder + '/tempImgBest_{}.jpg'.format(c),{'x_scale': 0.3, 'y_scale': 0.3})
            imgsWorst[c].save(image_folder + '/tempImgWorst_{}.jpg'.format(c))
            sht1.insert_image(row, 6, image_folder + '/tempImgWorst_{}.jpg'.format(c),{'x_scale': 0.3, 'y_scale': 0.3})
        row += 1

    # Close the workbook and remove the temporary image folder.
    wb.close()
    shutil.rmtree(image_folder)
    st.success(f"Alle Samples evaluiert.")
    return workbook_name, file_name



def evaluateModels(nr,total,textentryColId, docId,imgExport, textentryStartPage, textentryEndPage):
    """
        This function evaluates a specific model on a specified document. 
        Defined through st.session_state['models']
    """
 
    currentDocId = docId
    currentColId = textentryColId
    docName = uf.get_doc_name_from_id(currentColId, currentDocId, st)
    
    success = st.success(str(nr) + ' von ' + str(total) + ' Samples ausgewertet. ' + docName + ' gestartet.')
    #get the keys of the transcriptions of the Ground Truth
    keys_GT = get_doc_transcript_keys(textentryColId, currentDocId, textentryStartPage, textentryEndPage, 'GT')
    #get the keys of the transcriptions of the selected model
    keys = get_doc_transcript_keys(textentryColId, currentDocId, textentryStartPage, textentryEndPage, st.session_state['model'])
    transcripts_GT = getDocTranscript(textentryColId, currentDocId, textentryStartPage, textentryEndPage, 'GT')
    transcripts_M = getDocTranscript(textentryColId, currentDocId, textentryStartPage, textentryEndPage, st.session_state['model'])
    charAmount_List = []

    if len(transcripts_GT) == len(transcripts_M):
        for i in range(len(transcripts_GT)):
            amount = (len(transcripts_GT[i]) + len(transcripts_M[i]))/2
            charAmount_List.append(len(transcripts_GT[i]))

    cer_list = []
    cer_list_gew = []
    worst_cer = 0.0
    best_cer = 0.0
    image_worst = ""
    image_best = ""
    #calculate cer for every transcription a model produced
    if not (keys == None or keys_GT == None):
        for k in range(len(keys)):
            wer, cer = getErrorRate(keys[k], keys_GT[k])
            cer_list.append(cer)
        for j in range(len(cer_list)):
            cer_list_gew.append(cer_list[j]*charAmount_List[j]/np.sum(charAmount_List))
        pages = uf.extract_transcription_raw(currentColId, currentDocId, textentryStartPage, textentryEndPage, st.session_state['model'], st)
        #find best and worst cer
        cer_best = [100,0]
        cer_worst = [0,0]
        for h in range(len(cer_list)):
            if cer_list[h] < cer_best[0]:
                cer_best[0] = cer_list[h]
                cer_best[1] = h
            if cer_list[h] > cer_worst[0]:
                cer_worst[0] = cer_list[h]
                cer_worst[1] = h
            
        worst_cer = cer_worst[0]
        best_cer = cer_best[0]

        #save best and worst cer as image and variable if checkbox selected ---------
        if imgExport:
            image_worst_temp = uf.get_image_from_url(uf.get_document_r(currentColId, currentDocId, st)['pageList']['pages'][cer_worst[1]]['url'], st)
            image_best_temp = uf.get_image_from_url(uf.get_document_r(currentColId, currentDocId, st)['pageList']['pages'][cer_best[1]]['url'], st)
            soup_best = BeautifulSoup(pages[cer_best[1]], "xml")
            soup_worst = BeautifulSoup(pages[cer_worst[1]], "xml")
            for region in soup_best.findAll("TextLine"):
            #crop out the image
                cords = region.find('Coords')['points']
                points = [c.split(",") for c in cords.split(" ")]
                maxX = -1000
                minX = 100000
                maxY = -1000
                minY = 100000
                for p in points:
                    maxX = max(int(p[0]), maxX)
                    minX = min(int(p[0]), minX)
                    maxY = max(int(p[1]), maxY)
                    minY = min(int(p[1]), minY)
                image_best = image_best_temp.crop((minX, minY, maxX,maxY))
            for region in soup_worst.findAll("TextLine"):
            #crop out the image
                cords = region.find('Coords')['points']
                points = [c.split(",") for c in cords.split(" ")]
                maxX = -1000
                minX = 100000
                maxY = -1000
                minY = 100000
                for p in points:
                    maxX = max(int(p[0]), maxX)
                    minX = min(int(p[0]), minX)
                    maxY = max(int(p[1]), maxY)
                    minY = min(int(p[1]), minY)
                image_worst = image_worst_temp.crop((minX, minY, maxX,maxY))
        else:
            image_worst = ""
            image_best = ""
            
    success.empty()
    CER = np.sum(cer_list_gew)
    model = st.session_state['model']

    return docName, CER, best_cer, worst_cer, image_best, image_worst, model


def get_doc_transcript_keys(colId, docId, textentryStartPage, textentryEndPage, toolName):
    """
        Get the keys for the transcriptions of a certain document. Those are needed in order to extract the wer and cer.
    """
    #get document
    doc = uf.get_document_r(colId, docId, st)['pageList']['pages']
    
    #setup start page
    if isinstance(textentryStartPage, int):
        startPage = textentryStartPage
    else:
        startPage = int(textentryStartPage.get())
    
    #define the endPages
    if textentryEndPage == "-":
        textentryEndPage = len(doc)

    #setup the endpage
    if isinstance(textentryEndPage, int):
        endPage = textentryEndPage
    else:
        endPage = int(textentryEndPage.get())
    
    
    #define the pages
    pages = range(startPage, endPage)
    
    full_text = []
    
    keys = []
    #go through all pages
    for page in pages:
        for ts in doc[page]['tsList']['transcripts']:
            if toolName == 'GT':
                if ts['status'] == 'GT':
                    keys.append(ts['key'])
                    break
            else:
                try:
                    if toolName in ts['toolName']:
                        keys.append(ts['key'])
                        break
                except:
                    pass
    if len(keys) == len(pages):
        return keys
    elif toolName == "GT":
        st.error("Fehler! Nicht für alle Pages in Sample mit Docid " + str(docId) + " GT vorhanden.")
        return None
    else:
        #self.popupmsg("HTR müssen noch ausgeführt werden. Dies kann einige Zeit dauern...")
        print("Keine Transkriptionen für ausgewähltes Modell vorhanden.")
        return None
        
    return keys


def getDocTranscript(colId, docId, textentryStartPage, textentryEndPage, toolName):
    """
        This function returns the transcription of a certain document.
    """
    pxList = uf.extract_transcription_raw(colId, docId, textentryStartPage, textentryEndPage, toolName, st)
    if pxList == None:
        return
    full_text = []
    full_text_List = []
    raw_text = ''
    for px in pxList:
        soup = BeautifulSoup(px, "xml")
        for line in soup.findAll("TextLine"):
            for t in line.findAll("Unicode"):
                full_text.append(t.text)
        for line in full_text:
            raw_text = line + '\n'
        full_text_List.append(raw_text[:-1])
        full_text = []
        raw_text = ''
    return full_text_List


def getDocIdsList(sid, colid):
    docs = get_documents(sid, colid)
    docIds = []
    for d in docs:
        docIds.append(d['docId'])
    return docIds


def getErrorRate(key, key_ref):
    """
        This gets the wer and cer for a specific model on a specified document
    """
    if st.session_state.proxy is not None and st.session_state.proxy["https"] == 'http://:@:':
        r = requests.get('https://transkribus.eu/TrpServer/rest/recognition/errorRate?JSESSIONID={}&key={}&ref={}'
                    .format(st.session_state.sessionId, key, key_ref))
    else:
        r = requests.get('https://transkribus.eu/TrpServer/rest/recognition/errorRate?JSESSIONID={}&key={}&ref={}'
                    .format(st.session_state.sessionId, key, key_ref), proxies = st.session_state.proxy)
    #extract wer and cer from the content
    wer = float(et.fromstring(r.content)[0].text)
    cer = float(et.fromstring(r.content)[1].text)
    return wer, cer


def get_models_list(colId):
    """
        This function returns a list of all available models in transkribus
    """
    if st.session_state.proxy is not None and st.session_state.proxy["https"] == 'http://:@:':
        r = requests.get('https://transkribus.eu/TrpServer/rest/recognition/{}/list?JSESSIONID={}'.format(colId, st.session_state.sessionId))
    else:
        r = requests.get('https://transkribus.eu/TrpServer/rest/recognition/{}/list?JSESSIONID={}'.format(colId, st.session_state.sessionId), proxies = st.session_state.proxy)

    modelsId = r.text.split('htrId>')[1::2]
    models = r.text.split('name>')[1::2]
    modelsProvider = r.text.split('provider>')[1::2]
    for i in range(len(models)):
        models[i] = models[i].replace('</', '')
        modelsId[i] = modelsId[i].replace('</', '')
        modelsProvider[i] = modelsProvider[i].replace('</', '')
    modelsIdMap = dict(zip(models,modelsId))
    modelsProviderMap = dict(zip(models, modelsProvider))
    models.sort()
    return models, modelsIdMap, modelsProviderMap


def get_documents(sid, colid):
    # Check if a proxy is set in the Streamlit session state and if the proxy's https setting is a specific value
    if st.session_state.proxy is not None and st.session_state.proxy["https"] == 'http://:@:':
        # If the conditions are met, make a GET request without a proxy to the Transkribus API to get documents for a specific collection
        r = requests.get("https://transkribus.eu/TrpServer/rest/collections/{}/list?JSESSIONID={}".format(colid, sid))
    else:
        # If the proxy is different, make the GET request with the proxy settings
        r = requests.get("https://transkribus.eu/TrpServer/rest/collections/{}/list?JSESSIONID={}".format(colid, sid), proxies=st.session_state.proxy)
    
    # Check if the request was successful (status code 200)
    if r.status_code == requests.codes.ok:
        # Return the JSON response from the API if the request was successful
        return r.json()
    else:
        # If the request failed, print the response and display an error message in Streamlit
        print(r)
        st.error('Fehler! Fehler bei der Abfrage der Dokumentliste. Col-ID ' + str(colid) + ' invalid?')
        # Return None to indicate that the request was unsuccessful
        return None
    

if __name__ == "__main__":
    app()