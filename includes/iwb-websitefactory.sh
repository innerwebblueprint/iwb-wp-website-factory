#!/bin/bash

## iwb-websitefactory.sh
# This script is embedded inside the docker image:
# iwbp/iwbwpwebsitefactory
# It's purpose is to perform internal operations at container start.
# It only runs once at boot time, initiated by supervisord.
# Enviornment variables are set with a docker compose file.
# See includes/supervisord.conf in the repository.

## A brief overview of what this startup script does:
# Downloads from Storj, the latest backup html files to web root 
# Downloads from Storj, latest wp db and imports into the database

echo 'Initializing IWB enviormnet'

## Static String Variables
downloadPath='/var/download'
extractPath='/var/download/extract'
webRootPath='/var/www/html'
## Enviornment dependent variables
datasetHtmlOverwrite=${DATASET_HTML_OVERWRITE}
datasetDbOverwrite=${DATASET_DB_OVERWRITE}
datasetDbImport=${DATASET_DB_IMPORT}
ServerName=${DOMAIN_NAME}
domainName=${DOMAIN_NAME}
htmlLatestFileName=$domainName"_wp_html_latest.tar.gz"
dbLatestFileName=$domainName"_wp_db_latest.sql.gz"
dbLatestImportName=$domainName"_wp_db_latest.sql"
storjBucket=${STORJ_WPOPS_BUCKET}
storjAccessGrant=${STORJ_GRANT}
storjConfigPath='/var/storj/'
storjConfigFilename=$storjConfigPath"config.ini"
storjHtmlPath="sj://"$storjBucket"/html/daily/"
storjDbPath="sj://"$storjBucket"/db/hourly/"
storjHtmlObj=$storjHtmlPath$htmlLatestFileName
storjdbObj=$storjDbPath$dbLatestFileName

# Create the extract path if it doesn't exist
if [ ! -d $extractPath ]; then
    mkdir -p $extractPath &&
    chown -R www-data:www-data $extractPath &&
    echo 'Creating extraction directory'
fi

# Setup storj uplink credentials from enviornment variable
# Create storj config directory if it doesn't exist
if [ ! -d $storjConfigPath ]; then
    mkdir -p $storjConfigPath &&
    echo '[metrics]\n addr =' > $storjConfigFilename &&
    chown -R www-data:www-data $storjConfigPath &&
    echo 'Creating Storj config directory'
fi

## To-Do: 
## Verify Storj Connectivity

##  Download site html backup archive from Storj
##  if this fails... likely because of a first install...
##  we check later and download wordpress.

## Check for $datasetHtmlOverwrite directive.
## If NOT set to 'nooverwrite' we download the latest backup of the sites files
## from Storj. (gotta love the double negatives LOL)
if [ $datasetHtmlOverwrite != 'nooverwrite']; then
    echo 'Attempting download: '$storjHtmlObj
    echo 'This may take a moment depending on archive size and available bandiwidth...'

    ## Attempt to download
    uplink cp --config-dir $storjConfigPath --access $storjAccessGrant $storjHtmlObj $downloadPath || echo 'Download failed... will attempt fresh wordpress install'

    if [ -f $downloadPath/$htmlLatestFileName ];
        then
            echo "$htmlLatestFileName found"
            echo 'Download complete...'
            ## Extract to correct location 
            echo '     '
            echo 'Extracting : '$downloadPath/$htmlLatestFileName' To: '$extractPath
            tar -xf $downloadPath/$htmlLatestFileName -C $extractPath &&
            echo 'Extraction complete...'
            ## Copy files to the correct location 
            ## I'll delete them later on during cleanup
            echo 'Relocating files to web root'
            cp -r $extractPath/. $webRootPath &&
            #cp -r $extractPath/* $webRootPath &&
            echo "Files relocated..."
        else
            echo "$htmlLatestFileName not found."
            echo "Attempting fresh wordpress install"
            echo "Downloading wp now"
            wp --path='/var/www/html/' --allow-root core download &&
            echo "WP downloaded..."
    fi

    # Setting up wp-config file for wordpress
    echo 'Setting up wp-config file for wordpress'
    wpConfigFile="/var/www/html/wp-config.php"
    echo "Checking for $wpConfigFile"
    if [ -f "$wpConfigFile" ];
        then
            echo "$wpConfigFile found"
        else
            echo "$wpConfigFile NOT found..."
            echo "Copy wordpress config env version into place"
            cp /usr/src/wordpress/wp-config-docker.php /var/www/html/wp-config.php &&
            echo "Config file copied"
    fi
fi

## @todo - make this conditional on $datasetDbOverwrite = overwrite
## actually make overwrite the default, and nooverwrite skip

# Download latest db backup file
echo 'Downloading: ' $storjdbObj
uplink cp --config-dir $storjConfigPath --access $storjAccessGrant $storjdbObj $downloadPath &&

# Extract file
echo 'Extracting: ' $storjdbObj
gunzip -f $downloadPath/$dbLatestFileName &&
echo 'Extracting complete. ' $storjdbObj

## Now import the database if there is one
echo "Checking for database file $dbLatestFileName"

if [ -f $downloadPath/$dbLatestImportName ];
    then
        echo "$dbLatestImportName found"
        echo "Importing wp db from backup"
        wp --path='/var/www/html/' db import --allow-root $downloadPath/$dbLatestImportName &&
        echo "Database imported..."
    else
        echo "$dbFile not found."
        echo "You will need to install wordpress"
        ## To-Do: 
        ## Auto install wordpress with supplied enviornmnet variables
fi

echo "Cleaning up working files..."
rm -rf $downloadPath/* &&
# rm -rf /var/download/* &&
echo "Cleanup complete..."

# Create tmp directories for auto backups
echo "Creating tmp directoryies for archives..."
mkdir -p /var/www/tmp/db
mkdir -p /var/www/tmp/html

echo "correcting permissions..."
chown -R www-data:www-data /var/www/ &&

# Now I need to setup a system cron job to call wp-cron
echo "Setting up cron job entry"
# Setup a call to wp-cron on a 5 minute schedule
echo "*/5 * * * * curl http://localhost/wp-cron.php" >> /var/tmp/mycron
crontab /var/tmp/mycron &&
rm /var/tmp/mycron &&
echo "Shuffling Wordpress Salts"
wp --path='/var/www/html/' --allow-root config shuffle-salts

## To-Do: 
## Check for IWB Website Factory iwb-website-factory wordpress plugin
## Install if it's not installed.

echo "Your website should now work"
