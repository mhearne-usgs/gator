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
>\#filename extensions for the ISF and quakeml files<br/>
>ISF_EXTENSION = ISF_Verified<br/>
>
>QUAKEML_EXTENSION = quakeml_Verified<br/>
>
>\#location of the output Hydra data<br/>
>PDEFOLDER = F:\Hydra\Output\PDE<br/>
>
>\#time since last file update - in minutes<br/>
>TIMEWINDOW = 4<br/>
>
>\#FTP url where output will be transferred<br/>
>SERVER = ftp://ftpint.usgs.gov/pub/cr/co/golden/idc<br/>

Usage:
=====
usage: aggregate.py [-h] [-n]

Concatenate and transfer Hydra output files to FTP.

optional arguments:<br/>
  -h, --help      show this help message and exit<br/>
  -n, --no-clean  Do NOT delete input files after transfer
