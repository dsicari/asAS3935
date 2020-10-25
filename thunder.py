# lightning sensor
from RPi_AS3935 import RPi_AS3935

# sql commands
import MySQLdb

# para capturar interrupcao do sensor
import RPi.GPIO as GPIO

import os
import time
from datetime import datetime
import glob


GPIO.setmode(GPIO.BCM)

# Utilizar i2ctools para encontrar address e bus
sensor = RPi_AS3935(address=0x03, bus=1)
sensor.set_indoors(True)
sensor.set_noise_floor(0)

# O tune eh 0x04, o qual vem na embalagem do sensor
sensor.calibrate(tun_cap=0x04)

#-----------------------------------------------------------------------------------

def handle_interrupt(channel):
	time.sleep(0.003)
	global sensor
	reason = sensor.get_interrupt()
	if reason == 0x01:
		print "%s :: Noise level too high - adjusting (COD: -1)" % strDateTime()
		sensor.raise_noise_floor()
		SqlCmd("log", "Noise level too high - adjusting (COD: -1)")
	elif reason == 0x04:
		print "%s :: Disturber detected - masking (COD: -2)" % strDateTime()
		sensor.set_mask_disturber(True)
		SqlCmd("log", "Disturber detected - masking (COD: -2)")
	elif reason == 0x08:
		distance = sensor.get_distance()
		print "%s :: Sensed lightning! It was %s km away" % (strDateTime(), distance)
		SqlCmd("thunder", distance)

#-----------------------------------------------------------------------------------

def SqlCmd(cmd, msg):
	try:
		rslt = False
		db = MySQLdb.connect(host="localhost", user="root", passwd="", db="urano")
		cur = db.cursor()	
		r = SqlTestConn(cur)
		if(r == True):
			#
			# DO MYSQL STUFF
			#
			if(cmd=="teste"):
				rslt = True	
			elif(cmd=="log"):
				cur.execute("INSERT INTO log (msg ,registro) VALUES (%s, %s)",(msg, strDateTime()))
				db.commit()
				print "::%s:: SqlLog Complete" % strDateTime()
				rslt = True	
			elif(cmd=="thunder"):
				cur.execute("INSERT INTO trovao (distancia ,registro) VALUES (%s, %s)",(msg, strDateTime()))
				db.commit()
				print "::%s::  SqlThunder Complete" % strDateTime()
				rslt = True	
		else:
			print "Connection Failed"
		return rslt
	except MySQLdb.Error, e:
		print "ERROR %d IN CONNECTION: %s" % (e.args[0], e.args[1])
	return False

#-----------------------------------------------------------------------------------

def SqlTestConn(cur):
	try:
		cur.execute("SELECT VERSION()")
	    	results = cur.fetchone()
		if results:
			return True
		else:
			return False               
	except MySQLdb.Error, e:
		print "ERROR %d IN CONNECTION: %s" % (e.args[0], e.args[1])
	return False
	
#-----------------------------------------------------------------------------------

def strDateTime():
    return (time.strftime("%Y-%m-%d ") + time.strftime("%H:%M:%S"))

#-----------------------------------------------------------------------------------	
    
# Interrupcao
pin = 17
GPIO.setup(pin, GPIO.IN)
GPIO.add_event_detect(pin, GPIO.RISING, callback=handle_interrupt)

# Testando SQL
print ":: :: Teste SQL :: ::"
if(SqlCmd("teste", "") == False):
    print "::%s::  ERROR: Sql Fails" % strDateTime()
else:
    print "::%s::  Sql OK" % strDateTime()

# OK, aguardando eventos do sensor
print " --- Waiting for lightning - or at least something that looks like it --- "

count = 0

while True:
    time.sleep(1.0)	
    count = count + 1
    if cont == 60:
        if(SqlCmd("teste", "") == False):
            count = 0;
            print "::%s::  ERROR: Sql Fails, restarting mysql..." % strDateTime()
            os.system("sudo service mysql restart")

	
