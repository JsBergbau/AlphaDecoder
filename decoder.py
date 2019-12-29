#!/usr/bin/python3
#Version 1.0beta 30.12.2019
import re
from time import sleep
import sys
from subprocess import Popen, PIPE
import fileinput

#nur 4 Byte Strings
def toInt(s):
	vorne=s[:2]
	hinten=s[-2:]
	gedreht=hinten + vorne
	return int(gedreht,16)
	
Pumpenmodus = dict()
Pumpenmodus['00'] = "Konstantdrehzahl Stufe 3"
Pumpenmodus['01'] = "Konstantdrehzahl Stufe 2"
Pumpenmodus['02'] = "Konstantdrehzahl Stufe 1"
Pumpenmodus['03'] = "Autoadapt"
Pumpenmodus['04'] = "Proportionaldruck Stufe 1"
Pumpenmodus['05'] = "Proportionaldruck Stufe 2"
Pumpenmodus['06'] = "Proportionaldruck Stufe 3"
Pumpenmodus['07'] = "Konstantdifferenzdruck Stufe 1"
Pumpenmodus['08'] = "Konstantdifferenzdruck Stufe 2"
Pumpenmodus['09'] = "Konstantdifferenzdruck Stufe 3"	

def getPumpenmodus(s):
	if s in Pumpenmodus:
		return Pumpenmodus[s]
	else:
		return "Unbekannter Pumpenmodus"
	
def verarbeiteDatenpaket(datenpaket):
	#print(datenpaket)
	
	regex=re.compile("(>.*)[\r\n][ ](.*)")		
	datenpaket=regex.sub(r'\1\2',datenpaket)
	datenpaket=regex.sub(r'\1\2',datenpaket)
	datenpaket=re.sub(r'>|[ ]','',datenpaket)
	#Ab hier haben wir die Daten Zeile für Zeile
	
	datenpaket=datenpaket.rstrip()
	
	#print(datenpaket)
	if re.match(r'[A-F0-9]{32}4D493430',datenpaket):#prüfen ob wir Daten eines Alpha Readers empfangen
		if re.match(r'[A-F0-9]{48}F0',datenpaket):
			print ("Alpha Reader ist ein, bitte auf die Pumpe setzen oder Alpha Reader Modus durch langes Drücken der rechten Taste an der Pumpe aktivieren")
			batteriestatusindikator=re.search(r'(?<=[A-F0-9]{52})([A-F0-9]{2})',datenpaket).group(0)
			print("Batteriestatusindikator: " + batteriestatusindikator + "\n")
		elif re.match(r'[A-F0-9]{48}F2',datenpaket): #prüfen ob wir auch das richtige Paket haben
			sequenznummer=re.search(r'(?<=[A-F0-9]{54})([A-F0-9]{2})',datenpaket).group(0)
			if(sequenznummer != verarbeiteDatenpaket.sequenznummerVorher):
				verarbeiteDatenpaket.sequenznummerVorher=sequenznummer
				signalstärke=re.search(r'[A-F0-9]{2}$',datenpaket).group(0)
				signalstärke=int(signalstärke,16)-256
				datenprotokollversion=re.search(r'(?<=[A-F0-9]{52})([A-F0-9]{2})',datenpaket).group(0)
				batteriestatusindikator=re.search(r'(?<=[A-F0-9]{56})([A-F0-9]{2})',datenpaket).group(0)
				pumpenkennung=re.search(r'(?<=[A-F0-9]{58})([A-F0-9]{4})',datenpaket).group(0)
				volumenstromHex=re.search(r'(?<=[A-F0-9]{62})([A-F0-9]{4})',datenpaket).group(0)
				volumenstrom=round(toInt(volumenstromHex) / 6.5534)
				förderhöheHex=re.search(r'(?<=[A-F0-9]{66})([A-F0-9]{4})',datenpaket).group(0)
				förderhöhe=round(toInt(förderhöheHex) / 3276.7,2)
				unbekannt1=re.search(r'(?<=[A-F0-9]{70})([A-F0-9]{2})',datenpaket).group(0)
				pumpenmodus=re.search(r'(?<=[A-F0-9]{72})([A-F0-9]{2})',datenpaket).group(0)
				temperatur=int(re.search(r'(?<=[A-F0-9]{74})([A-F0-9]{2})',datenpaket).group(0),16)
				unbekannt2=re.search(r'(?<=[A-F0-9]{76})([A-F0-9]{4})',datenpaket).group(0)
				unbekannt3=re.search(r'(?<=[A-F0-9]{80})([A-F0-9]{8})',datenpaket).group(0)
				unbekannt3=re.sub(r'([0-9A-F]{2})',r'\1 ',unbekannt3)
				werte="Volumenstrom: " + str(volumenstrom) + "\nFörderhöhe: " + str(förderhöhe)+ " Meter"\
				"\nPumpentemperatur: " + str(temperatur) + " °C" + \
				"\nBatteriestatusindikator: " + batteriestatusindikator + \
				"\nPumpenkennung: " + pumpenkennung + \
				"\nSignalstärke: " + str(signalstärke) + " dBm" + \
				"\nDatenprotokollversion: " + datenprotokollversion +  \
				"\nUnbekannt 1: " + unbekannt1 + "\nPumpenmodus: " + getPumpenmodus(pumpenmodus) + " (" + pumpenmodus + ")" + \
				"\nUnbekannt 2: " + unbekannt2 + "\nUnbekannt 3: " + unbekannt3 + "\n"
				print(werte)
				
verarbeiteDatenpaket.sequenznummerVorher="0"				

def main():
	
	skip=0
	ersteZeile=True
	datenpaket=""
	for line in fileinput.input():
		#Überspringe die ersten beiden Zeilen ohne sinnvolle Daten
		# HCI sniffer - Bluetooth packet analyzer ver 5.50
		# device: hci0 snap_len: 1500 filter: 0x2
		if(skip<2):
			skip += 1
			continue
		if ersteZeile:
			datenpaket+=line
			ersteZeile=False
			continue
		
		#Nach dieser Logik braucht es mindestens 2 Datenpakete, da die Verarbeitung des ersten erst beginnt, wenn das nächste schon eintrifft. Hier unerheblich
		if(line[0]=='>'):
			verarbeiteDatenpaket(datenpaket)
			datenpaket=line
		else:
			datenpaket+=line		
	
	
if __name__=="__main__":
	main()
