gator
=====

Hydra ISF and quakeML aggreGATOR

Installation:
=====
Run: python setup.py

The configuration file should be installed in $HOME/gator.ini by the setup process.

Config file should look something like this:
<pre>
[CONFIG]

#filename extensions for the ISF and quakeml files
ISF_EXTENSION = ISF_Verified

QUAKEML_EXTENSION = quakeml_Verified

#location of the output Hydra data
ISFFOLDER = F:\Hydra\Output\PDE\ISF
QUAKEMLFOLDER = F:\Hydra\Output\quakeML

#time since last file update - in minutes
TIMEWINDOW = 4

#FTP url where output will be transferred
SERVER = ftp://ftpint.usgs.gov/pub/cr/co/golden/idc
</pre>

Usage:
=====
<pre>
usage: aggregate.py [-h] [-n] [-w]

Concatenate and transfer Hydra output files to FTP.

optional arguments:
  -h, --help      show this help message and exit
  -n, --no-clean  Do NOT delete input ISF and QuakeML files after transfer
  -w, --wipe-ftp  Wipe out all files on destination FTP folder (use with
                  caution!)
</pre>
