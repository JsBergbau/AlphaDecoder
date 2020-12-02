# AlphaDecoder
Dieses Programm dekodiert Daten des Grundfos Alpha Reader MI401. Eventuell funktioniert es auch bei den Grundwasser Alpha 3 Pumpen mit Bluetooth. Hier einfach mal ausprobieren. Da Alphareader ist ein kleines durch eine CR 2032 betriebenes Gerät, welches auf die Pumpe aufgesteckt wird und eigentlich zum hydraulischen Abgleich gedacht ist. Sobald das Gerät eingeschaltet wird, sendet es Bluetooth Low Energy Advertising Pakete aus. Es besteht keine Notwendigkeit und Möglichkeit mit dem Gerät koppeln. Es ist wohl ein Firmware Update möglich, erfordert aber, aus welchen Gründen auch immer, ein iPhone oder ein Android Gerät mit Bluetooth 5.0. Dieses würde die Reichweite angeblich verlängern. Die Reichweite ist auch ohne Update schon sehr groß und auch noch durch zwei Betondecken sind die Werte zu empfangen. Ein weiterer Alpha Reader lässt sich als Repeater einsetzen.

Sobald der Alpha Reader auf die Pumpe gesteckt wurde, sendet es per Bluetooth LE Advertising Report sämtliche Daten aus. Alle Pakete werden tragen einen Sequenz Nummer und werden mehrfach wiederholt. In meinen Aufzeichnungen parat Kopie waren das zwischen vier und neun Wiederholungen. Die offizielle Grundfos-App zeigt erst Werte an, wenn zwei Pakete mit unterschiedlicher Sequenznummer empfangen wurden.

Für das Reverse Engineering war sehr hilfreich die Pakete mittels folgender Befehlen aufzuzeichnen:

`1.	sudo hcitool lescan --duplicate > /dev/null &`

nur durch die --duplicate Option wird sichergestellt, dass auch alle Pakete empfangen werden, da das Gerät ja immer unter derselben Mac Adresse auftritt

`2.	sudo hcidump --raw hci`

Damit bekommt man nun die Datenpakete geliefert.
Diesen Weg verwendet auch der Decoder um die Daten zu verarbeiten.

Fürs Reverse-Engineering wurden die aufgefangen Pakete modifiziert und erneut abgeschickt. Das klappt mittels 

`sudo hcitool -i hci0 cmd 0x08 0x0009 0c 0b 09 4d 49 34 30 31`
Dies setzt den Namen auf MI401

`sudo hcitool -i hci0 cmd 0x08 0x0008 1e 06 08 4D 49 34 30 31 16 FF 14 F2 11 01 16 03 F0 24 09 0A 6B 0E ED 04 10 01 4C FF FF FF FF`
Setzt das zusendende Paket.

Mit `sudo hciconfig hci0 leadv 3` beginnt das Senden der Pakete. Bedeutet hierbei, dass das Gerät nicht verwendbar gesendet wird. Weitere Pakete bzw. geänderte Pakete können ganz einfach durch einen erneuten Aufruf von `sudo hcitool -i hci0 cmd 0x08 0x0008 [Weitere Daten]` gesendet werden. Das Senden stoppt man mit `sudo hciconfig hci0 noleadv`

Die eigentlichen Daten befinden sich ab dem 25. Byte. Die meisten Pakete haben den Typ 0xF2. Es gibt noch F0 Pakete. Diese werden gesendet wenn der Reader nicht auf der Pumpe steckt, die Pumpe aus ist oder nicht der AlphaReader-Modus durch langes Drücken der W-m³/h Taste aktiviert ist. In regelmäßigen Abständen sendet der Reader auch F1 Pakete. Diese sind ein Byte länger als die F2 Pakete. Mit diesen Paketen habe ich mich nicht weiter beschäftigt. Alle hier dekodierten Daten stecken im F1 Paket.
Es werden wesentlich mehr Daten angezeigt als die Grundfos-App liefert. Letztere liefert lediglich den Volumenstrom.

Bei einigen Werten des Pakets bin ich mir nicht genau sicher, welche Daten sie darstellen sollen. Deswegen handelt es sich ja auch nur eine Betaversion, es wird sicher noch einige Änderungen geben. Die Unterscheidung wird in Klammern mit „unsicher“ bzw. „gesichert“ angegeben.
Aufbau des Pakets. 
Wir betrachten hier nur die letzten Byte des Pakets
```
1  2  3  4  5  6   7 8  9  10 11 12 13 14 15 16 17 18 19 20 21
F2 11 01 2E 02 00 24 09 06 C4 0E 31 04 15 01 F0 99 16 61 30 E4
```

1: Pakettyp

2: Unbekannt

3: Protokollversion (unsicher)

4: Sequenznummer (gesichert)

5: Batteriestatus (unsicher)

6-7: Pumpenidentifikationsnummer (ziemlich sicher, bei einer anderen Pumpe gibt es einen anderen Wert)

8-9: Aktueller Volumenstrom als INT16 im LittleEndian-Format. Den erhaltenen Wert muss man durch 6,5534 für den Volumenstrom in l/h dividieren. (gesichert)

10-11: Aktuelle Förderhöhe, ebenfalls als INT16 im LittleEndian-Format. Der Wert wird durch 3276,7 dividiert für die aktuelle Förderhöhe in Metern. (gesichert)

12: unbekannt, könnte auch eine Art Sequenznummer sein

13: Aktueller Pumpenmodus (gesichert)
- 00 = "Konstantdrehzahl Stufe 3"
- 01 = "Konstantdrehzahl Stufe 2"
- 02 = "Konstantdrehzahl Stufe 1"
- 03 = "Autoadapt"
- 04 = "Proportionaldruck Stufe 1"
- 05 = "Proportionaldruck Stufe 2"
- 06 = "Proportionaldruck Stufe 3"
- 07 = "Konstantdifferenzdruck Stufe 1"
- 08 = "Konstantdifferenzdruck Stufe 2"
- 09 = "Konstantdifferenzdruck Stufe 3"

14: Pumpentemperatur in °C (gesichert)

15: Unbekannt, wechselt zwischen 00 und 01

16: Vermutlich auch eine Art Sequenznummer. Steigt in 4er Inkrementen an

17-20: Unbekannt

21: Signalstärke. Das ist bei jedem Bluetooth LE Gerät so. Dieser Wert abzüglich 256 ergibt die Signalstärke in dBm
 
Weitere Hinweise: die Pumpe gibt den Volumenstrom in sehr groben Intervallen aus. So habe ich des Öfteren zum Beispiel erlebt, dass er von eins auf 80 dann auf 119 springt. Dazwischen habe ich keine Werte gefunden, dies setzt sich natürlich auch bei höheren Werten fort.

Die Pumpentemperatur ist tatsächlich nur der Wert am Gehäuse und nicht des Fördermediums. Diese hängt jedoch stark von der Temperatur des Fördermediums ab. Bei zwei mit der Dämmschale versehenen Pumpen nebeneinander betrug die Temperatur an der Pumpe mit 50 °C Medientemperatur 26 °C. Bei der anderen Pumpe mit ca. 32 °C Medientemperatur betrug die Pumpentemperatur 18 °C, bei einer Raumtemperatur von ca. 16 °C. Da die Pumpe über eine automatische Erkennung der Nachtabsenkung verfügt und dies über der Erkennung einer sinkenden Fördernmedientemperatur geschieht, hat die Pumpe wohl auch hierfür einen Sensor. Diesen Wert auszulesen ist mir nicht gelungen.

Das Programm liest die Ausgabe von hcidump --raw hci via Pipe ein. Zur Vereinfachung ist die AlphaDekoder.sh Datei beigefügt.

### Benötigte Pakete:
python3
bluez
bluez-hcidump
`sudo apt install python3 bluez bluez-hcidump`

Ausführen mit sudo ./AlphaDecoder.sh

## Raspberry Pi Zero W zum Auslesen der Grundfos Pumpe
Zum Auslesen der Pumpendaten bzw. Empfang der Bluetoothpakete eignet sich ein Raspberry Pi Zero W hervorragend. Der Raspberry Pi 4 hat Stand Dezember 2020 leider immer noch einige Probleme mit Bluetooth, siehe z.B. https://github.com/RPi-Distro/firmware-nonfree/issues/8
https://github.com/RPi-Distro/bluez-firmware/issues/6
https://github.com/abandonware/noble/issues/99

Auch war die Reichweite in meinen Tests deutlich geringer als bei einem Raspberry Pi Zero W, welcher eine hervorragende Empfangsqualität besitzt. Der Raspberry Pi 3B war bei der Reichweite ok.



