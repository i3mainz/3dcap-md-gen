# -*- coding: utf-8 -*-
#
# Agisoft-Metashape Script

# Laura Raddatz / i3mainz
# Anja Cramer / LEIZA
# Timo Homburg / i3mainz
# 2020/2021/2022/2023/2024/2025

import Metashape
import os, json
import time, math 
import random
import datetime
import tkinter
from tkinter import filedialog
import tkinter.font as tkFont
from tkinter import *

production=True
# production=False

# python script version
script_name = "agisoft-metashape_3dcap-metadata.py"
script_label = "Agisoft Metashape 3DCAP Metadata Script"
github_release = "1.0.0"

####################### TTL Export #############################

## Mapping of datatypes present in the JSON dictionary to datatypes present in the TTL file .
datatypes={"float":"xsd:float","double":"xsd:double","str":"xsd:string","date":"xsd:date","int":"xsd:integer","bool":"xsd:boolean","NoneType":"xsd:string", "dateTime":"xsd:dateTime", "list":"xsd:list"}

## Namespace for classes defined in the resulting ontology model .
ontologynamespace="http://objects.mainzed.org/ont#"

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

## Prefix name for the data namespace .
dataprefix="ex"

# Prefix name for prov-o namespace .
provnamespace = "http://www.w3.org/ns/prov#"

#atos 2016
referencepointid="reference_point_id"
globalreferencepointid="point_id"

## Prefix name for the rdfs namespace .
rdfs='http://www.w3.org/2000/01/rdf-schema#'

##Prefix name for the  gigamesh namespace
giganamespace="http://www.gigamesh.eu/ont#"

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
		if info not in jsonobj or "value" not in jsonobj[info] or jsonobj[info]["value"]==None or jsonobj[info]["value"]=="":
			continue			
		propuri=str(ontologyprefix)+":"+first_lower(str(info)).replace("/","_").replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","").replace("[","_").replace("]","")
		if "uri" in jsonobj[info]:
			#print(jsonobj[info]["uri"])
			if jsonobj[info]["uri"].startswith("http"):
				propuri="<"+str(jsonobj[info]["uri"][0:jsonobj[info]["uri"].rfind("#")]+"#"+first_lower(jsonobj[info]["uri"][jsonobj[info]["uri"].rfind("#")+1:]))+">"
			elif ":" in jsonobj[info]["uri"]:
				propuri=str(jsonobj[info]["uri"][0:jsonobj[info]["uri"].rfind(":")]+":"+first_lower(jsonobj[info]["uri"][jsonobj[info]["uri"].rfind(":")+1:]))
		else:
			propuri=str(ontologyprefix)+":"+first_lower(str(info)).replace("/","_").replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","").replace("[","_").replace("]","")
		ttlstring.add(str(propuri)+" rdfs:isDefinedBy <"+str(toolpropnamespace)+str(info).replace("/","_").replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","").replace("[","_").replace("]","")+"> .\n")
		#print("Propuri: "+propuri)
		#print(jsonobj[info]["value"])
		#print(isinstance(jsonobj[info]["value"],list))
		if isinstance(jsonobj[info]["value"],list):
			for val in jsonobj[info]["value"]:
				ttlstring=handleProperty(jsonobj,info,id,labelprefix,propuri,classs,ttlstring,val,str(ontologyprefix)+":"+first_upper(str(info)).replace("/","_").replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","").replace("[","_").replace("]",""))
		else:
			ttlstring=handleProperty(jsonobj,info,id,labelprefix,propuri,classs,ttlstring,jsonobj[info]["value"],str(ontologyprefix)+":"+first_upper(str(info)).replace("/","_").replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","").replace("[","_").replace("]",""))
	#print ("ttlstring")
	return ttlstring

def exportInformationFromStructuredList(thelist,projectid,projectname,thekey,index,dataprefix,labelprefix,thelabel,theclass,informationkey,ttlstring,subdata=[{}],hasactivity=False):
	for index, data in enumerate(thelist):
		theid=str(projectid)+"_"+thekey+"_"+str(index)
		ttlstring.add(str(dataprefix)+":"+str(theid)+" rdf:type "+str(ontologyprefix)+":"+str(theclass)+", "+provenancedict.get("entity")+" .\n")
		ttlstring.add(str(dataprefix)+":"+str(theid)+" rdfs:label \""+thelabel+" "+str(theid)+" from "+str(projectname)+"\"@en .\n")
		print(informationkey)
		if hasactivity:
			ttlstring.add(str(dataprefix)+":"+str(theid)+" prov:wasDerivedFrom "+str(dataprefix)+":"+str(projectid)+" .\n")	
		if informationkey!=None and informationkey in data:
			ttlstring=exportInformationFromIndAsTTL(data[informationkey],theid,str(ontologyprefix)+":"+str(theclass),thelabel+" "+str(index),ttlstring)
		elif informationkey==None and not isinstance(data,str):
			ttlstring=exportInformationFromIndAsTTL(data,theid,str(ontologyprefix)+":"+str(theclass),thelabel+" "+str(index),ttlstring)
		for item in subdata:       
			if item["key"] in data:
				print(item["key"])
				itemid=str(theid)+"_"+item["key"]
				ttlstring.add(str(dataprefix)+":"+str(itemid)+" rdf:type "+str(ontologyprefix)+":"+item["class"]+" .\n")
				ttlstring.add(str(dataprefix)+":"+str(itemid)+" rdfs:label \""+labelprefix+" "+thelabel+" "+str(index)+" "+item["label"]+"\" .\n")
				ttlstring.add(str(dataprefix)+":"+str(theid)+" "+str(ontologyprefix)+":"+item["relation"]+" "+str(dataprefix)+":"+str(itemid)+" .\n")
				if hasactivity:
					ttlstring.add(str(dataprefix)+":"+str(itemid)+" "+str(ontologyprefix)+":partOf "+str(dataprefix)+":"+str(theid)+"_activity .\n")							
				ttlstring=exportInformationFromIndAsTTL(data[item["key"]],itemid,str(ontologyprefix)+":"+item["class"],labelprefix+" "+thelabel+" "+str(index)+" "+item["label"],ttlstring)


def checkfornewline(literal):
    if '\n' in literal or '\r' in literal:
        return "\"\""+literal+"\"\""
    else:
        return literal

units={}
def csAsSVG(csdef):
    svgstr= """<svg width=\"400\" height=\"250\" viewbox=\"0 0 375 220\"><defs><marker id=\"arrowhead\" markerWidth=\"10\" markerHeight=\"7\" refX=\"0\" refY=\"2\" orient=\"auto\"><polygon points=\"0 0, 4 2, 0 4\" /></marker></defs>"""
    print(csdef)
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
				ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace("/","_").replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+" rdfs:label \""+checkfornewline(str(jsonobj[info][englishlabel]).replace("\"","'"))+" \"@en .\n")
				ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace("/","_").replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+"_value rdfs:label \""+checkfornewline(str(jsonobj[info][englishlabel]).replace("\"","'"))+" Measurement Value \"@en .\n")
			else:
				ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace("/","_").replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+" rdfs:label \""+checkfornewline(str(jsonobj[info][englishlabel]).replace("\"","'"))+" ("+str(labelprefix)+")\"@en .\n")
				ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace("/","_").replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+"_value rdfs:label \""+checkfornewline(str(jsonobj[info][englishlabel]).replace("\"","'"))+" Measurement Value ("+str(labelprefix)+")\"@en .\n")
		if germanlabel in jsonobj[info] and jsonobj[info][germanlabel]!=None and str(jsonobj[info][germanlabel])!="" and str(jsonobj[info][germanlabel])!="...":
			ttlstring.add(str(propuri)+" rdfs:label \""+str(jsonobj[info][germanlabel]).replace("\"","'")+"\"@de .\n")
			if labelprefix=="":
				ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace("/","_").replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+" rdfs:label \""+checkfornewline(str(jsonobj[info][germanlabel]).replace("\"","'"))+" \"@de .\n")
				ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace("/","_").replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+"_value rdfs:label \""+checkfornewline(str(jsonobj[info][germanlabel]).replace("\"","'"))+" Messwert \"@de .\n")			
			else:
				ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace("/","_").replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+" rdfs:label \""+checkfornewline(str(jsonobj[info][germanlabel]).replace("\"","'"))+" ("+str(labelprefix)+")\"@de .\n")
				ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace("/","_").replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+"_value rdfs:label \""+checkfornewline(str(jsonobj[info][germanlabel]).replace("\"","'"))+" Messwert ("+str(labelprefix)+")\"@de .\n")
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
			ttlstring.add(propclass+" rdf:type owl:Class .\n") 
			ttlstring.add(propclass+" rdfs:label \""+propclass.replace("_"," ").replace(ontologyprefix+":","")+"\"@en .\n") 
			ttlstring.add(propclass+" rdfs:subClassOf om:Quantity .\n") 
			ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace("/","_").replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+" rdf:type "+propclass+" .\n") 
		ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace("/","_").replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+"_value rdf:type om:Measure .\n") 
		ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace("/","_").replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+" om:hasValue "+str(dataprefix)+":"+str(id)+"_"+str(info).replace("/","_").replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+"_value .\n")
		#print(jsonobj[info]["unit"])
		if jsonobj[info]["unit"].startswith("http"):
			ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace("/","_").replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+"_value om:hasUnit <"+str(jsonobj[info]["unit"])+"> .\n")
			ttlstring.add("<"+str(jsonobj[info]["unit"])+"> rdf:type om:UnitOfMeasure .\n")
			ttlstring.add("<"+str(jsonobj[info]["unit"])+"> rdfs:label \""+str(jsonobj[info]["unit"]).replace("\"","'")+"\"@en .\n")
		elif ":" in jsonobj[info]["unit"]:
			ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace("/","_").replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+"_value om:hasUnit "+str(jsonobj[info]["unit"].replace(" ",""))+" .\n")
			ttlstring.add(str(jsonobj[info]["unit"].replace(" ",""))+" rdf:type om:UnitOfMeasure .\n")
			ttlstring.add(str(jsonobj[info]["unit"].replace(" ",""))+" rdfs:label \""+jsonobj[info]["unit"].replace("\"","'")+"\" .\n")
		else:
			ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace("/","_").replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+"_value om:hasUnit \""+str(jsonobj[info]["unit"])+"\" .\n")
		ttlstring.add(str(dataprefix)+":"+str(id)+"_"+str(info).replace("/","_").replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+"_value om:hasNumericalValue \""+checkfornewline(str(inputvalue).replace("\\","\\\\"))+"\"^^"+str(datatypes[jsonobj[info]["value_type"]])+" .\n")		  
		ttlstring.add(str(dataprefix)+":"+str(id)+" "+str(propuri)+" "+str(dataprefix)+":"+str(id)+"_"+str(info).replace("/","_").replace(" ","").replace("[","_").replace("]","").replace("(","").replace(")","")+" .\n")
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
				ttlstring.add("<"+jsonobj[info]["measurementclass"].replace(" ","")+"> rdfs:label \""+jsonobj[info]["measurementclass"].replace("\"","'")+"\"@en .\n") 					
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
				ttlstring.add(str(propuri)+" rdfs:label \""+checkfornewline(str(jsonobj[info][englishlabel]).replace("\"","'"))+"\"@en .\n")
			if germanlabel in jsonobj[info] and jsonobj[info][germanlabel]!=None and str(jsonobj[info][germanlabel])!="" and str(jsonobj[info][germanlabel])!="...":
				ttlstring.add(str(propuri)+" rdfs:label \""+checkfornewline(str(jsonobj[info][germanlabel]).replace("\"","'"))+"\"@de .\n")
			ttlstring.add(str(propuri)+" rdfs:range "+str(datatypes[jsonobj[info]["value_type"]])+" .\n")
			ttlstring.add(str(dataprefix)+":"+str(id)+" "+str(propuri)+" \""+checkfornewline(str(inputvalue).replace("\\","\\\\"))+"\"^^"+str(datatypes[jsonobj[info]["value_type"]])+" .\n")
	#print("handled Property")
	return ttlstring

## Converts a preformatted dictionary to a set of triples .
#  @param dict the dictionary to export from
#  @param measurementToExport indicates whether to export measurements
def exportToTTL(dict,measurementToExport,ttlstring,usermetadata=None):
	#print ("drin in exportToTTL")
	projectid=str(generate_uuid())
	userid=str(generate_uuid())
	projlabelkey="prj_n"
	projects="projects"
	projkey="chunks"
	userkey="user_keywords"
	mesheskey="meshes"
	scalebarskey="scalebars"
	sensorskey="sensors"
	sensorinformationkey="calibration"
	densecloudkey="densecloud"
	alignmentsetupkey="alignment_setup"
	densecloudinformationkey="densecloud_information"
	densecloudsetupkey="densecloud_setup"
	meshprocessingkey="processing"
	calibkey="calibration"
	generalkey="general"
	meshinfokey="mesh_information"
	meshsetupkey="mesh_setup"    
	meshtexturesetupkey="texture_setup"
	globalrefpointkey="global_referencepoints"
	refpointkey="referencepoints"
	globalrefpointinfo="global_referencepoints_information"
	projinfokey="project_information"
	measurmentserieskey = "chunk_information"
	measurementskey="cameras"
	measurementinformation="camera_properties"
	messungkey="messung"
	applicationkey="applications"
	capturingdevice="capturing_device"
	mssetup="alignment_setup"
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
	ttlstring.add(str(ontologyprefix)+":Software rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":Software rdfs:label \"software\"@en .\n")
	ttlstring.add(str(ontologyprefix)+":Software rdfs:subClassOf "+provenancedict.get("entity")+" .\n")
	ttlstring.add(str(ontologyprefix)+":Scalebar rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":Scalebar rdfs:label \"scalebar\"@en .\n")
	ttlstring.add(str(ontologyprefix)+":Scalebar rdfs:subClassOf "+provenancedict.get("entity")+" .\n")
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
	ttlstring.add(str(ontologyprefix)+":Sensor rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":Sensor rdfs:label \"Sensor\"@en .\n")
	ttlstring.add(str(ontologyprefix)+":Algorithm rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":Algorithm rdfs:label \"Algorithm\"@en .\n")
	ttlstring.add(str(ontologyprefix)+":Algorithm rdfs:subClassOf "+provenancedict.get("agent")+" .\n")
	ttlstring.add(str(ontologyprefix)+":Pointcloud rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":Pointcloud rdfs:label \"Pointcloud\"@en .\n")
	ttlstring.add(str(ontologyprefix)+":Pointcloud rdfs:subClassOf geo:Geometry .\n")
	ttlstring.add(str(ontologyprefix)+":Densecloud rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":Densecloud rdfs:subClassOf "+str(ontologyprefix)+":Pointcloud .\n")
	ttlstring.add(str(ontologyprefix)+":Densecloud rdfs:label \"Densecloud\"@en .\n")
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
	ttlstring.add(str(ontologyprefix)+":texturesetup rdf:type owl:ObjectProperty .\n")
	ttlstring.add(str(ontologyprefix)+":texturesetup rdfs:range "+str(ontologyprefix)+":MeshSetup .\n")
	ttlstring.add(str(ontologyprefix)+":texturesetup rdfs:domain "+str(ontologyprefix)+":Mesh .\n")
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
	ttlstring.add(str(ontologyprefix)+":AlignmentSetup rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":AlignmentSetup rdfs:subClassOf prov:Entity .\n")
	ttlstring.add(str(ontologyprefix)+":AlignmentSetup rdfs:label \"Alignment setup\"@en .\n")
	ttlstring.add(str(ontologyprefix)+":CalibrationObject rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":Measurement rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":Measurement rdfs:label \"Measurement\".\n")
	ttlstring.add(str(ontologyprefix)+":Measurement rdfs:subClassOf prov:Entity .\n")
	ttlstring.add(str(ontologyprefix)+":MeasurementSeries rdf:type owl:Class .\n")
	ttlstring.add(str(ontologyprefix)+":MeasurementSeries rdfs:label \"Measurement Series\".\n")
	ttlstring.add(str(ontologyprefix)+":MeasurementSeries rdfs:subClassOf prov:Entity .\n")
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
	ttlstring.add(str(ontologyprefix)+":GRP_calculation_algorithm rdf:type "+str(ontologyprefix)+":Algorithm . \n")	
	for pro in dict[projects]:
		#print(projkey)		
		#print (pro[projinfokey])
		if projinfokey in pro:
			if "prj_n" in pro[projinfokey]:
				labelprefix=pro[projinfokey]["prj_n"]["value"]
				projectname=pro[projinfokey]["prj_n"]["value"]
			ttlstring.add(str(dataprefix)+":"+str(projectid)+" rdf:type "+str(ontologyprefix)+":MeasurementProject .\n")
			#print(pro[projinfokey])
			ttlstring=exportInformationFromIndAsTTL(pro[projinfokey],projectid,str(ontologyprefix)+":MeasurementProject",labelprefix,ttlstring)
		# if usermetadata!=None:
		if len(usermetadata) > 0:
			ttlstring=addUserMetadataToId(ttlstring,usermetadata,projectid)
		#print(pro[applicationkey])
		if applicationkey in pro:
			if "PROJECT.TYPE" in pro[applicationkey][0] and "PROJECT.VERSION" in pro[applicationkey][0]:
				softwareid=str(pro[applicationkey][0]["PROJECT.TYPE"]["value"]).strip().replace(" ","_")+"_"+str(pro[applicationkey][0]["PROJECT.VERSION"]["value"]).strip().replace(" ","_").replace(".","_").replace("-","_")
			elif "application_name" in pro[applicationkey][0] and "application_build_information.version" in pro[applicationkey][0]:
				softwareid=str(pro[applicationkey][0]["application_name"]["value"]).strip().replace(" ","_")+"_"+str(pro[applicationkey][0]["application_build_information.version"]["value"]).strip().replace(" ","_").replace(".","_").replace("-","_")
			else:
				softwareid="ATOS2016"
			ttlstring.add(str(dataprefix)+":"+softwareid+" rdf:type "+str(ontologyprefix)+":Software  .\n")
			ttlstring.add(str(dataprefix)+":"+softwareid+" rdfs:label \""+str(softwareid).replace("_"," ")+"\"@en .\n")
			ttlstring=exportInformationFromIndAsTTL(pro[applicationkey][0],softwareid,str(ontologyprefix)+":Software",labelprefix,ttlstring)
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
				if globalrefpointkey in project and refpointkey in project[globalrefpointkey]:
					for index, grp in enumerate(project[globalrefpointkey][refpointkey]):
						#print(ttlstring)
						#print("GRP: "+str(grp))
						if "point_id" in grp:
							index = grp["point_id"]["value"]
							#print (index)
						elif "r_id" in grp:
							index = grp["r_id"]["value"]
							#print (index)						
						grpid=str(projectid)+"_ms_"+str(msindex)+"_grp"+str(index)
						#print (grpid)
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
							ttlstring=csFromPoint(str(dataprefix)+":"+str(grpid),grp["r_x"],grp["r_y"],grp["r_z"],ttlstring)
						elif "coordinate.x" in grp and "coordinate.y" in grp and "coordinate.z" in grp:
							ttlstring.add(str(dataprefix)+":"+str(grpid)+" geo:asWKT \"POINT("+str(grp["coordinate.x"]["value"])+" "+str(grp["coordinate.y"]["value"])+" "+str(grp["coordinate.z"]["value"])+")\"^^geo:wktLiteral .\n")
							ttlstring=csFromPoint(str(dataprefix)+":"+str(grpid),grp["coordinate.x"],grp["coordinate.y"],grp["coordinate.z"],ttlstring)
						elif "position x" in grp and "position y" in grp and "position z" in grp:
							ttlstring.add(str(dataprefix)+":"+str(grpid)+" geo:asWKT \"POINT("+str(grp["position x"]["value"])+" "+str(grp["position y"]["value"])+" "+str(grp["position z"]["value"])+")\"^^geo:wktLiteral .\n")
							ttlstring=csFromPoint(str(dataprefix)+":"+str(grpid),grp["position x"],grp["position y"],grp["position z"],ttlstring)
				if globalrefpointkey in project and scalebarskey in project[globalrefpointkey]:
					exportInformationFromStructuredList(project[globalrefpointkey][scalebarskey],projectid,projectname,scalebarskey,index,dataprefix,labelprefix,labelprefix+" MS "+str(msindex)+" ","Scalebar",None,ttlstring,[])
			if alignmentsetupkey in project:
				ttlstring.add(str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+"_alignmentsetup rdf:type "+str(ontologyprefix)+":AlignmentSetup .\n")
				ttlstring.add(str(dataprefix)+":"+str(projectid)+"_ms_"+str(msindex)+"_alignmentsetup rdfs:label \"MS "+str(msindex)+" Alignment Setup\" .\n")
				ttlstring=exportInformationFromIndAsTTL(project[alignmentsetupkey],str(projectid)+"_ms_"+str(msindex)+"_alignmentsetup",str(ontologyprefix)+":AlignmentSetup",labelprefix,ttlstring)
			if sensorskey in project:
				for seindex, sensor in enumerate(project[sensorskey]):
					sensorid=str(projectid)+"_sensor_"+str(seindex)
					calibid=str(sensorid)+"_calibration"
					mscheckid=str(sensorid)+"_mscheck"
					capturedevid=str(sensorid)+"_capturingdevice"
					ttlstring.add(str(dataprefix)+":"+str(sensorid)+" rdf:type "+str(ontologyprefix)+":Sensor, "+provenancedict.get("entity")+" .\n")
					ttlstring.add(str(dataprefix)+":"+str(sensorid)+" rdfs:label \"Sensor "+str(sensorid)+" from "+str(projectname)+"\"@en .\n")
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
						ttlstring.add(str(dataprefix)+":"+str(calibid)+"_activity rdf:type prov:Activity .\n")
						if labelprefix=="":
							ttlstring.add(str(dataprefix)+":"+str(calibid)+"_activity rdfs:label \"MS "+str(seindex)+" Measurement "+str(index)+" Calibration Activity \"@en .\n")
							ttlstring.add(str(dataprefix)+":"+str(calibid)+"_activity rdfs:label \"Sensor "+str(seindex)+" Messvorgang "+str(index)+" Kalibrierung \"@de .\n")
						else:
							ttlstring.add(str(dataprefix)+":"+str(calibid)+"_activity rdfs:label \"MS "+str(seindex)+" Measurement "+str(index)+" Calibration Activity ("+str(labelprefix)+")\"@en .\n")
							ttlstring.add(str(dataprefix)+":"+str(calibid)+"_activity rdfs:label \"Sensor "+str(seindex)+" Messvorgang "+str(index)+" Kalibrierung ("+str(labelprefix)+")\"@de .\n")							
						ttlstring.add(str(dataprefix)+":"+str(calibid)+"_activity prov:wasAssociatedWith "+str(dataprefix)+":"+str(userid)+" .\n")
						ttlstring.add(str(dataprefix)+":"+str(calibid)+" rdf:type "+str(ontologyprefix)+":Calibration .\n")
						if calobject in sensor[calibkey]:
							calobjid=""
							calobjname=""
							if "calibration_object_name" in messung[calibkey][calobject]:
								#print(messung[calibkey][calobject])
								calobjid=str(messung[calibkey][calobject]["calibration_object_name"]["value"]).replace(" ","")+"_calibration_object"
								calobjname=str(messung[calibkey][calobject]["calibration_object_name"]["value"])
							else:
								calobjid=str(sensorid)+"_calibration_object"
							ttlstring.add(str(dataprefix)+":"+str(calibid)+" "+str(ontologyprefix)+":calibrationobject "+str(dataprefix)+":"+str(calobjid)+" .\n")
							ttlstring.add(str(dataprefix)+":"+str(calobjid)+" rdfs:label \""+labelprefix+" MS "+str(msindex)+" Measurement "+str(index)+" Calibration Object"+"\" .\n")
							ttlstring.add(str(dataprefix)+":"+str(calibid)+"_activity prov:used "+str(dataprefix)+":"+str(calobjid)+" .\n")
							ttlstring.add(str(dataprefix)+":"+str(calobjid)+" rdf:type "+str(ontologyprefix)+":CalibrationObject .\n")
							ttlstring=exportInformationFromIndAsTTL(messung[calibkey][calobject],calobjid,str(ontologyprefix)+":CalibrationObject",calobjname+" Calibration Object",ttlstring)
						if calsetup in sensor[calibkey]:
							calsetupid=str(sensorid)+"_calibration_setup"
							ttlstring.add(str(dataprefix)+":"+str(calsetupid)+" rdf:type "+str(ontologyprefix)+":CalibrationSetup .\n")
							ttlstring.add(str(dataprefix)+":"+str(calsetupid)+" rdfs:label \""+labelprefix+" MS "+str(msindex)+" Measurement "+str(index)+" Calibration Setup"+"\" .\n")
							ttlstring.add(str(dataprefix)+":"+str(calibid)+" "+str(ontologyprefix)+":calibrationsetup "+str(dataprefix)+":"+str(calsetupid)+" .\n")
							ttlstring.add(str(dataprefix)+":"+str(calsetupid)+" "+str(ontologyprefix)+":partOf "+str(dataprefix)+":"+str(calibid)+"_activity .\n")
							ttlstring=exportInformationFromIndAsTTL(sensor[calibkey][calsetup],calsetupid,str(ontologyprefix)+":CalibrationSetup",labelprefix+" MS "+str(seindex)+" Sensor "+str(index)+" Calibration Setup",ttlstring)							
						if calproperties in sensor[calibkey]:
							ttlstring=exportInformationFromIndAsTTL(sensor[calibkey][calproperties],calibid,str(ontologyprefix)+":Calibration",labelprefix+" MS "+str(seindex)+" Sensor "+str(index)+" Calibration",ttlstring)
						ttlstring=exportInformationFromIndAsTTL(sensor[calibkey],calibid,str(ontologyprefix)+":Calibration",labelprefix+" MS "+str(seindex)+" Sensor "+str(index)+" Calibration",ttlstring)
					#print(ttlstring)
			if densecloudkey in project:
				exportInformationFromStructuredList(project[densecloudkey],projectid,projectname,densecloudkey,index,dataprefix,labelprefix,labelprefix+" MS "+str(msindex)+" ","Densecloud",densecloudinformationkey,ttlstring,
				[{"key":densecloudsetupkey,"label":"Densecloud Setup","class":"DenseCloudSetup","relation":"setup"}])
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
						ttlstring=exportInformationFromIndAsTTL(messung[capturingdevice],mscheckid,str(ontologyprefix)+":MeasurementCheck",labelprefix+" MS "+str(msindex)+" Measurement "+str(index)+" Measurement Check",ttlstring)
					if measurementinformation in messung:
						ttlstring=exportInformationFromIndAsTTL(messung[measurementinformation],messungid,str(ontologyprefix)+":Measurement",labelprefix+" MS "+str(msindex)+" Measurement "+str(index),ttlstring)
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
							ttlstring.add(str(dataprefix)+":"+str(rpuri)+" rdf:type "+str(ontologyprefix)+":ReferencePoint .\n")				
							ttlstring.add(str(dataprefix)+":"+str(rpuri)+" rdfs:label \"RP"+str(index2)+" ("+str(labelprefix)+" MS "+str(msindex)+" Measurement "+str(messungindex)+")\"@en .\n")
							ttlstring.add(str(dataprefix)+":"+str(rpuri)+" rdfs:label \"RP"+str(index2)+" ("+str(labelprefix)+" Messreihe "+str(msindex)+" Messung "+str(messungindex)+")\"@de .\n")
							ttlstring=exportInformationFromIndAsTTL(rp,rpuri,str(ontologyprefix)+":ReferencePoint",labelprefix+" MS "+str(msindex)+" Measurement "+str(index)+" RP"+str(index2),ttlstring)
							if "r_x" in rp and "r_y" in rp and "r_z" in rp:
							# atos v6.2
								ttlstring.add(str(dataprefix)+":"+str(rpuri)+" geo:asWKT \"POINT("+str(rp["r_x"]["value"])+" "+str(rp["r_y"]["value"])+" "+str(rp["r_z"]["value"])+")\"^^geo:wktLiteral .\n")
								ttlstring=csFromPoint(str(dataprefix)+":"+str(rpuri),grp["r_x"],grp["r_y"],grp["r_z"],ttlstring)
							#atos 2016
							elif "reference_point_coordinate.x" in rp and "reference_point_coordinate.y" in rp and "reference_point_coordinate.z" in rp:
								ttlstring.add(str(dataprefix)+":"+str(rpuri)+" geo:asWKT \"POINT("+str(rp["reference_point_coordinate.x"]["value"])+" "+str(rp["reference_point_coordinate.y"]["value"])+" "+str(rp["reference_point_coordinate.z"]["value"])+")\"^^geo:wktLiteral .\n")
								ttlstring=csFromPoint(str(dataprefix)+":"+str(rpuri),grp["reference_point_coordinate.x"],grp["reference_point_coordinate.y"],grp["reference_point_coordinate.z"],ttlstring)
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
			if mesheskey in project:					
				for index, mesh in enumerate(project[mesheskey]):
					meshid=str(projectid)+"_mesh_"+str(index)
					ttlstring.add(str(dataprefix)+":"+str(meshid)+" rdf:type "+str(ontologyprefix)+":Mesh, "+provenancedict.get("entity")+" .\n")
					ttlstring.add(str(dataprefix)+":"+str(meshid)+" rdfs:label \"Mesh "+str(meshid)+" from "+str(projectname)+"\"@en .\n")
					ttlstring.add(str(dataprefix)+":"+str(meshid)+" prov:wasDerivedFrom "+str(dataprefix)+":"+str(projectid)+" .\n")
					if meshprocessingkey in mesh:
						#print(mesh[meshprocessingkey])
						lastprocid=""
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
					exportInformationFromStructuredList(project[mesheskey],projectid,projectname,"mesh",index,dataprefix,labelprefix,labelprefix+" MS "+str(msindex)+" ","Mesh",meshinfokey,ttlstring,[{"key":meshsetupkey,"label":"Mesh Setup","class":"MeshSetup","relation":"setup"},{"key":meshtexturesetupkey,"label":"Mesh Texture","class":"TextureSetup","relation":"texturesetup"}])
					#ttlstring=exportInformationFromIndAsTTL(mesh[meshinfokey],meshid,str(ontologyprefix)+":Mesh",labelprefix+" Mesh Attribute ",ttlstring)							
	return ttlstring

def entryToTTL(idd,realobj,ttlstring):
    print(realobj)
    ttlstring.add("<"+idd+"> <"+realobj["value"]+" <"+realobj["value"]+"> .\n")
    ttlstring.add("<"+realobj["value"]+"> rdfs:label \""+realobj["key_eng"]+"\"@en .\n")
    ttlstring.add("<"+realobj["value"]+"> rdfs:label \""+realobj["key_deu"]+"\"@de .\n")
    return ttlstring

def addUserMetadataToId(ttlstring,usermetadata,theid):
				data=usermetadata["projects"][0]["general"]
				realobj=data["real_object"][0]
				robjid=theid+"_robj"
				for key in realobj:
#					print(key)
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
				if "research_project" in data:
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
												#ttlstring.add("<"+app["institute"]["value"]+"> rdfs:label \""+app["institute"]["value_label"]+"\" .\n")      
												ttlstring.add("<"+app["institute"]["value"]+"> rdfs:label \""+app["institute"]["value"]+"\" .\n")  
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



##############################################################

###  GUI

class Window(Frame):
	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):		
		self.master.title("Metadaten Agisoft Metashape")
		self.master.rowconfigure( 0, weight = 1 )
		self.master.columnconfigure( 0, weight = 10)
		self.grid( sticky = W+E+N+S )

		# Variablen
		self.filepath = tkinter.StringVar()
		self.unit_mm = tkinter.IntVar()
		self.unit_cm = tkinter.IntVar()
		self.unit_m = tkinter.IntVar()
		self.unit_project = tkinter.IntVar()
		self.uri = tkinter.BooleanVar()

		####### FILE GROUPS 
		filegroup = LabelFrame(self, text = "Agisoft file")
		filegroup.grid(row = 0, column = 0, sticky = W, padx=5, pady=5 )
		browseButton = Button(filegroup, text = 'Browse', command = self.first_browser)
		browseButton.grid(row = 1, column=0, sticky = W+E+N+S, padx=5, pady=5 )
		filepathText = Entry(filegroup, textvariable = self.filepath, width=150)
		filepathText.grid(row = 1, column = 1, columnspan=5, sticky = W+E+N+S , padx=5, pady=5)		

		lbl = Label(filegroup,text="Select one unit:")
		lbl.grid(row = 2, column=0, sticky = W)		
		checkbutton_mm = Checkbutton(filegroup, text="millimetre", variable=self.unit_mm)
		checkbutton_mm.grid(row = 2, column=1, sticky = W+E+N+S, padx=5, pady=5 )
		checkbutton_m = Checkbutton(filegroup, text="metre", variable=self.unit_m)
		checkbutton_m.grid(row = 2, column=3, sticky = W+E+N+S, padx=5, pady=5 )

		lbl_2 = Label(filegroup,text="Output with URI only:")
		lbl_2.grid(row = 3, column=0, sticky = W)	
		checkbutton_uri = Checkbutton(filegroup, variable=self.uri)
		checkbutton_uri.grid(row = 3, column=1, sticky = W, padx=5, pady=5 )

		checkbutton_project = Checkbutton(filegroup, text="project unit", variable=self.unit_project)
		checkbutton_project.grid(row = 2, column=5, sticky = W+E+N+S, padx=5, pady=5 )

		browseButton = Button(filegroup, text = 'Start', command = self.startMetadata)
		browseButton.grid(row = 4, column=0, sticky = W, padx=5, pady=5 )
		

	def close_window(self):		
		print ("6")
		root.destroy()
	
	# select file and return
	def show_file_browser(self):
		filetypes = (('text files', '*.psx'),('All files', '*.*'))
		self.filename = filedialog.askopenfilename(filetypes=filetypes)			
		print ("... file open ... " + self.filename)
		return self.filename
	
	def return_unit (self):
		if self.unit_mm.get() == 1:
			unit = 'unit_mm'
			print ("millimetre units")
			print (unit)
		elif self.unit_m.get() == 1:
			unit = 'unit_m'
			print ("metre units")
			print (unit)
		elif self.unit_project.get() == 1:
			unit = 'unit_project'
			print ("project units")
			print (unit)
		else:
			unit = None
			print ("... units")
			print (unit)

		return unit

	def first_browser(self):
		file = self.show_file_browser()
		self.filepath.set(file)

	def request_withUri(self):
		print(':...................')
		print(self.uri)
		#print(includeonlypropswithuri)
		if self.uri.get() == True:
			includeonlypropswithuri= True
	
		else:
			includeonlypropswithuri=False
		print(includeonlypropswithuri)
		return includeonlypropswithuri


	def startMetadata (self):
		unit = self.return_unit()
		includeonlypropswithuri= self.request_withUri()

		print ("... projekt wird zur nächsten Methode übergeben und gestartet")
		exportMeta(self.filename , unit, includeonlypropswithuri)
		print ("... close GUI")
		self.close_window()



#################################  Methode zum Erzeugen der Metadaten  ###################################################################
	
#### return DICTIONARY

def createMetaDic(dic_user, input_file, selected_unit, includeonlypropswithuri):

	print (includeonlypropswithuri)

	mav =  (((Metashape.app.version).split('.'))[0])
	
	print ("... inside createMetaDic")
	doc = Metashape.Document()
	doc.open(input_file)	

	dic_prj = {}
	list_projects= []
	project ={}
	list_chunks = []	
	project_info = {}
	app = {}
	list_app = []
	project_unit=""

	# add script version infos
	list_app.append(script_version())
	
	if "projects" in dic_user:
		for e in dic_user["projects"]:
			if 'general' in e:
				project['general'] = e['general']

	def infos_app (keyword,beschreibung, value, unit,description,uri,measurementclass, from_application ='true'):
		dir = {}
		dir["value"] = value
		dir["key_deu"] = beschreibung
		if description!=None:
			dir["key_eng"] = description		
		if uri!=None:
			dir["uri"] = uri	
		if measurementclass!=None:
			dir["measurementclass"] = measurementclass			
		dir["value_type"] = type(value).__name__
		if unit!=None:
			dir["unit"] = unit
		if from_application!=None:
			dir["from_application"] = from_application
		if keyword == 'LastSavedDateTime' or keyword == 'OriginalDateTime':
			dir['value_type']= 'dateTime'
	
		if dir["value"] != None:
			if len(str(dir["value"])) != 0:
				app[keyword] = {}		
				app[keyword] = dir
	
	def infos_p (keyword, beschreibung,value, unit=None, description=None, uri=None,  measurementclass=None, from_application ='true'):
		dir = {}
		dir["value"] = value			
		dir["key_deu"] = beschreibung
		dir["from_application"]=from_application
		if  description != None:
			dir["key_eng"] =  description
		if  uri != None:
			dir["uri"] =  uri
		if  unit != None:
			dir["unit"] =  unit
		if measurementclass!=None:
				dir["measurementclass"] = measurementclass
		dir["value_type"] = type(value).__name__
		if keyword == 'LastSavedDateTime' or keyword == 'OriginalDateTime':
			dir['value_type']= 'dateTime'

		if dir["value"] != None:
			if len(str(dir["value"])) != 0:
				if includeonlypropswithuri and "uri" in dir:
					project_info[keyword] = {}		
					project_info[keyword] = dir
				if not includeonlypropswithuri:			
					project_info[keyword] = {}
					project_info[keyword] = dir


	### Chunk Informations 
	
	def infos_chunk (keyword, beschreibung,value, unit, description, uri, measurementclass, from_application='true'):
		dir = {}
		dir["value"] = value			
		dir["key_deu"] = beschreibung
		dir['from_application']= from_application
		if  description != None:
			dir["key_eng"] =  description
		if  uri != None:
			dir["uri"] =  uri
		if  unit != None:
			dir["unit"] =  unit
		if measurementclass!=None:
			dir["measurementclass"] = measurementclass
		dir["value_type"] = type(value).__name__
		if keyword == 'LastSavedDateTime' or keyword == 'OriginalDateTime':
			dir['value_type']= 'dateTime'

		if dir["value"] != None:
			if len(str(dir["value"])) != 0:
				if includeonlypropswithuri and "uri" in dir:
					chunk_info[keyword] = {}		
					chunk_info[keyword] = dir
				if not includeonlypropswithuri:			
					chunk_info[keyword] = {}
					chunk_info[keyword] = dir

	def infos_alignment_setup (keyword, beschreibung,value, unit, description, uri, measurementclass, from_application='true'):
		dir = {}
		dir["value"] = value			
		dir["key_deu"] = beschreibung
		dir['from_application']= from_application
		if  description != None:
			dir["key_eng"] =  description
		if  uri != None:
			dir["uri"] =  uri
		if  unit != None:
			dir["unit"] =  unit
		if measurementclass!=None:
			dir["measurementclass"] = measurementclass		
		if value != None:
			dir["value_type"] = type(value).__name__
		if keyword == 'LastSavedDateTime' or keyword == 'OriginalDateTime':
			dir['value_type']= 'dateTime'
		if keyword == 'LastSavedDateTime':
			dir["value_type"] = 'dateTime'

		if dir["value"] != None:
			if len(str(dir["value"])) != 0:
				if includeonlypropswithuri and "uri" in dir:
					alignment[keyword] = {}		
					alignment[keyword] = dir
				if not includeonlypropswithuri:			
					alignment[keyword] = {}
					alignment[keyword] = dir


	def infos_marker (keyword, beschreibung,value, unit, description, uri, measurementclass, from_application= 'true'):
		dir = {}
		dir["value"] = value			
		dir["key_deu"] = beschreibung
		dir["from_application"]= from_application
		if  description != None:
			dir["key_eng"] =  description
		if  uri != None:
			dir["uri"] =  uri
		if  unit != None:
			dir["unit"] =  unit
		if measurementclass!=None:
			dir["measurementclass"] = measurementclass
		dir["value_type"] = type(value).__name__
		if keyword == 'LastSavedDateTime' or keyword == 'OriginalDateTime':
			dir['value_type']= 'dateTime'

		if dir["value"] != None:
			if len(str(dir["value"])) != 0:
				if includeonlypropswithuri and "uri" in dir:
					rp_info[keyword] = {}		
					rp_info[keyword] = dir
				if not includeonlypropswithuri:			
					rp_info[keyword] = {}
					rp_info[keyword] = dir

	def infos_kali_setup(keyword, beschreibung, value, unit, description, uri, measurementclass, from_application='true'):
		dir = {}
		dir["value"] = value			
		dir["key_deu"] = beschreibung
		dir['from_application']= from_application
		if  description != None:
			dir["key_eng"] =  description
		if  uri != None:
			dir["uri"] =  uri
		if  unit != None:
			dir["unit"] =  unit
		dir["value_type"] = type(value).__name__
		if keyword == 'LastSavedDateTime' or keyword == 'OriginalDateTime':
			dir['value_type']= 'dateTime'
		if measurementclass!=None:
			dir["measurementclass"] = measurementclass

		if dir["value"] != None:
			if len(str(dir["value"])) != 0:
				if includeonlypropswithuri and "uri" in dir:
					kali_setup[keyword] = {}		
					kali_setup[keyword] = dir
				if not includeonlypropswithuri:			
					kali_setup[keyword] = {}
					kali_setup[keyword] = dir

	def infos_kali_properties (keyword, beschreibung, value, unit, description, uri, measurementclass, from_application='true'):
		dir = {}
		dir["value"] = value			
		dir["key_deu"] = beschreibung
		dir['from_application']= from_application
		if  description != None:
			dir["key_eng"] =  description
		if  uri != None:
			dir["uri"] =  uri
		if  unit != None:
			dir["unit"] =  unit
		dir["value_type"] = type(value).__name__
		if keyword == 'LastSavedDateTime' or keyword == 'OriginalDateTime':
			dir['value_type']= 'dateTime'
		if measurementclass!=None:
			dir["measurementclass"] = measurementclass

		if dir["value"] != None:
			if len(str(dir["value"])) != 0:
				if includeonlypropswithuri and "uri" in dir:
					kali_properties[keyword] = {}		
					kali_properties[keyword] = dir
				if not includeonlypropswithuri:			
					kali_properties[keyword] = {}
					kali_properties[keyword] = dir

	def infos_sensor(keyword, beschreibung, value, unit, description, uri, measurementclass, from_application='true'):
		dir = {}
		dir["value"] = value			
		dir["key_deu"] = beschreibung
		dir['from_application']= from_application
		if  description != None:
			dir["key_eng"] =  description
		if  uri != None:
			dir["uri"] =  uri
		if  unit != None:
			dir["unit"] =  unit
		dir["value_type"] = type(value).__name__
		if keyword == 'LastSavedDateTime' or keyword == 'OriginalDateTime':
			dir['value_type']= 'dateTime'
		if measurementclass!=None:
			dir["measurementclass"] = measurementclass

		if dir["value"] != None:
			if len(str(dir["value"])) != 0:
				if includeonlypropswithuri and "uri" in dir:
					kali_cd[keyword] = {}		
					kali_cd[keyword] = dir
				if not includeonlypropswithuri:			
					kali_cd[keyword] = {}
					kali_cd[keyword] = dir

	def infos_cameras(keyword, beschreibung,value, unit, description, uri, measurementclass, value_type, from_application='true'):
		dir = {}
		dir["value"] = value
		try:
			dir["value"] = int(value)
		except:
			dir["value"] = value
		dir["key_deu"] = beschreibung
		dir["from_application"]=from_application
		if  description != None:
			dir["key_eng"] =  description
		if  uri != None:
			dir["uri"] =  uri
		if  unit != None:
			dir["unit"] =  unit
		if measurementclass!=None:
			dir["measurementclass"] = measurementclass
		# dir["value_type"] = type(dir["value"]).__name__
		dir["value_type"] = value_type

		if dir["value"] != None:
			if len(str(dir["value"])) != 0:
				if includeonlypropswithuri and "uri" in dir:
					camera_info[keyword] = {}		
					camera_info[keyword] = dir
				if not includeonlypropswithuri:			
					camera_info[keyword] = {}
					camera_info[keyword] = dir

	def infos_tiepoints(keyword, beschreibung,value, unit, description, uri, measurementclass, from_application='true'):
		dir = {}
		dir["value"] = value
		dir["key_deu"] = beschreibung
		dir["from_application"]=from_application
		if  description != None:
			dir["key_eng"] =  description
		if  uri != None:
			dir["uri"] =  uri
		if  unit != None:
			dir["unit"] =  unit
		if measurementclass!=None:
			dir["measurementclass"] = measurementclass
		dir["value_type"] = type(value).__name__
		if keyword == 'LastSavedDateTime' or keyword == 'OriginalDateTime':
			dir['value_type']= 'dateTime'

		if dir["value"] != None:
			if len(str(dir["value"])) != 0:
				if includeonlypropswithuri and "uri" in dir:
					tiepoint_info[keyword] = {}		
					tiepoint_info[keyword] = dir
				if not includeonlypropswithuri:			
					tiepoint_info[keyword] = {}
					tiepoint_info[keyword] = dir

	def infos_densecloud(keyword, beschreibung,value, unit, description, uri, measurementclass, from_application='true'):
		dir = {}
		dir["value"] = value
		dir["key_deu"] = beschreibung
		dir["from_application"]=from_application
		if  description != None:
			dir["key_eng"] =  description
		if  uri != None:
			dir["uri"] =  uri
		if  unit != None:
			dir["unit"] =  unit
		if measurementclass!=None:
			dir["measurementclass"] = measurementclass
		dir["value_type"] = type(value).__name__
		if keyword == 'LastSavedDateTime' or keyword == 'OriginalDateTime':
			dir['value_type']= 'dateTime'

		if dir["value"] != None:
			if len(str(dir["value"])) != 0:
				if includeonlypropswithuri and "uri" in dir:
					densecloud_info[keyword] = {}		
					densecloud_info[keyword] = dir
				if not includeonlypropswithuri:			
					densecloud_info[keyword] = {}
					densecloud_info[keyword] = dir

	def infos_dc_setup(keyword, beschreibung,value, unit, description, uri, measurementclass, from_application='true'):
		dir = {}
		dir["value"] = value
		dir["key_deu"] = beschreibung
		dir["from_application"]=from_application
		if  description != None:
			dir["key_eng"] =  description
		if  uri != None:
			dir["uri"] =  uri
		if  unit != None:
			dir["unit"] =  unit
		if measurementclass!=None:
			dir["measurementclass"] = measurementclass
		dir["value_type"] = type(value).__name__
		if keyword == 'LastSavedDateTime' or keyword == 'OriginalDateTime':
			dir['value_type']= 'dateTime'

		if dir["value"] != None:
			if len(str(dir["value"])) != 0:
				if includeonlypropswithuri and "uri" in dir:
					densecloud_setup[keyword] = {}		
					densecloud_setup[keyword] = dir
				if not includeonlypropswithuri:			
					densecloud_setup[keyword] = {}
					densecloud_setup[keyword] = dir

	def infos_mesh(keyword, beschreibung,value, unit, description, uri, measurementclass, from_application='true'):
		dir = {}
		dir["value"] = value 
		dir["key_deu"] = beschreibung
		dir["from_application"]= from_application
		if  description != None:
			dir["key_eng"] =  description
		if  uri != None:
			dir["uri"] =  uri
		if  unit != None:
			dir["unit"] =  unit
		if measurementclass!=None:
			dir["measurementclass"] = measurementclass
		dir["value_type"] = type(value).__name__
		if keyword == 'LastSavedDateTime' or keyword == 'OriginalDateTime':
			dir['value_type']= 'dateTime'

		if dir["value"] != None:
			if len(str(dir["value"])) != 0:
				if includeonlypropswithuri and "uri" in dir:
					mesh_info[keyword] = {}		
					mesh_info[keyword] = dir
				if not includeonlypropswithuri:			
					mesh_info[keyword] = {}
					mesh_info[keyword] = dir

	def infos_mesh_setup(keyword, beschreibung,value, unit, description, uri, measurementclass, from_application='true'):
		dir = {}
		dir["value"] = value 
		dir["key_deu"] = beschreibung
		dir["from_application"]= from_application
		if  description != None:
			dir["key_eng"] =  description
		if  uri != None:
			dir["uri"] =  uri
		if  unit != None:
			dir["unit"] =  unit
		if measurementclass!=None:
			dir["measurementclass"] = measurementclass
		dir["value_type"] = type(value).__name__
		if keyword == 'LastSavedDateTime' or keyword == 'OriginalDateTime':
			dir['value_type']= 'dateTime'

		if dir["value"] != None:
			if len(str(dir["value"])) != 0:
				if includeonlypropswithuri and "uri" in dir:
					mesh_setup[keyword] = {}		
					mesh_setup[keyword] = dir
				if not includeonlypropswithuri:			
					mesh_setup[keyword] = {}
					mesh_setup[keyword] = dir

	def infos_texturing(keyword, beschreibung,value, unit, description, uri, measurementclass, from_application='true'):
		dir = {}
		dir["value"] = value
		dir["key_deu"] = beschreibung
		dir["from_application"]= from_application
		if  description != None:
			dir["key_eng"] =  description
		if  uri != None:
			dir["uri"] =  uri
		if  unit != None:
			dir["unit"] =  unit
		if measurementclass!=None:
			dir["measurementclass"] = measurementclass
		dir["value_type"] = type(value).__name__
		if keyword == 'LastSavedDateTime' or keyword == 'OriginalDateTime':
			dir['value_type']= 'dateTime'

		if dir["value"] != None:
			if len(str(dir["value"])) != 0:
				if includeonlypropswithuri and "uri" in dir:
					texture_info[keyword] = {}		
					texture_info[keyword] = dir
				if not includeonlypropswithuri:			
					texture_info[keyword] = {}
					texture_info[keyword] = dir

	def individual_marker (keyword, beschreibung,value, unit, description, uri, measurementclass, from_application ='true'):
		dir = {}
		dir.clear()
		dir["value"] = value
		dir["key_deu"] = beschreibung
		dir["from_application"]= from_application
		if  description != None:
			dir["key_eng"] =  description
		if  uri != None:
			dir["uri"] =  uri
		if  unit != None:
			dir["unit"] =  unit
		if measurementclass!=None:
			dir["measurementclass"] = measurementclass
		dir["value_type"] = type(value).__name__
		if keyword == 'LastSavedDateTime' or keyword == 'OriginalDateTime':
			dir['value_type']= 'dateTime'

		if dir["value"] != None:
			if len(str(dir["value"])) != 0:
				if includeonlypropswithuri and "uri" in dir:
					rp[keyword] = {}		
					rp[keyword] = dir
				if not includeonlypropswithuri:			
					rp[keyword] = {}
					rp[keyword] = dir


	def infos_local_rp (keyword, beschreibung,value, unit, description, uri, measurementclass, from_application ='true'):
		dir = {}
		dir.clear()
		dir["value"] = value
		dir["key_deu"] = beschreibung
		dir["from_application"]= from_application
		if  description != None:
			dir["key_eng"] =  description
		if  uri != None:
			dir["uri"] =  uri
		if  unit != None:
			dir["unit"] =  unit
		if measurementclass!=None:
			dir["measurementclass"] = measurementclass
		dir["value_type"] = type(value).__name__
		if keyword == 'LastSavedDateTime' or keyword == 'OriginalDateTime':
			dir['value_type']= 'dateTime'

		if dir["value"] != None:
			if len(str(dir["value"])) != 0:
				if includeonlypropswithuri and "uri" in dir:
					local_rp[keyword] = {}		
					local_rp[keyword] = dir
				if not includeonlypropswithuri:			
					local_rp[keyword] = {}
					local_rp[keyword] = dir
	
	def individual_scalebar(keyword, beschreibung,value, unit, description, uri, measurementclass, from_application ='true'):
		dir = {}
		dir.clear()
		dir["value"] = value
		dir["key_deu"] = beschreibung
		dir["from_application"]= from_application
		if  description != None:
			dir["key_eng"] =  description
		if  uri != None:
			dir["uri"] =  uri
		if  unit != None:
			dir["unit"] =  unit
		if measurementclass!=None:
			dir["measurementclass"] = measurementclass
		dir["value_type"] = type(value).__name__
		if keyword == 'LastSavedDateTime' or keyword == 'OriginalDateTime':
			dir['value_type']= 'dateTime'

		if dir["value"] != None:
			if len(str(dir["value"])) != 0:
				if includeonlypropswithuri and "uri" in dir:
					dic_scalebar[keyword] = {}		
					dic_scalebar[keyword] = dir
				if not includeonlypropswithuri:			
					dic_scalebar[keyword] = {}
					dic_scalebar[keyword] = dir
	
	def infos_dem (keyword, beschreibung,value, unit, description, uri, measurementclass, from_application ='true'):
		dir = {}
		dir.clear()
		dir["value"] = value
		dir["key_deu"] = beschreibung
		dir["from_application"]= from_application
		if  description != None:
			dir["key_eng"] =  description
		if  uri != None:
			dir["uri"] =  uri
		if  unit != None:
			dir["unit"] =  unit
		if measurementclass!=None:
			dir["measurementclass"] = measurementclass
		dir["value_type"] = type(value).__name__
		if keyword == 'LastSavedDateTime' or keyword == 'OriginalDateTime':
			dir['value_type']= 'dateTime'

		if dir["value"] != None:
			if len(str(dir["value"])) != 0:
				if includeonlypropswithuri and "uri" in dir:
					dem_infos[keyword] = {}		
					dem_infos[keyword] = dir
				if not includeonlypropswithuri:			
					dem_infos[keyword] = {}
					dem_infos[keyword] = dir

	def infos_dem_setup (keyword, beschreibung,value, unit, description, uri, measurementclass, from_application ='true'):
		dir = {}
		dir.clear()
		dir["value"] = value
		dir["key_deu"] = beschreibung
		dir["from_application"]= from_application
		if  description != None:
			dir["key_eng"] =  description
		if  uri != None:
			dir["uri"] =  uri
		if  unit != None:
			dir["unit"] =  unit
		if measurementclass!=None:
			dir["measurementclass"] = measurementclass
		dir["value_type"] = type(value).__name__
		if keyword == 'LastSavedDateTime' or keyword == 'OriginalDateTime':
			dir['value_type']= 'dateTime'

		if dir["value"] != None:
			if len(str(dir["value"])) != 0:
				if includeonlypropswithuri and "uri" in dir:
					dem_setup[keyword] = {}		
					dem_setup[keyword] = dir
				if not includeonlypropswithuri:			
					dem_setup[keyword] = {}
					dem_setup[keyword] = dir

	def infos_orthomosaic (keyword, beschreibung,value, unit, description, uri, measurementclass, from_application ='true'):
		dir = {}
		dir.clear()
		dir["value"] = value
		dir["key_deu"] = beschreibung
		dir["from_application"]= from_application
		if  description != None:
			dir["key_eng"] =  description
		if  uri != None:
			dir["uri"] =  uri
		if  unit != None:
			dir["unit"] =  unit
		if measurementclass!=None:
			dir["measurementclass"] = measurementclass
		dir["value_type"] = type(value).__name__
		if keyword == 'LastSavedDateTime' or keyword == 'OriginalDateTime':
			dir['value_type']= 'dateTime'

		if dir["value"] != None:
			if len(str(dir["value"])) != 0:
				if includeonlypropswithuri and "uri" in dir:
					orthomosaic_infos[keyword] = {}		
					orthomosaic_infos[keyword] = dir
				if not includeonlypropswithuri:			
					orthomosaic_infos[keyword] = {}
					orthomosaic_infos[keyword] = dir

	def infos_orthomosaic_setup (keyword, beschreibung,value, unit, description, uri, measurementclass, from_application ='true'):
		dir = {}
		dir.clear()
		dir["value"] = value
		dir["key_deu"] = beschreibung
		dir["from_application"]= from_application
		if  description != None:
			dir["key_eng"] =  description
		if  uri != None:
			dir["uri"] =  uri
		if  unit != None:
			dir["unit"] =  unit
		if measurementclass!=None:
			dir["measurementclass"] = measurementclass
		dir["value_type"] = type(value).__name__
		if keyword == 'LastSavedDateTime' or keyword == 'OriginalDateTime':
			dir['value_type']= 'dateTime'

		if dir["value"] != None:
			if len(str(dir["value"])) != 0:
				if includeonlypropswithuri and "uri" in dir:
					orthomosaic_setup[keyword] = {}		
					orthomosaic_setup[keyword] = dir
				if not includeonlypropswithuri:			
					orthomosaic_setup[keyword] = {}
					orthomosaic_setup[keyword] = dir



	### Start get Informations Chunk 

	for i in range(len(doc.chunks)):
		chunks={}
		chunk_info={}
		list_sensors = []
		alignment ={}
		tiepoint_info= {}
		print(selected_unit) 

		if selected_unit == 'unit_project':
			project_unit =True

		print ("--------")
		print ("chunk")
		print (doc.chunks[i].label)

		# chunk key/ ID
		keyword= "chunk_id"
		beschreibung ="Chunk ID"
		value = doc.chunks[i].key
		description="chunk ID"
		unit = None
		uri= ontologynamespace + 'chunk_id'
		measurementclass=None
		infos_chunk(keyword, beschreibung, value, unit,description, uri, measurementclass)

		# Chunkname
		keyword= "label"
		beschreibung ="Name"
		value = doc.chunks[i].label
		description="name"
		unit = None
		uri= rdfs + 'label'
		measurementclass=None
		infos_chunk(keyword, beschreibung, value, unit,description, uri, measurementclass)

		# Anzahl Bilder 
		keyword= "number_of_cameras"
		beschreibung = "Anzahl Kameras"
		value = len(doc.chunks[i].cameras)
		description="number of cameras"
		unit = None
		uri= ontologynamespace + 'numberOfCameras'
		measurementclass=None
		infos_chunk(keyword, beschreibung, value, unit,description, uri, measurementclass)

		# Anzahl Kalibrierungen
		keyword = 'number_of_calibrations'
		beschreibung = "Anzahl Kalibrierungen"
		value = len(doc.chunks[i].sensors)
		description="number of calibrations"
		unit = None
		uri= None
		measurementclass=None
		infos_chunk(keyword, beschreibung, value, unit,description, uri, measurementclass)

		# Flying altitude Einheit m
		# Ground Resolution Einheit:cm/pixel
		# Coverage area Einheit m²

		# Chunk Koordinatensystem
		keyword= "crs"
		beschreibung = "Koordinatensytem"
		value =doc.chunks[i].crs.name
		description='coordinate system'
		unit = None
		uri= ontologynamespace +'crs'
		measurementclass=None
		infos_chunk(keyword, beschreibung, value, unit,description, uri, measurementclass)

		if project_unit:
			if '(m)' in doc.chunks[i].crs.name:
				selected_unit = 'unit_m'
				print(unit)
			elif'(mm)'in doc.chunks[i].crs.name:
				selected_unit = 'unit_mm'
				print (unit)
			else:
				unit = None

		# # Region 
		keyword= 'region center - x value'
		beschreibung = 'Mittelpunkt Region X Wert'
		#value= 'test'
		value = doc.chunks[i].region.center.x
		description='center of region - x value'
		if selected_unit == "unit_mm":
			unit = om+'millimetre'
		elif selected_unit == "unit_m":
			unit = om+'metre'
		else:
			unit = None		
		uri= ''
		measurementclass=None
		infos_chunk(keyword, beschreibung, value, unit,description, uri, measurementclass)

		keyword= 'region center - y value'
		beschreibung = 'Mittelpunkt Region Y Wert'
		#value= 'test'
		value = doc.chunks[i].region.center.y
		description='center of region - y value'
		if selected_unit == "unit_mm":
			unit = om+'millimetre'
		elif selected_unit == "unit_m":
			unit = om+'metre'
		else:
			unit = None		
		uri= ''
		measurementclass=None
		infos_chunk(keyword, beschreibung, value, unit,description, uri, measurementclass)

		keyword= 'region center - z value'
		beschreibung = 'Mittelpunkt Region Z Wert'
		#value= 'test'
		value = doc.chunks[i].region.center.z
		description='center of region - z value'
		if selected_unit == "unit_mm":
			unit = om+'millimetre'
		elif selected_unit == "unit_m":
			unit = om+'metre'
		else:
			unit = None		
		uri= ''
		measurementclass=None
		infos_chunk(keyword, beschreibung, value, unit,description, uri, measurementclass)

		keyword= 'region size X'
		beschreibung = 'X-Ausdehnungen der Region'
		value = doc.chunks[i].region.size.x
		#value =  'geht nicht'
		description='x dimension of region'
		if selected_unit == "unit_mm":
			unit = om+'millimetre'
		elif selected_unit == "unit_m":
			unit = om+'metre'
		else:
			unit = None		
		uri= ''
		measurementclass=None
		infos_chunk(keyword, beschreibung, value, unit,description, uri, measurementclass)

		keyword= 'region size Y'
		beschreibung = 'Y-Ausdehnungen der Region'
		value = doc.chunks[i].region.size.y
		#value =  'geht nicht'
		description='y dimension of region'
		if selected_unit == "unit_mm":
			unit = om+'millimetre'
		elif selected_unit == "unit_m":
			unit = om+'metre'
		else:
			unit = None		
		uri= ''
		measurementclass=None
		infos_chunk(keyword, beschreibung, value, unit,description, uri, measurementclass)

		keyword= 'region size Z'
		beschreibung = 'Z-Ausdehnungen der Region'
		value = doc.chunks[i].region.size.z
		#value =  'geht nicht'
		description='z dimension of region'
		if selected_unit == "unit_mm":
			unit = om+'millimetre'
		elif selected_unit == "unit_m":
			unit = om+'metre'
		else:
			unit = None		
		uri= ''
		measurementclass=None
		infos_chunk(keyword, beschreibung, value, unit,description, uri, measurementclass)	

		# Projections
		# Reprojection error

		## Alignment Setup

		# Chunk Metadata / align/adaptive_fitting
		keyword= "adaptive_fitting"
		beschreibung = "Adaptive Anpassung"
		if 'align/adaptive_fitting' in doc.chunks[i].meta:
			value =doc.chunks[i].meta['align/adaptive_fitting']
		elif 'AlignCameras/adaptive_fitting' in doc.chunks[i].meta:
			value = doc.chunks[i].meta['AlignCameras/adaptive_fitting']
		else: 
			value = None 
		description='adaptive fitting'
		unit = None
		uri= ontologynamespace +'adaptive_fitting'
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		# Chunk Metadata / optimize/sigma0
		keyword= 'optimize_sigma0'
		beschreibung = 'Optimiert, Sigma0'
		if 'optimize/sigma0' in doc.chunks[i].meta:
			value = doc.chunks[i].meta['optimize/sigma0']
		elif 'OptimizeCameras/sigma0' in doc.chunks[i].meta:
			value = doc.chunks[i].meta['OptimizeCameras/sigma0']
		else:
			value=None
		description='optimize, sigma0'
		unit = None
		uri=ontologynamespace + 'optimize_sigma0'
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		# Chunk Metadata / optimize fit flags
		keyword= 'optimize_fit_flags'
		beschreibung = 'Optimiert, Fit Flags'
		if 'optimize/fit_flags' in doc.chunks[i].meta:
			value = doc.chunks[i].meta['optimize/fit_flags']
		elif 'OptimizeCameras/fit_flags' in doc.chunks[i].meta:
			value = doc.chunks[i].meta['OptimizeCameras/fit_flags']
		else:
			value=None
		description='optimize, fit flags'
		unit = None
		uri= None 
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		# Chunk Metadata / min image
		keyword= 'min_image'
		beschreibung = ''
		if 'AlignCameras/min_image' in doc.chunks[i].meta:
			value = doc.chunks[i].meta['AlignCameras/min_image']
		else:
			value=None
		description='min image'
		unit = None
		uri= None 
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		# Chunk Metadata / reset alignment 
		keyword= 'reset_alignment'
		beschreibung = ''
		if 'AlignCameras/reset_alignment' in doc.chunks[i].meta:
			value = doc.chunks[i].meta['AlignCameras/reset_alignment']
		else:
			value=None
		description='reset alignment'
		unit = None
		uri= None 
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		# Chunk Metadata / AlignCameras/subdivide_task
		keyword= 'subdivide_task'
		beschreibung = ''
		if 'AlignCameras/subdivide_task' in doc.chunks[i].meta:
			value = doc.chunks[i].meta['AlignCameras/subdivide_task']
		else:
			value=None
		description='subdivide task'
		unit = None
		uri= None 
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		# Chunk Metadata / Info/LastSavedDateTime
		keyword= 'LastSavedDateTime'
		beschreibung = 'Zuletzt gespeichert'
		if 'Info/LastSavedDateTime' in doc.chunks[i].meta:
			#value = doc.chunks[i].meta['Info/LastSavedDateTime']
			if not doc.chunks[i].meta['Info/LastSavedDateTime']== None:
				timeobject = time.strptime((doc.chunks[i].meta['Info/LastSavedDateTime']), "%Y:%m:%d %H:%M:%S")
				value = (time.strftime("%Y-%m-%dT%H:%M:%S",timeobject))
			else:
				value = doc.chunks[i].meta['Info/LastSavedDateTime']
		else:
			value=None
		description='last saved date time'
		unit = None
		uri= None 
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		# Chunk Metadata / Info/LastSavedSoftwareVersion
		keyword= 'LastSavedSoftwareVersion'
		beschreibung = 'Zuletzt gespeicherte Softwareversion'
		if 'Info/LastSavedSoftwareVersion' in doc.chunks[i].meta:
			value = doc.chunks[i].meta['Info/LastSavedSoftwareVersion']
		else:
			value=None
		description='last saved software version'
		unit = None
		uri= None 
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		# Chunk Metadata / AlignCameras/network_distribute
		keyword= 'AlignCameras/network_distribute'
		beschreibung = ''
		if 'AlignCameras/network_distribute' in doc.chunks[i].meta:
			value = doc.chunks[i].meta['AlignCameras/network_distribute']
		else:
			value=None
		description='network distribute'
		unit = None
		uri= None 
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)


		### point_cloud.meta # bis metashape app version 1.9.9 (mav)
		### tie_points.meta # ab metashape app version 2.0.0 (mav)

		# 'match/mask_tiepoints'
		keyword= 'mask_tiepoints'
		beschreibung= 'Maske Tiepoints'
		description='Mask tiepoints'
		if mav == "2":	
			if 'match/mask_tiepoints' in doc.chunks[i].tie_points.meta:
				value =doc.chunks[i].tie_points.meta['match/mask_tiepoints']
			else: 
				value =None 
		else:
			if 'match/mask_tiepoints' in doc.chunks[i].point_cloud.meta:
				value =doc.chunks[i].point_cloud.meta['match/mask_tiepoints']
			else: 
				value =None 		
		unit = None
		uri= ontologynamespace + 'mask_tiepoints'
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		# 'match/match_downscale'
		keyword= 'match_downscale'
		beschreibung= ''
		description=''	
		if mav == "2":	
			if 'MatchPhotos/downscale' in doc.chunks[i].tie_points.meta:
				# keyword= 'MatchPhotos/downscale'
				value =doc.chunks[i].tie_points.meta['MatchPhotos/downscale']
			else:
				value= None
		else:
			if 'match/match_downscale' in doc.chunks[i].point_cloud.meta:
				# keyword= 'match/match_downscale'			
				value =doc.chunks[i].point_cloud.meta['match/match_downscale']			
			elif 'MatchPhotos/downscale' in doc.chunks[i].point_cloud.meta:
				# keyword= 'MatchPhotos/downscale'
				value =doc.chunks[i].point_cloud.meta['MatchPhotos/downscale']
			else:
				value= None		
		unit = None
		uri= ontologynamespace + 'match_downscale'
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		# matching_accuracy
		accuracy_values = {"0":"highest", "1":"high", "2": "medium", "4": "low", "8":"lowest"}
		keyword= 'matching_accuracy'
		beschreibung= 'Matching Genauigkeit'
		description='matching accuracy'
		if value in accuracy_values:
			print (accuracy_values[value])
			value = (accuracy_values[value])
		else: 
			value = None 		
		unit = None
		uri= ontologynamespace + 'matchingAccuracy'
		measurementclass=None
		from_application = 'derived from match_downscale'
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass, from_application)

		# 'match/match_filter_mask'
		keyword= 'match_filter_mask'
		beschreibung= 'Filterpunkte nach Maske'
		description='Filter points by mask'
		if mav == "2":
			value = doc.chunks[i].tie_points.meta['match/match_filter_mask']
		else:
			value = doc.chunks[i].point_cloud.meta['match/match_filter_mask']		
		unit = None
		uri= ontologynamespace +'match_filter_masks'
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		#'match/match_point_limit'
		keyword= 'match_point_limit'
		beschreibung= 'Keypunktlimit'
		description='Keypoint limit'
		if mav == "2":
			if 'match/match_point_limit' in doc.chunks[i].tie_points.meta:
				value = doc.chunks[i].tie_points.meta['match/match_point_limit']
			elif 'MatchPhotos/keypoint_limit' in doc.chunks[i].tie_points.meta:
				value = doc.chunks[i].tie_points.meta['MatchPhotos/keypoint_limit']
			else: 
				value = None
		else:
			if 'match/match_point_limit' in doc.chunks[i].point_cloud.meta:
				value = doc.chunks[i].point_cloud.meta['match/match_point_limit']
			elif 'MatchPhotos/keypoint_limit' in doc.chunks[i].point_cloud.meta:
				value = doc.chunks[i].point_cloud.meta['MatchPhotos/keypoint_limit']
			else: 
				value = None		
		uri = ontologynamespace + 'match_point_limit'
		unit = None
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		#'MatchPhotos/keypoint_limit_per_mpx'
		keyword= 'keypoint_limit_per_mpx'
		beschreibung= ''
		description='keypoint_limit per mpx'
		if mav == "2":
			if 'MatchPhotos/keypoint_limit_per_mpx' in doc.chunks[i].tie_points.meta:
				value = doc.chunks[i].tie_points.meta['MatchPhotos/keypoint_limit_per_mpx']
			else: 
				value = None
		else:
			value = None		
		uri = ontologynamespace + 'keypoint_limit_per_mpx'
		unit = None
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)


		#'match/match_preselection_generic'
		keyword= 'match_preselection_generic'
		beschreibung= 'Generische Vorauswahl'
		description='Generic preselection'
		if mav == "2":
			if 'match/match_preselection_generic' in doc.chunks[i].tie_points.meta:
				value = doc.chunks[i].tie_points.meta['match/match_preselection_generic']
			elif 'MatchPhotos/generic_preselection' in doc.chunks[i].tie_points.meta:
				value = doc.chunks[i].tie_points.meta['MatchPhotos/generic_preselection']
			elif 'MatchPhotos/preselection_generic' in doc.chunks[i].tie_points.meta:
				value = doc.chunks[i].tie_points.meta['MatchPhotos/preselection_generic']
			else: 
				value = None
		else:
			if 'match/match_preselection_generic' in doc.chunks[i].point_cloud.meta:
				value = doc.chunks[i].point_cloud.meta['match/match_preselection_generic']
			elif 'MatchPhotos/generic_preselection' in doc.chunks[i].point_cloud.meta:
				value = doc.chunks[i].point_cloud.meta['MatchPhotos/generic_preselection']
			elif 'MatchPhotos/preselection_generic' in doc.chunks[i].point_cloud.meta:
				value = doc.chunks[i].point_cloud.meta['MatchPhotos/preselection_generic']
			else: 
				value = None		
		unit = None
		uri= ontologynamespace +'match_preselection_generic'
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		#'match/match_tiepoint_limit'
		keyword= 'match_tiepoint_limit'
		beschreibung= 'Tiepunktlimit'
		description='tiepoint limit'
		if mav == "2":
			if 'match/match_tiepoint_limit' in doc.chunks[i].tie_points.meta:
				value = doc.chunks[i].tie_points.meta['match/match_tiepoint_limit']
			elif 'MatchPhotos/tiepoint_limit' in doc.chunks[i].tie_points.meta:
				value = doc.chunks[i].tie_points.meta['MatchPhotos/tiepoint_limit']
			else: 
				value = None 
		else:
			if 'match/match_tiepoint_limit' in doc.chunks[i].point_cloud.meta:
				value = doc.chunks[i].point_cloud.meta['match/match_tiepoint_limit']
			elif 'MatchPhotos/tiepoint_limit' in doc.chunks[i].point_cloud.meta:
				value = doc.chunks[i].point_cloud.meta['MatchPhotos/tiepoint_limit']
			else: 
				value = None 
		unit = None
		uri= ontologynamespace + 'match_tiepoint_limit'
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		#### since version 2 point_cloud = tie_clouds
		# Chunk Poincloud Meta /Info/LastSavedDateTime
		# Chunk Poincloud Meta /Info/LastSavedSoftwareVersion
		# Chunk Poincloud Meta /Info/OriginalDateTime
		# Chunk Poincloud Meta /Info/OriginalSoftwareVersion
		# Chunk TiePoints Meta / MatchPhotos/ram_used
		# Chunk TiePoints Meta / MatchPhotos/duration

		# Chunk Poincloud Meta /MatchPhotos/max_workgroup_size
		keyword= 'max_workgroup_size'
		beschreibung= ''
		description=''
		if mav =="2":
			if 'MatchPhotos/max_workgroup_size' in doc.chunks[i].tie_points.meta:
				value = doc.chunks[i].tie_points.meta['MatchPhotos/max_workgroup_size']
			else: 
				value = None
		else:
			if 'MatchPhotos/max_workgroup_size' in doc.chunks[i].point_cloud.meta:
				value = doc.chunks[i].point_cloud.meta['MatchPhotos/max_workgroup_size']
			else: 
				value = None
		unit = None
		uri= None
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		# Chunk Poincloud Meta /MatchPhotos/network_distribute
		keyword= 'network_distribute'
		beschreibung= ''
		description='network distribute'
		if mav ==  "2":
			if 'MatchPhotos/network_distribute' in doc.chunks[i].tie_points.meta:
				value = doc.chunks[i].tie_points.meta['MatchPhotos/network_distribute']
			else: 
				value = None 
		else:
			if 'MatchPhotos/network_distribute' in doc.chunks[i].point_cloud.meta:
				value = doc.chunks[i].point_cloud.meta['MatchPhotos/network_distribute']
			else: 
				value = None 
		unit = None
		uri= None
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)
		
		# Chunk Poincloud Meta /MatchPhotos/reset_matches
		keyword= 'reset_matches'
		beschreibung= ''
		description='reset matches'
		if mav =="2":
			if 'MatchPhotos/reset_matches' in doc.chunks[i].tie_points.meta:
				value = doc.chunks[i].tie_points.meta['MatchPhotos/reset_matches']
			else: 
				value = None 
		else:
			if 'MatchPhotos/reset_matches' in doc.chunks[i].point_cloud.meta:
				value = doc.chunks[i].point_cloud.meta['MatchPhotos/reset_matches']
			else: 
				value = None 
		unit = None
		uri= None
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		# Chunk Poincloud Meta /MatchPhotos/store_keypoints
		keyword= 'store_keypoints'
		beschreibung= ''
		description='store keypoints'
		if mav =="2":
			if 'MatchPhotos/store_keypoints' in doc.chunks[i].tie_points.meta:
				value = doc.chunks[i].tie_points.meta['MatchPhotos/store_keypoints']
			else: 
				value = None 
		else:
			if 'MatchPhotos/store_keypoints' in doc.chunks[i].point_cloud.meta:
				value = doc.chunks[i].point_cloud.meta['MatchPhotos/store_keypoints']
			else: 
				value = None 
		
		unit = None
		uri= None
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		# Chunk Poincloud Meta /MatchPhotos/workitem_size_cameras
		keyword= 'workitem_size_cameras'
		beschreibung=''
		description=''
		if mav == "2":
			if 'MatchPhotos/workitem_size_cameras' in doc.chunks[i].tie_points.meta:
				value = doc.chunks[i].tie_points.meta['MatchPhotos/workitem_size_cameras']
			else: 
				value = None 
		else:
			if 'MatchPhotos/workitem_size_cameras' in doc.chunks[i].point_cloud.meta:
				value = doc.chunks[i].point_cloud.meta['MatchPhotos/workitem_size_cameras']
			else: 
				value = None 
		unit = None
		uri= None
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		# Chunk Poincloud Meta /MatchPhotos/workitem_size_pairs
		keyword= 'workitem_size_pairs'
		beschreibung= ''
		description=''
		if mav == "2":
			if 'MatchPhotos/workitem_size_pairs' in doc.chunks[i].tie_points.meta:
				value = doc.chunks[i].tie_points.meta['MatchPhotos/workitem_size_pairs']
			else: 
				value = None 
		else:
			if 'MatchPhotos/workitem_size_pairs' in doc.chunks[i].point_cloud.meta:
				value = doc.chunks[i].point_cloud.meta['MatchPhotos/workitem_size_pairs']
			else: 
				value = None 
		
		unit = None
		uri= None
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)
		
		# Chunk Poincloud Meta /match/match_select_pairs
		keyword= 'match_select_pairs'
		beschreibung= ''
		description='match select pairs'
		if mav == "2":	
			if 'match/mask_tiepoints' in doc.chunks[i].tie_points.meta:
				value =doc.chunks[i].tie_points.meta['match/mask_tiepoints']
			else: 
				value =None 
		else:
			if 'match/mask_tiepoints' in doc.chunks[i].point_cloud.meta:
				value =doc.chunks[i].point_cloud.meta['match/mask_tiepoints']
			else: 
				value =None 		
		unit = None
		uri= None
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		#MatchPhotos/descriptor_type
		keyword= 'descriptor_type'
		beschreibung= ''
		description='descriptor type'
		if mav == "2":
			if 'MatchPhotos/descriptor_type' in doc.chunks[i].tie_points.meta:
				value = doc.chunks[i].tie_points.meta['MatchPhotos/descriptor_type']
			else: 
				value = None 
		else:
			if 'MatchPhotos/descriptor_type' in doc.chunks[i].point_cloud.meta:
				value = doc.chunks[i].point_cloud.meta['MatchPhotos/descriptor_type']
			else: 
				value = None 
		
		unit = None
		uri= None
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		#MatchPhotos/descriptor_version
		keyword= 'descriptor_version'
		beschreibung= ''
		description='descriptor version'
		if mav == "2":
			if 'MatchPhotos/descriptor_version' in doc.chunks[i].tie_points.meta:
				value = doc.chunks[i].tie_points.meta['MatchPhotos/descriptor_version']
			else: 
				value = None 
		else:
			if 'MatchPhotos/descriptor_version' in doc.chunks[i].point_cloud.meta:
				value = doc.chunks[i].point_cloud.meta['MatchPhotos/descriptor_version']
			else: 
				value = None 
		
		unit = None
		uri= None
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		#MatchPhotos/filter_stationary_points
		keyword= 'filter_stationary_points'
		beschreibung= ''
		description='filter stationary points'
		if mav == "2":
			if 'MatchPhotos/filter_stationary_points' in doc.chunks[i].tie_points.meta:
				value = doc.chunks[i].tie_points.meta['MatchPhotos/filter_stationary_points']
			else: 
				value = None 
		else:
			if 'MatchPhotos/filter_stationary_points' in doc.chunks[i].point_cloud.meta:
				value = doc.chunks[i].point_cloud.meta['MatchPhotos/filter_stationary_points']
			else: 
				value = None 
		
		unit = None
		uri= None
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		#MatchPhotos/guided_matching
		keyword= 'guided_matching'
		beschreibung= ''
		description='guided matching'
		if mav == "2":
			if 'MatchPhotos/guided_matching' in doc.chunks[i].tie_points.meta:
				value = doc.chunks[i].tie_points.meta['MatchPhotos/guided_matching']
			else: 
				value = None 
		else:
			if 'MatchPhotos/guided_matching' in doc.chunks[i].point_cloud.meta:
				value = doc.chunks[i].point_cloud.meta['MatchPhotos/guided_matching']
			else: 
				value = None 		
		unit = None
		uri= None
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		#MatchPhotos/keep_keypoints
		keyword= 'keep_keypoints'
		beschreibung= ''
		description='keep keypoints'
		if mav == "2":
			if 'MatchPhotos/keep_keypoints' in doc.chunks[i].tie_points.meta:
				value = doc.chunks[i].tie_points.meta['MatchPhotos/keep_keypoints']
			else: 
				value = None 
		else:
			if 'MatchPhotos/keep_keypoints' in doc.chunks[i].point_cloud.meta:
				value = doc.chunks[i].point_cloud.meta['MatchPhotos/keep_keypoints']
			else: 
				value = None 		
		unit = None
		uri= None
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		#MatchPhotos/reference_preselection
		keyword= 'reference_preselection'
		beschreibung= ''
		description='reference_preselection'
		if mav == "2":
			if 'MatchPhotos/reference_preselection' in doc.chunks[i].tie_points.meta:
				value = doc.chunks[i].tie_points.meta['MatchPhotos/reference_preselection']
			else: 
				value = None 
		else:
			if 'MatchPhotos/reference_preselection' in doc.chunks[i].point_cloud.meta:
				value = doc.chunks[i].point_cloud.meta['MatchPhotos/reference_preselection']
			else: 
				value = None 		
		unit = None
		uri= None
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		#MatchPhotos/reference_preselection_mode
		keyword= 'reference_preselection_mode'
		beschreibung= ''
		description='reference preselection mode'
		if mav =="2":
			if 'MatchPhotos/reference_preselection_mode' in doc.chunks[i].tie_points.meta:
				value = doc.chunks[i].tie_points.meta['MatchPhotos/reference_preselection_mode']
			else: 
				value = None
		else:
			if 'MatchPhotos/reference_preselection_mode' in doc.chunks[i].point_cloud.meta:
				value = doc.chunks[i].point_cloud.meta['MatchPhotos/reference_preselection_mode']
			else: 
				value = None 
		unit = None
		uri= None
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

		#MatchPhotos/subdivide_task
		keyword= 'subdivide_task'
		beschreibung= ''
		description='subdivide task'
		if mav =="2":
			if 'MatchPhotos/subdivide_task' in doc.chunks[i].tie_points.meta:
				value = doc.chunks[i].tie_points.meta['MatchPhotos/subdivide_task']
			else: 
				value = None 
		else:
			if 'MatchPhotos/subdivide_task' in doc.chunks[i].point_cloud.meta:
				value = doc.chunks[i].point_cloud.meta['MatchPhotos/subdivide_task']
			else: 
				value = None 
		unit = None
		uri= None
		measurementclass=None
		infos_alignment_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)


		## Tiepoint Information

		# Anzahl Punkte
		keyword= 'number_of_tiepoints'
		beschreibung= 'Anzahl Tiepunkte'
		if mav == '2':
			value = len(doc.chunks[i].tie_points.points)
		else:
			value = len(doc.chunks[i].point_cloud.points)
		description='number of tiepoints'
		unit = None
		uri= ontologynamespace + 'numberOfTiepoints'
		measurementclass=None
		infos_tiepoints(keyword, beschreibung, value, unit,description, uri, measurementclass)


		## DenseCloud Information

		list_densecloud =[]

		if mav == '2':
			if (len(doc.chunks[i].point_clouds)) > 0:
				for d in range(len(doc.chunks[i].point_clouds)):
					denseclouds={}
					densecloud_info= {}
					densecloud_setup = {} 
					densecloud = doc.chunks[i].point_clouds[d]
		else:
			if (len(doc.chunks[i].dense_clouds)) > 0:
				for d in range(len(doc.chunks[i].dense_clouds)):
					denseclouds={}
					densecloud_info= {}
					densecloud_setup = {} 
					densecloud = doc.chunks[i].dense_clouds[d]





				print ("-------")
				print ("densecloud")
				print (densecloud.label)

				## Dense Cloud informationen 
				keyword= 'label'
				beschreibung= 'Name'
				value = densecloud.label
				description='name'
				unit = None
				uri= rdfs +'label'
				measurementclass=None
				infos_densecloud(keyword, beschreibung, value, unit,description, uri, measurementclass)

				# id 
				keyword= 'densecloud_id'
				beschreibung= 'Densecloud ID'
				value = densecloud.key
				description='densecloud ID'
				unit = None
				uri= ontologynamespace +'densecloud_id'
				measurementclass= None
				infos_densecloud(keyword, beschreibung, value, unit,description, uri, measurementclass)

				keyword= 'number of points'
				beschreibung= 'Anzahl Punkte'
				value = doc.chunks[i].dense_cloud.point_count
				description='number of points'
				unit = None
				uri= ontologynamespace + 'numberOfPoints'
				measurementclass=None
				infos_densecloud(keyword, beschreibung, value, unit,description, uri, measurementclass)

				## densecloud setup 
				# keep depth 
				keyword= 'keep_depth'
				beschreibung= ''
				value = densecloud.meta['BuildDenseCloud/keep_depth']
				description=''
				unit = None
				uri= None
				measurementclass=None
				infos_dc_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

				keyword= 'max_neighbors'
				beschreibung= ''
				value = densecloud.meta['BuildDenseCloud/max_neighbors']
				description=''
				unit = None
				uri= None
				measurementclass=None
				infos_dc_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

				keyword= 'max_workgroup_size'
				beschreibung= ''
				value = densecloud.meta['BuildDenseCloud/max_workgroup_size']
				description=''
				unit = None
				uri= None
				measurementclass=None
				infos_dc_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

				keyword= 'point_colors'
				beschreibung= 'Berechne Punktfarben'
				value = densecloud.meta['BuildDenseCloud/point_colors']
				description='calculate point Colors'
				unit = None
				uri= None
				measurementclass=None
				infos_dc_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

				keyword= 'point_confidence'
				beschreibung= 'Berechne Punkt Konfidenz'
				value = densecloud.meta['BuildDenseCloud/point_confidence']
				description='calculate point confidence'
				unit = None
				uri= None
				measurementclass=None
				infos_dc_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

				keyword= 'resolution'
				beschreibung= ''
				value = densecloud.meta['BuildDenseCloud/resolution']
				description=''
				unit = None
				uri= None
				measurementclass=None
				infos_dc_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

				keyword= 'subdivide_task'
				beschreibung= ''
				value = densecloud.meta['BuildDenseCloud/subdivide_task']
				description=''
				unit = None
				uri= None
				measurementclass=None
				infos_dc_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

				keyword= 'BuildDepthMaps_downscale'
				beschreibung= ''
				value = densecloud.meta['BuildDepthMaps/downscale']
				description=''
				unit = None
				uri= None
				measurementclass=None
				infos_dc_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

				keyword= 'filter_mode'
				beschreibung= 'Filtermodus'
				value = densecloud.meta['BuildDepthMaps/filter_mode']
				description='Filtering mode'
				unit = None
				uri= None
				measurementclass=None
				infos_dc_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

				keyword= 'max_neighbors'
				beschreibung= ''
				value = densecloud.meta['BuildDepthMaps/max_neighbors']
				description=''
				unit = None
				uri= None
				measurementclass=None
				infos_dc_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

				keyword= 'max_workgroup_size'
				beschreibung= ''
				value = densecloud.meta['BuildDepthMaps/max_workgroup_size']
				description=''
				unit = None
				uri= None
				measurementclass=None
				infos_dc_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

				keyword= 'reuse_depth'
				beschreibung= ''
				value = densecloud.meta['BuildDepthMaps/reuse_depth']
				description=''
				unit = None
				uri= None
				measurementclass=None
				infos_dc_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

				keyword= 'subdivide_task'
				beschreibung= ''
				value = densecloud.meta['BuildDepthMaps/subdivide_task']
				description=''
				unit = None
				uri= None
				measurementclass=None
				infos_dc_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

				keyword= 'workitem_size_cameras'
				beschreibung= ''
				value = densecloud.meta['BuildDepthMaps/workitem_size_cameras']
				description=''
				unit = None
				uri= None
				measurementclass=None
				infos_dc_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

				keyword= 'LastSavedDateTime'
				beschreibung= 'Zuletzt gespeichertes Datum Zeit'
				if not densecloud.meta['Info/LastSavedDateTime']== None:
					timeobject = time.strptime((densecloud.meta['Info/LastSavedDateTime']), "%Y:%m:%d %H:%M:%S")
					value = (time.strftime("%Y-%m-%dT%H:%M:%S",timeobject))
				else:
					value = densecloud.meta['Info/LastSavedDateTime']
				description='last saved date time'
				unit = None
				uri= None
				measurementclass=None
				infos_dc_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

				keyword= 'LastSavedSoftwareVersion'
				beschreibung= 'Zuletzt gespeicherte Softwareversion'
				value = densecloud.meta['Info/LastSavedSoftwareVersion']
				description='last saved software version'
				unit = None
				uri= None
				measurementclass=None
				infos_dc_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

				keyword= 'OriginalDateTime'
				beschreibung= 'Original Datum Zeit'
				if not densecloud.meta['Info/OriginalDateTime']== None:
					timeobject = time.strptime((densecloud.meta['Info/OriginalDateTime']), "%Y:%m:%d %H:%M:%S")
					value = (time.strftime("%Y-%m-%dT%H:%M:%S",timeobject))
				else:
					value = densecloud.meta['Info/OriginalDateTime']
				description='original date time'
				unit = None
				uri= None
				measurementclass=None
				infos_dc_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

				keyword= 'OriginalSoftwareVersion'
				beschreibung= 'Originale Softwareversion'
				value = densecloud.meta['Info/OriginalSoftwareVersion']
				description='original software version'
				unit = None
				uri= None
				measurementclass=None
				infos_dc_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

				if len(densecloud_info) >0:
					denseclouds['densecloud_information']= densecloud_info
				if len(densecloud_setup) >0:
					denseclouds['densecloud_setup']= densecloud_setup
				if len(denseclouds) >0:
					list_densecloud.append(denseclouds)
		
		
		## Kalibrierinformations 

		for m in range(len(doc.chunks[i].sensors)):

			kali={}
			kali_infos={}
			kali_cd ={}
			kali_setup ={}
			kali_properties={}
			sensor = doc.chunks[i].sensors[m]

			# Werte aus dem Report
			# Sensortyp 
			keyword= 'sensortype'
			beschreibung= 'Sensortyp'
			value = sensor.label
			description='sensor type'
			unit = None
			uri= ontologynamespace + 'sensortype'
			measurementclass=None
			infos_sensor(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# sensor label 
			keyword= 'name'
			beschreibung= 'Name'
			value = sensor.label
			description='name'
			unit = None
			uri= rdfs + 'label'
			measurementclass=None
			infos_sensor(keyword, beschreibung, value, unit,description, uri, measurementclass)	

			# sensor id 
			keyword= 'sensor_id'
			beschreibung= 'Sensor ID'
			value = sensor.key
			description='sensor ID'
			unit = None
			uri= ontologynamespace +'sensor_id'
			measurementclass=None
			infos_sensor(keyword, beschreibung, value, unit,description, uri, measurementclass)			

			# focal length 
			keyword= 'focal_length'
			beschreibung= 'Sensorbrennweite'
			value = sensor.focal_length
			description='sensor focal length'
			unit = om+'millimetre'
			uri= ontologynamespace +'FocalLengthCamera'
			measurementclass=None
			infos_sensor(keyword, beschreibung, value, unit,description, uri, measurementclass)		

			# Pixel width
			keyword= 'pixel_width'
			beschreibung= 'Pixelbreite'
			value = sensor.pixel_width
			description='pixelwidth'
			unit = om+'millimetre'
			uri= ontologynamespace +'pixel_width'
			measurementclass=None
			infos_sensor(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# Pixel height
			keyword= 'pixel_height'
			beschreibung= 'Pixelhöhe'
			value = sensor.pixel_height
			description='pixelheight'
			unit = om+'millimetre'
			uri= ontologynamespace +'pixel_height'
			measurementclass=None
			infos_sensor(keyword, beschreibung, value, unit,description, uri, measurementclass)

			## sensor setup
			# sensor fixed
			keyword= 'fixed_calibration'
			beschreibung= 'Feste Kalibrierung'
			value = sensor.fixed_calibration
			description='fixed calibration'
			unit = None
			uri= ontologynamespace + 'fixed_calibration'
			measurementclass=None
			infos_kali_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)			

			# sensor fixed parameters
			if sensor.fixed_calibration == True:
				keyword= 'fixed_params'
				beschreibung= 'Feste Parameter'
				value = sensor.fixed_params
				description='fixed parameter'
				unit = None
				uri= None
				measurementclass=None
				infos_kali_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# # Parameter innere Orientierung 
			# Adjusted 
			# Focal length
			keyword= 'focal_length'
			beschreibung= 'Brennweite'
			value = sensor.calibration.f
			description='focal length'
			unit = om +'pixel'
			uri= exifnamespace + 'focalLength'
			measurementclass=None
			infos_kali_properties(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# cx
			keyword= 'principal_point_x_coordinate'
			beschreibung= 'Bildhauptpunkt X Koordinate'
			value = sensor.calibration.cx
			description="principal point x coordinate"
			unit = om +':pixel'
			uri= ontologynamespace +'PrincipalPointXCoordinate'
			measurementclass=None
			infos_kali_properties(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# cy
			keyword= 'principal_point_y_coordinate'
			beschreibung= 'Bildhauptpunkt Y Koordinate'
			value = sensor.calibration.cy
			description="principal point y coordinate"
			unit = om +'pixel'
			uri= ontologynamespace +'PrincipalPointYCoordinate'
			measurementclass=None
			infos_kali_properties(keyword, beschreibung, value, unit,description, uri, measurementclass)
			
			# b1
			keyword= 'radial_distortion_coefficient_b1'
			beschreibung= 'Radialer Verzerrungskoeffizient B1'
			value = sensor.calibration.b1
			description="radial distortion coefficient b1"
			unit = om +'pixel'
			uri= ontologynamespace +'RadialDistortionCoefficientB2'
			measurementclass=None
			infos_kali_properties(keyword, beschreibung, value, unit,description, uri, measurementclass)
			
			# b2
			keyword= 'radial_distortion_coefficient_b2'
			beschreibung= 'Radialer Verzerrungskoeffizient B2'
			value = sensor.calibration.b2
			description="radial distortion coefficient b2"
			unit = om + 'pixel'
			uri= ontologynamespace +'RadialDistortionCoefficientB2'
			measurementclass=None
			infos_kali_properties(keyword, beschreibung, value, unit,description, uri, measurementclass)
			
			# k1
			keyword= 'radial distortion coefficient k1'
			beschreibung= 'Radialer Verzerrungskoeffizient K1'
			value = sensor.calibration.k1
			description="radial distortion coefficient k1"
			unit = om +'pixel'
			uri= ontologynamespace +'RadialDistortionCoefficientK1'
			measurementclass=None
			infos_kali_properties(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# k2 
			keyword= 'radial_distortion_coefficient_k2'
			beschreibung= 'Radialer Verzerrungskoeffizient K2'
			value = sensor.calibration.k2
			description="radial distortion coefficient k2"
			unit = om + 'pixel'
			uri= ontologynamespace +'RadialDistortionCoefficientK2'
			measurementclass=None
			infos_kali_properties(keyword, beschreibung, value, unit,description, uri, measurementclass)
			
			# k3
			keyword= 'radial_distortion_coefficient_k3'
			beschreibung= 'Radialer Verzerrungskoeffizient K3'
			value = sensor.calibration.k3
			description="radial distortion coefficient k3"
			unit = om +'pixel'
			uri= ontologynamespace +'RadialDistortionCoefficientK3'
			measurementclass=None
			infos_kali_properties(keyword, beschreibung, value, unit,description, uri, measurementclass)
			
			# k4 
			keyword= 'radial_distortion_coefficient_k4'
			beschreibung= 'Radialer Verzerrungskoeffizient K4'
			value = sensor.calibration.k4
			description="radial distortion coefficient k4"
			unit = om +'pixel'
			uri= ontologynamespace +'RadialDistortionCoefficientK4'
			measurementclass=None
			infos_kali_properties(keyword, beschreibung, value, unit,description, uri, measurementclass)
				
			# p1
			keyword= 'tangential_distortion_coefficient_p1'
			beschreibung= 'Tangentialer Verzerrungskoeffizient P1'
			value = sensor.calibration.p1
			description="tangential distortion coefficient p1"
			unit = om +'pixel'
			uri= ontologynamespace +'TangentialDistortionCoefficientP1'
			measurementclass=None
			infos_kali_properties(keyword, beschreibung, value, unit,description, uri, measurementclass)
			
			# p2
			keyword= 'tangential_distortion_coefficient_p2'
			beschreibung= 'Tangentialer Verzerrungskoeffizient P2'
			value = sensor.calibration.p2
			description="tangential distortion coefficient p2"
			unit = om +'pixel'
			uri= ontologynamespace +'TangentialDistortionCoefficientP2'
			measurementclass=None
			infos_kali_properties(keyword, beschreibung, value, unit,description, uri, measurementclass)
			
			# p3 
			keyword= 'tangential_distortion_coefficient_p3'
			beschreibung= 'Tangentialer Verzerrungskoeffizient P3'
			value = sensor.calibration.p3
			description="tangential distortion coefficient p3"
			unit = om + 'pixel'
			uri= ontologynamespace +'TangentialDistortionCoefficientP3'
			measurementclass=None
			infos_kali_properties(keyword, beschreibung, value, unit,description, uri, measurementclass)
			
			# p4 
			keyword= 'tangential_distortion_coefficient_p4'
			beschreibung= 'Tangentialer Verzerrungskoeffizient P4'
			value = sensor.calibration.p4
			description="tangential distortion coefficient p4"
			unit = om +'pixel'
			uri= ontologynamespace +'TangentialDistortionCoefficientP4'
			measurementclass=None
			infos_kali_properties(keyword, beschreibung, value, unit,description, uri, measurementclass)
			
			# height
			keyword= 'image_height'
			beschreibung= 'Bildhöhe'
			value = sensor.calibration.height
			description='image height'
			unit = om +'pixel'
			uri= exifnamespace +'imageLength'
			measurementclass=None
			infos_kali_properties(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# width
			keyword= 'image_width'
			beschreibung= 'Bildbreite'
			value = sensor.calibration.width
			description='image width'
			unit = om + 'pixel'
			uri= exifnamespace +'imageWidth'
			measurementclass=None
			infos_kali_properties(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# # error (point,proj)
			# keyword= 'error'
			# beschreibung= 'error'
			# value = sensor.calibration.error
			# description=None
			# unit = None
			# uri= None
			# measurementclass=None
			# infos_kali_properties(keyword, beschreibung, value, unit,description, uri, measurementclass)
			
			# # covariance_matrix
			keyword= 'covariance_matrix'
			beschreibung= 'Kovarianzmatrix'
			value =str(sensor.calibration.covariance_matrix)
			description='covariance matrix'
			unit = om+'millimetre'
			uri= ontologynamespace +'covariance_matrix'
			measurementclass=None
			infos_kali_properties(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# covariance_params
			keyword= 'covariance_param'
			beschreibung= 'Kovarianzmatrix Parameter'
			value = sensor.calibration.covariance_params
			description='covariance matrix parameter'
			unit = None
			uri= ontologynamespace +'covariance_param'
			measurementclass=None
			infos_kali_properties(keyword, beschreibung, value, unit,description, uri, measurementclass)

			if len(kali_setup)>0:
				kali_infos['cal_setup']= kali_setup
			if len(kali_properties)>0:
				kali_infos['cal_properties']= kali_properties
			if len(kali_infos)>0:
				kali['calibration']= kali_infos
			if len (kali_cd):
				kali['capturing_device']= kali_cd
			if len(kali)>0:
				list_sensors.append(kali)
		

		## Cameras Informations 

		list_cameras=[]
		for j in range(len(doc.chunks[i].cameras)):
			
			cameras={}
			camera_info={}
			list_local_refpoints=[]
			camera = doc.chunks[i].cameras[j]

			# id
			keyword = 'camera_id'
			beschreibung = "Camera ID"
			value = camera.key
			description= 'camera ID'
			unit = None
			uri= ontologynamespace + 'camera_id'
			measurementclass=None
			if type(value).__name__ == None:
				value_type = "None"
			else:
				value_type = type(value).__name__
			infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type)

			# Name
			keyword = 'label'
			beschreibung = "Name"
			value = camera.label
			description= 'name'
			unit = None
			uri= rdfs + 'label'
			measurementclass=None
			if type(value).__name__ == None:
				value_type = "None"
			else:
				value_type = type(value).__name__
			infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type)
			
			# estimated X
			try:
				camera_est_vektor = doc.chunks[i].transform.matrix.mulp(camera.center)
			except:
				camera_est_vektor =None
			keyword = 'estimated_coordinate_x'
			beschreibung = "Geschätzte Koordinate X"
			if camera_est_vektor != None:
				value = camera_est_vektor[0]
			else: 
				value = None
			description= 'estimated coordinate x'
			#unit
			if selected_unit == "unit_mm":
				unit = om+'millimetre'
			elif selected_unit == "unit_m":
				unit = om+'metre'
			else:
				unit = None				
			uri= ontologynamespace +'EstimatedCoordiateX'
			measurementclass=None
			from_application = 'calculated'
			if type(value).__name__ == None:
				value_type = "None"
			else:
				value_type = type(value).__name__
			infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type, from_application)

			# estimated Y
			keyword = 'estimated_coordinate_y'
			beschreibung = "Geschätzte Koordinate Y"
			if camera_est_vektor != None:
				value = camera_est_vektor[1]
			else: 
				value = None
			description= 'estimated coordinate y'
			if selected_unit == "unit_mm":
				unit = om+'millimetre'
			elif selected_unit == "unit_m":
				unit = om+'metre'
			else:
				unit = None		
			uri= ontologynamespace +'EstimatedCoordiateY'
			measurementclass=None
			from_application = 'calculated'
			if type(value).__name__ == None:
				value_type = "None"
			else:
				value_type = type(value).__name__
			infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type, from_application)

			# estimated Z
			keyword = 'estimated_coordinate_z'
			beschreibung = "Geschätzte Koordinate Z"
			if camera_est_vektor != None:
				value = camera_est_vektor[2]
			else: 
				value = None
			description= 'estimated coordinate z'
			if selected_unit == "unit_mm":
				unit = om+'millimetre'
			elif selected_unit == "unit_m":
				unit = om+'metre'
			else:
				unit = None		
			uri= ontologynamespace +'EstimatedCoordiateZ'
			measurementclass=None
			from_application = 'calculated'
			if type(value).__name__ == None:
				value_type = "None"
			else:
				value_type = type(value).__name__
			infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type, from_application)

			# projections
			# error (pix)

			## Sensor der zu dieser camera gehört
			# id
			keyword = 'sensor_id'
			beschreibung = "Sensor ID"
			value = doc.chunks[i].cameras[j].sensor.key
			description= 'sensor ID'
			unit = None
			uri= ontologynamespace +'sensor_id'
			measurementclass=None
			if type(value).__name__ == None:
				value_type = "None"
			else:
				value_type = type(value).__name__
			infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type)

			##EXIF Infos (bei eingescannten Bildern gibt es kein Exif)
			# Aufnahmedatum Original
			try:				
				keyword = 'DateTimeOriginal'
				beschreibung = "Aufnahmedatum, Uhrzeit, Original"
				description='date, time, original'
				timeobject = time.strptime((doc.chunks[i].cameras[j].photo.meta['Exif/DateTimeOriginal']), "%Y:%m:%d %H:%M:%S")
				value = (time.strftime("%Y-%m-%dT%H:%M:%S",timeobject))
				unit = None
				uri= exifnamespace+'dateTimeOriginal'
				measurementclass=None
				value_type = "dateTime"
				infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type)
			except:
				value = None
			# Wenn die Aufnahmezeit auch noch Dezimalsekunden hat
			try:				
				keyword = 'DateTimeOriginal'
				beschreibung = "Aufnahmedatum, Uhrzeit, Original"
				description='date, time, original'
				timeobject = time.strptime((doc.chunks[i].cameras[j].photo.meta['Exif/DateTimeOriginal']), "%Y:%m:%d %H:%M:%S.%f")
				value = (time.strftime("%Y-%m-%dT%H:%M:%S",timeobject))
				unit = None
				uri= exifnamespace+'dateTimeOriginal'
				measurementclass=None
				value_type = "dateTime"
				infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type)
			except:
				value = None


			# Isowert
			try:
				keyword = 'ISOSpeedRatings'
				beschreibung = "Isowert"
				description='ISOSpeedRatings'
				value = doc.chunks[i].cameras[j].photo.meta['Exif/ISOSpeedRatings']
				unit = exifnamespace + 'isoSpeedRatings'
				uri= None
				measurementclass=None
				if type(value).__name__ == None:
					value_type = "None"
				else:
					value_type = type(value).__name__
				infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type)
			except:
				value = None
		
			# Brennweite
			try:
				keyword = 'FocalLength'
				beschreibung = "Brennweite"
				description='focallength'
				value = doc.chunks[i].cameras[j].photo.meta['Exif/FocalLength']
				unit = om+'millimetre'
				uri= exifnamespace + 'focalLength'
				measurementclass=None
				if type(value).__name__ == None:
					value_type = "None"
				else:
					value_type = type(value).__name__
				infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type)
			except:
				value = None
		
			# Blende
			try:
				keyword = "ApertureValue"
				beschreibung = "Blende"
				description='aperture'
				value = doc.chunks[i].cameras[j].photo.meta['Exif/ApertureValue']
				unit = None
				uri= exifnamespace +'ApertureValue'
				measurementclass=None
				if type(value).__name__ == None:
					value_type = "None"
				else:
					value_type = type(value).__name__
				infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type)
			except:
				value = None

			# Kamerahersteller 
			try:
				keyword = 'Make'
				beschreibung = "Kamera Hersteller"
				description='make'
				value = doc.chunks[i].cameras[j].photo.meta['Exif/Make']
				unit = None
				uri= exifnamespace + 'make'
				measurementclass=None
				if type(value).__name__ == None:
					value_type = "None"
				else:
					value_type = type(value).__name__
				infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type)
			except:
				vallue = None
		
			# Kamera
			try:
				keyword = 'Model'
				beschreibung = "Kamera Model"
				description='model'
				value = doc.chunks[i].cameras[j].photo.meta['Exif/Model']
				unit = None
				uri= exifnamespace + 'model'
				measurementclass=None
				if type(value).__name__ == None:
					value_type = "None"
				else:
					value_type = type(value).__name__
				infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type)
			except:
				value = None

			# Objektiv
			try:				
				keyword = 'FocalLengthIn35mmFilm'
				beschreibung = "FocalLengthIn35mmFilm"
				description="FocalLengthIn35mmFilm"
				value = doc.chunks[i].cameras[j].photo.meta['Exif/FocalLengthIn35mmFilm']
				unit = om+'millimetre'
				uri= exifnamespace + 'focalLengthIn35mmFilm'
				measurementclass=None
				if type(value).__name__ == None:
					value_type = "None"
				else:
					value_type = type(value).__name__
				infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type)
			except:
				value = None

			# Belichtungszeit / Shutter 
			try:
				keyword = 'ExposureTime'
				beschreibung = "Belichtungszeit"
				description='exposure time'
				value = doc.chunks[i].cameras[j].photo.meta['Exif/ExposureTime']
				unit = om +'second-Time'
				uri= exifnamespace +'ExposureTime'
				measurementclass=None
				if type(value).__name__ == None:
					value_type = "None"
				else:
					value_type = type(value).__name__
				infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type)
			except:
				value = None

			# F-Stop 
			try:
				keyword = 'FNumber'
				beschreibung = "Blendenzahl"
				description='fnumber'
				value = doc.chunks[i].cameras[j].photo.meta['Exif/FNumber']
				unit = None
				uri= exifnamespace + 'FNumber'
				measurementclass=None
				if type(value).__name__ == None:
					value_type = "None"
				else:
					value_type = type(value).__name__
				infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type)
			except:
				value = None

			#Exif/FocalPlaneXResolution
			try:
				keyword = 'FocalPlaneXResolution'
				beschreibung = "X Auflösung "
				description='FocalPlaneXResolution'
				value = doc.chunks[i].cameras[j].photo.meta['Exif/FocalPlaneXResolution']
				unit = None
				uri= exifnamespace + 'FocalPlaneXResolution'
				measurementclass=None
				if type(value).__name__ == None:
					value_type = "None"
				else:
					value_type = type(value).__name__
				infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type)
			except:
				value = None

			#Exif/FocalPlaneYResolution
			try:
				keyword = 'FocalPlaneYResolution'
				beschreibung = "Y Auflösung"
				description='FocalPlaneYResolution'
				value = doc.chunks[i].cameras[j].photo.meta['Exif/FocalPlaneYResolution']
				unit = None
				uri= exifnamespace + 'FocalPlaneYResolution'
				measurementclass=None
				if type(value).__name__ == None:
					value_type = "None"
				else:
					value_type = type(value).__name__
				infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type)
			except:
				value = None

			#ShutterSpeedValue
			try:
				keyword = 'ShutterSpeedValue'
				beschreibung = "ShutterSpeedValue"
				description='ShutterSpeedValue'
				value = doc.chunks[i].cameras[j].photo.meta['Exif/ShutterSpeedValue']
				unit = None
				uri= exifnamespace + 'ShutterSpeedValue'
				measurementclass=None
				if type(value).__name__ == None:
					value_type = "None"
				else:
					value_type = type(value).__name__
				infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type)
			except:
				value = None

			#Software
			try:
				keyword = 'Software'
				beschreibung = "Software"
				description='software'
				value = doc.chunks[i].cameras[j].photo.meta['Exif/Software']
				unit = None
				uri= exifnamespace + 'software'
				measurementclass=None
				if type(value).__name__ == None:
					value_type = "None"
				else:
					value_type = type(value).__name__
				infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type)
			except:
				value = None

			#File/ImageHeight
			keyword = 'ImageHeight'
			beschreibung = "Bildhöhe"
			description='image height'
			value = doc.chunks[i].cameras[j].photo.meta['File/ImageHeight']
			unit = None
			uri= exifnamespace + 'imageHeight'
			measurementclass=None
			if type(value).__name__ == None:
				value_type = "None"
			else:
				value_type = type(value).__name__
			infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type)

			#File/ImageWidth
			keyword = 'ImageWidth'
			beschreibung = "Bildbreite"
			description='image width'
			value = doc.chunks[i].cameras[j].photo.meta['File/ImageWidth']
			unit = None
			uri= exifnamespace +'imageWidth'
			measurementclass=None
			if type(value).__name__ == None:
				value_type = "None"
			else:
				value_type = type(value).__name__
			infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type)

			#Exif/LensModel
			try:
				keyword = 'lens model'
				beschreibung = "Linsenmodell"
				description='lens model'
				value = doc.chunks[i].cameras[j].photo.meta['Exif/LensModel']
				unit = None
				uri= None
				measurementclass=None
				if type(value).__name__ == None:
					value_type = "None"
				else:
					value_type = type(value).__name__
				infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type)
			except:
				value = None

			# ## Processing Information 

			# Kamera ausgerichtet 
			keyword = 'enabled'
			beschreibung = "Kamera aktiviert?"
			description= 'camera enabled?'
			unit = None
			uri= ontologynamespace + 'Enabled'
			measurementclass=None
			value = doc.chunks[i].cameras[j].enabled
			if type(value).__name__ == None:
				value_type = "None"
			else:
				value_type = type(value).__name__
			infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type)

			# transformation
			keyword = 'transform'
			beschreibung = "Transformationsmatrix"
			value =str(doc.chunks[i].cameras[j].transform)
			description='transformation matrix'
			unit = None
			uri= None
			measurementclass=None
			if type(value).__name__ == None:
				value_type = "None"
			else:
				value_type = type(value).__name__
			infos_cameras(keyword, beschreibung, value, unit,description, uri, measurementclass, value_type)

			# local refpoints 
			for p in range(len(doc.chunks[i].markers)):
				local_rp = {}

				image_coord= doc.chunks[i].markers[p].projections[doc.chunks[i].cameras[j]]
				if image_coord != None:
					
					# referencepoint_id 
					keyword = 'referencepoint_id'
					beschreibung = "Referenzpunkt ID"
					value =doc.chunks[i].markers[p].key
					description= 'referencepoint id'
					unit = None
					uri= ontologynamespace + 'referencepoint_id'
					measurementclass=None
					infos_local_rp(keyword, beschreibung, value, unit,description, uri, measurementclass)

					# referencepoint_label
					keyword = 'label'
					beschreibung = "Name"
					value =doc.chunks[i].markers[p].label
					description= 'name'
					unit = None
					uri= rdfs + 'label'
					measurementclass=None
					infos_local_rp(keyword, beschreibung, value, unit,description, uri, measurementclass)
	
					# Bildkoordinaten x y 
					keyword = 'coordinate_x'
					beschreibung = "Koordinate X"
					value =image_coord.coord[0]
					description='coordinate x'
					unit = om + 'pixel'
					uri= None
					measurementclass=None
					infos_local_rp(keyword, beschreibung, value, unit,description, uri, measurementclass)

					# Bildkoordinaten x y 
					keyword = 'coordinate_y'
					beschreibung = "Koordinate Y"
					value =image_coord.coord[1]
					description='coordinate_x'
					unit = om +'pixel'
					uri= None
					measurementclass=None
					infos_local_rp(keyword, beschreibung, value, unit,description, uri, measurementclass)

					# marker aktiviert 
					keyword = 'enabled'
					beschreibung = "Aktiviert"
					value =image_coord.pinned
					description='enabled'
					unit = None
					uri= None
					measurementclass=None
					infos_local_rp(keyword, beschreibung, value, unit,description, uri, measurementclass)

					if len(local_rp)>0:
						list_local_refpoints.append(local_rp)

			if len(camera_info)>0:
				cameras["camera_properties"]=camera_info
			if len(list_local_refpoints)>0:
				cameras["referencepoints"]=list_local_refpoints
			if len(cameras)>0:
				list_cameras.append(cameras)

		# Marker Information
		global_rp={}
		global_rp.clear()
		list_rp =[]		
		controlpoints = 0
		checkpoints = 0

		for k in range(len(doc.chunks[i].markers)):
			rp ={}
			rp.clear()

			marker = doc.chunks[i].markers[k]

			# marker label 
			keyword= 'label'
			beschreibung = 'Name'
			value =marker.label
			description= 'name'
			unit = None
			uri= rdfs + 'label'
			measurementclass=None
			individual_marker(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# marker id 
			keyword= 'referencepoint_id'
			beschreibung = 'Referenzpunkt ID'
			value =marker.key
			description= 'reference point ID'
			unit = None
			uri= ontologynamespace + 'referencepoint_id'
			measurementclass=None
			individual_marker(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# Enables/disables the marker
			keyword= 'referencepoint_enabled'
			beschreibung = 'Referenzpunkt verwendet'
			value = marker.enabled
			description='referencepoint enabled'
			unit = None
			uri= ontologynamespace + 'ReferencepointEnabled'
			measurementclass=None
			individual_marker(keyword, beschreibung, value, unit,description, uri, measurementclass)
			
			# marker projections
			keyword= 'projections'
			beschreibung = 'Projektionen'
			value = len(marker.projections)
			description='projections'
			unit = None
			uri= ontologynamespace + 'Projections'
			measurementclass=None
			individual_marker(keyword, beschreibung, value, unit,description, uri, measurementclass)
			
			# enabled reference (belongs to imported (target) coordinates)
			keyword= 'reference_enabled'
			beschreibung = 'Referenzkoordinaten vorhanden'
			value = marker.reference.enabled
			description='reference coordinates exist'
			unit = None
			uri= ontologynamespace + 'ReferenceEnabled'
			measurementclass=None
			individual_marker(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# marker.reference.location 
			# imported coordinates (target)
			# x
			keyword= 'x_reference_location'
			beschreibung = 'importierte X-Koordinate (Soll)'
			try: 
				value = marker.reference.location[0]
			except: 
				value = None 
			description='imported X coordinate (target)'
			if selected_unit == "unit_mm":
				unit = om+'millimetre'
			elif selected_unit == "unit_m":
				unit = om+'metre'
			else:
				unit = None
			uri= ontologynamespace + 'xCoordinate'
			measurementclass=None
			individual_marker(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# y
			keyword= 'y_reference_location'
			beschreibung = 'importierte Y-Koordinate (Soll)'
			try: 
				value = marker.reference.location[1]
			except: 
				value = None 
			description='imported Y coordinate (target)'
			if selected_unit == "unit_mm":
				unit = om+'millimetre'
			elif selected_unit == "unit_m":
				unit = om+'metre'
			else:
				unit = None
			uri= ontologynamespace + 'yCoordinate'
			measurementclass=None
			individual_marker(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# z
			keyword= 'z_reference_location'
			beschreibung = 'importierte Z-Koordinate (Soll)'
			try: 
				value = marker.reference.location[2]
			except: 
				value = None 
			description='imported Z coordinate (target)'
			if selected_unit == "unit_mm":
				unit = om+'millimetre'
			elif selected_unit == "unit_m":
				unit = om+'metre'
			else:
				unit = None
			uri= ontologynamespace + 'zCoordinate'
			measurementclass=None
			individual_marker(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# estimated coordinate x
			keyword= 'x_estimated_coordiate'
			beschreibung = 'Geschätzte Koordinate X'
			try: 
				estimated_vector =  doc.chunks[i].crs.project(doc.chunks[i].transform.matrix.mulp(marker.position)) 
				value = estimated_vector[0]
			except: 
				value = None
			description='estimated coordinate X'
			if selected_unit == "unit_mm":
				unit = om+'millimetre'
			elif selected_unit == "unit_m":
				unit = om+'metre'
			else:
				unit = None
			uri= ontologynamespace + 'EstimatedCoordiateX'
			measurementclass=None
			individual_marker(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# estimated coordinate y
			keyword= 'y_estimated_coordiate'
			beschreibung = 'Geschätzte Koordinate Y'
			try: 
				value = estimated_vector[1]
			except: 
				value = None
			description='estimated coordinate Y'
			if selected_unit == "unit_mm":
				unit = om+'millimetre'
			elif selected_unit == "unit_m":
				unit = om+'metre'
			else:
				unit = None
			uri= ontologynamespace + 'EstimatedCoordiateY'
			measurementclass=None
			individual_marker(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# estimated coordinate z
			keyword= 'z_estimated_coordiate'
			beschreibung = 'Geschätzte Koordinate Z'
			try: 
				value = estimated_vector[2]
			except:
				value= None
			description='estimated coordinate z'
			if selected_unit == "unit_mm":
				unit = om+'millimetre'
			elif selected_unit == "unit_m":
				unit = om+'metre'
			else:
				unit = None
			uri= ontologynamespace + 'EstimatedCoordiateZ'
			measurementclass=None
			individual_marker(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# calculated from extimated and reference
			# only if location exists (target coordinates imported)

			# x error 
			if not marker.reference.location == None:
				keyword= 'x_error'
				beschreibung = 'X Error'
				try:
					error_vector = estimated_vector - marker.reference.location 
					value = error_vector[0]
				except: 
					value: None
				description='error X'
				if selected_unit == "unit_mm":
					unit = om+'millimetre'
				elif selected_unit == "unit_m":
					unit = om+'metre'
				else:
					unit = None
				uri= ontologynamespace + 'XError'
				measurementclass=None
				from_application ='script-based calculation'
			individual_marker(keyword, beschreibung, value, unit,description, uri, measurementclass, from_application)

			# y_error 
			if not marker.reference.location == None:
				keyword= 'y_error'
				beschreibung = 'Y Error'
				try: 
					value = error_vector[1]
				except:
					value= None 
				description='y error'
				if selected_unit == "unit_mm":
					unit = om+'millimetre'
				elif selected_unit == "unit_m":
					unit = om+'metre'
				else:
					unit = None
				uri= ontologynamespace + 'YError'
				measurementclass=None
				from_application ='script-based calculation'
				individual_marker(keyword, beschreibung, value, unit,description, uri, measurementclass, from_application)

			# z error  
			if not marker.reference.location == None:
				keyword= 'z_error'
				beschreibung = 'Error Z'
				try:
					value = error_vector[2]
				except:
					value= None
				description='z error'
				if selected_unit == "unit_mm":
					unit = om+'millimetre'
				elif selected_unit == "unit_m":
					unit = om+'metre'
				else:
					unit = None
				uri= ontologynamespace + 'ZError'
				measurementclass=None
				from_application ='script-based calculation'
				individual_marker(keyword, beschreibung, value, unit,description, uri, measurementclass, from_application)

			# total error (calculated)
			# only if location exists (target coordinates imported)
			if not marker.reference.location == None:
				keyword= 'total_error'
				beschreibung = 'Total Error'
				try: 
					value = math.sqrt(math.pow(error_vector[0],2) + math.pow(error_vector[1],2) +math.pow(error_vector[2],2))
				except: 
					value= None 
				description='total error'
				if selected_unit == "unit_mm":
					unit = om+'millimetre'
				elif selected_unit == "unit_m":
					unit = om+'metre'
				else:
					unit = None
				uri= ontologynamespace + 'TotalError'
				measurementclass=None
				from_application ='script-based calculation'
				individual_marker(keyword, beschreibung, value, unit,description, uri, measurementclass, from_application)

			## marker position im aktuellen frame (pixel?)
			# marker position x
			keyword= 'x_current_frame_position'
			beschreibung = 'x-Postion in der aktuellen Ansicht'
			try:
				value = marker.position[0]
			except:
				value=None
			description='x position in current frame'
			unit = om +'pixel'
			uri= None 
			measurementclass=None
			individual_marker(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# marker position y
			keyword= 'y_current_frame_position'
			beschreibung = 'y-Postion in der aktuellen Ansicht'
			try:
				value = marker.position[1]
			except:
				value=None			
			description='y position in current frame'
			unit = om +'pixel'
			uri= None
			measurementclass=None
			individual_marker(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# marker position z
			keyword= 'z_current_frame_position'
			beschreibung = 'z-Postion in der aktuellen Ansicht'
			try:
				value = marker.position[2]
			except:
				value=None			
			description='z position in current frame'
			unit = om +'pixel'
			uri= None
			measurementclass=None
			individual_marker(keyword, beschreibung, value, unit,description, uri, measurementclass)

			if marker.reference.enabled == True:
				controlpoints = controlpoints + 1
			elif marker.reference.enabled == False:
				checkpoints = checkpoints +1

			if len(rp)>0:
				list_rp.append(rp)		
			if len(list_rp)>0:
				global_rp["referencepoints"]=list_rp


		# global referencepoints information (allgemein)

		rp_info ={}

		# Anzahl Marker (gesamt)
		keyword= "number_of_markers"
		beschreibung = "Anzahl Referenzpunkte"
		value = len(doc.chunks[i].markers)
		description='number of referencepoints'
		unit = None
		uri= ontologynamespace +'numberOfReferencepoints'
		measurementclass=None
		infos_marker(keyword, beschreibung, value, unit,description, uri, measurementclass)

		# Anzahl Control points 
		keyword= "number_of_controlpoints"
		beschreibung = "Anzahl Anschlusspunkte"
		value = controlpoints
		description='number of controlpoints'
		unit = None
		uri= None
		measurementclass=None
		from_application = 'derived from marker enabled'
		infos_marker(keyword, beschreibung, value, unit,description, uri, measurementclass, from_application)

		# Anzahl Checkpoints
		keyword= "number_of_checkpoints"
		beschreibung = "Anzahl Kontrollpunkte"
		value = checkpoints
		description='number of checkpoints'
		unit = None
		uri= None
		measurementclass=None
		from_application = 'derived from marker enabled'
		infos_marker(keyword, beschreibung, value, unit,description, uri, measurementclass, from_application)
		# Error checkpoints m
		# Error controlpoints m 
		# Error checkpoints pixel
		# Error controlpoints pixel 	

		if len(rp_info)>0:
			global_rp["global_referencepoints_information"]=rp_info


		##### SCALEBARS
		list_scalebars = []		
		for sb in range(len(doc.chunks[i].scalebars)):

			# dictionary für jede einzelne Scalebar
			dic_scalebar = {}
			dic_scalebar.clear

			scalebar = doc.chunks[i].scalebars[sb]

			# key 
			keyword= 'scalebar_key'
			beschreibung = 'scalebar id'
			value = scalebar.key
			description= 'Maßstabs ID '
			unit = None
			uri= None
			measurementclass=None
			individual_scalebar(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# label 
			keyword= 'label'
			beschreibung = 'Name'
			value = scalebar.label
			description= 'name'
			unit = None
			uri= rdfs + 'label'
			measurementclass=None
			individual_scalebar(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# point0 
			keyword= 'scalebar_point0'
			beschreibung = 'Anfangspunkt'
			value = scalebar.point0.label
			description= 'startpoint'
			unit = None
			uri= None
			measurementclass=None
			individual_scalebar(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# point1 
			keyword= 'scalebar_point1'
			beschreibung = 'Endpunkt'
			value = scalebar.point1.label
			description= 'endpoint'
			unit = None
			uri= None
			measurementclass=None
			individual_scalebar(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# accuracy 
			keyword= 'scalebar_accuracy'
			beschreibung = 'Genauigkeit'
			value = scalebar.reference.accuracy
			description= 'accuracy'
			if selected_unit == "unit_mm":
				unit = om+'millimetre'
			elif selected_unit == "unit_m":
				unit = om+'metre'
			else:
				unit = None
			uri= None
			measurementclass=None
			individual_scalebar(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# distance 
			keyword= 'scalebar_distance'
			beschreibung = 'Abstand'
			value = scalebar.reference.distance
			description= 'distance'
			if selected_unit == "unit_mm":
				unit = om+'millimetre'
			elif selected_unit == "unit_m":
				unit = om+'metre'
			else:
				unit = None
			uri= None
			measurementclass=None
			individual_scalebar(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# enabled 
			keyword= 'scalebar_enabled'
			beschreibung = 'Wird der Maßstab benutzt'
			value = scalebar.reference.enabled
			description= 'enabled scalebar'
			unit = None
			uri= None
			measurementclass=None
			individual_scalebar(keyword, beschreibung, value, unit,description, uri, measurementclass)

			if len(dic_scalebar)>0:
				list_scalebars.append(dic_scalebar)	
		
		if len(list_scalebars)>0:
			global_rp["scalebars"]=list_scalebars

		### meshes 
		list_meshes =[]
		
		for l in range(len(doc.chunks[i].models)):
			meshes={}
			mesh_info={}
			mesh_setup={}
			texture_info={}

			model= doc.chunks[i].models[l]

			print ("-------")
			print ((len(doc.chunks[i].models)))
			print (model)

			# Model ID
			keyword= 'mesh_id'
			beschreibung = 'Mesh ID'
			value = model.key
			description='mesh ID'
			unit = None
			uri= ontologynamespace + 'mesh_id'
			measurementclass=None
			infos_mesh(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# Name/Label 
			keyword= 'label'
			beschreibung = 'Name'
			value = model.label
			description='name'
			unit = None
			uri= rdfs+'label'
			measurementclass=None
			infos_mesh(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# Anzahl Punkte
			keyword= 'number of points'
			beschreibung = 'Anzahl Punkte'
			value = len(model.vertices)
			description='number of points'
			unit = None
			uri= giganamespace+'TotalNumberOfVertices'
			measurementclass=None
			infos_mesh(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# Anzahl Dreiecke 
			keyword= 'number of triangles'
			beschreibung = 'Anzahl Dreiecke'
			value = len(model.faces)
			description='number of triangles'
			unit = None
			uri= giganamespace+'TotalNumberOfFaces'
			measurementclass=None
			infos_mesh(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# Fläche 
			keyword= 'area'
			beschreibung = 'Fläche'
			value = model.area()
			description='area'
			if selected_unit == "unit_mm":
				unit = om+'squareMillimetre'
			elif selected_unit == "unit_m":
				unit = om+'metre'
			else:
				unit = None	
			uri= giganamespace+'TotalArea'
			measurementclass=None
			infos_mesh(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# berechneter Wert
			# durchschnittlicher Punktabstand 
			keyword= 'average_point_distance'
			beschreibung = 'durchschnittlicher Punktabstand'			
			description='average point distance'
			if selected_unit == "unit_mm":
				unit = om+'millimetre'
			elif selected_unit == "unit_m":
				unit = om+'metre'
			else:
				unit = None		
			uri= ontologynamespace +'AveragePointDistance'
			measurementclass=None
			from_application= "script-based calculation"
			try:
				value =  1/math.sqrt( len(model.vertices) / model.area())
			except:
				value = None
			infos_mesh(keyword, beschreibung, value, unit,description, uri, measurementclass, from_application)

			# Volumen 
			keyword= 'volume'
			beschreibung = 'Volumen'
			value = model.volume()
			print ("Volumen")
			print (model.volume())
			description='volume'
			if selected_unit == "unit_mm":
				unit = om+'cubicMillimetre'
			elif selected_unit == "unit_m":
				unit = om+'cubicMetre'
			else:
				unit = None		
			uri= ontologynamespace+'volume'
			measurementclass=None
			infos_mesh(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# Anzahl Löcher 
			# Min XYZ
			# Max XYZ
			# Textur 
			# Punktfarben

			## Texturing Parameters
			# atlas/atlas_blend_mode
			keyword= 'atlas_blend_mode'
			beschreibung = 'Überlagerungsmodus'
			description='Blending mode'
			if 'atlas/atlas_blend_mode' in model.meta:
				value = model.meta['atlas/atlas_blend_mode']
			else:
				value = None
			unit = None
			uri= ontologynamespace +'blendingmode'
			measurementclass=None
			infos_texturing(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# atlas/atlas_count
			keyword= 'atlas_count'
			beschreibung = 'Anzahl Texturbilder'
			description='number of texture images'
			if 'atlas/atlas_count' in model.meta:
				value = model.meta['atlas/atlas_count']
			elif 'BuildUV/page_count' in model.meta:
				value = model.meta['BuildUV/page_count']
			elif 'BuildUV/texture_count' in model.meta:
				value = model.meta['BuildUV/texture_count']
			else: 
				value= None
			unit = None
			uri= ontologynamespace +'numberOfTextureImages'
			measurementclass=None
			infos_texturing(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# atlas/atlas_height
			keyword= 'atlas_height'
			beschreibung = 'Texturbild Höhe'
			description='texture image height'
			if 'atlas/atlas_height' in model.meta:
				value = model.meta['atlas/atlas_height']
			else:
				value=None
			unit = om + 'pixel'
			uri= ontologynamespace + 'TextureImageHeight'
			measurementclass=None
			infos_texturing(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# atlas/atlas_mapping_mode
			keyword= 'atlas_mapping_mode'
			beschreibung = 'Abbildungsmodus'
			description='Mapping Mode'
			if 'atlas/atlas_mapping_mode' in model.meta:
				value = model.meta['atlas/atlas_mapping_mode']
			if 'BuildUV/mapping_mode' in model.meta:
				value = model.meta['BuildUV/mapping_mode']
			unit = None
			uri= ontologynamespace +'mappingmode'
			measurementclass=None
			infos_texturing(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# atlas/atlas_width
			keyword= 'atlas_width'
			beschreibung = 'Texturbild Breite'
			description='texture image width'
			if 'atlas/atlas_width' in model.meta: 
				value =model.meta['atlas/atlas_width']
			else:
				value =None
			unit = om +'pixel'
			uri= ontologynamespace + 'TextureImageWidth'
			measurementclass=None
			infos_texturing(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# atlas/fill_holes
			keyword= 'fill_holes'
			beschreibung = 'Lochfüllung aktivieren'
			description='Enable hole filling'
			if 'atlas/fill_holes' in model.meta: 
				value = model.meta['atlas/fill_holes']
				if value == 'false':
					value=False
				if value == 'true':
					value=True 
			else: 
				value = None
			unit = None
			uri= ontologynamespace + 'enableHoleFilling'
			measurementclass=None
			infos_texturing(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# atlas/ghosting_filter
			keyword= 'ghosting_filter'
			beschreibung = 'Ghostingfilter aktivieren'
			description='Enable ghosting filter'
			if 'atlas/ghosting_filter' in model.meta:
				value = model.meta['atlas/ghosting_filter']
				if value == 'false':
					value=False
				if value == 'true':
					value=True 
			else:
				value = None 
			unit = None
			uri= ontologynamespace + 'enableGhostingFilter'
			measurementclass=None
			infos_texturing(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildUV/camera
			keyword= 'BuildUV_camera'
			beschreibung = ''
			description='camera'
			value = model.meta['BuildUV/camera']
			unit = None
			uri= None
			measurementclass=None
			infos_texturing(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildUV/adaptive_resolution
			keyword= 'BuildUV_adaptive_resolution'
			beschreibung = ''
			description='adaptive resolution'
			value = model.meta['BuildUV/adaptive_resolution']
			unit = None
			uri= None
			measurementclass=None
			infos_texturing(keyword, beschreibung, value, unit,description, uri, measurementclass)

			## Mesh Setup
			# BuildDepthMaps/downscale
			keyword= 'BuildDepthMaps_downscale'
			beschreibung = ''
			description='BuildDepthMaps downscale'
			value = model.meta['BuildDepthMaps/downscale']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildDepthMaps/filter_mode
			keyword= 'BuildDepthMaps_filter_mode'
			beschreibung = ''
			description='BuildDepthMaps filter mode'
			value = model.meta['BuildDepthMaps/filter_mode']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildDepthMaps/max_neighbors
			keyword= 'BuildDepthMaps_max_neighbors'
			beschreibung = ''
			description='BuildDepthMaps max neighbors'
			value = model.meta['BuildDepthMaps/max_neighbors']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildDepthMaps/max_workgroup_size
			keyword= 'BuildDepthMaps_max_workgroup_size'
			beschreibung = ''
			description='BuildDepthMaps max workgroup size'
			value = model.meta['BuildDepthMaps/max_workgroup_size']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildDepthMaps/reuse_depth
			keyword= 'BuildDepthMaps_reuse_depth'
			beschreibung = ''
			description='BuildDepthMaps reuse depth'
			value = model.meta['BuildDepthMaps/reuse_depth']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildDepthMaps/subdivide_task
			keyword= 'BuildDepthMaps_subdivide_task'
			beschreibung = ''
			description='BuildDepthMaps subdivide task'
			value = model.meta['BuildDepthMaps/subdivide_task']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildDepthMaps/workitem_size_cameras
			keyword= 'BuildDepthMaps/workitem_size_cameras'
			beschreibung = ''
			description='BuildDepthMaps workitem size cameras'
			value = model.meta['BuildDepthMaps/workitem_size_cameras']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildModel/face_count
			keyword= 'BuildModel_face_count'
			beschreibung = ''
			description='BuildModel face_count'
			value = model.meta['BuildModel/face_count']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildModel/face_count_custom
			keyword= 'BuildModel_face_count_custom'
			beschreibung = ''
			description='BuildModel face count custom'
			value = model.meta['BuildModel/face_count_custom']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildModel/interpolation
			keyword= 'BuildModel_interpolation'
			beschreibung = ''
			description='BuildModel interpolation'
			value = model.meta['BuildModel/interpolation']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildModel/keep_depth
			keyword= 'BuildModel_keep_depth'
			beschreibung = ''
			description='BuildModel keep depth'
			value = model.meta['BuildModel/keep_depth']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildModel/max_workgroup_size
			keyword= 'BuildModel/max_workgroup_size'
			beschreibung = ''
			description='BuildModel/max_workgroup_size'
			value = model.meta['BuildModel/max_workgroup_size']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildModel/resolution
			keyword= 'BuildModel_resolution'
			beschreibung = ''
			description='BuildModel resolution'
			value = model.meta['BuildModel/resolution']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildModel/source_data
			keyword= 'BuildModel_source_data'
			beschreibung = ''
			description='BuildModel source data'
			value = model.meta['BuildModel/source_data']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildModel/subdivide_task
			keyword= 'BuildModel_subdivide_task'
			beschreibung = ''
			description='BuildModel subdivide_task'
			value = model.meta['BuildModel/subdivide_task']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildModel/surface_type
			keyword= 'BuildModel_surface_type'
			beschreibung = ''
			description='BuildModel surface_type'
			value = model.meta['BuildModel/surface_type']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildModel/trimming_radius
			keyword= 'BuildModel_trimming_radius'
			beschreibung = ''
			description='BuildModel trimming_radius'
			value = model.meta['BuildModel/trimming_radius']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildModel/vertex_colors
			keyword= 'BuildModel_vertex_colors'
			beschreibung = ''
			description='BuildModel vertex_colors'
			value = model.meta['BuildModel/vertex_colors']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildModel/vertex_confidence
			keyword= 'BuildModel_vertex_confidence'
			beschreibung = ''
			description='BuildModel vertex_confidence'
			value = model.meta['BuildModel/vertex_confidence']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildModel/volumetric_masks
			keyword= 'BuildModel_volumetric_masks'
			beschreibung = ''
			description='BuildModel_volumetric_masks'
			value = model.meta['BuildModel/volumetric_masks']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildModel/workitem_size_cameras
			keyword= 'BuildModel_workitem_size_cameras'
			beschreibung = ''
			description='BuildModel workitem_size_cameras'
			value = model.meta['BuildModel/workitem_size_cameras']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildUV/texture_size
			keyword= 'BuildUV_texture_size'
			beschreibung = ''
			description='BuildUV texture_size'
			value = model.meta['BuildUV/texture_size']
			unit = None
			uri= ontologynamespace + 'TextureImageSize'
			measurementclass=None
			infos_texturing(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# Info/OriginalDateTime
			keyword= 'OriginalDateTime'
			beschreibung = ''
			description='Original Date Time'
			#value = model.meta['Info/OriginalDateTime']
			if not model.meta['Info/OriginalDateTime']== None:
				timeobject = time.strptime((model.meta['Info/OriginalDateTime']), "%Y:%m:%d %H:%M:%S")
				value = (time.strftime("%Y-%m-%dT%H:%M:%S",timeobject))
			else:
				value = model.meta['Info/OriginalDateTime']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# Info/OriginalSoftwareVersion
			keyword= 'OriginalSoftwareVersion'
			beschreibung = ''
			description='Original Software Version'
			value = model.meta['Info/OriginalSoftwareVersion']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# Info/LastSavedDateTime
			keyword= 'LastSavedDateTime'
			beschreibung = ''
			description='last saved date time'
			if not model.meta['Info/LastSavedDateTime']== None:
				timeobject = time.strptime((model.meta['Info/LastSavedDateTime']), "%Y:%m:%d %H:%M:%S")
				value = (time.strftime("%Y-%m-%dT%H:%M:%S",timeobject))
			else:
				value = model.meta['Info/LastSavedDateTime']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# Info/LastSavedSoftwareVersion
			keyword= 'LastSavedSoftwareVersion'
			beschreibung = ''
			description='last saved softwareVersion'
			value = model.meta['Info/LastSavedSoftwareVersion']
			unit = None
			uri= None
			measurementclass=None
			infos_mesh_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			if len(mesh_info)>0:
				meshes["mesh_information"]=mesh_info
			if len(mesh_setup)>0:
				meshes["mesh_setup"]=mesh_setup
			if len(texture_info)>0:
				meshes["texture_setup"]=texture_info
			if len(meshes)>0:
				list_meshes.append(meshes)

		list_dem= []
		for m in range(len(doc.chunks[i].elevations)):
			dem = {}
			dem_infos = {}
			dem_setup = {}
			elevation = doc.chunks[i].elevations[m]

			# id 
			keyword = 'dem_id'
			beschreibung= 'Dem_Id'
			description='dem id'
			value = elevation.key
			unit = None
			uri= None
			measurementclass=None
			infos_dem(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# bottom
			keyword = 'bottom'
			beschreibung= ''
			description='bottom'
			value = elevation.bottom
			unit = None
			uri= None
			measurementclass=None
			infos_dem(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# height
			keyword = 'height'
			beschreibung= ''
			description='height'
			value = elevation.height
			unit = None
			uri= None
			measurementclass=None
			infos_dem(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# max
			keyword = 'max'
			beschreibung= ''
			description='max'
			value = elevation.max
			unit = None
			uri= None
			measurementclass=None
			infos_dem(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# min
			keyword = 'min'
			beschreibung= ''
			description='min'
			value = elevation.min
			unit = None
			uri= None
			measurementclass=None
			infos_dem(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# label
			keyword = 'label'
			beschreibung= ''
			description='name'
			value = elevation.label
			unit = None
			uri= None
			measurementclass=None
			infos_dem(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# left 
			keyword = 'left'
			beschreibung= ''
			description='left'
			value = elevation.left
			if selected_unit == "unit_mm":
				unit = om+'millimetre'
			elif selected_unit == "unit_m":
				unit = om+'metre'
			else:
				unit = None
			uri= None
			measurementclass=None
			infos_dem(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# right
			keyword = 'right'
			beschreibung= ''
			description='right'
			value = elevation.right 
			if selected_unit == "unit_mm":
				unit = om+'millimetre'
			elif selected_unit == "unit_m":
				unit = om+'metre'
			else:
				unit = None
			uri= None
			measurementclass=None
			infos_dem(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# crs
			keyword = 'crs'
			beschreibung= ''
			description='crs'
			value = elevation.crs.name
			if selected_unit == "unit_mm":
				unit = om+'millimetre'
			elif selected_unit == "unit_m":
				unit = om+'metre'
			else:
				unit = None
			uri= None
			measurementclass=None
			infos_dem(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# top
			keyword = 'top'
			beschreibung= ''
			description='top'
			value = elevation.top
			unit = None
			uri= None
			measurementclass=None
			infos_dem(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# width
			keyword = 'width'
			beschreibung= ''
			description='width'
			value = elevation.width
			unit = None
			uri= None
			measurementclass=None
			infos_dem(keyword, beschreibung, value, unit,description, uri, measurementclass)

			## dem Setup ?
			# BuildDem/flip_x
			keyword = 'BuildDem_flip_x'
			beschreibung= ''
			description='BuildDem flip x'
			value = elevation.meta['BuildDem/flip_x']
			unit = None
			uri= None
			measurementclass=None
			infos_dem_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildDem/flip_y
			keyword = 'BuildDem_flip_y'
			beschreibung= ''
			description='BuildDem flip y'
			value = elevation.meta['BuildDem/flip_y']
			unit = None
			uri= None
			measurementclass=None
			infos_dem_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildDem/flip_z
			keyword = 'BuildDem_flip_z'
			beschreibung= ''
			description='BuildDem flip z'
			value = elevation.meta['BuildDem/flip_z']
			unit = None
			uri= None
			measurementclass=None
			infos_dem_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildDem/interpolation
			keyword = 'BuildDem_interpolation'
			beschreibung= ''
			description='BuildDem interpolation'
			value = elevation.meta['BuildDem/interpolation']
			unit = None
			uri= None
			measurementclass=None
			infos_dem_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildDem/max_workgroup_size
			keyword = 'BuildDem_max_workgroup_size'
			beschreibung= ''
			description='BuildDem max workgroup size'
			value = elevation.meta['BuildDem/max_workgroup_size']
			unit = None
			uri= None
			measurementclass=None
			infos_dem_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildDem/resolution
			keyword = 'BuildDem_resolution'
			beschreibung= ''
			description='BuildDem resolution'
			value = elevation.meta['BuildDem/resolution']
			unit = None
			uri= None
			measurementclass=None
			infos_dem_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildDem/source_data
			keyword = 'BuildDem_source_data'
			beschreibung= ''
			description='BuildDem source data'
			value = elevation.meta['BuildDem/source_data']
			unit = None
			uri= None
			measurementclass=None
			infos_dem_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildDem/subdivide_task
			keyword = 'BuildDem_subdivide_task'
			beschreibung= ''
			description='BuildDem subdivide task'
			value = elevation.meta['BuildDem/subdivide_task']
			unit = None
			uri= None
			measurementclass=None
			infos_dem_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildDem/workitem_size_tiles
			keyword = 'BuildDem_workitem_size_tiles'
			beschreibung= ''
			description='BuildDem workitem size tiles'
			value = elevation.meta['BuildDem/workitem_size_tiles']
			unit = None
			uri= None
			measurementclass=None
			infos_dem_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildDepthMaps/downscale
			keyword = 'BuildDepthMaps_downscale'
			beschreibung= ''
			description='BuildDepthMaps downscale'
			value = elevation.meta['BuildDepthMaps/downscale']
			unit = None
			uri= None
			measurementclass=None
			infos_dem_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildDepthMaps/filter_mode
			keyword = 'BuildDepthMaps_filter_mode'
			beschreibung= ''
			description='BuildDepthMaps filter mode'
			value = elevation.meta['BuildDepthMaps/filter_mode']
			unit = None
			uri= None
			measurementclass=None
			infos_dem_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildDepthMaps/max_neighbors
			keyword = 'BuildDepthMaps_max_neighbors'
			beschreibung= ''
			description='BuildDepthMaps max neighbors'
			value = elevation.meta['BuildDepthMaps/max_neighbors']
			unit = None
			uri= None
			measurementclass=None
			infos_dem_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildDepthMaps/max_workgroup_size
			keyword = 'BuildDepthMaps_max_workgroup_size'
			beschreibung= ''
			description='BuildDepthMaps max workgroup size'
			value = elevation.meta['BuildDepthMaps/max_workgroup_size']
			unit = None
			uri= None
			measurementclass=None
			infos_dem_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildDepthMaps/reuse_depth
			keyword = 'BuildDepthMaps_reuse_depth'
			beschreibung= ''
			description='BuildDepthMaps reuse depth'
			value = elevation.meta['BuildDepthMaps/reuse_depth']
			unit = None
			uri= None
			measurementclass=None
			infos_dem_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildDepthMaps/subdivide_task
			keyword = 'BuildDepthMaps_subdivide_task'
			beschreibung= ''
			description='BuildDepthMaps subdivide task'
			value = elevation.meta['BuildDepthMaps/subdivide_task']
			unit = None
			uri= None
			measurementclass=None
			infos_dem_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildDepthMaps/workitem_size_cameras
			keyword = 'BuildDepthMaps_workitem_size_cameras'
			beschreibung= ''
			description='BuildDepthMaps workitem size cameras'
			value = elevation.meta['BuildDepthMaps/workitem_size_cameras']
			unit = None
			uri= None
			measurementclass=None
			infos_dem_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# Info/LastSavedDateTime
			keyword = 'Info_LastSavedDateTime'
			beschreibung= ''
			description='last saved date time'
			if not elevation.meta['Info/LastSavedDateTime']== None:
				timeobject = time.strptime((elevation.meta['Info/LastSavedDateTime']), "%Y:%m:%d %H:%M:%S")
				value = (time.strftime("%Y-%m-%dT%H:%M:%S",timeobject))
			else:
				value = elevation.meta['Info/LastSavedDateTime']
			unit = None
			uri= None
			measurementclass=None
			infos_dem_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# Info/LastSavedSoftwareVersion
			keyword = 'Info_LastSavedSoftwareVersion'
			beschreibung= ''
			description='last saved software version'
			value = elevation.meta['Info/LastSavedSoftwareVersion']
			unit = None
			uri= None
			measurementclass=None
			infos_dem_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# Info/OriginalDateTime
			keyword = 'Info_OriginalDateTime'
			beschreibung= ''
			description='original date time'
			if not elevation.meta['Info/OriginalDateTime']== None:
				timeobject = time.strptime((elevation.meta['Info/OriginalDateTime']), "%Y:%m:%d %H:%M:%S")
				value = (time.strftime("%Y-%m-%dT%H:%M:%S",timeobject))
			else:
				value = elevation.meta['Info/OriginalDateTime']
			unit = None
			uri= None
			measurementclass=None
			infos_dem_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# Info/OriginalSoftwareVersion
			keyword = 'Original_SoftwareVersion'
			beschreibung= ''
			description='original software version'
			value = elevation.meta['Info/OriginalSoftwareVersion']
			unit = None
			uri= None
			measurementclass=None
			infos_dem_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			if len(dem_infos)>0:
				dem['digital_elevation_model_information']=dem_infos
			if len(dem_setup)>0:
				dem['digital_elevation_model_setup']=dem_setup
			if len(dem)>0:
				list_dem.append(dem)
		
		list_orthomosaics = []
		for o in range(len(doc.chunks[i].orthomosaics)):
			orthomosaic ={}
			orthomosaic_infos = {}
			orthomosaic_setup ={}
			ortho = doc.chunks[i].orthomosaics[o] 

			# id 
			keyword = 'orthomosaic_id'
			beschreibung= 'Orthomosaik_Id'
			description='orthomosaic id'
			value = ortho.key
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# label
			keyword = 'label'
			beschreibung= 'name'
			description='name'
			value = ortho.label
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# bottom 
			keyword = 'bottom'
			beschreibung= ''
			description='bottom'
			value = ortho.bottom
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# top
			keyword = 'top'
			beschreibung= ''
			description='top'
			value = ortho.top
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# height
			keyword = 'height'
			beschreibung= ''
			description='height'
			value = ortho.height
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# left
			keyword = 'left'
			beschreibung= ''
			description='left'
			value = ortho.left
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# right
			keyword = 'right'
			beschreibung= ''
			description='right'
			value = ortho.right
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# crs  
			keyword = 'crs'
			beschreibung= ''
			description='crs'
			value = ortho.crs.name
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic(keyword, beschreibung, value, unit,description, uri, measurementclass)

			## orthomosaic setup?
			# BuildOrthomosaic/blending_mode
			keyword = 'BuildOrthomosaic_blending_mode'
			beschreibung= ''
			description='BuildOrthomosaic blending mode'
			value = ortho.meta['BuildOrthomosaic/blending_mode']
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildOrthomosaic/cull_faces
			keyword = 'BuildOrthomosaic_cull_faces'
			beschreibung= ''
			description='BuildOrthomosaic cull faces'
			value = ortho.meta['BuildOrthomosaic/cull_faces']
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildOrthomosaic/fill_holes
			keyword = 'BuildOrthomosaic_fill_holes'
			beschreibung= ''
			description='BuildOrthomosaic fill holes'
			value = ortho.meta['BuildOrthomosaic/fill_holes']
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildOrthomosaic/flip_x
			keyword = 'BuildOrthomosaic_flip_x'
			beschreibung= ''
			description='BuildOrthomosaic flip x'
			value = ortho.meta['BuildOrthomosaic/flip_x']
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildOrthomosaic/flip_y
			keyword = 'BuildOrthomosaic_flip_y'
			beschreibung= ''
			description='BuildOrthomosaic flip y'
			value = ortho.meta['BuildOrthomosaic/flip_y']
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildOrthomosaic/flip_z
			keyword = 'BuildOrthomosaic_flip_z'
			beschreibung= ''
			description='BuildOrthomosaic flip z'
			value = ortho.meta['BuildOrthomosaic/flip_z']
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildOrthomosaic/ghosting_filter
			keyword = 'BuildOrthomosaic_ghosting_filter'
			beschreibung= ''
			description='BuildOrthomosaic ghosting filter'
			value = ortho.meta['BuildOrthomosaic/ghosting_filter']
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildOrthomosaic/max_workgroup_size
			keyword = 'BuildOrthomosaic_max_workgroup_size'
			beschreibung= ''
			description='BuildOrthomosaic max workgroup size'
			value = ortho.meta['BuildOrthomosaic/max_workgroup_size']
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildOrthomosaic/refine_seamlines
			keyword = 'BuildOrthomosaic_refine_seamlines'
			beschreibung= ''
			description='BuildOrthomosaic refine seamlines'
			value = ortho.meta['BuildOrthomosaic/refine_seamlines']
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildOrthomosaic/resolution
			keyword = 'BuildOrthomosaic_resolution'
			beschreibung= ''
			description='BuildOrthomosaic resolution'
			value = ortho.meta['BuildOrthomosaic/resolution']
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildOrthomosaic/resolution_x
			keyword = 'BuildOrthomosaic_resolution_x'
			beschreibung= ''
			description='BuildOrthomosaic resolution x'
			value = ortho.meta['BuildOrthomosaic/resolution_x']
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildOrthomosaic/resolution_y
			keyword = 'BuildOrthomosaic_resolution_y'
			beschreibung= ''
			description='BuildOrthomosaic resolution y'
			value = ortho.meta['BuildOrthomosaic/resolution_y']
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildOrthomosaic/subdivide_task
			keyword = 'BuildOrthomosaic_subdivide_task'
			beschreibung= ''
			description='BuildOrthomosaic subdivide task'
			value = ortho.meta['BuildOrthomosaic/subdivide_task']
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildOrthomosaic/surface_data
			keyword = 'BuildOrthomosaic_surface_data'
			beschreibung= ''
			description='BuildOrthomosaic surface data'
			value = ortho.meta['BuildOrthomosaic/surface_data']
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildOrthomosaic/workitem_size_cameras
			keyword = 'BuildOrthomosaic_workitem_size_cameras'
			beschreibung= ''
			description='BuildOrthomosaic workitem size cameras'
			value = ortho.meta['BuildOrthomosaic/workitem_size_cameras']
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# BuildOrthomosaic/workitem_size_tiles
			keyword = 'BuildOrthomosaic_workitem_size_tiles'
			beschreibung= ''
			description='BuildOrthomosaic workitem size tiles'
			value = ortho.meta['BuildOrthomosaic/workitem_size_tiles']
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# Info/LastSavedDateTime
			keyword = 'Info_LastSavedDateTime'
			beschreibung= ''
			description='last saved date time'
			if not ortho.meta['Info/LastSavedDateTime'] == None:
				timeobject = time.strptime((ortho.meta['Info/LastSavedDateTime']), "%Y:%m:%d %H:%M:%S")
				value = (time.strftime("%Y-%m-%dT%H:%M:%S",timeobject))
			else:
				value = ortho.meta['Info/LastSavedDateTime']
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# Info/LastSavedSoftwareVersion
			keyword = 'Info_LastSavedSoftwareVersion'
			beschreibung= ''
			description='last saved software version'
			value = ortho.meta['Info/LastSavedSoftwareVersion']
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# Info/OriginalDateTime
			keyword = 'BuildOrthomosaic_cull_faces'
			beschreibung= ''
			description='BuildOrthomosaic cull faces'
			value = ortho.meta['BuildOrthomosaic/cull_faces']
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			# Info/OriginalSoftwareVersion
			keyword = 'BuildOrthomosaic_cull_faces'
			beschreibung= ''
			description='BuildOrthomosaic cull faces'
			value = ortho.meta['BuildOrthomosaic/cull_faces']
			unit = None
			uri= None
			measurementclass=None
			infos_orthomosaic_setup(keyword, beschreibung, value, unit,description, uri, measurementclass)

			if len (orthomosaic_infos)>0:
				orthomosaic['orthomosaic_information']=orthomosaic_infos
			if len (orthomosaic_setup)>0:
				orthomosaic['orthomosaic_setup']=orthomosaic_setup
			if len(orthomosaic)>0:
				list_orthomosaics.append(orthomosaic)

		if len(list_dem)>0:
			chunks['digital_elevation_models']= list_dem
		if len(list_orthomosaics)>0:
			chunks['orthomosaics']= list_orthomosaics
		if len(list_sensors)>0:
			chunks["sensors"]=list_sensors	
		if len(list_meshes)>0:
			chunks["meshes"]= list_meshes
		if len(global_rp)>0:
			chunks["global_referencepoints"]= global_rp
		if len(list_cameras)>0:
			chunks["cameras"]= list_cameras 
		if len(chunk_info)>0:
			chunks["chunk_information"]=chunk_info 
		if len(alignment)>0:
			chunks["alignment_setup"]=alignment 
		if len(tiepoint_info)>0:
			chunks["tiepoints"]=tiepoint_info 
		if len(list_densecloud)>0:
			chunks["densecloud"]=list_densecloud
		if len(chunks)>0:
			list_chunks.append(chunks)
		
	## App Informationen

	#Softwarevendor
	keyword = 'OriginalSoftwareVendor'
	beschreibung= 'Softwarehersteller'
	value = doc.meta['Info/OriginalSoftwareVendor']
	if value == None:
		value = "Agisoft"
	description='software vendor'
	unit = None
	uri= ontologynamespace + 'softwarevendor'
	measurementclass=None
	infos_app(keyword, beschreibung, value, unit,description, uri, measurementclass)

	##Softwarename
	keyword = 'OriginalSoftwareName'
	beschreibung= 'Softwarename'
	value = doc.meta['Info/OriginalSoftwareName']
	if value == None:
		value = "Agisoft Metashape"
	description='softwarename'
	unit = None
	uri= ontologynamespace + 'softwarename'
	measurementclass=None
	infos_app(keyword, beschreibung, value, unit,description, uri, measurementclass)  

	#Softwareversion
	keyword = 'OriginalSoftwareVersion'
	beschreibung= 'Softwareversion'
	value = doc.meta['Info/OriginalSoftwareVersion']
	description='softwareversion'
	unit = None
	uri= ontologynamespace + 'softwareversion'
	measurementclass=None
	infos_app(keyword, beschreibung, value, unit,description, uri, measurementclass)

	# Info/LastSavedSoftwareVersion
	keyword = 'LastSavedSoftwareVersion'
	beschreibung= 'Zuletzt gespeicherte Softwareversion'
	value = doc.meta['Info/LastSavedSoftwareVersion']
	description='last saved softwareversion'
	unit = None
	uri= None
	measurementclass=None
	infos_app(keyword, beschreibung, value, unit,description, uri, measurementclass)

	# Info/OriginaDateTime
	keyword = 'OriginalDateTime'
	beschreibung= 'Original Datum Zeit'
	if not doc.meta['Info/OriginalDateTime'] == None:
		timeobject = time.strptime((doc.meta['Info/OriginalDateTime']), "%Y:%m:%d %H:%M:%S")
		value = (time.strftime("%Y-%m-%dT%H:%M:%S",timeobject))
	else:
		value = None
	description='original date time'
	unit = None
	uri= None
	measurementclass=None
	infos_app(keyword, beschreibung, value, unit,description, uri, measurementclass)
	
	# Info/LastSavedDateTime
	keyword = 'LastSavedDateTime'
	beschreibung= 'Zuletzt gespeichert'
	if not doc.meta['Info/LastSavedDateTime'] == None:
		timeobject = time.strptime((doc.meta['Info/LastSavedDateTime']), "%Y:%m:%d %H:%M:%S")
		value = (time.strftime("%Y-%m-%dT%H:%M:%S",timeobject))
	else:
		value = None
	description='last saved date time'
	unit = None
	uri= None
	measurementclass=None
	infos_app(keyword, beschreibung, value, unit,description, uri, measurementclass)


	## Projektinformationen 

	# Messverfahren 	
	keyword= 'acquisition_technology'
	beschreibung = "Aufnahmeverfahren"
	value= 'structure from motion'
	unit= None
	description='acquisition technology'
	uri= ontologynamespace+"AcquisitionTechnology"
	measurementclass=None
	from_application= 'false'
	infos_p(keyword,beschreibung,value,unit,description,uri,measurementclass, from_application)	

	# Projektname 
	keyword = 'project_name'
	beschreibung= 'Projektname'
	value = os.path.basename(doc.path)[:-4]
	description="projectname"
	unit = None
	uri= rdfs + 'label'
	measurementclass=None
	infos_p(keyword, beschreibung, value, unit,description, uri, measurementclass)

	# Projektdatei
	keyword = 'project_file'
	beschreibung= 'Projektdatei'
	value = os.path.basename(doc.path)
	description="project file"
	unit = None
	uri= ontologynamespace + 'projectfile'
	measurementclass=None
	infos_p(keyword, beschreibung, value, unit,description, uri, measurementclass)

	# Anzahl Chunks
	keyword = 'number_of_chunks'
	beschreibung = "Anzahl Chunks"
	value = len(doc.chunks)
	description="number of chunks"
	unit = None
	uri= ontologynamespace + 'numberOfChunks'
	measurementclass=None
	infos_p(keyword, beschreibung, value, unit,description, uri, measurementclass)


	if len(list_chunks)>0:
		project["chunks"]= list_chunks
	if len(app)>0:
		list_app.append(app)
	if len(list_app)>0:
		project["applications"]= list_app
	if len(project_info)>0:
		project["project_information"]= project_info
	if len(project)>0:
		list_projects.append(project)
	if len(list_projects)>0:
		dic_prj["projects"] = list_projects
	
	print (".... createMetaDic is finished")
	return dic_prj

########################## Methode zu Ende 

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

# startet Methode zum Erzeugen des Dictionaries
# export als JSON
# startet Methode zum Erzeugen des TTL
# export als TTL

def exportMeta(input_file, unit,includeonlypropswithuri, manualmetadatapathJSON=None):

	print ("in exportMeta()")
	print ("_")
	
	#Definition von Variablen		
	try:
		out_file = input_file.replace(".psx","")



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
		dic_dig["userdata"] = {}
		if os.path.isfile(objectdescriptionpathTTL):
			readInputTTL(objectdescriptionpathTTL,ttlstring)
		elif os.path.isfile(objectdescriptionpathTXT):
			readInputTXTForArtifactDescription(objectdescriptionpathTXT,ttlstring);	
		if os.path.isfile(manualmetadatapathTTL):
			readInputTTL(manualmetadatapathTTL,ttlstring)
		elif os.path.isfile(manualmetadatapathJSON):		### ÜBERPRÜFEN .....
			print (manualmetadatapathJSON)
			with open(manualmetadatapathJSON, 'r',encoding='utf8') as json_file:
				# dic_dig=json.load(json_file)
				dic_dig["userdata"]=json.load(json_file)
		elif os.path.isfile(manualmetadatapathYAML):
			with open(manualmetadatapathYAML) as yaml_file:
				dic_dig["userdata"]=yaml.load(yaml_file)
	except:
		print (".... files to import/export funktioniert nicht")


	# start von methode createMetaDic ## return dictionary (dic_prj) wo alles drin ist
	# dic_prj = createMetaDic(dic_dig, input_file, unit, includeonlypropswithuri)
	dic_prj = createMetaDic(dic_dig["userdata"], input_file, unit, includeonlypropswithuri)

	#filenamesuffix = Softwareversion
	try: 
		i = 0
		filenamesuffix = ""
		while i < len(dic_prj['projects'][0]['applications']):
			dic_f = dic_prj['projects'][0]['applications'][i]
			print (i)
			print (dic_f)
			if 'OriginalSoftwareVendor' in dic_f.keys():
				print ("yes")
				print (dic_f['OriginalSoftwareVendor']['value'])
				print (((dic_f['OriginalSoftwareVersion']['value']).split("."))[0])
				filenamesuffix = (dic_f['OriginalSoftwareVendor']['value']) + (((dic_f['OriginalSoftwareVersion']['value']).split("."))[0]) + (((dic_f['OriginalSoftwareVersion']['value']).split("."))[1]) + (((dic_f['OriginalSoftwareVersion']['value']).split("."))[2])
			i = i + 1
	except:
		filenamesuffix = 'agisoft'
			
	out_file_json = out_file+"_metadata_" + filenamesuffix + ".json"
	out_file_ttl = out_file+"_metadata_" + filenamesuffix + ".ttl"

	try:
		###### export der Metadaten in JSON-File
		with open(out_file_json, 'w',encoding='utf8') as fp:
			json.dump(dic_prj, fp, indent = 4, ensure_ascii=False)

		# Methode zum Umwandeln des Dictionary in TTL 
		# externe Infos aus ttlstring werden übergeben
		if dic_dig!=None and dic_dig!={} and "userdata" in dic_dig:
			fertiges_ttl = exportToTTL(dic_prj, None, ttlstring,dic_dig["userdata"])
		else:
			fertiges_ttl=exportToTTL(dic_prj, None, ttlstring)  
		
		##### export der Metadaten in TTL-File
		with open(out_file_ttl, 'w',encoding='utf8') as text_file:
			text_file.write(ttlstringhead)
			for item in fertiges_ttl:
				text_file.write("%s" % item)
		text_file.close()

	except:
		print ("... export geht nicht")
	
#######################################################################################################

if production:
	root = Tk()
	def_font = tkinter.font.nametofont("TkDefaultFont")
	def_font.config(size=10)
	app = Window()
	root.mainloop()
else:
	print ("ist NICHT in produktion")	
	ttlstring=set()
	path="Holz_meta_agisoft.json"
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
	with open(path, 'r') as myfile:
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
print ("fertsch")
