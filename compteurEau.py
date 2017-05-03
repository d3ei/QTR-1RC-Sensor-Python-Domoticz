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

#
# Vos paramètres
#
domoticz_ip="192.168.1.40"
domoticz_port="8080"
dummy_idx={'counter': 58, 'switch':57} # les numéros de devices attribués par Domoticz: un compteur incrémental pour la conso et un interrupteur virtuel pour le détail
IRPIN = 17 # branché sur la GPIO17
HIGH_LEVEL = 0.00022 # niveau de declenchement haut
LOW_LEVEL = 0.00019 # niveau de declenchement bas entre haut et bas il ne se passe rien :/
VOLUME_INC = 0.1 # 1 = 10 litres, allez demander à Domoticz pourquoi ;)
TIME_INTERVAL = 0.3 # temps entre deux interrogations du capteur, dépend de la vitesse de la roue du compteur
DEBUG = True # Log plus ou moins d'infos, utile pour régler les niveaux haut et bas
SCRIPT_PATH = '/home/pi/pyj/' # chemin de votre script
SCRIPT_NAME = 'compteurEau' # nom de votre script sans l'extension .py
#
#
#

# Logger
formatter_info = logging.Formatter("%(asctime)s -- %(name)s -- %(levelname)s -- %(message)s")
logger_info = logging.getLogger("info_log")
handler_info = logging.handlers.RotatingFileHandler(SCRIPT_PATH + SCRIPT_NAME + "-info.log", mode="a", maxBytes= 1000000, backupCount= 3,encoding="utf-8")
handler_info.setFormatter(formatter_info)
logger_info.setLevel(logging.INFO)
logger_info.addHandler(handler_info)

logger_info.info(SCRIPT_NAME + ' Started !!! ' + SCRIPT_PATH + SCRIPT_NAME + '.py')

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
        if DEBUG:
            logger_info.info("duration: %s" % pulse_duration) # pour regler la sensibilite
        # Durée supérieure au niveau haut
        if pulse_duration > HIGH_LEVEL:
            if DEBUG:
                logger_info.info("%s-->ON" % time.time())
            FrontOffNb = 0
            # on ne détecte que les changements de niveau bas à niveau haut
            if IsFrontHigh == True:
                # Enfin, j'ai noté avec mon capteur des passages au niveau haut isolés et sans lien avec la réflexion sur la partie miroir de la roue.
                # Je me retrouvais donc avec des unités en plus.
                # Pour prendre en compte ce problème je vérifie deux valeurs hautes successives avant de rajouter une unité
                if FrontOnNb == 1:
                    # ajoute une unité au compteur
                    requete='http://'+domoticz_ip+':'+domoticz_port+'/json.htm?type=command&param=udevice&idx='+str(dummy_idx['counter'])+'&svalue='+str(VOLUME_INC)
                    urllib.urlopen(requete)
                    # change l'état de l'interrupteur
                    requete='http://'+domoticz_ip+':'+domoticz_port+'/json.htm?type=command&param=switchlight&idx='+str(dummy_idx['switch'])+'&switchcmd=On&level=0'
                    urllib.urlopen(requete)
                    IsFrontHigh = False
                    logger_info.info("%s : 1 Unite" % time.ctime())
                else:
                    FrontOnNb = 1
        # Durée inférieure au niveau bas
        elif pulse_duration < LOW_LEVEL:
            if DEBUG:
                logger_info.info("%s-->OFF" % time.time())
            FrontOnNb = 0
            if IsFrontHigh == False:
                if FrontOffNb == 1:
                    # change l'état de l'interrupteur
                    requete='http://'+domoticz_ip+':'+domoticz_port+'/json.htm?type=command&param=switchlight&idx='+str(dummy_idx['switch'])+'&switchcmd=Off&level=0'
                    urllib.urlopen(requete)
                    IsFrontHigh = True
                else:
                    FrontOffNb = 1
    return 0

if __name__ == '__main__':
    try:
        while True:
            IRSensor()
            time.sleep(TIME_INTERVAL)
    except KeyboardInterrupt:
        logger_info.info(SCRIPT_NAME + ' Stopped !!!')
    except:
        logger_info.info(SCRIPT_NAME + ' Stopped no idea why !!!')
        raise
    finally:
        GPIO.cleanup(IRPIN) # on nettoie la GPIO
