############################################################################
#    Copyright (C) 2023 by macGH                                           #
#                                                                          #
#    This lib is free software; you can redistribute it and/or modify      #
#    it under the terms of the LGPL                                        #
#    This program is distributed in the hope that it will be useful,       #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#    GNU General Public License for more details.                          #
#                                                                          #
############################################################################

# Controlling the Mean Well devices BIC-2200 and NPB-abc0
# Please note: this Lib is currently only wokring with these 2 devices 
# and also not fully tested.
# Use at your own risk !  

# Requirement for using
# Needed external python modules
# pip3 install ifcfg

# Version history
# macGH 18.06.2023  Version 0.1.0
# macGH 19.06.2023  Version 0.1.1: Added checkcandevice
# macGH 20.06.2023  Version 0.1.2: Added mycan.ini read device paramter
# macGH 13.07.2023  Version 0.1.3: Added read of BIC2200 operation
# macGH 10.02.2024  Version 0.1.4: Added can_set_ADR to change the address later if multible Devices are used
# macGH 16.02.2024  Version 0.1.5: Added Firmware read
# macGH 26.03.2024  Version 0.1.6: Update system config
# macGH 13.05.2024  Version 0.1.7: Set Output to 0 too low or high, val is changed to min/max out value of device, added decode NPB Curve
# macGH 24.09.2024  Version 0.1.8: Addad Fanspeed for BIC2200


import os
import can
import ifcfg
import configparser
import logging

######################################################################################
# Explanations
######################################################################################

######################################################################################
# def __init__(self, usedmwdev, mwcanid, devpath, loglevel):
#
# usedmwdev = Meanwell device
# 0 = BIC2200
# 1 = NPB-abc0 (NPB-0450 .. NPB-1700)
#
# mwcanid
# ID = Cortroller Message ID + Device ID [00-07] 
# Be sure you select the right Device-ID (Jumper block on device)
# BIC-2200 00 - 07  
# NPB-abc0 00 - 03  
#
# devpath
# Add the right /dev/tty device here, mostly .../dev/ttyACM0, if empty default path is used
#
# loglevel
# Enter Loglevel 0,10,20,30,40,50 
# CRITICAL   50
# ERROR      40
# WARNING    30
# INFO       20
# DEBUG      10
# NOTSET      0
######################################################################################


######################################################################################
# const values
#Devices
DEV_BIC_2200 = 0
DEV_NPB      = 1
DEV_CAN0     = 0
DEV_RS232    = 1


#SYSTEM CONFIG BITS
SYSTEM_CONFIG_CAN_CTRL       = 0
SYSTEM_CONFIG_OPERATION_INIT = 1 #BIT1 + BIT2 --> 00 .. 11
SYSTEM_CONFIG_EEP_OFF        = 10

#SYSTEM STATUS BITS
SYSTEM_STATUS_M_S           = 0
SYSTEM_STATUS_DC_OK         = 1
SYSTEM_STATUS_PFC_OK        = 2
SYSTEM_STATUS_ADL_ON        = 4
SYSTEM_STATUS_INITIAL_STATE = 5
SYSTEM_STATUS_EEPER         = 6

#NPB CURVE_CONFIG BITS
CURVE_CONFIG_CUVS  =  0 #Bit0 + Bit1 --> 00 .. 11
CURVE_CONFIG_TCS   =  2 #Bit2 + Bit3 --> 00 .. 11
CURVE_CONFIG_STGS  =  6
CURVE_CONFIG_CUVE  =  7
CURVE_CONFIG_CCTOE =  8
CURVE_CONFIG_CVTOE =  9
CURVE_CONFIG_FVTOE = 10
CURVE_CONFIG_RSTE  = 11

#NPB CHG STATUS
CHG_STATUS_FULLM       =  0
CHG_STATUS_CCM         =  1
CHG_STATUS_CVM         =  2
CHG_STATUS_FVM         =  3
CHG_STATUS_WAKEUP_STOP =  6
CHG_STATUS_NTCER       = 10
CHG_STATUS_BTNC        = 11
CHG_STATUS_CCTOF       = 13
CHG_STATUS_CVTOF       = 14
CHG_STATUS_FVTOF       = 15

#FAULT STATUS BITS
FAULT_FAN_FAIL = 0
FAULT_OTP      = 1
FAULT_OVP      = 2
FAULT_OLP      = 3
FAULT_SHORT    = 4
FAULT_AC_FAIL  = 5
FAULT_OP_OFF   = 6
FAULT_HI_TEMP  = 7
FAULT_HV_OVP   = 8


#########################################
# gereral function
def set_bit(value, bit):
    return value | (1<<bit)

def clear_bit(value, bit):
    return value & ~(1<<bit)

def is_bit(value, bit):
    return bool(value & (1<<bit))

#########################################
##class
class mwcan:
  
    #########################################
    # Decode Bitstring to text
    def decode_fault_status(self,val):
        print("BIT flags: " + format(val, '#016b'))
        if self.USEDMWHW in [0]:
            if not is_bit(val,0):     print("FAULT  BIT  0: FAN working normally")
            else:                     print("FAULT  BIT  0: FAN locked")
        if self.USEDMWHW in [1]:      print("FAULT  BIT  0: NOT USED")
 
        if self.USEDMWHW in [0,1]:
            if not is_bit(val,1):     print("FAULT  BIT  1: Internal temperature normal")
            else:                     print("FAULT  BIT  1: Internal temperature abnormal")

        if self.USEDMWHW in [0,1]:
            if not is_bit(val,2):     print("FAULT  BIT  2: DC voltage normal")
            else:                     print("FAULT  BIT  2: DC voltage protected")
        
        if self.USEDMWHW in [0,1]:
            if not is_bit(val,3):     print("FAULT  BIT  3: DC voltage normal")
            else:                     print("FAULT  BIT  3: DC voltage protected")

        if self.USEDMWHW in [0,1]:
            if not is_bit(val,4):     print("FAULT  BIT  4: Shorted circuit do not exist")
            else:                     print("FAULT  BIT  4: Output shorted circuit protected")
        
        if self.USEDMWHW in [0,1]:
            if not is_bit(val,5):     print("FAULT  BIT  5: AC main normal")
            else:                     print("FAULT  BIT  5: AC abnormal protection")
        
        if self.USEDMWHW in [0,1]:
            if not is_bit(val,6):     print("FAULT  BIT  6: Output/DC turned on")
            else:                     print("FAULT  BIT  6: Output/DC turned off")

        if self.USEDMWHW in [0,1]:
            if not is_bit(val,7):     print("FAULT  BIT  7: Internal temperature normal")
            else:                     print("FAULT  BIT  7: Internal temperature abnormal")

        if self.USEDMWHW in [0]:
            if not is_bit(val,8):     print("FAULT  BIT  8: HV voltage normal")
            else:                     print("FAULT  BIT  8: HV over voltage protected")

    def decode_system_status(self,val):
        print("BIT flags: " + format(val, '#016b'))
        if self.USEDMWHW in [0]:
            if not is_bit(val,0):     print("STATUS BIT  0: Current device is Slave")
            else:                     print("STATUS BIT  0: Current device is Master")
        if self.USEDMWHW in [1]:      print("STATUS BIT  0: NOT USED")
 
        if self.USEDMWHW in [0]:
            if not is_bit(val,1):     print("STATUS BIT  1: Secondary DD output voltage status TOO LOW")
            else:                     print("STATUS BIT  1: Secondary DD output voltage status NORMAL")
        if self.USEDMWHW in [1]:
            if not is_bit(val,1):     print("STATUS BIT  1: DC output at a normal range")
            else:                     print("STATUS BIT  1: DC output too low")

        if self.USEDMWHW in [0]:
            if not is_bit(val,2):     print("STATUS BIT  2: Primary PFC OFF or abnormal")
            else:                     print("STATUS BIT  2: Primary PFC ON normally")
        if self.USEDMWHW in [1]:      print("STATUS BIT  2: NOT USED")
        
        print("STATUS BIT  3: NOT USED")
        
        if self.USEDMWHW in [0]:
            if not is_bit(val,4):     print("STATUS BIT  4: Active dummy load off/function not supported")
            else:                     print("STATUS BIT  4: Active dummy load on")
        if self.USEDMWHW in [1]:      print("STATUS BIT  4: NOT USED")
        
        if self.USEDMWHW in [0]:
            if not is_bit(val,5):     print("STATUS BIT  5: In initialization status")
            else:                     print("STATUS BIT  5: NOT in initialization status")
        if self.USEDMWHW in [1]:
            if not is_bit(val,5):     print("STATUS BIT  5: NOT in initialization status")
            else:                     print("STATUS BIT  5: In initialization status")
        
        if not is_bit(val,6):         print("STATUS BIT  6: EEPROM data access normal")
        else:                         print("STATUS BIT  6: EEPROM data access error")
        print("STATUS BIT  7: NOT USED")

    def decode_system_config(self,val):
        print("BIT flags: " + format(val, '#016b'))
        c = val & 0b00000001
        if self.USEDMWHW in [0]:
            if c == 0:                print("CONFIG BIT    0: The output voltage/current defined by control over SVR")
            if c == 1:                print("CONFIG BIT    0: The output voltage, current, ON/OFF control defined by control CAN MODE")
        if self.USEDMWHW in [1]:      print("CONFIG BIT    0: NOT USED")
        
        c = (val >> 1) & 0b00000011
        if c == 0:                    print("CONFIG BIT  2-1: Power OFF, pre-set 0x00(OFF)")    
        if c == 1:                    print("CONFIG BIT  2-1: Power ON, pre-set0x01(ON)")    
        if c == 2:                    print("CONFIG BIT  2-1: Pre-set is previous set value")    
        if c == 3:                    print("CONFIG BIT  2-1: not used, reserved")    
       
        c = (val >> 7) & 0b00000011
        if c == 0:                    print("CONFIG BIT  8-9: Immediate. Changes to parameters are written to EEPROM (default)")    
        if c == 1:                    print("CONFIG BIT  8-9: 1 minute delay. Write changes to EEPROM if all parameters remain unchanged for 1 minute")    
        if c == 2:                    print("CONFIG BIT  8-9: 10 minute delay. Write changes to EEPROM if all parameters remain unchanged for 10 minute")    
        if c == 3:                    print("CONFIG BIT  8-9: not used, reserved")    

        c = (val >> SYSTEM_CONFIG_EEP_OFF) & 0b00000001
        if c == 0:                    print("CONFIG BIT   10: Enable. Parameters to be saved into EEPROM (default)")    
        if c == 1:                    print("CONFIG BIT   10: Disable. Parameters NOT to be saved into EEPROM")    

    def decode_curve_config(self,val): #only NPB
        print("BIT flags: " + format(val, '#016b'))
        c = val & 0b00000011
        if c == 0:                    print("CONFIG BIT  1-0: CUVS  Customized charging curve(default)")    
        if c == 1:                    print("CONFIG BIT  1-0: CUVS  Preset charging curve 1")    
        if c == 2:                    print("CONFIG BIT  1-0: CUVS  Preset charging curve 2")    
        if c == 3:                    print("CONFIG BIT  1-0: CUVS  Preset charging curve 3")    

        c = (val >> 2) & 0b00000011
        if c == 0:                    print("CONFIG BIT  2-3: TCS   disable")    
        if c == 1:                    print("CONFIG BIT  2-3: TCS   -3mV/°C/cell(default)")    
        if c == 2:                    print("CONFIG BIT  2-3: TCS   -4mV/°C/cell")    
        if c == 3:                    print("CONFIG BIT  2-3: TCS   -5mV/°C/cell")    
  
        c = (val >> CURVE_CONFIG_CUVE) & 0b00000001
        if c == 0:                    print("CONFIG BIT    7: CUVE  Disabled, power supply mode")    
        if c == 1:                    print("CONFIG BIT    7: CUVE  Enabled, charger mode(defaut)")    

        c = (val >> CURVE_CONFIG_CCTOE) & 0b00000001
        if c == 0:                    print("CONFIG BIT    8: CCTOE Disabled")    
        if c == 1:                    print("CONFIG BIT    8: CCTOE Enabled")    

        c = (val >> CURVE_CONFIG_CVTOE) & 0b00000001
        if c == 0:                    print("CONFIG BIT    9: CVTOE Disabled")    
        if c == 1:                    print("CONFIG BIT    9: CVTOE Enabled")    

        c = (val >> CURVE_CONFIG_FVTOE) & 0b00000001
        if c == 0:                    print("CONFIG BIT   10: FVTOE Disabled")    
        if c == 1:                    print("CONFIG BIT   10: FVTOE Enabled")    

        c = (val >> CURVE_CONFIG_RSTE) & 0b00000001
        if c == 0:                    print("CONFIG BIT   11: RSTE  Disabled")    
        if c == 1:                    print("CONFIG BIT   11: RSTE  Enabled")    

    def decode_chg_status(self,val):
        if self.USEDMWHW == 0: return
        print("BIT flags: " + format(val, '#016b'))
        if self.USEDMWHW in [1]:
            if not is_bit(val,0):     print("CHG    BIT  0: Not fully charged")
            else:                     print("CHG    BIT  0: Fully charged")
 
        if self.USEDMWHW in [1]:
            if not is_bit(val,1):     print("CHG    BIT  1: The charger NOT in constant current mode")
            else:                     print("CHG    BIT  1: The charger in constant current mode")

        if self.USEDMWHW in [1]:
            if not is_bit(val,2):     print("CHG    BIT  2: The charger NOT in constant voltage mode")
            else:                     print("CHG    BIT  2: The charger in constant voltage mode")
        
        if self.USEDMWHW in [1]:
            if not is_bit(val,3):     print("CHG    BIT  3: The charger NOT in float mode")
            else:                     print("CHG    BIT  3: The charger in float mode")

        print("CHG    BIT  4: NOT USED")
        print("CHG    BIT  5: NOT USED")
        
        if self.USEDMWHW in [1]:
            if not is_bit(val,6):     print("CHG    BIT  6: Wake up finished")
            else:                     print("CHG    BIT  6: Wake up not finished")

        print("CHG    BIT  7: NOT USED")
        print("CHG    BIT  8: NOT USED")
        print("CHG    BIT  9: NOT USED")

        if self.USEDMWHW in [1]:
            if not is_bit(val,10):     print("CHG    BIT 10: NO short-circuit in the circuitry of temperature compensation")
            else:                      print("CHG    BIT 10: The circuitry of temperature compensation has short-circuited")

        if self.USEDMWHW in [1]:
            if not is_bit(val,11):     print("CHG    BIT 11: Battery detected")
            else:                      print("CHG    BIT 11: Battery NOT detected")

        print("CHG    BIT 12: NOT USED")

        if self.USEDMWHW in [1]:
            if not is_bit(val,13):     print("CHG    BIT 13: NO time out in constant current mode")
            else:                      print("CHG    BIT 13: Constant current mode time out")

        if self.USEDMWHW in [1]:
            if not is_bit(val,14):     print("CHG    BIT 14: NO time out in constant voltage mode")
            else:                      print("CHG    BIT 14: Constant voltage mode time out")

        if self.USEDMWHW in [1]:
            if not is_bit(val,15):     print("CHG    BIT 15: NO time out in float mode")
            else:                      print("CHG    BIT 15: Float mode timed out")

    def decode_firmware(self,val):
        MCU1 = (val & 0xFF00) >> 8
        MCU2 = val & 0x00FF
        print("Firmware: MCU1: " + str(MCU1) + " - MCU2: " + str(MCU2))
        return str(MCU1) + "-" + str(MCU2)

##################################################################################################################################################
##################################################################################################################################################

    def checkcandevice(self,val):
        f = 0
        for name, interface in ifcfg.interfaces().items():
            # Check for Can0 interface
            logging.debug("can checkcandevice: " + name + " - " + str(interface))
            if interface['device'] == val:
                f = 1
                #can0 always found if slcand with RS232CAN is used, even when deleted
                #workaround because of bug in ifcfg, check if up and running
                logging.info("Found can0 interface. Check if already up ... ")
                if(interface['flags'] == "193<UP,RUNNING,NOARP> "):  
                    f = 2
                    logging.info("Found can0 interface. Already created.")
        return f

    def mwcaniniread(self,val):
        logging.debug("Detected Device: " + val)
        self.mwtype = val
        config = configparser.ConfigParser()
        config.sections()
        spath = os.path.dirname(os.path.realpath(__file__)) 
        logging.debug("Ini Path: " + spath + '/mwcan.ini')
        config.read(spath + '/mwcan.ini')
        if config.has_section(val): 
            self.dev_Voltage             = int(config.get(val, 'Voltage'))
            self.dev_MaxWatt             = int(config.get(val, 'MaxWatt'))
            self.dev_BoostChargeVoltage  = round(float(config.get(val, 'BoostChargeVoltage'))*100)
            self.dev_FloatChargeVoltage  = round(float(config.get(val, 'FloatChargeVoltage'))*100)
            self.dev_MinChargeVoltage    = round(float(config.get(val, 'MinChargeVoltage'))*100)
            self.dev_MaxChargeVoltage    = round(float(config.get(val, 'MaxChargeVoltage'))*100)
            self.dev_MinChargeCurrent    = round(float(config.get(val, 'MinChargeCurrent'))*100)
            self.dev_MaxChargeCurrent    = round(float(config.get(val, 'MaxChargeCurrent'))*100)

            #BIC-2200 parameter
            self.dev_MinDisChargeVoltage = round(float(config.get(val, 'MinDisChargeVoltage'))*100)
            self.dev_MaxDisChargeVoltage = round(float(config.get(val, 'MaxDisChargeVoltage'))*100)
            self.dev_MinDisChargeCurrent = round(float(config.get(val, 'MinDisChargeCurrent'))*100)
            self.dev_MaxDisChargeCurrent = round(float(config.get(val, 'MaxDisChargeCurrent'))*100)

            logging.info("Voltage:             " + str(self.dev_Voltage) + " V")
            logging.info("MaxWatt:             " + str(self.dev_MaxWatt) + " W")
            logging.info("BoostChargeVoltage:  " + str(self.dev_BoostChargeVoltage)  + " V (0.01)")
            logging.info("FloatChargeVoltage:  " + str(self.dev_FloatChargeVoltage)  + " V (0.01)")
            logging.info("MinChargeVoltage:    " + str(self.dev_MinChargeVoltage)    + " V (0.01)")
            logging.info("MaxChargeVoltage:    " + str(self.dev_MaxChargeVoltage)    + " V (0.01)")
            logging.info("MinChargeCurrent:    " + str(self.dev_MinChargeCurrent)    + " A (0.01)")
            logging.info("MaxChargeCurrent:    " + str(self.dev_MaxChargeCurrent)    + " A (0.01)")
            
            logging.info("MinDisChargeVoltage: " + str(self.dev_MinDisChargeVoltage) + " V (0.01)")
            logging.info("MaxDisChargeVoltage: " + str(self.dev_MaxDisChargeVoltage) + " V (0.01)")
            logging.info("MinDisChargeCurrent: " + str(self.dev_MinDisChargeCurrent) + " A (0.01)")
            logging.info("MaxDisChargeCurrent: " + str(self.dev_MaxDisChargeCurrent) + " A (0.01)")
            
            return 0
        else:
            return -1

    def __init__(self, usedmwdev, mwcanid, devpath, loglevel):
        logging.basicConfig(level=loglevel, encoding='utf-8')
        if devpath == "": devpath = "/dev/ttyACM0" #just try if is is the common devpath
        self.CAN_DEVICE    = devpath
        
        self.can_set_ADR(usedmwdev, mwcanid)
      
        logging.debug("CAN device  : " + self.CAN_DEVICE)
        logging.debug("CAN adr to  : " + str(self.CAN_ADR))
        logging.debug("CAN adr from: " + self.CAN_ADR_R)

    def can_set_ADR(self,usedmwdev, mwcanid):
        self.USEDMWHW      = usedmwdev 
        if usedmwdev==0: #BIC-2200 
            CAN_ADR_S   = "0x000C03" + mwcanid
            CAN_ADR_S_R = "000c02"   + mwcanid #return from CAN is lowercase
        if usedmwdev==1: #NPB
            CAN_ADR_S   = "0x000C01" + mwcanid
            CAN_ADR_S_R = "000c00"   + mwcanid #return from CAN is lowercase

        self.CAN_ADR   = int(CAN_ADR_S,16)
        self.CAN_ADR_R = CAN_ADR_S_R           #need string to compare of return of CAN
        return

    #########################################
    # CAN function
    def can_up(self):
        self.can0found = self.checkcandevice("can0") 
        
        if self.can0found < 2: #2 = fully up, #1 = created but not up, #0 = can0 not exists, mostly RS232 devices 
            if self.can0found == 0: 
                os.system('sudo slcand -f -s5 -o ' + self.CAN_DEVICE) #looks like a RS232 device, bring it up 
                logging.debug("can_up: RS232 DEVICE ?")

            logging.debug("can_up: Link Set")
            os.system('sudo ip link set can0 up type can bitrate 250000')
            os.system('sudo ip link set up can0 txqueuelen 1000')
        
        # init interface for using with this class
        logging.debug("can_up: init SocketCan")
        self.can0 = can.interface.Bus(channel = 'can0', bustype = 'socketcan')
        
        #Get Meanwell device and set parameter from mwcan.ini file
        t = self.type_read().strip()
        if self.mwcaniniread(t) == -1:
            raise Exception("MEANWELL DEVICE NOT FOUND")
        
        return t
        
    def can_down(self):
        self.can0.shutdown() #Shutdown our interface
        if self.can0found < 2: #only shutdown system can0 if it was created by us
            logging.info("can_down: shutdown CAN0")
            os.system('sudo ip link set can0 down')
            os.system('sudo ip link del can0')
        else:
            logging.info("can0 was externally created. Not removing it.")


    #########################################
    # receive function
    def can_receive(self):
        msgr = str(self.can0.recv(0.5))
        logging.debug(msgr)
        if msgr != "None":
            msgr_split = msgr.split()
            #Check if the CAN response is from our request
            if msgr_split[3] != self.CAN_ADR_R:
                return -1
            
            if msgr_split[7] == "3":
                hexval = (msgr_split[10])
                decval = int(hexval,8)
            
            if msgr_split[7] == "4":
                hexval = (msgr_split[11] + msgr_split[10])
                decval = int(hexval,16)
            
            #special format for scaling factor and frimware version
            if msgr_split[7] == "8":
                if(msgr_split[8] == "84"): #Firmware
                    i=10
                    hexarray = ""
                    while(msgr_split[i]) != "ff":
                        hexarray = hexarray + msgr_split[i] 
                        i+=1

                    hexval = bytearray.fromhex(hexarray) #Currently only 2 Bytes
                    decval = int(hexval.hex(),16)
                    hexval = hexval.hex() 

                if(msgr_split[8] == "c0"): #Scaling Factor
                    hexval = bytearray.fromhex(msgr_split[15]+msgr_split[14]+msgr_split[13]+msgr_split[12]+msgr_split[11]+msgr_split[10])
                    decval = int(hexval.hex(),16)
                    hexval = hexval.hex() 

            logging.debug("Return HEX: " + hexval)
            logging.debug("Return DEC: " + str(decval))
            logging.debug("Return BIN: " + format(decval, '#016b'))
            
        else: 
            logging.error("ERROR: TIMEOUT - NO MESSAGE RETURNED ! CHECK SETTINGS OR MESSAGE TYPE NOT SUPPORTED !")
            decval = -1

        return decval
    
    def can_receive_char(self):
        msgr = str(self.can0.recv(0.5))
        logging.debug(msgr)
        if msgr != "None":
            msgr_split = msgr.split()
            #Check if the CAN response is from our request
            if msgr_split[3] != self.CAN_ADR_R:
                return ""
            
            if msgr_split[7] == "5":
                s = bytearray.fromhex(msgr_split[10]+msgr_split[11]+msgr_split[12]).decode()

            if msgr_split[7] == "8":
                s = bytearray.fromhex(msgr_split[10]+msgr_split[11]+msgr_split[12]+msgr_split[13]+msgr_split[14]+msgr_split[15]).decode()
            logging.debug(s)

        else:
            logging.error('Timeout occurred, no message.')
            s = ""

        return s

    #############################################################################
    # Read Write operation function
    def can_read_write(self,lobyte,hibyte,rw,val,count=2):
        if rw==0:
            msg = can.Message(arbitration_id=self.CAN_ADR, data=[lobyte,hibyte], is_extended_id=True)
            self.can0.send(msg)
            v = self.can_receive()
        else:
            valhighbyte = val >> 8
            vallowbyte  = val & 0xFF
            if count == 1: #1 byte to send
                msg = can.Message(arbitration_id=self.CAN_ADR, data=[lobyte,hibyte,vallowbyte], is_extended_id=True)
            if count == 2: #2 byte to send
                msg = can.Message(arbitration_id=self.CAN_ADR, data=[lobyte,hibyte,vallowbyte,valhighbyte], is_extended_id=True)
            self.can0.send(msg)
            v = val
            
        return v
    
    def can_read_string(self,lobyte,hibyte,lobyte2,hibyte2):

        msg = can.Message(arbitration_id=self.CAN_ADR, data=[lobyte,hibyte], is_extended_id=True)
        self.can0.send(msg)
        s1 = ""
        s1 = self.can_receive_char()
    
        s2 = ""
        if (lobyte2 > 0) or (hibyte2 > 0):
            msg = can.Message(arbitration_id=self.CAN_ADR, data=[lobyte2,hibyte2], is_extended_id=True)
            self.can0.send(msg)
            s2 = self.can_receive_char()
        
        s=s1+s2
        logging.info("Received String: " + s)
        return s

    #############################################################################
    # Operation function
    
    def operation(self,rw,val):#0=off, 1=on
        logging.debug("Turn output on or off 0x0000")
        # Command Code 0x0000
        return self.can_read_write(0x00,0x00,rw,val,1)
    
    def v_out_set(self,rw,val): #0=read, 1=set
        logging.debug("read/write charge voltage setting (format: value, F=0.01) 0x0020")
        # Command Code 0x0020
        # Read Charge Voltage
        if rw == 1:
            if val < self.dev_MinChargeVoltage:
                val = self.dev_MinChargeVoltage
            if val > self.dev_MaxChargeVoltage:
                val = self.dev_MaxChargeVoltage
        
        return self.can_read_write(0x20,0x00,rw,val)
   
    def i_out_set(self,rw,val): #0=read, 1=set
        logging.debug("read/write charge current setting (format: value, F=0.01) 0x0030")
        # Command Code 0x0030
        # Set Charge Current
        if rw == 1:
            if val < self.dev_MinChargeCurrent:
                val = self.dev_MinChargeCurrent
            if val > self.dev_MaxChargeCurrent:
                val = self.dev_MaxChargeCurrent
        
        return self.can_read_write(0x30,0x00,rw,val)
    
    def fault_status_read(self): #0=read, 1=set
        logging.debug("read Fault Status 0x0040")
        # Command Code 0x0040
        # Set Charge Current
        return self.can_read_write(0x40,0x00,0,0)

    def v_in_read(self):
        logging.debug("read ac voltage (format: value, F=0.10) 0x0050")
        # Command Code 0x0050
        # Read AC Voltage
        return self.can_read_write(0x50,0x00,0,0)

    def v_out_read(self):
        logging.debug("read dc voltage (format: value, F=0.01) 0x0060")
        # Command Code 0x0060
        # Read DC Voltage
        return self.can_read_write(0x60,0x00,0,0)

    def i_out_read(self):
        logging.debug("read dc current (format: value, F=0.01) 0x0061")
        # Command Code 0x0061
        # Read DC Current
        v = self.can_read_write(0x61,0x00,0,0)
        #BIC-2200 return negative current with 
        if self.USEDMWHW in [0]:
             if v > 20000: v = v - 65536
        return(v)
   
    def temp_read(self):
        logging.debug("read power supply temperature (format: value, F=0.10) 0x0062")
        # Command Code 0x0062
        # Read internal Temperature 
        return self.can_read_write(0x62,0x00,0,0)
    
    def manu_read(self):
        logging.debug("read power supply Manufacturer 0x0080")
        # Command Code 0x0080
        # Command Code 0x0081
        # Read Type of PSU
        return self.can_read_string(0x80,0x00,0x81,0x00)

    def type_read(self):
        logging.debug("read power supply type 0x0082 + 0x0083")
        # Command Code 0x0082
        # Command Code 0x0083
        # Read Type of PSU
        return self.can_read_string(0x82,0x00,0x83,0x00)
    
    def firmware_read(self):
        logging.debug("read firmware version 0x0084")
        # Command Code 0x0084
        # Read Type of PSU
        return self.can_read_write(0x84,0x00,0,0)

    def manu_factory_location(self):
        logging.debug("read firmware version 0x0084")
        # Command Code 0x0085
        # Read Type of PSU
        return self.can_read_string(0x85,0x00,0x00,0x00)

    def manu_date(self):
        logging.debug("read firmware version 0x0084")
        # Command Code 0x0086
        # Read Type of PSU
        return self.can_read_string(0x86,0x00,0x00,0x00)

    def serial_read(self):
        logging.debug("read power supply serial 0x0087 + 0x0088")
        # Command Code 0x0087
        # Command Code 0x0088
        # Read serial number of PSU
        return self.can_read_string(0x87,0x00,0x88,0x00)

    def system_scaling_factor(self):
        logging.debug("read scaling factors 0x00C0")
        # Command Code 0x00C0
        # Read system scaling factors 
        return self.can_read_write(0xC0,0x00,0,0)

    def system_status(self):
        logging.debug("read system status 0x00C1")
        # Command Code 0x00C1
        # Read system status 
        return self.can_read_write(0xC1,0x00,0,0)

    def system_config(self,rw,val):
        logging.debug("read/write system config 0x00C2")
        # Command Code 0x00C2
        # Read/Write system config 
        return self.can_read_write(0xC2,0x00,rw,val)

    #############################################################################
    ##NPB-abc0 only: Charger functions
    #############################################################################
    def NPB_curve_CC(self,rw,val):
        logging.debug("read/write Constant current setting of charge curve (format: value, F=0.01) 0x00B0")
        # Command Code 0x00B0
        # Read/Write Constant current setting of charge curve
        return self.can_read_write(0xB0,0x00,rw,val)

    def NPB_curve_CV(self,rw,val):
        logging.debug("read/write Constant voltage setting of charge curve (format: value, F=0.01) 0x00B1")
        # Command Code 0x00B1
        # Read/Write Constant voltage setting of charge curve
        return self.can_read_write(0xB1,0x00,rw,val)

    def NPB_curve_FV(self,rw,val):
        logging.debug("read/write floating voltage setting of charge curve (format: value, F=0.01) 0x00B2")
        # Command Code 0x00B2
        # Read/Write floating voltage setting of charge curve
        return self.can_read_write(0xB2,0x00,rw,val)

    def NPB_curve_TC(self,rw,val):
        logging.debug("read/write Taper current setting value of charging curve (format: value, F=0.01) 0x00B3")
        # Command Code 0x00B3
        # Read/Write Taper current setting value of charging curve
        return self.can_read_write(0xB3,0x00,rw,val)

    def NPB_curve_config(self,rw,val):
        logging.debug("Set CURVE CONFIG of NPB Device 0x00B4")
        # Command Code 0x00B4
        # first Read the current value, change and verify

        return self.can_read_write(0xB4,0x00,rw,val)

    def NPB_curve_config_pos(self,rw,pos,val):
        logging.debug("Set Bits in CURVE CONFIG of NPB Device 0x00B4")
        # Command Code 0x00B4
        # first Read the current value, change and verify

        v = self.can_read_write(0xB4,0x00,0,0)
        
        #modify bit at pos to val
        if rw==1: #0=read, 1=write
            if val==1:
              v = set_bit(v,pos)
            else:
              v = clear_bit(v,pos)
    
        #Write it back
            v = self.can_read_write(0xB4,0x00,1,v)
        #Read to check
            v = self.can_read_write(0xB4,0x00,0,0)
    
        return v

    def NPB_curve_CC_TIMEOUT(self,rw,val):
        logging.debug("read/write CC charge timeout setting of charging curve 0x00B5")
        # Command Code 0x00B5
        # Read/Write CC charge timeout setting of charging curve
        return self.can_read_write(0xB5,0x00,rw,val)

    def NPB_curve_CV_TIMEOUT(self,rw,val):
        logging.debug("read/write CV charge timeout setting of charging curve 0x00B6")
        # Command Code 0x00B6
        # Read/Write CV charge timeout setting of charging curve
        return self.can_read_write(0xB6,0x00,rw,val)

    def NPB_curve_FV_TIMEOUT(self,rw,val):
        logging.debug("read/write FV charge timeout setting of charging curve 0x00B7")
        # Command Code 0x00B7
        # Read/Write FV charge timeout setting of charging curve
        return self.can_read_write(0xB7,0x00,rw,val)

    def NPB_chg_status_read(self):
        logging.debug("read Charge status 0x00B8")
        # Command Code 0x00B8
        # Read/Write system config 
        return self.can_read_write(0xB8,0x00,0,0)

    #############################################################################
    ##BIC-2200 only - charge dischagre functions
    #############################################################################
    def BIC_fanspeed1(self): 
        logging.debug("set direction charge 0x0100")
        # Command Code 0x0070
        # read fanspeed 1
        return self.can_read_write(0x70,0x00,0,0)

    def BIC_fanspeed2(self): 
        logging.debug("set direction charge 0x0100")
        # Command Code 0x0071
        # read fanspeed 2
        return self.can_read_write(0x71,0x00,0,0)

    def BIC_chargemode(self,rw,val): #0=charge, 1=discharge
        logging.debug("set direction charge 0x0100")
        # Command Code 0x0100
        # Set Direction Charge
        return self.can_read_write(0x00,0x01,rw,val,1)

    def BIC_discharge_v(self,rw,val):
        logging.debug("read/write discharge voltage setting 0x0120")
        # Command Code 0x0120
        # Set Discharge Voltage
        if rw == 1:
            if val < self.dev_MinDisChargeVoltage:
                val = self.dev_MinDisChargeVoltage
            if val > self.dev_MaxDisChargeVoltage:
                val = self.dev_MaxDisChargeVoltage
        
        return self.can_read_write(0x20,0x01,rw,val)
    
    def BIC_discharge_i(self,rw,val):
        logging.debug("read/write discharge current setting 0x0130")
        # Command Code 0x0130
        # Read Discharge Current
        if rw == 1:
            if val < self.dev_MinDisChargeCurrent:
                val = self.dev_MinDisChargeCurrent
            if val > self.dev_MaxDisChargeCurrent:
                val = self.dev_MaxDisChargeCurrent
        
        return self.can_read_write(0x30,0x01,rw,val)

    def BIC_bidirectional_config(self,rw,val): #0=charge, 1=discharge
        logging.debug("Bidirectional mode configuration 0x0140")
        # Command Code 0x0140
        # Set Bidirectional mode configuration
        return self.can_read_write(0x40,0x01,rw,val)
