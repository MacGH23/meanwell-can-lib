# meanwell-can-lib for python
Tool to control Meanwell CAN Devices Charger / Power Supplys and Charger via CAN Bus

Tested with the Version BIC-2200-CAN-24 and NPB-1200-24 PSU/Charger

Please note:  
This python lib and tool controls read and write settings to the CAN device.</br>
It is not yet complete and also not fully tested. </br>
Do not use without monitoring the device. </br>
There is no error handling yet !!!</br>
Use at your own risk !</br>
</br>
Note: Do not modify the mycan.ini file ! This is for general information, not for configuration !</br>

mwcancmd.py sample application

	   Usage: ./mwcancmd.py parameter value
       To use a standalone cmd to the mw device
	   
       on                   -- output on
       off                  -- output off

       cvread               -- read charge voltage setting
       cvset <value>        -- set charge voltage
       ccread               -- read charge current setting
       ccset <value>        -- set charge current

       dvread               -- read discharge voltage setting
       dvset <value>        -- set discharge voltage
       dcread               -- read discharge current setting
       dcset <value>        -- set discharge current

       vread                -- read DC voltage
       cread                -- read DC current
       acvread              -- read AC voltage

       charge               -- set direction charge battery
       discharge            -- set direction discharge battery

       tempread             -- read power supply temperature

       <value> = amps oder volts * 100 --> 25,66V = 2566 
        
All scripts are without any warranty. Use at your own risk
