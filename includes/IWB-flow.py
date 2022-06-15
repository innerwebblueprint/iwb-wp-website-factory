#!/usr/bin/python3

## IWB-flow.py
# This script is embedded inside the docker image:
# iwbp/iwbwpwebsitefactory
# It's purpose is to perform operations inside the container at boot time
# It only runs once at boot time, initiated by supervisord
# See includes/supervisord.conf in the repository

import os
import os.path
from pydoc import text
import time
import xml.etree.ElementTree as ET
import re

## 
# This is leftover - factored out - but I may re-include it later
##
