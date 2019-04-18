# Copyright (c) 2019 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.


import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import string
import time
import re
import commands
import argparse
import sys
from argparse import ArgumentParser, RawTextHelpFormatter


bugRow=0
bugCol =''
columnInfo='I'
bugId=''
bugData=''
bugCountTotal=0
bugCountFixed=0
bugCountNotFixed=0
bugCountNotResolved=0
bugCountError=0
sheetName=''
release=''
spreadSheet=''

if __name__ == '__main__':
    parser = ArgumentParser(description='This script iterates through a list of bugs and checks if the bugs are fixed in a specific release the Customer is interested in. \nPros:You wont miss your lunch break, Coffee breaks, Sleep etc', formatter_class=RawTextHelpFormatter)

    parser.add_argument('-s','--sheet', help='Please specify the Sheet Name', required=True)
    parser.add_argument('-l','--link', help='Please specify the URL of the Google SpreadSheet', required=True)
    parser.add_argument('-r','--releaseTrain',help='Please specify the Release Train. Check if the bug fix has been merged to the specific project (e.g. delhi.A1-rel)', required=True)
    parser.add_argument('-bugCol','--bugColumn',help='Please specify the Bug Column', required=False, default='B')
    parser.add_argument('-bugRow','--rowNumber',help='Please specify the starting Row number', required=False, type=int, default=2)
    parser.add_argument('-statusCol','--statusColumn',help='Please specify the starting Row number', required=False)

    args = vars(parser.parse_args())

    release                 =   args['releaseTrain']
    sheetName               =   args['sheet']
    spreadSheet             =   args['link']
    bugCol                  =   args['bugColumn']
    bugRow                  =   args['rowNumber']
    columnInfo              =   args['statusColumn']

print "\n"
print "Spread Sheet URL           : %s" %spreadSheet
print "Sheet Name                 : %s" %sheetName

scope = ['https://spreadsheets.google.com/feeds']
credentials = ServiceAccountCredentials.from_json_keyfile_name('json_gspread_auth_key.json',scope)
gc = gspread.authorize(credentials)
sh =gc.open_by_url('%s'%spreadSheet)
wksheet = sh.worksheet(sheetName)
allValues = wksheet.get_all_values()
rowFinalValue=len(allValues)+ 1
print "Total Entries in the sheet : %d" %(rowFinalValue-1)

stringBugFixed = 'Conclusion   :  Fixed in '+release
stringBugNotResolved="ERROR        :  Bug is NOT RESOLVED !!!"
stringBugNotFixed="Conclusion   :  NOT Fixed in "+release
stringNoChangeList='No change list found'
stringError='ERROR        :  Unable to fetch data'
cmd='wheresMyFix.py -p' + ' '+release
matchString='.*Conclusion\s+:\s+Fixed\sIn\s' + release + '.*'

def updateCell(col,row,bugId,bugStatus,swatString):
   scope = ['https://spreadsheets.google.com/feeds']
   credentials = ServiceAccountCredentials.from_json_keyfile_name('json_gspread_auth_key.json',scope)
   gc = gspread.authorize(credentials)
   sh =gc.open_by_url('%s'%spreadSheet)
   wksheet = sh.worksheet(sheetName)
   foo=1
   while foo==1:
      try:
         time.sleep(3)
         wksheet.update_acell('%s''%d'%(columnInfo,bugRow),bugStatus)
         time.sleep(3)
         wksheet.update_acell('%s''%d'%(chr(ord(columnInfo)+1),bugRow),swatString)
         time.sleep(3)
      except Exception as e:
         print "Exception while trying to Update the status"
         print e
         print "Sleeping 15 Seconds and Retyring"
         time.sleep(15)
         continue
      else:
         time.sleep(1)
         print "\tUpdate complete"
         foo=2

def getBugId():
   foo=1
   while foo==1:
      try:
         scope = ['https://spreadsheets.google.com/feeds']
         credentials = ServiceAccountCredentials.from_json_keyfile_name('json_gspread_auth_key.json',scope)
         gc = gspread.authorize(credentials)
         sh = gc.open_by_url('%s'%spreadSheet)
         wksheet = sh.worksheet(sheetName)
         bugId = wksheet.acell('%s''%d'%(bugCol,bugRow)).value
      except Exception as e:
         print "Exception while trying to get BugID"
         print "Sleeping 15 Seconds and Retyring"
         time.sleep(15)
         continue
      else:
          print "\n---------------------"
          print 'Checking BUG : %s'%bugId
          foo=2
   return bugId

while bugRow<rowFinalValue:
   bugId = getBugId()
   bugCountTotal=bugCountTotal+1
   cmd=cmd +' '+ bugId
   foo=1
   while foo==1:
      try:
         status,bugCheck = commands.getstatusoutput(cmd)
      except Exception as e:
         print "\tException while trying to run wheresMyFix tool"
         print "Sleeping 15 Seconds and Retyring"
         time.sleep(15)
         continue
      else:
         print "\tSuccessfully retrieved Bug status"
         foo=2

   if stringBugFixed in bugCheck:
      #print "\n---------------------"
      print '\tThis bug is Resolved and Fixed in '+release
      print '\tUpdating status for Bug ID : %s' %bugId
      bugData='Fixed'
      mString='.*Conclusion\s+:\s+Fixed\sin\s' + release + '.*'
      matchString = re.search(mString,bugCheck)
      bugInfo= matchString.group()
      updateCell(columnInfo,bugCol,bugId,bugData,bugInfo)
      bugCountFixed=bugCountFixed+1
      time.sleep(1)
   #elif bugCheck.find (failString)== -1:

   elif stringBugNotResolved in bugCheck:
      #print "\n---------------------"
      print '\tThis bug is NOT Resolved'
      print '\tUpdating status for Bug ID : %s' %bugId
      bugData='Not Fixed'
      updateCell(columnInfo,bugCol,bugId,bugData,stringBugNotResolved)
      bugCountNotResolved=bugCountNotResolved+1
      time.sleep(1)

   elif stringBugNotFixed in bugCheck:
      #print "\n---------------------"
      print '\tThis bug is NOT Fixed'
      print '\tUpdating status for Bug ID : %s' %bugId
      bugData='Not Fixed'
      updateCell(columnInfo,bugCol,bugId,bugData,stringBugNotFixed)
      bugCountNotFixed=bugCountNotFixed+1
      time.sleep(1)

   elif stringNoChangeList in bugCheck:
      #print "\n---------------------"
      print '\tThis bug has NO Change List'
      print '\tUpdating status for Bug ID : %s' %bugId
      bugData='Not Fixed'
      updateCell(columnInfo,bugCol,bugId,bugData,stringNoChangeList)
      time.sleep(1)

   elif stringError in bugCheck:
      #print "\n---------------------"
      print '\tError: Unable to fetch data'
      print '\tUpdating status for Bug ID : %s' %bugId
      bugData = 'Error'
      updateCell(columnInfo,bugCol,bugId,bugData,stringError)
      bugCountError=bugCountError+1
      time.sleep(1)


   bugRow   = bugRow+1
   bugId    = ''
   bugData  = ''
   cmd      = 'wheresMyFix.py -p' + ' '+release
   bugCheck = ''

print"\n\n"
print"************SUMMARY****************"
print "Total Bugs in the sheet\t\t\t: %d"%bugCountTotal
print "Total Bugs Fixed in " + release + "\t: %d"%bugCountFixed
print "Total Bugs Not Fixed in " + release + "\t: %d"%bugCountNotFixed
print "Bugs Not Resolved\t\t\t: %d"%bugCountNotResolved
print "Bugs that Errored out\t\t\t: %d"%bugCountError
print '\nPlease check the spreadsheet'
print"***********************************"
