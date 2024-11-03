#!/usr/bin/env python3

# Controlling the Mean Well NPB-abc0 and BIC-2200-CAN
# tested only with the 24V Version NPB-1200 and BIC-2200-CAN-24

# Requirement for using
# Needed external python modules
# pip3 install ifcfg

# What is missing:

# macGH 15.06.2023  Version 0.2.3
#       - support for Meanwell NPB-x Charger
#       - new config area
# macGH 16.06.2023  Version 0.2.4: fault and status queries    
# macGH 18.06.2023  Version 0.2.5: Changed to mwcan.py class
# macGH 19.06.2023  Version 0.2.6: Fixed some parts 
# macGH 16.02.2024  Version 0.2.7: Added firmware read
# macGH 26.03.2024  Version 0.2.8: Added systemconfig read write
# macGH 13.05.2024  Version 0.2.9: Added NPB config curve read
# macGH 24.09.2024  Version 0.3.0: Added BIC read Fanspeed

import os
import can
import sys
import signal
import atexit
import ifcfg
from mwcan import *

####################################################
# Config
# 0 = BIC-2200
# 1 = NPM-abc0
USEDMW = 0

# BIC-2200 --> "00" to "07"
# NPM-abc0 --> "00" to "03"
USEDID = "03"

# "" = default = "/dev/ttyACM0"
# if you have another device specify here
RS232DEV = "" 

# Enter Loglevel 0,10,20,30,40,50 
# CRITICAL   50
# ERROR      40
# WARNING    30
# INFO       20
# DEBUG      10
# NOTSET      0
LOGLEVEL     = 20
logtofile    = 0
logtoconsole = 1

def on_exit():
    print("CLEAN UP ...")
    candev.can_down()
    
def handle_exit(signum, frame):
    sys.exit(0)

def mwcan_commands():
    print("")
    print(" " + sys.argv[0] + " - controlling the Meanwell CAN devices BIC-2200 Power Supply and NPB-abc0 Charger")
    print("")
    print(" Usage:")
    print("        " + sys.argv[0] + " parameter and <value>")
    print("")
    print("       on                      -- output on")
    print("       off                     -- output off")
    print("       readonoff               -- read current on/off status")
    print("")
    print("       cvread                  -- read charge voltage setting")
    print("       cvset <value>           -- set charge voltage")
    print("       ccread                  -- read charge current setting")
    print("       ccset <value>           -- set charge current")
    print("")
    print("       dvread                  -- read discharge voltage setting")
    print("       dvset <value>           -- set discharge voltage")
    print("       dcread                  -- read discharge current setting")
    print("       dcset <value>           -- set discharge current")
    print("")
    print("       vread                   -- read DC voltage")
    print("       cread                   -- read DC current")
    print("       acvread                 -- read AC voltage")
    print("")
    print("       charge                  -- set direction charge battery")
    print("       discharge               -- set direction discharge battery")
    print("")
    print("       tempread                -- read power supply temperature")
    print("       typeread                -- read power supply type")
    print("       firmwareread            -- read power supply firmware")
    print("       serialread              -- read power supply serial number")
    print("       statusread              -- read status")
    print("       fan1                    -- read fanspeed1")
    print("       fan2                    -- read fanspeed2")
    print("       faultread               -- read fault status")    
    print("       readscaling             -- read scaling factors")    
    print("       systemconfigread        -- read system config")    
    print("       systemconfigset <value> -- write system config")    
    print("       NPB_chargemode <value>  -- Set PSU = 0 or Chargermode = 1")    
    print("       NPB_readcurve           -- read NPB curve config")    
    print("")
    print("       <value> = amps oder volts * 100 --> 25,66V = 2566")
    print("")
    print("       Version 0.2.6 ")

#########################################
# Operation function

def readoperation():#0=off, 1=on
    print ("Read operation mode")
    v = candev.operation(0,0)
    print(v)
    return v

def operation(val):#0=off, 1=on
    print ("turn output on=1 / off=0 ")
    v = candev.operation(1,val)
    print(v)
    return v

def charge_voltage(rw,val=0x00): #0=read, 1=set
    # print ("read/set charge voltage")
    # Command Code 0x0020
    # Read Charge Voltage
    if (rw == 1) and (val == 0x00) : return -1
    v = candev.v_out_set(rw,val)
    print(v)
    return v

def charge_current(rw,val=0x00): #0=read, 1=set
    # print ("read/set charge current")
    # Command Code 0x0030
    # Read Charge Voltage
    #if (rw == 1) and (val == 0x00) : return -1
    v = candev.i_out_set(rw,val)
    print(v)
    return v

def discharge_voltage(rw,val=0x00): #0=read, 1=set
    # print ("read/set discharge voltage")
    # Command Code 0x0120
    # Read Charge Voltage
    if (rw == 1) and (val == 0x00) : return -1
    v = candev.BIC_discharge_v(rw,val)
    print(v)
    return v

def discharge_current(rw,val=0x00): #0=read, 1=set
    # print ("read/set charge current")
    # Command Code 0x0130
    # Read Charge Voltage
    if (rw == 1) and (val == 0x00) : return -1
    v = candev.BIC_discharge_i(rw,val)
    print(v)
    return v

def vread():
    # print ("read dc voltage")
    # Command Code 0x0060
    # Read DC Voltage
    v = candev.v_out_read()
    print(v)
    return v

def cread():
    # print ("read dc current")
    # Command Code 0x0061
    # Read DC Current
    v = candev.i_out_read()
    print(v)
    return v

def acvread():
    # print ("read ac voltage")
    # Command Code 0x0050
    # Read AC Voltage
    v = candev.v_in_read()
    print(v)
    return v

def BIC_chargemode(val): #0=charge, 1=discharge
    # print ("set direction charge")
    # Command Code 0x0100
    # Set Direction Charge
    v = candev.BIC_chargemode(1,val)
    print(v)
    return v

def NPB_readcurve():
    # print ("Set PSU or Charger Mode to NPB Device")
    # Command Code 0x00B4
    v = candev.NPB_curve_config(0,0)
    candev.decode_curve_config(v)
    return v

def NPB_chargemode(rw, val=0xFF):
    # print ("Set PSU or Charger Mode to NPB Device")
    # Command Code 0x00B4
    v = candev.NPB_curve_config_pos(1,CURVE_CONFIG_CUVE,val) #Bit 7 should be 0
    print(v)
    return v

def typeread():
    # print ("read power supply type")
    # Command Code 0x0082
    # Command Code 0x0083
    # Read Type of PSU
    v = candev.type_read()
    print(v)
    return v

def firmwareread():
    # print ("read power supply type")
    # Command Code 0x0084
    # Read firmware version of PSU
    v = candev.firmware_read()
    print(v)
    candev.decode_firmware(v)
    return v

def serialread():
    # print ("read power supply type")
    # Command Code 0x0087
    # Command Code 0x0088
    # Read serial of PSU
    v = candev.serial_read()
    print(v)
    return v

def tempread():
    # print ("read power supply temperature")
    # Command Code 0x0062
    # Read AC Voltage
    v = candev.temp_read()
    print(v)
    return v

def readscaling():
    # print ("Read System Scaling factor")
    # Command Code 0x00C0
    # Read System Status
    
    v = candev.system_scaling_factor()
    return v

def statusread():
    # print ("Read System Status")
    # Command Code 0x00C1
    # Read System Status
    
    v = candev.system_status()
    candev.decode_system_status(v)
    return v
        
def readfan1():
    # print ("Read fan1")
    # Command Code 0x0070
    v = candev.BIC_fanspeed1()
    print(v)
    return v

def readfan2():
    # print ("Read fan2")
    # Command Code 0x0071
    v = candev.BIC_fanspeed2()
    print(v)
    return v

def systemconfig(rw,val):
    # print ("Read System config")
    # Command Code 0x00C2
    # Read System config
    
    v = candev.system_config(rw,val) 
    candev.decode_system_config(v)
    return v

def faultread():
    # print ("Read System Fault Status")
    # Command Code 0x0040
    # Read System Fault Status
    
    v = candev.fault_status_read() 
    candev.decode_fault_status(v)
    return v

def command_line_argument():
    if len (sys.argv) == 1:
        print ("")
        print ("Error: First command line argument missing.")
        mwcan_commands()
        error = 1
        return
    
    if   sys.argv[1] in ['on']:        operation(1)
    elif sys.argv[1] in ['off']:       operation(0)
    elif sys.argv[1] in ['readonoff']: readoperation()
    elif sys.argv[1] in ['cvread']:    charge_voltage(0)
    elif sys.argv[1] in ['cvset']:     charge_voltage(1,int(sys.argv[2]))
    elif sys.argv[1] in ['ccread']:    charge_current(0)
    elif sys.argv[1] in ['ccset']:     charge_current(1,int(sys.argv[2]))
    elif sys.argv[1] in ['dvread']:    discharge_voltage(0)
    elif sys.argv[1] in ['dvset']:     discharge_voltage(1,int(sys.argv[2]))
    elif sys.argv[1] in ['dcread']:    discharge_current(0)
    elif sys.argv[1] in ['dcset']:     discharge_current(1,int(sys.argv[2]))
    elif sys.argv[1] in ['vread']:     vread()
    elif sys.argv[1] in ['cread']:     cread()
    elif sys.argv[1] in ['acvread']:   acvread()
    elif sys.argv[1] in ['charge']:    BIC_chargemode(0)
    elif sys.argv[1] in ['discharge']: BIC_chargemode(1)
    elif sys.argv[1] in ['tempread']:  tempread()
    elif sys.argv[1] in ['typeread']:  typeread()
    elif sys.argv[1] in ['serialread']: serialread()
    elif sys.argv[1] in ['firmwareread']:firmwareread()
    elif sys.argv[1] in ['statusread']: statusread()
    elif sys.argv[1] in ['fan1']:       readfan1()
    elif sys.argv[1] in ['fan2']:       readfan2()
    elif sys.argv[1] in ['faultread']:  faultread()
    elif sys.argv[1] in ['readscaling']:readscaling()
    elif sys.argv[1] in ['systemconfigread']:systemconfig(0,0)
    elif sys.argv[1] in ['systemconfigset'] :systemconfig(1,int(sys.argv[2]))
    elif sys.argv[1] in ['NPB_chargemode']: NPB_chargemode(int(sys.argv[2]))
    elif sys.argv[1] in ['NPB_readcurve']: NPB_readcurve()
    else:
        print("")
        print("Unknown first argument '" + sys.argv[1] + "'")
        mwcan_commands()
        error = 1
        return

#### Main 
atexit.register(on_exit)
signal.signal(signal.SIGTERM, handle_exit)
signal.signal(signal.SIGINT, handle_exit)

#CAN INIT
if USEDMW == 0xFF:
    print("ERROR - YOU NEED TO CONFIGURE THE DEVICE USED IN THE BEGINNING OF THIS SCRIPT")
    sys.exit(1)

if USEDID == "":
    print("ERROR - YOU NEED TO CONFIGURE THE ID IN THE BEGINNING OF THIS SCRIPT")
    sys.exit(1)

mylogs = logging.getLogger()
mylogs.setLevel(LOGLEVEL)

if logtofile == 1:
    file = logging.FileHandler(self.logpath, mode='a')
    file.setLevel(LOGLEVEL)
    fileformat = logging.Formatter("%(asctime)s:%(module)s:%(levelname)s:%(message)s",datefmt="%H:%M:%S")
    file.setFormatter(fileformat)
    mylogs.addHandler(file)

if logtoconsole == 1:
    stream = logging.StreamHandler()
    stream.setLevel(LOGLEVEL)
    streamformat = logging.Formatter("%(asctime)s:%(module)s:%(levelname)s:%(message)s",datefmt="%H:%M:%S")
    stream.setFormatter(streamformat)    
    mylogs.addHandler(stream)


candev = mwcan(USEDMW,USEDID,RS232DEV,LOGLEVEL)
candev.can_up()
print("Found Device: " + candev.mwtype)

command_line_argument()

sys.exit(0)
