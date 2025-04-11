# converts txt files from atos v6.2 into json files
# imports the manualmetadata.json file (this contains additional information)
# export json-file and ttl-file 

# Anja Cramer / LEIZA
# Timo Homburg / i3mainz
# Laura Raddatz / i3mainz
# 2020/2021/2022/2023/2024/2025


import json
import os
import sys
import random


searchPath = r"D:\LEIZA-Projekte\Metadaten\Release_2025-03\zenodo - Kopie\atos-v62_project"
manualmetadatapathJSON=""
# manualmetadatapathJSON =r"C:\Users\Folder\manualmetadata.json"

## Prefix name for the data namespace .
dataprefix="ex"
# variable python script
# script_uri=str(dataprefix)+":"+script_name
## Prefix name for the class namespace .
ontologyprefix="giga"
toolnamespace="http://objects.mainzed.org/tool/"
toolpropnamespace="http://objects.mainzed.org/tool/atos/62/"
## Namespace for instances defined in the TTL export .
datanamespace="http://objects.mainzed.org/data/"
## Prefix name for the exif namespace .
exifnamespace="http://www.w3.org/2003/12/exif/"
## Prefix name for the exif namespace .
om="http://www.ontology-of-units-of-measure.org/resource/om-2/"
## Prefix name for the rdfs namespace .
rdfs='http://www.w3.org/2000/01/rdf-schema#'
##Prefix name for the  gigamesh namespace
ontologynamespace="http://www.gigamesh.eu/ont#"
# Prefix name for prov-o namespace .
provnamespace = "http://www.w3.org/ns/prov#"
#atos 2016
referencepointid="reference_point_id"
globalreferencepointid="point_id"

ttlstringhead="@prefix "+str(ontologyprefix)+": <"+str(ontologynamespace)+"> .\n@prefix frapo: <http://purl.org/cerif/frapo>.\n@prefix geocrs: <http://www.opengis.net/ont/crs/>.\n@prefix geocrsaxis: <http://www.opengis.net/ont/crs/cs/axis/> .\n@prefix geo: <http://www.opengis.net/ont/geosparql#> .\n@prefix "+str(dataprefix)+": <"+str(datanamespace)+"> .\n@prefix foaf: <http://xmlns.com/foaf/0.1/> .\n@prefix prov: <http://www.w3.org/ns/prov-o/> .\n@prefix rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#> . \n@prefix om:<http://www.ontology-of-units-of-measure.org/resource/om-2/> .\n@prefix rdfs:<http://www.w3.org/2000/01/rdf-schema#> . \n@prefix owl:<http://www.w3.org/2002/07/owl#> . \n@prefix i3atos:<http://www.i3mainz.de/metadata/atos#> . \n@prefix dc:<http://purl.org/dc/terms/> .\n@prefix i3data:<http://www.i3mainz.de/data/grabbauten/> . \n@prefix i3:<http://www.i3mainz.de/ont#> . \n@prefix xsd:<http://www.w3.org/2001/XMLSchema#> . \n"


# methode zum Umwandeln in dictonary

def generate_uuid():
	random_string = ''
	random_str_seq = "0123456789abcdef"
	uuid_format = [8, 4, 4, 4, 12]
	for n in uuid_format:
		for i in range(0,n):
			random_string += str(random_str_seq[random.randint(0, len(random_str_seq) - 1)])
		if i != n:
			random_string += '-'
	return random_string[:-1]

def convertTxt2Json (txtFile):
    print ("in Methode: convertTxt2Json")
    dic_prj = {}
    try:
        with open(txtFile, 'r', encoding="utf-8") as txt_string:
            stringData = txt_string.read().replace('\'', '\"').replace('\\','/')
            print ("read")
        dic_prj=json.loads(stringData)
        txt_string.close()
    except:
        print (sys.exc_info())
    return dic_prj

def readTTL(ttlFile,ttlstring):
    print("readTTL "+str(ttlFile))
    projectid=generate_uuid()
    try:
        with open(ttlFile,'r',encoding="utf-8") as ttls:
            for line in ttls:
                #print(line)
                if "rdf:type" in line and ":MeasurementProject" in line and "owl:Class" not in line:
                    print(line)
                    projectid=line[line.find(":")+1:line.find("rdf:type")-1].strip()
                    print(projectid)
                ttlstring.add(line)
    except Exception as e:
        print(e)
    return [ttlstring,projectid]
    
def entryToTTL(idd,realobj,ttlstring):
    #print(realobj)
    ttlstring.add("<"+idd+"> <"+realobj["value"]+" <"+realobj["value"]+"> .\n")
    ttlstring.add("<"+realobj["value"]+"> rdfs:label \""+realobj["key_eng"]+"\"@en .\n")
    ttlstring.add("<"+realobj["value"]+"> rdfs:label \""+realobj["key_deu"]+"\"@de .\n")
    return ttlstring
                
def addUserMetadataToId(ttlstring,usermetadata,theid):
    data=usermetadata["projects"][0]["general"]
    realobj=data["real_object"][0]
    robjid=theid+"_robj"
    for key in realobj:
        #print(key)
        ttlstring=entryToTTL(robjid,realobj[key],ttlstring)
    if "3d_creator" in data["3d_creation"]:
        realobj=data["3d_creation"]["3d_creator"]
        if "orcid_id" in realobj:
            creatorid=realobj["orcid_id"]["value"]
        else:
            creatorid=str(generate_uuid())
        ttlstring.add("<"+theid+"> dc:creator <"+creatorid+"> .\n")
        ttlstring.add("<"+creatorid+"> rdf:type foaf:Person .\n")
        ttlstring.add("<"+creatorid+"> rdfs:label \""+realobj["person_first_name"]["value"]+" "+realobj["person_surname"]["value"]+"\"@en .\n")
        for key in realobj:
            ttlstring=entryToTTL(creatorid,realobj[key],ttlstring)  
    if "3d_contributors" in data["3d_creation"]:
        realobj=data["3d_creation"]["3d_contributors"]
        for cont in realobj:
            if "orcid_id" in cont:
                creatorid=cont["orcid_id"]["value"]
            else:
                creatorid=str(generate_uuid())
            ttlstring.add("<"+theid+"> dc:contributor <"+creatorid+"> .\n")
            ttlstring.add("<"+creatorid+"> rdf:type foaf:Person .\n")
            ttlstring.add("<"+creatorid+"> rdfs:label \""+cont["person_first_name"]["value"]+" "+cont["person_surname"]["value"]+"\"@en .\n")
            for key in cont:
                ttlstring=entryToTTL(creatorid,cont[key],ttlstring)    
    if "persons_responsible" in data["3d_creation"]:
        realobj=data["3d_creation"]["persons_responsible"]
        for cont in realobj:
            if "orcid_id" in cont:
                creatorid=cont["orcid_id"]["value"]
            else:
                creatorid=str(generate_uuid())
            ttlstring.add("<"+creatorid+"> rdf:type foaf:Person .\n")
            ttlstring.add("<"+creatorid+"> rdfs:label \""+cont["person_first_name"]["value"]+" "+cont["person_surname"]["value"]+"\"@en .\n")
            for key in cont:
                ttlstring=entryToTTL(creatorid,cont[key],ttlstring)       
    realobj=data["research_project"]
    if "research_project_name" in realobj:
        rpid=realobj["research_project_name"]["value"].replace(" ","_")
    else:
        rpid=str(generate_uuid())
    ttlstring.add("<"+rpid+"> rdf:type <http://xmlns.com/foaf/0.1/Project> .\n")
    ttlstring.add("<"+rpid+"> rdfs:label \""+realobj["research_project_name"]["value"]+"\"@en .\n")
    if "description" in realobj:        
        ttlstring.add("<"+rpid+"> skos:definition \""+realobj["description"]["value"]+"\"@en .\n")
    if "funding" in realobj:
        ttlstring.add("<"+rpid+"_"+realobj["funding"]["value"].replace(" ","_")+"> rdf:type <http://purl.org/cerif/frapo/FundingAgency> .\n")
        ttlstring.add("<"+rpid+"_"+realobj["funding"]["value"].replace(" ","_")+"> rdfs:label \""+realobj["funding"]["value"]+"\"@en .\n")
        ttlstring.add("<"+rpid+"> <http://purl.org/cerif/frapo/hasFundingAgency> <"+rpid+"_"+realobj["funding"]["value"].replace(" ","_")+"> .\n")
    if "applicants" in realobj:
        for app in realobj["applicants"]:
            ttlstring.add("<"+rpid+"> <http://purl.org/cerif/frapo/isAppliedForBy> <"+app["institute"]["value"]+"> .\n")
            ttlstring.add("<"+app["institute"]["value"]+"> rdf:type <http://purl.org/cerif/frapo/ResearchInstitute> .\n")
            ttlstring.add("<"+app["institute"]["value"]+"> rdfs:label \""+app["institute"]["value_label"]+"\" .\n")       
    if "duration" in realobj and "project_start" in realobj["duration"]:
                    ttlstring.add("<"+rpid+"> <http://www.w3.org/2006/time#hasBeginning> \""+realobj["duration"]["project_start"]["value"]+"\"^^xsd:date .\n")
    if "duration" in realobj and "project_end" in realobj["duration"]:
                    ttlstring.add("<"+rpid+"> <http://www.w3.org/2006/time#hasEnd> \""+realobj["duration"]["project_end"]["value"]+"\"^^xsd:date .\n")
    if "license" in data:
        realobj=data["license"]
        if "license_3d_model" in realobj:
            ttlstring.add("<"+theid+"> <http://purl.org/dc/terms/license> <"+realobj["license_3d_model"]["value"]+"> .\n")
            ttlstring.add("<"+realobj["license_3d_model"]["value"]+"> rdf:type <"+realobj["license_3d_model"]["uri"]+"> .\n")
            ttlstring.add("<"+realobj["license_3d_model"]["value"]+"> rdfs:label \""+realobj["license_3d_model"]["value_label"]+"\"@en .\n")
        if "license_metadata" in realobj:
            ttlstring.add("<"+theid+"> <http://www.w3.org/ns/dcat#resource> <"+theid+"_metadata> .\n")
            ttlstring.add("<"+theid+"_metadata> <http://www.w3.org/ns/dcat#resource> <http://www.w3.org/ns/dcat#Dataset>.\n")
            ttlstring.add("<"+theid+"_metadata> <http://purl.org/dc/terms/license> <"+realobj["license_metadata"]["uri"]+"> .\n")
            ttlstring.add("<"+theid+"_metadata> rdfs:label \"Metadata License: "+realobj["license_metadata"]["value_label"]+"\"@en .\n")
        if "rights_holder" in realobj:
            ttlstring.add("<"+theid+"> <http://purl.org/dc/terms/rightsHolder> <"+realobj["rights_holder"]["value"]+"> .\n")
            ttlstring.add("<"+realobj["rights_holder"]["value"]+"> rdfs:label \""+realobj["rights_holder"]["value_label"]+"\"@en .\n")
    return ttlstring

# methode zum Hinzufügen der general-json
def addMetaJSON (manualmetadatapathJSON, out_file):
    dic_user = {}
    # check if local _manualmetadata.json exists
    manualmetadatapathJSON_file = out_file+"_manualmetadata.json"
    if os.path.isfile(manualmetadatapathJSON_file):
        with open(manualmetadatapathJSON_file, 'r', encoding="utf-8") as json_file_in:
            dic_user=json.load(json_file_in)
        json_file_in.close()
    # check if global _manualmetadata.json exists
    elif os.path.isfile(manualmetadatapathJSON):
        with open(manualmetadatapathJSON, 'r', encoding="utf-8") as json_file_in:
            dic_user=json.load(json_file_in)
        json_file_in.close()
    return dic_user


for root, dirs, files in os.walk (searchPath):
    for file in files:
        if os.path.splitext(file)[-1]==".txt":
            out_file = (root+"\\"+file).replace(".txt","")
            out_json= out_file + ".json"
            out_ttl= out_file + ".ttl"

            dic_prj = convertTxt2Json (root+"\\"+file)
            dic_user = addMetaJSON (manualmetadatapathJSON, out_file)
            if len(dic_user) > 0:
                dic_prj["projects"][0]["general"] = dic_user["projects"][0]["general"]
            ttlstring=set()
            projectid=str(generate_uuid())
            print(out_ttl)
            if os.path.exists(out_ttl):
                res=readTTL(out_ttl,ttlstring)
                ttlstring=res[0]
                projectid=res[1]
                # save json as ttl
            if len(dic_user) > 0:
                addUserMetadataToId(ttlstring,dic_user,projectid)
            with open(out_json,'w', encoding="utf-8") as json_file:
                json.dump(dic_prj, json_file, indent=4, ensure_ascii=False)
            json_file.close()
            with open(out_ttl,'w', encoding="utf-8") as ttl_file:
                for line in ttlstring:
                    ttl_file.write(line)


print ("fertsch")
