powerspy.py
===========

**powerspy.py** is a utility script to measure voltage, current and power in real time using the [Alciom](http://www.alciom.com/) PowerSpy device.

## Prerequisites:

1. [Required] powerspy.py requires python bluez to communicate using bluetooth with the device. It can be installed on Ubuntu using the following command:

		apt-get install python-bluez

2. [Optional, recommended] set up your bluetooth device to connect automatically without asking for PIN.
This can be done by modifying or creating /var/lib/bluetooth/DEVICE/pincodes with the following content: 

		POWERSPY PIN

POWERSPY and DEVICE are the device addresses of the Powerspy and the bluetooth receiver. They can be found with the commands 

		hcitool scan 

and 

		hcitool dev 

respectively.
Then, restart bluetooth:

	sudo restart bluetooth


## Getting started

Use 'powerspy.py -h' to get more information on how to run the utility.


Example of use:

		./powerspy.py 00:0B:CE:07:1D:32

## License

	powerspy.py is free software; you can redistribute it and/or modify it under
	the terms of the Lesser GNU Lesser General Public License as published by
	the Free Software Foundation; either version 3 of the License, or
	(at your option) any later version.
	
	powerspy.py is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	Lesser GNU Lesser General Public License for more details.
	
	You should have received a copy of the Lesser GNU Lesser General Public License
	along with powerspy.py.  If not, see <http://www.gnu.org/licenses/>

-- The strawberry growers team.
