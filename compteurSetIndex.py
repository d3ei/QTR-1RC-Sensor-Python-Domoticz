#!/home/pi/pyj.venv/bin/python
# -*- coding: utf-8 -*-

# Mise à jour compteur Domoticz
# by D3ei 05-2017

import json
import requests
import urllib

# Parametres Domoticz
domoticz_ip="192.168.1.40"
domoticz_port="8080"

counter_diff = input("Entrez le nombre de litres à ajouter ou enlever (- devant ;)) à votre index Domoticz pour égaler l'index réel de votre compteur : ")
counter_idx = input("Numéro du compteur (58 = eau, 89 = gaz) : ")

print "Il faut ajouter "+str(float(counter_diff) / 10)+" unité(s)."

requete='http://'+domoticz_ip+':'+domoticz_port+'/json.htm?type=command&param=udevice&idx='+str(counter_idx)+'&svalue='+str(float(counter_diff) / 10)
urllib.urlopen(requete)
