gator
=====

Hydra ISF and quakeML aggreGATOR

Installation:
=====
Run: python setup.py

The configuration file should be installed in $HOME/gator.ini by the setup process.

Config file should look something like this:

>[CONFIG]
>
>#filename extensions for the ISF and quakeml files
>ISF_EXTENSION = ISF_Verified
>
>QUAKEML_EXTENSION = quakeml_Verified
>
>#location of the output Hydra data
>PDEFOLDER = F:\Hydra\Output\PDE
>
>#time since last file update - in minutes
>TIMEWINDOW = 4
>
>#FTP url where output will be transferred
>SERVER = ftp://ftpint.usgs.gov/pub/cr/co/golden/idc

Usage:
=====
usage: aggregate.py [-h] [-n]

Concatenate and transfer Hydra output files to FTP.

optional arguments:<br/>
  -h, --help      show this help message and exit<br/>
  -n, --no-clean  Do NOT delete input files after transfer
