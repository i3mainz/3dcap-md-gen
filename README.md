# 3D Capturing and Processing Metadata Generator (3dcap-md-gen)
Details on exporting metadata with these scripts are discussed and explained in the publication: Homburg, T., Cramer, A., Raddatz, L., Mara, H.. Metadata schema and ontology for capturing and processing of 3D cultural heritage objects. Herit Sci 9, 91 (2021).  https://doi.org/10.1186/s40494-021-00561-w
  
 
Contributors: [![ORCID ID](https://info.orcid.org/wp-content/uploads/2019/11/orcid_16x16.png)](https://orcid.org/0000-0002-9499-5840) Timo Homburg, [![ORCID ID](https://info.orcid.org/wp-content/uploads/2019/11/orcid_16x16.png)](https://orcid.org/0000-0002-5232-1944) Anja Cramer, [![ORCID ID](https://info.orcid.org/wp-content/uploads/2019/11/orcid_16x16.png)](https://orcid.org/0000-0001-7640-1247) Laura Raddatz

Source Code Documentation: [Doxygen Documentation](http://i3mainz.github.io/3dcap-md-gen)

Scripts are implemented in the following applications
* [ZEISS / GOM](#zeiss--gom)
* [ATOS v6.2](#atos-v62)
* [Agisoft Metashape](#agisoft-metashape)

## ZEISS / GOM

### Getting started

### Script
* atos-2016_3dcap-metadata.py

#### Software
* To use the script you need a **license** for the GOM Software, GOM Inspect Professional or ZEISS INSPECT. We tested the python scripts inside
  * **ATOS Professional 2016** and **GOM Inspect Professional 2016**
  * **GOM Software 2021**
  * **ZEISS INSPECT 2023**
* Other versions of the software might work as well, but the script was only tested with this version 
* Open the software and import the Python script under the menu Scripting or Add-ons.

#### Parameters
* The variable **includeonlypropswithuri** can be set True or False. With True only the metadata that is assigned an "uri" in the script will be exported, with False all.
* The keyword **sensor_type** (uri: sensorType) are a list of structured light scanners. If your scanner is not included, you can add it there, otherwise your sensor in the exported TTL will get the general class " capturing device". The following sensors ar included:
	* ATOS III Rev.01
	* ATOS III Rev.02
	* ATOS Q (8M)
* The variables **referencepointid** and **globalreferencepointid** contain the keyword for the point ID. For other ATOS Python libraries this could be different.

### Namespaces
The data generated by this script may be published at a SPARQL endpoint. To make data URIs of this metadata dereferencable, it is possible to define a data namespace in the script. If no namespace is defined, a default namespace is used.

### Exports
* The metadata are exported as ****.ttl** and ****.json** files.
* They are saved at the same path as the opened ATOS file.
* The filename corresponds to the name of the opened ATOS file.

#### json file
* Contains the metadata of the ATOS project
* You can open it with an editor 

#### ttl file
* The content of the ****.ttl** file is based on the ontology structure. https://github.com/mainzed/mainzedObjectsOntology
* You can open it e.g. with Protégé.

### Sample data
* Sample data can be found here [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.15100515.svg)](https://doi.org/10.5281/zenodo.15100515).
* There is a zip folder **atos-2016_project.zip** that contains the ****.atos** file and **zeiss-2023_project.zip** with  ****.zinspect** file
* In **atos_2016_3d-modell.zip** and **zeiss-2023_3d-modell.zip** you can download the 3d-model of the scanning project.
* In **atos_2016_metadata.zip** and **zeiss-2023_metadata.zip** are the metadata belonging to the scanning project and the 3d-model, which are the result of this script.

## ATOS v6.2

### Script
* atos-v62_3dcap_metadata.py
* atos_v62_txt2json.py

### Getting started

#### Software
* To use the script you need a **license** for the software **ATOS v6.2 (GOM a ZEISS company)**.
* Other versions of the software may work as well, because we only have this version we could use the script only here.
* Open the software ATOS v6.2.
* Import the Python script under the menu item Macro.

#### Parameters
* The variable **includeonlypropswithuri** can be set True or False. With True only the metadata that is assigned an "uri" in the script will be exported, with False all.
* The keyword **sensor_type** (uri: sensorType) are a list of structured light scanners. If your scanner is not included, you can add it there, otherwise your sensor in the exported TTL will get the general class " capturing device". The following sensors ar included:
	* ATOS II (first generation)
	* ATOS III Rev.01  (conjunction with its serial number)
* The variables **referencepointid** and **globalreferencepointid** contain the keyword for the point ID. For other ATOS Python libraries this could be different.

### Namespaces
The data generated by this script may be published at a SPARQL endpoint. To make data URIs of this metadata dereferencable, it is possible to define a data namespace in the script. If no namespace is defined, a default namespace is used.

#### ATOS files
* The script writes out the metadata for ****.session** files.

### Exports
* The metadata are exported as ****.txt** and ****.ttl** files.
* They are saved at the same path as the opened ATOS file.
* The filename corresponds to the name of the opened ATOS file.

#### txt file / json file
* The ATOS v6.2 software includes the Pyton version 2.3, in which it is not possible to import the external json library. Therefore the dictionary is written into a ****.txt** file, which can be converted into a ****.json** file in another environment.
* The Python script **atos_v62_txt2json.py** (availibel here) imports the ****.txt** file and, if available, the separately created _**manualmetadata.json**. The script merges the data and export into a ****.json** file. The script also converts the manualmetadata to ttl-format and append to existing ****.ttl** file.

#### ttl file
* The content of the ****.ttl** file is based on the ontology structure. https://github.com/mainzed/mainzedObjectsOntology
* You can open it e.g. with Protégé.

### Sample data
* Sample data can be found here [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.15100515.svg)](https://doi.org/10.5281/zenodo.15100515).
* There is a zip folder **atos-v62_project.zip** that contains both the ****.amp** file and the ****.session** file that you can use for testing.
* In **atos_62_3d-modell.zip** you can download the 3d-model of the scanning project.
* In **atos_62_metadata.zip** are the metadata belonging to the scanning project and the 3d-model, which are the result of this script.

## Agisoft Metashape

### Script
* agisoft-metashape_3dcap-metadata.py
### Getting started

#### Software
*  To use the script you need a **license** for the **Professional Edition** of **Agisoft Metashape** 
* Agisoft project files also store the metadata of input data, processes and results. They can be accessed with the Python module of Agisoft Metashape. The keys for accessing the metadata have changed during version upgrades. The scripts were applied to the following Agisoft versions:  1.8.4 / 1.7.2 / 1.6.2 / 1.5.5 / 1.5.4 / 1.5.1 / 1.5.0 / and older versions
* After installing the Python 3 module from Agisoft and activating the Agisoft Metashape license in the development environment (e.g. Visual Studio Code), the script can be executed directly
* After starting, an input window will open, where the Agisoft project and the **unit** used in the project must be selected. The reason for selecting the unit are older Agisoft projects where we did not have unit millimeter set directly in the project but used it anyway.

#### Parameters
* The variable **includeonlypropswithuri** can be set True or False. With True only the metadata that is assigned an "uri" in the script will be exported, with False all.

### Namespaces
The data generated by this script may be published at a SPARQL endpoint. To make data URIs of this metadata dereferencable, it is possible to define a data namespace in the script. If no namespace is defined, a default namespace is used.

### Exports
* The metadata are exported as ****.ttl** and ****.json** files.
* They are saved at the same path as the selected Agisoft project file.
* The file name corresponds to the name of the opened Agisoft project file.

#### json file
* Contains the metadata of the Agisoft project
* You can open it with an editor 

#### ttl file
* The content of the ****.ttl** file is based on the ontology structure. https://github.com/mainzed/mainzedObjectsOntology
* You can open it e.g. with Protégé.


### Sample data
* Sample data can be found here [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7463876.svg)](https://doi.org/10.5281/zenodo.7463876).
* There are two sample data, the difference are used references:
	* sample 1: with coded targets and **imported coordinate list**
	* sample 2:  with coded targets and defined **scale bars** in between
* The zip files **sample-1_agisoft-project.zip** and **sample-2_agisoft-project.zip** contain Agisoft project files and the captured images. (Agisoft version 1.8.4)
* In  **sample-1_result_3d-model.zip** and **sample-2_result_3d-model.zip** you can download the 3d-model of the project.
