# -*- coding: utf-8 -*-
#
# GOM-Script-Version: 6.2.0-6
# Pythonversion 2.4

# Anja Cramer / LEIZA
# Timo Homburg / i3mainz
# Laura Raddatz / i3mainz
# Informationen von atos-Projektdateien (Messdaten: *.amp / *.session)
# 2020/2021/2022/2023/2024/2025

import gom
import xml, time, os, random
import math
import datetime

# input folder
input_folder = r"D:\atos-v62_project"

## Indicates if only properties for which a URI has been defined in the JSON dict should be considered for the TTL export .
includeonlypropswithuri=False
#includeonlypropswithuri=True

# python script version
script_name = "atos-v62_3dcap_metadata.py"
script_label = "ATOS v6.2 3DCAP Metadata Script"
github_release = "1.0.0"


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
ttlstringhead="@prefix "+str(ontologyprefix)+": <"+str(ontologynamespace)+"> .\n@prefix geocrs: <http://www.opengis.net/ont/crs/>.\n@prefix geocrsaxis: <http://www.opengis.net/ont/crs/cs/axis/> .\n@prefix geo: <http://www.opengis.net/ont/geosparql#> .\n@prefix "+str(dataprefix)+": <"+str(datanamespace)+"> .\n@prefix foaf: <http://xmlns.com/foaf/0.1/> .\n@prefix prov: <http://www.w3.org/ns/prov-o/> .\n@prefix rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#> . \n@prefix om:<http://www.ontology-of-units-of-measure.org/resource/om-2/> .\n@prefix rdfs:<http://www.w3.org/2000/01/rdf-schema#> . \n@prefix owl:<http://www.w3.org/2002/07/owl#> . \n@prefix i3atos:<http://www.i3mainz.de/metadata/atos#> . \n@prefix dc:<http://purl.org/dc/terms/> .\n@prefix i3data:<http://www.i3mainz.de/data/grabbauten/> . \n@prefix i3:<http://www.i3mainz.de/ont#> . \n@prefix xsd:<http://www.w3.org/2001/XMLSchema#> . \n"


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

units={}
def csAsSVG(csdef):
				svgstr= """<svg width=\"400\" height=\"250\" viewbox=\"0 0 375 220\"><defs><marker id=\"arrowhead\" markerWidth=\"10\" markerHeight=\"7\" refX=\"0\" refY=\"2\" orient=\"auto\"><polygon points=\"0 0, 4 2, 0 4\" /></marker></defs>"""
				#print(csdef)
				if len(csdef["axis_list"])>0:
								if csdef["axis_list"][0]["unit_name"] in units:
												svgstr+="""<line x1=\"20\" y1=\"200\" x2=\"200\" y2=\"200\" stroke=\"red\" stroke-width=\"5\" marker-end=\"url(#arrowhead)\"></line><text x=\"110\" y=\"220\" class=\"small\">"""+str(csdef["axis_list"][0]["abbrev"])+": "+str(csdef["axis_list"][0]["name"])+" ("+str(units[csdef["axis_list"][0]["unit_name"]])+") ("+str(csdef["axis_list"][0]["direction"])+")</text>"
								else:
												svgstr+="""<line x1=\"20\" y1=\"200\" x2=\"200\" y2=\"200\" stroke=\"red\" stroke-width=\"5\" marker-end=\"url(#arrowhead)\"></line><text x=\"110\" y=\"220\" class=\"small\">"""+str(csdef["axis_list"][0]["abbrev"])+": "+str(csdef["axis_list"][0]["name"])+" ("+str(csdef["axis_list"][0]["unit_name"])+") ("+str(csdef["axis_list"][0]["direction"])+")</text>"
				if len(csdef["axis_list"])>1:
								if csdef["axis_list"][1]["unit_name"] in units:
												svgstr+="""<line x1=\"20\" y1=\"200\" x2=\"20\" y2=\"20\" stroke=\"green\" stroke-width=\"5\" marker-end=\"url(#arrowhead)\"></line><text x=\"35\" y=\"20\" class=\"small\">"""+str(csdef["axis_list"][1]["abbrev"])+": "+str(csdef["axis_list"][1]["name"])+" ("+str(units[csdef["axis_list"][1]["unit_name"]])+") ("+str(csdef["axis_list"][1]["direction"])+")</text>"
								else:
												svgstr+="""<line x1=\"20\" y1=\"200\" x2=\"20\" y2=\"20\" stroke=\"green\" stroke-width=\"5\" marker-end=\"url(#arrowhead)\"></line><text x=\"35\" y=\"20\" class=\"small\">"""+str(csdef["axis_list"][1]["abbrev"])+": "+str(csdef["axis_list"][1]["name"])+" ("+str(csdef["axis_list"][1]["unit_name"])+") ("+str(csdef["axis_list"][1]["direction"])+")</text>"
				if len(csdef["axis_list"])>2:
								if csdef["axis_list"][2]["unit_name"] in units:
												svgstr+="""<line x1=\"20\" y1=\"200\" x2=\"190\" y2=\"30\" stroke=\"blue\" stroke-width=\"5\" marker-end=\"url(#arrowhead)\"></line><text x=\"210\" y=\"25\" class=\"small\">"""+str(csdef["axis_list"][2]["abbrev"])+": "+str(csdef["axis_list"][2]["name"])+" ("+str(units[csdef["axis_list"][2]["unit_name"]])+") ("+str(csdef["axis_list"][2]["direction"])+")</text>"
								else:
												svgstr+="""<line x1=\"20\" y1=\"200\" x2=\"190\" y2=\"30\" stroke=\"blue\" stroke-width=\"5\" marker-end=\"url(#arrowhead)\"></line><text x=\"210\" y=\"25\" class=\"small\">"""+str(csdef["axis_list"][2]["abbrev"])+": "+str(csdef["axis_list"][2]["name"])+" ("+str(csdef["axis_list"][2]["unit_name"])+") ("+str(csdef["axis_list"][2]["direction"])+")</text>"
				return svgstr.replace("\"","'")+"</svg>"


def csAxisAsSVG(axisdef):
				svgstr= """<svg width=\"400\" height=\"100\" viewbox=\"0 0 275 100\"><defs><marker id=\"arrowhead\" markerWidth=\"10\" markerHeight=\"7\" refX=\"0\" refY=\"2\" orient=\"auto\"><polygon points=\"0 0, 4 2, 0 4\" /></marker></defs>"""
				if axisdef["unit_name"] in units:
								svgstr+="""<line x1=\"20\" y1=\"50\" x2=\"200\" y2=\"50\" stroke=\"gray\" stroke-width=\"5\" marker-end=\"url(#arrowhead)\"></line><text x=\"30\" y=\"70\" class=\"small\">"""+str(axisdef["abbrev"])+": "+str(axisdef["name"])+" ("+str(units[axisdef["unit_name"]])+") ("+str(axisdef["direction"])+")</text>"
				else:
								svgstr+="""<line x1=\"20\" y1=\"50\" x2=\"200\" y2=\"50\" stroke=\"gray\" stroke-width=\"5\" marker-end=\"url(#arrowhead)\"></line><text x=\"30\" y=\"70\" class=\"small\">"""+str(axisdef["abbrev"])+": "+str(axisdef["name"])+" ("+str(axisdef["unit_name"])+") ("+str(axisdef["direction"])+")</text>"
				return svgstr.replace("\"","'")+"</svg>"


def csFromPoint(pointind,x,y,z,ttlstring):
	crsid=str(dataprefix)+":cs_3d_x_"+str(x["unit"]).replace("om:","")+"_y_"+str(y["unit"]).replace("om:","")+"_z_"+str(z["unit"]).replace("om:","")
	ttlstring.add(str(pointind)+" geo:inSRS "+str(crsid)+" .\n")
	ttlstring.add(str(crsid)+" geocrs:asSVG \""+str(csAsSVG({"axis_list":[{"unit_name":x["unit"],"direction":"x","abbrev":"x","name":"x"},{"unit_name":y["unit"],"direction":"y","abbrev":"y","name":"y"},{"unit_name":z["unit"],"direction":"z","abbrev":"z","name":"z"}]}))+"\"^^xsd:string .\n")
	ttlstring.add(str(crsid)+" rdfs:label \"Local 3D Coordinate System X("+str(x["unit"])+") Y("+str(y["unit"])+") Z("+str(z["unit"])+")\" . \n")
	ttlstring.add(str(crsid)+" rdf:type geocrs:CoordinateSystem . \n")
	ttlstring.add(str(crsid)+" geocrs:axis "+str(crsid)+"_xaxis .\n")
	axisid=str(crsid)+"_xaxis"
	ttlstring.add("geocrsaxis:"+axisid+" rdf:type geocrs:CoordinateSystemAxis . \n")
	ttlstring.add("geocrsaxis:"+axisid+" geocrs:asSVG \""+str(csAxisAsSVG({"unit_name":x["unit"],"direction":"x","abbrev":"x","name":"x"}))+"\"^^geocrs:svgLiteral . \n")
	ttlstring.add("geocrsaxis:"+axisid+" geocrs:axisAbbrev \""+str("x").replace("\"","'")+"\"^^xsd:string . \n")
	ttlstring.add(str(crsid)+" geocrs:axis "+str(crsid)+"_yaxis .\n")
	axisid=str(crsid)+"_yaxis"
	ttlstring.add("geocrsaxis:"+axisid+" rdf:type geocrs:CoordinateSystemAxis . \n")
	ttlstring.add("geocrsaxis:"+axisid+" geocrs:asSVG \""+str(csAxisAsSVG({"unit_name":y["unit"],"direction":"y","abbrev":"y","name":"y"}))+"\"^^geocrs:svgLiteral . \n")
	ttlstring.add("geocrsaxis:"+axisid+" geocrs:axisAbbrev \""+str("y").replace("\"","'")+"\"^^xsd:string . \n")
	ttlstring.add(str(crsid)+" geocrs:axis "+str(crsid)+"_zaxis .\n")
	ttlstring.add("geocrsaxis:"+axisid+" rdf:type geocrs:CoordinateSystemAxis . \n")
	ttlstring.add("geocrsaxis:"+axisid+" geocrs:asSVG \""+str(csAxisAsSVG({"unit_name":z["unit"],"direction":"z","abbrev":"z","name":"z"}))+"\"^^geocrs:svgLiteral . \n")
	ttlstring.add("geocrsaxis:"+axisid+" geocrs:axisAbbrev \""+str("z").replace("\"","'")+"\"^^xsd:string . \n")
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
			ttlstring.add(str(dataprefix)+":"+str(id)+" "+str(propuri)+" \"\"\""+str(inputvalue)+"\"\"\" .\n")
		else:
			ttlstring.add(str(propuri)+" rdf:type owl:DatatypeProperty .\n")
			ttlstring.add(str(propuri)+" rdfs:domain "+str(classs)+" .\n")
			if englishlabel in jsonobj[info] and jsonobj[info][englishlabel]!=None and str(jsonobj[info][englishlabel])!="" and str(jsonobj[info][englishlabel])!="...":
				ttlstring.add(str(propuri)+" rdfs:label \""+str(jsonobj[info][englishlabel]).replace("\"","'")+"\"@en .\n")
			if germanlabel in jsonobj[info] and jsonobj[info][germanlabel]!=None and str(jsonobj[info][germanlabel])!="" and str(jsonobj[info][germanlabel])!="...":
				ttlstring.add(str(propuri)+" rdfs:label \""+str(jsonobj[info][germanlabel]).replace("\"","'")+"\"@de .\n")
			ttlstring.add(str(propuri)+" rdfs:range "+str(datatypes[jsonobj[info]["value_type"]])+" .\n")
			ttlstring.add(str(dataprefix)+":"+str(id)+" "+str(propuri)+" \"\"\""+str(inputvalue).replace("\\","\\\\")+"\"\"\"^^"+str(datatypes[jsonobj[info]["value_type"]])+" .\n")
	#print("handled Property")
	return ttlstring

## Converts a preformatted dictionary to a set of triples .
#  @param dict the dictionary to export from
#  @param measurementToExport indicates whether to export measurements
def exportToTTL(dict,measurementToExport,ttlstring,usermetadata=None):
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
		if usermetadata!=None:
			ttlstring=addUserMetadataToId(ttlstring,usermetadata,projectid)
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
							ttlstring=exportInformationFromIndAsTTL(grp,grpid,str(ontologyprefix)+":GRP",labelprefix+" MS "+str(msindex)+" GRP"+str(index),ttlstring)
							if "r_x" in grp and "r_y" in grp and "r_z" in grp:
								ttlstring.add(str(dataprefix)+":"+str(grpid)+" geo:asWKT \"POINT("+str(grp["r_x"]["value"])+" "+str(grp["r_y"]["value"])+" "+str(grp["r_z"]["value"])+")\"^^geo:wktLiteral .\n")
								ttlstring=csFromPoint(str(dataprefix)+":"+str(grpid),grp["r_x"],grp["r_y"],grp["r_z"],ttlstring)
							elif "coordinate.x" in grp and "coordinate.y" in grp and "coordinate.z" in grp:
								ttlstring.add(str(dataprefix)+":"+str(grpid)+" geo:asWKT \"POINT("+str(grp["coordinate.x"]["value"])+" "+str(grp["coordinate.y"]["value"])+" "+str(grp["coordinate.z"]["value"])+")\"^^geo:wktLiteral .\n")
								ttlstring=csFromPoint(str(dataprefix)+":"+str(grpid),grp["coordinate.x"],grp["coordinate.y"],grp["coordinate.z"],ttlstring)
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
										ttlstring=csFromPoint(str(dataprefix)+":"+str(rpuri),rp["r_x"],rp["r_y"],rp["r_z"],ttlstring)
									###atos 2016
									elif "reference_point_coordinate.x" in rp and "reference_point_coordinate.y" in rp and "reference_point_coordinate.z" in rp:
										ttlstring.add(str(dataprefix)+":"+str(rpuri)+" geo:asWKT \"POINT("+str(rp["reference_point_coordinate.x"]["value"])+" "+str(rp["reference_point_coordinate.y"]["value"])+" "+str(rp["reference_point_coordinate.z"]["value"])+")\"^^geo:wktLiteral .\n")
										ttlstring=csFromPoint(str(dataprefix)+":"+str(rpuri),rp["r_x"],rp["r_y"],rp["r_z"],ttlstring)
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
					for cont in realobj:
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

####################################################################################################
#
######### Methode zum Speichern der Skript Informationen 

# metadaten python-script
def script_version():
	
	# Zeitpunkt
	now = datetime.datetime.now()
	now_string = str(now.year)+"-"+str(now.month).zfill(2)+"-"+str(now.day).zfill(2)+'T'+str(now.hour).zfill(2)+':'+str(now.minute).zfill(2)+':'+str(now.second).zfill(2)
	
	# def dictionary
	dic_script = {}
	
	dic_script["github"]={}
	dic_script["github"]["key_deu"]="GitHub Repository"
	dic_script["github"]["key_eng"]="GitHub Repository"
	dic_script["github"]["value"]="http://github.com/i3mainz/3dcap-md-gen"
	dic_script["github"]["value_type"]="str"
	dic_script["github"]["uri"]="http://www.wikidata.org/entity/Q364"
	dic_script["github"]["from_application"]="false"
	
	dic_script["github_release"]={}
	dic_script["github_release"]["key_deu"]="GitHub Release"
	dic_script["github_release"]["key_eng"]="GitHub Release"
	dic_script["github_release"]["value"]=github_release
	dic_script["github_release"]["value_type"]="str"
	dic_script["github_release"]["uri"]="http://www.wikidata.org/entity/Q20631656"
	dic_script["github_release"]["from_application"]="false"
	
	dic_script["script_name"]={}
	dic_script["script_name"]["key_deu"]="Python Skript Name"
	dic_script["script_name"]["key_eng"]="Python Script name"
	dic_script["script_name"]["value"]=script_name
	dic_script["script_name"]["value_type"]="str"
	dic_script["script_name"]["uri"]="http://www.wikidata.org/entity/Q15955723"
	dic_script["script_name"]["from_application"]="false"
	
	dic_script["start_time_script"]={}
	dic_script["start_time_script"]["key_deu"]="Skriptausführungszeit"
	dic_script["start_time_script"]["key_eng"]="Script execution time"
	dic_script["start_time_script"]["value"]=now_string
	dic_script["start_time_script"]["value_type"]="dateTime"
	dic_script["start_time_script"]["uri"]=provnamespace+"startedAtTime"
	dic_script["start_time_script"]["from_application"]="false"
	
	return dic_script	

######################## GET METADATA ###############################

######################## PROJECTS ###############################


######## project / measurement series ###############





for root, dirs, files in os.walk(input_folder):
	for atos_file in files:
		if os.path.splitext(atos_file)[-1]==".session":
			gom.script.sys.load_session (
				files=[root + "/" + atos_file], 
				mode=gom.List ('delete', ['append', 'delete']), 
				remember_file_name=True)

			dic_prj ={}
			list_prj=[]
			prj = 0

			while prj < 1:
				
				dic_dig = {}
				list_projects = []	

				#### application ####
				dic_dig_app = {}
				list_app = []
				
			
				#### project ####
				dic_dig_project = {}	
				
				## Creates a dictionary / JSON object about information given from the respective software.
				#  @param beschreibung the description of the parameter of the software in German
				#  @param description the description of the parameter of the software in English
				#  @param keyword
				#  @param einheit The unit to be associated with the software parameter
				#  @param uri The URI to be associated with the software parameter
				#  @param measurementclass
				#  @param application indicates if the parameter is a software parameter or an external parameter		
				def infos_app (beschreibung, description, keyword, einheit, uri, measurementclass, application):		
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
					if einheit!=None:
						dir["unit"] = einheit
					if application!=None:
						dir["from_application"] = application			
					# if keyword = 'PROJECT.DATE' - change datetype
					if keyword == 'PROJECT.DATE':
						value_new = dir["value"]
						capturetime = time.strptime(value_new, "%m/%d/%y")
						dir["value"] = (time.strftime("%Y-%m-%d",capturetime))
						dir["value_type"] = "date"			
					# store in dictionary	
					if dir["value"] != None:				
						if len(str(dir["value"])) != 0:
							dic_dig_app[keyword]= {}		
							dic_dig_app[keyword]= dir		

				def infos_project (beschreibung, description, keyword, einheit, uri, measurementclass, application):						
					dir = {}
					dir.clear()
					if keyword == 'acquisition_technology':
						dir["value"] = 'fringe projection'
						dir["value_type"] = type(dir["value"]).__name__
					elif keyword == 'project_name':
						try:
							value = gom.app.get('ACTUAL_SESSION_FILE')
							dir["value"] = (value.split("\\")[-1].replace(".session",""))
							dir["value_type"] = type(dir["value"]).__name__					
						except:
							dir["value"] = None
							dir["value_type"] = type(dir["value"]).__name__				
					else:
						dir["value"] = gom.app.get(keyword)
						dir["value_type"] = type(gom.app.get(keyword)).__name__
						
					dir["key_deu"] = beschreibung
					
					if description!=None:
						dir["key_eng"] = description		
					if uri!=None:
						dir["uri"] = uri	
					if measurementclass!=None:
						dir["measurementclass"] = measurementclass						

					if einheit!=None:
						dir["unit"] = einheit
					if application!=None:
						dir["from_application"] = application
					if keyword == 'PROJECT.DATE':
						value_new = dir["value"]
						capturetime = time.strptime(value_new, "%m/%d/%y")
						dir["value"] = (time.strftime("%Y-%m-%d",capturetime))
						dir["value_type"] = "date"
					# store in dictionary
					if dir["value"] != None:				
						if len(str(dir["value"])) != 0:
							dic_dig_project[keyword]= {}		
							dic_dig_project[keyword]= dir
							

				############ get values  #############	
				
				# Aktuelles Datum
				beschreibung = "Aktuelles Datum"
				description = None
				keyword = 'PROJECT.DATE'
				einheit = None
				uri= None
				measurementclass = None
				application = "true"
				infos_app (beschreibung, description, keyword, einheit, uri, measurementclass, application)	
				
				# Applikationsname	
				beschreibung = "Applikationsname"
				description = "Application name"
				keyword = 'PROJECT.TYPE'
				einheit = None
				uri= None
				measurementclass = None
				application = "true"
				infos_app (beschreibung, description, keyword, einheit, uri, measurementclass, application)
				
				# Applikationsversion	
				beschreibung = "Applikationsversion"
				description = "Application version"
				keyword = 'PROJECT.VERSION'
				einheit = None
				uri= None
				measurementclass = None
				application = "true"
				infos_app (beschreibung, description, keyword, einheit, uri, measurementclass, application)

				# Heimatverzeichnis	
				beschreibung = "Heimatverzeichnis"
				description = "Home directory"
				keyword = 'HOME'
				einheit = None
				uri= None
				measurementclass = None
				application = "true"
				infos_app (beschreibung, description, keyword, einheit, uri, measurementclass, application)
				
				# Projektverzeichnis
				beschreibung = "Projektverzeichnis"
				description = "Project directory"
				keyword = 'PROJECTDIR'
				einheit = None
				uri= None
				measurementclass = None
				application = "true"
				infos_app (beschreibung, description, keyword, einheit, uri, measurementclass, application)
				
				# Sitzungsname (komplett)
				beschreibung = "Sitzungsname (komplett)"
				description = "Session name (complete)"
				keyword = 'ACTUAL_SESSION_FILE'
				einheit = None
				uri= None
				measurementclass = None
				application = "true"
				infos_project (beschreibung, description, keyword, einheit, uri, measurementclass, application)

				# Projektname (komplett)
				beschreibung = "Projektname"
				description = "Project name"
				keyword = 'project_name'
				einheit = None
				uri= 'rdfs:label'
				measurementclass = None
				application = "false"
				infos_project (beschreibung, description, keyword, einheit, uri, measurementclass, application)

				# Softwarsprache
				beschreibung = "Softwaresprache"
				description = "Software language"
				keyword = 'LANGUAGE'
				einheit = None
				uri= None
				measurementclass = None
				application = "true"
				infos_app (beschreibung, description, keyword, einheit, uri, measurementclass, application)

				# Softwareverzeichnis
				beschreibung = "Softwareverzeichnis"
				description = "Software directory"
				keyword = 'SOFTWAREDIR'
				einheit = None
				uri= None
				measurementclass = None
				application = "true"
				infos_app (beschreibung, description, keyword, einheit, uri, measurementclass, application)
				
				# Verzeichnis für temporäre Daten	
				beschreibung = "Verzeichnis für temporäre Daten"
				description = "Temporary directory"
				keyword = 'TEMPDIR'
				einheit = None
				uri= None
				measurementclass = None
				application = "true"
				infos_app (beschreibung, description, keyword, einheit, uri, measurementclass, application)


				### MEASUREMENT SERIES (in atos v6.2 project information) #############################################################################################
				
				p = 0				
				
				while p < len( gom.app.projects):		
					#### measurment series ####
					dic_project = {}	
					####  measurment_series_information ####
					dic_prj_info = {}
					##### calibration / sensor ID
					sensor_id = 0	
					
					## Creates a dictionary / JSON object about information given from the respective software.
					#  @param beschreibung the description of the parameter of the software in German
					#  @param description the description of the parameter of the software in English
					#  @param keyword
					#  @param einheit The unit to be associated with the software parameter
					#  @param uri The URI to be associated with the software parameter
					#  @param measurementclass
					#  @param application indicates if the parameter is a software parameter or an external parameter
					def infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application):		
						dir = {}
						dir.clear()
						try:
							dir["value"] = gom.app.projects[p].get(keyword)
							dir["key_deu"] = beschreibung
							if description!=None:
								dir["key_eng"] = description		
							if uri!=None:
								dir["uri"] = uri	
							if measurementclass!=None:
								dir["measurementclass"] = measurementclass			
							dir["value_type"] = type(gom.app.projects[p].get(keyword)).__name__
							if einheit!=None:
								dir["unit"] = einheit
							if application!=None:
								dir["from_application"] = application
																																
							if dir["value"] != None:				
								if len(str(dir["value"])) != 0:
									if includeonlypropswithuri and "uri" in dir:
										dic_prj_info[keyword] = {}		
										dic_prj_info[keyword] = dir
									if not includeonlypropswithuri:
										dic_prj_info[keyword] = {}		
										dic_prj_info[keyword] = dir
						except:
							print ("error")
							print(e)
																												

				
					############ get values #############
					
					# Eckmasksierung
					beschreibung = "Eckmaskierung"
					description = "Corner mask size"
					keyword = 'prj_corner_mask'
					einheit = om+"percent"
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)	
						
					# Ellipsenqualität
					beschreibung = "Ellipsenqualität"
					description = "Ellipse quality"
					keyword = 'prj_ellipse_quality'
					einheit = om+"pixel"
					uri=ontologynamespace+"EllipseQuality"
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Expansionskoeffizient
					beschreibung = "Expansionskoeffizient"
					description = "Expansion coefficient"
					keyword = 'prj_ref_frame_exp_coeff'
					einheit = None
					uri= ontologynamespace+"ExpansionCoefficient"
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Kalibrierungstemperatur Rahmen
					beschreibung = "Kalibrierungstemperatur Rahmen"
					description = "Frame calibration temperature"
					keyword = 'prj_ref_frame_cal_temperature'
					einheit = om+"degreeCelsius"
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Feinausrichtung
					beschreibung = "Feinausrichtung"
					description = "Alignment"
					keyword = 'prj_alignment'
					einheit = None
					uri=ontologynamespace+"Alignment"
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)	
					
					# Lichtfaktorkalibrierungs-Umgebung
					beschreibung = "Lichtfaktorkalibrierungs-Umgebung"
					description = "Light factor calibration enviroment"
					keyword = 'prj_light_factor_calibration_environment'
					einheit = None
					uri=ontologynamespace+"LightFactorCalibrationEnvironment"
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Max. Lichtänderung
					beschreibung = "Max. Lichtänderung"
					description = None
					keyword = 'prj_max_lighting'
					einheit = "Grauwerte"  #gehen von 0 bis 100
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Max. Sekunden zwischen Lichtfaktorkalibrierung
					beschreibung = "Max. Sekunden zwischen Lichtfaktorkalibrierung"
					description = None
					keyword = 'prj_max_sec_between_light_factor_calibration'
					einheit = om+"seconds-Time"
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Max. Sensorbewegung
					beschreibung = "Max. Sensorbewegung"
					description = "Max. sensor movement"
					keyword = 'prj_max_movement'
					einheit = om+"pixel"
					uri= ontologynamespace+ "MaximumSensorMovement"
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Messtemperatur
					beschreibung = "Messtemperatur"
					description = "Measurement temperature"
					keyword = 'prj_measurement_temperature'
					einheit = om+"degreeCelsius"
					uri=ontologynamespace+"MeasurementTemperature"
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Min. Modulationsschwelle
					beschreibung = "Min. Modulationsschwelle"
					description = None
					keyword = 'prj_mod_threshold'
					einheit = "Grauwerte"  #gehen von 0 bis 255
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Nah zum Sensor
					beschreibung = "Nah zum Sensor"
					description = "Close to sensor"
					keyword = 'prj_depth_min'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Phasensteps
					beschreibung = "Phasensteps"
					description = "Phase steps"
					keyword = 'prj_phase_steps'
					einheit = None
					uri=ontologynamespace+"numberOfPhaseSteps"
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Projekt Basisverzeichnis
					beschreibung = "Projekt Basisverzeichnis"
					description = None
					keyword = 'prj_directory'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Projektname
					beschreibung = "Projektname"
					description = "Project name"
					keyword = 'prj_n'
					uri= 'rdfs:label'
					einheit = None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Referenzpunktfarbe
					beschreibung = "Referenzpunktfarbe"
					description = None
					keyword = 'prj_ref_color'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Referenzpunktgröße
					beschreibung = "Referenzpunktgröße"
					description = None
					keyword = 'prj_ref_type'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Referenzpunktvorlage-Name
					beschreibung = "Referenzpunktvorlage-Name"
					description = None
					keyword = 'prj_ref_frame_template_name'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Status: Bewegungskontrolle an?
					beschreibung = "Status: Bewegungskontrolle an?"
					description = "State: enable movement check?"
					keyword = 'prj_check_movement'
					einheit = None
					uri=ontologynamespace+"movementControlActivated"
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Status: Daten von einer Kamera?
					beschreibung = "Status: Daten von einer Kamera?"
					description = None
					keyword = 'prj_one_cam'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Status: Feinausrichtung berechnen?
					beschreibung = "Status: Feinausrichtung berechnen?"
					description = "State: alignment computed?"
					keyword = 'prj_aligned'
					einheit = None
					uri=ontologynamespace+"areMeasurementsAligned"
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Status: Lichtkontrolle an?
					beschreibung = "Status: Lichtkontrolle an?"
					description = "State: enable lighting check?"
					keyword = 'prj_check_lighting'
					einheit = None
					uri=ontologynamespace+"lightControlActivated"
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Status: Punkte an Glanzstellen berechnen?
					beschreibung = "Status: Punkte an Glanzstellen berechnen?"
					description = "State: use shiny points?"
					keyword = 'prj_shiny_points'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Status: Punkte bei starken Grauwertübergängen verwendet?
					beschreibung = "Status: Punkte bei starken Grauwertübergängen verwendet?"
					description = None
					keyword = 'prj_col_trans'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Status: Ref.-Punktgröße verwendet?
					beschreibung = "Status: Ref.-Punktgröße verwendet?"
					description = None
					keyword = 'prj_use_ref_type'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Status: Referenzpunkte einsammeln?
					beschreibung = "Status: Referenzpunkte einsammeln?"
					description = None
					keyword = 'prj_add_ref'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Status: Transformationskontrolle an?
					beschreibung = "Status: Transformationskontrolle an?"
					description = "State: enable transformation check?"
					keyword = 'prj_check_trafo'
					einheit = None
					uri=ontologynamespace+"transformationCheck"
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Status: alle Entfaltungschecks verwendet? (ATOS II / III)?
					beschreibung = "Status: alle Entfaltungschecks verwendet? (ATOS II / III)?"
					description = None
					keyword = 'prj_use_all_unwrap_checks'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Status: kleinste Modulationsmakse verwendet (nur ATOS III)?
					beschreibung = "Status: kleinste Modulationsmakse verwendet (nur ATOS III)?"
					description = None
					keyword = 'prj_smallest_mod_mask'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Status: lange Dreiecke verwendet?
					beschreibung = "Status: lange Dreiecke verwendet?"
					description = "State: use long triangles?"
					keyword = 'prj_long_triangles'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Status: starkes Umgebungslicht?
					beschreibung = "Status: starkes Umgebungslicht?"
					description = "State: strong ambient light?"
					keyword = 'prj_ambient_light'
					einheit = None
					uri=ontologynamespace+"strongAmbientLight"
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Tiefenbeschränkung
					beschreibung = "Tiefenbeschränkung"
					description = None
					keyword = 'prj_depth'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Vorschau-Raster
					beschreibung = "Vorschau-Raster"
					description = None
					keyword = 'prj_raster'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Weiter entfernt vom Sensor
					beschreibung = "Weiter entfernt vom Sensor"
					description = None
					keyword = 'prj_depth_max'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Abteilung
					beschreibung = gom.app.projects[p].get ('d_department')
					description = "Abteilung"
					keyword = 'c_department'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Ausrichtung
					beschreibung = gom.app.projects[p].get ('d_alignment')
					description = "Ausrichtung"
					keyword = 'c_alignment'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
					# Bauteil
					beschreibung = gom.app.projects[p].get ('d_part')
					description = "Part"
					keyword = 'c_part'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Chargen-Nr.
					beschreibung = gom.app.projects[p].get ('d_charge_nr')
					description = "Charge number"
					keyword = 'c_charge_nr'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
					# Datenstand
					beschreibung = gom.app.projects[p].get ('d_version')
					description = "Version"
					keyword = 'c_version'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Datum
					beschreibung = gom.app.projects[p].get ('d_date')
					description = "Date"
					keyword = 'c_date'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
					# Firma
					beschreibung = gom.app.projects[p].get ('d_company')
					description = "Company"
					keyword = 'c_company'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
					# Kommentar 1
					beschreibung = gom.app.projects[p].get ('d_comment1')
					description = "Comment 1"
					keyword = 'c_comment1'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
					# Kommentar 2
					beschreibung = gom.app.projects[p].get ('d_comment2')
					description = "Comment 2"
					keyword = 'c_comment2'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Kommentar 3
					beschreibung = gom.app.projects[p].get ('d_comment3')
					description = "Comment 3"
					keyword = 'c_comment3'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)	
					
					# Ort
					beschreibung = gom.app.projects[p].get ('d_location')
					description = "Location"
					keyword = 'c_location'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)	
				
					# Projekt
					beschreibung = gom.app.projects[p].get ('d_project')
					description = "Project"
					keyword = 'c_project'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Prüfer
					beschreibung = gom.app.projects[p].get ('d_inspector')
					description = "Inspector"
					uri= None
					keyword = 'c_inspector'
					einheit = None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# System
					beschreibung = gom.app.projects[p].get ('d_system')
					description = "System"
					keyword = 'c_system'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Teile-Nr.
					beschreibung = gom.app.projects[p].get ('d_part_nr')
					description = "Part number"
					keyword = 'c_part_nr'
					einheit = None
					uri=None
					measurementclass = None
					application = "true"
					infos_projects (beschreibung, description, keyword, einheit, uri, measurementclass, application)
				
					
					### GLOBALE REFERENZPUNKTE #############################################################################################
					
					list_grp = []
					grp = 0
					
					while grp < len(gom.app.projects[p].gref_points):
						dic_grp = {}	
						
						## Creates a dictionary / JSON object about information given from the respective software.
						#  @param beschreibung the description of the parameter of the software in German
						#  @param description the description of the parameter of the software in English
						#  @param keyword
						#  @param einheit The unit to be associated with the software parameter
						#  @param uri The URI to be associated with the software parameter
						#  @param measurementclass
						#  @param application indicates if the parameter is a software parameter or an external parameter						
						def infos_grp(beschreibung, description, keyword, einheit, uri, measurementclass, application):
								dir = {}
								dir.clear()
								try:
									dir["value"] = gom.app.projects[p].gref_points[grp].get(keyword)
									dir["key_deu"] = beschreibung
									if description!=None:
										dir["key_eng"] = description
									if uri!=None:
										dir["uri"] = uri	
									if measurementclass!=None:
										dir["measurementclass"] = measurementclass			
									dir["value_type"] = type(gom.app.projects[p].gref_points[grp].get(keyword)).__name__
									if einheit!=None:
										dir["unit"] = einheit
									if application!=None:
										dir["from_application"] = application
																																								
									if dir["value"] != None:				
										if len(str(dir["value"])) != 0:
											if includeonlypropswithuri and "uri" in dir:
												dic_grp[keyword]= {}		
												dic_grp[keyword]= dir
											if not includeonlypropswithuri:
												dic_grp[keyword]= {}		
												dic_grp[keyword]= dir
								except:
									print ("error")
									print(e)
							
								
						############ get values ############# 	
						
						# Punkt ID
						beschreibung = "Punkt ID"
						description = "Point ID"
						keyword = 'r_id'
						einheit = None
						uri= ontologynamespace+'PointID'
						measurementclass = None
						application = "true"
						infos_grp (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Punktekennzeichnung (Messung)
						beschreibung = "Punktekennzeichnung (Messung)"
						description = "Point flags (measurement)"
						keyword = 'r_state'
						einheit = None
						uri= ontologynamespace+'PointMeasurementState'
						measurementclass = None
						application = "true"
						infos_grp (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Punktekennzeichnung (Project)
						beschreibung = "Punktekennzeichnung (Project)"
						description = "Point flags (project)"
						keyword = 'r_pstate'
						einheit = None
						uri=ontologynamespace+'PointProjectState'
						measurementclass = None
						application = "true"
						infos_grp (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Status: Punkt ist gemeinsamer Referenzpunkt?
						beschreibung = "Status: Punkt ist gemeinsamer Referenzpunkt?"
						description = "State: point is common ref.point?"
						keyword = 'r_common'
						einheit = None
						uri=ontologynamespace+'commonReferencepoint'
						measurementclass = None
						application = "true"
						infos_grp (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Status: selektiert?
						beschreibung = "Status: selektiert?"
						description = "State: selected?"
						keyword = 'selected'
						einheit = None
						uri=None
						measurementclass = None
						application = "true"
						infos_grp (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# x-coordinate
						beschreibung = "x-Koordinate"
						description = "x-coordinate"
						keyword = 'r_x'
						einheit = om+"millimetre"
						uri=ontologynamespace+'xCoordinate'
						measurementclass = None
						application = "true"
						infos_grp (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# y-coordinate
						beschreibung = "y-Koordinate"
						description = "y-coordinate"
						keyword = 'r_y'
						einheit = om+"millimetre"
						uri=ontologynamespace+'yCoordinate'
						measurementclass = None
						application = "true"
						infos_grp (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# z-coorinate
						beschreibung = "z-Koordinate"
						description = "z-coordinate"
						keyword = 'r_z'
						einheit = om+"millimetre"
						uri=ontologynamespace+'zCoordinate'
						measurementclass = None
						application = "true"
						infos_grp (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Point deviation
						beschreibung = "Punktabweichung"
						description = "Point deviation"
						keyword = 'r_dev'
						einheit = om+"millimetre"
						uri=ontologynamespace+'PointMeasurementDeviation'
						measurementclass = None
						application = "true"
						infos_grp (beschreibung, description, keyword, einheit, uri, measurementclass, application)		
						
						if len(dic_grp) > 0:
							list_grp.append(dic_grp)
						
						grp = grp + 1
					
					
					### MEASUREMENTS #############################################################################################
					list_sensors = []
					temp_list_cal_time = [] # hier kommt nur der Zeitpunkt der Kalibrierung rein, für spätere Abfrage
					list_measurements = []
					
					m = 0	
					
					while m < len(gom.app.projects[p].measurements):
						dic_sensor = {}
						dic_measurement = {}	
						
						dic_measurement_sensor = {}
						dic_measurement_cal = {}
						
						dic_measurement_setup ={}			
						dic_measurement_check ={}
						dic_measurement_info = {}
						
						dic_measurement_cal_calobject = {}
						dic_measurement_cal_calsetup = {}
						dic_measurement_cal_calresults = {}
						
						### Information added manually ###
						# recording technology
						# nur wenn es auch Messungen gibt
						beschreibung = "Aufnahmeverfahren"
						description = "acquisition technology"
						keyword = 'acquisition_technology'
						einheit = None
						uri= ontologynamespace+"AcquisitionTechnology"
						measurementclass = ontologynamespace+"FringeProjection"
						application = "false"
						infos_project (beschreibung, description, keyword, einheit, uri, measurementclass, application)	
						
						
						## Creates a dictionary / JSON object about information given from the respective software.
						#  @param beschreibung the description of the parameter of the software in German
						#  @param description the description of the parameter of the software in English
						#  @param keyword
						#  @param einheit The unit to be associated with the software parameter
						#  @param uri The URI to be associated with the software parameter
						#  @param measurementclass
						#  @param application indicates if the parameter is a software parameter or an external parameter
						
						def measurements_sensor (beschreibung, description, keyword, einheit, uri, measurementclass, application, value=None):			
							dir = {}
							dir.clear()
							# zeitangaben
							try:
								if keyword == 'm_cal_time':
									value = gom.app.projects[p].measurements[m].get(keyword)
									if value != None:
										capturetime = time.strptime(value, "%a %b %d %H:%M:%S %Y")
										dir["value"] = (time.strftime("%Y-%m-%dT%H:%M:%S",capturetime))
								elif keyword =='theoretical_measuring_point_distance':
									dir["value"] = value
								else:
									dir["value"] = gom.app.projects[p].measurements[m].get(keyword)
																																				
								if keyword == 'm_cal_time':
									dir["value_type"] = "dateTime"
								elif keyword =='theoretical_measuring_point_distance':
									dir["value_type"] = type(value).__name__
								else:
									dir["value_type"] = type(gom.app.projects[p].measurements[m].get(keyword)).__name__
								dir["key_deu"] = beschreibung
								if description!=None:
									dir["key_eng"] = description
								if uri!=None:
									dir["uri"] = uri	
								if measurementclass!=None:
									dir["measurementclass"] = measurementclass
								if einheit!=None:
									dir["unit"] = einheit
								if application!=None:
									dir["from_application"] = application
																																				
								if dir["value"] != None:				
									if len(str(dir["value"])) != 0:
										if includeonlypropswithuri and "uri" in dir:
											dic_measurement_sensor[keyword]= {}		
											dic_measurement_sensor[keyword]= dir
										if not includeonlypropswithuri:
											dic_measurement_sensor[keyword] = {}		
											dic_measurement_sensor[keyword] = dir
							except:
								print ("error")
								print(e)
											
						def measurements_setup (beschreibung, description, keyword, einheit, uri, measurementclass, application):
							dir = {}
							dir.clear()
							try:
								if keyword == "invert m_one_cam":
									dir["value"] = gom.app.projects[p].measurements[m].get('m_one_cam')
									if dir["value"] == True:
										dir["value"] = False
									if dir["value"] == False:
										dir["value"] = True
									dir["value_type"] = type(gom.app.projects[p].measurements[m].get('m_one_cam')).__name__					
								elif keyword == "invert m_shiny_points":
									dir["value"] = gom.app.projects[p].measurements[m].get('m_shiny_points')
									if dir["value"] == True:
										dir["value"] = False
									if dir["value"] == False:
										dir["value"] = True
									dir["value_type"] = type(gom.app.projects[p].measurements[m].get('m_shiny_points')).__name__					
								else:
									dir["value"] = gom.app.projects[p].measurements[m].get(keyword)
									dir["value_type"] = type(gom.app.projects[p].measurements[m].get(keyword)).__name__					
								dir["key_deu"] = beschreibung
								if description!=None:
									dir["key_eng"] = description
								if uri!=None:
									dir["uri"] = uri	
								if measurementclass!=None:
									dir["measurementclass"] = measurementclass		
								if einheit!=None:
									dir["unit"] = einheit
								if application!=None:
									dir["from_application"] = application
																																				
								if dir["value"] != None:				
									if len(str(dir["value"])) != 0:
										if includeonlypropswithuri and "uri" in dir:
											dic_measurement_setup[keyword] = {}		
											dic_measurement_setup[keyword] = dir
										if not includeonlypropswithuri:
											dic_measurement_setup[keyword] = {}		
											dic_measurement_setup[keyword] = dir
							except:
								print ("error")
								print(e)


						def measurements_check (beschreibung, description, keyword, einheit, uri, measurementclass, application):
							dir = {}
							dir.clear()		
							try:
								if keyword == "invert m_one_cam":
									dir["value"] = gom.app.projects[p].measurements[m].get('m_one_cam')
									if dir["value"] == True:
										dir["value"] = False
									if dir["value"] == False:
										dir["value"] = True
									dir["value_type"] = type(gom.app.projects[p].measurements[m].get('m_one_cam')).__name__					
								elif keyword == "invert m_shiny_points":
									dir["value"] = gom.app.projects[p].measurements[m].get('m_shiny_points')
									if dir["value"] == True:
										dir["value"] = False
									if dir["value"] == False:
										dir["value"] = True
									dir["value_type"] = type(gom.app.projects[p].measurements[m].get('m_shiny_points')).__name__					
								else:
									dir["value"] = gom.app.projects[p].measurements[m].get(keyword)
									dir["value_type"] = type(gom.app.projects[p].measurements[m].get(keyword)).__name__					
								dir["key_deu"] = beschreibung
								if description!=None:
									dir["key_eng"] = description
								if uri!=None:
									dir["uri"] = uri	
								if measurementclass!=None:
									dir["measurementclass"] = measurementclass		
								if einheit!=None:
									dir["unit"] = einheit
								if application!=None:
									dir["from_application"] = application
																																				
								if dir["value"] != None:				
									if len(str(dir["value"])) != 0:
										if includeonlypropswithuri and "uri" in dir:
											dic_measurement_check[keyword] = {}		
											dic_measurement_check[keyword] = dir
										if not includeonlypropswithuri:
											dic_measurement_check[keyword] = {}		
											dic_measurement_check[keyword] = dir
							except:			
								print ("error")					
								print(e)
											
						def infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application):
								dir = {}
								dir.clear()	
								try:
									if keyword == "invert_m_one_cam":
										dir["value"] = gom.app.projects[p].measurements[m].get('m_one_cam')
										if dir["value"] == True:
											dir["value"] = False
										if dir["value"] == False:
											dir["value"] = True
										dir["value_type"] = type(gom.app.projects[p].measurements[m].get('m_one_cam')).__name__
									elif keyword == "invert_m_shiny_points":
										dir["value"] = gom.app.projects[p].measurements[m].get('m_shiny_points')
										if dir["value"] == True:
											dir["value"] = False
										if dir["value"] == False:
											dir["value"] = True
										dir["value_type"] = type(gom.app.projects[p].measurements[m].get('m_shiny_points')).__name__
									elif keyword == "invert_m_col_trans":
										dir["value"] = gom.app.projects[p].measurements[m].get('m_col_trans')
										if dir["value"] == True:
											dir["value"] = False
										if dir["value"] == False:
											dir["value"] = True
										dir["value_type"] = type(gom.app.projects[p].measurements[m].get('m_col_trans')).__name__							
									elif keyword == "adapted_m_trafo_mode":
										dir["value"] = gom.app.projects[p].measurements[m].get('m_trafo_mode')
										if dir["value"] == "automatic":
											dir["value"] = "reference_points"
										dir["value_type"] = type(gom.app.projects[p].measurements[m].get('m_trafo_mode')).__name__	
									else:
										dir["value"] = gom.app.projects[p].measurements[m].get(keyword)
										dir["value_type"] = type(gom.app.projects[p].measurements[m].get(keyword)).__name__						
									dir["key_deu"] = beschreibung
									if description!=None:
										dir["key_eng"] = description
									if uri!=None:
										dir["uri"] = uri	
									if measurementclass!=None:
										dir["measurementclass"] = measurementclass			
									if einheit!=None:
										dir["unit"] = einheit
									if application!=None:
										dir["from_application"] = application

									if dir["value"] != None:				
										if len(str(dir["value"])) != 0:
											if includeonlypropswithuri and "uri" in dir:
												dic_measurement_info[keyword] = {}		
												dic_measurement_info[keyword] = dir
											if not includeonlypropswithuri:
												dic_measurement_info[keyword] = {}		
												dic_measurement_info[keyword] = dir
								except:
									print ("error")
									print(e)
							
						def cal_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application):
								dir = {}
								dir.clear()
								try:
									if keyword == 'm_cal_time':
										value = gom.app.projects[p].measurements[m].get(keyword)
										if value != None:
											capturetime = time.strptime(value, "%a %b %d %H:%M:%S %Y")
											dir["value"] = (time.strftime("%Y-%m-%dT%H:%M:%S",capturetime))
										else:
											dir["value"] = None
									else:
										dir["value"] = gom.app.projects[p].measurements[m].get(keyword)						
									if keyword == 'm_cal_time':
										dir["value_type"] = "dateTime"
									else:
										dir["value_type"] = type(gom.app.projects[p].measurements[m].get(keyword)).__name__
									dir["key_deu"] = beschreibung
									if description!=None:
										dir["key_eng"] = description
									if uri!=None:
										dir["uri"] = uri	
									if measurementclass!=None:
										dir["measurementclass"] = measurementclass			
									if einheit!=None:
										dir["unit"] = einheit
									if application!=None:
										dir["from_application"] = application

									if dir["value"] != None:				
										if len(str(dir["value"])) != 0:
											if includeonlypropswithuri and "uri" in dir:
												dic_measurement_cal[keyword]= {}		
												dic_measurement_cal[keyword]= dir
											if not includeonlypropswithuri:
												dic_measurement_cal[keyword]= {}		
												dic_measurement_cal[keyword]= dir
								except:
									print ("error")
									print(e)
											
						def cal_measurements_calobject (beschreibung, description, keyword, einheit, uri, measurementclass, application):
								dir = {}
								dir.clear()
								try:
									if keyword == 'm_cal_time':
										value = gom.app.projects[p].measurements[m].get(keyword)
										if value != None:
											capturetime = time.strptime(value, "%a %b %d %H:%M:%S %Y")
											dir["value"] = (time.strftime("%Y-%m-%dT%H:%M:%S",capturetime))
									else:
										dir["value"] = gom.app.projects[p].measurements[m].get(keyword)						
									if keyword == 'm_cal_time':
										dir["value_type"] = "dateTime"
									else:
										dir["value_type"] = type(gom.app.projects[p].measurements[m].get(keyword)).__name__
									dir["key_deu"] = beschreibung
									if description!=None:
										dir["key_eng"] = description
									if uri!=None:
										dir["uri"] = uri	
									if measurementclass!=None:
										dir["measurementclass"] = measurementclass
									if einheit!=None:
										dir["unit"] = einheit
									if application!=None:
										dir["from_application"] = application

									if dir["value"] != None:				
										if len(str(dir["value"])) != 0:
											if includeonlypropswithuri and "uri" in dir:
												dic_measurement_cal_calobject[keyword]= {}		
												dic_measurement_cal_calobject[keyword]= dir
											if not includeonlypropswithuri:
												dic_measurement_cal_calobject[keyword]= {}		
												dic_measurement_cal_calobject[keyword]= dir
								except:
									print ("error")
									print(e)


						def cal_measurements_calsetup (beschreibung, description, keyword, einheit, uri, measurementclass, application):
								dir = {}
								dir.clear()
								try:
									if keyword == 'm_cal_time':
										value = gom.app.projects[p].measurements[m].get(keyword)
										if value != None:
											capturetime = time.strptime(value, "%a %b %d %H:%M:%S %Y")
											dir["value"] = (time.strftime("%Y-%m-%dT%H:%M:%S",capturetime))
									else:
										dir["value"] = gom.app.projects[p].measurements[m].get(keyword)						
									if keyword == 'm_cal_time':
										dir["value_type"] = "dateTime"
									else:
										dir["value_type"] = type(gom.app.projects[p].measurements[m].get(keyword)).__name__
									dir["key_deu"] = beschreibung
									if description!=None:
										dir["key_eng"] = description
									if uri!=None:
										dir["uri"] = uri	
									if measurementclass!=None:
										dir["measurementclass"] = measurementclass
									if einheit!=None:
										dir["unit"] = einheit
									if application!=None:
										dir["from_application"] = application
																																				
									if dir["value"] != None:				
										if len(str(dir["value"])) != 0:
											if includeonlypropswithuri and "uri" in dir:
												dic_measurement_cal_calsetup[keyword]= {}		
												dic_measurement_cal_calsetup[keyword]= dir
											if not includeonlypropswithuri:
												dic_measurement_cal_calsetup[keyword]= {}		
												dic_measurement_cal_calsetup[keyword]= dir
								except:
									print ("error")
									print(e)


						def cal_measurements_calresults (beschreibung, description, keyword, einheit, uri, measurementclass, application):
								dir = {}
								dir.clear()
								try:
									if keyword == 'm_cal_time':
										value = gom.app.projects[p].measurements[m].get(keyword)																																								
										if value != None:
											capturetime = time.strptime(value, "%a %b %d %H:%M:%S %Y")
											dir["value"] = (time.strftime("%Y-%m-%dT%H:%M:%S",capturetime))
											dir["value_type"] = "dateTime"
										else:
											dir["value"] = value
											dir["value_type"] = type(value).__name__
								
									else:
										dir["value"] = gom.app.projects[p].measurements[m].get(keyword)
										dir["value_type"] = type(gom.app.projects[p].measurements[m].get(keyword)).__name__			

									dir["key_deu"] = beschreibung
									if description!=None:
										dir["key_eng"] = description
									if uri!=None:
										dir["uri"] = uri	
									if measurementclass!=None:
										dir["measurementclass"] = measurementclass
									if einheit!=None:
										dir["unit"] = einheit
									if application!=None:
										dir["from_application"] = application												

									if dir["value"] != None:				
										if len(str(dir["value"])) != 0:
											if includeonlypropswithuri and "uri" in dir:
												dic_measurement_cal_calresults[keyword]= {}		
												dic_measurement_cal_calresults[keyword]= dir
											if not includeonlypropswithuri:
												dic_measurement_cal_calresults[keyword]= {}		
												dic_measurement_cal_calresults[keyword]= dir
								except:
									print ("error")
									print(e)
								
						############ get values #############
								
						# Aktuelle Kameratemperatur
						beschreibung = "Aktuelle Kameratemperatur"
						description = None
						keyword = 'm_x2006_cam_temp_act'
						einheit = om+"degreeCelsius"
						uri = None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Anzahl der Belichtungen
						beschreibung = "Anzahl der Belichtungen"
						description = "Number of shutter times"
						keyword = 'm_shutter_times'
						einheit = None
						uri= ontologynamespace+"numberOfShutterTimes"
						measurementclass = None
						application = "true"
						measurements_setup (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Anzahl der Punkte
						beschreibung = "Anzahl der Punkte"
						description = None
						keyword = 'm_points'
						einheit = None
						uri= ontologynamespace+"numberOfPoints"
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
								
						# Anzahl der Referenzpunkte
						beschreibung = "Anzahl der Referenzpunkte"
						description = None
						keyword = 'm_num_rp'
						einheit = None
						uri= ontologynamespace+"numberOfReferencePoints"
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Anzahl der Transformationspunkte
						beschreibung = "Anzahl der Transformationspunkte"
						description = "Number of reference points"
						keyword = 'm_num_trafo_points'
						einheit = None
						uri= ontologynamespace+"numberOfTransformationPoints"
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Belichtungszeit 0
						beschreibung = "Belichtungszeit 0"
						description = "Shutter time"
						keyword = 'm_shutter_time0'
						einheit = om+"seconds-Time"
						uri= exifnamespace+'exposureTime'
						measurementclass = None
						application = "true"
						measurements_setup (beschreibung, description, keyword, einheit, uri, measurementclass, application)		
						
						# Belichtungszeit 1
						beschreibung = "Belichtungszeit 1"
						description = "Shutter time"
						keyword = 'm_shutter_time1'
						einheit = om+"seconds-Time"
						uri= exifnamespace+'exposureTime'
						measurementclass = None
						application = "true"
						measurements_setup (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Belichtungszeit 2
						beschreibung = "Belichtungszeit 2"
						description = "Shutter time"
						keyword = 'm_shutter_time2'
						einheit = om+"seconds-Time"
						uri= exifnamespace+'exposureTime'
						measurementclass = None
						application = "true"
						measurements_setup (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Belichtungszeit 3
						beschreibung = "Belichtungszeit 3"
						description = "Shutter time"
						keyword = 'm_shutter_time3'
						einheit = om+"seconds-Time"
						uri= exifnamespace+'exposureTime'
						measurementclass = None
						application = "true"
						measurements_setup (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Belichtungszeit 4
						beschreibung = "Belichtungszeit 4"
						description = "Shutter time"
						keyword = 'm_shutter_time4'
						einheit = om+"seconds-Time"
						uri= exifnamespace+'exposureTime'
						measurementclass = None
						application = "true"
						measurements_setup (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Belichtugnszeit 5
						beschreibung = "Belichtungszeit 5"
						description = "Shutter time"
						keyword = 'm_shutter_time5'
						einheit = om+"seconds-Time"
						uri= exifnamespace+'exposureTime'
						measurementclass = None
						application = "true"
						measurements_setup (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Belichtungszeit 6
						beschreibung = "Belichtungszeit 6"
						description = "Shutter time"
						keyword = 'm_shutter_time6'
						einheit = om+"seconds-Time"
						uri= exifnamespace+'exposureTime'
						measurementclass = None
						application = "true"
						measurements_setup (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Belichtungszeit Referenzpunkte
						beschreibung = "Belichtungszeit Referenzpunkte"
						description = "Reference points shutter time"
						keyword = 'm_ref_shutter'
						einheit = om+"seconds-Time"
						uri= ontologynamespace+"ExposureTimeForReferencePoints"
						measurementclass = None
						application = "true"
						measurements_setup (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Belichtungszeit Tapelinienbeleuchtung
						beschreibung = "Belichtungszeit Tapelinienbeleuchtung"
						description = None
						keyword = 'm_gray_shutter'
						einheit = om+"seconds-Time"
						uri= None
						measurementclass = None
						application = "true"
						measurements_setup (beschreibung, description, keyword, einheit, uri, measurementclass, application)
							
						# aus width wird length bei ATOS II						
						if gom.app.projects[p].measurements[m].get('m_sensor') == "atos 2":
							# Breite des Messvolumens
							beschreibung = "Länge Messvolumen"
							description = None
							keyword = 'm_vol_width'
							einheit = om+"millimetre"
							uri=ontologynamespace+"MeasuringVolumeLength"
							measurementclass = None
							application = "true"
							measurements_sensor (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						else:
							# Breite des Messvolumens
							beschreibung = "Breite des Messvolumens"
							description = None
							keyword = 'm_vol_width'
							einheit = om+"millimetre"
							uri=ontologynamespace+"MeasuringVolumeDepth"
							measurementclass = None
							application = "true"
							measurements_sensor (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Eckmaskierung
						beschreibung = "Eckmaskierung"
						description = "Corner mask size"
						keyword = 'm_corner_mask'
						einheit = om+"percent"
						uri= ontologynamespace+"CornerMask"
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Fehler während der Automatisierungsprotokoll-Ausführung
						beschreibung = "Fehler während der Automatisierungsprotokoll-Ausführung"
						description = None
						keyword = 'm_automation_error'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Gültige Kameratemperatur
						beschreibung = "Gültige Kameratemperatur"
						description = None
						keyword = 'm_x2006_cam_temp_valid'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Gültige Lampenaufwärmung
						beschreibung = "Gültige Lampenaufwärmung"
						description = None
						keyword = 'm_x2006_lamp_warmup_valid'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						measurements_check (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Höhe des Messvolumens			
						beschreibung = "Höhe des Messvolumens"
						description = None
						keyword = 'm_vol_height'
						einheit = om+"millimetre"
						uri=ontologynamespace+"MeasuringVolumeWidth"
						measurementclass = None
						application = "true"
						measurements_sensor (beschreibung, description, keyword, einheit, uri, measurementclass, application)
							
						# Kamera Betriebstemperatur
						beschreibung = "Kamera Betriebstemperatur"
						description = None
						keyword = 'm_x2006_cam_temp_nom'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
				
						# Kamerakennung (links)
						beschreibung = "Kamerakennung (links)"
						description = None
						keyword = 'm_camera_identifier_left'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Kamerakennung (rechts)
						beschreibung = "Kamerakennung (rechts)"
						description = None
						keyword = 'm_camera_identifier_right'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Kameratemperatur in Ordnung
						beschreibung = "Kameratemperatur in Ordnung"
						description = None
						keyword = 'm_x2006_cam_temp_ok'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Kameratyp
						beschreibung = "Kameratyp"
						description = None
						keyword = 'm_sensor_camera_type'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Kamerawinkel
						beschreibung = "Kamerawinkel"
						description = None
						keyword = 'm_camera_angle'
						einheit = om+"radian"
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Lichtfaktor
						beschreibung = "Lichtfaktor"
						description = None
						keyword = 'm_x2006_light_factor'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Lichtintensität
						beschreibung = "Lichtintensität"
						description = None
						keyword = 'm_x2006_brightness'
						einheit = om+"percent"
						uri= ontologynamespace+"LightIntensity"
						measurementclass = None
						application = "true"
						measurements_setup (beschreibung, description, keyword, einheit, uri, measurementclass, application)
				
						# Lichtänderung (linkes Bild)
						beschreibung = "Lichtänderung (linkes Bild)"
						description = None
						keyword = 'm_lighting_left'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						measurements_check (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Lichtänderung (rechtes Bild)
						beschreibung = "Lichtänderung (rechtes Bild)"
						description = None
						keyword = 'm_lighting_right'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						measurements_check (beschreibung, description, keyword, einheit, uri, measurementclass, application)
				
						# Länge Messvolumen
						## für ATOS II anpassen
						if gom.app.projects[p].measurements[m].get('m_sensor') == "atos 2":
							beschreibung = "Tiefe Messvolumen"
							description = None
							keyword = 'm_vol_length'
							einheit = om+"millimetre"
							uri=ontologynamespace+"MeasuringVolumeDepth"
							measurementclass = None
							application = "true"
							measurements_sensor (beschreibung, description, keyword, einheit, uri, measurementclass, application)		
						else:
							beschreibung = "Länge Messvolumen"
							description = None
							keyword = 'm_vol_length'
							einheit = om+"millimetre"
							uri=ontologynamespace+"MeasuringVolumeLength"
							measurementclass = None
							application = "true"
							measurements_sensor (beschreibung, description, keyword, einheit, uri, measurementclass, application)				
						
						# Messbeleuchtung
						beschreibung = "Messbeleuchtung"
						description = None
						keyword = 'm_measure_light'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Messung-Abweichung
						beschreibung = "Messung-Abweichung"
						description = None
						keyword = 'm_dev'
						einheit = om+"millimetre"
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Min. Modulationsschwelle (linkes Bild)
						beschreibung = "Min. Modulationsschwelle (linkes Bild)"
						description = "Min. Mask threshold (left image)"
						keyword = 'm_mod_left'
						einheit = "Grauwerte"
						uri= ontologynamespace+"MinimumFringeContrastLeftImage"
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						
						## Min. Modulationsschwelle (rechtes Bild) ####  ACHTUNG HIER IST FALSCHER WERT !!!!!!!! IST GLEICH "NAH ZUM SENSOR"
						#gom.app.projects['V14_022a.amp'].measurements['M1'].get ('m_mod_right')		
						
						# Nah zum Sensor
						beschreibung = "Nah zum Sensor"
						description = None
						keyword = 'm_depth_min'
						einheit = om+"millimetre"
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
				
						# Name der Messung
						beschreibung = "Name der Messung"
						description = "Measurement name"
						keyword = 'm_name'
						einheit = None
						uri= rdfs+"label"
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
				
						# Punkt ID - do not work !!!
				#		beschreibung = "Punkt ID"
				#		keyword = 'r_id' , 0
				#		infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
						# Punktekennzeichung (Messung) - do not work !!!
				#		beschreibung = "Punktekennzeichung (Messung)"
				#		keyword = 'r_state',0
				#		infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Punktekennzeichnung (Projekt) - do not work !!!
				#		beschreibung = "Punktekennzeichnung (Projekt)"
				#		keyword = 'r_pstate',0
				#		infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Referenzpunkt-Lichtquelle
						beschreibung = "Referenzpunkt-Lichtquelle"
						description = None
						keyword = 'm_ref_point_source'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Referenzpunktbeleuchtung
						beschreibung = "Referenzpunktbeleuchtung"
						description = None
						keyword = 'm_reference_light'
						einheit = om+"seconds-Time"
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Sekunden seit der letzten Lichtfaktorkalibrierung
						beschreibung = "Sekunden seit der letzten Lichtfaktorkalibrierung"
						description = None
						keyword = 'm_x2006_seconds_since_light_factor_calibration'
						einheit = om+"seconds-Time"
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
				
						# Sensorbewegung (linkes Bild)
						beschreibung = "Sensorbewegung (linkes Bild)"
						description = None
						keyword = 'm_movement_left'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						measurements_check (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Sensorbewegung (rechtes Bild)
						beschreibung = "Sensorbewegung (rechtes Bild)"
						description = None
						keyword = 'm_movement_right'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						measurements_check (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Sensorkennung
						beschreibung = "Sensorkennung"
						description = "Sensor identifier"
						keyword = 'm_sensor_identifier'
						einheit = None
						uri= ontologynamespace+"serialNumber"
						measurementclass="http://www.wikidata.org/entity/Q1198578"
						application = "true"
						measurements_sensor (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Sensormodell
						beschreibung = "Sensormodell"
						description = None
						keyword = 'm_sensor'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
						# Status: Daten von einzelner Kamera?
						beschreibung = "Status: Daten von einzelner Kamera?"
						description = "State: data from one camera only?"
						keyword = 'm_one_cam'
						einheit = None
						uri= ontologynamespace+"useTripleScanPoints"
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Status: Daten von einzelner Kamera? 
						# ** INVERTIERT **
						beschreibung = "Status: Triple-Scan-Punkte vermeiden?"
						description = "State: Avoid Triple Scan points?"
						keyword = "invert_m_one_cam"
						einheit = None
						uri= ontologynamespace+"avoidTripleScanPoints"
						measurementclass = None
						application = "true, inverted value from keyword = m_one_cam"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)			
						
						# Status: Kamera- und Sensorkennung gültig?
						beschreibung = "Status: Kamera- und Sensorkennung gültig?"
						description = None
						keyword = 'm_camera_sensor_identifier_valid'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Status: Lichtfaktorkalibrierung?
						beschreibung = "Status: Lichtfaktorkalibrierung?"
						description = None
						keyword = 'm_x2006_light_factor_calibrated'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Status: Messung transformiert?
						beschreibung = "Status: Messung transformiert?"
						description = None
						keyword = 'm_transformed'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Status: Projektorkalibrierung verwenden?
						beschreibung = "Status: Projektorkalibrierung verwenden?"
						description = None
						keyword = 'm_proj_calib'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Status: Punkt ist gemeinsamer Referenzpunk?  - do not work !!!		
				#		beschreibung = "Status: Punkt ist gemeinsamer Referenzpunk?"
				#		keyword = 'r_common', 0
				#		infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Status: Punkte an Glanzstellen berechnen?
						beschreibung = "Status: Punkte an Glanzstellen berechnen?"
						description = "State: use shiny points?"
						keyword = 'm_shiny_points'
						einheit = None
						uri=ontologynamespace+"usePointsOnShinyAreas"
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Status: Punkte an Glanzstellen berechnen?
						# ** INVERTIERT **
						beschreibung = "Status: Punkte auf Glanzstellen vermeiden?"
						description = "State: Avoid points on shiny surfaces?"
						keyword = 'invert_m_shiny_points'
						einheit = None
						uri=ontologynamespace+"avoidPointsOnShinyAreas"
						measurementclass = None
						application = "true, inverted value from keyword = m_shiny_points"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
									
						# Status: Punkte bei starkten Grauwertunterschieden berechnen?
						beschreibung = "Status: Punkte bei starkten Grauwertunterschieden berechnen?"
						description = "Status: use points at strong color transitions?"
						keyword = 'm_col_trans'
						einheit = None
						uri=ontologynamespace+"useStrongColorTransitionsPoints"
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Status: Punkte bei starkten Grauwertunterschieden berechnen?
						# ** INVERTIERT **
						beschreibung = "Status: Punkte bei starken Helligkeitsunterschieden vermeiden?"
						description = "State: Avoid points at strong brightness differences?"
						keyword = 'invert_m_col_trans'
						einheit = None
						uri= ontologynamespace+"avoidStrongBrightnessDifferencePoints"
						measurementclass = None
						application = "true, inverted value from keyword = m_col_trans"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Status: Tapelinienbeleuchtung verwendet?
						beschreibung = "Status: Tapelinienbeleuchtung verwendet?"
						description = None
						keyword = 'm_use_gray_shutter'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Status: kleinste Modulationsmaske verwenden (nur ATOS III) verwendet?
						beschreibung = "Status: kleinste Modulationsmaske verwenden (nur ATOS III) verwendet?"
						description = None
						keyword = 'm_smallest_mod_mask'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Statur: lange Dreiecke verwendet?
						beschreibung = "Statur: lange Dreiecke verwendet?"
						description = None
						keyword = 'm_long_tri'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Status: selektiert? - do not work !!!
				#		beschreibung = "Status: selektiert?"
				#		keyword = 'selected',0
				#		infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Tiefenbeschänkung
						beschreibung = "Tiefenbeschänkung"
						description = None
						keyword = 'm_depth'
						einheit = om+"millimetre"
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Transformationsmatrix der Messung
						beschreibung = "Transformationsmatrix der Messung"
						description = None
						keyword = 'm_trafo_matrix'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Transformationsmodus der Messung
						beschreibung = "Transformationsmodus der Messung"
						description = "Measurement transformation mode"
						keyword = 'm_trafo_mode'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
									
						# Transformationsmodus der Messung
						# ** INVERTIERT **
						beschreibung = "Transformationsmethode"
						description = "Transformation method"
						keyword = 'adapted_m_trafo_mode'
						einheit = None
						uri= ontologynamespace+"measurementTransformationMethod"
						measurementclass = None
						application = "true, adapted value from keyword = m_trafo_mode"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Verbleibende Lampenaufwärmzeit
						beschreibung = "Verbleibende Lampenaufwärmzeit"
						description = None
						keyword = 'm_x2006_lamp_warmup_rem_sec'
						einheit = om+"seconds-Time"
						uri= None
						measurementclass = None
						application = "true"
						measurements_check (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Vorschau-Raster
						beschreibung = "Vorschau-Raster"
						description = None
						keyword = 'm_raster'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Weiter entfernt vom Sensor
						beschreibung = "Weiter entfernt vom Sensor"
						description = None
						keyword = 'm_depth_max'
						einheit = om+"millimetre"
						uri= None
						measurementclass = None
						application = "true"
						infos_measurements (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Anzahl der Kameras
						beschreibung = "Anzahl der Kameras"
						description = "Number of cameras"
						keyword = 'm_cal_num_cameras'
						einheit = None
						uri = ontologynamespace+"numberOfCameras"
						measurementclass = None
						application = "true"
						measurements_sensor (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Anzahl der Maßstäbe
						beschreibung = "Anzahl der Maßstäbe"
						description = "Number of scales"
						keyword = 'm_cal_num_scales'
						einheit = None
						uri=ontologynamespace+"numberOfScales"
						measurementclass = None
						application = "true"
						cal_measurements_calobject (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Aufnahmemodus
						beschreibung = "Aufnahmemodus"
						description = None
						keyword = 'm_cal_snap_mode'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						cal_measurements_calsetup (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Ausdehnungskoeffizient
						beschreibung = "Ausdehnungskoeffizient"
						description = None
						keyword = 'm_cal_exp_coeff'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						cal_measurements_calobject  (beschreibung, description, keyword, einheit, uri, measurementclass, application)
				
						# Breite des Messvolumens
						# für ATOS II anpassen
						### HIER
						if (gom.app.projects[p].measurements[m].get('m_sensor') == "atos 2") and (gom.app.projects[p].measurements[m].get('m_cal_sensor_width') == None):
							beschreibung = "Länge des Messvolumens"
							description = "Measurement volume length"
							keyword = 'm_vol_width'
							einheit = om+"millimetre"
							uri=ontologynamespace+"CalibrationVolumeLength"
							measurementclass = None
							application = "true"
							cal_measurements_calresults  (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						else:
							beschreibung = "Länge des Messvolumens"
							description = "Measurement volume length"
							keyword = 'm_cal_sensor_width'
							einheit = om+"millimetre"
							uri=ontologynamespace+"CalibrationVolumeDepth"
							measurementclass = None
							application = "true"
							cal_measurements_calresults  (beschreibung, description, keyword, einheit, uri, measurementclass, application)
							
						# Datum der Kalibrierung
						beschreibung = "Datum der Kalibrierung"
						description = "Calibration date"
						keyword = 'm_cal_time'
						einheit = None
						uri = ontologynamespace+"CalibrationDate"
						measurementclass = None
						application = "true"
						cal_measurements_calresults (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Höhe des Messvolumens
						if (gom.app.projects[p].measurements[m].get('m_sensor') == "atos 2") and (gom.app.projects[p].measurements[m].get('m_cal_sensor_width') == None):
							beschreibung = "Höhe des Messvolumens"
							description = "Measurement volume height"
							keyword = 'm_vol_height'
							einheit = om+"millimetre"
							uri=ontologynamespace+"CalibrationVolumeWidth"
							measurementclass = None
							application = "true"
							cal_measurements_calresults  (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						else:
							beschreibung = "Höhe des Messvolumens"
							description = "Measurement volume height"
							keyword = 'm_cal_sensor_height'
							einheit = om+"millimetre"
							uri=ontologynamespace+"CalibrationVolumeWidth"
							measurementclass = None
							application = "true"
							cal_measurements_calresults  (beschreibung, description, keyword, einheit, uri, measurementclass, application)
									
						# Höhenänderung
						beschreibung = "Höhenänderung"
						description = "Height variance"
						keyword = 'm_cal_var_height'
						einheit = om+"millimetre"
						uri= ontologynamespace+"HeightVariance"
						measurementclass = None
						application = "true"
						cal_measurements_calresults  (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Identifizierungspunkt-ID
						beschreibung = "Identifizierungspunkt-ID"
						description = None
						keyword = 'm_cal_obj_id'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						cal_measurements_calobject (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Kalibrierabweichung
						beschreibung = "Kalibrierabweichung"
						description = "Calibration deviation"
						keyword = 'm_cal_residual'
						einheit = om+"millimetre"
						uri= ontologynamespace+"CalibrationDeviation"
						measurementclass = None
						application = "true"
						cal_measurements_calresults  (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Kalibrierobjekt
						beschreibung = "Kalibrierobjekt"
						description = None
						keyword = 'm_cal_obj_type'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						cal_measurements_calobject (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Lichtintensität
						beschreibung = "Lichtintensität"
						description = None
						keyword = 'm_cal_light_intensity'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						cal_measurements_calsetup (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Max. Winkel
						beschreibung = "Max. Winkel"
						description = None
						keyword = 'm_cal_max_angle'
						einheit = om+"radian"
						uri= None
						measurementclass = None
						application = "true"
						cal_measurements_calresults (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Maßstabsabweichung
						beschreibung = "Maßstabsabweichung"
						description = "scale deviation"
						keyword = 'm_cal_scale_dev'
						einheit = om+"millimetre"
						uri=ontologynamespace+"ScaleDeviation"
						measurementclass = None
						application = "true"
						cal_measurements_calresults  (beschreibung, description, keyword, einheit, uri, measurementclass, application)
				
						# Messtemperatur
						beschreibung = "Messtemperatur"
						description = "Measurement temperature"
						keyword = 'm_cal_temp'
						einheit = om+"degreeCelsius"
						uri= ontologynamespace+"CalibrationTemperature"
						measurementclass = None
						application = "true"
						cal_measurements_calobject (beschreibung, description, keyword, einheit, uri, measurementclass, application)	
					
						# Min. Winkel
						beschreibung = "Min. Winkel"
						description = None
						keyword = 'm_cal_min_angle'
						einheit = om+"radian"
						uri= None
						measurementclass = None
						application = "true"
						cal_measurements_calresults (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Name
						beschreibung = "Name"
						description = "Name"
						keyword = 'm_cal_obj_name'
						einheit = None
						uri= ontologynamespace+"calibrationObjectName"
						measurementclass = None
						application = "true"
						cal_measurements_calobject (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Objektiv
						beschreibung = "Objektiv"
						description = "Camera lenses"
						keyword = 'm_cal_lense'
						einheit = om+"millimetre"
						measurementclass="http://www.wikidata.org/entity/Q193540"
						uri= ontologynamespace+"FocalLengthCamera"
						application = "true"
						measurements_sensor (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Retro-Kalibrierung
						beschreibung = "Retro-Kalibrierung"
						description = None
						keyword = 'm_cal_retro'
						einheit = None
						uri= None
						measurementclass = None
						application = "true"
						cal_measurements_calresults (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Schnellkalibrierung
						beschreibung = "Schnellkalibrierung"
						description = None
						keyword = 'm_cal_quick'
						einheit = None
						uri= ontologynamespace+"isQuickCalibrated"
						measurementclass = None
						application = "true"
						cal_measurements_calresults (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Tiefe des Messvolumens
						### Anpassen für ATOS II
						if (gom.app.projects[p].measurements[m].get('m_sensor') == "atos 2") and (gom.app.projects[p].measurements[m].get('m_cal_sensor_width') == None):
							beschreibung = "Tiefe des Messvolumens"
							description = "Measurement volume depth"
							keyword = 'm_vol_length'
							einheit = om+"millimetre" 
							uri=ontologynamespace+"CalibrationVolumeDepth"
							measurementclass = None
							application = "true"
							cal_measurements_calresults  (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						else:
							beschreibung = "Tiefe des Messvolumens"
							description = "Measurement volume depth"
							keyword = 'm_cal_sensor_depth'
							einheit = om+"millimetre" 
							uri=ontologynamespace+"CalibrationVolumeLength"
							measurementclass = None
							application = "true"
							cal_measurements_calresults  (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Triangulationswinkel
						beschreibung = "Triangulationswinkel"
						description = "Camera angle"
						keyword = 'm_cal_cam_angle'
						einheit = om+"radian" 
						uri=ontologynamespace+"CameraAngle"
						measurementclass = None
						application = "true"
						cal_measurements_calresults  (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						# Zertifizierungstemperatur
						beschreibung = "Zertifizierungstemperatur"
						description = "Certification temperature"
						keyword = 'm_cal_ref_temp'
						einheit = om+"degreeCelsius" 
						uri=ontologynamespace+"ReferenceTemperature"
						measurementclass = None
						application = "true"
						cal_measurements_calobject (beschreibung, description, keyword, einheit, uri, measurementclass, application)
						
						
						#### additional_infos ####
						#### INFOS die nicht mit dem Skript abgegriffen werden können ####

						# image_width			
						def additional_infos_sensor (beschreibung, description, value, keyword, einheit, uri, measurementclass, application):
							dir = {}
							dir.clear()
							dir["value"] = value
							dir["key_deu"] = beschreibung
							if description!=None:
								dir["key_eng"] = description		
							if uri!=None:
								dir["uri"] = uri	
							if measurementclass!=None:
								dir["measurementclass"] = measurementclass			
							dir["value_type"] = type(dir["value"]).__name__
							if einheit!=None:
								dir["unit"] = einheit
							if application!=None:
								dir["from_application"] = application
								
							if dir["value"] != None:				
								if len(str(dir["value"])) != 0:
									if includeonlypropswithuri and "uri" in dir:
										dic_measurement_sensor[keyword]= {}		
										dic_measurement_sensor[keyword]= dir
									if not includeonlypropswithuri:
										dic_measurement_sensor[keyword]= {}		
										dic_measurement_sensor[keyword]= dir
						
						def additional_infos (beschreibung, description, value, keyword, einheit, uri, measurementclass, application):
							dir = {}
							dir.clear()
							dir["value"] = value
							dir["key_deu"] = beschreibung
							if description!=None:
								dir["key_eng"] = description		
							if uri!=None:
								dir["uri"] = uri	
							if measurementclass!=None:
								dir["measurementclass"] = measurementclass	
							if keyword == "acquisition_time":
								dir["value_type"] = "dateTime"
							else:
								dir["value_type"] = type(dir["value"]).__name__
							if einheit!=None:
								dir["unit"] = einheit
							if application!=None:
								dir["from_application"] = application

							if dir["value"] != None:				
								if len(str(dir["value"])) != 0:
									if includeonlypropswithuri and "uri" in dir:
										dic_measurement_info[keyword]= {}		
										dic_measurement_info[keyword]= dir
									if not includeonlypropswithuri:
										dic_measurement_info[keyword]= {}		
										dic_measurement_info[keyword]= dir
						
							
						def additional_info_setup (beschreibung, description, value, keyword, einheit, uri, measurementclass, application):
							dir = {}
							dir.clear()
							dir["value"] = value
							dir["key_deu"] = beschreibung
							if description!=None:
								dir["key_eng"] = description		
							if uri!=None:
								dir["uri"] = uri	
							if measurementclass!=None:
								dir["measurementclass"] = measurementclass	
							if keyword == "acquisition_time":
								dir["value_type"] = "dateTime"
							else:
								dir["value_type"] = type(dir["value"]).__name__
							if einheit!=None:
								dir["unit"] = einheit
							if application!=None:
								dir["from_application"] = application
								
							if dir["value"] != None:				
								if len(str(dir["value"])) != 0:
									if includeonlypropswithuri and "uri" in dir:
										dic_measurement_setup[keyword]= {}		
										dic_measurement_setup[keyword]= dir
									if not includeonlypropswithuri:
										dic_measurement_setup[keyword]= {}		
										dic_measurement_setup[keyword]= dir
						
					
						# Für die Bildbreite und den Sensortyp muss klar sein welcher Scanner verwendet wurde	
					
						# wenn sensortyp = atos II dann wird folgendes übertragen						
						if (gom.app.projects[p].measurements[m].get('m_sensor') == "atos 2") and (gom.app.projects[p].measurements[m].get('m_sensor_identifier') == None):
							
							# sensor_type
							beschreibung = "Sensortyp"
							description = "Sensor type"
							value = "ATOS II (first generation)"
							keyword = "sensor_type"
							einheit = None
							uri = ontologynamespace+"sensorType"
							measurementclass = None
							application = "false"	
							additional_infos_sensor (beschreibung, description, value, keyword, einheit, uri, measurementclass, application)
							
							# Bildbreite
							beschreibung = "Bildbreite"
							description = "Image width"
							value = int("1280")
							keyword = "image_width"
							einheit = om+"pixel"
							uri = exifnamespace+"imageWidth"
							measurementclass = None
							dic = dic_measurement_info		
							application = "false"	
							additional_info_setup (beschreibung, description, value, keyword, einheit, uri, measurementclass, application)
							
							# Bildhöhe
							beschreibung = "Bildhöhe"
							description = "Image height"
							value = int("1024")
							keyword = "image_height"
							einheit = om+"pixel"
							uri = exifnamespace+"imageHeight"
							measurementclass = None
							dic = dic_measurement_info
							application = "false"			
							additional_info_setup (beschreibung, description, value, keyword, einheit, uri, measurementclass, application)
							
							# kalibriertes Messvolumen ist bei ATOS II leer, kann aber von dem vordefinierten übernommen werden
							# wobei das vordefinierte erstmal neue uri bekommen muss....
							beschreibung = "Bildhöhe"
							description = "Image height"
							value = int("1024")
							keyword = "image_height"
							einheit = om+"pixel"
							uri = exifnamespace+"imageHeight"
							measurementclass = None
							dic = dic_measurement_info
							application = "false"			
							additional_info_setup (beschreibung, description, value, keyword, einheit, uri, measurementclass, application)
							
							
						# wenn seriennummer = "D08061" dann ist es ATOS III Rev. 01 und folgendes wird übertragen:			
						if gom.app.projects[p].measurements[m].get ('m_sensor_identifier') == "D08061":
							
							# sensor_type
							beschreibung = "Sensortyp"
							description = "Sensor type"
							value = "ATOS III Rev.01"
							keyword = "sensor_type"
							einheit = None
							uri = ontologynamespace+"sensorType"
							measurementclass = None
							application = "false"	
							additional_infos_sensor (beschreibung, description, value, keyword, einheit, uri, measurementclass, application)
							
							# Bildbreite
							beschreibung = "Bildbreite"
							description = "Image width"
							value = int("2048")
							keyword = "image_width"
							einheit = om+"pixel"
							uri = exifnamespace+"imageWidth"
							measurementclass = None
							dic = dic_measurement_info		
							application = "false"	
							additional_info_setup (beschreibung, description, value, keyword, einheit, uri, measurementclass, application)
							
							# Bildhöhe
							beschreibung = "Bildhöhe"
							description = "Image height"
							value = int("2048")
							keyword = "image_height"
							einheit = om+"pixel"
							uri = exifnamespace+"imageHeight"
							measurementclass = None
							dic = dic_measurement_info
							application = "false"			
							additional_info_setup (beschreibung, description, value, keyword, einheit, uri, measurementclass, application)
							
				
						# Aufnahmezeitpunkt
						m_file = gom.app.projects[p].get ('prj_directory') + "\\measurements\\" + gom.app.projects[p].measurements[m].get ('m_name') + ".atos"
						capturetime = time.ctime(os.path.getmtime(m_file)) 
						capturetime = time.strptime(capturetime, "%a %b %d %H:%M:%S %Y")
						capturetime = (time.strftime("%Y-%m-%dT%H:%M:%S",capturetime))
						
						beschreibung = "Aufnahmezeit"
						description = "Acquisition time"
						value = capturetime
						keyword = "acquisition_time"
						einheit = None
						uri = ontologynamespace+'acquisitionTime'
						measurementclass = None
						dic = dic_measurement_info
						application = "false"			
						additional_infos (beschreibung, description, value, keyword, einheit, uri, measurementclass, application)
							
					
						########################  REFERENZPUNKTE #############################################################################################
						
						# einzelne einzelne Referenzpunkte
						list_refpoints = []			
						rp = 0	
						
						while rp < len(gom.app.projects[p].measurements[m].ref_points):
							dic_refpoint = {}			
						
							def infos_refpoints (beschreibung, description, keyword, einheit, uri, measurementclass, application):
									dir = {}
									dir.clear()
									try:
										dir["value"] = gom.app.projects[p].measurements[m].ref_points[rp].get(keyword)
										dir["key_deu"] = beschreibung
										if description!=None:
											dir["key_eng"] = description
										if uri!=None:
											dir["uri"] = uri	
										if measurementclass!=None:
											dir["measurementclass"] = measurementclass			
										dir["value_type"] = type(gom.app.projects[p].measurements[m].ref_points[rp].get(keyword)).__name__
										if einheit!=None:
											dir["unit"] = einheit
										if application!=None:
											dir["from_application"] = application
																																												
										if dir["value"] != None:				
											if len(str(dir["value"])) != 0:
												if includeonlypropswithuri and "uri" in dir:
													dic_refpoint[keyword]= {}		
													dic_refpoint[keyword]= dir
												if not includeonlypropswithuri:
													dic_refpoint[keyword]= {}		
													dic_refpoint[keyword]= dir
									except:
										print ("error")
										print(e)
									
							############ get values #############
						
							# Punkt ID
							beschreibung = "Punkt ID"
							description = "Point ID"
							keyword = 'r_id'
							einheit = None
							uri = ontologynamespace+'PointID'
							measurementclass = None
							application = "true"
							infos_refpoints (beschreibung, description, keyword, einheit, uri, measurementclass, application)

							# Punktekennzeichnung (Messung)
							beschreibung = "Punktekennzeichnung (Messung)"
							description = "Point flags (measurement)"
							keyword = 'r_state'
							einheit = None
							uri= ontologynamespace+'PointMeasurementState'
							measurementclass = None
							application = "true"
							infos_refpoints (beschreibung, description, keyword, einheit, uri, measurementclass, application)
							
							# Punktekennzeichnung (Project)
							beschreibung = "Punktekennzeichnung (Project)"
							description = "Point flags (project)"
							keyword = 'r_pstate'
							einheit = None
							uri= ontologynamespace+'PointProjectState'
							measurementclass = None
							application = "true"
							infos_refpoints (beschreibung, description, keyword, einheit, uri, measurementclass, application)

							# Status: Punkt ist gemeinsamer Referenzpunkt?
							beschreibung = "Status: Punkt ist gemeinsamer Referenzpunkt?"
							description = "State: point is common ref.point?"
							keyword = 'r_common'
							einheit = None
							uri= ontologynamespace+'commonReferencepoint'
							measurementclass = None
							application = "true"
							infos_refpoints (beschreibung, description, keyword, einheit, uri, measurementclass, application)

							# Status: selektiert?
							beschreibung = "Status: selektiert?"
							description = "State: selected?"
							keyword = 'selected'
							einheit = None
							uri= None
							measurementclass = None
							application = "true"
							infos_refpoints (beschreibung, description, keyword, einheit, uri, measurementclass, application)
							
							# x-coordinate
							beschreibung = "x-Koordinate"
							description = "x-coordinate"
							keyword = 'r_x'
							einheit = om+"millimetre"
							uri= ontologynamespace+'xCoordinate'
							measurementclass = None
							application = "true"
							infos_refpoints (beschreibung, description, keyword, einheit, uri, measurementclass, application)
							
							# y-coordinate
							beschreibung = "y-Koordinate"
							description = "y-coordinate"
							keyword = 'r_y'
							einheit = om+"millimetre"
							uri= ontologynamespace+'yCoordinate'
							measurementclass = None
							application = "true"
							infos_refpoints (beschreibung, description, keyword, einheit, uri, measurementclass, application)
							
							# z-coorinate
							beschreibung = "z-Koordinate"
							description = "z-coordinate"
							keyword = 'r_z'
							einheit = om+"millimetre"
							uri= ontologynamespace+'zCoordinate'
							measurementclass = None
							application = "true"
							infos_refpoints (beschreibung, description, keyword, einheit, uri, measurementclass, application)
							
							# Point deviation
							beschreibung = "Punktabweichung"
							description = "Point deviation"
							keyword = 'r_dev'
							einheit = om+"millimetre"
							uri= ontologynamespace+'PointMeasurementDeviation'
							measurementclass = None
							application = "true"
							infos_refpoints (beschreibung, description, keyword, einheit, uri, measurementclass, application)
				
							if len(dic_refpoint) > 0:
								list_refpoints.append(dic_refpoint)	
								
							rp = rp + 1	
							
							
						if len(dic_measurement_cal_calobject) > 0:
							dic_measurement_cal["cal_object"] = dic_measurement_cal_calobject
						if len(dic_measurement_cal_calsetup) > 0:
							dic_measurement_cal["cal_setup"] = dic_measurement_cal_calsetup
						if len(dic_measurement_cal_calresults) > 0:
							dic_measurement_cal["cal_properties"] = dic_measurement_cal_calresults


						### theroretischer Messpunktabstand		
						if 'sensor_type' in dic_measurement_sensor:
							st = (dic_measurement_sensor['sensor_type']['value'])
							
							## "ATOS III Rev.01"
							if st == "ATOS III Rev.01":
								value = None
								mv_length = gom.app.projects[p].measurements[m].get('m_vol_length')
								# MV 30
								if 27 < mv_length < 33:
									value = 0.02
								# MV 65
								elif 58 < mv_length < 72 :
									value = 0.03
								# MV 100
								elif 90 < mv_length < 110:
									value = 0.05
								# MV 150
								elif 135 < mv_length < 165:
									value = 0.07
								# MV 300
								elif 270 < mv_length < 330:
									value = 0.15
								# MV 500
								elif 450 < mv_length < 550:
									value = 0.25
								# MV 1000
								elif 900 < mv_length < 1100:
									value = 0.50								
								# MV 1500
								elif 1350 < mv_length < 1650:
									value = 0.75
								# MV 2000
								elif 1800 < mv_length < 2200:
									value = 1.00

								# Länge Messvolumen
								value = value
								beschreibung = 'Theoretischer Messpunktabstand'
								description = 'theoretical measuring point distance'
								keyword = 'theoretical_measuring_point_distance'
								einheit = om+"millimetre"
								uri=ontologynamespace+'TheoreticalMeasuringPointDistance'
								measurementclass = None
								application = 'derived from the used measuring volume'
								measurements_sensor (beschreibung, description, keyword, einheit, uri, measurementclass, application, value)			
							
							elif st == "ATOS II (first generation)":
								value = None
								# hier muss nach width gefragt werden, ansonsten gleich
								mv_length = gom.app.projects[p].measurements[m].get('m_vol_width')
								# MV 100
								if 90 < mv_length < 110:
									value = 0.07
								# MV 35
								elif 31 < mv_length < 39:
									value = 0.03
								# MV 270
								elif 250 < mv_length < 290:
									value = 0.21
								# MV 730
								elif 700 < mv_length < 760:
									value = 0.60
							

								# Länge Messvolumen
								value = value
								beschreibung = 'Theoretischer Messpunktabstand'
								description = 'theoretical measuring point distance'
								keyword = 'theoretical_measuring_point_distance'
								einheit = om+"millimetre"
								uri=ontologynamespace+'TheoreticalMeasuringPointDistance'
								measurementclass = None
								application = 'derived from the used measuring volume'
								measurements_sensor (beschreibung, description, keyword, einheit, uri, measurementclass, application, value)		

						dic_sensor["calibration"] = dic_measurement_cal
						dic_sensor["capturing_device"] = dic_measurement_sensor
						
						
						
						########### calibratino NEW ##############
					
						# temporäre Vergleichsliste mit allen Kalibrierzeiten anlegen und wenn noch nicht in Liste "temp_list_cal_time", dann rein einen "sensor" anlegen
						if "m_cal_time" in dic_measurement_cal_calresults:
							cal_time_new = dic_measurement_cal_calresults["m_cal_time"]["value"]
						else:
							cal_time_new = None

						# schauen ob aktuelle Kalibrierungszeit schon in der Liste ist
						# wenn ja, dann die sensor_id abgreifen und der aktuellen Messung hinzufügen
						if cal_time_new in temp_list_cal_time:
							for s in list_sensors:
								if "calibration" in s:
									if "cal_properties" in s["calibration"]:
										if "m_cal_time" in s["calibration"]["cal_properties"]:
											if "value" in s["calibration"]["cal_properties"]["m_cal_time"]:
												cal_time_store = s["calibration"]["cal_properties"]["m_cal_time"]["value"] # Zeiten die schon in temp. liste gespeichert sind
												if cal_time_store == cal_time_new:  # wenn gleich, dann ...
													dic_measurement_info["sensor_id"] = s["capturing_device"]["sensor_id"] #sensor_id abgreifen und der aktuellen Messung hinzufügen
							
							
						# wenn Kalibrierungszeit noch in in Liste, dann 
						# neue sensor_id erzeugen und zu den sensor-informationen / kalibrierungen hinzufügen
						if not cal_time_new in temp_list_cal_time:		
							temp_list_cal_time.append(cal_time_new)
							
							# sensor_id zu dic_sensor hinzufügen
							dic_s = {}
							
							dic_s["value"] = sensor_id
							dic_s["key_deu"] = "Sensor ID"
							dic_s["from_application"] = "false"
							dic_s["key_eng"] = "sensor ID"
							dic_s["uri"]= ontologynamespace+'sensor_id'
							dic_s["value_type"] = type(dic_s["value"]).__name__
							
							dic_sensor["capturing_device"]["sensor_id"] = dic_s
							
							# sensor_id zu Messung hinzufügen
							dic_measurement_info["sensor_id"] = dic_s
							
							# sensor_id hochzählen
							sensor_id =+1
							
							# alles zu "sensor_lise" hinzufügen
							list_sensors.append(dic_sensor)


						
						#### Merge Dictonaries #####
				
							
						if len(dic_measurement_setup) > 0:
							dic_measurement["measurement_setup"] = dic_measurement_setup
						if len(dic_measurement_check) > 0:
							dic_measurement["measurement_check"] = dic_measurement_check
						if len(dic_measurement_info) > 0:
							dic_measurement["measurement_properties"] = dic_measurement_info
						
						if len(list_refpoints) > 0:
							dic_measurement["referencepoints"] = list_refpoints
						
						if len(dic_measurement) > 0:
							list_measurements.append(dic_measurement)
						m = m + 1
					
					if len(dic_prj_info) > 0:
						dic_project["measurement_series_information"] = dic_prj_info
					if len(list_measurements) > 0:
						dic_project["measurements"] = list_measurements

					dic_project["sensors"] = list_sensors
					
					dic_gp2 = {}
					if len(list_grp) > 0:
						dic_gp2["referencepoints"] = list_grp
					if len(dic_gp2) > 0:
						dic_project["global_referencepoints"] = dic_gp2
					
					if len(dic_project) > 0:
						list_projects.append(dic_project)
						
					p = p + 1
					
					

				
				###################### MESHES ######################
				
				list_meshes = []	
				me = 0
				while me < len( gom.app.meshes):
					dic_mesh = {}
					dic_mesh_info = {}
					list_mesh_processing = []
					dic_mesh_processing = {}
					str_mesh_processing_poly = None
					dic_mesh_processing_poly = {}
					dic_mesh_processing_poly_setup = {}
					list_mesh_processing_poly_post = []
					dic_mesh_processing_poly_post = {}	
					
					def infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application, value=None):
						dir = {}
						dir.clear()
						try:
							if keyword == "comment":
								c = gom.app.meshes[me].get(keyword)
								dir["value"] = c.replace("\n",", ")
							elif value == None:
								dir["value"] = gom.app.meshes[me].get(keyword)
							else:
								dir["value"] = value		
							dir["key_deu"] = beschreibung
							if description!=None:
								dir["key_eng"] = description		
							if uri!=None:
								dir["uri"] = uri	
							if measurementclass!=None:
								dir["measurementclass"] = measurementclass
																																
							if value == None:
								dir["value_type"] = type(gom.app.meshes[me].get(keyword)).__name__
							else:	
								dir["value_type"] = type(value).__name__
																																
							if einheit!=None:
								dir["unit"] = einheit
							if application!=None:
								dir["from_application"] = application
																																
							if dir["value"] != None:				
								if len(str(dir["value"])) != 0:
									if includeonlypropswithuri and "uri" in dir:
										dic_mesh_info[keyword]= {}		
										dic_mesh_info[keyword]= dir
									if not includeonlypropswithuri:
										dic_mesh_info[keyword]= {}		
										dic_mesh_info[keyword]= dir
						except:
							print ("error")
							print(e)
					
					###############################################
					
					# Anzahl der Dreiecke
					beschreibung = "Anzahl der Dreiecke"
					description = "Number of triangles"
					keyword = "num_triangles"
					einheit = None
					uri= giganamespace+"TotalNumberOfFaces"
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)
				
					# Anzahl der Punkte
					beschreibung = "Anzahl der Punkte"
					description = "Number of points"
					keyword = "num_points"
					einheit = None
					uri=giganamespace+"TotalNumberOfVertices"
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)
							
					# Belichtungszeiteinheit
					beschreibung = "Belichtungszeiteinheit"
					description = None
					keyword = "u_shutter"
					einheit = om+"seconds-Time"
					uri= None
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)	
					
					# Fläche
					beschreibung = "Fläche"
					description = "Area"
					keyword = "area"
					einheit = om+"squareMillimetre"
					uri=giganamespace+"TotalArea"
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)	
					
					# Fläche (selektiert)
					beschreibung = "Fläche (selektiert)"
					description = None
					keyword = "selected_area"
					einheit = om+"squareMillimetre"
					uri= None
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Flächeneinheit
					beschreibung = "Flächeneinheit"
					description = None
					keyword = "u_area"
					einheit = None
					uri= None
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Inaktiv-Grund
					beschreibung = "Inaktiv-Grund"
					description = None
					keyword = "inact_reason"
					einheit = None
					uri= None
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)

					# Kommentar
					beschreibung = "Kommentar"
					description = "comment"
					keyword = "comment"
					einheit = None
					uri= None
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Längeneinheit
					beschreibung = "Längeneinheit"
					description = None
					keyword = "u"
					einheit = None
					uri= None
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Materialstärke
					beschreibung = "Materialstärke"
					description = None
					keyword = "off"
					einheit = om+"millimetre"
					uri= None
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)

					# Max. X-Grenze
					beschreibung = "Max. X-Grenze"
					description = "Max. X limit"
					keyword = "boundb_maxx"
					einheit = om+"millimetre"
					uri= giganamespace+"MaximumXCoordinate"
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Max. Y-Grenze
					beschreibung = "Max. Y-Grenze"
					description = "Max. Y limit"
					keyword = "boundb_maxy"
					einheit = om+"millimetre"
					uri= giganamespace+"MaximumYCoordinate"
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)	
					
					# Max. Z-Grenze
					beschreibung = "Max. Z-Grenze"
					description = "Max. Z limit"
					keyword = "boundb_maxz"
					einheit = om+"millimetre"
					uri= giganamespace+"MaximumZCoordinate"
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)	
					
					# Min. X-Grenze
					beschreibung = "Min. X-Grenze"
					description = "Min. X limit"
					keyword = "boundb_minx"
					einheit = om+"millimetre"
					uri= giganamespace+"MinimumXCoordinate"
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Min. Y-Grenze
					beschreibung = "Min. Y-Grenze"
					description = "Min. Y limit"
					keyword = "boundb_miny"
					einheit = om+"millimetre"
					uri= giganamespace+"MinimumYCoordinate"
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Min. Z-Grenze
					beschreibung = "Min. Z-Grenze"
					description = "Min. Z limit"
					keyword = "boundb_minz"
					einheit = om+"millimetre"
					uri= giganamespace+"MinimumZCoordinate"
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Name
					beschreibung = "Name"
					description = "Name"
					keyword = "n"
					einheit = None
					uri= rdfs+"label"
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Punktindex
				#	gom.app.meshes["V14_022a_1_1"].get ("id", 0)
					
					# Reporteinheit
					beschreibung = "Reporteinheit"
					description = None
					keyword = "u_figure"
					einheit = None
					uri= None
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Status: Gegenseite messen?
					beschreibung = "Status: Gegenseite messen?"
					description = None
					keyword = "uoff"
					einheit = None
					uri= None
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Status: Referenz?
					beschreibung = "Status: Referenz?"
					description = None
					keyword = "is_ref"
					einheit = None
					uri= None
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Status: aktiv?
					beschreibung = "Status: aktiv?"
					description = None
					keyword = "is_active"
					einheit = None
					uri= None
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Status: inaktiv?
					beschreibung = "Status: inaktiv?"
					description = None
					keyword = "is_inact"
					einheit = None
					uri= None
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Status: selektiert?
					beschreibung = "Status: selektiert?"
					description = None
					keyword = "selected"
					einheit = None
					uri= None
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)
				
					# Temperatureinheit
					beschreibung = "Temperatureinheit"
					description = None
					keyword = "u_temp"
					einheit = None
					uri= None
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Typ
					beschreibung = "Typ"
					description = None
					keyword = "type"
					einheit = None
					uri= None
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Verzeichnispfad
					beschreibung = "Verzeichnispfad"
					description = None
					keyword = "n_path"
					einheit = None
					uri= None
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Volumen
					beschreibung = "Volumen"
					description = "volume"
					keyword = "volume"
					einheit = om+"cubicMillimetre"
					uri=ontologynamespace+"volume"
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Volumeneinheit
					beschreibung = "Volumeneinheit"
					description = None
					keyword = "u_volume"
					einheit = None
					uri= None
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)

					# Winkeleinheit
					beschreibung = "Winkeleinheit"
					description = None
					keyword = "u_angle"
					einheit = None
					uri= None
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					# Zeiteinheit
					beschreibung = "Zeiteinheit"
					description = None
					keyword = "u_time"
					einheit = None
					uri= None
					measurementclass = None
					application = "true"
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application)
					
					
					##### BERECHNUNGEN #####
					
					# berechneter Wert 		
					# durchschnittliche 3D-Punkt-Auflösung pro mm²
					beschreibung= "durchschnittliche Auflösung"
					description= "average resolution"
					keyword= "average_resolution"		
					einheit = "1/mm²"		
					uri=None
					measurementclass=None
					application= "script-based calculation"				
					anz_punkte_netz_ar = gom.app.meshes[me].get ("num_points")
					flaeche_netz_ar = gom.app.meshes[me].get ("area")
					value = anz_punkte_netz_ar / flaeche_netz_ar		
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application, value)
					
					# berechneter Wert
					# durchschnittlicher Punktabstand 
					beschreibung= "durchschnittlicher Punktabstand"
					description= "average point distance"
					keyword= "average_point_distance_mist"		
					einheit= om+"millimetre"		
					uri=ontologynamespace +"AveragePointDistance"
					measurementclass=None
					application= "script-based calculation"		
					anz_punkte_netz= gom.app.meshes[me].get ("num_points")
					flaeche_netz= gom.app.meshes[me].get ("area")
					value= 1/math.sqrt(anz_punkte_netz / flaeche_netz)
					infos_meshes (beschreibung, description, keyword, einheit, uri, measurementclass, application, value)
					

					
					#### POLYGONISATION ####

					####  Metadaten aus dem Kommentar  ####			
					c = gom.app.meshes[me].get ("comment") 	
					for poly in c.split("\n"):
						liste = poly.split("=")
						if len(liste) == 2:
							if (liste[0].replace(" ","")) == "poly_raster":
								dir = {}
								dir.clear()
								dir["value"] = "polygonisation"
								dir["value_type"] = type(dir["value"]).__name__
								dic_mesh_processing["processname"] = dir
								
								# poly_raster
								keyword = liste[0].replace(" ","")
								dir = {}
								dir.clear()
								dir["value"] = liste[1].replace(" ","")
								dir["key_deu"] = "Polygonisierungsraster"
								dir["key_eng"] = "polygonisation raster"				
								dir["value_type"] = type(dir["value"]).__name__
								dir["uri"] = ontologynamespace+"polyRaster"
								dir["from_application"] = "true, part value from keyword = comment"
									
								if dir["value"] != None:				
									if len(str(dir["value"])) != 0:
										if includeonlypropswithuri and "uri" in dir:
											dic_mesh_processing_poly_setup[keyword]= {}		
											dic_mesh_processing_poly_setup[keyword]= dir
										if not includeonlypropswithuri:
											dic_mesh_processing_poly_setup[keyword]= {}		
											dic_mesh_processing_poly_setup[keyword]= dir
									
								
								if dir["value"] != "1:1":						
									#smooth
									dic_mesh_processing_poly_post_s = {}					
									# prozess
									dir = {}
									dir.clear()
									dir["value"] = "smooth"
									dir["value_type"] = type(dir["value"]).__name__
									dic_mesh_processing_poly_post_s["processname"] = {}		
									dic_mesh_processing_poly_post_s["processname"] = dir					
									# automatic
									dir = {}
									dir.clear()
									dir["value"] = True
									dir["value_type"] = type(dir["value"]).__name__
									dir["from_application"] = "False"						
									if dir["value"] != None:				
										if len(str(dir["value"])) != 0:
											if includeonlypropswithuri and "uri" in dir:
												dic_mesh_processing_poly_post_s["automatic"]= {}		
												dic_mesh_processing_poly_post_s["automatic"]= dir
											if not includeonlypropswithuri:
												dic_mesh_processing_poly_post_s["automatic"]= {}		
												dic_mesh_processing_poly_post_s["automatic"]= dir
												
									if len(dic_mesh_processing_poly_post_s) > 0:					
										list_mesh_processing_poly_post.append(dic_mesh_processing_poly_post_s)
									
									#thin
									dic_mesh_processing_poly_post_t = {}					
									# prozess
									dir = {}
									dir.clear()
									dir["value"] = "thin"
									dir["value_type"] = type(dir["value"]).__name__						
									dic_mesh_processing_poly_post_t["processname"] = {}		
									dic_mesh_processing_poly_post_t["processname"] = dir					
									# automatic
									dir = {}
									dir.clear()
									dir["value"] = True
									dir["value_type"] = type(dir["value"]).__name__
									dir["from_application"] = "False"						
									if dir["value"] != None:				
										if len(str(dir["value"])) != 0:
											if includeonlypropswithuri and "uri" in dir:
												dic_mesh_processing_poly_post_t["automatic"]= {}		
												dic_mesh_processing_poly_post_t["automatic"]= dir
											if not includeonlypropswithuri:
												dic_mesh_processing_poly_post_t["automatic"]= {}		
												dic_mesh_processing_poly_post_t["automatic"]= dir
									
									if len(dic_mesh_processing_poly_post_t) > 0:				
										list_mesh_processing_poly_post.append(dic_mesh_processing_poly_post_t)
										
									if len(list_mesh_processing_poly_post) > 0:
										dic_mesh_processing["postprocessing"] = list_mesh_processing_poly_post
				
							elif (liste[0].replace(" ","")) == "ref_points":
								dic_mesh_processing_poly_post_r = {}
								# prozess
								dir = {}
								dir.clear()
								dir["value"] = "reference points"
								dir["value_type"] = type(dir["value"]).__name__
								dic_mesh_processing_poly_post_r["processname"] = {}		
								dic_mesh_processing_poly_post_r["processname"] = dir					
								# automatic
								dir = {}
								dir.clear()
								dir["value"] = True
								dir["value_type"] = type(dir["value"]).__name__
								dir["from_application"] = "False"
								dic_mesh_processing_poly_post_r["automatic"] = {}		
								dic_mesh_processing_poly_post_r["automatic"] = dir					
									
								# ref_points
								keyword = liste[0].replace(" ","")
								dir = {}
								dir.clear()
								dir["value"] = liste[1].replace(" ","")
								dir["key_deu"] = "automatische Bearbeitung von Referenzpunkten"
								dir["key_eng"] = "automatic postprocessing of referenzpoints"				
								dir["value_type"] = type(liste[1].replace(" ","")).__name__
								dir["from_application"] = "true, part value from keyword = comment"
								dir["uri"] = ontologynamespace+"refpoints"
								
								if dir["value"] != None:				
									if len(str(dir["value"])) != 0:
										if includeonlypropswithuri and "uri" in dir:
											dic_mesh_processing_poly_post_r[keyword]= {}		
											dic_mesh_processing_poly_post_r[keyword]= dir
										if not includeonlypropswithuri:
											dic_mesh_processing_poly_post_r[keyword]= {}		
											dic_mesh_processing_poly_post_r[keyword]= dir				
								
								if len(dic_mesh_processing_poly_post_r) > 0:
									list_mesh_processing_poly_post.append(dic_mesh_processing_poly_post_r)
				

					if len(dic_mesh_processing_poly_setup) > 0:
						dic_mesh_processing["setup"] = dic_mesh_processing_poly_setup		
					if len(dic_mesh_processing) > 0:
						list_mesh_processing.append(dic_mesh_processing)		
					if len(dic_mesh_info) > 0:
						dic_mesh["mesh_information"] = dic_mesh_info
					if len(dic_mesh_processing) > 0:
						dic_mesh["processing"] = list_mesh_processing
					if len(dic_mesh) > 0:
						list_meshes.append(dic_mesh)
					
					me = me + 1
				

				if len(list_meshes) > 0:	
					dic_dig["meshes"] = list_meshes
				if len(dic_dig_app) > 0:
					list_app.append(dic_dig_app)
				if len(script_version()) > 0:
					list_app.append(script_version())
				if len(list_app) > 0:		
					dic_dig["applications"] = list_app
				if len(dic_dig_project) > 0:
					dic_dig["project_information"] = dic_dig_project
				if len(list_projects) > 0:
					dic_dig["measurement_series"] = list_projects
				if len(dic_dig) > 0:
					list_prj.append(dic_dig)
					
				prj = prj + 1	
				
			if len(list_prj) > 0:	
				dic_prj["projects"]=list_prj
			######################## PROJECTS END ###############################
			
			print ("hier")




			############### EXPORTS #################

			## output files
#			newfiles = (gom.app.get ("ACTUAL_SESSION_FILE")).split(".")[0]
			newfiles = ((gom.app.get ("ACTUAL_SESSION_FILE"))[:-8])
			if len(newfiles) == 0:
				newfiles = gom.app.projects[0].get ("prj_directory") + "/" + (gom.app.projects[0].get ("prj_n")).split(".")[0]
			out_file_txt = newfiles + ".txt"
			out_file_json = newfiles + ".json"
			out_file_ttl = newfiles  + ".ttl"

			#### json ####
			out_json = open(out_file_json , "w")
			#out_json.write(str(dic_prj).replace(""","").replace(""",""").replace(""\\"",""\\\\"").decode("string_escape"))
			out_json.close()

			#### dictionary in textfile ####
			out_txt = open(out_file_txt , "w")
			out_txt.write(str(dic_prj).replace("True","true").replace("False","false").decode("string_escape"))
			out_txt.close()

			######## ttl  ########
			ttlstring=set()
			fertiges_ttl = exportToTTL(dic_prj, None, ttlstring)
#			text_file = open(out_file_ttl, "w",encoding="utf8") #geht nicht mit der alten Pythonversion in atos v6.2
			text_file = open(out_file_ttl, "w")
			text_file.write(ttlstringhead)
			for item in fertiges_ttl:
				text_file.write("%s" % item)
			text_file.close()

			#######################

			######

			print (atos_file)

print ("fertsch :-) :-)")
