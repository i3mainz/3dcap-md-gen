# 3D Capturing and Processing Metadata Generator (3dcap-md-gen)
Scripts for exporting scanning metadata as described in the publication "Metadata Schema and Ontology for Capturing and Processing of 3D Cultural Heritage Objects"

Contributors: Timo Homburg [![ORCID ID](https://orcid.org/0000-0002-9499-5840)]

## ATOS 2016 Script

### Getting started

* Step **1**
* Step 2

### Exports

### Sample data



## ATOS 6.2 Script

### Getting started

#### Software
* To use the script you need a **license** for the software **ATOS v6.2 (GOM a ZEISS company)**.
* Other versions of the software may work as well, because we only have this version we could use the script only here.
* Open the software ATOS v6.2.
* Import the Python script under the menu item Macro.

#### Parameters
* The variable **includeonlypropswithuri** can be set True or False. With True only the metadata that is assigned an "uri" in the script will be exported, with False all.
* The variable **sensortype** are a list of structured light scanners. If your scanner is not included, you can add it here, otherwise your sensor in the exported TTL will get the general class " capturing device".
* The variables **referencepointid** and **globalreferencepointid** contain the keyword for the point ID. For other ATOS Python libraries this could be different.
* You can additionally adjust the variables of the namespaces

#### ATOS files
* The script writes out the metadata for ****.amp** and ****.session** files.
* There you will find in the zip folder "**atos-v62_project.zip**, by both ****.amp** and ****.session**, which you can use for testing.

### Exports
* The metadata are exported as ****.ttl** and ****.txt** files.
* They are saved at the same path as the opened ATOS file.
* The filename corresponds to the name of the opened ATOS file.

#### (json) txt file
* The ATOS v6.2 software includes the Pyton version 2.3, in which it is not possible to import the external json library. Therefore the dictionary is written into a ****.txt** file, which can be converted into a ****.json** file in another environment.

#### ttl file
* The content of the ****.ttl** file is based on the ontology structure. (link to release on Zenodo ?).
* You can open it e.g. with Protégé.

### Sample data
* Sample data can be found here [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4428498.svg)](https://doi.org/10.5281/zenodo.4428498).
* There is a zip folder **atos-v62_project.zip** that contains both the ****.amp** file and the ****.session** file that you can use for testing.
* In **atos_62_3d-modell.zip** you can download the 3d-model of the scanning project.
* In **atos_62_metadata.zip** are the metadata belonging to the scanning project and the 3d-model, which are the result of this script.



