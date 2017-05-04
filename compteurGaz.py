#!/home/pi/pyj.venv/bin/python
# -*- coding: utf-8 -*-

# Script de relève de mesure du capteur QTR-1RC (https://www.pololu.com/product/2459) 
# branché sur une raspberry pi 3, alim 5V, Masse et GPIO
# by D3ei 05-2017
#
# Raspberry Pi Python Code for QTR-1RC IR Sensor
# Thanks to tobyonline copyleft 2016 robot-resource.blogspot.com http://tobyonline.co.uk

import logging
from logging.handlers import RotatingFileHandler
import json
import requests
import urllib
import RPi.GPIO as GPIO
import time
import ConfigParser

#
# Configuration
#
config = ConfigParser.RawConfigParser()
config.read("/home/pi/pyj/compteurGaz.cfg")
#
#
#

domoticz_ip = config.get("domoticz", "domoticz_ip")
domoticz_port = config.getint("domoticz", "domoticz_port")
counter_idx = config.getint("domoticz", "counter_idx")
switch_idx = config.getint("domoticz", "switch_idx")
IRPIN = config.getint("capteur", "IRPIN")
HIGH_LEVEL = config.getfloat("capteur", "HIGH_LEVEL")
LOW_LEVEL = config.getfloat("capteur", "LOW_LEVEL")
VOLUME_INC = config.getfloat("script", "VOLUME_INC")
TIME_INTERVAL = config.getfloat("script", "TIME_INTERVAL")
DEBUG = config.getboolean("script", "DEBUG")
SCRIPT_PATH = config.get("script", "SCRIPT_PATH")
SCRIPT_NAME = config.get("script", "SCRIPT_NAME")

# Logger
formatLog = logging.Formatter("%(asctime)s -- %(name)s -- %(levelname)s -- %(message)s")
handlerLog = logging.handlers.RotatingFileHandler(SCRIPT_PATH + SCRIPT_NAME + ".log", mode="a", maxBytes= 1000000, backupCount= 3,encoding="utf-8")
handlerLog.setFormatter(formatLog)
loggerJ = logging.getLogger(SCRIPT_NAME)
loggerJ.addHandler(handlerLog)
if DEBUG:
    loggerJ.setLevel(logging.DEBUG)
else:
    loggerJ.setLevel(logging.INFO)

loggerJ.info(SCRIPT_NAME + ' Started !!! ' + SCRIPT_PATH + SCRIPT_NAME + '.py')
loggerJ.debug('--------- DEBUG MODE STARTED ---------')

IsFrontHigh = False
FrontOnNb = 0
FrontOffNb = 0
GPIO.setmode(GPIO.BCM)

def IRSensor():
    global IsFrontHigh
    global FrontOnNb
    global FrontOffNb
    GPIO.setup(IRPIN, GPIO.OUT)
    GPIO.output(IRPIN, GPIO.HIGH)
    time.sleep(0.00001) # charge du noeud de sortie 
    pulse_end = 0
    pulse_start = time.time() # demare le chrono
    GPIO.setup(IRPIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # relie l'entrée à la résistance de pull down 0v
    while GPIO.input(IRPIN)> 0:
        pass # attente de la charge à travers la photoresistance
    if  GPIO.input(IRPIN)<=0:
        pulse_end = time.time() # inf ou egal a 0 on mesure le temps

    # aucune idée du pourquoi mais par moment le 0 input ne passe pas et pulse_end non initialise
    if pulse_end != 0:
        pulse_duration = pulse_end - pulse_start
        loggerJ.debug("duration: %s" % pulse_duration) # pour regler la sensibilite
        # Durée supérieure au niveau haut
        if pulse_duration > HIGH_LEVEL:
            loggerJ.debug("%s-->ON" % time.time())
            FrontOffNb = 0
            # on ne détecte que les changements de niveau bas à niveau haut
            if IsFrontHigh == True:
                # Enfin, j'ai noté avec mon capteur des passages au niveau haut isolés et sans lien avec la réflexion sur la partie miroir de la roue.
                # Je me retrouvais donc avec des unités en plus.
                # Pour prendre en compte ce problème je vérifie deux valeurs hautes successives avant de rajouter une unité
                if FrontOnNb == 1:
                    # ajoute une unité au compteur
                    requete='http://'+domoticz_ip+':'+str(domoticz_port)+'/json.htm?type=command&param=udevice&idx='+str(counter_idx)+'&svalue='+str(VOLUME_INC)
                    urllib.urlopen(requete)
                    # change l'état de l'interrupteur
                    requete='http://'+domoticz_ip+':'+str(domoticz_port)+'/json.htm?type=command&param=switchlight&idx='+str(switch_idx)+'&switchcmd=On&level=0'
                    urllib.urlopen(requete)
                    IsFrontHigh = False
                    loggerJ.info("%s : 1 Unite" % time.ctime())
                else:
                    FrontOnNb = 1
        # Durée inférieure au niveau bas
        elif pulse_duration < LOW_LEVEL:
            loggerJ.debug("%s-->OFF" % time.time())
            FrontOnNb = 0
            if IsFrontHigh == False:
                if FrontOffNb == 1:
                    # change l'état de l'interrupteur
                    requete='http://'+domoticz_ip+':'+str(domoticz_port)+'/json.htm?type=command&param=switchlight&idx='+str(switch_idx)+'&switchcmd=Off&level=0'
                    urllib.urlopen(requete)
                    IsFrontHigh = True
                else:
                    FrontOffNb = 1
    return 0

if __name__ == "__main__":
    try:
        while True:
            IRSensor()
            time.sleep(TIME_INTERVAL)
    except KeyboardInterrupt:
        loggerJ.info(SCRIPT_NAME + ' Stopped !!!')
    except:
        loggerJ.critical(SCRIPT_NAME + ' Stopped no idea why !!!')
        raise
    finally:
        GPIO.cleanup(IRPIN) # on nettoie la GPIO
