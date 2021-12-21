# -*- coding: utf-8 -*-
#
# GOM-Script-Version: 2016

# Anja Cramer / RGZM
# Timo Homburg / i3mainz
# Laura Raddatz / i3mainz
# 2020/2021

#import gom
import json, math, time
import xml, time, os, random
import datetime

production=True
#production=False

## Indicates if only properties for which a URI has been defined in the JSON dict should be considered for the TTL export .
#includeonlypropswithuri=False
includeonlypropswithuri=True


# python script version
script_name = "atos-2016_3dcap_metadata.py"
script_label = "ATOS 2016 3DCAP Metadata Script"
github_release = "0.1.2"


####################### TTL Export #############################

## Mapping of datatypes present in the JSON dictionary to datatypes present in the TTL file .
datatypes={"float":"xsd:float","double":"xsd:double","str":"xsd:string","date":"xsd:date","int":"xsd:integer","bool":"xsd:boolean","NoneType":"xsd:string", "dateTime":"xsd:dateTime", "list":"xsd:list"}

## Namespace for classes defined in the resulting ontology model .
ontologynamespace="http://objects.mainzed.org/ont#"

## Prefix name for the data namespace .
dataprefix="ex"
# variable python script
script_uri=str(dataprefix)+":"+script_name

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
giganamespace="http://www.gigamesh.eu/ont#"

# Prefix name for prov-o namespace .
provnamespace = "http://www.w3.org/ns/prov#"

#atos 2016
referencepointid="reference_point_id"
globalreferencepointid="point_id"



## Provenance dictionary: Might be used to change the provenance vocabulary .
provenancedict_prov_o={
	"entity":"prov:Entity",
	"activity":"prov:Activity",
	"agent":"prov:Agent",
	"used":"prov:used",
	"person":"foaf:Person"
}

## Provenance dictionary cidoc crm: Might be used to change the provenance vocabulary .
provenancedict_crmdig={
	"entity":"http://www.cidoc-crm.org/cidoc-crm/D1",
	"activity":"http://www.cidoc-crm.org/cidoc-crm/D11",
	"agent":"prov:Agent",
	"used":"prov:used",
	"person":"http://www.cidoc-crm.org/cidoc-crm/D21"
}

sensorTypeToClass={
"ATOS III Rev.01": str(ontologyprefix)+":StructuredLightScanner",
"ATOS Core": str(ontologyprefix)+":StructuredLightScanner",
"ATOS II (first generation)": str(ontologyprefix)+":StructuredLightScanner",
"ATOS III Rev.02": str(ontologyprefix)+":StructuredLightScanner",
}

provenancedict=provenancedict_prov_o

## Key for the german label as present in the JSON dictionary .
germanlabel="key_deu"

## Key for the english label as present in the JSON dictionary .
englishlabel="key_eng"



artifactURI=None

## Header for the TTL export which includes all necessary namespaces.
ttlstringhead="@prefix "+str(ontologyprefix)+": <"+str(ontologynamespace)+"> .\n@prefix geo: <http://www.opengis.net/ont/geosparql#> .\n@prefix "+str(dataprefix)+": <"+str(datanamespace)+"> .\n@prefix foaf: <http://xmlns.com/foaf/0.1/> .\n@prefix prov: <http://www.w3.org/ns/prov-o/> .\n@prefix rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#> . \n@prefix om:<http://www.ontology-of-units-of-measure.org/resource/om-2/> .\n@prefix rdfs:<http://www.w3.org/2000/01/rdf-schema#> . \n@prefix owl:<http://www.w3.org/2002/07/owl#> . \n@prefix i3atos:<http://www.i3mainz.de/metadata/atos#> . \n@prefix dc:<http://purl.org/dc/terms/> .\n@prefix i3data:<http://www.i3mainz.de/data/grabbauten/> . \n@prefix i3:<http://www.i3mainz.de/ont#> . \n@prefix xsd:<http://www.w3.org/2001/XMLSchema#> . \n"

## Generates a UUID.
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

## Turns the first character of a String to lowercase .
#  @param s The string to modify .
#  @return a String with the first character to lowercase
def first_upper(s):
	if len(s) == 0:
		return s
	else:
		return s[0].upper() + s[1:]
				
## Turns the first character of a String to lowercase .
#  @param s The string to modify .
#  @return a String with the first character to lowercase
def first_lower(s):
	if len(s) == 0:
		return s
	else:
		return s[0].lower() + s[1:]

## Reads a TTL file, splits its header and body and merges it to the internal TTL set .
#  @param filepath The filepath of the TTL file to read .
#  @param ttlstring The set of triples to append to .
def readInputTTL(filepath,ttlstring):
	file1 = open(filepath, 'r') 
	Lines = file1.readlines()
	count = 0
	for line in Lines: 
		if line.startswith("@"):
			ttlstringhead+=line+"\n"
		else:
			ttlstring.add(line)
	file1.close()

## Extracts the ID of a previously created object to extend its provenance hierarchy .
#  @param ttlstring The set of triples to append to .
#  @param filterclass The class to use for filtering .
#  @return a set of filtered triples
def filterLastId(ttlstring,filterclass):
	concernedtriples=set()
	for triple in ttlstring:
		for filt in filterclass:
			if filt in triple:
				concernedtriples.add(triple)
	if len(concernedtriples)==0:
		return None
	if len(concernedtriples)==1 and concernedtriples[0].contains("rdf:type"):
		return concernedtriples.split(" ")[0];
		
## Reads an artifact description given in a text file and converts its information to TLL .
#  @param filepath the path of the text file to process
#  @param ttlstring the set of triples to store the result in
def readInputTXTForArtifactDescription(filepath,ttlstring):
	file1 = open(filepath, 'r') 
	firstline = file1.readline()
	if ";" in firstline:
		entities=firstline.split(";")
		if len(entities)>2:
			if entities[0].startswith("http") and entities[2].startswith("http"):
				ttlstring.add("<"+entities[0]+"> rdf:type <"+entities[2]+"> .\n")
				ttlstring.add("<"+entities[0]+"> rdfs:label \""+entities[1]+" Artifact\"@en .\n")
				ttlstring.add("<"+entities[2]+"> rdf:type owl:Class .\n")
				ttlstring.add("<"+entities[2]+"> rdfs:subClassOf prov:Entity .\n")
			elif entities[0].startswith("http") and not entities[2].startswith("http"):
				ttlstring.add("<"+entities[0]+"> rdf:type "+entities[2]+" .\n")
				ttlstring.add("<"+entities[0]+"> rdfs:label \""+entities[1]+" Artifact\"@en .\n")
				ttlstring.add(entities[2]+" rdf:type owl:Class .\n")
				ttlstring.add(entities[2]+" rdfs:subClassOf prov:Entity .\n")
			elif not entities[0].startswith("http") and not entities[2].startswith("http"):
				ttlstring.add("<"+datanamespace+entities[0]+"> rdf:type "+entities[2]+" .\n")
				ttlstring.add("<"+datanamespace+entities[0]+"> rdfs:label \""+entities[1]+" Artifact\"@en .\n")
				ttlstring.add(entities[2]+" rdf:type owl:Class .\n")
				ttlstring.add(entities[2]+" rdfs:subClassOf prov:Entity .\n")
			else:
				ttlstring.add("<"+datanamespace+entities[0]+"> rdf:type <"+entities[2]+"> .\n")
				ttlstring.add("<"+datanamespace+entities[0]+"> rdfs:label \""+entities[1]+" Artifact\"@en .\n")
				ttlstring.add("<"+entities[2]+"> rdf:type owl:Class .\n")
				ttlstring.add("<"+entities[2]+"> rdfs:subClassOf prov:Entity .\n")
		else:
			if entities[0].startswith("http"):
				ttlstring.add("<"+entities[0]+"> rdf:type giga:Artifact .\n")
			else:
				ttlstring.add("<"+datanamespace+entities[0]+"> rdf:type giga:Artifact .\n")
		if entities[0].startswith("http"):
			artifactURI=entities[0]
		else:
			artifactURI=datanamespace+entities[0]			
	file1.close()

## Reads an instance present in a JSON representation and appends its TTL representation to the triple set .
#  @param jsonobj The JSON object to process 
#  @param id The id of the current instance 
#  @param classs The class of the current instance 
#  @param labelprefix A string prefix to be prepended to a rdfs:label expression 
#  @param ttlstring The set of triples to append to 
def exportInformationFromIndAsTTL(jsonobj,id,classs,labelprefix,ttlstring):
	for info in jsonobj:
		#print(classs)
		#print(jsonobj[info])		
		if not info in jsonobj or not "value" in jsonobj[info] or jsonobj[info]["value"]==None or jsonobj[info]["value"]=="":
			continue			
		propuri=str(ontologyprefix)+":"+first_lower(str(info)).replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","").replace("[","_").replace("]","")
		if "uri" in jsonobj[info]:
			#print(jsonobj[info]["uri"])
			if jsonobj[info]["uri"].startswith("http"):
				propuri="<"+str(jsonobj[info]["uri"][0:jsonobj[info]["uri"].rfind("#")]+"#"+first_lower(jsonobj[info]["uri"][jsonobj[info]["uri"].rfind("#")+1:]))+">"
			elif ":" in jsonobj[info]["uri"]:
				propuri=str(jsonobj[info]["uri"][0:jsonobj[info]["uri"].rfind(":")]+":"+first_lower(jsonobj[info]["uri"][jsonobj[info]["uri"].rfind(":")+1:]))
		else:
			propuri=str(ontologyprefix)+":"+first_lower(str(info)).replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","").replace("[","_").replace("]","")
		ttlstring.add(str(propuri)+" rdfs:isDefinedBy <"+str(toolpropnamespace)+str(info).replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","").replace("[","_").replace("]","")+"> .\n")
		#print("Propuri: "+propuri)
		#print(jsonobj[info]["value"])
		#print(isinstance(jsonobj[info]["value"],list))
		if isinstance(jsonobj[info]["value"],list):
			for val in jsonobj[info]["value"]:
				ttlstring=handleProperty(jsonobj,info,id,labelprefix,propuri,classs,ttlstring,val,str(ontologyprefix)+":"+first_upper(str(info)).replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","").replace("[","_").replace("]",""))
		else:
			ttlstring=handleProperty(jsonobj,info,id,labelprefix,propuri,classs,ttlstring,jsonobj[info]["value"],str(ontologyprefix)+":"+first_upper(str(info)).replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","").replace("[","_").replace("]",""))
	#print ("ttlstring")
	return ttlstring

## Processes a given property depending on its type .
def handleProperty(jsonobj,info,id,labelprefix,propuri,classs,ttlstring,inputvalue,propclass):
	if "unit" in jsonobj[info] and jsonobj[info]["unit"]!=None and jsonobj[info]["unit"]!="":
		ttlstring.add(str(propuri)+" rdf:type owl:ObjectProperty .\n")
		ttlstring.add(str(propuri)+" rdfs:domain "+str(classs)+" .\n")
		ttlstring.add(str(propuri)+" rdfs:range om:Measure .\n")
		if englishlabel in jsonobj[info] and jsonobj[info][englishlabel]!=None and str(jsonobj[info][englishlabel])!="" and str(jsonobj[info][englishlabel]).strip()!="...":
			ttlstring.add(str(propuri)+" rdfs:label \""+str(jsonobj[info][englishlabel]).replace("\"","'")+"\"@en .\n")
			if labelprefix=="":
				ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+" rdfs:label \""+str(jsonobj[info][englishlabel]).replace("\"","'")+" \"@en .\n")
				ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+"_value rdfs:label \""+str(jsonobj[info][englishlabel]).replace("\"","'")+" Measurement Value \"@en .\n")
			else:
				ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+" rdfs:label \""+str(jsonobj[info][englishlabel]).replace("\"","'")+" ("+str(labelprefix)+")\"@en .\n")
				ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+"_value rdfs:label \""+str(jsonobj[info][englishlabel]).replace("\"","'")+" Measurement Value ("+str(labelprefix)+")\"@en .\n")
		if germanlabel in jsonobj[info] and jsonobj[info][germanlabel]!=None and str(jsonobj[info][germanlabel])!="" and str(jsonobj[info][germanlabel])!="...":
			ttlstring.add(str(propuri)+" rdfs:label \""+str(jsonobj[info][germanlabel]).replace("\"","'")+"\"@de .\n")
			if labelprefix=="":
				ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+" rdfs:label \""+str(jsonobj[info][germanlabel]).replace("\"","'")+" \"@de .\n")
				ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+"_value rdfs:label \""+str(jsonobj[info][germanlabel]).replace("\"","'")+" Messwert \"@de .\n")			
			else:
				ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+" rdfs:label \""+str(jsonobj[info][germanlabel]).replace("\"","'")+" ("+str(labelprefix)+")\"@de .\n")
				ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+"_value rdfs:label \""+str(jsonobj[info][germanlabel]).replace("\"","'")+" Messwert ("+str(labelprefix)+")\"@de .\n")
		if "measurementclass" in jsonobj[info] and jsonobj[info]["measurementclass"]!=None and str(jsonobj[info]["measurementclass"])!="":
			if ":" in jsonobj[info]["measurementclass"]:
				if jsonobj[info]["measurementclass"].startswith("http"):
					ttlstring.add("<"+jsonobj[info]["measurementclass"].replace(" ","")+"> rdf:type owl:Class .\n") 
					ttlstring.add("<"+jsonobj[info]["measurementclass"].replace(" ","")+"> rdfs:label \""+jsonobj[info]["measurementclass"].replace("\"","'")+"\"@en .\n") 
					ttlstring.add("<"+jsonobj[info]["measurementclass"].replace(" ","")+"> rdfs:subClassOf om:Quantity .\n")				
				else:
					ttlstring.add(str(ontologyprefix)+":"+jsonobj[info]["measurementclass"].replace(" ","")+" rdf:type owl:Class .\n") 
					ttlstring.add(str(ontologyprefix)+":"+jsonobj[info]["measurementclass"].replace(" ","")+" rdfs:label \""+jsonobj[info]["measurementclass"].replace("\"","'")+"\"@en .\n") 
					ttlstring.add(str(ontologyprefix)+":"+jsonobj[info]["measurementclass"].replace(" ","")+" rdfs:subClassOf om:Quantity .\n") 
			else:
				ttlstring.add("<"+jsonobj[info]["measurementclass"].replace(" ","")+"> rdf:type owl:Class .\n")
				ttlstring.add("<"+jsonobj[info]["measurementclass"].replace(" ","")+"> rdfs:label \""+jsonobj[info]["measurementclass"].replace("\"","'")+"\"@en .\n") 					
				ttlstring.add("<"+jsonobj[info]["measurementclass"].replace(" ","")+"> rdfs:subClassOf om:Quantity .\n") 
		else:
			ttlstring.add(propclass+" rdf:type owl:Class .\n") 
			ttlstring.add(propclass+" rdfs:label \""+propclass.replace("_"," ").replace(ontologyprefix+":","")+"\"@en .\n") 
			ttlstring.add(propclass+" rdfs:subClassOf om:Quantity .\n") 
			ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+" rdf:type "+propclass+" .\n") 
		ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+"_value rdf:type om:Measure .\n") 
		ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+" om:hasValue "+str(dataprefix)+":"+str(id)+"_"+str(info).replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+"_value .\n")
		#print(jsonobj[info]["unit"])
		if jsonobj[info]["unit"].startswith("http"):
			ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+"_value om:hasUnit <"+str(jsonobj[info]["unit"])+"> .\n")
			ttlstring.add("<"+str(jsonobj[info]["unit"])+"> rdf:type om:UnitOfMeasure .\n")
			ttlstring.add("<"+str(jsonobj[info]["unit"])+"> rdfs:label \""+jsonobj[info]["unit"].replace("\"","'")+"\"@en .\n")
		elif ":" in jsonobj[info]["unit"]:
			ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+"_value om:hasUnit "+str(jsonobj[info]["unit"].replace(" ",""))+" .\n")
			ttlstring.add(str(jsonobj[info]["unit"].replace(" ",""))+" rdf:type om:UnitOfMeasure .\n")
			ttlstring.add(str(jsonobj[info]["unit"].replace(" ",""))+" rdfs:label \""+jsonobj[info]["unit"].replace("\"","'")+"\" .\n")
		else:
			ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+"_value om:hasUnit \""+str(jsonobj[info]["unit"])+"\" .\n")
		ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+"_value om:hasNumericalValue \""+str(inputvalue).replace("\\","\\\\")+"\"^^"+str(datatypes[jsonobj[info]["value_type"]])+" .\n")		  
		ttlstring.add(str(dataprefix)+":"+str(id)+" "+str(propuri)+" "+str(dataprefix)+":"+str(id)+"_"+str(info).replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+" .\n")
	elif "value_type" in jsonobj[info] and jsonobj[info]["value_type"]=="enumeration":
		ttlstring.add(str(propuri)+" rdf:type owl:ObjectProperty .\n")
		ttlstring.add(str(propuri)+" rdfs:domain "+str(classs)+" .\n")
		if "measurementclass" in jsonobj[info] and jsonobj[info]["measurementclass"]!=None and str(jsonobj[info]["measurementclass"])!="":
			if ":" in jsonobj[info]["measurementclass"]:
				ttlstring.add(str(ontologyprefix)+":"+jsonobj[info]["measurementclass"].replace(" ","")+" rdf:type owl:Class .\n") 
				ttlstring.add(str(ontologyprefix)+":"+jsonobj[info]["measurementclass"].replace(" ","")+" rdfs:label \""+jsonobj[info]["measurementclass"].replace("\"","'")+"\"@en .\n") 
				ttlstring.add(str(ontologyprefix)+":"+jsonobj[info]["measurementclass"].replace(" ","")+" rdfs:subClassOf "+str(ontologyprefix)+":Enumeration .\n") 
				ttlstring.add(str(ontologyprefix)+":"+jsonobj[info]["measurementclass"].replace(" ","")+"_"+inputvalue+" rdf:type "+str(ontologyprefix)+":"+jsonobj[info]["measurementclass"].replace(" ","")+" .\n") 
				ttlstring.add(str(dataprefix)+":"+str(id)+" "+str(propuri)+" "+str(ontologyprefix)+":"+jsonobj[info]["measurementclass"]+"_"+str(inputvalue)+" .\n") 
			else:
				ttlstring.add("<"+jsonobj[info]["measurementclass"].replace(" ","")+"> rdf:type owl:Class .\n")
				ttlstring.add("<"+jsonobj[info]["measurementclass"].replace(" ","")+"> rdfs:label \""+jsonobj[info]["measurementclass"].replace("\"","'")++"\"@en .\n") 					
				ttlstring.add("<"+jsonobj[info]["measurementclass"].replace(" ","")+"> rdfs:subClassOf "+str(ontologyprefix)+":Enumeration .\n")  
				ttlstring.add("<"+jsonobj[info]["measurementclass"].replace(" ","")+"_"+inputvalue+"> rdf:type <"+jsonobj[info]["measurementclass"].replace(" ","")+"> .\n")
				ttlstring.add(str(dataprefix)+":"+str(id)+" "+str(propuri)+" <"+jsonobj[info]["measurementclass"].replace(" ","")+"_"+str(inputvalue).replace(" ","")+"> .\n")   
		else:
			classuri=str(ontologyprefix)+":"+str(propuri).replace(str(ontologyprefix),"").capitalize()
			ttlstring.add(classuri+" rdf:type owl:Class .\n")				
			ttlstring.add(classuri+" rdfs:subClassOf "+str(ontologyprefix)+":Enumeration .\n")  
			ttlstring.add(classuri+"_"+str(inputvalue)+" rdf:type "+classuri+" .\n")
			ttlstring.add(str(dataprefix)+":"+str(id)+" "+str(propuri)+" "+classuri+"_"+str(inputvalue)+" .\n")   
	else:
		if propuri=="http://www.w3.org/2000/01/rdf-schema#label" or  propuri=="rdfs:label" or propuri=="http://www.w3.org/2000/01/rdf-schema#comment" or propuri=="rdfs:comment":
			ttlstring.add(str(propuri)+" rdf:type owl:AnnotationProperty .\n")
			ttlstring.add(str(dataprefix)+":"+str(id)+" "+str(propuri)+" \""+str(inputvalue)+"\" .\n")
		else:
			ttlstring.add(str(propuri)+" rdf:type owl:DatatypeProperty .\n")
			ttlstring.add(str(propuri)+" rdfs:domain "+str(classs)+" .\n")
			if englishlabel in jsonobj[info] and jsonobj[info][englishlabel]!=None and str(jsonobj[info][englishlabel])!="" and str(jsonobj[info][englishlabel])!="...":
				ttlstring.add(str(propuri)+" rdfs:label \""+str(jsonobj[info][englishlabel]).replace("\"","'")+"\"@en .\n")
			if germanlabel in jsonobj[info] and jsonobj[info][germanlabel]!=None and str(jsonobj[info][germanlabel])!="" and str(jsonobj[info][germanlabel])!="...":
				ttlstring.add(str(propuri)+" rdfs:label \""+str(jsonobj[info][germanlabel]).replace("\"","'")+"\"@de .\n")
			ttlstring.add(str(propuri)+" rdfs:range "+str(datatypes[jsonobj[info]["value_type"]])+" .\n")
			ttlstring.add(str(dataprefix)+":"+str(id)+" "+str(propuri)+" \""+str(inputvalue).replace("\\","\\\\")+"\"^^"+str(datatypes[jsonobj[info]["value_type"]])+" .\n")
	#print("handled Property")
	return ttlstring

## Converts a preformatted dictionary to a set of triples .
#  @param dict the dictionary to export from
#  @param measurementToExport indicates whether to export measurements
def exportToTTL(dict,measurementToExport,ttlstring):
	###print ("drin in exportToTTL")
	projectid=str(generate_uuid())
	userid=str(generate_uuid())
	projlabelkey="prj_n"
	projects="projects"
	projkey="measurement_series"
	userkey="user_keywords"
	mesheskey="meshes"
	meshprocessingkey="processing"
	calibkey="calibration"
	sensorskey="sensors"
	sensorinformationkey="calibration"
	meshinfokey="mesh_information"
	globalrefpointkey="global_referencepoints"
	refpointkey="referencepoints"
	globalrefpointinfo="global_referencepoints_information"
	projinfokey="project_information"
	measurmentserieskey = "measurement_series_information"
	measurementskey="measurements"
	measurementinformation="measurement_properties"
	messungkey="messung"
	applicationkey="applications"
	capturingdevice="capturing_device"
	mssetup="measurement_setup"
	calsetup="cal_setup"
	calobject="cal_object"
	calproperties="cal_properties"
	mscheck="measurement_check"
	softwareid="ATOS2016"
	labelprefix=""
	projectname=""
	if ttlstring==None:
		ttlstring=set()
	ttlstring.add(str(ontologyprefix)+":Mesh rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":Mesh rdfs:subClassOf geo:Geometry .\n")
	ttlstring.add(str(ontologyprefix)+":Mesh rdfs:label \"Mesh\"@en .\n")
	ttlstring.add(str(ontologyprefix)+":IntermediateMeshResult rdfs:subClassOf "+str(ontologyprefix)+":Mesh .\n")	
	ttlstring.add(str(ontologyprefix)+":IntermediateMeshResult rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":IntermediateMeshResult rdfs:label \"Intermediate Mesh Result\"@en .\n")
	ttlstring.add("rdfs:label rdf:type owl:AnnotationProperty .\n")
	ttlstring.add(str(ontologyprefix)+":Tool rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":Tool rdfs:label \"Tool\"@en .\n")
	ttlstring.add(str(ontologyprefix)+":Tool rdfs:subClassOf "+provenancedict.get("entity")+" .\n")
	ttlstring.add(str(ontologyprefix)+":CapturingDevice rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":CapturingDevice rdfs:label \"capturing device\"@en .\n")
	ttlstring.add(str(ontologyprefix)+":CapturingDevice rdfs:subClassOf "+str(ontologyprefix)+":Tool .\n")
	ttlstring.add(str(ontologyprefix)+":Scanner rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":Scanner rdfs:label \"scanner\"@en .\n")
	ttlstring.add(str(ontologyprefix)+":Scanner rdfs:subClassOf "+str(ontologyprefix)+":CapturingDevice .\n")
	ttlstring.add(str(ontologyprefix)+":Sensor rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":Sensor rdfs:label \"Sensor\"@en .\n")
	ttlstring.add(str(ontologyprefix)+":Software rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":Software rdfs:label \"software\"@en .\n")
	ttlstring.add(str(ontologyprefix)+":Software rdfs:subClassOf "+provenancedict.get("entity")+" .\n")
	ttlstring.add(str(ontologyprefix)+":Verification rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":Verification rdfs:label \"verification\"@en .\n")
	ttlstring.add(str(ontologyprefix)+":Verification rdfs:subClassOf "+provenancedict.get("entity")+" .\n")
	ttlstring.add(str(ontologyprefix)+":Setup rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":Setup rdfs:label \"setup\"@en .\n")
	ttlstring.add(str(ontologyprefix)+":Setup rdfs:subClassOf "+provenancedict.get("entity")+" .\n")
	ttlstring.add(str(ontologyprefix)+":StructuredLightScanner rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":StructuredLightScanner rdfs:label \"structured light scanner\"@en .\n")
	ttlstring.add(str(ontologyprefix)+":StructuredLightScanner rdfs:subClassOf "+str(ontologyprefix)+":Scanner .\n")
	ttlstring.add(str(ontologyprefix)+":CalibrationObject rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":CalibrationObject rdfs:label \"calibration object\"@en .\n")
	ttlstring.add(str(ontologyprefix)+":CalibrationObject rdfs:subClassOf "+str(ontologyprefix)+":Tool .\n")
	ttlstring.add(str(ontologyprefix)+":MeasurementSetup rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":MeasurementSetup rdfs:label \"measurement setup\"@en .\n")
	ttlstring.add(str(ontologyprefix)+":MeasurementSetup rdfs:subClassOf "+str(ontologyprefix)+":Setup .\n")
	ttlstring.add(str(ontologyprefix)+":CalibrationSetup rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":CalibrationSetup rdfs:label \"calibration setup\"@en .\n")
	ttlstring.add(str(ontologyprefix)+":CalibrationSetup rdfs:subClassOf "+str(ontologyprefix)+":Setup  .\n")
	ttlstring.add(str(ontologyprefix)+":MeasurementCheck rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":MeasurementCheck rdfs:label \"measurement check\"@en .\n")
	ttlstring.add(str(ontologyprefix)+":MeasurementCheck rdfs:subClassOf "+str(ontologyprefix)+":Verification .\n")
	ttlstring.add(str(ontologyprefix)+":Algorithm rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":Algorithm rdfs:label \"Algorithm\"@en .\n")
	ttlstring.add(str(ontologyprefix)+":Algorithm rdfs:subClassOf "+provenancedict.get("agent")+" .\n")
	ttlstring.add(provenancedict.get("entity")+" rdf:type owl:Class .\n")
	ttlstring.add(provenancedict.get("person")+" rdf:type owl:Class .\n")
	ttlstring.add(provenancedict.get("person")+" rdfs:label \"Person\".\n")
	ttlstring.add(provenancedict.get("person")+" rdfs:subClassOf "+provenancedict.get("agent")+" .\n")
	ttlstring.add(provenancedict.get("entity")+" rdfs:subClassOf owl:Thing .\n")
	ttlstring.add("owl:Thing rdf:type owl:Class .\n")
	ttlstring.add("owl:Thing rdfs:label \"Thing\" .\n")
	ttlstring.add(provenancedict.get("entity")+" rdfs:label \"Entity\".\n")
	ttlstring.add(provenancedict.get("agent")+" rdf:type owl:Class .\n")
	ttlstring.add(provenancedict.get("agent")+" rdfs:label \"Agent\".\n")
	ttlstring.add(provenancedict.get("agent")+" rdfs:subClassOf owl:Thing .\n")
	ttlstring.add(provenancedict.get("activity")+" rdf:type owl:Class .\n")
	ttlstring.add(provenancedict.get("activity")+" rdfs:label \"Activity\".\n")
	ttlstring.add(provenancedict.get("activity")+" rdfs:subClassOf owl:Thing .\n")
	ttlstring.add("dc:creator rdf:type owl:ObjectProperty .\n")
	ttlstring.add("dc:creator rdfs:domain "+str(ontologyprefix)+":Mesh .\n")
	ttlstring.add("dc:creator rdfs:range foaf:Person .\n")
	ttlstring.add("prov:wasDerivedFrom rdf:type owl:ObjectProperty .\n")
	ttlstring.add("prov:wasDerivedFrom rdfs:range "+provenancedict.get("entity")+" .\n")
	ttlstring.add("prov:wasDerivedFrom rdfs:domain "+provenancedict.get("entity")+" .\n")
	ttlstring.add("prov:wasInformedBy rdf:type owl:ObjectProperty .\n")
	ttlstring.add("prov:wasInformedBy rdfs:range "+provenancedict.get("activity")+" .\n")
	ttlstring.add("prov:wasInformedBy rdfs:domain "+provenancedict.get("activity")+" .\n")
	ttlstring.add("prov:wasInvalidatedBy rdf:type owl:ObjectProperty .\n")
	ttlstring.add("prov:wasInvalidatedBy rdfs:range "+provenancedict.get("activity")+" .\n")
	ttlstring.add("prov:wasInvalidatedBy rdfs:domain "+provenancedict.get("activity")+" .\n")
	ttlstring.add("prov:wasGeneratedBy rdf:type owl:ObjectProperty .\n")
	ttlstring.add("prov:wasGeneratedBy rdfs:range "+provenancedict.get("activity")+" .\n")
	ttlstring.add("prov:wasGeneratedBy rdfs:domain "+provenancedict.get("entity")+" .\n")
	ttlstring.add("prov:actedOnBehalfOf rdf:type owl:ObjectProperty .\n")
	ttlstring.add("prov:actedOnBehalfOf rdfs:range "+provenancedict.get("agent")+" .\n")
	ttlstring.add("prov:actedOnBehalfOf rdfs:domain "+provenancedict.get("agent")+" .\n")
	ttlstring.add("prov:wasAttributedTo rdf:type owl:ObjectProperty .\n")
	ttlstring.add("prov:wasAttributedTo rdfs:range "+provenancedict.get("agent")+" .\n")
	ttlstring.add("prov:wasAttributedTo rdfs:domain "+provenancedict.get("entity")+" .\n")
	ttlstring.add("prov:used rdf:type owl:ObjectProperty .\n")
	ttlstring.add("prov:used rdfs:range "+provenancedict.get("entity")+" .\n")
	ttlstring.add("prov:used rdfs:domain "+provenancedict.get("activity")+" .\n")
	ttlstring.add("prov:wasAssociatedWith rdf:type owl:ObjectProperty .\n")
	ttlstring.add("prov:wasAssociatedWith rdfs:range "+provenancedict.get("agent")+" .\n")
	ttlstring.add("prov:wasAssociatedWith rdfs:domain "+provenancedict.get("entity")+" .\n")
	ttlstring.add("om:hasNumericalValue rdf:type owl:DatatypeProperty .\n")
	ttlstring.add("om:hasNumericalValue rdfs:range xsd:integer .\n")
	ttlstring.add("om:hasNumericalValue rdfs:domain om:Measure .\n")
	ttlstring.add("om:hasNumericalValue rdfs:label \"has numerical value\"@en .\n")
	ttlstring.add("om:hasValue rdf:type owl:ObjectProperty .\n")
	ttlstring.add("om:hasValue rdfs:label \"has value\"@en .\n")
	ttlstring.add("om:hasUnit rdf:type owl:ObjectProperty .\n")
	ttlstring.add("om:hasUnit rdfs:label \"has unit\"@en .\n")
	ttlstring.add("om:hasUnit rdfs:domain om:Measure .\n")
	ttlstring.add("om:hasUnit rdfs:range om:UnitOfMeasure .\n")
	ttlstring.add("geo:asWKT rdf:type owl:DatatypeProperty .\n")
	ttlstring.add("geo:asWKT rdfs:label \"asWKT\"@en .\n")
	ttlstring.add("om:Quantity rdf:type owl:Class .\n")
	ttlstring.add("om:Quantity rdfs:label \"Quantity\".\n")
	ttlstring.add("om:Quantity rdfs:subClassOf owl:Thing .\n")
	ttlstring.add("om:Measure rdf:type owl:Class .\n")
	ttlstring.add("om:Measure rdfs:label \"Measure\".\n")
	ttlstring.add("om:Measure rdfs:subClassOf owl:Thing .\n")
	ttlstring.add("om:UnitOfMeasure rdf:type owl:Class .\n")
	ttlstring.add("om:UnitOfMeasure rdfs:label \"Unit Of Measure\".\n")
	ttlstring.add("om:UnitOfMeasure rdfs:subClassOf owl:Thing .\n")
	ttlstring.add(str(ontologyprefix)+":calibration rdf:type owl:ObjectProperty .\n")
	ttlstring.add(str(ontologyprefix)+":calibration rdfs:range "+str(ontologyprefix)+":Calibration .\n")
	ttlstring.add(str(ontologyprefix)+":calibration rdfs:domain "+str(ontologyprefix)+":Measurement .\n")
	ttlstring.add(str(ontologyprefix)+":sensor rdf:type owl:ObjectProperty .\n")
	ttlstring.add(str(ontologyprefix)+":sensor rdfs:range "+str(ontologyprefix)+":Sensor .\n")
	ttlstring.add(str(ontologyprefix)+":sensor rdfs:domain "+str(ontologyprefix)+":Measurement .\n")
	ttlstring.add(str(ontologyprefix)+":calibrationsetup rdf:type owl:ObjectProperty .\n")
	ttlstring.add(str(ontologyprefix)+":calibrationsetup rdfs:range "+str(ontologyprefix)+":Setup .\n")
	ttlstring.add(str(ontologyprefix)+":calibrationsetup rdfs:domain "+str(ontologyprefix)+":Calibration .\n")
	ttlstring.add(str(ontologyprefix)+":calibrationobject rdf:type owl:ObjectProperty .\n")
	ttlstring.add(str(ontologyprefix)+":calibrationobject rdfs:range "+str(ontologyprefix)+":CalibrationObject .\n")
	ttlstring.add(str(ontologyprefix)+":calibrationobject rdfs:domain "+str(ontologyprefix)+":Calibration .\n")
	ttlstring.add(str(ontologyprefix)+":capturingdevice rdf:type owl:ObjectProperty .\n")
	ttlstring.add(str(ontologyprefix)+":capturingdevice rdfs:range "+str(ontologyprefix)+":Tool .\n")
	ttlstring.add(str(ontologyprefix)+":capturingdevice rdfs:domain "+str(ontologyprefix)+":Measurement .\n")
	ttlstring.add(str(ontologyprefix)+":globalReferencePoint rdf:type owl:ObjectProperty .\n")
	ttlstring.add(str(ontologyprefix)+":globalReferencePoint rdfs:range "+str(ontologyprefix)+":GRP .\n")
	ttlstring.add(str(ontologyprefix)+":globalReferencePoint rdfs:domain "+str(ontologyprefix)+":MeasurementSeries .\n")	
	ttlstring.add(str(ontologyprefix)+":referencePoint rdf:type owl:ObjectProperty .\n")
	ttlstring.add(str(ontologyprefix)+":referencePoint rdfs:range "+str(ontologyprefix)+":ReferencePoint .\n")
	ttlstring.add(str(ontologyprefix)+":referencePoint rdfs:domain "+str(ontologyprefix)+":Measurement .\n")	
	ttlstring.add(str(ontologyprefix)+":partOf rdf:type owl:ObjectProperty .\n")
	ttlstring.add(str(ontologyprefix)+":partOf rdfs:range "+str(ontologyprefix)+":MeasurementCheck.\n")
	ttlstring.add(str(ontologyprefix)+":partOf rdfs:range "+str(ontologyprefix)+":MeasurementSetup.\n")
	ttlstring.add(str(ontologyprefix)+":partOf rdfs:domain "+str(ontologyprefix)+":Measurement .\n")
	ttlstring.add(str(ontologyprefix)+":usedBy rdf:type owl:ObjectProperty .\n")
	ttlstring.add(str(ontologyprefix)+":usedBy rdfs:range "+str(ontologyprefix)+":Measurement .\n")
	ttlstring.add(str(ontologyprefix)+":usedBy rdfs:domain "+str(ontologyprefix)+":CapturingDevice .\n")
	ttlstring.add(str(ontologyprefix)+":setup rdf:type owl:ObjectProperty .\n")
	ttlstring.add(str(ontologyprefix)+":setup rdfs:range "+str(ontologyprefix)+":MeasurementSetup .\n")
	ttlstring.add(str(ontologyprefix)+":setup rdfs:domain "+str(ontologyprefix)+":Measurement .\n")
	ttlstring.add(str(ontologyprefix)+":verification rdf:type owl:ObjectProperty .\n")
	ttlstring.add(str(ontologyprefix)+":verification rdfs:range "+str(ontologyprefix)+":MeasurementCheck .\n")
	ttlstring.add(str(ontologyprefix)+":verification rdfs:domain "+str(ontologyprefix)+":Measurement .\n")
	ttlstring.add(str(ontologyprefix)+":measurementSeries rdf:type owl:ObjectProperty .\n")
	ttlstring.add(str(ontologyprefix)+":measurementSeries rdfs:range "+str(ontologyprefix)+":MeasurementSeries .\n")
	ttlstring.add(str(ontologyprefix)+":measurementSeries rdfs:domain "+str(ontologyprefix)+":MeasurementProject .\n")
	ttlstring.add(str(ontologyprefix)+":measurement rdf:type owl:ObjectProperty .\n")
	ttlstring.add(str(ontologyprefix)+":measurement rdfs:range "+str(ontologyprefix)+":Measurement .\n")
	ttlstring.add(str(ontologyprefix)+":measurement rdfs:domain "+str(ontologyprefix)+":MeasurementSeries .\n")
	ttlstring.add(str(ontologyprefix)+":Calibration rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":CalibrationObject rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":Measurement rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":Measurement rdfs:label \"Measurement\".\n")
	ttlstring.add(str(ontologyprefix)+":Measurement rdfs:subClassOf prov:Entity .\n")
	ttlstring.add(str(ontologyprefix)+":MeasurementSeries rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":MeasurementSeries rdfs:label \"Measurement Series\".\n")
	ttlstring.add(str(ontologyprefix)+":MeasurementSeries rdfs:subClassOf prov:Entity .\n")
	ttlstring.add(str(ontologyprefix)+":MeasurementProjectMetadata rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":MeasurementProjectMetadata rdfs:label \"Measurement Project Metadata\".\n")
	ttlstring.add(str(ontologyprefix)+":MeasurementProjectMetadata rdfs:subClassOf prov:Entity .\n")
	ttlstring.add(str(ontologyprefix)+":MeasurementProject rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":MeasurementProject rdfs:label \"Measurement Project\".\n")
	ttlstring.add(str(ontologyprefix)+":MeasurementProject rdfs:subClassOf prov:Entity .\n")
	ttlstring.add(str(ontologyprefix)+":ReferencePoint rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":ReferencePoint rdfs:label \"reference point\".\n")
	ttlstring.add(str(ontologyprefix)+":ReferencePoint rdfs:subClassOf geo:Point . geo:Point rdfs:subClassOf geo:Geometry . geo:Geometry rdfs:subClassOf prov:Entity .\n")
	ttlstring.add(str(ontologyprefix)+":GRP rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":GRP rdfs:label \"global reference point\".\n")
	ttlstring.add(str(ontologyprefix)+":GRP rdfs:subClassOf "+str(ontologyprefix)+":ReferencePoint .\n")
	ttlstring.add(str(ontologyprefix)+":Calibration rdfs:subClassOf prov:Entity .\n")
	ttlstring.add(str(ontologyprefix)+":Calibration rdfs:label \"Calibration\".\n")
	ttlstring.add(str(dataprefix)+":metadata_calculation_activity rdf:type "+provenancedict.get("activity")+" . \n")	
	ttlstring.add(str(ontologyprefix)+":GRP_calculation_algorithm rdf:type "+str(ontologyprefix)+":Algorithm . \n")	
	for pro in dict[projects]:
		#print(projkey)		
		#print (pro[projinfokey])
		if projinfokey in pro:
			if "prj_n" in pro[projinfokey]:
				labelprefix=pro[projinfokey]["prj_n"]["value"]
				projectname=pro[projinfokey]["prj_n"]["value"]
			ttlstring.add(str(dataprefix)+":"+str(projectid)+" rdf:type "+str(ontologyprefix)+":MeasurementProject .\n")
			ttlstring.add(str(dataprefix)+":"+str(projectid)+"_metadata rdf:type "+str(ontologyprefix)+":MeasurementProjectMetadata .\n")
			ttlstring.add(str(dataprefix)+":"+str(projectid)+"_metadata prov:wasGeneratedBy "+str(dataprefix)+":metadata_calculation_activity .\n")
			ttlstring.add(str(dataprefix)+":"+str(projectid)+"_metadata prov:wasAttributedTo "+str(dataprefix)+":"+script_name+".\n")
			ttlstring.add(str(dataprefix)+":"+str(projectid)+" "+str(dataprefix)+":metadata "+str(dataprefix)+":"+str(projectid)+"_metadata .\n")
			#print(pro[projinfokey])
			ttlstring=exportInformationFromIndAsTTL(pro[projinfokey],projectid,str(ontologyprefix)+":MeasurementProject",labelprefix,ttlstring)
		ttlstring.add(str(dataprefix)+":"+str(userid)+" rdf:type foaf:Person, "+provenancedict.get("agent")+" .\n")
		ttlstring.add(str(dataprefix)+":"+str(projectid)+" dc:creator "+str(dataprefix)+":"+str(userid)+" .\n")
		ttlstring.add(str(dataprefix)+":"+str(userid)+" rdfs:label \"Creator of "+str(labelprefix)+"\" .\n")
		#print(pro[applicationkey])
		if applicationkey in pro:
			for appl in pro[applicationkey]:
				if "script_name" in appl and "value" in appl["script_name"] and appl["script_name"]["value"]==script_name:
					ttlstring.add(str(dataprefix)+":"+script_name+" rdf:type "+str(ontologyprefix)+":Software  .\n")
					ttlstring.add(str(dataprefix)+":"+script_name+" rdfs:label \""+str(script_label)+"\"@en  .\n")
					ttlstring=exportInformationFromIndAsTTL(appl,script_name,str(ontologyprefix)+":Software",labelprefix,ttlstring)
				else:
					if "PROJECT.TYPE" in appl and "PROJECT.VERSION" in appl:
						softwareid=str(appl["PROJECT.TYPE"]["value"]).strip().replace(" ","_")+"_"+str(appl["PROJECT.VERSION"]["value"]).strip().replace(" ","_").replace(".","_").replace("-","_")
					elif "application_name" in appl and "application_build_information.version" in appl:
						softwareid=str(appl["application_name"]["value"]).strip().replace(" ","_")+"_"+str(appl["application_build_information.version"]["value"]).strip().replace(" ","_").replace(".","_").replace("-","_")
					else:
						softwareid="ATOS2016"
					ttlstring.add(str(dataprefix)+":"+softwareid+" rdf:type "+str(ontologyprefix)+":Software  .\n")
					ttlstring.add(str(dataprefix)+":"+softwareid+" rdfs:label \""+str(softwareid).replace("_"," ")+"\"@en  .\n")
					ttlstring=exportInformationFromIndAsTTL(appl,softwareid,str(ontologyprefix)+":Software",labelprefix,ttlstring)
		if projkey in pro:
			for msindex, project in enumerate(pro[projkey]):
				#print(project)
				ttlstring.add(str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+" rdf:type "+str(ontologyprefix)+":MeasurementSeries .\n")
				ttlstring.add(str(dataprefix)+":"+str(projectid)+" prov:wasDerivedFrom "+str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+" .\n")
				ttlstring.add(str(dataprefix)+":"+str(projectid)+" "+str(ontologyprefix)+":measurementSeries "+str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+" .\n")
				ttlstring.add(str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+" rdfs:label \"Measurement Series "+str(msindex)+" for "+str(labelprefix)+"\"@en .\n")
				ttlstring.add(str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+" prov:wasAttributedTo "+str(dataprefix)+":"+str(userid)+" .\n")
				ttlstring.add(str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+" prov:wasGeneratedBy "+str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+"_activity .\n")
				ttlstring.add(str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+"_activity prov:wasAssociatedWith "+str(dataprefix)+":"+str(userid)+" .\n")
				if artifactURI!=None:
					ttlstring.add(str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+"_activity prov:used "+artifactURI+" .\n")						
				ttlstring.add(str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+"_activity rdf:type prov:Activity .\n")
				ttlstring.add(str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+"_activity rdfs:label \"MS "+str(msindex)+" Activity ("+str(labelprefix)+")\"@en .\n")
				ttlstring.add(str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+"_activity rdfs:label \" Messreihe "+str(msindex)+" ("+str(labelprefix)+")\"@de .\n")
				if measurmentserieskey in project:
					#print(project[measurmentserieskey])
					ttlstring=exportInformationFromIndAsTTL(project[measurmentserieskey],str(projectid)+"_ms_"+str(msindex),str(ontologyprefix)+":MeasurementSeries",labelprefix,ttlstring)
					if measurementToExport==None:
						#print ("measurementToExport==None:")			
						if projkey in project:						
							#print (project[projinfokey])
							if projinfokey in project:
								if "prj_n" in project[projinfokey]:
									labelprefix=project[projinfokey]["prj_n"]["value"]+"Measurement Series "+str(msindex)
								ttlstring.add(str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+" rdf:type "+str(ontologyprefix)+":MeasurementSeries, prov:Entity .\n")
								#print(project[projinfokey])
								ttlstring=exportInformationFromIndAsTTL(project[measurmentserieskey],projectid+"_ms_"+str(msindex),str(ontologyprefix)+":MeasurementSeries",labelprefix,ttlstring)
								ttlstring.add(str(dataprefix)+":"+str(userid)+" rdf:type foaf:Person, "+provenancedict.get("agent")+" .\n")
								ttlstring.add(str(dataprefix)+":"+str(projectid)+" dc:creator "+str(dataprefix)+":"+str(userid)+" .\n")
								ttlstring.add(str(dataprefix)+":"+str(userid)+" rdfs:label \"Creator of "+str(labelprefix)+"\" .\n")
								#print(ttlstring)
					if userkey in project:
						ttlstring=exportInformationFromIndAsTTL(project[userkey],userid,"foaf:Person",labelprefix,ttlstring)
					#print(ttlstring)
					#print(project[globalrefpointkey])
					if globalrefpointkey in project and refpointkey in project[globalrefpointkey]:
						for index, grp in enumerate(project[globalrefpointkey][refpointkey]):
							if "point_id" in grp:
								index = grp["point_id"]["value"]
								#print (index)
							elif "r_id" in grp:
								index = grp["r_id"]["value"]
								#print (index)						
							grpid=str(projectid)+"_ms_"+str(msindex)+"_grp"+str(index)
							#print (grpid)
							ttlstring.add(str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+" "+str(ontologyprefix)+":globalReferencePoint "+str(dataprefix)+":"+str(grpid)+" . \n")
							ttlstring.add(str(dataprefix)+":"+str(grpid)+" rdf:type "+str(ontologyprefix)+":GRP .\n")
							ttlstring.add(str(dataprefix)+":"+str(grpid)+" rdfs:label \"GRP"+str(index)+" ( Measurement Series "+str(msindex)+")\"@en .\n")
							ttlstring.add(str(dataprefix)+":"+str(grpid)+" rdfs:label \"GRP"+str(index)+" ( Messreihe "+str(msindex)+")\"@de .\n")
							ttlstring.add(str(dataprefix)+":"+str(grpid)+" prov:wasGeneratedBy "+str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+"_grp_calculation_activity .\n")
							ttlstring.add(str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+"_grp_calculation_activity prov:wasAssociatedWith "+str(ontologyprefix)+":GRP_calculation_algorithm. \n")
							ttlstring.add(str(ontologyprefix)+":GRP_calculation_algorithm prov:actedOnBehalfOf "+str(dataprefix)+":"+str(userid)+" . \n")
							ttlstring.add(str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+"_grp_calculation_activity rdf:type "+provenancedict.get("activity")+" .\n")
							ttlstring.add(str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+"_grp_calculation_activity rdfs:label \"GRP Calculation Activity\"@en .\n")
							ttlstring.add(str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+"_grp_calculation_activity rdfs:label \"GRP Berechnung\"@de .\n")
							#print("265:"+str(project[globalrefpointkey]))
							#print("266: "+str(grp))
							ttlstring=exportInformationFromIndAsTTL(grp,grpid,str(ontologyprefix)+":GRP",labelprefix+" MS "+str(msindex)+" GRP"+str(index),ttlstring)
							if "r_x" in grp and "r_y" in grp and "r_z" in grp:
								ttlstring.add(str(dataprefix)+":"+str(grpid)+" geo:asWKT \"POINT("+str(grp["r_x"]["value"])+" "+str(grp["r_y"]["value"])+" "+str(grp["r_z"]["value"])+")\"^^geo:wktLiteral .\n")					
							elif "coordinate.x" in grp and "coordinate.y" in grp and "coordinate.z" in grp:
								ttlstring.add(str(dataprefix)+":"+str(grpid)+" geo:asWKT \"POINT("+str(grp["coordinate.x"]["value"])+" "+str(grp["coordinate.y"]["value"])+" "+str(grp["coordinate.z"]["value"])+")\"^^geo:wktLiteral .\n")
				if sensorskey in project:
					for seindex, sensor in enumerate(project[sensorskey]):
						sensorid=str(projectid)+"_sensor_"+str(seindex)
						calibid=str(sensorid)+"_calibration"
						mscheckid=str(sensorid)+"_mscheck"
						capturedevid=str(sensorid)+"_capturingdevice"
						ttlstring.add(str(dataprefix)+":"+str(sensorid)+" rdf:type "+str(ontologyprefix)+":Sensor, "+provenancedict.get("entity")+" .\n")
						ttlstring.add(str(dataprefix)+":"+str(sensorid)+" rdfs:label \"Sensor "+str(seindex)+" from "+str(projectname)+"\"@en .\n")
						ttlstring.add(str(dataprefix)+":"+str(sensorid)+" prov:wasDerivedFrom "+str(dataprefix)+":"+str(projectid)+" .\n")
						if capturingdevice in sensor:
							if "sensor_type" in sensor[capturingdevice] and sensor[capturingdevice]["sensor_type"]["value"] in sensorTypeToClass:
								ttlstring.add(str(dataprefix)+":"+str(capturedevid)+" rdf:type "+str(sensorTypeToClass[sensor[capturingdevice]["sensor_type"]["value"]])+" .\n")
							else:
								ttlstring.add(str(dataprefix)+":"+str(capturedevid)+" rdf:type "+str(ontologyprefix)+":CapturingDevice .\n")
							ttlstring.add(str(dataprefix)+":"+str(sensorid)+" "+str(ontologyprefix)+":capturingdevice "+str(dataprefix)+":"+str(capturedevid)+" .\n")
							ttlstring.add(str(dataprefix)+":"+str(mscheckid)+" "+str(ontologyprefix)+":partOf "+str(dataprefix)+":"+str(sensorid)+"_activity .\n")
							ttlstring.add(str(dataprefix)+":"+str(capturedevid)+" rdfs:label \""+labelprefix+"Sensor "+str(seindex)+" Capturing Device\"@en .\n")
							ttlstring=exportInformationFromIndAsTTL(sensor[capturingdevice],capturedevid,str(ontologyprefix)+":CapturingDevice",labelprefix+" Sensor "+str(seindex)+" Caturing Device",ttlstring)				
						if calibkey in sensor:
							ttlstring.add(str(dataprefix)+":"+str(sensorid)+" "+str(ontologyprefix)+":calibration "+str(dataprefix)+":"+str(calibid)+" .\n")
							ttlstring.add(str(dataprefix)+":"+str(calibid)+" rdfs:label \"Sensor "+str(seindex)+" Calibration\"@en .\n")
							ttlstring.add(str(dataprefix)+":"+str(calibid)+" rdf:type "+str(ontologyprefix)+":Calibration .\n")
							ttlstring.add(str(dataprefix)+":"+str(calibid)+"_activity rdf:type prov:Activity .\n")
							if labelprefix=="":
								ttlstring.add(str(dataprefix)+":"+str(calibid)+"_activity rdfs:label \"MS "+str(seindex)+" Measurement "+str(msindex)+" Calibration Activity \"@en .\n")
								ttlstring.add(str(dataprefix)+":"+str(calibid)+"_activity rdfs:label \"Sensor "+str(seindex)+" Messvorgang "+str(msindex)+" Kalibrierung \"@de .\n")
							else:
								ttlstring.add(str(dataprefix)+":"+str(calibid)+"_activity rdfs:label \"MS "+str(seindex)+" Measurement "+str(msindex)+" Calibration Activity ("+str(labelprefix)+")\"@en .\n")
								ttlstring.add(str(dataprefix)+":"+str(calibid)+"_activity rdfs:label \"Sensor "+str(seindex)+" Messvorgang "+str(msindex)+" Kalibrierung ("+str(labelprefix)+")\"@de .\n")							
							ttlstring.add(str(dataprefix)+":"+str(calibid)+"_activity prov:wasAssociatedWith "+str(dataprefix)+":"+str(userid)+" .\n")
							ttlstring.add(str(dataprefix)+":"+str(calibid)+" rdf:type "+str(ontologyprefix)+":Calibration .\n")
							if calobject in sensor[calibkey]:
								calobjid=""
								calobjname=""
								if "calibration_object_name" in sensor[calibkey][calobject]:
									#print(messung[calibkey][calobject])
									calobjid=str(sensor[calibkey][calobject]["calibration_object_name"]["value"]).replace(" ","")+"_calibration_object"
									calobjname=str(sensor[calibkey][calobject]["calibration_object_name"]["value"])
								else:
									calobjid=str(sensorid)+"_calibration_object"
								ttlstring.add(str(dataprefix)+":"+str(calibid)+" "+str(ontologyprefix)+":calibrationobject "+str(dataprefix)+":"+str(calobjid)+" .\n")
								ttlstring.add(str(dataprefix)+":"+str(calobjid)+" rdfs:label \""+labelprefix+" Sensor "+str(seindex)+" Calibration Object"+"\" .\n")
								ttlstring.add(str(dataprefix)+":"+str(calibid)+"_activity prov:used "+str(dataprefix)+":"+str(calobjid)+" .\n")
								ttlstring.add(str(dataprefix)+":"+str(calobjid)+" rdf:type "+str(ontologyprefix)+":CalibrationObject .\n")
								ttlstring=exportInformationFromIndAsTTL(sensor[calibkey][calobject],calobjid,str(ontologyprefix)+":CalibrationObject",calobjname+" Calibration Object",ttlstring)
							if calsetup in sensor[calibkey]:
								calsetupid=str(sensorid)+"_calibration_setup"
								ttlstring.add(str(dataprefix)+":"+str(calsetupid)+" rdf:type "+str(ontologyprefix)+":CalibrationSetup .\n")
								ttlstring.add(str(dataprefix)+":"+str(calsetupid)+" rdfs:label \""+labelprefix+" Sensor "+str(seindex)+" Calibration Setup"+"\" .\n")
								ttlstring.add(str(dataprefix)+":"+str(calibid)+" "+str(ontologyprefix)+":calibrationsetup "+str(dataprefix)+":"+str(calsetupid)+" .\n")
								ttlstring.add(str(dataprefix)+":"+str(calsetupid)+" "+str(ontologyprefix)+":partOf "+str(dataprefix)+":"+str(calibid)+"_activity .\n")
								ttlstring=exportInformationFromIndAsTTL(sensor[calibkey][calsetup],calsetupid,str(ontologyprefix)+":CalibrationSetup",labelprefix+" Sensor "+str(seindex)+" Calibration Setup",ttlstring)							
							if calproperties in sensor[calibkey]:
								ttlstring=exportInformationFromIndAsTTL(sensor[calibkey][calproperties],calibid,str(ontologyprefix)+":Calibration",labelprefix+" Sensor "+str(seindex)+" Calibration",ttlstring)
							ttlstring=exportInformationFromIndAsTTL(sensor[calibkey],calibid,str(ontologyprefix)+":Calibration",labelprefix+" Sensor "+str(seindex)+" Calibration",ttlstring)
						#print(ttlstring)
				if measurementskey in project:
					for index, messung in enumerate(project[measurementskey]):
					#print(index)
						if measurementToExport==None or measurementToExport==index:
							messungid=str(projectid)+"_ms_"+str(msindex)+"_measurement"+str(index)
							calibid=str(messungid)+"_calibration"
							capturedevid=str(messungid)+"_capturingdevice"
							mssetupid=str(messungid)+"_mssetup"
							mscheckid=str(messungid)+"_mscheck"
							ttlstring.add(str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+" "+str(ontologyprefix)+":measurement "+str(dataprefix)+":"+str(messungid)+" .\n")
							ttlstring.add(str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+" prov:wasDerivedFrom "+str(dataprefix)+":"+str(messungid)+" .\n")
							ttlstring.add(str(dataprefix)+":"+str(messungid)+" rdf:type "+str(ontologyprefix)+":Measurement .\n")
							ttlstring.add(str(dataprefix)+":"+str(messungid)+" rdfs:label \"MS "+str(msindex)+" Measurement "+str(index)+" for "+str(labelprefix)+"\"@en .\n")
							ttlstring.add(str(dataprefix)+":"+str(messungid)+" prov:wasAttributedTo "+str(dataprefix)+":"+str(userid)+" .\n")
							ttlstring.add(str(dataprefix)+":"+str(messungid)+" prov:wasGeneratedBy "+str(dataprefix)+":"+str(messungid)+"_activity .\n")
							ttlstring.add(str(dataprefix)+":"+str(messungid)+"_activity prov:wasAssociatedWith "+str(dataprefix)+":"+str(userid)+" .\n")
							if artifactURI!=None:
								ttlstring.add(str(dataprefix)+":"+str(messungid)+"_activity prov:used "+artifactURI+" .\n")						
							ttlstring.add(str(dataprefix)+":"+str(messungid)+"_activity rdf:type prov:Activity .\n")
							ttlstring.add(str(dataprefix)+":"+str(messungid)+"_activity prov:used "+str(dataprefix)+":"+softwareid+" .\n")
							ttlstring.add(str(dataprefix)+":"+str(messungid)+"_activity rdfs:label \"MS "+str(msindex)+" Measurement "+str(index)+" Activity ("+str(labelprefix)+")\"@en .\n")
							ttlstring.add(str(dataprefix)+":"+str(messungid)+"_activity rdfs:label \"Messreihe "+str(msindex)+" Messvorgang "+str(index)+" ("+str(labelprefix)+")\"@de .\n")
							if measurementinformation in messung and "sensor_id" in messung[measurementinformation] and "value" in messung[measurementinformation]["sensor_id"]:	
								ttlstring.add(str(dataprefix)+":"+str(messungid)+" "+str(ontologyprefix)+":sensor "+str(dataprefix)+":"+str(projectid)+"_sensor_"+str(messung[measurementinformation]["sensor_id"]["value"])+" .\n")	
							if mssetup in messung:
								ttlstring.add(str(dataprefix)+":"+str(mssetupid)+" rdf:type "+str(ontologyprefix)+":MeasurementSetup .\n")
								ttlstring.add(str(dataprefix)+":"+str(messungid)+" "+str(ontologyprefix)+":setup "+str(dataprefix)+":"+str(mssetupid)+" .\n")
								ttlstring.add(str(dataprefix)+":"+str(mssetupid)+" "+str(ontologyprefix)+":partOf "+str(dataprefix)+":"+str(messungid)+"_activity .\n")
								ttlstring.add(str(dataprefix)+":"+str(mssetupid)+" rdfs:label \""+labelprefix+" MS "+str(msindex)+" Measurement "+str(index)+" Setup\"@en .\n")
								ttlstring=exportInformationFromIndAsTTL(messung[mssetup],mssetupid,str(ontologyprefix)+":MeasurementSetup",labelprefix+" MS "+str(msindex)+" Measurement "+str(index)+" Setup",ttlstring)
							if mscheck in messung:
								ttlstring.add(str(dataprefix)+":"+str(mscheckid)+" rdf:type "+str(ontologyprefix)+":MeasurementCheck .\n")
								ttlstring.add(str(dataprefix)+":"+str(messungid)+" "+str(ontologyprefix)+":verification "+str(dataprefix)+":"+str(mscheckid)+" .\n")
								ttlstring.add(str(dataprefix)+":"+str(mscheckid)+" prov:used "+str(dataprefix)+":"+str(messungid)+"_activity .\n")
								ttlstring.add(str(dataprefix)+":"+str(mscheckid)+" rdfs:label \""+labelprefix+" MS "+str(msindex)+" Measurement "+str(index)+" Measurement Check\"@en .\n")
								ttlstring=exportInformationFromIndAsTTL(messung[mscheck],mscheckid,str(ontologyprefix)+":MeasurementCheck",labelprefix+" MS "+str(msindex)+" Measurement "+str(index)+" Measurement Check",ttlstring)
							ttlstring=exportInformationFromIndAsTTL(messung[measurementinformation],messungid,str(ontologyprefix)+":Measurement",labelprefix+" MS "+str(msindex)+" Measurement "+str(index),ttlstring)
							#print(messung)
							index2=0
							index2oid = 0
							messungindex=index
							if refpointkey in messung:
								for index,rp in enumerate(messung[refpointkey]):
									if "r_id" in rp:
										index2 = rp["r_id"]["value"]
									elif "reference_point_id" in rp:
										index2 = rp["reference_point_id"]["value"]
									else:
										index2 = "_noid_" + str(index2oid)
										index2oid+=1	
									#print("aaa:"+str(rp))
									rpuri=str(messungid)+"_rp"+str(index2)
									ttlstring.add(str(dataprefix)+":"+str(messungid)+" "+str(ontologyprefix)+":referencePoint "+str(dataprefix)+":"+str(rpuri)+" . \n")
									ttlstring.add(str(dataprefix)+":"+str(rpuri)+" rdf:type "+str(ontologyprefix)+":ReferencePoint .\n")				
									ttlstring.add(str(dataprefix)+":"+str(rpuri)+" rdfs:label \"RP"+str(index2)+" ("+str(labelprefix)+" MS "+str(msindex)+" Measurement "+str(messungindex)+")\"@en .\n")
									ttlstring.add(str(dataprefix)+":"+str(rpuri)+" rdfs:label \"RP"+str(index2)+" ("+str(labelprefix)+" Messreihe "+str(msindex)+" Messung "+str(messungindex)+")\"@de .\n")
									ttlstring=exportInformationFromIndAsTTL(rp,rpuri,str(ontologyprefix)+":ReferencePoint",labelprefix+" MS "+str(msindex)+" Measurement "+str(index)+" RP"+str(index2),ttlstring)
									if "r_x" in rp and "r_y" in rp and "r_z" in rp:
									### atos v6.2
										ttlstring.add(str(dataprefix)+":"+str(rpuri)+" geo:asWKT \"POINT("+str(rp["r_x"]["value"])+" "+str(rp["r_y"]["value"])+" "+str(rp["r_z"]["value"])+")\"^^geo:wktLiteral .\n")			
									###atos 2016
									elif "reference_point_coordinate.x" in rp and "reference_point_coordinate.y" in rp and "reference_point_coordinate.z" in rp:
										ttlstring.add(str(dataprefix)+":"+str(rpuri)+" geo:asWKT \"POINT("+str(rp["reference_point_coordinate.x"]["value"])+" "+str(rp["reference_point_coordinate.y"]["value"])+" "+str(rp["reference_point_coordinate.z"]["value"])+")\"^^geo:wktLiteral .\n")
									#print(rp)
									ttlstring.add(str(dataprefix)+":"+str(rpuri)+" prov:wasGeneratedBy "+str(dataprefix)+":"+str(messungid)+"_activity . \n")
									ttlstring.add(str(dataprefix)+":"+str(messungid)+"_activity rdfs:label \"MS "+str(msindex)+" Measurement "+str(index)+" Activity\"@en. \n")
									ttlstring.add(str(dataprefix)+":"+str(rpuri)+" prov:wasAttributedTo "+str(dataprefix)+":"+str(messungid)+"_algorithm . \n")
									ttlstring.add(str(dataprefix)+":"+str(messungid)+"_algorithm rdfs:label \"MS "+str(msindex)+" Measurement "+str(index)+" Algorithm\"@en. \n")
									ttlstring.add(str(dataprefix)+":"+str(messungid)+"_algorithm rdf:type "+str(ontologyprefix)+":Algorithm . \n")
									ttlstring.add(str(dataprefix)+":"+str(messungid)+"_algorithm prov:actedOnBehalfOf "+str(dataprefix)+":"+str(userid)+" . \n")
									#print(rpuri)
									if measurementToExport==None and index2!=None:
										#print("grp loop")
										if globalrefpointkey in project:
											if refpointkey in project[globalrefpointkey]:
												for index, point in enumerate(project[globalrefpointkey][refpointkey]):
													if referencepointid in rp and globalreferencepointid in point and rp[referencepointid]["value"]==point[globalreferencepointid]["value"]:
														if "point_id" in point:
															index = point["point_id"]["value"]
															#print (index)
														elif "r_id" in point:
															index = point["r_id"]["value"]
															#print (index)	
														#print(str(rp[referencepointid]["value"])+" - "+str(point[globalreferencepointid]["value"]))
														#print(str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+"_grp"+str(index)+" prov:wasDerivedFrom "+str(dataprefix)+":"+str(rpuri)+" . \n")
														ttlstring.add(str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+"_grp"+str(index)+" prov:wasDerivedFrom "+str(dataprefix)+":"+str(rpuri)+" . \n")
														ttlstring.add(str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+"_grp_calculation_activity rdf:type prov:Activity . \n")
														ttlstring.add(str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+"_grp_calculation_activity prov:used "+str(dataprefix)+":"+str(rpuri)+" . \n")
									#print("next")
		if mesheskey in pro:					
			for index, mesh in enumerate(pro[mesheskey]):
				meshid=str(projectid)+"_mesh_"+str(index)
				ttlstring.add(str(dataprefix)+":"+str(meshid)+" rdf:type "+str(ontologyprefix)+":Mesh, "+provenancedict.get("entity")+" .\n")
				ttlstring.add(str(dataprefix)+":"+str(meshid)+" rdfs:label \"Mesh "+str(meshid)+" from "+str(projectname)+"\"@en .\n")
				ttlstring.add(str(dataprefix)+":"+str(meshid)+" prov:wasDerivedFrom "+str(dataprefix)+":"+str(projectid)+" .\n")
				lastprocid=""
				if meshprocessingkey in mesh:
					#print(mesh[meshprocessingkey])
					for indexprocstep, procstep in enumerate(mesh[meshprocessingkey]):
						ttlstring.add(str(dataprefix)+":"+str(meshid)+"_creation_"+str(0)+"_activity rdf:type prov:Activity .\n")
						ttlstring.add(str(dataprefix)+":"+str(meshid)+"_creation_"+str(0)+"_activity rdfs:label \"Mesh Creation Activity "+str(0)+": "+str(procstep["processname"]["value"])+"\"@en .\n")
						ttlstring.add(str(dataprefix)+":"+str(meshid)+"_creation_"+str(0)+"_activity rdfs:label \"Mesherstellungsschritt "+str(0)+": ("+str(procstep["processname"]["value"])+")\"@de .\n")
						ttlstring.add(str(dataprefix)+":"+str(meshid)+"_creation_"+str(0)+"_activity prov:used "+str(dataprefix)+":"+str(projectid)+" .\n")
						if "setup" in procstep:
							ttlstring=exportInformationFromIndAsTTL(procstep["setup"],str(meshid)+"_creation_"+str(0)+"_activity","prov:Activity","Mesh Creation Activity "+procstep["processname"]["value"],ttlstring)
						if "postprocessing" in procstep:
							for indexpostproc, postproc in enumerate(procstep["postprocessing"]):
								ttlstring.add(str(dataprefix)+":"+str(meshid)+"_creation_"+str(indexpostproc+1)+"_activity rdf:type prov:Activity .\n")
								if "processname" in postproc and "value" in postproc["processname"]:
									ttlstring.add(str(dataprefix)+":"+str(meshid)+"_creation_"+str(indexpostproc+1)+"_activity rdfs:label \"Mesh Creation Activity "+str(indexpostproc+1)+": "+str(postproc["processname"]["value"])+"\"@en .\n")
									ttlstring.add(str(dataprefix)+":"+str(meshid)+"_creation_"+str(indexpostproc+1)+"_activity rdfs:label \"Mesherstellungsschritt "+str(indexpostproc+1)+": "+str(postproc["processname"]["value"])+"\"@de .\n")
								else:
									ttlstring.add(str(dataprefix)+":"+str(meshid)+"_creation_"+str(indexpostproc+1)+"_activity rdfs:label \"Mesh Creation Activity "+str(indexpostproc+1)+"\"@en .\n")
									ttlstring.add(str(dataprefix)+":"+str(meshid)+"_creation_"+str(indexpostproc+1)+"_activity rdfs:label \"Mesherstellungsschritt "+str(indexpostproc+1)+"\"@de .\n")
								if indexpostproc==0:
									ttlstring.add(str(dataprefix)+":"+str(meshid)+"_creation_"+str(indexpostproc+1)+"_activity prov:wasInformedBy "+str(dataprefix)+":"+str(meshid)+"_creation_"+str(indexpostproc)+"_activity .\n")
									if indexpostproc!=0:
										ttlstring.add(str(dataprefix)+":"+str(meshid)+"_intermediate_"+str(indexpostproc+1)+" prov:wasDerivedFrom "+str(dataprefix)+":"+str(meshid)+"_intermediate_"+str(indexpostproc)+" .\n")
									ttlstring.add(str(dataprefix)+":"+str(meshid)+"_intermediate_"+str(indexpostproc+1)+" prov:wasGeneratedBy "+str(dataprefix)+":"+str(meshid)+"_creation_"+str(indexpostproc+1)+"_activity .\n")
								else:
									ttlstring.add(str(dataprefix)+":"+str(meshid)+"_creation_"+str(indexpostproc+1)+"_activity prov:wasInformedBy "+str(dataprefix)+":"+str(meshid)+"_creation_"+str(indexpostproc)+"_activity .\n")
									if indexpostproc!=0:
										ttlstring.add(str(dataprefix)+":"+str(meshid)+"_intermediate_"+str(indexpostproc+1)+" prov:wasDerivedFrom "+str(dataprefix)+":"+str(meshid)+"_intermediate_"+str(indexpostproc)+" .\n")
										ttlstring.add(str(dataprefix)+":"+str(meshid)+"_intermediate_"+str(indexpostproc)+" prov:wasInvalidatedBy "+str(dataprefix)+":"+str(meshid)+"_creation_"+str(indexpostproc+1)+"_activity .\n")
									ttlstring.add(str(dataprefix)+":"+str(meshid)+"_intermediate_"+str(indexpostproc+1)+" prov:wasGeneratedBy "+str(dataprefix)+":"+str(meshid)+"_creation_"+str(indexpostproc+1)+"_activity .\n")
									ttlstring.add(str(dataprefix)+":"+str(meshid)+"_creation_"+str(indexpostproc+1)+"_activity prov:used "+str(dataprefix)+":"+str(meshid)+"_intermediate_"+str(indexpostproc)+" .\n")
								ttlstring.add(str(dataprefix)+":"+str(meshid)+"_intermediate_"+str(indexpostproc+1)+" rdfs:label \"Mesh "+str(meshid)+" Intermediate Result "+str(indexpostproc)+"\"@en .\n")
								ttlstring.add(str(dataprefix)+":"+str(meshid)+"_intermediate_"+str(indexpostproc+1)+" rdfs:label \"Mesh "+str(meshid)+" Zwischenergebnis "+str(indexpostproc)+"\"@en .\n")
								ttlstring.add(str(dataprefix)+":"+str(meshid)+"_intermediate_"+str(indexpostproc+1)+" rdf:type "+str(ontologyprefix)+":IntermediateMeshResult .\n")
								lastprocid=str(dataprefix)+":"+str(meshid)+"_intermediate_"+str(indexpostproc+1)
								if "processname" in postproc and "value" in postproc["processname"]:
									ttlstring=exportInformationFromIndAsTTL(postproc,str(meshid)+"_creation_"+str(indexpostproc+1)+"_activity","prov:Activity","Mesh Creation Activity "+str(indexpostproc)+": "+str(postproc["processname"]["value"])+" ",ttlstring)	
								else:
									ttlstring=exportInformationFromIndAsTTL(postproc,str(meshid)+"_creation_"+str(indexpostproc+1)+"_activity","prov:Activity","Mesh Creation Activity "+str(indexpostproc)+" ",ttlstring)							
						else:
							ttlstring.add(str(dataprefix)+":"+str(meshid)+" prov:wasGeneratedBy "+str(dataprefix)+":"+str(meshid)+"_creation_"+str(0)+"_activity .\n")
				if lastprocid!="":
					ttlstring.add(str(dataprefix)+":"+str(meshid)+" owl:sameAs "+str(lastprocid)+" .\n")
				ttlstring=exportInformationFromIndAsTTL(mesh[meshinfokey],meshid,str(ontologyprefix)+":Mesh",labelprefix+" Mesh Attribute ",ttlstring)							
	return ttlstring


#####################################################################################################



## Method for collecting metadata of the measurement series, measurements and networks
## An externally created dictionary with user information can be given

def createMetaDic(dic_user): # befor exportjson(), now createMetaDic()
		

	dic_dig = {}
	dic_dig_app={}
	list_app=[]
	
	list_project_info=[]
	project = {}
	project_info ={}
	sensor_id = 0 
	
	list_app.append(dic_dig_app)
	
	# add script version infos
	list_app.append(script_version())
	
	# import userkey / general information 
	if "projects" in dic_user:
		for e in dic_user["projects"]:
			if 'general' in e:
				project['general'] = e['general']

	def infos_app (keyword,beschreibung,unit,description,uri,measurementclass, value, from_application):		
		dir = {}
		dir.clear()
		dir["value"] = gom.app.get(keyword)
		dir["key_deu"] = beschreibung
		if description!=None:
			dir["key_eng"] = description		
		if uri!=None:
			dir["uri"] = uri	
		if measurementclass!=None:
			dir["measurementclass"] = measurementclass			
		dir["value_type"] = type(gom.app.get(keyword)).__name__
		if unit!=None:
			dir["unit"] = unit
		if from_application!=None:
			dir["from_application"] = from_application
			
		if keyword == 'PROJECT.DATE':
			value_new = dir["value"]
			
		if keyword == "application_build_information.date": 
			dir["value_type"]="date"
			
		if dir["value"] != None:
			if len(str(dir["value"])) != 0:
				dic_dig_app[keyword] = {}		
				dic_dig_app[keyword] = dir
				
	# Applikationsname
	keyword= 'application_name'
	beschreibung = "Applikationsname"
	unit= None
	description="application name" 
	uri= None
	measurementclass=None
	value= gom.app.get ('application_name')
	from_application= "true"
	infos_app(keyword,beschreibung,unit,description,uri,measurementclass, value, from_application) 
	
	# Applilationsbuild-Informationen / Version
	keyword= 'application_build_information.version'
	beschreibung = "Applikationsbuild-Informationen / Version"
	unit= None
	description='application build information / version'
	uri= None
	measurementclass=None
	value=  gom.app.get(keyword)
	from_application= "true"
	infos_app(keyword,beschreibung,unit,description,uri,measurementclass, value, from_application) 
	
	# Applilationsbuild-Informationen / Revision
	keyword= 'application_build_information.revision'
	beschreibung = "Applikationsbuild-Informationen / Revision"
	unit= None
	description='application build information / Revision'
	uri= None
	measurementclass=None
	value=  gom.app.get(keyword)
	from_application= "true"
	infos_app(keyword,beschreibung,unit,description,uri,measurementclass, value, from_application)  

	# Applilationsbuild-Informationen / Datum
	keyword= 'application_build_information.date'
	beschreibung = "Applikationsbuild-Informationen / Datum"
	unit= None
	description='application build information / date'
	uri= None
	measurementclass=None
	value=  gom.app.get(keyword)
	from_application= "true"
	infos_app(keyword,beschreibung,unit,description,uri,measurementclass, value, from_application) 
	

	
	#project 
	def infos_p (keyword, beschreibung,unit=None,description=None, uri=None, measurementclass=None, value=None, from_application="true"):
		dir = {}
		if value== None:
			dir["value"] = gom.app.project.get(keyword)
		else:
			dir["value"]= value 			
		dir["key_deu"] = beschreibung
		if  description != None:
			dir["key_eng"] =  description
		if  uri != None:
			dir["uri"] =  uri
		if  unit != None:
			dir["unit"] =  unit
		if measurementclass!=None:
			dir["measurementclass"] = measurementclass
		dir["from_application"]=from_application
		
		try:
			dir["value_type"] = type(gom.app.project.get(keyword)).__name__
		except:
			dir["value_type"] = type(dir["value"]).__name__
				
		if dir["value"] != None:
			if len(str(dir["value"])) != 0:
				if includeonlypropswithuri and "uri" in dir:
					project_info[keyword] = {}		
					project_info[keyword] = dir
				
				if not includeonlypropswithuri:			
					project_info[keyword] ={}		
					project_info[keyword] = dir
		
			
	### Projektinformationen 
	
	anz_messungen = 0
		
	##Benutzerdefinierte Keywords
	# Abteilung
	keyword= 'user_department'
	beschreibung = "Abteilung"
	unit= None
	description="department" 
	uri= None
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Bauteil
	keyword= 'user_part'
	beschreibung = "Bauteil"
	unit= None 
	description="Part" 
	uri= None
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Chargen-Nr.
	keyword= 'user_charge_nr'
	beschreibung = "Chargen-Nr."
	unit= None
	description="Charge No." 
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass)  
	
	# Datenstand
	keyword= 'user_version'
	beschreibung = "Datenstand"
	unit= None 
	description="Data Status" 
	uri= None
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
		
	# Fehlermeldung 
	
	## Datum
	#keyword= 'user_date'
	#beschreibung = "Datum"
	#unit= None 
	#infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Firma
	keyword= 'user_company'
	beschreibung = "Firma"
	unit= None 
	description="Company" 
	uri= None
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Ort 
	keyword= 'user_location'
	beschreibung = "Ort"
	unit= None 
	description="Location" 
	uri= None
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Projekt 
	keyword= 'user_project'
	beschreibung = "Projekt"
	unit= None 
	description="Project" 
	uri= None
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Prüfer
	keyword= 'user_inspector'
	beschreibung = "Prüfer"
	unit= None
	description="Inspector" 
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# System 
	keyword= 'user_system'
	beschreibung = "System"
	unit= None
	description="System" 
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Teile-Nr. 
	keyword= 'user_part_nr'
	beschreibung = "Teile-Nr."
	unit= None 
	description="Part No." 
	uri= None
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	## Information
	
	# Erzeugungszeit des Projektes 
	keyword= 'project_creation_time'
	beschreibung = "Erzeugungszeit des Projektes"
	unit= None
	description="Creationtime of the Project " 
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Name 
	keyword= 'name'
	beschreibung = "Name"
	unit= None
	description="Name" 
	uri= None
	measurementclass=None  
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass)
	
	# Projektdatei 
	keyword= 'project_file'
	beschreibung = "Projektdatei"
	unit= None
	description="Project file" 
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass)
	
	# Projektdateigröße
	keyword= 'project_file_size'
	beschreibung = "Projektdateigröße"
	unit= 'Bytes'
	description="Project file size" 
	uri= None
	measurementclass=None  
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass)
	
	# Projektdatenreduzierung 
	keyword= 'project_data_reduction'
	beschreibung = "Project data reduction"
	unit= None
	description="Projectfile" 
	uri= None
	measurementclass=None  
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass)
	
	# Projektname
	keyword= 'project_name'
	beschreibung = "Projektname"
	unit= None
	description="Project name" 
	uri= rdfs+"label"
	measurementclass=None  
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass)
	
	# Änderungszeit des Projektes 
	keyword= 'project_modification_time'
	beschreibung = "Änderungszeit des Projektes"
	unit= None
	description="Project modification time" 
	uri= None
	measurementclass=None  
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass)
	
	## Projektinformation 
	
	# Aktuelle Reportseite
	keyword = 'current_report_page'
	beschreibung = "Aktuelle Reportseite"
	unit= None
	description="Current report page" 
	uri= None
	measurementclass=None  
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Aktueller Stufenbereich
	keyword = 'current_stage_range'
	beschreibung = "Aktueller Stufenbereich"
	unit= None
	description="Current stage range" 
	uri= None
	measurementclass=None  
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Anzahl der Belichtungszeiten 
	keyword = 'number_of_exposure_times'
	beschreibung = "Anzahl der Belichtungszeiten"
	unit= None
	description="Number of exposure times" 
	uri= None
	measurementclass=None  
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Art der Referenzpunktqualität für Photogrammetrie
	keyword = 'ellipse_quality_type_for_photogrammetry'
	beschreibung = "Art der Referenzpunktqualität für Photogrammetrie"
	unit= None
	description="Ellipse finder quality for photogrammetry" 
	uri= None
	measurementclass=None  
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Art der Referenzpunktqualität für Scannen 
	keyword = 'ellipse_quality_type'
	beschreibung = "Art der Referenzpunktqualität für Scannen"
	unit= None
	description="Ellipse finder quality for scanning" 
	uri= None
	measurementclass=None   
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Ausnahme "Lichtänderung": Abbruch?
	keyword = 'exception_lighting_change_abort'
	beschreibung = 'Ausnahme "Lichtänderung": Abbruch?'
	unit= None
	description='Exception "Lightning change":abort?' 
	uri= None
	measurementclass=None   
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Ausnahme "Lichtänderung": Anzahl der Wiederholungen 
	keyword = 'exception_lighting_change_number_of_repetitions'
	beschreibung = 'Ausnahme "Lichtänderung": Anzahl der Wiederholungen'
	unit= None
	description='Exception "Lightning change":number of repetitions' 
	uri= None
	measurementclass=None  
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Ausnahme "Lichtänderung": Verzögerung
	keyword = 'exception_lighting_change_delay'
	beschreibung = 'Ausnahme "Lichtänderung": Verzögerung'
	unit= None
	description='Exception "Lightning change":delay' 
	uri= None
	measurementclass=None  
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Ausnahme "Sensor dekalibriert": Verzögerung
	keyword = 'exception_decalibrated_sensor_delay'
	beschreibung = 'Ausnahme "Sensor dekalibriert": Verzögerung'
	unit= None
	description='Exception "Decalibrated":delay' 
	uri= None
	measurementclass=None  
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Ausnahme "Sensor dekalibriert": Abbruch?
	keyword = 'exception_decalibrated_sensor_abort'
	beschreibung = 'Ausnahme "Sensor dekalibriert": Abbruch?'
	unit= None
	description='Exception "Decalibrated":abort?' 
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Ausnahme "Sensor dekalibriert": Anzahl der Wiederholungen 
	keyword = 'exception_decalibrated_sensor_number_of_repetitions'
	beschreibung = 'Ausnahme "Sensor dekalibriert": Anzahl der Wiederholungen'
	unit= None
	description='Exception "Decalibrated":number of repetitions' 
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Ausnahme "Sensorbewegung": Abbruch?
	keyword = 'exception_sensor_movement_abort'
	beschreibung = 'Ausnahme "Sensorbewegung": Abbruch?'
	unit= None
	description='Exception "Sensor movement":abort?' 
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Ausnahme "Sensorbewegung": Anzahl der Wiederholungen 
	keyword = 'exception_sensor_movement_number_of_repetitions'
	beschreibung = 'Ausnahme "Sensorbewegung": Anzahl der Wiederholungen'
	unit= None
	description='Exception "Sensor movement":number of repetitions' 
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Ausnahme "Sensorbewegung": Verzögerung
	keyword = 'exception_sensor_movement_delay' 
	beschreibung = 'Ausnahme "Sensorbewegung": Verzögerung'
	unit= None
	description='Exception "Sensor movement":delay' 
	uri= None
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Ausnahme "Transformation": Abbruch?
	keyword = 'exception_transformation_abort'
	beschreibung = 'Ausnahme "Transformation": Abbruch?'
	unit= None
	description='Exception "Transformation":delay' 
	uri= None
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Ausnahme "Transformation": Anzahl der Wiederholungen
	keyword = 'exception_transformation_number_of_repetitions'
	beschreibung = 'Ausnahme "Transformation": Anzahl der Wiederholungen'
	unit= None
	description='Exception "Transformation":number of repetitions' 
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Ausnahme "Transformation": Verzögerung
	
	##--Ausrichtung 
	#-Name
	keyword = 'alignment.name'
	beschreibung="Name"
	unit= None
	description="Name" 
	uri= None
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass)
		
	#Abweichung
	keyword = 'alignment.deviation'
	beschreibung= 'Abweichung'
	unit=om+"millimetre"
	description="Deviation" 
	uri= None
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass)
		
	# Drehung X
	keyword = 'alignment.rotation.x'
	beschreibung= 'Drehung X'
	unit=om+"radian"
	description="Rotation X"
	uri= ontologynamespace+'alignmentRotationX'
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass)
	
	# Drehung Y
	keyword = 'alignment.rotation.y'
	beschreibung= 'Drehung Y'
	unit=om+"radian"
	description="Rotation Y" 
	uri= ontologynamespace+'alignmentRotationY'
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass)
	
	# Drehung Z
	keyword = 'alignment.rotation.z'
	beschreibung= 'Drehung Z'
	unit=om+"radian"
	description="Rotation Z"
	uri= ontologynamespace+'alignmentRotationZ'
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass)
		
	# Verschiebung X
	keyword = 'alignment.translation.x'
	beschreibung= 'Verschiebung X'
	unit=om+"millimetre"
	description="Translation X"
	uri= ontologynamespace+'alignmentTranslationX'
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass)
	
	# Verschiebung Y
	keyword = 'alignment.translation.y'
	beschreibung= 'Verschiebung Y'
	unit=om+"millimetre"
	description="Translation Y"
	uri= ontologynamespace+'alignmentTranslationY'
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass)
	
	# Verschiebung Z 
	keyword = 'alignment.translation.z'
	beschreibung= 'Verschiebung Z'
	unit=om+"millimetre"
	description="Translation Z"
	uri= ontologynamespace+'alignmentTranslationZ'
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass)
	
	
	## Benutzerdefinierte Keywords
	# Ausrichtungsresiduum (Messungen)
	keyword = 'measurement_alignment_residual'
	beschreibung = 'Ausrichtungsresiduum (Messungen)'
	unit=om+"millimetre"
	description="Alignment residual (measurments)"
	uri= ontologynamespace+'MeasurementAlignmentResidual'
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Ausrichtungsresiduum (Refernzpunkte)
	keyword = 'measurement_reference_point_alignment_residual'
	beschreibung = 'Ausrichtungsresiduum (Referenzpunkte)'
	unit=om+"millimetre"
	description="Alignment residual (reference points)"
	uri= ontologynamespace+'MeasurementPointAlignmentResidual'
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Ausrichtungsresiduum (Vorschaunetze)
	keyword = 'measurement_mesh_alignment_residual'
	beschreibung = 'Ausrichtungsresiduum (Vorschaunetze)'
	unit=om+"millimetre"
	description="Alignment residual (preview meshes)"
	uri= ontologynamespace+'MeasurementMeshAlignmentResidual'
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Automatische Belichtungszeit(Modus)
	keyword = 'automatic_exposure_time_mode'
	beschreibung = 'Automatische Belichtungszeit(Modus)'
	unit= om+"second-Time" 
	description="Automatic exposure time (mode)"
	uri= None
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Benutzerdefinierte Referenzpunktfarbe
	keyword = 'user_defined_reference_point_color'
	beschreibung = 'Benutzerdefinierte Referenzpunktfarbe'
	unit= None
	description="User defined reference point color"
	uri= None
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Benutzte Norm "Allgemeine Toleranzen" (Toleranztabelle)
	keyword = 'used_general_tolerances'
	beschreibung = 'Benutzte Norm "Allgemeine Toleranzen" (Toleranztabelle)'
	unit= None
	description='Used standard "General tolerances"(tolerance table)'
	uri= None
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Benutzte Norm "Form/Lage Toleranzen" (Toleranztabelle) 
	keyword = 'used_gdat_tolerances'
	beschreibung = 'Benutzte Norm "Form/Lage Toleranzen" (Toleranztabelle)'
	unit= None
	description='Used standard "GD&T tolerances"(tolerance table)'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# CAD-Gruppe
	keyword = 'cad_group'
	beschreibung = 'CAD-Gruppe'
	unit= None
	description='CAD Group' 
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	#-- Digitalisierungs- und Inspektionsmodul 
	
	# Eindeutiger Indentifikator des Automatisierungsmoduls
	keyword = 'project_building_block_uuid_draft'
	beschreibung = 'Eindeutiger Indentifikator des Automatisierungsmoduls'
	unit= None
	description='Unique identifier'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Ellipsenfinder-Qualität für Photogrammetrie 
	keyword = 'ellipse_quality_for_photogrammetry'
	beschreibung = 'Ellipsenfinder-Qualität für Photogrammetrie'
	unit= om+"pixel"
	description='Ellipse finder quality for photogrammetry'
	uri= ontologynamespace+'EllipseQualityForPhotogrammetry'
	measurementclass=None	 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Ellipsenfinder-Qualität für Scannen
	keyword = 'ellipse_quality'
	beschreibung = 'Ellipsenfinder-Qualität für Scannen'
	unit= om+"pixel"
	description='Ellipse finder quality for scanning'
	uri= ontologynamespace+'EllipseQuality'
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass)  
	
	# Ellipsenmindestgröße für Photogrammetrie
	keyword = 'min_ellipse_radius_for_photogrammetry'
	beschreibung = 'Ellipsenmindestgröße für Photogrammetrie'
	unit= om+"millimetre"
	description='Min. ellipse size for photogrammetry'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass)  
	
	# Ellipsenmindestgröße für Scannen
	keyword = 'min_ellipse_radius'
	beschreibung = 'Ellipsenmindestgröße für Scannen'
	unit= om+"millimetre"
	description='Min. ellipse size for scanning'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Inspektionselement (Liste) - nicht in Reports
	keyword = 'inspections_not_in_reports'
	beschreibung = 'Inspektionselement (Liste) - nicht in Reports'
	unit= None
	description='Inspection elements(list)-not in reports'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Ist-Master
	keyword = 'actual_master'
	beschreibung = 'Ist-Master'
	unit= None
	description='Actual master'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
		
	# Max.Blickwinkel Sensor/Fläche
	keyword = 'max_viewing_angle_sensor_surface'
	beschreibung = 'Max.Blickwinkel Sensor/Fläche'
	unit= om+"radian"
	description='Max. viewing angle sensor/surface'
	uri= None
	measurementclass=None	
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Max. Residuum
	keyword = 'max_residual'
	beschreibung = 'Max. Residuum'
	unit= None
	description='Max. residual'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Max. Sensorbewegung
	keyword = 'max_sensor_movement'
	beschreibung = 'Max. Sensorbewegung'
	unit=om+"pixel"
	description='Max. sensor movement'
	uri= ontologynamespace+'MaximumSensorMovement'
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Max. Tiefenbegrenzung
	keyword = 'max_depth_limitation'
	beschreibung = 'Max. Tiefenbegrenzung'
	unit= None
	description='Max. depth limitation'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
		
	# Messauflösung
	keyword = 'measurement_resolution'
	beschreibung = 'Messauflösung'
	unit= None
	description='Measurment resolution'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
		
	# Messtemperatur
	keyword = 'measurement_temperature'
	beschreibung = 'Messtemperatur'
	unit=om+"degreeCelsius"
	description='Measurment temperature'
	uri= ontologynamespace+'MeasurementTemperature'
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
		
	# Min. Streifenkontrast
	keyword = 'min_fringe_contrast'
	beschreibung = 'Min. Streifenkontrast'
	unit= None
	description='Min. fringe contrast'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Min. Tiefenbegrenzung 
	keyword = 'min_depth_limitation'
	beschreibung = 'Min. Tiefenbegrenzung'
	unit= None
	description='Min. depth limitation'
	uri= None
	measurementclass=None  
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Minimaler Ellipsenkontrast für Photogrammetrie
	keyword = 'min_ellipse_contrast_for_photogrammetry'
	beschreibung = 'Minimaler Ellipsenkontrast für Photogrammetrie'
	unit= None
	description='Min. ellipse contrast for photogrammetry'
	uri= None
	measurementclass=None  
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Minimaler Ellipsenkontrast für Scannen 
	keyword = 'min_ellipse_contrast_for_scanning'
	beschreibung = 'Minimaler Ellipsenkontrast für Scannen'
	unit= None
	description='Min. ellipse contrast for scanning'
	uri= None
	measurementclass=None  
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
		
	# -- Photogrammetriemodul
	
	# Projekt-Kexwords (Liste der Projekt-Keywords) 
	keyword = 'project_keywords'
	beschreibung = 'Projekt-Keywords (Liste der Projekt-Keywords)'
	unit= None
	description='Project keywords (list of project keywords)'
	uri= None
	measurementclass=None  
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Qualitätskontrolle Triple-Scan-Punkte
	keyword = 'quality_triple_scan_points_mode'
	beschreibung = 'Qualitätskontrolle Triple-Scan-Punkte'
	unit= None
	description='Quality check Triple Scan points'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Referenzpunktgröße 
	keyword = 'reference_point_size'
	beschreibung = 'Referenzpunktgröße'
	unit=om+"millimetre"
	description='Reference point size'
	uri= None
	measurementclass=None	 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Referenzpunktmaterialstärke
	keyword = 'reference_point_thickness'
	beschreibung = 'Referenzpunktmaterialstärke'
	unit= None
	description='Reference point thickness'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass)  
	
	# Referenzpunkttyp 
	keyword = 'reference_point_type'
	beschreibung = 'Referenzpunkttyp'
	unit= None
	description='Reference point type'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
		
	# -- Referenzstufe
	
	# Reflexionserkennung
	keyword = 'reflection_detection'
	beschreibung = 'Reflexionserkennung' 
	unit= None
	description='Reflection detection'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Schwellwert für Qualität der Triple-Scan-Punkte
	keyword = 'quality_triple_scan_points_threshold'
	beschreibung = 'Schwellwert für Qualität der Triple-Scan-Punkte'
	unit= None
	description='Quality check Triple Scan points'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Status: Benutzerdefinierte Refernzpunktgröße benutzt?
	keyword = 'use_user_defined_reference_point_size[0]'
	beschreibung = 'Status: Benutzerdefinierte Refernzpunktgröße benutzt?'
	unit= None
	description='State: Use user-defined reference point size?'
	uri= None
	measurementclass=None
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Status: Einfluss von Randbereichen bei Polygonisierung reduzieren?
	keyword = 'reduce_influence_of_border_areas'
	beschreibung = 'Status: Einfluss von Randbereichen bei Polygonisierung reduzieren?'
	unit= None
	description='State: Reduce influence of border areas for polygonization?'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Status: Grauwert-Features berücksichtigen?
	keyword = 'observe_gray_value_feature'
	beschreibung = 'Status: Grauwert-Features berücksichtigen?'
	unit= None
	description='State: Observe gray value feature?'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Status: Kontrolle "Lichtänderung"?
	keyword = 'check_lighting_change'
	beschreibung = 'Status: Kontrolle "Lichtänderung"?'
	unit= None
	description='State: Check "Lightning change"?'
	uri= ontologynamespace+'lightningChangeCheck'
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Status: Kontrolle "Sensor dekalibriert"?
	keyword = 'check_decalibrated_sensor'
	beschreibung = 'Status: Kontrolle "Sensor dekalibriert"?'
	unit= None
	description='State: Check "Decalibrated sensor"?'
	uri= ontologynamespace+'sensorDecalibrationCheck'
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Status: Kontrolle "Sensorbewegung"?
	keyword = 'check_sensor_movement'
	beschreibung = 'Status: Kontrolle "Sensorbewegung"?'
	unit= None
	description='State: Check "Sensor movement"?'
	uri= ontologynamespace+'movementControlActivated'
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Status: Kontrolle "Transformation"?
	keyword = 'check_transformation'
	beschreibung = 'Status: Kontrolle "Transformation"?'
	unit= None
	description='State: Check "Transformation"?'
	uri= ontologynamespace+'transformationCheck'
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Status: Kontrolle fehlender Referenzpunkte?
	keyword = 'check_missing_reference_points'
	beschreibung = 'Status: Kontrolle fehlender Referenzpunkte?'
	unit= None
	description='State: Check missing reference points?'
	uri= ontologynamespace+'missingReferencePointCheck'
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
		
	# Status: Nach Abbruch zur Endposition fahren?
	keyword = 'automation_move_to_endposition_on_abort'
	beschreibung = 'Status: Nach Abbruch zur Endposition fahren?'
	unit= None
	description='State: Move to end postion on abort ?'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Status: Punnkte an Nutkanten vermeiden?
	keyword = 'avoid_points_on_groove_edges'
	beschreibung = 'Status: Punnkte an Nutkanten vermeiden?'
	unit= None
	description='State: Avoid points on groovy edges ?'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Status: Punkte an Scan-Bereichsgrenzen vermeiden?
	keyword = 'avoid_points_on_borders_in_scan_area'
	beschreibung = 'Status: Punkte an Scan-Bereichsgrenzen vermeiden?'
	unit= None
	description='State: Avoid points on borders in scan area ?'
	uri= ontologynamespace+'avoidScanningAreaBorderPoints'
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Status: Punkte auf Glanzstellen vermeiden?
	keyword = 'avoid_points_on_shiny_surfaces'
	beschreibung = 'Status: Punkte auf Glanzstellen vermeiden?'
	unit= None
	description='State: Avoid points on shiny surfaces ?'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Status: Punkte bei starken Helligkeitsunterschieden vermeiden?
	keyword = 'avoid_points_at_strong_brightness_differences'
	beschreibung = 'Status: Punkte bei starken Helligkeitsunterschieden vermeiden?'
	unit= None
	description='State: Avoid points at strong brightness differences ?'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Status: Punkte in Schattenbereichen vermeiden
	keyword = 'avoid_points_in_shadow_areas'
	beschreibung = 'Status: Punkte in Schattenbereichen vermeiden'
	unit= None
	description='State: Avoid points in shadow areas ?'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Status: Referenzpunktgröße benutzt?
	keyword = 'use_reference_point_size'
	beschreibung = 'Status: Referenzpunktgröße benutzt?'
	unit= None
	description='State: Use reference point size ?'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
		
	# Status: Sind Messungen ausgerichtet?
	keyword = 'are_measurements_aligned'
	beschreibung = 'Status: Sind Messungen ausgerichtet?'
	unit= None
	description='State: Are measurements alligned ?'
	uri= ontologynamespace+'areMeasurementsAligned'
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
		
	# Status: Triple-Scan-Punkte bei starken Helligkeitsunterschieden vermeiden? 
	keyword = 'avoid_triple_scan_points_at_strong_brightness_differences'
	beschreibung = 'Status: Triple-Scan-Punkte bei starken Helligkeitsunterschieden vermeiden?'
	unit= None
	description='State: Avoid Triple Scan points at strong brightness differences ?'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Status: Triple-Scan-Punkte vermeiden?
	keyword = 'avoid_triple_scan_points'
	beschreibung = 'Status: Triple-Scan-Punkte vermeiden?'
	unit= None
	description='State: Avoid Triple Scan points ?'
	uri= ontologynamespace+'avoidTripleScanPoints'
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Status: Wird Qualität der Triple-Scan-Punkte geprüft?
	keyword = 'is_quality_triple_scan_points_checked'
	beschreibung = 'Status: Wird Qualität der Triple-Scan-Punkte geprüft?'
	unit= None
	description='State: Is quality Triple Scan points checked ?'
	uri= None
	measurementclass=None  
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# -- Stufe
	
	# Tiefenbegrenzungsmodus
	keyword = 'depth_limitation_mode'
	beschreibung = 'Tiefenbegrenzungsmodus'
	unit= None
	description='Depth limitation mode'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Typ der Messungstransformation
	keyword = 'measurement_transformation_type'
	beschreibung = 'Typ der Messungstransformation'
	unit= None
	description='Measurement transformation type'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# Typ des Automatisierungsmoduls 
	keyword = 'project_building_block_type_draft'
	beschreibung = 'Typ des Automatisierungsmoduls'
	unit= None
	description='Automation module type'
	uri= None
	measurementclass=None 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass) 
	
	# -- VMR-Modul 
	
	# -- Vorlageninformation
	
	# measurementseries
	
	list_messreihen = []
	mr = 0
	
	while mr < len(gom.app.project.measurement_series):
		
		messreihe = {}
		messreihe_infos = {}
		
		def infos_mr (keyword, beschreibung,unit=None, description=None, uri=None, measurementclass=None, value=None, from_application="true"):
			dir = {}
			if keyword == 'reference_points_master_series':
				dir["value"] = gom.app.project.measurement_series[mr].get(keyword).get('name')
				dir["value_type"] = type(dir["value"]).__name__
			elif value == None:
				dir["value"] = gom.app.project.measurement_series[mr].get(keyword)
				dir["value_type"] = type(gom.app.project.measurement_series[mr].get(keyword)).__name__
			else:
				dir["value"] = value 
				dir["value_type"] = type(dir["value"]).__name__
			
			dir["key_deu"] = beschreibung
			if  description != None:
				dir["key_eng"] =  description
			if  uri != None:
				dir["uri"] =  uri
			if  unit != None:
				dir["unit"] =  unit
			if  measurementclass != None:
				dir["measurementclass"] =  measurementclass

			dir["from_application"]=from_application
			
			if dir["value"] != None:
				if len(str(dir["value"])) != 0:
					if includeonlypropswithuri and "uri" in dir:
						messreihe_infos[keyword] ={}		
						messreihe_infos[keyword] = dir			

					if not includeonlypropswithuri:			
						messreihe_infos[keyword] ={}		
						messreihe_infos[keyword] = dir

		
		##  Icons		
		# Icon des Objekttyps
		keyword = 'icon (type)'
		beschreibung = "Icon des Objekttyps"
		unit=None
		description= 'Object type icon'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# Icon des Objekttyps und des Status 
		keyword = 'icon (explorer_type_and_state)'
		beschreibung = "Icon des Objekttyps und des Status"
		unit=None
		description= 'Object type and state icon'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
	
		## Informationen
	
		# Anzahl der benutzten gemeinsamen Referenzpunkte
		keyword = 'number_of_used_common_reference_points'
		beschreibung = "Anzahl der benutzten gemeinsamen Referenzpunkte"
		unit=None
		description= 'Number of used common reference points'
		uri=ontologynamespace+'numberOfUsedCommonReferencePoints'
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# Ausdehnungskoeffizient des Referenzpunktrahmens
		keyword = 'reference_point_frame_expansion_coefficient'
		beschreibung = "Ausdehnungskoeffizient des Referenzpunktrahmens"
		unit=None
		description= 'Reference point frame expansion coefficisent'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# Benötigte Ausrichtung zur Berechnung
		keyword = 'alignment_at_calculation'
		beschreibung = "Benötigte Ausrichtung zur Berechnung"
		unit=None
		description= 'Required allignment for calculation'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# Benötigte Starrkörperbewegungskorrektur zur Berechnung 
		keyword = 'rigid_body_motion_compensation_at_calculation'
		beschreibung = "Benötigte Starrkörperbewegungskorrektur zur Berechnung"
		unit=None
		description= 'Required rigid body motion compensation for calculation'
		uri=None
		measurementclass=None		
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# Berechnungsinformationen 
		keyword = 'computation_information'
		beschreibung = "Berechnungsinformationen"
		unit=None
		description= 'Computation information'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
				
		# Element-Keywords (Liste der Element-Keywords)
		keyword = 'element_keywords'
		beschreibung = "Element-Keywords (Liste der Element-Keywords)"
		unit=None
		description= 'Element keywords (list of element keywords)'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# Explorerkategorie
		keyword = 'explorer_category'
		beschreibung = "Explorerkategorie"
		unit=None
		description= 'Explorer category'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# Externe Photogrammetriedatei
		keyword = 'external_photogrammetry_file'
		beschreibung = "Externe Photogrammetriedatei"
		unit=None
		description= 'External photogrammetry file'
		uri=None
		measurementclass=None		
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# Importdatei
		keyword = 'import_file'
		beschreibung = "Importdatei"
		unit=None
		description= 'Import file'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# Importdateiname
		keyword = 'import_file_name'
		beschreibung = "Importdateiname"
		unit=None
		description= 'Import file name'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# Kalibriertemperatur des Referenzpunktrahmens 
		keyword = 'reference_point_frame_calibration_temperature'
		beschreibung = "Kalibriertemperatur des Referenzpunktrahmens"
		unit=om+"degreeCelsius"
		description= 'Reference point frame calibration temprature'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# Kommentar
		keyword = 'comment'
		beschreibung = "Kommentar"
		unit=None
		description= 'comment'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# Messaufbau
		keyword = 'measuring_setup'
		beschreibung = "Messaufbau"
		unit=None
		description= 'Measuring setup'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# Name
		keyword = 'name'
		beschreibung = "Name"
		unit=None
		description= 'Name'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# Name(importiert)
		keyword = 'imported_name'
		beschreibung = "Name(importiert)"
		unit=None
		description= 'Name(imported)'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# Name des Referenzpunktrahmens
		keyword = 'reference_point_frame_name'
		beschreibung = "Name des Referenzpunktrahmens"
		unit=None
		description= 'reference point frame name'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
				
		# Residuum der Transformation über gemeinsame Referenzpunkte
		keyword = 'common_reference_point_transformation_residual'
		beschreibung = "Residuum der Transformation über gemeinsame Referenzpunkte"
		unit=None
		description= 'Common reference point transformation residual'
		uri=ontologynamespace+'CommonReferencePointTransformationResidual'
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
			
		# Status: ExternePhotogrammetrie GSI Einheit in 'mm'?
		keyword = 'external_photogrammetry_gsi_unit_is_mm'
		beschreibung = "Status: ExternePhotogrammetrie GSI Einheit in 'mm'?"
		unit=None
		description= "State: GSI unit is 'mm'(external photogrammetry)"
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# Status: Ist ASCII als GSI geladen (externe Photogrammetrie)?
		keyword = 'external_photogrammetry_load_ascii_as_gsi'
		beschreibung = "Status: Ist ASCII als GSI geladen (externe Photogrammetrie)?"
		unit=None
		description= 'State: Is ASCII loaded as GSI(external photogrammetry)'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# Status: Ist Element selektiert? 
		keyword = 'is_selected'
		beschreibung = "Status: Ist Element selektiert? "
		unit=None
		description= 'State: Is element selected?'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# Status: Ist Element sichtbar?
		keyword = 'is_visible'
		beschreibung = "Status: Ist Element sichtbar?"
		unit=None
		description= 'State: Is element visible?'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
			
		# Status: Ist Sichtbarkeitszustand gesperrt?
		keyword = 'is_visibility_locked'
		beschreibung = "Status: Ist Sichtbarkeitszustand gesperrt?"
		unit=None
		description= 'State: Is visibility state locked?'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
				
		# Status: Ist in Inspektionselement referenziert?
		keyword = 'is_referenced_in_inspection'
		beschreibung = "Status: Ist in Inspektionselement referenziert?"
		unit=None
		description= 'State: Is referenced in inspection element?'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
			
		# Status: Ist über gemeinsameReferenzpunkte transformiert?
		keyword = 'is_transformed_by_common_reference_points'
		beschreibung = "Status: Ist über gemeinsameReferenzpunkte transformiert?"
		unit=None
		description= 'State: Is transformed by common reference points?'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# Status: Name erzeugt? 
		keyword = 'is_name_generated'
		beschreibung = "Status: Name erzeugt? "
		unit=None
		description= 'State: Is name generated?'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# Status: Punkte außerhalb CAD ausschneiden?
		keyword = 'cut_out_points_outside_cad'
		beschreibung = "Status: Punkte außerhalb CAD ausschneiden?"
		unit=None
		description= 'State: Cut out points outside CAD?'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# Status: Punkte für VDI Test ausschneiden?
		keyword = 'cut_out_points_for_vdi'
		beschreibung = "Status: Punkte für VDI Test ausschneiden?"
		unit=None
		description= 'State: Cut out points for VDI test?'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# Status: Punkte hinter Ebene ausschneiden?
		keyword = 'cut_out_points_below_plane'
		beschreibung = "Status: Punkte hinter Ebene ausschneiden?"
		unit=None
		description= 'State: Cut out points below plane?'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# Status: Schattenpunkte der Vorrichtung ausschneiden?
		keyword = 'cut_out_shadow_points_of_fixture'
		beschreibung = "Status: Schattenpunkte der Vorrichtung ausschneiden?"
		unit=None
		description= 'State: Cut out shadow points of fixture?'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# Tags (Liste der Elementtags)
		keyword = 'tags'
		beschreibung = "Tags (Liste der Elementtags)"
		unit=None
		description= 'Tags(list of element tags)'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
				
		# Transformationsmodus 
		keyword = 'transformation_mode'
		beschreibung = "Transformationsmodus"
		unit=None
		description= 'Transformation mode'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
				
#		# Reference points master measurement series
		if (gom.app.project.measurement_series[mr].get ('transformation_mode')) == 'depends on other':
			keyword = 'reference_points_master_series'
			beschreibung = None
			unit=None
			description= 'Reference points master measurement series'
			uri=None
			measurementclass=None
			infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
	
		# VDI-Aufnahme/Überwachung
		keyword = 'vdi_acceptance_test'
		beschreibung = "VDI-Aufnahme/Überwachung"
		unit=None
		description= 'VSI acceptance/reverification test'
		uri=None
		measurementclass=None
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# berechnete Werte 
		# Anzahl Messungen pro Messreihe 
		keyword = 'number of measurements'
		beschreibung = "Anzahl Messungen"
		unit=None
		description= 'number of measurements'
		uri=None
		measurementclass=None
		from_application= "script-based calculation"
		value= len(gom.app.project.measurement_series[mr].measurements)
		anz_messungen = anz_messungen + value
		infos_mr(keyword,beschreibung,unit,description,uri,measurementclass, value, from_application)
		
	
		# Einzelmessungen 
		list_messungen = []
		list_sensors = []
		temp_list_cal_time =[]
		m = 0
		
		while m < (len(gom.app.project.measurement_series[mr].measurements)):
				
			messung = {}
			dic_measurement_setup= {}
			dic_measurement_check={}
			dic_measurement_info ={}
			dic_measurement_sensor={}
			# sensors
			dic_sensor = {}
			calibration={}
			dic_measurement_cal_sensor= {}
			dic_measurement_cal_calobject= {}
			dic_measurement_cal_calsetup= {}
			dic_measurement_cal_calresults= {}
			
			# Messverfahren 	
			# nur wenn es Messungen gibt, kann es auch eine Aufnahmeverfahren geben
			keyword= 'acquisition_technology'
			beschreibung = "Aufnahmeverfahren"
			value= 'fringe projection'
			unit= None
			description='acquisition technology'
			uri= ontologynamespace+"AcquisitionTechnology"
			measurementclass=ontologynamespace+"FringeProjection"
			from_application= 'false'
			infos_p(keyword,beschreibung,unit,description,uri,measurementclass, value,from_application)	
			
			# measurements			
			def infos_m (keyword, beschreibung,unit=None, description=None, uri=None, measurementclass=None, from_application="true" ):
				dir = {}
				dir["value"] = gom.app.project.measurement_series[mr].measurements[m].get (keyword)
				dir["key_deu"] = beschreibung
				if  description != None:
					dir["key_eng"] =  description
				if  uri != None:
					dir["uri"] =  uri
				if  unit != None:
					dir["unit"] =  unit
				if  measurementclass != None:
					dir["measurementclass"] =  measurementclass
				dir["value_type"] = type(gom.app.project.measurement_series[mr].measurements[m].get(keyword)).__name__
				dir["from_application"]= from_application
				
				if keyword == "acquisition_time": 
					t = time.strptime(gom.app.project.measurement_series[mr].measurements[m].get ('acquisition_time'), "%a %b %d %H:%M:%S %Y")
					capturetime = (time.strftime("%Y-%m-%dT%H:%M:%S",t))
					dir["value"] = capturetime
					dir["value_type"]="dateTime"
						
				if dir["value"] != None:
					if len(str(dir["value"])) != 0:
						if includeonlypropswithuri and "uri" in dir:
							messung[keyword] = {}		
							messung[keyword] = dir
						if not includeonlypropswithuri:			
							messung[keyword] = {}		
							messung[keyword] = dir
					
								
			def infos_m_setup (keyword, beschreibung,unit=None, description=None, uri=None, measurementclass=None, from_application="true" ):
				dir = {}
				dir["value"] = gom.app.project.measurement_series[mr].measurements[m].get (keyword)
				dir["key_deu"] = beschreibung
				if  description != None:
					dir["key_eng"] =  description
				if  uri != None:
					dir["uri"] =  uri
				if  unit != None:
					dir["unit"] =  unit
				if  measurementclass != None:
					dir["measurementclass"] =  measurementclass
				dir["value_type"] = type(gom.app.project.measurement_series[mr].measurements[m].get(keyword)).__name__
				dir["from_application"]= from_application
				
				if keyword == "acquisition_time": 
					t = time.strptime(gom.app.project.measurement_series[mr].measurements[m].get ('acquisition_time'), "%a %b %d %H:%M:%S %Y")
					capturetime = (time.strftime("%Y-%m-%dT%H:%M:%S",t))
					dir["value"] = capturetime
					dir["value_type"]="dateTime"
					
				if dir["value"] != None:
					if len(str(dir["value"])) != 0:
						if includeonlypropswithuri and "uri" in dir:
							dic_measurement_setup[keyword] = {}		
							dic_measurement_setup[keyword] = dir
						if not includeonlypropswithuri:			
							dic_measurement_setup[keyword] = {}		
							dic_measurement_setup[keyword] = dir
		
			def infos_m_check (keyword, beschreibung,unit=None, description=None, uri=None, measurementclass=None, from_application="true" ):
				dir = {}
				dir["value"] = gom.app.project.measurement_series[mr].measurements[m].get (keyword)
				dir["key_deu"] = beschreibung
				if  description != None:
					dir["key_eng"] =  description
				if  uri != None:
					dir["uri"] =  uri
				if  unit != None:
					dir["unit"] =  unit
				if  measurementclass != None:
					dir["measurementclass"] =  measurementclass
				dir["value_type"] = type(gom.app.project.measurement_series[mr].measurements[m].get(keyword)).__name__
				dir["from_application"]= from_application
				
				if keyword == "acquisition_time": 
					t = time.strptime(gom.app.project.measurement_series[mr].measurements[m].get ('acquisition_time'), "%a %b %d %H:%M:%S %Y")
					capturetime = (time.strftime("%Y-%m-%dT%H:%M:%S",t))
					dir["value"] = capturetime
					dir["value_type"]="dateTime"

				if dir["value"] != None:
					if len(str(dir["value"])) != 0:
						if includeonlypropswithuri and "uri" in dir:
							dic_measurement_check[keyword] = {}		
							dic_measurement_check[keyword] = dir
						if not includeonlypropswithuri:			
							dic_measurement_check[keyword] = {}
							dic_measurement_check[keyword] = dir
				
			def infos_m_properties (keyword, beschreibung,unit=None, description=None, uri=None, measurementclass=None, from_application="true" ):
				dir = {}
				dir["value"] = gom.app.project.measurement_series[mr].measurements[m].get (keyword)
				dir["key_deu"] = beschreibung
				if  description != None:
					dir["key_eng"] =  description
				if  uri != None:
					dir["uri"] =  uri
				if  unit != None:
					dir["unit"] =  unit
				if  measurementclass != None:
					dir["measurementclass"] =  measurementclass
				dir["value_type"] = type(gom.app.project.measurement_series[mr].measurements[m].get(keyword)).__name__
				dir["from_application"]= from_application
				
				if keyword == "acquisition_time": 
					t = time.strptime(gom.app.project.measurement_series[mr].measurements[m].get ('acquisition_time'), "%a %b %d %H:%M:%S %Y")
					capturetime = (time.strftime("%Y-%m-%dT%H:%M:%S",t))
					dir["value"] = capturetime
					dir["value_type"]="dateTime"

				if dir["value"] != None:
					if len(str(dir["value"])) != 0:
						if includeonlypropswithuri and "uri" in dir:
							dic_measurement_info[keyword] = {}		
							dic_measurement_info[keyword] = dir
						if not includeonlypropswithuri:			
							dic_measurement_info[keyword] = {}
							dic_measurement_info[keyword] = dir	
							

			## capturing device 	
						
			def infos_capturing_device (keyword, beschreibung, value, unit=None, description=None, uri=None, measurementclass=None, from_application="true"):
				dir = {}
				dir["value"] = value
				dir["key_deu"] = beschreibung
				if  description != None:
					dir["key_eng"] =  description
				if  uri != None:
					dir["uri"] =  uri
				if  unit != None:
					dir["unit"] =  unit
				if  measurementclass != None:
					dir["measurementclass"] =  measurementclass
				dir["value_type"] = type(value).__name__
				dir["from_application"]= from_application
				
				if keyword == "acquisition_time": 
					t = time.strptime(gom.app.project.measurement_series[mr].measurements[m].get ('acquisition_time'), "%a %b %d %H:%M:%S %Y")
					capturetime = (time.strftime("%Y-%m-%dT%H:%M:%S",t))
					dir["value"] = capturetime
					dir["value_type"]="dateTime"

				if dir["value"] != None:
					if len(str(dir["value"])) != 0:
						if includeonlypropswithuri and "uri" in dir:
							dic_measurement_sensor[keyword] = {}		
							dic_measurement_sensor[keyword] = dir
						if not includeonlypropswithuri:			
							dic_measurement_sensor[keyword] = {}		
							dic_measurement_sensor[keyword] = dir

			## calibration	
			
			def infos_cali (keyword, beschreibung,unit=None, description=None, uri=None, measurementclass=None, from_application="true"):
				dir = {}
				
				dir["value"] = gom.app.project.measurement_series[mr].measurements[m].get (keyword)
				dir["key_deu"] = beschreibung
				if  description != None:
					dir["key_eng"] =  description
				if  uri != None:
					dir["uri"] =  uri
				if  unit != None:
					dir["unit"] =  unit
				if  measurementclass != None:
					dir["measurementclass"] =  measurementclass
				dir["value_type"] = type(gom.app.project.measurement_series[mr].measurements[m].get(keyword)).__name__
				dir["from_application"]= from_application
								
				if dir["value"] != None:
					if len(str(dir["value"])) != 0:
						if includeonlypropswithuri and "uri" in dir:
							calibration[keyword] = {}		
							calibration[keyword] = dir
						if not includeonlypropswithuri:			
							calibration[keyword] = {}
							calibration[keyword] = dir
				

			def infos_cali_calobject (keyword, beschreibung,unit=None, description=None, uri=None, measurementclass=None, from_application="true"):
				dir = {}
				
				dir["value"] = gom.app.project.measurement_series[mr].measurements[m].get (keyword)
				dir["key_deu"] = beschreibung
				if  description != None:
					dir["key_eng"] =  description
				if  uri != None:
					dir["uri"] =  uri
				if  unit != None:
					dir["unit"] =  unit
				if  measurementclass != None:
					dir["measurementclass"] =  measurementclass
				dir["value_type"] = type(gom.app.project.measurement_series[mr].measurements[m].get(keyword)).__name__
				dir["from_application"]= from_application
				
				if dir["value"] != None:
					if len(str(dir["value"])) != 0:
						if includeonlypropswithuri and "uri" in dir:
							dic_measurement_cal_calobject[keyword] = {}		
							dic_measurement_cal_calobject[keyword] = dir
						if not includeonlypropswithuri:			
							dic_measurement_cal_calobject[keyword] = {}
							dic_measurement_cal_calobject[keyword] = dir


			def infos_cali_calsetup (keyword, beschreibung,unit=None, description=None, uri=None, measurementclass=None, from_application="true"):
				dir = {}
				
				dir["value"] = gom.app.project.measurement_series[mr].measurements[m].get (keyword)
				dir["key_deu"] = beschreibung
				if  description != None:
					dir["key_eng"] =  description
				if  uri != None:
					dir["uri"] =  uri
				if  unit != None:
					dir["unit"] =  unit
				if  measurementclass != None:
					dir["measurementclass"] =  measurementclass
				dir["value_type"] = type(gom.app.project.measurement_series[mr].measurements[m].get(keyword)).__name__
				dir["from_application"]= from_application
				
				## calibration_light_intensity, als int ohne '%' im value 
				if keyword == 'calibration_light_intensity':
					value= dir['value']
					value_new= value.replace('%','')
					value= int(value_new)
					dir["value_type"] = type(value).__name__
					dir["value"]= value 	
				
				if dir["value"] != None:
					if len(str(dir["value"])) != 0:
						if includeonlypropswithuri and "uri" in dir:
							dic_measurement_cal_calsetup[keyword] = {}		
							dic_measurement_cal_calsetup[keyword] = dir
						if not includeonlypropswithuri:			
							dic_measurement_cal_calsetup[keyword] = {}
							dic_measurement_cal_calsetup[keyword] = dir

					
			def infos_cali_calproperties (keyword, beschreibung,unit=None, description=None, uri=None, measurementclass=None, from_application="true"):
				dir = {}
				
				dir["value"] = gom.app.project.measurement_series[mr].measurements[m].get (keyword)
				dir["key_deu"] = beschreibung
				if  description != None:
					dir["key_eng"] =  description
				if  uri != None:
					dir["uri"] =  uri
				if  unit != None:
					dir["unit"] =  unit
				if  measurementclass != None:
					dir["measurementclass"] =  measurementclass
				dir["value_type"] = type(gom.app.project.measurement_series[mr].measurements[m].get(keyword)).__name__
				dir["from_application"]= from_application
				
				if keyword == "calibration_date": 
					t = time.strptime(gom.app.project.measurement_series[mr].measurements[m].get ('calibration_date'), "%a %b %d %H:%M:%S %Y")
					capturetime = (time.strftime("%Y-%m-%dT%H:%M:%S",t))
					dir["value"] = capturetime
					dir["value_type"]="dateTime"

				if dir["value"] != None:
					if len(str(dir["value"])) != 0:
						if includeonlypropswithuri and "uri" in dir:
							dic_measurement_cal_calresults[keyword] = {}		
							dic_measurement_cal_calresults[keyword] = dir
						if not includeonlypropswithuri:			
							dic_measurement_cal_calresults[keyword] = {}
							dic_measurement_cal_calresults[keyword] = dir
					
				
			## lokale Referenzpunkte
					
			rp_local = 0 
			list_rp_local= []
		
			while rp_local < gom.app.project.measurement_series[mr].measurements[m].get ('number_of_reference_points'):
				
				refpoints_local ={}
				def local_rp (keyword, beschreibung,unit=None, description=None, uri=None, measurementclass=None, from_application="true"):
					dir = {}
					dir["value"] = gom.app.project.measurement_series[mr].measurements[m].get(keyword+"["+str(rp_local)+"]")
					dir["key_deu"] = beschreibung
					if  description != None:
						dir["key_eng"] =  description
					if  uri != None:
						dir["uri"] =  uri
					if  unit != None:
						dir["unit"] =  unit
					if  measurementclass != None:
						dir["measurementclass"] =  measurementclass
					dir["value_type"] = type(gom.app.project.measurement_series[mr].measurements[m].get(keyword+"["+str(rp_local)+"]")).__name__
					dir["from_application"]= from_application
					
					if dir["value"] != None:
						if len(str(dir["value"])) != 0:
							if includeonlypropswithuri and "uri" in dir:
								refpoints_local[keyword] = {}		
								refpoints_local[keyword] = dir
							if not includeonlypropswithuri:			
								refpoints_local[keyword] = {}
								refpoints_local[keyword] = dir
													

				# Referenzpunktindex
				keyword = 'reference_point_id'
				beschreibung = "Referenzpunktindex"
				unit=None
				description= 'reference point id'
				uri=ontologynamespace+ 'PointID'
				measurementclass=None	
				local_rp(keyword,beschreibung,unit,description,uri,measurementclass)
		
				# Referenzpunktkoordinate X
				keyword = 'reference_point_coordinate.x'
				beschreibung = "Referenzpunktkoordinate X"
				unit='om:millimetre'
				description= 'Reference point coordinate X'
				uri=ontologynamespace+ 'xCoordinate'
				measurementclass=None
				local_rp(keyword,beschreibung,unit,description,uri,measurementclass)
				
				# Referenzpunktkoordinate Y
				keyword = 'reference_point_coordinate.y'
				beschreibung = "Referenzpunktkoordinate Y"
				unit='om:millimetre'
				description= 'Reference point coordinate Y'
				uri=ontologynamespace+ 'yCoordinate'
				measurementclass=None
				local_rp(keyword,beschreibung,unit,description,uri,measurementclass)
				
				# Referenzpunktkoordinate Z
				keyword = 'reference_point_coordinate.z'
				beschreibung = "Referenzpunktkoordinate Z"
				unit='om:millimetre'
				description= 'Reference point coordinate Z'
				uri=ontologynamespace+ 'zCoordinate'
				measurementclass=None
				local_rp(keyword,beschreibung,unit,description,uri,measurementclass)
				
				# Referenzpunktnormale X
				keyword = 'reference_point_normal.x'
				beschreibung = "Referenzpunktnormale X"
				unit='om:millimetre'
				description= 'Reference point normal X'
				uri=ontologynamespace+"xNormal"
				measurementclass=None
				local_rp(keyword,beschreibung,unit,description,uri,measurementclass)
				
				# Referenzpunktnormale Y
				keyword = 'reference_point_normal.y'
				beschreibung = "Referenzpunktnormale Y"
				unit='om:millimetre'
				description= 'Reference point normal Y'
				uri=ontologynamespace+"yNormal"
				measurementclass=None
				local_rp(keyword,beschreibung,unit,description,uri,measurementclass)
				
				# Referenzpunktnormale Z
				keyword = 'reference_point_normal.z'
				beschreibung = "Referenzpunktnormale Z"
				unit='om:millimetre'
				description= 'Reference point normal Z'
				uri=ontologynamespace+"zNormal"
				measurementclass=None
				local_rp(keyword,beschreibung,unit,description,uri,measurementclass)
			
				
				if len(refpoints_local) > 0:
					list_rp_local.append(refpoints_local)
				
				rp_local= rp_local+1
					
			## Icons
			
			# Icon des Objekttyps
			keyword = 'icon (type)'
			beschreibung = "Icon des Objekttyps"
			unit=None
			description= 'Object type icon'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Icon des Objekttyps und des Status
			keyword = 'icon (explorer_type_and_state)'
			beschreibung = "Icon des Objekttyps und des Status"
			unit=None
			description= 'Object type and state icon'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			## Informationen 
			
			# Aktuelle Kameratemperatur(ATOS IIe Rev.01 / ATOS III Rev.01)
			keyword = 'current_camera_temperature'
			beschreibung = "Aktuelle Kameratemperatur(ATOS IIe Rev.01 / ATOS III Rev.01)"
			unit=om+"degreeCelsius"
			description= 'Current camera temperature(ATOS IIe Rev.01 / ATOS III Rev.01)'
			uri=ontologynamespace+'CameraTemperature'
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
				
			# Anzahl der Belichtungszeiten 
			keyword = 'number_of_exposure_times'
			beschreibung = "Anzahl der Belichtungszeiten"
			unit=None
			description= 'Number of exposure times'
			uri=ontologynamespace+'numberOfShutterTimes'
			measurementclass=None
			infos_m_setup (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Anzahl der Kameras
			keyword = 'number_of_cameras'
			beschreibung = "Anzahl der Kameras"
			unit=None
			description= 'Number of cameras'
			uri=ontologynamespace+'numberOfCameras'
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)

			# Anzahl der Referenzkameras 
			keyword = 'number_of_reference_cameras'
			beschreibung = "Anzahl der Referenzkameras"
			unit=None
			description= 'Number of reference cameras'
			uri=ontologynamespace+'numberOfReferenceCameras'
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Anzahl der Referenzpunkte
			keyword = 'number_of_reference_points'
			beschreibung = "Anzahl der Referenzpunkte"
			unit=None
			description= 'Number of reference points'
			uri=ontologynamespace+'numberOfReferencePoints'
			measurementclass=None
			infos_m_properties (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Anzahl der Transformationspunkte 
			keyword = 'number_of_transformation_points'
			beschreibung = "Anzahl der Transformationspunkte "
			unit=None
			description= 'Number of transformation points'
			uri=ontologynamespace+'numberOfTransformationPoints'
			measurementclass=None
			infos_m_properties(keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Anzahl der Vorschaupunkte
			keyword = 'number_of_preview_points'
			beschreibung = "Anzahl der Vorschaupunkte"
			unit=None
			description= 'Number of preview points'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Anzahl der Wiederholungen
			keyword = 'number_of_repetitions'
			beschreibung = "Anzahl der Wiederholungen"
			unit=None
			description= 'Number of repetitions'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Automatische Belichtungszeit (Modus)
			keyword = 'automatic_exposure_time_mode'
			beschreibung = "Automatische Belichtungszeit (Modus)"
			unit=None
			description= 'Automatic exposure time(mode)'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Automatisierung: Achsposition
			keyword = 'automation_axis_position'
			beschreibung = "Automatisierung: Achsposition"
			unit=None
			description= 'Automation: Axis position'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Automatisierung: Kartesische Position (Ist-Wert)
			keyword = 'automation_cartesian_position_actual'
			beschreibung = "Automatisierung: Kartesische Position (Ist-Wert)"
			unit=None
			description= 'Automation: Actual cartesian position'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Automatisierung: Kartesische Position (Soll-Wert)
			keyword ='automation_cartesian_position' 
			beschreibung = "Automatisierung: Kartesische Position (Soll-Wert)"
			unit=None
			description= 'Automation: Cartesian Position'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Automatisierung: Positionsabweichung (Soll/Ist) kartesisch
			keyword ='automation_cartesian_position_discrepancy'
			beschreibung = "Automatisierung: Positionsabweichung (Soll/Ist) kartesisch"
			unit=None
			description= 'Automation: Cartesian position discrepancy'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Automatisierungsgerät
			keyword ='automation_device'
			beschreibung = "Automatisierungsgerät"
			unit=None
			description= 'Automation device'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
								
			# Benötigte Ausrichtung zur Berechnung 
			keyword ='alignment_at_calculation'
			beschreibung = "Benötigte Ausrichtung zur Berechnung"
			unit=None
			description= 'Allignment at calculation'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Benötigte Starrkörperbewegungskorrektur zur Berechnung 
			keyword = 'rigid_body_motion_compensation_at_calculation'
			beschreibung = "Benötigte Starrkörperbewegungskorrektur zur Berechnung "
			unit=None
			description= 'Required rigid body motion compensation for calculation'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Berechnungsgrundlage
			keyword = 'computation_basis'
			beschreibung = "Berechnungsgrundlage"
			unit=None
			description= 'Computation basis'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Berechnungsinformation
			keyword = 'computation_information'
			beschreibung = "Berechnungsinformation"
			unit=None
			description= 'Computation information'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Berechnungsmodus
			keyword ='computation_mode'
			beschreibung = "Berechnungsmodus"
			unit=None
			description= 'Computation mode'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Beschleunigung des Sensor
			keyword ='sensor_acceleration'
			beschreibung = "Beschleunigung des Sensor"
			unit='mm/s²' # Schreibweise?
			description= 'Acceleration sensor'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Element-Keywords (Liste der Element-Keywords)
			keyword ='element_keywords'
			beschreibung = "Element-Keywords (Liste der Element-Keywords)"
			unit=None
			description= 'element keywords'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Ergebnis der Dekalibrierungskontrolle 
			keyword = 'decalibrated_sensor_check_result'
			beschreibung = "Ergebnis der Dekalibrierungskontrolle "
			unit=None
			description= 'Decalibrated sensor check result'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Importdatei 
			keyword = 'import_file'
			beschreibung = "Importdatei"
			unit=None
			description= 'Import file'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass) 
			
			# Importdateiname
			keyword = 'import_file_name'
			beschreibung = "Importdateiname"
			unit=None
			description= 'Import file name'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Index im Pfad
			keyword = 'index_in_path'
			beschreibung = "Index im Pfad"
			unit=None
			description= 'Index in path'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Kamera-Betriebstemperatur (ATOS IIe Rev.01)
			keyword = 'camera_operating_temperature'
			beschreibung = "Kamera-Betriebstemperatur (ATOS IIe Rev.01)"
			unit=om+"degreeCelsius"
			description= 'Camera operating temperature(ATOS IIe Rev.01/ATOS III Rev.01)'
			uri=ontologynamespace+'operatingTemperature'
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Kamerakennung
			keyword = 'camera_identifiers'
			beschreibung = "Kamerakennung"
			unit=None
			description= 'Camera identifiers'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Kameratyp 
			keyword = 'camera_type'
			beschreibung = "Kameratyp"
			unit=None
			description= 'Camera type'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Kommentar
			keyword = 'comment'
			beschreibung = "Kommentar"
			unit=None
			description= 'Comment'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Lichtfaktor (ATOS IIe Rev.01 / ATOS III Rev.01)
			keyword = 'light_factor'
			beschreibung = "Lichtfaktor (ATOS IIe Rev.01 / ATOS III Rev.01)"
			unit=None
			description= 'Light factor (ATOS IIe Rev.01 / ATOS III Rev.01)'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Lichtintensität (ATOS IIe Rev.01 / ATOS III Rev.01)
			keyword = 'light_intensity'
			beschreibung = "Lichtintensität (ATOS IIe Rev.01 / ATOS III Rev.01)"
			unit=None
			description= 'Light intensity (ATOS IIe Rev.01 / ATOS III Rev.01)'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Max. Blickwinkel Sensor/Fläche
			keyword = 'max_viewing_angle_sensor_surface'
			beschreibung = "Max. Blickwinkel Sensor/Fläche"
			unit=None
			description= 'Max. viewing angle sensor/surface'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Max. Residuum 
			keyword = 'max_residual'
			beschreibung = "Max. Residuum"
			unit=om+"millimetre"
			description= 'Max. residual'
			uri=ontologynamespace+'MaximumResidual'
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Max. Tiefenbegrenzung
			keyword = 'max_depth_limitation'
			beschreibung = "Max. Tiefenbegrenzung"
			unit=None
			description= 'Max depth limitation'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Messauflösung
			keyword = 'measurement_resolution'
			beschreibung = "Messauflösung"
			unit=None
			description= 'Measurement resolution'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Min. Tiefenbegrenzung 
			keyword = 'min_depth_limitation'
			beschreibung = "Min. Tiefenbegrenzung "
			unit=None
			description= 'Min. depth limitation'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Mittlere Einschneideabweichung
			keyword = 'mean_intersection_deviation'
			beschreibung = "Mittlere Einschneideabweichung"
			unit=om+"millimetre"
			description= 'Mean intersection deviation'
			uri=ontologynamespace+'MeanIntersectionDeviation'
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Name(importiert)
			keyword = 'imported_name'
			beschreibung = "Name(importiert)"
			unit=None
			description= 'Imported name'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
				
			# Neigungswinkel des Sensors 
			keyword = 'sensor_tilt_angle'
			beschreibung = "Neigungswinkel des Sensors"
			unit=om+"radian"
			description= 'Sensor tilt angle'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Pfadstatus 
			keyword = 'path_status'
			beschreibung = "Pfadstatus"
			unit=None
			description= 'Path status'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Positionsabweichung (real/virtuell)
			keyword = 'position_discrepancy_real_virtual'
			beschreibung = "Positionsabweichung (real/virtuell)"
			unit=None
			description= 'Position discrepancy (real/virtual)'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Qualität Triple-Scan-Punkte
			keyword = 'quality_triple_scan_points'
			beschreibung = "Qualität Triple-Scan-Punkte"
			unit=None
			description= 'Quality Triple Scan points'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Qualitätskontrolle Triple-Scan-Punkte
			keyword = 'quality_triple_scan_points_mode'
			beschreibung = "Qualitätskontrolle Triple-Scan-Punkte"
			unit=None
			description= 'Quality check Triple Scan points'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Referenzkamerakennung 
			keyword = 'reference_camera_identifiers'
			beschreibung = "Referenzkamerakennung"
			unit=None
			description= 'Reference camera identifiers'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Rotationswinkel des Sensors 
			keyword = 'sensor_rotation_angle'
			beschreibung = "Rotationswinkel des Sensors"
			unit=om+"radian"
			description= 'Sensor rotation angle'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Schwellwert für Qualität der Triple-Scan-Punkte
			keyword = 'quality_triple_scan_points_threshold'
			beschreibung = "Schwellwert für Qualität der Triple-Scan-Punkte"
			unit=None
			description= 'Threshold for quality Triple Scan points'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Schätzwert für die Transformationsstabilität 
			keyword = 'transformation_stability_rating'
			beschreibung = "Schätzwert für die Transformationsstabilität"
			unit=None
			description= 'Transformation stability rating'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)		
			
			# Sekunden seit der letzten Lichtfaktorkalibrierung 
			keyword = 'seconds_since_last_light_factor_calibration'
			beschreibung = "Sekunden seit der letzten Lichtfaktorkalibrierung"
			unit=om+"second-Time"
			description= 'Seconds since last light factor calibration'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Status: Aktuelle Position?
			keyword = 'is_current_position'
			beschreibung = ""
			unit=None
			description= 'State: Is current position?'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Status: Einfluss von Randbereichen bei Polygonisierung reduzieren?
			keyword = 'reduce_influence_of_border_areas'
			beschreibung = "Status: Einfluss von Randbereichen bei Polygonisierung reduzieren?"
			unit=None
			description= 'State: Reduce influence of border areas?'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Status: Grauwert-Features berücksichtigen?
			keyword = 'observe_gray_value_feature'
			beschreibung = "Status: Grauwert-Features berücksichtigen?"
			unit=None
			description= 'State: Observe gray value feature?'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass) 
	
			# Status: Ist Element selektiert?
			keyword = 'is_selected'
			beschreibung = "Status: Ist Element selektiert?"
			unit=None
			description= 'State: Is element selected?'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Status: Ist Element sichtbar?
			keyword = 'is_visible'
			beschreibung = "Status: Ist Element sichtbar?"
			unit=None
			description= 'State: Is element visible'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Status: Ist Kameratemperatur gültig (ATOS IIe Rev.01 / ATOS III Rev.01)?
			keyword = 'is_camera_temperature_valid'
			beschreibung = "Status: Ist Kameratemperatur gültig (ATOS IIe Rev.01 / ATOS III Rev.01)?"
			unit=None
			description= 'State: Is camera temperature valid (ATOS IIe Rev.01 / ATOS III Rev.01)?'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Status: Ist Kameratemperatur ok (ATOS IIe Rev.01 / ATOS III Rev.01)?	
			keyword = 'is_camera_temperature_ok'
			beschreibung = "Status: Ist Kameratemperatur ok (ATOS IIe Rev.01 / ATOS III Rev.01)?"
			unit=None
			description= 'State: Is camera temperature ok (ATOS IIe Rev.01 / ATOS III Rev.01)?'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Status: Ist Lampenaufwärmung gültig (ATOS IIe Rev.01 / ATOS III Rev.01)?
			keyword = 'is_lamp_warmup_valid'
			beschreibung = "Status: Ist Lampenaufwärmung gültig (ATOS IIe Rev.01 / ATOS III Rev.01)?"
			unit=None
			description= 'State: Is lamp warm up valid (ATOS IIe Rev.01 / ATOS III Rev.01)?'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
					
			# Status: Ist Mehrfachaufnahme aktiviert? 
			keyword = 'is_double_snap_enabled'
			beschreibung = "Status: Ist Mehrfachaufnahme aktiviert? "
			unit=None
			description= 'State: Is double snap enabled?'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Status: Ist Sichtbarkeitszustand gesperrt?
			keyword = 'is_visibility_locked'
			beschreibung = "Status: Ist Sichtbarkeitszustand gesperrt?"
			unit=None
			description= 'State: Is visibility locked?'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Status: Ist geringe Genauigkeit für Best-Fit Transformation erlaubt?
			keyword = 'transformation_low_best_fit_accuracy'
			beschreibung = "Status: Ist geringe Genauigkeit für Best-Fit Transformation erlaubt?"
			unit=None
			description= 'State: Is low accuracy for best-fit transformation allowed?'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Status: Ist in Inspektionselement referenziert?  
			keyword = 'is_referenced_in_inspection'
			beschreibung = "Status: Ist in Inspektionselement referenziert?"
			unit=None
			description= 'State: Is referenced in inspection element?'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Status: Lichtfaktorkalibrierung Status (ATOS IIe Rev.01 / ATOS III Rev.01)? 
			keyword = 'is_light_factor_calibrated'
			beschreibung = "Status: Lichtfaktorkalibrierung Status (ATOS IIe Rev.01 / ATOS III Rev.01)?"
			unit=None
			description= 'State: Is light factor calibrated (ATOS IIe Rev.01 / ATOS III Rev.01)?'
			uri=ontologynamespace+'lightFactorCalibrated'
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Status: Name erzeugt?
			keyword = 'is_name_generated'
			beschreibung = "Status: Name erzeugt?"
			unit=None
			description= 'State: Is name generated?'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Status: Punkte an Nutkanten vermeiden?
			keyword = 'avoid_points_on_groove_edges'
			beschreibung = "Status: Punkte an Nutkanten vermeiden?"
			unit=None
			description= 'State: Avoid points on groove edges?'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Status: Punkte an Scan-Bereichsgrenzen vermeiden?
			keyword = 'avoid_points_on_borders_in_scan_area'
			beschreibung = "Status: Punkte an Scan-Bereichsgrenzen vermeiden?"
			unit=None
			description= 'State: Avoid points on borders in scan area?'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Status: Punkte in Schattenbereichen vermeiden? 
			keyword = 'avoid_points_in_shadow_areas'
			beschreibung = "Status: Punkte in Schattenbereichen vermeiden?"
			unit=None
			description= 'State: Avoid points in shadow areas?'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Status: Scan-Bereich definiert? 
			keyword = 'is_scan_area_defined'
			beschreibung = "Status: Scan-Bereich definiert? "
			unit=None
			description= 'State: Is scan area defined?'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Status: Sind Aufnahmeparameter gültig?
			keyword = 'are_acquisition_parameters_valid'
			beschreibung = "Status: Sind Aufnahmeparameter gültig?"
			unit=None
			description= 'State: Are acquisition parameters valid?'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Status: Sind Kamera- und Sensorkennungen gültig?
			keyword = 'are_camera_and_sensor_identifiers_valid'
			beschreibung = "Status: Sind Kamera- und Sensorkennungen gültig?"
			unit=None
			description= 'State: Are camera- and sensor identifiers valid?'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Status: Wird Qualität der Triple-Scan-Punkte geprüft?
			keyword = 'is_quality_triple_scan_points_checked'
			beschreibung = "Status: Wird Qualität der Triple-Scan-Punkte geprüft?"
			unit=None
			description= 'State: Is quality Triple Scan points checked?'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Tags (Liste der Elementtags)
			keyword = 'tags'
			beschreibung = "Tags (Liste der Elementtags)"
			unit=None
			description= 'Tags (List of element tags)'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Temperatur der Hauptplatine (Sensor)
			keyword = 'sensor_main_board_temperature'
			beschreibung = "Temperatur der Hauptplatine (Sensor)"
			unit= om+"degreeCelsius"
			description= 'Main board temperature (Sensor)'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Temperatur der Hauptstromversorgung (Sensor)
			keyword = 'sensor_main_power_supply_temperature'
			beschreibung = "Temperatur der Hauptstromversorgung (Sensor)"
			unit=om+"degreeCelsius"
			description= 'Main power supply temperature (Sensor)'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Temperatur der LED (Sensor)
			keyword = 'sensor_led_temperature'
			beschreibung = "Temperatur der LED (Sensor)"
			unit=om+"degreeCelsius"
			description= 'LED temperature (Sensor)'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Temperatur der LED-Stromversorgung (Sensor)
			keyword = 'sensor_led_power_supply_temperature'
			beschreibung = "Temperatur der LED-Stromversorgung (Sensor)"
			unit=om+"degreeCelsius"
			description= 'LED power supply temperature (Sensor)'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Temperatur der Projektionseinheit (Sensor)
			keyword = 'sensor_projection_unit_temperature'
			beschreibung = "Temperatur der Projektionseinheit (Sensor)"
			unit=om+"degreeCelsius"
			description= 'Projection unit temperature (Sensor)'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Temperatur des Kameraträgers (Sensor)
			keyword = 'sensor_camera_support_temperature'
			beschreibung = "Temperatur des Kameraträgers (Sensor)"
			unit=om+"degreeCelsius"
			description= 'Camera support temperature (Sensor)'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Temperatur des LED-Kühlkörpers (Sensor)
			keyword = 'sensor_led_heatsink_temperature'
			beschreibung = "Temperatur des LED-Kühlkörpers (Sensor)"
			unit=om+"degreeCelsius"
			description= 'LED heatsink temperature (Sensor)'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Tiefenbegrenzungsmodus
			keyword = 'depth_limitation_mode'
			beschreibung = "Tiefenbegrenzungsmodus"
			unit=None
			description= 'Depth limitation mode'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Typ der Projektorkalibrierung
			keyword = 'projector_calibration_type'
			beschreibung = "Typ der Projektorkalibrierung"
			unit=None
			description= 'Projector calibration type'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Umgebungstemperatur
			keyword = 'ambient_temperature'
			beschreibung = "Umgebungstemperatur"
			unit=om+"degreeCelsius"
			description= 'Ambient temperature'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Verbleibende Lampenaufwärmzeit (ATOS IIe Rev.01 / ATOS III Rev.01)
			keyword = 'remaining_lamp_warmup_time'
			beschreibung = "Verbleibende Lampenaufwärmzeit (ATOS IIe Rev.01 / ATOS III Rev.01)"
			unit=om+"second-Time"
			description= 'Remaining lamp warm up time (ATOS IIe Rev.01 / ATOS III Rev.01)'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Wiederholungsgrund 
			keyword = 'reason_for_repetition'
			beschreibung = "Wiederholungsgrund"
			unit=None
			description= 'Reason for repetition'
			uri=None
			measurementclass=None
			infos_m (keyword,beschreibung,unit,description,uri,measurementclass)
			
			
			## properties ## setup ## check 
			# Anzahl der gemeinsamen Referenzpunkte
			keyword = 'number_of_common_reference_points'
			beschreibung = "Anzahl der gemeinsamen Referenzpunkte"
			unit=None
			description= 'Number of common reference points'
			uri=ontologynamespace+'numberOfCommonReferencePoints'
			measurementclass=None
			infos_m_properties (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Aufnahmezeit 
			keyword = 'acquisition_time'
			beschreibung = "Aufnahmezeit"
			unit=None
			description= 'Acquisition time'
			uri=ontologynamespace+'acquisitionTime'
			measurementclass=None
			infos_m_properties (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Maximale Einschneideabweichung
			keyword = 'max_intersection_deviation'
			beschreibung = "Maximale Einschneideabweichung"
			unit=om+"pixel"
			description= 'Max. intersection deviation'
			uri=ontologynamespace+'MaxIntersectionDeviation'
			measurementclass=None
			infos_m_properties (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Messungs-ID (eindeutig über alle Messreihen)
			keyword = 'unique_measurement_id'
			beschreibung = "Messungs-ID (eindeutig über alle Messreihen)"
			unit=None
			description= 'Measurement ID(unique trough all measurement series)'
			uri=ontologynamespace+'measurementId'
			measurementclass=None
			infos_m_properties (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Min. Streifenkontrast
			keyword ='min_fringe_contrast'
			beschreibung = "Min. Streifenkontrast"
			unit='Grauwerte'
			description= 'Min. fringe contrast'
			uri=ontologynamespace+'MinimumFringeContrast'
			measurementclass=None
			infos_m_properties (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# schleife damit alle belichtungszeiten rausgeschrieben werden 
			for i in range(gom.app.project.measurement_series[mr].measurements[m].get ('number_of_exposure_times')):
				
				# Belichtungszeiten
				keyword = 'exposure_times ['+ str(i) +']'
				beschreibung = "Belichtungszeit "+ str(i)
				unit=om+"second-Time"
				description= 'Exposure time'
				uri=exifnamespace+'exposureTime'
				measurementclass=None
				infos_m_setup (keyword,beschreibung,unit,description,uri,measurementclass)
		
				# Anzahl der Punkte pro Belichtungszeit
				keyword = 'points_per_exposure_time ['+ str(i) +']'
				beschreibung = "Anzahl der Punkte für Belichtungszeit "+ str(i)
				unit=None
				description= 'Points per exposure time'
				uri=None
				measurementclass=None
				infos_m_properties (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Bildbreite
			keyword = 'image_width'
			beschreibung = "Bildbreite"
			unit=om+"pixel"
			description= 'Image width'
			uri=exifnamespace+'imageWidth'
			measurementclass=None
			infos_m_setup (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Bildhöhe
			keyword = 'image_height'
			beschreibung = "Bildhöhe"
			unit=om+"pixel"
			description= 'Image height'
			uri=exifnamespace + 'imageHeight'
			measurementclass=None
			infos_m_setup (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Eckenmaskierungsgröße 
			keyword = 'corner_mask_size'
			beschreibung = "Eckenmaskierungsgröße"
			unit=om+"percent"
			description= 'Corner mask size'
			uri=ontologynamespace+'CornerMask'
			measurementclass=None
			infos_m_properties (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# check 
			# Ergebnis der Lichtänderungskontrolle
			keyword = 'lighting_change_check_result'
			beschreibung = "Ergebnis der Lichtänderungskontrolle"
			unit=None
			description= 'Lightning change check result'
			uri=None
			measurementclass=None
			infos_m_check (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Ergebnis der Sensorbewegungskontrolle 
			keyword = 'sensor_movement_check_result'
			beschreibung = "Ergebnis der Sensorbewegungskontrolle "
			unit=None
			description= 'Sensor movement check result'
			uri=ontologynamespace+'sensorMovementCheck'
			measurementclass=None
			infos_m_check (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Lichtänderung (Sigma)
			keyword = 'lighting_change_sigma'
			beschreibung = "Lichtänderung (Sigma)"
			unit='Grauwerte'
			description= 'Light change sigma'
			uri=ontologynamespace+'LightChangeSigma'
			measurementclass=None
			infos_m_check (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Mittlere Lichtänderung
			keyword = 'lighting_change_mean'
			beschreibung = "Mittlere Lichtänderung"
			unit='Grauwerte'
			description= 'Mean lighting change'
			uri=ontologynamespace +'MeanLightingChange'
			measurementclass=None
			infos_m_check (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Name 
			keyword = 'name'
			beschreibung = "Name"
			unit=None
			description= 'Name'
			uri=rdfs+"label"
			measurementclass=None
			infos_m_properties (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Referenzpunktbelichtungszeit 
			keyword = 'reference_point_exposure_time'
			beschreibung = "Referenzpunktbelichtungszeit"
			unit=om+"second-Time"
			description= 'Reference point exposure time'
			uri=ontologynamespace+'ShutterTime'
			measurementclass=None
			infos_m_setup (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Sensorbewegung 
			keyword = 'sensor_movement'
			beschreibung = "Sensorbewegung"
			unit=om+"pixel"
			description= 'Sensor movement'
			uri=ontologynamespace+'SensorMovement'
			measurementclass=None
			infos_m_check (keyword,beschreibung,unit,description,uri,measurementclass)

			# Status: Ist Messung transformiert?
			keyword = 'is_measurement_transformed'
			beschreibung = "Status: Ist Messung transformiert?"
			unit=None
			description= 'State: measurement transformed?'
			uri=None
			measurementclass=None
			infos_m_properties (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Status: Punkte auf Glanzstellen vermeiden 
			keyword ='avoid_points_on_shiny_surfaces'
			beschreibung = "Status: Punkte auf Glanzstellen vermeiden"
			unit=None
			description= 'State: Avoid points on shiny surfaces?'
			uri=None
			measurementclass=None
			infos_m_properties (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Status: Punkte bei starken Helligkeitsunterschieden vermeiden?
			keyword = 'avoid_points_at_strong_brightness_differences'
			beschreibung = "Status: Punkte bei starken Helligkeitsunterschieden vermeiden?"
			unit=None
			description= 'State: Avoid points at strong brightness differences?'
			uri=None
			measurementclass=None
			infos_m_properties (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Status: Reflexionserkennung
			keyword = 'reflection_detection'
			beschreibung = "Status: Reflexionserkennung"
			unit=None
			description= 'State: Reflection detection?'
			uri=ontologynamespace+'reflectionDetectionActivated'
			measurementclass=None
			infos_m_setup (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Status: Sensor-Betriebstemperatur erreicht?
			keyword ='sensor_operation_temperature_reached'
			beschreibung = "Status: Sensor-Betriebstemperatur erreicht?"
			unit=None
			description= 'State: Is sensor operation temperature reached?'
			uri=ontologynamespace+'SensorTemperature'
			measurementclass=None
			infos_m_check (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Status: Triple-Scan-Punkte bei starken Helligkeitsunterschieden vermeiden? 
			keyword = 'avoid_triple_scan_points_at_strong_brightness_differences'
			beschreibung = "Status: Triple-Scan-Punkte bei starken Helligkeitsunterschieden vermeiden?"
			unit=None
			description= 'State: Avoid Triple Scan points at strong brightness differences?'
			uri=ontologynamespace+'avoidTripleScanPointsWithBrightnessDifference'
			measurementclass=None
			infos_m_properties (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Status: Triple-Scan-Punkte vermeiden? 
			keyword = 'avoid_triple_scan_points'
			beschreibung = "Status: Triple-Scan-Punkte vermeiden?"
			unit=None
			description= 'State: Avoid Triple Scan points?'
			uri=ontologynamespace+'avoidTripleScanPoints'
			measurementclass=None
			infos_m_properties (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Transformationsabweichung
			keyword = 'transformation_deviation'
			beschreibung = "Transformationsabweichung"
			unit=om+"millimetre"
			description= 'Transformation deviation'
			uri=ontologynamespace+'TransformationDeviation'
			measurementclass=None
			infos_m_properties (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Transformationsmethode
			keyword = 'transformation_method'
			beschreibung = "Transformationsmethode"
			unit=None
			description= 'Transformation method'
			uri=None
			measurementclass=None
			infos_m_properties (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Transformationsstabilität
			keyword = 'transformation_stability'
			beschreibung = "Transformationsstabilität"
			unit=None
			description= 'Transformation stability'
			uri=None
			measurementclass=None
			infos_m_properties (keyword,beschreibung,unit,description,uri,measurementclass)
				
				
				
			# Sensor 
			# capturing device 
			# Sensorkennung
			keyword = 'sensor_identifier'
			beschreibung = "Sensorkennung"
			unit=None
			description= 'Sensor identifier'
			uri=ontologynamespace +'serialNumber'
			measurementclass='http://www.wikidata.org/entity/Q1198578'
			value = gom.app.project.measurement_series[mr].measurements[m].get (keyword)
			infos_capturing_device (keyword,beschreibung,value,unit,description,uri,measurementclass)
	
			# Sensortyp 
			keyword = 'sensor_type'
			beschreibung = "Sensortyp"
			unit=None
			description= 'Sensor type'
			uri=ontologynamespace+'sensorType'
			measurementclass=None
			value = gom.app.project.measurement_series[mr].measurements[m].get (keyword)
			infos_capturing_device (keyword,beschreibung,value,unit,description,uri,measurementclass)
			
			
			## Messungskalibrierung
			
			# Anzahl der Kameras
			keyword = 'calibration_number_of_cameras'
			beschreibung = "Anzahl der Kameras"
			unit=None
			description= 'Number of cameras'
			uri=ontologynamespace+'numberOfCameras'
			measurementclass=None
			value = gom.app.project.measurement_series[mr].measurements[m].get (keyword)
			infos_capturing_device (keyword,beschreibung,value,unit,description,uri,measurementclass)
	
			# Anzahl der Maßstäbe
			keyword = 'calibration_number_of_scales'
			beschreibung = "Anzahl der Maßstäbe"
			unit=None
			description= 'Number of scales'
			uri=ontologynamespace+'numberOfScales'
			measurementclass=None
			infos_cali_calobject (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Aufnahmemodus
			keyword = 'calibration_snap_mode'
			beschreibung = "Aufnahmemodus"
			unit=None
			description= 'Snap mode'
			uri=None
			measurementclass=None
			infos_cali (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Ausdehnungskoeffizient 
			keyword = 'calibration_object_expansion_coefficient'
			beschreibung = "Ausdehnungskoeffizient"
			unit="x 10-6 K-1"
			description= 'Expansion coefficient'
			uri=ontologynamespace+'ExpansionCoefficient'
			measurementclass=None
			infos_cali_calobject (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Brennweite (Kamera)
			keyword = 'calibration_camera_focal_length'
			beschreibung = "Brennweite (Kamera)"
			unit=om+"millimetre"
			description= 'Focal length camera'
			uri= ontologynamespace + "FocalLengthCamera"
			measurementclass="http://www.wikidata.org/entity/Q193540"
			value = gom.app.project.measurement_series[mr].measurements[m].get (keyword)
			infos_capturing_device (keyword,beschreibung,value,unit,description,uri,measurementclass)
		
			# Brennweite (Projektor)
			keyword = 'calibration_projector_focal_length'
			beschreibung = "Brennweite (Projektor)"
			unit=om+"millimetre"
			description= 'Focal length projector'
			uri=ontologynamespace + "FocalLengthProjector"
			measurementclass="http://www.wikidata.org/entity/Q193540"
			value = gom.app.project.measurement_series[mr].measurements[m].get (keyword)
			infos_capturing_device (keyword,beschreibung,value,unit,description,uri,measurementclass)
		
			# Grenzwert Kalibrierabweichung
			keyword = 'limit_value_calibration_deviation' 
			beschreibung = "Grenzwert Kalibrierabweichung"
			unit=None
			description= 'Limit value calibration deviation'
			uri=None
			measurementclass=None
			infos_cali (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Grenzwert Maßstabsabweichung
			keyword = 'limit_value_calibration_scale_deviation'
			beschreibung = "Grenzwert Maßstabsabweichung"
			unit=None
			description= 'Limit value scale deviation'
			uri=None
			measurementclass=None
			infos_cali (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Grenzwert Projektorkalibrierabweichung
			keyword = 'limit_value_calibration_projector_deviation'
			beschreibung = "Grenzwert Projektorkalibrierabweichung"
			unit=None
			description= 'Limit value projector deviation '
			uri=None
			measurementclass=None
			infos_cali (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Höhenänderung
			keyword = 'calibration_height_variance'
			beschreibung = "Höhenänderung"
			unit=om+"millimetre"
			description= 'height variance'
			uri=ontologynamespace+'HeightVariance'
			measurementclass=None
			infos_cali_calproperties (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Identifizierungspunkt-ID
			keyword = 'calibration_object_identification_point_id'
			beschreibung = "Identifizierungspunkt-ID"
			unit=None
			description= 'Identification point ID'
			uri=None
			measurementclass=None
			infos_cali (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Kalibrierabweichung
			keyword = 'calibration_deviation'
			beschreibung = "Kalibrierabweichung"
			unit=om+"pixel"
			description= 'calibration deviation'
			uri=ontologynamespace+'CalibrationDeviation'
			measurementclass=None
			infos_cali_calproperties (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Kalibrierabweichung (optimiert)
			keyword = 'calibration_deviation_optimized'
			beschreibung = "Kalibrierabweichung (optimiert)"
			unit=om+"pixel"
			description= 'Calibration deviation (optimized)'
			uri=ontologynamespace+ 'CalibrationDeviationOptimized'
			measurementclass=None
			infos_cali_calproperties (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Kalibrierdatum 
			keyword = 'calibration_date'
			beschreibung = "Kalibrierdatum"
			unit=None
			description= 'Calibration date'
			uri= ontologynamespace+'CalibrationDate'
			measurementclass=None
			from_application ="true"		
			infos_cali_calproperties (keyword,beschreibung,unit,description,uri,measurementclass, from_application)
		
			# Kalibrierobjekttyp 
			keyword = 'calibration_object_type'
			beschreibung = "Kalibrierobjekttyp"
			unit=None
			description= 'Calibration object type'
			uri=None
			measurementclass=None
			infos_cali (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Kalibriervolumenbreite
			keyword = 'calibration_volume_width'
			beschreibung = "Kalibriervolumenbreite"
			unit=om+"millimetre"
			description= 'Calibration volume width'
			uri=ontologynamespace+'CalibrationVolumeWidth'
			measurementclass=None
			infos_cali_calproperties (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Kalibriervolumenlänge
			keyword = 'calibration_volume_length'
			beschreibung = "Kalibriervolumenlänge"
			unit=om+"millimetre"
			description= 'Calibration volume length'
			uri=ontologynamespace+'CalibrationVolumeLength'
			measurementclass=None
			infos_cali_calproperties (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Kalibriervolumentiefe
			keyword = 'calibration_volume_depth' 
			beschreibung = "Kalibriervolumentiefe"
			unit=om+"millimetre"
			description= 'Calibration volume depth'
			uri=ontologynamespace+'CalibrationVolumeDepth'
			measurementclass=None
			infos_cali_calproperties (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Kamerawinkel 
			keyword = 'calibration_camera_angle'
			beschreibung = "Kamerawinkel"
			unit=om+"radian"
			description= 'Camera angle'
			uri= ontologynamespace + "CameraAngle"
			measurementclass=None
			infos_cali_calproperties (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Lichtintensität 
			keyword = 'calibration_light_intensity'
			beschreibung = "Lichtintensität"
			unit='om:percent'
			description= 'Light intensity'
			uri=ontologynamespace+'LightIntensity'
			measurementclass=None
			infos_cali_calsetup (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Max. Ellipsenqualität 
			keyword = 'calibration_max_ellipse_quality'
			beschreibung = "Max. Ellipsenqualität"
			unit=None
			description= 'Max. ellipse quality'
			uri=None
			measurementclass=None
			infos_cali (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Max. Tiefenbegrenzung (kalibriert)
			keyword = 'calibration_max_z'
			beschreibung = "Max. Tiefenbegrenzung (kalibriert)"
			unit=None
			description= 'Max. depth limitation (calibrated)'
			uri=None
			measurementclass=None
			infos_cali (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Max. Tiefenbegrenzung (kalibriert, Referenzvolumen)
			keyword = 'calibration_reference_point_max_z'
			beschreibung = "Max. Tiefenbegrenzung (kalibriert, Referenzvolumen)"
			unit=None
			description= 'Max. depth limitation (calibrated, reference volume)'
			uri=None
			measurementclass=None
			infos_cali (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Maßstabsabweichung 
			keyword = 'calibration_scale_deviation'
			beschreibung = "Maßstabsabweichung"
			unit=om+"millimetre"
			description= 'Scale deviation'
			uri=ontologynamespace+'ScaleDeviation'
			measurementclass=None
			infos_cali_calproperties (keyword,beschreibung,unit,description,uri,measurementclass)
				
			# Messtemperatur 
			keyword = 'calibration_measurement_temperature'
			beschreibung = "Messtemperatur"
			unit = om+"degreeCelsius"
			description= 'Measurement temperature'
			uri=ontologynamespace + 'CalibrationTemperature'
			measurementclass=None
			infos_cali_calobject (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Messvolumenbreite
			keyword = 'measuring_volume_width'
			beschreibung = "Messvolumenbreite"
			unit=om+"millimetre"
			description= 'Measuring volume width'
			uri=ontologynamespace+'MeasuringVolumeWidth'
			measurementclass=None
			value = gom.app.project.measurement_series[mr].measurements[m].get (keyword)
			infos_capturing_device (keyword,beschreibung,value,unit,description,uri,measurementclass)
		
			# Messvolumenlänge
			keyword = 'measuring_volume_length'
			beschreibung = "Messvolumenlänge"
			unit =om+"millimetre"
			description= 'Measuring volume length'
			uri=ontologynamespace+'MeasuringVolumeLength'
			measurementclass=None
			value = gom.app.project.measurement_series[mr].measurements[m].get (keyword)
			infos_capturing_device (keyword,beschreibung,value,unit,description,uri,measurementclass)
			
			# theroretischer Messpunktabstand für Atos Triple Scan 8MP
			# MV100, MV170, MV560, MV700, MV1400
			mv_length = gom.app.project.measurement_series[mr].measurements[m].get ('measuring_volume_length')
			if 80 < mv_length < 120:
				value = 0.031
			elif 140 < mv_length <200 :
				value = 0.053
			elif 280 < mv_length < 360:
				value = 0.104
			elif 400 < mv_length < 500:
				value = 0.195
			elif 650 < mv_length < 750:
				value = 0.213
			elif 1200 < mv_length < 1500:
				value = 0.399
			keyword = 'theoretical_measuring_point_distance'
			beschreibung = "Theoretischer Messpunktabstand"
			unit =om+"millimetre"
			description= 'theoretical measuring point distance'
			uri=ontologynamespace+'TheoreticalMeasuringPointDistance'
			measurementclass=None
			from_application= 'derived from the used measuring volume'
			infos_capturing_device (keyword,beschreibung, value, unit,description,uri,measurementclass,from_application)		
	
			# Messvolumentiefe
			keyword = 'measuring_volume_depth'
			beschreibung = "Messvolumentiefe"
			unit =om+"millimetre"
			description= 'Measuring volume depth'
			uri=ontologynamespace+'MeasuringVolumeDepth'
			measurementclass=None
			value = gom.app.project.measurement_series[mr].measurements[m].get (keyword)
			infos_capturing_device (keyword,beschreibung,value,unit,description,uri,measurementclass)
	
			# Min. Tiefenbegrenzung (kalibriert) 
			keyword = 'calibration_min_z'
			beschreibung = "Min. Tiefenbegrenzung (kalibriert)"
			unit=None
			description= 'Min. depth limitation (calibrated)'
			uri=None
			measurementclass=None
			infos_cali (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Min. Tiefenbegrenzung (kalibriert, Referenzvolumen)
			keyword = 'calibration_reference_point_min_z'
			beschreibung = "Min. Tiefenbegrenzung (kalibriert, Referenzvolumen)"
			unit=None
			description= 'Min. depth limitation (calibrated, reference volume)'
			uri=None
			measurementclass=None
			infos_cali (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Name des Kalibrierobjekts 
			keyword = 'calibration_object_name'
			beschreibung = "Name des Kalibrierobjekts"
			unit=None
			description= 'Calibration object name'
			uri=rdfs+ 'label'
			measurementclass=None
			infos_cali_calobject (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Projektorkalibrierabweichung 
			keyword = 'calibration_projector_deviation'
			beschreibung = "Projektorkalibrierabweichung"
			unit='om:pixel'
			description= 'Projector calibration deviation'
			uri=ontologynamespace + 'ProjectorDeviation'
			measurementclass=None
			infos_cali_calproperties (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Projektorkalibrierabweichung (optimiert)
			keyword = 'calibration_projector_deviation_optimized'
			beschreibung = "Projektorkalibrierabweichung (optimiert)"
			unit='om:pixel'
			description= 'Projector calibration deviation (optimized)'
			uri=None
			#uri=ontologynamespace + 'ProjectorDeviationOptimized'
			measurementclass=None
			infos_cali_calproperties (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Referenzvolumenbreite
			keyword = 'reference_volume_width'
			beschreibung = "Referenzvolumenbreite"
			unit=om+"millimetre"
			description= 'Reference volume width'
			uri=None
			#uri=ontologynamespace+'ReferenceVolumeWidth'
			measurementclass=None
			infos_cali (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Referenzvolumenhöhe
			keyword = 'reference_volume_length'
			beschreibung = "Referenzvolumenhöhe"
			unit=om+"millimetre"
			description= 'Reference volume length'
			uri=None
			#uri=ontologynamespace+'ReferenceVolumeLength'
			measurementclass=None
			infos_cali (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Referenzvolumentiefe
			keyword = 'reference_volume_depth'
			beschreibung = "Referenzvolumentiefe"
			unit=om+"millimetre"
			description= 'Reference volume depth'
			uri=None
			measurementclass=None
			infos_cali (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Schwellwert für Bewegungskontrolle 
			keyword = 'calibration_movement_check_threshold'
			beschreibung = "Schwellwert für Bewegungskontrolle"
			unit=None
			description= 'Threshold for movement check'
			uri=None
			measurementclass=None
			infos_cali (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Status: Ist Sensor mit Retro-Kalibrierung kalibriert?
			keyword = 'sensor_is_retro_calibrated'
			beschreibung = "Status: Ist Sensor mit Retro-Kalibrierung kalibriert?"
			unit=None
			description= 'State: Sensor is with retro calibrated?'
			uri=None
			measurementclass=None
			infos_cali (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Status: Ist Sensor mit Schnellkalibrierung kalibriert?
			keyword = 'calibration_is_quick_calibrated'
			beschreibung = "Status: Ist Sensor mit Schnellkalibrierung kalibriert?"
			unit=None
			description= 'State: Sensor is quick calibrated?'
			uri=ontologynamespace+'isQuickCalibrated'
			measurementclass=None
			infos_cali_calproperties (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Status: Ist Sensoreinstellung gültig? 
			keyword = 'calibration_is_sensor_setup_valid'
			beschreibung = "Status: Ist Sensoreinstellung gültig?"
			unit=None
			description= 'State: Is sensor setup valid?'
			uri=ontologynamespace+'sensorSetupValid'
			measurementclass=None
			value = gom.app.project.measurement_series[mr].measurements[m].get (keyword)
			infos_capturing_device (keyword,beschreibung,value,unit,description,uri,measurementclass)
	
			# Status: Kalibrierobjekt rezertifiziert? 
			keyword = 'calibration_object_recertified'
			beschreibung = "Status: Kalibrierobjekt rezertifiziert?"
			unit=None
			description= 'State: Calibration object recertified?'
			uri=None
			measurementclass=None
			infos_cali (keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Status: Überbelichtungsprüfung ignoriert?
			keyword = 'calibration_is_overexposure_check_ignored'
			beschreibung = "Status: Überbelichtungsprüfung ignoriert?"
			unit=None
			description= 'State: Is overexposure check ignored?'
			uri=None
			measurementclass=None
			infos_cali (keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Verbleibende Sensor-Aufwärmzeit 
			keyword = 'calibration_remaining_sensor_warmup_time'
			beschreibung = "Verbleibende Sensor-Aufwärmzeit"
			unit='om:minute-Time'
			description= 'Remaining sensor warm up time'
			uri=ontologynamespace+'RemainingSensorWarmupTime'
			measurementclass=None
			infos_cali_calsetup (keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Zertifizierungstemperatur
			keyword = 'calibration_object_certification_temperature'
			beschreibung = "Zertifizierungstemperatur"
			unit=om+"degreeCelsius"
			description= 'Certification temperature'
			uri=ontologynamespace+'ReferenceTemperature'
			measurementclass=None
			infos_cali_calobject (keyword,beschreibung,unit,description,uri,measurementclass)
			
	
			dir_mea = {}	
			#dir_mea["measurement_information"] = messung			
			if len(list_rp_local)>0:			
				dir_mea["referencepoints"] =list_rp_local
			dir_mea["measurement_setup"]=dic_measurement_setup
			dir_mea["measurement_check"]=dic_measurement_check
			dir_mea["measurement_properties"]=dic_measurement_info 
			dic_sensor["calibration"]=calibration
			dic_sensor["capturing_device"]=dic_measurement_sensor
			
			if len(dir_mea)>0:
				list_messungen.append(dir_mea)
			if len(list_messungen) >0:
				messreihe["measurements"]=list_messungen
			if len(dic_measurement_cal_calobject) >0:
				calibration["cal_object"]=dic_measurement_cal_calobject
			if len(dic_measurement_cal_calsetup)>0:
				calibration["cal_setup"]=dic_measurement_cal_calsetup
			if len(dic_measurement_cal_calresults) >0:
				calibration["cal_properties"]=dic_measurement_cal_calresults
			

			# temporäre Vergleichsliste mit allen Kalibrierzeiten anlegen und wenn noch nicht in Liste "temp_list_cal_time", dann rein einen "sensor" anlegen
			
			if "calibration_date" in dic_measurement_cal_calresults:
				cal_time_new = dic_measurement_cal_calresults["calibration_date"]["value"]
			else:
				cal_time_new = None
				
			if cal_time_new in temp_list_cal_time:
				for s in list_sensors:
					if "cal_properties" in s["calibration"]:
						if "calibration_date" in s["calibration"]["cal_properties"]:
							if "value" in s["calibration"]["cal_properties"]["calibration_date"]:
								cal_time_store = s["calibration"]["cal_properties"]["calibration_date"]["value"]
								if cal_time_store == cal_time_new:
									dic_measurement_info["sensor_id"] = s["capturing_device"]["sensor_id"]
								
			if not cal_time_new in temp_list_cal_time:
				temp_list_cal_time.append(cal_time_new)
				
				dic_s ={}
				dic_s["value"] = sensor_id
				dic_s["key_deu"] = "Sensor ID"
				dic_s["from_application"] = "false"
				dic_s["key_eng"] = "sensor ID"
				dic_s["uri"] = ontologynamespace + "sensor_id"
				dic_s["value_type"] = type(dic_s["value"]).__name__
				dic_sensor["capturing_device"]["sensor_id"] = dic_s
				
				dic_measurement_info["sensor_id"] = dic_s
				
				sensor_id = + 1 
				
				list_sensors.append(dic_sensor)
		
			m=m+1
		
	
		# Referenzpunkte (in Schleife Messreihe)	
		# hier gibt es allgemeneine Informationen, die für alle Refernzpunkte dieser Messreihe gelten 
		
		list_refpoints =[]
		refpoints={}
		refpoints_information={}
		
		try:
			rp = gom.app.project.measurement_series[mr].results['points'].get ('num_points')
		except: 
			rp = None		

		if rp is not None:
			def refpoints_mr (keyword, beschreibung, unit=None, description=None,  uri=None, measurementclass=None, from_application="true"):
				dir = {}
				dir["value"] = gom.app.project.measurement_series[mr].results['points'].get(keyword)
				dir["key_deu"] = beschreibung
				if  description != None:
					dir["key_eng"] =  description
				if  uri != None:
					dir["uri"] =  uri
				if  unit != None:
					dir["unit"] =  unit
				if  measurementclass != None:
					dir["measurementclass"] =  measurementclass
				dir["value_type"] = type(gom.app.project.measurement_series[mr].results['points'].get(keyword)).__name__
				dir["from_application"]= from_application				
				
				if dir["value"] != None:
					if len(str(dir["value"])) != 0:
						if includeonlypropswithuri and "uri" in dir:
							refpoints_information[keyword] = {}		
							refpoints_information[keyword] = dir
						if not includeonlypropswithuri:			
							refpoints_information[keyword] = {}		
							refpoints_information[keyword] = dir			
				
				
			# Anzahl der Punkte
			keyword='num_points' 
			beschreibung="Anzahl der Punkte"
			unit=None
			description= 'Number of points'
			uri=ontologynamespace+'totalNumberOfVertices'
			measurementclass=None
			refpoints_mr(keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Benötigte Ausrichtung zur Berechnung
			keyword='alignment_at_calculation'
			beschreibung="Benötigte Ausrichtung zur Berechnung"
			unit=None
			description= 'Allignment at calculation'
			uri=None
			measurementclass=None
			refpoints_mr(keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Benötigte Starrkörperbewegungskorrektur zur Berechnung
			keyword='rigid_body_motion_compensation_at_calculation'
			beschreibung="Benötigte Starrkörperbewegungskorrektur zur Berechnung"
			unit=None
			description= 'Rigid body motion compensation at calculation'
			uri=None
			measurementclass=None
			refpoints_mr(keyword,beschreibung,unit,description,uri,measurementclass)
	
			# Berechnungsinformationen
			keyword='computation_information'
			beschreibung="Berechnungsinformationen"
			unit=None
			description= 'Computation information'
			uri=None
			measurementclass=None
			refpoints_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
			# Name
			keyword='name'
			beschreibung="Name"
			unit=None
			description= 'Name'
			uri=None
			measurementclass=None
			refpoints_mr(keyword,beschreibung,unit,description,uri,measurementclass)
			
			# Name(importiert) 
			keyword='imported_name'
			beschreibung="Name(importiert)"
			unit=None
			description= 'Name (imported)'
			uri=None
			measurementclass=None
			refpoints_mr(keyword,beschreibung,unit,description,uri,measurementclass)
			
		
			# neue Schleife innerhalb der globalen Referenzpunkten 
			# hier gibt es Informationen, die nur für einen bestimmten Referenzpunkt gelten 
			
			p= 0 
			list_rp_individual= []
			
			while p < gom.app.project.measurement_series[mr].results['points'].get ('num_points'):
					
				refpoints_individual ={}
				def individual_refpoints_mr (keyword, beschreibung, unit=None, description=None, uri=None,measurementclass=None, from_application="true"):
					dir = {}
					dir["value"] = gom.app.project.measurement_series[mr].results['points'].get(keyword+"["+str(p)+"]")
					dir["key_deu"] = beschreibung
					if  description != None:
						dir["key_eng"] =  description
					if  uri != None:
						dir["uri"] =  uri
					if  unit != None:
						dir["unit"] =  unit
					if  measurementclass != None:
						dir["measurementclass"] =  measurementclass
					dir["value_type"] = type(gom.app.project.measurement_series[mr].results['points'].get(keyword+"["+str(p)+"]")).__name__
					dir["from_application"]=from_application
						
					if dir["value"] != None:
						if len(str(dir["value"])) != 0:
							if includeonlypropswithuri and "uri" in dir:
								refpoints_individual[keyword] = {}		
								refpoints_individual[keyword] = dir
							if not includeonlypropswithuri:			
								refpoints_individual[keyword] = {}		
								refpoints_individual[keyword] = dir			
				
		
				# Beobachtungswinkel 
				keyword='observation_angle'
				beschreibung="Beobachtungswinkel"
				unit=om+"radian"
				description= 'Observation angle'
				uri=None
				measurementclass=None
				individual_refpoints_mr(keyword,beschreibung,unit,description,uri,measurementclass)
				
				# Anzahl der Beobachtugen 
				keyword='number_of_observations'			
				beschreibung='Anzahl der Beobachtugen'
				unit=None
				description= 'Number of observations'
				uri=None
				measurementclass=None
				individual_refpoints_mr(keyword,beschreibung,unit,description,uri,measurementclass)
				
				# Punkt-ID 
				keyword='point_id'
				beschreibung= "Punkt-ID"
				unit=None
				description= 'Point ID'
				uri=ontologynamespace+ 'PointID'
				measurementclass=None
				individual_refpoints_mr(keyword,beschreibung,unit,description,uri,measurementclass)
				
				# Punkt-Materialstärke
				keyword= 'point_thickness'
				beschreibung= "Punkt-Materialstärke"
				unit=om+"millimetre"
				description= 'Point thickness'
				uri=ontologynamespace+'PointThickness'
				measurementclass=None
				individual_refpoints_mr(keyword,beschreibung,unit,description,uri,measurementclass)
				
				# Punkttyp 
				keyword='point_type'
				beschreibung= "Punkttyp"
				unit=None
				description= 'Point type'
				uri=None
				measurementclass=None
				individual_refpoints_mr(keyword,beschreibung,unit,description,uri,measurementclass)
					
				# Durchmesser
				keyword='diameter'
				beschreibung= "Durchmesser"
				unit=om+"millimetre"
				description= 'Diameter'
				uri=ontologynamespace+'diameter'
				measurementclass=None
				individual_refpoints_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
				# Koordinate X
				keyword='coordinate.x'
				beschreibung= "Koordinate X"
				unit='om:millimetre'
				description= 'Coordinate X'
				uri=ontologynamespace+'xCoordinate'
				measurementclass=None
				individual_refpoints_mr(keyword,beschreibung,unit,description,uri,measurementclass)
	
				# Koordinate Y
				keyword='coordinate.y'
				beschreibung= "Koordinate Y"
				unit='om:millimetre'
				description= 'Coordinate Y'
				uri=ontologynamespace+'yCoordinate'
				measurementclass=None
				individual_refpoints_mr(keyword,beschreibung,unit,description,uri,measurementclass)
			
				# Koordinate Z
				keyword='coordinate.z'
				beschreibung= "Koordinate Z"
				unit='om:millimetre'
				description= 'Coordinate Z'
				uri=ontologynamespace+'zCoordinate'
				measurementclass=None
				individual_refpoints_mr(keyword,beschreibung,unit,description,uri,measurementclass)
				
				# Normale X
				keyword='normal.x'
				beschreibung= "Normale X"
				unit='om:millimetre'
				description= 'Normal X'
				uri=None
				measurementclass=None
				individual_refpoints_mr(keyword,beschreibung,unit,description,uri,measurementclass)
		
				# Normale Y
				keyword='normal.y'
				beschreibung= "Normale Y"
				unit='om:millimetre'
				description= 'Normal Y'
				uri=None
				measurementclass=None
				individual_refpoints_mr(keyword,beschreibung,unit,description,uri,measurementclass)
				
				# Normale Z
				keyword='normal.z'
				beschreibung= "Normale Z"
				unit='om:millimetre'
				description= 'Normale Z'
				uri=None
				measurementclass=None
				individual_refpoints_mr(keyword,beschreibung,unit,description,uri,measurementclass)
			
				# Residuum 
				keyword= 'residual'
				beschreibung= "Residuum"
				unit='om:millimetre'
				description= 'Residual'
				uri=None
				measurementclass=None
				individual_refpoints_mr(keyword,beschreibung,unit,description,uri,measurementclass)
			
				# Status: Benutzerdefinierte Referenzpunktgröße benutzt? 
				keyword='use_user_defined_reference_point_size'
				beschreibung= "Status: Benutzerdefinierte Referenzpunktgröße benutzt?"
				unit=None
				description= 'State: Use User-defined reference point size?'
				uri=None
				measurementclass=None
				individual_refpoints_mr(keyword,beschreibung,unit,description,uri,measurementclass)
			
				
				if len(refpoints_individual) > 0:
					list_rp_individual.append(refpoints_individual)
				if len(list_rp_individual) > 0:
					refpoints["referencepoints"]= list_rp_individual
	
				p = p+1
			
			if len(refpoints_information)>0:	
				refpoints["global_referencepoints_information"]= refpoints_information
			if len(refpoints) >0:
				messreihe["global_referencepoints"]= refpoints
					
		if len(messreihe_infos)>0:
			messreihe["measurement_series_information"]=messreihe_infos
		if len(list_sensors)>0:
			messreihe["sensors"]=list_sensors	
		if len(messreihe) > 0: 
			list_messreihen.append(messreihe) 

			
		mr = mr +1 
		
	# Netze 		
			
	list_meshes = []
	n = 0
	anz_n = 0 
	netz_name=[]
	for e in gom.app.project.actual_elements:
		etype = e.get ('icon (type)')
		if etype == "mesh":
			anz_n=anz_n+1
			netz_name.append(e.get ('name'))
			
	list_meshes = []
	
	while n < anz_n:
		
		dic_mesh = {}	
		dic_mesh_info = {}
		dic_mesh_processing={}
		list_mesh_processing=[]
		dic_mesh_processing_poly_setup={}
		dic_mesh_processing_poly_post={}
		list_mesh_processing_poly_post=[]

		#mesh information		
		def infos_n (keyword, beschreibung, unit=None, description=None, uri=None, measurementclass=None, value=None, from_application="true"):
			dir = {}
			if value == None:
				value = gom.app.project.actual_elements[netz_name[n]].get (keyword)
			dir["value"] = value 			
			dir["key_deu"] = beschreibung
			if  description != None:
				dir["key_eng"] =  description
			if  uri != None:
				dir["uri"] =  uri
			if  unit != None:
				dir["unit"] =  unit
			if  measurementclass != None:
				dir["measurementclass"] =  measurementclass
			dir["value_type"] = type(value).__name__
			dir["from_application"]= from_application		
			
			if dir["value"] != None:
				if len(str(dir["value"])) != 0:
					if includeonlypropswithuri and "uri" in dir:
						dic_mesh_info[keyword] = {}		
						dic_mesh_info[keyword] = dir
					if not includeonlypropswithuri:			
						dic_mesh_info[keyword] = {}		
						dic_mesh_info[keyword] = dir	
						
			
		#Anzahl der Dreiecke
		keyword= 'num_triangles'
		beschreibung= 'Anzahl der Dreiecke'
		unit=None
		description= 'Number of triangles'
		uri=giganamespace+'TotalNumberOfFaces'
		measurementclass=None
		infos_n(keyword,beschreibung,unit,description,uri,measurementclass)
	
		# Anzahl der Löcher 
		keyword= 'number_of_holes'
		beschreibung= 'Anzahl der Löcher'
		unit=None
		description= 'Number of holes'
		uri=ontologynamespace+'numberOfHoles'
		measurementclass=None
		infos_n(keyword,beschreibung,unit,description,uri,measurementclass)
	
		# Anzahl der Punkte
		keyword= 'num_points'
		beschreibung= 'Anzahl der Punkte'
		unit=None
		description= 'Number of points'
		uri=giganamespace+'TotalNumberOfVertices'
		measurementclass=None
		infos_n(keyword,beschreibung,unit,description,uri,measurementclass)
	
		# Fläche 
		keyword= 'area'
		beschreibung= 'Fläche'
		unit= om+"squareMillimetre"
		description= 'Area'
		uri=giganamespace+'TotalArea'
		measurementclass=None
		infos_n(keyword,beschreibung,unit,description,uri,measurementclass)
	
		# Name 
		keyword= 'name'
		beschreibung= 'Name'
		unit=None
		description= 'Name'
		uri=rdfs+'label'
		measurementclass=None
		infos_n(keyword,beschreibung,unit,description,uri,measurementclass)
	
		# Volumen 
		keyword= 'volume'
		beschreibung= 'Volumen'
		unit = 'om:cubicMillimetre' 
		description= 'Volume'
		uri=ontologynamespace+'volume'
		measurementclass=None
		infos_n(keyword,beschreibung,unit,description,uri,measurementclass)
	
		# Kommentar
		keyword= 'comment'
		beschreibung= 'Kommentar'
		unit=None
		description= 'Comment'
		uri=None
		measurementclass=None
		infos_n(keyword,beschreibung,unit,description,uri,measurementclass)
	
		# Minimum X
		keyword= 'bounding_box.min.x'
		beschreibung= 'Minimum X'
		unit=om+"millimetre"
		description= 'Minimum X'
		uri=giganamespace+'MinimumXCoordinate'
		measurementclass=None
		infos_n(keyword,beschreibung,unit,description,uri,measurementclass)
	
		# Minimum Y
		keyword= 'bounding_box.min.y'
		beschreibung= 'Minimum Y'
		unit=om+"millimetre"
		description= 'Minimum Y'
		uri=giganamespace+'MinimumYCoordinate'
		measurementclass=None
		infos_n(keyword,beschreibung,unit,description,uri,measurementclass)
	
		# Minimun Z
		keyword= 'bounding_box.min.z'
		beschreibung= 'Minimun Z'
		unit=om+"millimetre"
		description= 'Minimum Z'
		uri=giganamespace+'MinimumZCoordinate'
		measurementclass=None
		infos_n(keyword,beschreibung,unit,description,uri,measurementclass)
	
		# Maximum X
		keyword= 'bounding_box.max.x'
		beschreibung= 'Maximum X'
		unit=om+"millimetre"
		description= 'Maximum X'
		uri=giganamespace+'MaximumXCoordinate'
		measurementclass=None
		infos_n(keyword,beschreibung,unit,description,uri,measurementclass)
	
		# Maximum Y
		keyword= 'bounding_box.max.y'
		beschreibung= 'Maximum Y'
		unit=om+"millimetre"
		description= 'Maximum Y'
		uri=giganamespace+'maximumYCoordinate'
		measurementclass=None
		infos_n(keyword,beschreibung,unit,description,uri,measurementclass)
	
		# Maximum Z
		keyword= 'bounding_box.max.z'
		beschreibung= 'Maximum Z'
		unit=om+"millimetre"
		description= 'Maximum Z'
		uri=giganamespace+'maximumZCoordinate'
		measurementclass=None
		infos_n(keyword,beschreibung,unit,description,uri,measurementclass)
		
		# berechneter Wert 
		# durchschnittliche Auflösung pro mm²
		keyword= 'average resolution'
		beschreibung= 'durchschnittliche Auflösung'
		unit = '1/mm²'
		description= 'average resolution'
		uri=None
		measurementclass=None
		from_application= "script-based calculation"
		anz_punkte_netz= gom.app.project.actual_elements[netz_name[n]].get ('num_points')
		flaeche_netz= gom.app.project.actual_elements[netz_name[n]].get ('area')
		value = anz_punkte_netz / flaeche_netz
		infos_n(keyword,beschreibung,unit,description,uri,measurementclass, value,from_application)
		
		# berechneter Wert
		# durchschnittlicher Punktabstand 
		keyword= 'average_point_distance'
		beschreibung= 'durchschnittlicher Punktabstand'
		unit=om+"millimetre"
		description= 'average point distance'
		uri=ontologynamespace +'AveragePointDistance'
		measurementclass=None
		from_application= "script-based calculation"
		value = 1/math.sqrt(anz_punkte_netz / flaeche_netz)
		infos_n(keyword,beschreibung,unit,description,uri,measurementclass, value, from_application)
		
		
		# processing 	
		def infos_poly_processname (keyword, value):
			dir = {}
			dir["value"] = value 			
			dir["value_type"] = type(value).__name__
			dic_mesh_processing[keyword] = dir
				
						
		def infos_poly_setup (keyword, beschreibung, unit=None, description=None, uri=None, measurementclass=None, value=None, from_application="true"):
			dir = {}
			
			if value == None:
				dir["value"] = gom.app.project.actual_elements[netz_name[n]].get (keyword)
			else:
				dir["value"] = value 			
			dir["key_deu"] = beschreibung
			if  description != None:
				dir["key_eng"] =  description
			if  uri != None:
				dir["uri"] =  uri
			if  unit != None:
				dir["unit"] =  unit
			if  measurementclass != None:
				dir["measurementclass"] =  measurementclass
			dir["value_type"] = type(value).__name__
			dir["from_application"]= from_application
				
			if dir["value"] != None:
				if len(str(dir["value"])) != 0:
					if includeonlypropswithuri and "uri" in dir:
						dic_mesh_processing_poly_setup[keyword] = {}		
						dic_mesh_processing_poly_setup[keyword] = dir
					if not includeonlypropswithuri:			
						dic_mesh_processing_poly_setup[keyword] = {}		
						dic_mesh_processing_poly_setup[keyword] = dir
		
		
		def infos_poly_post_smooth (keyword, beschreibung, unit=None, description=None, uri=None, measurementclass=None, value=None, from_application="true"):
			dir = {}
			if keyword == "automatic" or keyword == "processname":
				dir["value"]=value
				dir["value_type"] = type(value).__name__
				if keyword == "automatic":
					dir["from_application"]= from_application
			else:
				if value == None:
					dir["value"] = gom.app.project.actual_elements[netz_name[n]].get (keyword)
				else:
					dir["value"] = value 			
				dir["key_deu"] = beschreibung
				if  description != None:
					dir["key_eng"] =  description
				if  uri != None:
					dir["uri"] =  uri
				if  unit != None:
					dir["unit"] =  unit
				if  measurementclass != None:
					dir["measurementclass"] =  measurementclass
				dir["value_type"] = type(value).__name__
				dir["from_application"]= from_application
				
			if dir["value"] != None:
				if len(str(dir["value"])) != 0:
					if includeonlypropswithuri and "uri" in dir:
						dic_smooth[keyword] = {}		
						dic_smooth[keyword] = dir
					if not includeonlypropswithuri:			
						dic_smooth[keyword] = {}		
						dic_smooth[keyword] = dir
						
						
		def infos_poly_post_thin (keyword, beschreibung, unit=None, description=None, uri=None, measurementclass=None, value=None, from_application="true"):
			dir = {}
			if keyword == "automatic" or keyword == "processname":
				dir["value"]=value
				dir["value_type"] = type(value).__name__
				if keyword == "automatic":
					dir["from_application"]= from_application
			else:
				if value == None:
					dir["value"] = gom.app.project.actual_elements[netz_name[n]].get (keyword)
				else:
					dir["value"] = value 			
				dir["key_deu"] = beschreibung
				if  description != None:
					dir["key_eng"] =  description
				if  uri != None:
					dir["uri"] =  uri
				if  unit != None:
					dir["unit"] =  unit
				if  measurementclass != None:
					dir["measurementclass"] =  measurementclass
				dir["value_type"] = type(value).__name__
				dir["from_application"]= from_application
			
			if dir["value"] != None:
				if len(str(dir["value"])) != 0:
					if includeonlypropswithuri and "uri" in dir:
						dic_thin[keyword] = {}		
						dic_thin[keyword] = dir
					if not includeonlypropswithuri:			
						dic_thin[keyword] = {}		
						dic_thin[keyword] = dir

		# Kommentar aufdröseln
		mesh_comment = gom.app.project.actual_elements[netz_name[n]].get ('comment')
		for k in mesh_comment.split("\n\n"):
			if "POLYGONISATION:" in k:
				
				# processname 
				keyword= 'processname'
				value='polygonisation'
				infos_poly_processname(keyword,value)
				
				for poly in k.replace("BASIC POLYGONISATION:\n","").split("\n"):
					liste = poly.replace("mm","").split(" = ")
	
					if len(liste) == 2:			
						# Basic Polygonisation
						## Setup 
		
						if liste[0] == "creation tolerance":
						###creation tolerance 
							keyword= 'creation tolerance'
							beschreibung= 'Erstellungstoleranz'
							unit=om+"millimetre"
							description= 'creation tolerance'
							uri=ontologynamespace + 'CreationTolerance'
							measurementclass=None
							value=float(liste[1])
							from_application="True, part value from keyword='comment'"
							infos_poly_setup(keyword,beschreibung,unit,description,uri,measurementclass, value, from_application)	
							
						elif liste[0] == "merge tolerance":
						# merge tolerance
							keyword= 'merge tolerance'
							beschreibung= 'Merge-Toleranz'
							unit=om+"millimetre"
							description= 'merge tolerance'
							uri=ontologynamespace + 'MergeTolerance'
							measurementclass=None
							value=float(liste[1])
							from_application="True, part value from keyword='comment'"
							infos_poly_setup(keyword,beschreibung,unit,description,uri,measurementclass, value, from_application)	
							
						elif liste[0] == "maximum gap":
						# maximum gap
							keyword= 'maximum gap'
							beschreibung= 'Maximaler Abstand'
							unit=om+"millimetre"
							description= 'maximum gap'
							uri=ontologynamespace + 'MaximumGap'
							measurementclass=None
							value=float(liste[1])
							from_application="True, part value from keyword='comment'"
							infos_poly_setup(keyword,beschreibung,unit,description,uri,measurementclass, value, from_application)
							
						elif liste[0] == "maximum edge length":
						# maximum edge length
							keyword= 'maximum edge length'
							beschreibung= 'Maximale Kantenlänge'
							unit=om+"millimetre"
							description= 'maximum edge length'
							uri=ontologynamespace + 'MaximumEdgeLength'
							measurementclass=None
							value=float(liste[1])
							from_application="True, part value from keyword='comment'"
							infos_poly_setup(keyword,beschreibung,unit,description,uri,measurementclass, value, from_application)

						elif liste[0] == "unit edge length":
						# unit edge length 
							keyword= 'unit edge length'
							beschreibung= 'Einheitliche Kantenlänge'
							unit=om+"millimetre"
							description= 'unit edge length'
							uri=ontologynamespace + 'UnitEdgeLength'
							measurementclass=None
							value=float(liste[1])
							from_application="True, part value from keyword='comment'"
							infos_poly_setup(keyword,beschreibung,unit,description,uri,measurementclass, value, from_application)

			if "'Polygonize large data volumes' is ON" in k:
				# lage data volume
				keyword= 'Polygonize large data volumes'
				beschreibung= 'Poligonisieren großer Datenmengen'
				unit=None
				description= 'Polygonize large data volumes'
				uri=ontologynamespace + 'polygonizeLargeDataVolumes'
				measurementclass=None
				value=True
				from_application="True, part value from keyword='comment'"
				infos_poly_setup(keyword,beschreibung,unit,description,uri,measurementclass, value, from_application)
			
			# Postprocessing
					
			if "POSTPROCESSING:" in k:
				for post in k.replace("POSTPROCESSING:\n","").split("\n"):
					post=post.replace("mm","").replace(")","")	
					liste2 = post.split("(")
					if len(liste2)== 2:
						pp_title = liste2[0]
						pp_values= liste2[1]
					# smooth	
						if "smooth" in pp_title:
							dic_smooth = {}
							smooth_items = pp_values.replace(" ","").split(",")
							smooth_item_size = smooth_items[0].split("=")
							smooth_item_mode = smooth_items[1].split("=")
							smooth_item_tolerance = smooth_items[2].split("=")
							smooth_size = smooth_item_size[0]
							smooth_size_value = smooth_item_size[1]
							smooth_mode = smooth_item_mode[0]
							smooth_mode_value = smooth_item_mode[1]
							smooth_tolerance = smooth_item_tolerance[0]
							smooth_tolerance_value = smooth_item_tolerance[1]
	
							#smooth
							##processname
							keyword='processname'
							beschreibung= None
							unit=None
							description= None
							uri=None
							measurementclass=None
							value=pp_title
							from_application=None
							infos_poly_post_smooth(keyword,beschreibung,unit,description,uri,measurementclass, value, from_application)
			
							##automatic
							keyword='automatic'
							beschreibung= None
							unit=None
							description= None
							uri=None
							measurementclass=None
							value=True
							from_application=False
							infos_poly_post_smooth(keyword,beschreibung,unit,description,uri,measurementclass, value, from_application)
							
							##size
							keyword= 'size'
							beschreibung= 'Größe'
							unit=None
							description= 'size'
							uri=ontologynamespace + 'size'
							measurementclass=None
							value=int(smooth_size_value)
							from_application="True, part value from keyword='comment'"
							infos_poly_post_smooth(keyword,beschreibung,unit,description,uri,measurementclass, value, from_application)
							
							##mode
							keyword= 'mode'
							beschreibung= 'Modus'
							unit=None
							description= 'mode'
							uri=ontologynamespace + 'mode'
							measurementclass=None
							value=int(smooth_mode_value)
							from_application="True, part value from keyword='comment'"
							infos_poly_post_smooth(keyword,beschreibung,unit,description,uri,measurementclass, value, from_application)
							
							##tolerance
							keyword= 'tolerance'
							beschreibung= 'Toleranz'
							unit=om+"millimetre"
							description= 'tolerance'
							uri=ontologynamespace + 'Tolerance'
							measurementclass=None
							value=float(smooth_tolerance_value)
							from_application="True, part value from keyword='comment'"
							infos_poly_post_smooth(keyword,beschreibung,unit,description,uri,measurementclass, value, from_application)
							
							list_mesh_processing_poly_post.append(dic_smooth)
					
						elif "thin" in pp_title:
							dic_thin = {}
							thin_items = pp_values.split(",")
							if len(thin_items) == 2:
								thin_item_maxedge = thin_items[0].split("=")
								thin_item_tolerance = thin_items[1].replace(" ","").split("=")
								thin_maxedge = thin_item_maxedge[0].replace(" ","_")
								thin_maxedge_value = thin_item_maxedge[1].replace(" ","")
								thin_tolerance = thin_item_tolerance[0]
								thin_tolerance_value = thin_item_tolerance[1]
							
								#thin
								##processname
								keyword='processname'
								beschreibung= None
								unit=None
								description= None
								uri=None
								measurementclass=None
								value=pp_title
								from_application=None
								infos_poly_post_thin(keyword,beschreibung,unit,description,uri,measurementclass, value, from_application)
				
								##automatic
								keyword='automatic'
								beschreibung= None
								unit=None
								description= None
								uri=None
								measurementclass=None
								value=True 
								from_application=False
								infos_poly_post_thin(keyword,beschreibung,unit,description,uri,measurementclass, value, from_application)
									
								##maximum edge length
								keyword= 'maximum_edge_length'
								beschreibung= 'maximale Kantenlänge'
								unit='om:millimetre'
								description= 'maximum edge length'
								uri=ontologynamespace + 'MaximumEdgeLength'
								measurementclass=None
								value=float(thin_maxedge_value)
								from_application="True, part value from keyword='comment'"
								infos_poly_post_thin(keyword,beschreibung,unit,description,uri,measurementclass, value, from_application)
				
								##tolerance
								keyword= 'tolerance'
								beschreibung= 'Toleranz'
								unit=om+"millimetre"
								description= 'tolerance'
								uri=ontologynamespace + 'Tolerance'
								measurementclass=None
								value=float(thin_tolerance_value)
								from_application="True, part value from keyword='comment'"
								infos_poly_post_thin(keyword,beschreibung,unit,description,uri,measurementclass, value, from_application)
								
								
								list_mesh_processing_poly_post.append(dic_thin)
									
		# Struktur Mesh		


		if len(list_mesh_processing_poly_post)>0:
			dic_mesh_processing["postprocessing"] = list_mesh_processing_poly_post
		if len(dic_mesh_processing_poly_setup)>0:
			dic_mesh_processing["setup"]=dic_mesh_processing_poly_setup
		if len(dic_mesh_info)>0:
			dic_mesh["mesh_information"] = dic_mesh_info
		if len(dic_mesh_processing)>0:
			list_mesh_processing.append(dic_mesh_processing)
		if len(list_mesh_processing)>0:	
			dic_mesh["processing"] = list_mesh_processing
		if len(dic_mesh)>0:
			list_meshes.append(dic_mesh)

		n = n +1

	# Projektinformationen 
	# berechneter Wert 
	# Anzahl Messungen (gesamtes Projekt)
	keyword= 'number of measurements'
	beschreibung= 'Anzahl Messungen'
	unit = None
	description= 'number of measurements'
	uri=None
	measurementclass=None
	from_application= "script-based calculation"
	value = anz_messungen 
	infos_p(keyword,beschreibung,unit,description,uri,measurementclass, value, from_application)
			
	# Ausgabe
	
	#list_project_info.append(project_info)
	if len(project_info)>0:
		project["project_information"] = project_info
	if len(list_messreihen)>0:	
		project["measurement_series"] =  list_messreihen
	if len(list_meshes)>0:
		project["meshes"]= list_meshes
	if len(list_app)>0:
		project["applications"]=list_app
	
	list_prj = []
	if len(project)>0:
		list_prj.append(project)
	
	if len(list_prj)>0:
		dic_dig["projects"] = list_prj
		
	return dic_dig
	
	
######### Methode zu Ende


######### Methode zum Speichern der Skript Informationen 

def script_version():
	
	# Zeitpunkt
	now = datetime.datetime.now()
	now_string = str(now.year)+"-"+str(now.month).zfill(2)+"-"+str(now.day).zfill(2)+'T'+str(now.hour).zfill(2)+':'+str(now.minute).zfill(2)+':'+str(now.second).zfill(2)
	
	# def dictionary
	dic_script = {}
	
	dic_script["github"]={}
	dic_script["github"]["key_deu"]="GitHub Repository"
	dic_script["github"]["key_eng"]="GitHub Repository"
	dic_script["github"]["value"]="https://github.com/i3mainz/3dcap-md-gen"
	dic_script["github"]["value_type"]="str"
	dic_script["github"]["uri"]="http:///www.wikidata.org/entity/Q364"
	dic_script["github"]["from_application"]="false"
	
	dic_script["github_release"]={}
	dic_script["github_release"]["key_deu"]="GitHub Release"
	dic_script["github_release"]["key_eng"]="GitHub Release"
	dic_script["github_release"]["value"]=github_release
	dic_script["github_release"]["value_type"]="str"
	dic_script["github_release"]["uri"]="http:///www.wikidata.org/entity/Q20631656"
	dic_script["github_release"]["from_application"]="false"
	
	dic_script["script_name"]={}
	dic_script["script_name"]["key_deu"]="Python Skript Name"
	dic_script["script_name"]["key_eng"]="Python Script name"
	dic_script["script_name"]["value"]=script_name
	dic_script["script_name"]["value_type"]="str"
	dic_script["script_name"]["uri"]="http:///www.wikidata.org/entity/Q15955723"
	dic_script["script_name"]["from_application"]="false"
	
	dic_script["start_time_script"]={}
	dic_script["start_time_script"]["key_deu"]="Skriptausführungszeit"
	dic_script["start_time_script"]["key_eng"]="Script execution time"
	dic_script["start_time_script"]["value"]=now_string
	dic_script["start_time_script"]["value_type"]="dateTime"
	dic_script["start_time_script"]["uri"]=provnamespace+"startedAtTime"
	dic_script["start_time_script"]["from_application"]="false"
	
	return dic_script


#########     HAUPTMETHODE     ##########################

def exportMeta(manualmetadatapathJSON=None):
	
	#Definition von Variablen
	
#	try:
	
		pfad = gom.app.project.get('project_file')
		x = pfad.split("\\")
		out_file = pfad.replace(x[-1],(gom.app.project.get('name')))
	
		out_file_json = out_file+"_meta_atos2016.json"
		e=out_file+"_meta_atos2016.csv"
		out_file_ttl=out_file+"_meta_atos2016.ttl"
		
		objectdescriptionpathTTL = out_file+"_objdesc.ttl"
		objectdescriptionpathTXT = out_file+"_objdesc.txt"
		manualmetadatapathTTL = out_file+"_manualmetadata.ttl"
		if manualmetadatapathJSON == None:
			manualmetadatapathJSON = out_file+"_manualmetadata.json"
		manualmetadatapathYAML = out_file+"_manualmetadata.yaml"
		
		## import externer Infos in einen ttl-string
		## import externer Infos in ein dictionary
		ttlstring=set()
		dic_dig = {}
		if os.path.isfile(objectdescriptionpathTTL):
			readInputTTL(objectdescriptionpathTTL,ttlstring)
		elif os.path.isfile(objectdescriptionpathTXT):
			readInputTXTForArtifactDescription(objectdescriptionpathTXT,ttlstring);	
		if os.path.isfile(manualmetadatapathTTL):
			readInputTTL(manualmetadatapathTTL,ttlstring)
		elif os.path.isfile(manualmetadatapathJSON):		### ÜBERPRÜFEN .....
			with open(manualmetadatapathJSON) as json_file:
				#dic_dig["userdata"]=json.load(json_file)
				dic_dig=json.load(json_file)
		elif os.path.isfile(manualmetadatapathYAML):
			with open(manualmetadatapathYAML) as yaml_file:
				dic_dig["userdata"]=yaml.load(yaml_file)
				
	
		# Methode zum Abreifen der Metadaten wird aufgerufen und in einem Dictionary gespeichert
		# externe Infos in dictionary wird übergeben
		dic_prj = createMetaDic(dic_dig)
		
		
		###### export der Metadaten in JSON-File
		with open(out_file_json, 'w') as fp:
			json.dump(dic_prj, fp, indent = 4, ensure_ascii=False)
	
		# Methode zum Umwandeln des Dictionary in TTL 
		# externe Infos aus ttlstring werden übergeben
		fertiges_ttl = exportToTTL(dic_prj, None, ttlstring)
		
		###### export der Metadaten in TTL-File
		with open(out_file_ttl, 'w',encoding='utf8') as text_file:
			text_file.write(ttlstringhead)
			for item in fertiges_ttl:
				text_file.write("%s" % item)
		text_file.close()
	
#	except:
#		print ("weiter gehts")

#######################################################################################################
#### Skript hier starten 

if production:	
	exportMeta()	

else:
	ttlstring=set()
	path="test_laura.json"
	objectdescriptionpathTTL = path+"_objdesc.ttl"
	objectdescriptionpathTXT = path+"_objdesc.txt"
	manualmetadatapathTTL = path+"_manualmetadata.ttl"
	manualmetadatapathJSON = path+"_manualmetadata.json"
	manualmetadatapathYAML = path+"_manualmetadata.yaml"
	ttlstring=set()
	if os.path.isfile(objectdescriptionpathTTL):
		readInputTTL(objectdescriptionpathTTL,ttlstring)     
	elif os.path.isfile(objectdescriptionpathTXT):
		readInputTXTForArtifactDescription(objectdescriptionpathTXT,ttlstring);
	dic_dig = {}
	if os.path.isfile(manualmetadatapathTTL):
		readInputTTL(manualmetadatapathTTL,ttlstring)
	elif os.path.isfile(manualmetadatapathJSON):
		with open(manualmetadatapathJSON) as json_file:
			dic_dig["userdata"]=json.load(json_file)
	elif os.path.isfile(manualmetadatapathYAML):
		with open(manualmetadatapathYAML) as yaml_file:
			dic_dig["userdata"]=yaml.load(yaml_file)
	with open('test_proc.json', 'r') as myfile:
		data=myfile.read()
	dic_prj=json.loads(data)
	###print(ttlstring)
	if True:
		fertiges_ttl = exportToTTL(dic_prj, None,ttlstring)
		text_file = open("out.ttl", "w",encoding='utf8')	
		text_file.write(ttlstringhead)
		for item in fertiges_ttl:
			text_file.write("%s" % item)
		text_file.close()
		
print ("fertsch 3dcap")

