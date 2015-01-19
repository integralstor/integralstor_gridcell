#!/usr/bin/python

import sys, os
import subprocess
import re, logging

def process_call(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    output = ""
    while True:
        out = process.stdout.readline()
        if out == '' and process.poll() != None: break
        output += out
    return (process.returncode, output)

if __name__ == "__main__":
	lcd = []
	lcd.append("/opt/fractalio/bin/fpctl")
	lcd.append("clear")
	(ret, output) = process_call(lcd)

	lcd = []
        args = len(sys.argv)
	if args == 2:
		lcd.append("/opt/fractalio/bin/fpctl")
		lcd.append("print")
		lcd.append(sys.argv[1])
		(ret, output) = process_call(lcd)
	elif args == 3:
		lcd.append("/opt/fractalio/bin/fpctl")
		lcd.append("move")
		lcd.append("0")
		lcd.append("0")
		(ret, output) = process_call(lcd)
		lcd = []
		lcd.append("/opt/fractalio/bin/fpctl")
		lcd.append("print")
		lcd.append(sys.argv[1])
		(ret, output) = process_call(lcd)
		lcd = []
		lcd.append("/opt/fractalio/bin/fpctl")
		lcd.append("move")
		lcd.append("0")
		lcd.append("1")
		(ret, output) = process_call(lcd)
		lcd = []
		lcd.append("/opt/fractalio/bin/fpctl")
		lcd.append("print")
		lcd.append(sys.argv[2])
		(ret, output) = process_call(lcd)
	else:
		lcd.append("/opt/fractalio/bin/fpctl")
		lcd.append("print")
		lcd.append('  fractal io ')
		(ret, output) = process_call(lcd)

	sys.exit(0)
