#!/home/pi/pyj.venv/bin/python
# -*- coding: utf-8 -*-

# Script de relève de mesure d'un photoresistor digital 
# branché sur une raspberry pi 3, alim 3V, Masse et GPIO
# by D3ei 05-2017
#

import logging
from logging.handlers import RotatingFileHandler
import json
import requests
import urllib
import RPi.GPIO as GPIO
import time
import ConfigParser
import sys
import os

def cb_addUnit(ch):
    requete='http://'+domoticz_ip+':'+str(domoticz_port)+'/json.htm?type=command&param=udevice&idx='+str(counter_idx)+'&svalue='+str(VOLUME_INC)
    urllib.urlopen(requete)
    loggerJ.debug('Flash detecte : une unite ajoutee ...')

if __name__ == '__main__':
    pathFull = os.path.abspath(os.path.dirname(sys.argv[0]))

    #
    # Configuration
    #
    config = ConfigParser.RawConfigParser()
    config.read(pathFull + "/compteurElec.cfg")

    domoticz_ip = config.get("domoticz", "domoticz_ip")
    domoticz_port = config.getint("domoticz", "domoticz_port")
    counter_idx = config.getint("domoticz", "counter_idx")
    IRPIN = config.getint("capteur", "IRPIN")
    VOLUME_INC = config.getfloat("script", "VOLUME_INC")
    DEBUG = config.getboolean("script", "DEBUG")
    SCRIPT_NAME = config.get("script", "SCRIPT_NAME")

    # Logger
    formatLog = logging.Formatter("%(asctime)s -- %(name)s -- %(levelname)s -- %(message)s")
    handlerLog = logging.handlers.RotatingFileHandler(pathFull + "/" + SCRIPT_NAME + ".log", mode="a", maxBytes= 1000000, backupCount= 3,encoding="utf-8")
    handlerLog.setFormatter(formatLog)
    loggerJ = logging.getLogger(SCRIPT_NAME)
    loggerJ.addHandler(handlerLog)
    if DEBUG:
        loggerJ.setLevel(logging.DEBUG)
    else:
        loggerJ.setLevel(logging.INFO)

    loggerJ.info(SCRIPT_NAME + ' Started !!! ' + pathFull + '/' + SCRIPT_NAME + '.py')
    loggerJ.debug('--------- DEBUG MODE STARTED ---------')

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(IRPIN,GPIO.IN)

    GPIO.add_event_detect(IRPIN, GPIO.FALLING, callback=cb_addUnit, bouncetime=75)

    try:
        while True:
            time.sleep(600)
    except KeyboardInterrupt:
        loggerJ.info(SCRIPT_NAME + ' Stopped !!!')
    except:
        loggerJ.critical(SCRIPT_NAME + ' Stopped no idea why !!!')
        raise
    finally:
        GPIO.remove_event_detect(IRPIN)
        GPIO.cleanup(IRPIN) # on nettoie la GPIO
