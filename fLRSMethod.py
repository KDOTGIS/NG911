#-------------------------------------------------------------------------------
# Name:        module2
# Purpose:
#
# Author:      kyleg
#
# Created:     02/10/2014
# Copyright:   (c) kyleg 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from NG911_Config import gdb, DOTRoads
import re

"""
This module encodes a string using Soundex, as described by
http://en.wikipedia.org/w/index.php?title=Soundex&oldid=466065377

Only strings with the letters A-Z and of length >= 2 are supported.
"""

invalid_re = re.compile("[AEHIOUWY]|[^A-Z]")
numerical_re = re.compile("[A-Z]")

charsubs = {'B': '1', 'F': '1', 'P': '1', 'V': '1',
            'C': '2', 'G': '2', 'J': '2', 'K': '2',
            'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
            'D': '3', 'T': '3', 'L': '4', 'M': '5',
            'N': '5', 'R': '6'}

def normalize(s):
    """ Returns a copy of s without invalid chars and repeated letters. """
    # remove invalid chars
    first = s[0].upper()
    s = re.sub(invalid_re, "", s.upper()[1:])
    # remove repeated chars
    char = None

    s_clean = first

    for c in s:
        if char != c:
            s_clean += c
        char = c

    return s_clean


def soundex(s):
#""" Encode a string using Soundex.
#Takes a string and returns its Soundex representation.
#"""
    if len(s) < 2:
        return None
    s = normalize(s)
    last = None
    enc = s[0]
    for c in s[1:]:
        if len(enc) == 4:
            break
        if charsubs[c] != last:
            enc += charsubs[c]
        last = charsubs[c]
    while len(enc) < 4:
        enc += '0'
    return enc


#this module applies soundex to named streets, and pads the numbered streets with zeros, keeping the numbering system intact
def numdex(s):
    if s[0] in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']:
        numerical_re = re.compile("[A-Z]|[^0-9][^0-9][^0-9][^0-9]")
        s=re.sub(numerical_re,"", s.zfill(4))
        return s.zfill(4)
    else:
        return soundex(s)

#removes street centerlines from the topology and creates geometric network, then checks geometric network connectivity
def StreetNetworkCheck(gdb):
    from arcpy import env, Exists, VerifyAndRepairGeometricNetworkConnectivity_management, RemoveFeatureClassFromTopology_management, CreateGeometricNetwork_management, FindDisconnectedFeaturesInGeometricNetwork_management
    checkfile = gdb
    env.workspace = checkfile
    print topo
    fd = arcpy.ListDatasests
    geonet = fd+"\Street_Network"
    #print geonet
    if Exists(geonet):
        print "Street Geometric Network Already Exists"
    else:
        RemoveFeatureClassFromTopology_management(topo, "RoadCenterline")
        CreateGeometricNetwork_management(fd, "Street_Network", "RoadCenterline SIMPLE_EDGE NO", "#", "#", "#", "#", "#")
    FindDisconnectedFeaturesInGeometricNetwork_management(fd+"/RoadCenterline", "Roads_Disconnected")
    StreetLogfile = reviewpath+"/KDOTReview/"+ntpath.basename(ng911)+".log"
    VerifyAndRepairGeometricNetworkConnectivity_management(geonet, StreetLogfile, "VERIFY_ONLY", "EXHAUSTIVE_CHECK", "0, 0, 10000000, 10000000")



def ConflateKDOTrestart(gdb, DOTRoads):
    from arcpy import SelectLayerByLocation_management, FeatureClassToFeatureClass_conversion
    from arcpy import env
    env.overwriteOutput = 1
    checkfile = gdb
    MakeFeatureLayer_management(DOTRoads+"/KDOT_HPMS_2012","KDOT_Roads","#","#","#")
    MakeFeatureLayer_management(checkfile+"/RoadCenterline","RoadCenterline","#","#","#")
    SelectLayerByLocation_management("KDOT_Roads","INTERSECT","RoadCenterline","60 Feet","NEW_SELECTION")
    FeatureClassToFeatureClass_conversion("KDOT_Roads",checkfile+r"/NG911","KDOT_Roads_Review","#","#","#")


#Prepares Street centerlines for LRS, detects changes and transfers the HPMS key field from the KDOT roads
def ConflateKDOT1(gdb, DOTRoads):
    from arcpy import MakeFeatureLayer_management, Exists, TransferAttributes_edit, DetectFeatureChanges_management, RubbersheetFeatures_edit, SelectLayerByLocation_management, FeatureClassToFeatureClass_conversion, GenerateRubbersheetLinks_edit, RubbersheetFeatures_edit
    from arcpy import env
    env.overwriteOutput = 1
    checkfile = gdb
    spatialtolerance = "20 feet"
    #MakeFeatureLayer_management(checkfile+"/AuthoritativeBoundary","AuthoritativeBoundary_Layer","#","#","#")
    #MakeFeatureLayer_management(checkfile+"/CountyBoundary","CountyBoundary_Layer","#","#","#")
    MakeFeatureLayer_management(DOTRoads+"/KDOT_HPMS_2012","KDOT_Roads","#","#","#")
    MakeFeatureLayer_management(checkfile+"/RoadCenterline","RoadCenterline","#","#","#")
    if Exists(checkfile+r"/NG911/KDOT_Roads_Review"):
        print "selection of KDOT roads for conflation already exists"
    else:
        SelectLayerByLocation_management("KDOT_Roads","INTERSECT","RoadCenterline","60 Feet","NEW_SELECTION")
        FeatureClassToFeatureClass_conversion("KDOT_Roads",checkfile+r"/NG911","KDOT_Roads_Review","#","#","#")
    MakeFeatureLayer_management(checkfile+"/KDOT_Roads_Review","KDOT_Roads_Review","#","#","#")
    GenerateRubbersheetLinks_edit("KDOT_Roads_Review","RoadCenterline",checkfile+r"/NG911/RoadLinks",spatialtolerance,"ROUTE_ID LRSKEY",checkfile+r"/RoadMatchTbl")
    MakeFeatureLayer_management(checkfile+"/NG911/RoadLinks","RoadLinks","#","#","#")
    MakeFeatureLayer_management(checkfile+"/NG911/RoadLinks_pnt","RoadLinks_pnt","#","#","#")
    RubbersheetFeatures_edit("KDOT_Roads_Review","RoadLinks","RoadLinks_pnt","LINEAR")
    DetectFeatureChanges_management("KDOT_Roads_Review","RoadCenterline",checkfile+r"/NG911/RoadDifference",spatialtolerance,"#",checkfile+r"/RoadDifTbl",spatialtolerance,"#")
    MakeFeatureLayer_management(checkfile+"/NG911/RoadDifference","RoadDifference","#","#","#")
    TransferAttributes_edit("KDOT_Roads_Review","RoadCenterline","YEAR_RECORD;ROUTE_ID",spatialtolerance,"#",checkfile+r"/LRS_MATCH")

def LRSRoutePrep(gdb, DOTroads):
    checkfile = gdb
    from arcpy import AddField_management, CalculateField_management, AddJoin_management, MakeTableView_management, RemoveJoin_management
    AddField_management(checkfile+"/RoadCenterline", "RouteName", "TEXT")
    AddField_management(checkfile+"/RoadCenterline", "KDOT_ADMO", "TEXT")
    AddField_management(checkfile+"/RoadCenterline", "PREDIR", "TEXT")
    AddField_management(checkfile+"/RoadCenterline", "Soundex", "TEXT")
    AddField_management(checkfile+"/RoadCenterline", "KDOT_Surface", "TEXT")
    AddField_management(checkfile+"/RoadCenterline", "KDOT_START_DATE", "DATE")
    AddField_management(checkfile+"/RoadCenterline", "KDOT_END_DATE", "DATE")
    AddField_management("RoadCenterline", "SuffCode", "TEXT")
    AddField_management("RoadCenterline", "UniqueNo", "TEXT")
    CalculateField_management("RoadCenterline","KDOT_START_DATE","1/1/1901","PYTHON_9.3","#")
    CalculateField_management("RoadCenterline","KDOT_ADMO","!ROUTE_ID![3]","PYTHON_9.3","#")
    CalculateField_management("RoadCenterline","PREDIR","0","PYTHON_9.3","#")
    # codify the road prefix direction for LRS
    Kdotdbfp = DOTRoads
    MakeTableView_management(Kdotdbfp+"\NG911_RdDir", "NG911_RdDir")
    CalculateField_management("RoadCenterline","PREDIR","0","PYTHON_9.3","#")
    AddJoin_management("RoadCenterline","PRD","NG911_RdDir", "RoadDir", "KEEP_COMMON")
    CalculateField_management("RoadCenterline","PREDIR","!NG911_RdDir.RdDirCode!","PYTHON_9.3","#")
    RemoveJoin_management("RoadCenterline")
    #Codify the Road Type for LRS
    MakeTableView_management(Kdotdbfp+"\NG911_RdTypes", "NG911_RdTypes")
    CalculateField_management("RoadCenterline","SuffCode","0","PYTHON_9.3","#")
    AddJoin_management("RoadCenterline","STS","NG911_RdTypes", "RoadTypes", "KEEP_COMMON")
    CalculateField_management("RoadCenterline","SuffCode","!NG911_RdTypes.LRS_CODE_TXT!","PYTHON_9.3","#")
    RemoveJoin_management("RoadCenterline")

    #Codify the County number for LRS (based on right side of street based on addressing direction, calculated for LEFT and RIGHT from NG911)
    AddField_management(checkfile+"/RoadCenterline", "KDOT_COUNTY_L", "TEXT")
    AddField_management(checkfile+"/RoadCenterline", "KDOT_COUNTY_R", "TEXT")
    CalculateField_management("RoadCenterline","KDOT_COUNTY_L","!ROUTE_ID![:3]","PYTHON_9.3","#")
    CalculateField_management("RoadCenterline","KDOT_COUNTY_R","!ROUTE_ID![:3]","PYTHON_9.3","#")
    MakeTableView_management(Kdotdbfp+"\NG911_County", "NG911_County")
    AddJoin_management("RoadCenterline","COUNTY_L","NG911_County", "CountyName", "KEEP_COMMON")
    CalculateField_management("RoadCenterline","KDOT_COUNTY_L","!NG911_County.CountyNumber!","PYTHON_9.3","#")
    RemoveJoin_management("RoadCenterline")
    AddJoin_management("RoadCenterline","COUNTY_R","NG911_County", "CountyName", "KEEP_COMMON")
    CalculateField_management("RoadCenterline","KDOT_COUNTY_R","!NG911_County.CountyNumber!","PYTHON_9.3","#")
    RemoveJoin_management("RoadCenterline")

    #Codify the City Limit\city number for LRS , calculated for LEFT and RIGHT from NG911)
    MakeTableView_management(Kdotdbfp+"\City_Limits", "City_Limits")
    AddField_management(checkfile+"/RoadCenterline", "KDOT_CITY_L", "TEXT")
    AddField_management(checkfile+"/RoadCenterline", "KDOT_CITY_R", "TEXT")
    CalculateField_management("RoadCenterline","KDOT_CITY_L","999","PYTHON_9.3","#")
    AddJoin_management("RoadCenterline","MUNI_R","City_Limits", "CITY", "KEEP_COMMON")
    CalculateField_management("RoadCenterline","KDOT_CITY_R","!City_Limits.CITY_CD!.zfill(3)","PYTHON_9.3","#")
    RemoveJoin_management("RoadCenterline")
    AddJoin_management("RoadCenterline","MUNI_L","City_Limits", "CITY", "KEEP_COMMON")
    CalculateField_management("RoadCenterline","KDOT_CITY_L","!City_Limits.CITY_CD!.zfill(3)","PYTHON_9.3","#")
    RemoveJoin_management("RoadCenterline")

    #calculate what should be a nearly unique LRS Route key based on the decoding and street name soundex/numdex function
    CalculateField_management("RoadCenterline","Soundex","numdex(!RD!)","PYTHON_9.3","#")
    CalculateField_management("RoadCenterline","RouteName","str(!KDOT_COUNTY!)+str(!KDOT_URBAN!)+str(!PREDIR!) + !Soundex! + str(!SuffCode!)+!TRAVEL!","PYTHON_9.3","#")
    MakeTableView_management(checkfile+"\RoadAlias", "RoadAlias")
    #Pull out State Highways to preserve KDOT LRS Key (CANSYS FORMAT - non directional CRAD)
    AddJoin_management("RoadCenterline","SEGID","RoadAlias", "SEGID")
    SelectLayerByAttribute_management("RoadCenterline", "NEW_SELECTION", "RoadAlias.LABEL LIKE 'US %' OR RoadAlias.LABEL LIKE 'I %' OR RoadAlias.LABEL LIKE 'K %'" )
    RemoveJoin_management("RoadCenterline")
    CalculateField_management("RoadCenterline","RouteName","!ROUTE_ID![:11]","PYTHON_9.3","#")
    SelectLayerByAttribute_management("RoadCenterline", "REMOVE_FROM_SELECTION", "TRAVEL is null" )
    CalculateField_management("RoadCenterline","RouteName","!ROUTE_ID![:11]+!TRAVEL!","PYTHON_9.3","#")
    #CalculateField_management("RoadCenterline_StateHwy","RouteName","!ROUTE_ID![3]+!ROUTE_ID![6:11]","PYTHON_9.3","#")

# makes the LRS route layer and dissolves the NG911 fields to LRS event tables
def LRSIt():
    MakeRouteLayer_na()

    pass


ConflateKDOT1(gdb, DOTRoads)
LRSRoutePrep(gdb, DOTRoads)
