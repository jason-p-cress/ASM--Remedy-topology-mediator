#!/usr/bin/python -u

#######################################################
#
# Remedy REST mediator for topology inclusion into ASM
#
# 02/09/21 - Jason Cress (jcress@us.ibm.com)
#
#######################################################

import sys
from httplib import IncompleteRead
import time
import datetime
import gc
import random
import base64
import json
import re
from pprint import pprint
import os
import ssl
import urllib2
import urllib
from collections import defaultdict
from multiprocessing import Process

def keyExists(d, myKey): 
   return d.has_key(myKey) or any(myhaskey(dd) for dd in d.values() if isinstance(dd, dict))


def loadProperties(filepath, sep='=', comment_char='#'):
    """
    Read the file passed as parameter as a properties file.
    """
    props = {}
    with open(filepath, "rt") as f:
        for line in f:
            l = line.strip()
            if l and not l.startswith(comment_char):
                key_value = l.split(sep)
                key = key_value[0].strip()
                value = sep.join(key_value[1:]).strip().strip('"') 
                props[key] = value 
    return props

def loadClassList(filepath, comment_char='#'):

   ciClassList = []

   with open(filepath, "rt") as f:
      for line in f:
         l = line.strip()
         if l and not l.startswith(comment_char):
            ciClassList.append(l)
   return(ciClassList)
 
#   ciClassList = { "cmdb_ci_cluster", "cmdb_ci_cluster_vip", "cmdb_ci_cluster_resource", "cmdb_ci_cluster_node", "cmdb_ci_vm", "cmdb_ci_server", "cmdb_ci_ip_router", "cmdb_ci_ip_switch", "cmdb_ci_appl", "cmdb_ci_db_instance", "cmdb_ci_service" }

def loadCmdbServer(filepath, sep=',', comment_char='#'):

   ##########################################################################################
   #
   # This function reads the ServiceNow server configuration file and returns a dictionary
   #
   ##########################################################################################

   lineNum = 0
   with open(filepath, "rt") as f:
      for line in f:
         cmdbServerDict = {}
         l = line.strip()
         if l and not l.startswith(comment_char):
            values = l.split(sep)
            if(len(values) < 3):
               print "Malformed server configuration entry on line number: " + str(lineNum)
            else:
               cmdbServerDict["server"] = values[0]
               cmdbServerDict["user"] = values[1]
               cmdbServerDict["password"] = values[2]
         lineNum = lineNum + 1

   return(cmdbServerDict)

def verifyAsmConnectivity(asmDict):
 
   ##################################################################
   #
   # This function verifies that the ASM server credentials are valid
   # ---+++ CURRENTLY UNIMPLEMENTED +++---
   #
   ##################################################################

   return True

def loadEntityTypeMapping(filepath, sep=",", comment_char='#'):

   ################################################################################
   #
   # This function reads the entityType map configuration file and returns a dictionary
   #
   ################################################################################

   lineNum = 0

   with open(filepath, "rt") as f:
      for line in f:
         l = line.strip()
         if l and not l.startswith(comment_char):
            values = l.split(sep)
            if(len(values) < 2 or len(values) > 2):
               print "Malformed entityType map config line on line " + str(lineNum)
            else:
               entityTypeMappingDict[values[0].replace('"', '')] = values[1].replace('"', '')

def loadAssetLifecycleStatusFilter(filepath, sep=",", comment_char='#'):

   ################################################################################
   #
   # This function reads the entityType map configuration file and returns a dictionary
   #
   ################################################################################

   print "opening AssetLifecycleStatus filter file at " + filepath

   lineNum = 0

   with open(filepath, "rt") as f:
      for line in f:
         l = line.strip()
         if l and not l.startswith(comment_char):
            assetLifecycleStatusFilterArray.append(l)

   #for l in assetLifecycleStatusFilterArray:
   #   print l

def loadPrimaryCapabilityFilter(filepath, sep=",", comment_char='#'):

   ################################################################################
   #
   # This function reads the entityType map configuration file and returns a dictionary
   #
   ################################################################################

   print "opening Primary Capability filter file at " + filepath

   lineNum = 0

   with open(filepath, "rt") as f:
      for line in f:
         l = line.strip()
         if l and not l.startswith(comment_char):
            primaryCapabilityFilterArray.append(l)



def loadPrimaryCapabilityMapping(filepath, sep=",", comment_char='#'):

   ################################################################################
   #
   # This function reads the entityType map configuration file and returns a dictionary
   #
   ################################################################################

   print "opening PrimaryCapability mapping file at " + filepath

   lineNum = 0

   with open(filepath, "rt") as f:
      for line in f:
         l = line.strip()
         if l and not l.startswith(comment_char):
            values = l.split(sep)
            if(len(values) < 2 or len(values) > 2):
               print "Malformed entityType map config line on line " + str(lineNum)
            else:
               primaryCapabilityMappingDict[values[0].replace('"', '')] = values[1].replace('"', '')

   print primaryCapabilityMappingDict

def loadRelationshipMapping(filepath, sep=",", comment_char='#'):

   ################################################################################
   #
   # This function reads the relationship map configuration file and returns a dictionary
   #
   ################################################################################

   lineNum = 0
   #relationshipMappingDict = {}
   with open(filepath, "rt") as f:
      for line in f:
         l = line.strip()
         if l and not l.startswith(comment_char):
            values = l.split(sep)
            if(len(values) < 3 or len(values) > 3):
               print "Malformed mapping config line on line " + str(lineNum)
            else:
               relationshipMappingDict[values[0].replace('"', '')] = values[2].replace('"', '')

def loadAsmServer(filepath, sep=",", comment_char='#'):

   ################################################################################
   #
   # This function reads the ASM server configuration file and returns a dictionary
   #
   ################################################################################

   lineNum = 0
   with open(filepath, "rt") as f:
      for line in f:
         asmDict = {}
         l = line.strip()
         if l and not l.startswith(comment_char):
            values = l.split(sep)
            if(len(values) < 5):
               print "Malformed ASM server config line on line " + str(lineNum)
            else:
               asmDict["server"] = values[0]
               asmDict["port"] = values[1]
               asmDict["user"] = values[2]
               asmDict["password"] = values[3]
               asmDict["tenantid"] = values[4]
               if(verifyAsmConnectivity(asmDict)):
                  return(asmDict)
               else:
                  print "Unable to connect to ASM server " + asmDict["server"] + " on port " + asmDict["port"] + ", please verify server, username, password, and tenant id in " + mediatorHome + "config/asmserver.conf"
         
def listArsCmdbClasses(token):

   #####################################
   #
   # This function gets all cmdb namespaces
   #
   # input: token
   #
   #####################################

   method = "GET"

   requestUrl = 'https://' + cmdbServerDict["server"] + '/api/cmdb/v1.0/classes/BMC.CORE'

   try:
      request = urllib2.Request(requestUrl)
      request.add_header("Content-Type",'application/json')
      request.add_header("Authorization","AR-JWT " + token)
      request.get_method = lambda: method

      response = urllib2.urlopen(request)
      xmlout = response.read()
      print str(xmlout)
      return str(xmlout)

   except IOError, e:
      print 'Failed to open "%s".' % requestUrl
      if hasattr(e, 'code'):
         print 'We failed with error code - %s.' % e.code
      elif hasattr(e, 'reason'):
         print "The error object has the following 'reason' attribute :"
         print e.reason
         print "This usually means the server doesn't exist,",
         print "is down, or we don't have an internet connection."
      return False

def listArsCmdbNamespaces(token):

   #####################################
   #
   # This function gets all cmdb namespaces
   #
   # input: token
   #
   #####################################

   method = "GET"

   requestUrl = 'https://' +  cmdbServerDict["server"] + '/api/cmdb/v1.0/namespaces'

   try:
      request = urllib2.Request(requestUrl)
      request.add_header("Content-Type",'application/json')
      request.add_header("Authorization","AR-JWT " + token)
      request.get_method = lambda: method

      response = urllib2.urlopen(request)
      xmlout = response.read()
      print str(xmlout)
      return str(xmlout)

   except IOError, e:
      print 'Failed to open "%s".' % requestUrl
      if hasattr(e, 'code'):
         print 'We failed with error code - %s.' % e.code
      elif hasattr(e, 'reason'):
         print "The error object has the following 'reason' attribute :"
         print e.reason
         print "This usually means the server doesn't exist,",
         print "is down, or we don't have an internet connection."
      return False


def getArsCmdb(token):

   #####################################
   #
   # This function gets all cmdb items
   #
   # input: token
   #
   #####################################

   namespace = "BMC.CORE"
   datasetId = "BMC.ASSET"
   classId = "BMC_COMPUTERSYSTEM"
   
   method = "GET"
   #print "REQUEST URL: " + requestUrl


   try:
      request = urllib2.Request(requestUrl)
      request.add_header("Content-Type",'application/json')
      request.add_header("Authorization","AR-JWT " + token)
      request.get_method = lambda: method

      response = urllib2.urlopen(request)
      xmlout = response.read()
      print str(xmlout)
      return str(xmlout)

   except IOError, e:
      print 'Failed to open "%s".' % requestUrl
      if hasattr(e, 'code'):
         print 'We failed with error code - %s.' % e.code
      elif hasattr(e, 'reason'):
         print "The error object has the following 'reason' attribute :"
         print e.reason
         print "This usually means the server doesn't exist,",
         print "is down, or we don't have an internet connection."
      return False

def getArsToken():

   #####################################
   #
   # This function generates an ARS token
   #
   # inputs: username, passord
   # output: token
   #
   #####################################


   username = cmdbServerDict["user"]
   password = cmdbServerDict["password"]

   print ":"
   print "Getting token, username is " + username + " and password is " + password
   
   global arsToken
   method = "POST"

   requestUrl = 'https://' + cmdbServerDict["server"] + '/api/jwt/login'
   body = "username=" + username + "&password=" + password

   #authHeader = 'Basic ' + base64.b64encode(asmServerDict["user"] + ":" + asmServerDict["password"])
   #print "auth header is: " + str(authHeader)
   #print "pushing the following json to ASM: " + jsonResource

   try:
      request = urllib2.Request(requestUrl, body)
      request.add_header("Content-Type",'application/x-www-form-urlencoded')
      #request.add_header("Content-Length",'32')
      #request.add_header("username",username)
      #request.add_header("password",password)
      request.get_method = lambda: method

      response = urllib2.urlopen(request)
      xmlout = response.read()
      sys.stderr.write("Received token: " + str(xmlout))
      #return str(xmlout)
      arsToken = str(xmlout)

   except IOError, e:
      print 'Failed to open "%s".' % requestUrl
      if hasattr(e, 'code'):
         print 'We failed with error code - %s.' % e.code
      elif hasattr(e, 'reason'):
         print "The error object has the following 'reason' attribute :"
         print e.reason
         print "This usually means the server doesn't exist,",
         print "is down, or we don't have an internet connection."
      print "FATAL: UNABLE TO AUTHENTICATE WITH ARS TO OBTAIN TOKEN USING PROVIDED CREDENTIALS"
      exit()
      return False

def releaseArsToken(token):

   #####################################
   #
   # This function releases an ARS token
   #
   # input: token
   # output: True/False
   #
   #####################################
   
   method = "POST"

   requestUrl = 'https://' + cmdbServerDict["server"] + '/api/jwt/logout'

   #authHeader = 'Basic ' + base64.b64encode(asmServerDict["user"] + ":" + asmServerDict["password"])
   #print "auth header is: " + str(authHeader)
   #print "pushing the following json to ASM: " + jsonResource

   try:
      request = urllib2.Request(requestUrl)
      request.add_header("Authorization","AR-JWT " + token)
      request.get_method = lambda: method

      response = urllib2.urlopen(request)
      xmlout = response.read()
      if hasattr(response, 'code'):
         sys.stderr.write("Code is: " + str(response.code))
      sys.stderr.write(str(xmlout))
      return True

   except IOError, e:
      print 'Failed to open "%s".' % requestUrl
      if hasattr(e, 'code'):
         print 'We failed with error code - %s.' % e.code
      elif hasattr(e, 'reason'):
         print "The error object has the following 'reason' attribute :"
         print e.reason
         print "This usually means the server doesn't exist,",
      return False

def createFileResource(resourceDict):

   #######################################################
   # 
   # Function to create a file observer entry for resource
   #
   #######################################################

   jsonResource = json.dumps(resourceDict)
   print "A:" + jsonResource

def createFileConnection(connectionDict):

   #########################################################
   # 
   # Function to create a file observer entry for connection 
   #
   #########################################################

   jsonResource = json.dumps(connectionDict)
   print "E:" + jsonResource

def createAsmResource(resourceDict):

   #######################################################
   #
   # Function to send a resource to the ASM rest interface
   #
   #######################################################

   method = "POST"

   #requestUrl = 'https://' + asmServerDict["server"] + ':' + asmServerDict["port"] + '/1.0/topology/resources'

   requestUrl = 'https://' + asmServerDict["server"] + ':' + asmServerDict["port"] + '/1.0/rest-observer/rest/resources'

   authHeader = 'Basic ' + base64.b64encode(asmServerDict["user"] + ":" + asmServerDict["password"])
   #print "auth header is: " + str(authHeader)
   jsonResource = json.dumps(resourceDict)
   #print "creating the following resource in ASM: " + jsonResource

   try:
      request = urllib2.Request(requestUrl, jsonResource)
      request.add_header("Content-Type",'application/json')
      request.add_header("Accept",'application/json')
      request.add_header("Authorization",authHeader)
      request.add_header("X-TenantId",asmServerDict["tenantid"])
      #request.add_header("JobId","HMC")
      request.get_method = lambda: method

      response = urllib2.urlopen(request)
      xmlout = response.read()
      return True

   except IOError, e:
      print 'Failed to open "%s".' % requestUrl
      if hasattr(e, 'code'):
         print 'We failed with error code - %s.' % e.code
      elif hasattr(e, 'reason'):
         print "The error object has the following 'reason' attribute :"
         print e.reason
         print "This usually means the server doesn't exist,",
         print "is down, or we don't have an internet connection."
      return False


def createAsmConnection(connectionDict):

   #########################################################
   #
   # Function to send a connection to the ASM rest interface
   #
   #########################################################
   
   method = "POST"

   requestUrl = 'https://' + asmServerDict["server"] + ':' + asmServerDict["port"] + '/1.0/rest-observer/rest/references'

   authHeader = 'Basic ' + base64.b64encode(asmServerDict["user"] + ":" + asmServerDict["password"])
   #print "auth header is: " + str(authHeader)
   jsonResource = json.dumps(connectionDict)
   #print "adding the following connection to ASM: " + jsonResource

   try:
      request = urllib2.Request(requestUrl, jsonResource)
      request.add_header("Content-Type",'application/json')
      request.add_header("Accept",'application/json')
      request.add_header("Authorization",authHeader)
      request.add_header("X-TenantId",asmServerDict["tenantid"])
      request.add_header("JobId","HMC")
      request.get_method = lambda: method

      response = urllib2.urlopen(request)
      xmlout = response.read()
      return True

   except IOError, e:
      print 'Failed to open "%s".' % requestUrl
      if hasattr(e, 'code'):
         print 'We failed with error code - %s.' % e.code
      elif hasattr(e, 'reason'):
         print "The error object has the following 'reason' attribute :"
         print e.reason
         print "This usually means the server doesn't exist,",
         print "is down, or we don't have an internet connection."
      return False

def getTotalRelCount():

   method = 'GET'
   #requestUrl = 'https://' + snowServerDict["server"] + '/api/now/stats/cmdb_rel_ci?sysparm_count=true'
   print("issuing relationship count query: " + requestUrl)
   authHeader = 'Basic ' + base64.b64encode(snowServerDict["user"] + ":" + snowServerDict["password"])
     
   try:
      request = urllib2.Request(requestUrl)
      request.add_header("Content-Type",'application/json')
      request.add_header("Accept",'application/json')
      request.add_header("Authorization",authHeader)
      request.get_method = lambda: method

      response = urllib2.urlopen(request)
      relCountResult = response.read()

   except IOError, e:
      print 'Failed to open "%s".' % requestUrl
      if hasattr(e, 'code'):
         print 'We failed with error code - %s.' % e.code
      elif hasattr(e, 'reason'):
         print "The error object has the following 'reason' attribute :"
         print e.reason
         print "This usually means the server doesn't exist,",
         print "is down, or we don't have an internet connection."


   relCountResultDict = json.loads(relCountResult)
   print("Found " + relCountResultDict["result"]["stats"]["count"])
   return(int(relCountResultDict["result"]["stats"]["count"]))

 
def getCiData(classname):

   ###################################################
   #
   # query Remedy cmdb_ci table and generate ASM objects
   #
   ###################################################

   global arsToken
   totalCi = 0
   global ciSysIdSet
   global ciSysIdList
   global readCisFromFile
   #ciType = "BMC_ComputerSystem"
   ciType = classname
   ciList = []

   readCiEntries = []
   writeToFile = 0
 
   readFromRest = 1
   readCisFromFile = 0

   if(readCisFromFile == "1"):
      if(os.path.isfile(mediatorHome  + "/log/" + ciType + ".json")):
         with open(mediatorHome + "/log/" + ciType + ".json") as text_file:
            completeResult = text_file.read()
            text_file.close()
         readCiEntries = json.loads(completeResult)
         del completeResult
         gc.collect()
         readFromRest = 0
      else:
         print "NOTE: read from file selected, yet file for ciType " + ciType + " does not exist. Reading from REST API."
         readFromRest = 1 
   else:
      readFromRest = 1

   if(readFromRest == 1):
      print "Entering read loop for " + ciType
      limit = 500
      method = "GET"
      isMore = 1
      offset = 0
      firstRun = 1
   
      while(isMore):
   
         asmObjectList = []
         
         requestUrl = 'https://' + cmdbServerDict["server"] + '/api/cmdb/v1.0/instances/BMC.ASSET/BMC.CORE/' + ciType + '?offset=' + str(offset) + "&limit=" + str(limit)
     
         retryTimer = 0
         for retry in [1,2,3]:
             retryTimer = retryTimer + 11
             try:
                request = urllib2.Request(requestUrl)
                request.add_header("Content-Type",'application/json')
                request.add_header("Authorization","AR-JWT " + arsToken)
                request.get_method = lambda: method
          
                response = urllib2.urlopen(request, timeout=10)
                ciDataResult = response.read()
                break
          
             except IOError, e:
                print 'Failed to open "%s".' % requestUrl
                if hasattr(e, 'code'):
                   print 'We failed with error code - %s.' % e.code
                   if(str(e.code) == "401"):
                      print "appears to be that the auth token has expired. Generating a new one..."
                      getArsToken()
                elif hasattr(e, 'reason'):
                   print "The error object has the following 'reason' attribute :"
                   print e.reason
                   print "This usually means the server doesn't exist,",
                   print "is down, or we don't have an internet connection."
                else:
                   print "ERROR: Unable to read from URL: " + requestUrl
                if(retry == 3):
                   print("FATAL: READ ERROR AFTER 3 TRIES: ABORTING READ")
                   print("Aborted URL: " + requestUrl)
                   break
                else:
                   time.sleep(retryTimer)

      
         ciEntries = json.loads(ciDataResult)
         print "FOUND INSTANCES: " + str(len(ciEntries["instances"])) + ", current offset is: " + str(offset)
         for ci in ciEntries["instances"]:
            #print "adding " + ci["instance_id"] + " to readCiEntries..."
            #readCiEntries.append(ci)
            #print "CREATING ASM VERTEX FOR " + ci["instance_id"]
            asmObject = createAsmVertex(ci)
            if(asmObject <> 0):
               asmObjectList.append(asmObject)
         if(writeToFile == 1):
            text_file = open(mediatorHome + "/log/" + ciType + ".json", "w")
            text_file.write(json.dumps(readCiEntries))
            text_file.close()

         numCi = len(ciEntries["instances"])
         totalCi = totalCi + numCi
         print "number of CIs found this fetch: " + str(numCi)
         print "total CIs: " + str(totalCi)
         vertices = open(mediatorHome + "/file-observer-files/vertices-" + startTime + ".json", "a")
         for asmVertex in asmObjectList:
            object_text = json.dumps(asmVertex)
            vertices.write("V:" + object_text + "\n" + "W:5 millisecond" + "\n")
            vertices.flush()
         vertices.close() 
         del asmObjectList
         if(numCi < limit):
            print "no more"
            isMore = 0
         else:
            print "is more"
            offset = offset + limit
            isMore = 1
      
         print str(totalCi) + " items in the cmdb ci table"

  #    writeToFile = 1 

   #if(writeToFile):
      #print "writing " + str(len(readCiEntries)) + " ci items to file"
      #text_file = open(mediatorHome + "/log/" + ciType + ".json", "w")
      #text_file.write(json.dumps(readCiEntries))
      #text_file.close()
      

   print "converting ciSysIdList to ciSysIdSet"
   ciSysIdSet = set(ciSysIdList) # convert our ciSysIdList to a set for faster evaluation
   print "there are " + str(len(ciSysIdSet)) + " items in ciSysIdSet, while there are " + str(len(ciSysIdList)) + " items in ciCysIdList..."
   return()

def createAsmVertex(ci):

   # Ignore HP storage switches. This capability would probably be better as a config option, but no time for this POC to implement...
   sys.stdout.write("Creating ASM Vertex")

   asmObject = {}
   asmObject["uniqueId"] = ci["instance_id"]
   asmObject["sys_class_name"] = ci["class_name_key"]["name"]
   for prop in ci["attributes"]:
      if(ci["attributes"][prop]):
         asmObject[prop] = ci["attributes"][prop]

   # Determine ASM naming

   if asmObject.has_key("HostName"):
      asmObject["name"] = asmObject["HostName"]
      extr = re.search("(.*)\.videotron\.com", asmObject["name"])
      if extr:
         extr = re.search("(.*?)\..*", asmObject["name"])
         if extr:
            asmObject["shortname"] = extr.group(1)
            asmObject["longname"] = asmObject["name"]
            asmObject["name"] = asmObject["shortname"]
   elif(asmObject.has_key("Name")):
         asmObject["name"] = asmObject["Name"]
         extr = re.search("(.*)\.videotron\.com", asmObject["name"])
         if extr:
            extr = re.search("(.*?)\..*", asmObject["name"])
            if extr:
               asmObject["shortname"] = extr.group(1)
               asmObject["longname"] = asmObject["name"]
               asmObject["name"] = asmObject["shortname"]

   else:
      asmObject["name"] = asmObject["uniqueId"]

   asmObject["_operation"] = "InsertReplace"
   asmObject["uniqueId"] = asmObject["uniqueId"]

   # Determine ASM entityType

   print "Determining PrimaryCapability"

   if asmObject.has_key("PrimaryCapability"):
      print "PRIMARYCAPABILITY: this object has a PrimaryCapability field, and it is: " + asmObject["PrimaryCapability"]
      if( asmObject["PrimaryCapability"] in primaryCapabilityMappingDict):
         print "PRIMARYCAPABILITY: this object is in our Mapping Dict"
         asmObject["entityTypes"] = [  primaryCapabilityMappingDict[asmObject["PrimaryCapability"]] ]
      elif( asmObject["sys_class_name"] in entityTypeMappingDict):
         print "PRIMARYCAPABILITY: No mapping for PrimaryCapabilty " + asmObject["PrimaryCapability"]
         asmObject["entityTypes"] = [ entityTypeMappingDict[asmObject["sys_class_name"]] ]
      else:
         print "PrimaryCapability exists, but no mapping exists for PrimaryCapability \"" + asmObject["PrimaryCapability"] + "\", nor does a mapping exist for object class \"" + asmObject["sys_class_name"] + "\""
   elif( asmObject["sys_class_name"] in entityTypeMappingDict):
      print "No PrimaryCapability field in record, but we do have a class mapping"
      asmObject["entityTypes"] = [ entityTypeMappingDict[asmObject["sys_class_name"]] ]
   else:
      print "No PrimaryCapability field in record, and no entityTypeMapping for class " + asmObject["sys_class_name"] + ". defaulting to server"
      asmObject["entityTypes"] = "server"

   # Identify any fields that would be useful to use as matchTokens...

   asmObject["matchTokens"] = [ asmObject["name"] + ":" + asmObject["uniqueId"] ]
   asmObject["matchTokens"].append( asmObject["uniqueId"] )
   asmObject["matchTokens"].append( asmObject["name"] )
   if asmObject.has_key("HostName"):
      if( asmObject["HostName"] ):
         asmObject["matchTokens"].append(asmObject["HostName"])
      

   if (asmObject.has_key("AssetLifecycleStatus") and len(assetLifecycleStatusFilterArray) > 0):
      if(asmObject["AssetLifecycleStatus"] in assetLifecycleStatusFilterArray):
         ciSysIdList.append(asmObject["uniqueId"])
         return(asmObject)
      else:
         print "This object AssetLifecycleStatus not in configuration: " + asmObject["AssetLifecycleStatus"].encode('utf-8') + ". Dropping object " + asmObject["name"].encode('utf-8')
         return(0)
   else:
      ciSysIdList.append(asmObject["uniqueId"])
      return(asmObject)


def getCiRelationships(ciType):

   ###################################################
   #
   # query Remedy baseRelationship table to obtain relationships
   #
   ###################################################

   global arsToken
   totalRelationships = 0
   global ciSysIdSet
   global ciSysIdList
   global readCisFromFile
   #ciType = "BMC_ComputerSystem"
   #ciType = "BMC_BaseRelationship"
   relationList = []

   readCiEntries = []
   writeToFile = 0
 
   readFromRest = 1

   if(readFromRest == 1):
      print "Entering read loop for " + ciType
      limit = 500
      method = "GET"
      isMore = 1
      offset = 0
      firstRun = 1
   
      while(isMore):
   
         asmObjectList = []
         
         requestUrl = 'https://' + cmdbServerDict["server"] + '/api/cmdb/v1.0/instances/BMC.ASSET/BMC.CORE/' + ciType + '?offset=' + str(offset) + "&limit=" + str(limit)
     
         retryTimer = 0

         for retry in [1,2,3]:
            retryTimer = retryTimer + 11
            try:
               request = urllib2.Request(requestUrl)
               request.add_header("Content-Type",'application/json')
               request.add_header("Authorization","AR-JWT " + arsToken)
               request.get_method = lambda: method
         
               response = urllib2.urlopen(request, timeout=10)
               ciDataResult = response.read()
         
            except IOError, e:
               print 'Failed to open "%s".' % requestUrl
               if hasattr(e, 'code'):
                  print 'We failed with error code - %s.' % e.code
                  if(str(e.code) == "401"):
                     print "appears to be that the auth token has expired. Generating a new one..."
                     getArsToken()
               elif hasattr(e, 'reason'):
                  print "The error object has the following 'reason' attribute :"
                  print e.reason
                  print "This usually means the server doesn't exist,",
                  print "is down, or we don't have an internet connection."
               else:
                  print "ERROR: Unable to read from URL: " + requestUrl
               if(retry == 3):
                  print("FATAL: READ ERROR AFTER 3 TRIES: ABORTING READ")
                  print("Aborted URL: " + requestUrl)
                  break
               else:
                  print "re-trying read"
                  time.sleep(retryTimer)
      
         #print "Result is: " + str(ciDataResult)
         relationEntries = json.loads(ciDataResult)
         print "FOUND INSTANCES: " + str(len(relationEntries["instances"])) + ", current offset is: " + str(offset)
         for rel in relationEntries["instances"]:
            #print "adding " + ci["instance_id"] + " to readCiEntries..."
            #readCiEntries.append(ci)
            asmObject = createAsmEdge(rel)
            if(asmObject != 0):
               asmObjectList.append(asmObject)
         if(writeToFile == 1):
            text_file = open(mediatorHome + "/log/" + ciType + ".json", "w")
            text_file.write(json.dumps(readCiEntries))
            text_file.close()

         numRelationships = len(relationEntries["instances"])
         totalRelationships = totalRelationships + numRelationships
         print "number of relationships found this fetch: " + str(numRelationships)
         print "total relationshipss: " + str(totalRelationships)
         edges = open(mediatorHome + "/file-observer-files/edges-" + startTime + ".json", "a")
         for asmEdge in asmObjectList:
            object_text = json.dumps(asmEdge)
            edges.write("E:" + object_text + "\n" + "W:5 millisecond" + "\n")
            edges.flush()
         edges.close() 
         del asmObjectList
         if(numRelationships < limit):
            print "no more"
            isMore = 0
         else:
            print "is more"
            offset = offset + limit
            isMore = 1
      
         #print str(len(readCiEntries)) + " items in the cmdb ci table"

  #    writeToFile = 1 

   #if(writeToFile):
      #print "writing " + str(len(readCiEntries)) + " ci items to file"
      #text_file = open(mediatorHome + "/log/" + ciType + ".json", "w")
      #text_file.write(json.dumps(readCiEntries))
      #text_file.close()
      

   #print "converting ciSysIdList to ciSysIdSet"
   #ciSysIdSet = set(ciSysIdList) # convert our ciSysIdList to a set for faster evaluation
   #print "there are " + str(len(ciSysIdSet)) + " items in ciSysIdSet, while there are " + str(len(ciSysIdList)) + " items in ciCysIdList..."
   #return()

def createAsmEdge(rawrel):

   rel = rawrel["attributes"]

   asmObject = {}

   #if(1==1):
   if(rel["Destination.InstanceId"] in ciSysIdSet and rel["Source.InstanceId"] in ciSysIdSet):
      #print "===== both parent and child in ciSysIdList, i.e. in topology, saving relationship. Parent: " + str(rel["parent"]["value"]) + ", Child: " + str(rel["child"]["value"])
      #print "Evaluating relationship: " + json.dumps(rel)
      if rel.has_key("Type"):
         if rel["Type"] not in relTypeSet:
            relTypeSet.add(rel["Type"])
         if( rel["Type"] in relationshipMappingDict):
            thisRelType = relationshipMappingDict[ rel["Type"] ]
         else:
            print "unmapped relationship type: " + rel["Type"] + ". Using default 'connectedTo'."
            thisRelType = "connectedTo"
      else:
         thisRelType = "connectedTo"
         rel["Type"] = "Relationship Type field does not exist in CMDB"
      relationDict = { "_fromUniqueId": rel["Source.InstanceId"], "_toUniqueId": rel["Destination.InstanceId"], "_edgeType": thisRelType, "Type": rel["Type"] }
      #print "found a relevant connection... adding to relationList array..."
      #relationList.append(relationDict)
      return(relationDict)
   else:
      return(0)



def DONOTUSEcreateAsmVertex(ci):



   asmObject = {}
   asmObject["uniqueId"] = ci["instance_id"]
   asmObject["sys_class_name"] = ci["class_name_key"]["name"]
   for prop in ci["attributes"]:
      if(ci["attributes"][prop]):
         asmObject[prop] = ci["attributes"][prop]
   if asmObject.has_key("HostName"):
      asmObject["name"] = asmObject["HostName"]
   else:
      if(asmObject.has_key("Name")):
         asmObject["name"] = asmObject["Name"]
      else:
         asmObject["name"] = asmObject["uniqueId"]
   asmObject["_operation"] = "InsertReplace"
   asmObject["uniqueId"] = asmObject["uniqueId"]
   if( asmObject["sys_class_name"] in entityTypeMappingDict):
      asmObject["entityTypes"] = [ entityTypeMappingDict[asmObject["sys_class_name"]] ]
   else:
      if(ciType in entityTypeMappingDict):
         asmObject["entityTypes"] = [ entityTypeMappingDict[ciType] ]
      else:
         print "no entitytype mapping for ciType: " + ciType + ", defaulting to 'server'"
         asmObject["entityTypes"] = "server"

   # Identify any fields that would be useful to use as matchTokens...

   asmObject["matchTokens"] = [ asmObject["name"] + ":" + asmObject["uniqueId"] ]
   asmObject["matchTokens"].append( asmObject["uniqueId"] )
   asmObject["matchTokens"].append( asmObject["name"] )
   if asmObject.has_key("HostName"):
      if( asmObject["HostName"] ):
         asmObject["matchTokens"].append(asmObject["HostName"])
      

   ciSysIdList.append(asmObject["uniqueId"])
   return(asmObject)


def DoNotUsegetCiRelationships():

   ###################################################
   #
   # query Remedy cmdb_rel table
   #
   ###################################################
   global readRelationshipsFromFile
   global totalSnowCmdbRelationships

   allRelEntries = []
   writeToFile = 1
   readFromRest = 0
   totalRelationships = 0

   if(readRelationshipsFromFile == "1"):
      writeToFile = 0
      print "Loading relationships from file rather than ServiceNow REST interface..."
      if(os.path.isfile(mediatorHome  + "/log/ciRelationships.json")):
         with open(mediatorHome + "/log/ciRelationships.json") as text_file:
            for relResult in text_file:
               #print(str(relResult))
               relEntries = json.loads(relResult)
               print "JPCLOG: FOUND " + str(len(relEntries["result"])) + " relationships for evaluation in this round of load."
               totalRelationships = totalRelationships + len(relEntries["result"])
               for rel in relEntries["result"]:
                  evaluateRelationship(rel)
         text_file.close()
         print "READ COMPLETE. Evaluated " + str(totalRelationships) + " relationships for relevance."
         readFromRest = 0
      else:
         print "NOTE: read from file selected, yet file for relationships does not exist. Obtaining relationships from REST API"
         readFromRest = 1
   else:
      print "reading relationships from ServiceNow REST API"
      readFromRest = 1
  
   if(readFromRest == 1):  
 
      limit = 50000
      authHeader = 'Basic ' + base64.b64encode(snowServerDict["user"] + ":" + snowServerDict["password"])
      method = "GET"
      isMore = 1
      offset = 0
      relPass = 1
      retryQuery = 0
      totalRelationshipsEvaluated = 0
   
      while(isMore):
 
         if(retryQuery > 0):
            if(retryQuery == 4):
               print("FATAL: Query at position: " + offset + " has failed 4 times. Skipping this segment...")
               offset = offset + limit
            else:
               print "retrying query due to read failure"
  
         requestUrl = 'https://' + snowServerDict["server"] + '/api/now/table/cmdb_rel_ci?sysparm_limit=' + str(limit) + '&sysparm_offset=' + str(offset)
         print("issuing query: " + requestUrl)
     
         for retry in [1,2,3]:
            try:
               request = urllib2.Request(requestUrl)
               request.add_header("Content-Type",'application/json')
               request.add_header("Accept",'application/json')
               request.add_header("Authorization",authHeader)
               request.get_method = lambda: method
         
               response = urllib2.urlopen(request)
               relDataResult = response.read()
               break
         
            except (IOError, IncompleteRead), e:
               print 'Failed to open "%s".' % requestUrl
               if hasattr(e, 'code'):
                  print 'We failed with error code - %s.' % e.code
               elif hasattr(e, 'reason'):
                  print "The error object has the following 'reason' attribute :"
                  print e.reason
                  print "This usually means the server doesn't exist,",
                  print "is down, or we don't have an internet connection."
               else:
                  print("ERROR: Unable to read from URL: " + requestUrl)
               if(retry == 3):
                  print("FATAL: READ ERROR AFTER 3 TRIES: ABORTING READ")
                  print("Aborted URL: " + requestUrl)
                  exit()

         try:
            relEntries = json.loads(relDataResult)
            retryQuery = 0
         except ValueError:
            print("ERROR: JSON parsing failed. Retrying query")
            retryQuery = retryQuery + 1

         if(retryQuery == 0):          # Successful read/load. No need to retry

            if(writeToFile):
               print "Saving " + str(len(relEntries["result"])) + " relationship items to file for future load"
               if(relPass == 1):
                  text_file = open(mediatorHome + "/log/ciRelationships.json", "w")
               else:
                  text_file = open(mediatorHome + "/log/ciRelationships.json", "a")
               text_file.write(relDataResult)
               text_file.write("\n")
               text_file.close()

            totalRelationshipsEvaluated = totalRelationshipsEvaluated + len(relEntries["result"])
   
            print "evaluating " + str(len(relEntries["result"])) + " relationships in this pass"
            for rel in relEntries["result"]:
               evaluateRelationship(rel)

            numRel = len(relEntries["result"])
   
            if(numRel < limit):
               if(totalRelationshipsEvaluated <= (totalSnowCmdbRelationships - (limit * 2))):
                  print("suspected short read... retrying")
                  #offset = offset + limit
                  #relPass = relPass + 1
                  retryQuery = retryQuery + 1
               else:
                  isMore = 0
            else:
               offset = offset + limit
               isMore = 1
               relPass = relPass + 1
               retryQuery = 0
      
         #print str(numRel) + " items in the cmdb relationships table"

      print "Relationship evaluation complete. Evaluated a total of " + str(totalRelationshipsEvaluated) + " relationships out of an expected " + str(totalSnowCmdbRelationships)


#   if(writeToFile):
#      print "writing " + str(len(allRelEntries)) + " relationship items to file"
#      text_file = open(mediatorHome + "/log/ciRelationships.json", "w")
#      text_file.write(json.dumps(allRelEntries))
#      text_file.close()
 
   #print "cycling through " + str(len(allRelEntries)) + " relationship entries"
   #numRels = len(allRelEntries)
   #relCount = 0
   #print "there are " + str(len(ciSysIdSet)) + " items in ciSysIdSet, while there are " + str(len(ciSysIdList)) + " items in ciCysIdList..."



def evaluateRelationship(rel):

   global ciSysIdSet
   global relationList
   #global allRelEntries

   relevant = 0
   
   if(isinstance(rel, dict)):
      pass
   else:
      print("relation passed to evaluateRelationship is not a dictionary. It contains the following:")
      print(str(rel))
      return

   if(rel.has_key("child") and rel.has_key("parent")):
      pass
   else:
      return

   if(isinstance(rel["child"], dict) and isinstance(rel["parent"], dict)):
      #print "found connection with both parent and child."
      #print "Parent is: " + rel["parent"]["value"]
      #print "Child is: " + rel["child"]["value"]
      #print "evaluating ciSysIdSet to see if both child/parent is there. Length of ciSysIdSet is: " + str(len(ciSysIdSet))
      if(rel["child"]["value"] in ciSysIdSet and rel["parent"]["value"] in ciSysIdSet):
         #if(str(rel["parent"]) in ciSysIdList):
         if 1==1:
            #print "===== both parent and child in ciSysIdList, i.e. in topology, saving relationship. Parent: " + str(rel["parent"]["value"]) + ", Child: " + str(rel["child"]["value"])
            if( rel["type"]["value"] in relationshipMappingDict):
               thisRelType = relationshipMappingDict[ rel["type"]["value"] ]
            else:
               print "unmapped relationship type: " + rel["type"]["value"] + ". Using default 'connectedTo'."
               thisRelType = "connectedTo"
            relationDict = { "_fromUniqueId": rel["parent"]["value"], "_toUniqueId": rel["child"]["value"], "_edgeType": thisRelType }
            relationDict["originalRelSysId"] = rel["type"]["value"]
            if rel["type"]["value"] not in relTypeSet:
               relTypeSet.add(rel["type"]["value"])
            #print "found a relevant connection... adding to relationList array..."
            relationList.append(relationDict)
         else:
            pass
      else:
         pass
         #print "neither parent or child is in siSysIdList, discarding"
   else:
      pass
      # either parent or child designated is not returning dict for this entry

def getCiDetail(sys_id, ciType):

   ###############################################################
   #
   # This function grabs ci detail data based on sys_id and ciType
   # ---+++ CURRENTLY UNIMPLEMENTED +++---
   #
   ###############################################################

 
   authHeader = 'Basic ' + base64.b64encode(snowServerDict["user"] + ":" + snowServerDict["password"])

   method = "GET"

   requestUrl = 'https://' + snowServerDict["server"] + '/api/now/cmdb/instance/' + ciType + "/" + sys_id + "?sysparm_limit=10000"


   try:
      request = urllib2.Request(requestUrl)
      request.add_header("Content-Type",'application/json')
      request.add_header("Accept",'application/json')
      request.add_header("Authorization",authHeader)
      request.get_method = lambda: method

      response = urllib2.urlopen(request)
      ciDetailResult = response.read()

   except IOError, e:
      print 'Failed to open "%s".' % requestUrl
      if hasattr(e, 'code'):
         print 'We failed with error code - %s.' % e.code
      elif hasattr(e, 'reason'):
         print "The error object has the following 'reason' attribute :"
         print e.reason
         print "This usually means the server doesn't exist,",
         print "is down, or we don't have an internet connection."
      return False

   ##print "logging out..."

   #print ciDetailResult
   ciEntry = json.loads(ciDetailResult)

   for relation in ciEntry["result"]["inbound_relations"]:
      createCiRelationship(sys_id, relation, "inbound")

   for relation in ciEntry["result"]["outbound_relations"]:
      createCiRelationship(sys_id, relation, "outbound")

   ciObject = ciEntry["result"]["attributes"]
#   ciObject["uniqueId"] = 
#   ciObject["name"] = 
#   cnaDict["entityTypes"] = 

   return(ciObject)


def createCiRelationship(sys_id, relationDict, relationDir):

   relationType = relationDict["type"]["display_value"]
   if relationType in relationshipMappingDict:
      edgeType = relationshipMappingDict[relationType]
   else:
      edgeType = "connectedTo"
      print "Unmapped relationship type " + relationType + ", using connectedTo by default" 
   
   if(relationDir == "inbound"):
      relationDict = { "_fromUniqueId": relationDict["target"]["value"], "_toUniqueId": sys_id, "_edgeType": edgeType}
      relationList.append(relationDict)
   elif(relationDir == "outbound"):
      relationDict = { "_fromUniqueId": sys_id, "_toUniqueId": relationDict["target"]["value"], "_edgeType": edgeType}
      relationList.append(relationDict)
   
   

#   cnaDict["uniqueId"] = id
#   cnaDict["name"] = cnaDict["MACAddress"]
#   cnaDict["entityTypes"] = [ "networkinterface" ]

   return cnaDict

######################################
#
#  ----   Main multiprocess dispatcher
#
######################################

if __name__ == '__main__':

   # messy global definitions in the interest of saving time..........

   global mediatorHome
   global logHome
   global configHome
   configDict = {}
   global asmDict
   asmDict = {}
   global snowServerDict
   global relationshipMappingDict
   relationshipMappingDict = {}
   #global ciList
   #ciList = []
   global ciSysIdList
   ciSysIdList = []
   global ciSysIdSet
   ciSysIdSet = set()
   global relationList
   relationList = []
   global entityTypeMappingDict
   entityTypeMappingDict = {}
   global writeToFile
   global relTypeSet
   relTypeSet = set() 
   global totalSnowCmdbRelationships
   global primaryCapabilityMappingDict
   primaryCapabilityMappingDict = {}
   global assetLifecycleStatusFilterArray
   assetLifecycleStatusFilterArray = []
   global primaryCapabilityFilterArray
   primaryCapabilityFilterArray = []


   ############################################
   #
   # verify directories and load configurations
   #
   ############################################

   mediatorBinDir = os.path.dirname(os.path.abspath(__file__))
   extr = re.search("(.*)bin", mediatorBinDir)
   if extr:
      mediatorHome = extr.group(1)
      #print "Mediator home is: " + mediatorHome
   else:
      print "FATAL: unable to find mediator home directory. Is it installed properly? bindir = " + mediatorBinDir
      exit()

   if(os.path.isdir(mediatorHome + "log")):
      logHome = extr.group(1)
   else:
      print "FATAL: unable to find log directory at " + mediatorHome + "log"
      exit()

   if(os.path.isfile(mediatorHome + "/config/cmdbserver.conf")):
      cmdbServerDict = loadCmdbServer(mediatorHome + "/config/cmdbserver.conf")
   else:
      print "FATAL: unable to find ServiceNow server list file " + mediatorHome + "/config/snowserver.conf"
      exit()

   if(os.path.isfile(mediatorHome + "/config/classlist.conf")):
      ciClassList = loadClassList(mediatorHome + "/config/classlist.conf")
   else:
      print "FATAL: unable to find ServiceNow server list file " + mediatorHome + "/config/snowserver.conf"
      exit()

#   if(os.path.isfile(mediatorHome + "/config/asmserver.conf")):
#      asmServerDict = loadAsmServer(mediatorHome + "/config/asmserver.conf")
#   else:
#      print "FATAL: unable to find ASM server configuration file " + mediatorHome + "/config/asmserver.conf"
#      exit()

   if(os.path.isfile(mediatorHome  + "/config/relationship-mapping.conf")):
      relationshipMapping = loadRelationshipMapping(mediatorHome + "/config/relationship-mapping.conf")
   else:
      print "FATAL: no relationship mapping file available at " + mediatorHome + "/config/relationship-mapping.conf"
      exit()

   if(os.path.isfile(mediatorHome  + "/config/entitytype-mapping.conf")):
      entityMapping = loadEntityTypeMapping(mediatorHome + "/config/entitytype-mapping.conf")
   else:
      print "FATAL: no entity type mapping file available at " + mediatorHome + "/config/entitytype-mapping.conf"
      exit()

   if(os.path.isfile(mediatorHome  + "/config/primarycapability-mapping.conf")):
      primaryCapabilityMapping = loadPrimaryCapabilityMapping(mediatorHome + "/config/primarycapability-mapping.conf")
   else:
      print "FATAL: no PrimaryCapability mapping file available at " + mediatorHome + "/config/entitytype-mapping.conf"
      exit()

   if(os.path.isfile(mediatorHome  + "/config/assetlifecyclestatus-filter.conf")):
      loadAssetLifecycleStatusFilter(mediatorHome + "/config/assetlifecyclestatus-filter.conf")
   else:
      print "No AssetLifecycleStatus filter file available at " + mediatorHome + "/config/assetlifecyclestatus-filter.conf. Will load objects with any lifecycle status."

   if(os.path.isfile(mediatorHome  + "/config/primarycapability-filter.conf")):
      loadPrimaryCapabilityFilter(mediatorHome + "/config/primarycapability-filter.conf")
   else:
      print "FATAL: no primary capability filter file available at " + mediatorHome + "/config/primarycapability-filter.conf"
      exit()

   if(os.path.isfile(mediatorHome  + "/config/getCmdbData.props")):
      configVars = loadProperties(mediatorHome + "/config/getCmdbData.props")
      sys.stderr.write(str(configVars))
      if 'readCisFromFile' in configVars.keys():
         global readCisFromFile
         readCisFromFile = configVars['readCisFromFile']
         if(readCisFromFile == "1"):
            sys.stderr.write("will read CIs from file if available")
         else:
            sys.stderr.write("will read CIs from ServiceNow REST API")
      else:
         sys.stderr.write("readCisFromFile property not set, defaulting to 0, read from ServiceNow REST API")
         readCisFromFile = 0
      if 'readRelationshipsFromFile' in configVars.keys():
         global readRelationshipsFromFile
         readRelationshipsFromFile = configVars['readRelationshipsFromFile']
         if(readRelationshipsFromFile == "1"):
            sys.stderr.write("will read relationships from file if available")
         else:
            sys.stderr.write("will read relationships from ServiceNow REST API")
      else:
         sys.stderr.write("readRelationshipsFromFile not in properties file, defaulting to 0, read from ServiceNow REST API")
         readRelationshipsFromFile = 0
   else:
      print "FATAL: unable to find the properties file " + mediatorHome + "/config/getCmdbData.props"
      exit()

#   print("readCisFromFile is: " + str(readCisFromFile))
#   print("readRelationshipsFromFile is: " + str(readRelationshipsFromFile))


# BEGINS HERE

   global arsToken

   getArsToken()

   #getCiData(token)
   #getArsCmdb(token)
   #listArsCmdbNamespaces(token)
   #listArsCmdbClasses(token)


   ############################################################################
   #
   # Cycle through each class of interest, and obtain CI records for each class
   #
   ############################################################################

   global startTime
   startTime=datetime.datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
   print("Start time: " + startTime)
   for className in ciClassList:
      print "querying Remedy CMDB for all CIs of type " + className
      getCiData(className)

   # Pull relationships

   print "querying Remedy CMDB for relationships"
   getCiRelationships("BMC_BaseRelationship")
   getCiRelationships("BMC_Dependency")

   sys.stderr.write("releasing token: " + arsToken)
   if(releaseArsToken(arsToken)):
      sys.stderr.write("successfully released token")
   else:
      sys.stderr.write("error releasing token")

   endTime=datetime.datetime.now().strftime("%Y-%m-%d--%H-%M-%S")

   print "Remedy topology mediation complete. Start time: " + startTime + ", end time: " + endTime

   exit()

#   print "CI mediation complete. Writing vertices file..."   
#   vertices = open(mediatorHome + "/file-observer-files/vertices-" + str(datetime.datetime.now()) + ".json", "a")
#   for ci in ciList:
#      ci_text = json.dumps(ci)
#      vertices.write("V:" + ci_text + "\n" + "W:5 millisecond" + "\n")
#      vertices.flush()
#   vertices.close()
#   totalCi = len(ciList)
##   del ciList
#   gc.collect()
   

   ###################################################################################################################################
   #
   # Next, we pull the relationship table. Then we will evaluate relationships that only are pertinent to our CIs of interest.
   # Both CI's of a relationship must be in our CI Class list for inclusion in topology. Any other relationship is deemed irrelevant
   # and discarded.
   #
   ###################################################################################################################################

   print "Loading and evaluating relationship table"
   totalSnowCmdbRelationships = getTotalRelCount()
   getCiRelationships()

## multi-processing stuff that isn't in use currently. could be enabled to concurrently pull all data for CIs and relationships to speed up the mediator
#      p = Process(target=getCiData, args=(className,))
#      p.start()

#   for ci in ciList:
#      print ci["name"]



   # Currently, this mediator only writes out file observer files. There are functions defined above that can directly inject into ASM via REST, but not in use at this time.
   # e.g. "createAsmResource() can be used to send a ci dict in ciList directly to the ASM rest interface
 
      
   print "Relationship mediation complete. Writing edges..."   
   edges = open(mediatorHome + "/file-observer-files/edges-" + str(datetime.datetime.now()) + ".json", "w")
   for rel in relationList:
      ci_text = json.dumps(rel)
      edges.write("E:" + ci_text + "\n" + "W:5 millisecond" + "\n")
      edges.flush()
   totalRelation = len(relationList)
   del relationList
   gc.collect()
   edges.close()
      
   print "Mediation complete."
   print "Number of CIs: " + str(totalCi)
   print "Number of Relations: " + str(totalRelation)
   print "Mediation started at: " + startTime
   print("Mediation completed at: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

   #debug info

   ## These functions may be used to send CI and relationships directly to ASM REST interface:
   # UNTESTED - this is code from the HMC mediation code available here: https://github.ibm.com/jcress/HMC-Mediator-for-Agile-Service-Manager

   #for ci in ciList:
   #   createAsmResource(ci)

   #for rel in relationList:
   #   createAsmConnection(rel)

   print "Unique relation types:"
   for relType in relTypeSet:
      print relType
      
      

      
   print "all done"

   exit()

   # debug info


