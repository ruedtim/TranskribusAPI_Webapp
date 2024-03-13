# StAZH Transkribus WebApp
The State Archives of the Canton of Zurich uses Transkribus to edit various collections. This WebApp is based on the [TranskribusPyClient](https://github.com/Transkribus/TranskribusPyClient) and allows to execute some functions in Transkribus in batch, respectively to automate certain work steps.

**Note:** The program is still in progress.

## Table of content:
- [Usage with docker](#usage-with-docker)
- [Usage with python](#usage-with-python)
- [Requirements](#requirements)
- [Login](#login)
- [Module Sampling](#module-sampling)
- [Module Export](#module-export)
- [Module Import](#module-import)

## Usage with docker:

There is a Dockerfile provided in the Repository. In order to run the WebAPI with docker just navigate to the base folder and generate a docker image with the following command:

```
docker build -t transkribus_api .
```
Then you can run the container on the streamlit port 8501 by executing:
```
docker run -p 8501:8501 transkribus_api
```
To view your app, you can browse to [http://0.0.0.0:8501](http://0.0.0.0:8501]) or [http://localhost:8501](http://localhost:8501)


## Usage with python:
In order to run the program with python, navigate to the base folder and run the following command:

```
	streamlit run Logout.py
```

## Requirements:

The following libraries need to be installed in order to run the Webapp with python:

```
	streamlit
	streamlit-option-menu
	pandas
	pillow
	streamlit-extras
	xlsxwriter
	xlwings
```

You can install them by running the following command in the command line after navigating to the base folder:

```
	pip install -q -r requirements.txt
```


## Login:

Fill in your Transkribus user credentials. 

## Modules:

### Module Sampling

#### Functionality:

This module provides a way to evaluate a certain model on an entire Collection. It is especially useful to generate the CER value of a model for all samples in a collection. The results will be written to an excel file.

#### Parameters:

- Collection id:
	- Here the id of a collection has to be added.

- Modelle:
	- Here a model can be selected. All models available in Transkribus should be listed.
	  Note that first one has to sync the models by clicking "Modelle abrufen".

#### Output:

ModelEvaluation.xlsx - Once the evaluation process is complete, you can download your document via a button.

### Module Export

#### Functionality:

With this module you can export text, tags and images of a specific textregion to an excel file.

#### Parameters:

- Collection id:
	- Here the id of a collection has to be added.
- Document id:
	- The id of a document.
- zu exportierende Textregion:
	- A text region name that defines the region which we want to export (only one region name).
- Checkbox:
	- Select if each line in a text region should form a separate line in the generated excel file.
- Start Seite:
	- The starting page. (Counting from 1)
- End Seite:
	- The ending page. If "-" is passed the process will go up to the last page.


#### Output:

RegionExtraction_docId_TextregionName_(lines or regions).xlsx - Once the evaluation process is complete, you can download your document via a button.

### Module Import 

#### Functionality:

This module enables previously exported and afterwards edited texts and tags to be imported back into Transkribus.

#### Parameters:

- Collection id:
	- Here the id of a collection has to be added.
- Checkbox:
	- Select if text regions are to be imported. Only the tags of the text regions can be imported (no texts). This is especially useful for (re)naming text regions according to a certain rule.
- CSV mit Importdaten auswählen:
	- Select the CSV-File with the Data to be imported. 
	  	- If the checkbox is selected, the CSV file must have the fields *Document Id, PageNo, Text Region Id, Tag*
	  	- If the checkbox is not selected, the CSV file must have the fields *Document Id, PageNo, Text Region Id, Text, Tag*
#### Output:

None - The results can be seen in Transkribus.
