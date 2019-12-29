#!/bin/bash
echo "Wenn keine Daten ausgegeben werden, bitte prüfen, ob als root läuft und der AlphaReader eingeschaltet und in Empfangsreichweite ist"
hcitool lescan --duplicate > /dev/null &
hcidump --raw hci | python3 decoder.py
