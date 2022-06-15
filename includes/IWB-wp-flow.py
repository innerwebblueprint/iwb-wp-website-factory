#!/usr/bin/python3
#####

## IWB-wp-flow.py
# This script is embedded inside the docker image:
# iwbp/iwbwpwebsitefactory
# This program expects 2 arguments: [dataSet] [interval]
# dataSet = db | html
# interval = hourly | daily | weekly | monthly | yearly
# This program is called by wordpress wp-cron configured by the IWB WP Flow plugin
# to process backups for the site on schedules defined by the plugin. 

#####
import os
import sys
import subprocess
from subprocess import check_output
import datetime
from datetime import datetime, timedelta

# asigning command line arguments
try:
    iwbDataset = str(sys.argv[1]);
except IndexError:
    print('Setting iwbDataset to default db') 
    iwbDataset = 'db'

try:
    iwbInterval = str(sys.argv[2]);
except IndexError:
    print('no interval argument')
    print('Setting iwbInterval to default hourly') 
    iwbInterval = 'hourly'

# Get enviornment variables
domainName = os.environ.get('DOMAIN_NAME')
storjBackupBucket = os.environ.get('STORJ_WPOPS_BUCKET')
storjAccessGrant = os.environ.get('STORJ_GRANT')

iwbDBDailyRetention = os.environ.get('IWB_DAILY_DB_RETENTION')
iwbDBWeeklyRetention = os.environ.get('IWB_WEEKLY_DB_RETENTION')
iwbDBMonthlyRetention = os.environ.get('IWB_MONTHLY_DB_RETENTION')
iwbDBYearlyRetention = os.environ.get('IWB_YEARLY_DB_RETENTION')

iwbHtmlDailyRetention = os.environ.get('IWB_DAILY_HTML_RETENTION')
iwbHtmlWeeklyRetention = os.environ.get('IWB_WEEKLY_HTML_RETENTION')
iwbHtmlMonthlyRetention = os.environ.get('IWB_MONTHLY_HTML_RETENTION')
iwbHtmlYearlyRetention = os.environ.get('IWB_YEARLY_HTML_RETENTION')

## Variable Declarations
exportPath = '/var/www/tmp/' + str(iwbDataset) + '/'
storjConfigPath = '/var/storj/'

## Set some sensible default retention settings 
#  in case none are provided
# DB dataset
if iwbDBDailyRetention == None: iwbDBDailyRetention = 7 # in days
if iwbDBWeeklyRetention == None: iwbDBWeeklyRetention = 28 # 4 weeks in days 4*7=28(keep 4 weeklys)
if iwbDBMonthlyRetention == None: iwbDBMonthlyRetention = 360 # 12m in days 30*12=360 (keep 12 monthlys)
if iwbDBYearlyRetention == None: iwbDBYearlyRetention = 3650 # in days (keep 20 yearlys)
# HTML dataset (web root)
if iwbHtmlDailyRetention == None: iwbHtmlDailyRetention = 3 #keep x daily archives
if iwbHtmlWeeklyRetention == None: iwbHtmlWeeklyRetention = 2 #keep x weekly archives
if iwbHtmlMonthlyRetention == None: iwbHtmlMonthlyRetention = 3 #keep x weekly archives
if iwbHtmlYearlyRetention == None: iwbHtmlYearlyRetention = 1 #keep x weekly archives


## Function Definitions

## iwbCheck (iwbDataset, iwbInterval)
#   Check that we have both a dataset and interval to work wtih
#
def iwbCheck (iwbDataset,iwbInterval):
    if iwbInterval != "":
        sys.stdout.write('Processing ' + str(iwbInterval) +'\n')    
    else:
        sys.exit("Plese provie an interval as a command line argument")
    
    if iwbDataset != "":
        sys.stdout.write('Processing ' + str(iwbDataset) +'\n')    
    else:
        sys.exit("Plese provie dataset as a command line argument")

## export_wp_dataset (exportFileName):
#   Export wordpress database and save to exportFileName
#
def export_wp_dataset (exportFileName):
    sys.stdout.write('Exporting ' + str(domainName) + ' wp database\n\n')
    #
    export_db = subprocess.run(["wp", "--allow-root", "--path=/var/www/html", "db", "export", str(exportPath)+str(exportFileName) ])
    return
    #wp --allow-root --path='/var/www/html/' db export /var/www/db/www.innerwebblueprint.com-wpdb.sql
    #wp --allow-root --path='/var/www/html/' plugin list

## iwb_backup_process (iwbDataset, iwbInterval):
#   
#
def iwb_backup_process (iwbDataset, iwbInterval):
    now = datetime.now()
    intervalHour = '{:02d}'.format(now.hour)
    intervalDay = '{:02d}'.format(now.day)
    intervalMonth = '{:02d}'.format(now.month)
    intervalYear = '{:02d}'.format(now.year)
    if iwbDataset == 'db':
        if iwbInterval == 'hourly':
            sys.stdout.write('\n\nStarting IWB ' + str(iwbInterval) + ' ' + str(iwbDataset) + ' backup process\n')
            #
            # Let's start by exporting this as the 'latest'
            exportFileName = str(domainName) + '_wp_' + str(iwbDataset) + '_latest.sql'
            export_wp_dataset(exportFileName)
            # Set some file names for the interval
            hourly_FileName = str(domainName) + '_wp_' + str(iwbDataset) + '_' + str(intervalHour) +'.sql'
            # Make a copy to save as hourly
            copy_export_db = subprocess.run(["cp", str(exportPath)+str(exportFileName), str(exportPath)+str(hourly_FileName)])
            # upload both files
            storj_upload(exportFileName)
            storj_upload(hourly_FileName)
            #
            return "hourly processing compelted"
        else: 
            # I should define all the options here - I'll just catch for now
            # this should run fine no matter what interval is supplied
            sys.stdout.write('\n\nStarting IWB ' + str(iwbInterval) + ' ' + str(iwbDataset) + ' backup process\n')
            #
            exportFileName = str(domainName) + '_wp_' + str(iwbDataset) + '_' + str(intervalYear) + '_' + str(intervalMonth) + '_' + str(intervalDay) +'.sql'
            #
            export_wp_dataset(exportFileName)
            storj_upload(exportFileName)
            #
            sys.stdout.write(str(iwbInterval) + ' processing complete.\n')
            #
    elif iwbDataset == 'html':
        if iwbInterval == 'daily':
            sys.stdout.write('\n\nStarting IWB ' + str(iwbInterval) + ' ' + str(iwbDataset) + ' backup process\n')
            #
            # Let's start by exporting this as the 'latest'
            # Set file name
            exportFileName = str(domainName) + '_wp_' + str(iwbDataset) + '_latest.tar'
            #
            export_file = subprocess.run(['tar', '-cf', str(exportPath) + str(exportFileName), '-C', '/var/www/html', '.'])
            # tar -cf test.tar -C /var/www/html .
            #
            # Set some file names for the interval
            dailyFileName = str(domainName) + '_wp_' + str(iwbDataset) + '_' + str(intervalDay) +'.tar'
            # Make a copy to save as hourly
            copy_export_db = subprocess.run(["cp", str(exportPath)+str(exportFileName), str(exportPath)+str(dailyFileName)])
            
            # upload both files
            storj_upload(exportFileName)
            storj_upload(dailyFileName)
            # Run the cleanup routine to remove files outside of retention
            storj_cleanup()
            #
            sys.stdout.write('Processing Complete \n')
            #
        else:
            ## non daily (no latest)
            sys.stdout.write('\n\nStarting IWB ' + str(iwbInterval) + ' ' + str(iwbDataset) + ' backup process\n')
            #
            exportFileName = str(domainName) + '_wp_' + str(iwbDataset) + '_' + str(intervalYear) + '_' + str(intervalMonth) + '_' + str(intervalDay) +'.tar'
            #
            export_file = subprocess.run(['tar', '-cf', str(exportPath) + str(exportFileName), '-C', '/var/www/html', '.'])

            #export_file = subprocess.run(["tar", "-cf", str(exportPath) + str(exportFileName), "/var/www/html/"])

            # Upload the file
            storj_upload(exportFileName)
            #
            sys.stdout.write(str(iwbInterval) + ' processing complete.\n')
            #
    else:
        sys.stdout.write('No dataset provided?')

## 
#  storj_upload (exportFileName): 
#
def storj_upload (exportFileName):
    localFileName = str(exportPath) + exportFileName
    # Compress File
    sys.stdout.write('Compressing ' + str(localFileName) + '\n\n')
    compress_file = subprocess.run(["gzip", "-f", str(localFileName)])
    localFileName = localFileName + '.gz'
    exportFileName = exportFileName + '.gz'
    # Upload to Storj
    storjObKey = 'sj://' + str(storjBackupBucket) + '/' + str(iwbDataset) + '/' + str(iwbInterval) + '/' + str(exportFileName)
    sys.stdout.write('Writing to distributed storage: ' + str(storjObKey) +'\n\n')
    file_upload = subprocess.run(["uplink", "cp", "--config-dir", str(storjConfigPath), "--access", str(storjAccessGrant),  str(localFileName), str(storjObKey)])
    # Delete local file
    iwb_delete_file = subprocess.run(["rm", str(localFileName)])

## 
#   storj_delete (storjObKey):
#
def storj_delete (storjObKey):
    storjDelete = subprocess.run(["uplink", "rm", "--config-dir", str(storjConfigPath), "--access", str(storjAccessGrant), str(storjObKey)])
    #sys.stdout.write('Deleted ' + str(storjObKey) + '\n')

## 
#   storj_file_processing(fileList,retention,cleanupDataset,cleanupInterval):
#
def storj_file_processing(fileList,retention,cleanupDataset,cleanupInterval):
    # monkies like to dance
    # Storj is not a real file system here, so we need to parse the ls to work with it.
    line = fileList.splitlines()
    for i in line:
        var = i.decode('utf-8')
        var = list(filter(None, var.split('  ')))
        if var[0]=='OBJ':
            datetime_object = datetime.strptime(var[1], ' %Y-%m-%d %H:%M:%S')
            first_time = datetime.now()
            elapsedTime = datetime_object - first_time
            #
            storjPath = 'sj://' + str(storjBackupBucket) +'/'  + str(cleanupDataset) + '/' + str(cleanupInterval)
            storjObjKey = str(storjPath) + '/' + str(var[3])
            #
            sys.stdout.write('Checking file ' + str(storjObjKey) + '\n')
            #
            retention = int(retention)
            if abs(elapsedTime.days) > retention:
                print('Deleting old file: ' + str(storjObjKey))
                storj_delete(storjObjKey)

## 
#   storj_retention_check (cleanupDataset,cleanupInterval):
#
def storj_retention_check (cleanupDataset,cleanupInterval):
    sys.stdout.write('... Processing ' + str(cleanupDataset) + ' Files\n')
    print('Checking intervals: ' + str(cleanupInterval) + '\n')
    #
    for loopInterval in cleanupInterval:
        if cleanupDataset == 'db':
            print('Checking ' + str(cleanupDataset) + ' Dataset')
            if loopInterval == 'daily':
                print('checking: '+ str(loopInterval))
                retention = iwbDBDailyRetention
            if loopInterval == 'weekly':
                print('checking: '+ str(loopInterval))
                retention = iwbDBWeeklyRetention
            if loopInterval == 'monthly':
                print('checking: '+ str(loopInterval))
                retention = iwbDBMonthlyRetention
            if loopInterval == 'yearly':
                print('checking: '+ str(loopInterval))
                retention = iwbDBYearlyRetention
        elif cleanupDataset == 'html':
            print('Checking ' + str(cleanupDataset) + ' Dataset')
            if loopInterval == 'daily':
                print('checking: '+ str(loopInterval))
                retention = iwbHtmlDailyRetention
            if loopInterval == 'weekly':
                print('checking: '+ str(loopInterval))
                retention = iwbHtmlWeeklyRetention
            if loopInterval == 'monthly':
                print('checking: '+ str(loopInterval))
                retention = iwbHtmlMonthlyRetention
            if loopInterval == 'yearly':
                print('checking: '+ str(loopInterval))
                retention = iwbHtmlYearlyRetention
        #
        storjPath = 'sj://' + str(storjBackupBucket) + '/' + str(cleanupDataset) +'/' + str(loopInterval) + '/'
        fileList = check_output(["uplink","ls", "--config-dir", str(storjConfigPath), "--access", str(storjAccessGrant), str(storjPath)])
        #
        storj_file_processing(fileList,retention,cleanupDataset,loopInterval)
    sys.stdout.write('End of dataset \n\n')
    return

## 
#   storj_cleanup ():
#
def storj_cleanup ():
    sys.stdout.write('\nRunning storj cleanup\n')
    checkIntervals = 'daily','weekly','monthly','yearly'
    #
    storj_retention_check('db',checkIntervals)
    storj_retention_check('html',checkIntervals)
    sys.stdout.write('Clean up completed\n')
    #

#iwbCheck (iwbDataset,iwbInterval)
iwb_backup_process (iwbDataset,iwbInterval)
