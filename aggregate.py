#!/usr/bin/env python

#stdlib imports
import urlparse
import ftplib
import os.path
import ConfigParser
import sys
import datetime
import zipfile
import argparse

CONFIG = 'gator.ini'

def pushFiles(filenames,ftpstr):
    try:
        urlparts = urlparse.urlparse(ftpstr)
        ftp = ftplib.FTP(urlparts.netloc)
        ftp.login()
        dirparts = urlparts.path.strip('/').split('/')
        for d in dirparts:
            try:
                ftp.cwd(d)
            except ftplib.error_perm,msg:
                try:
                    ftp.mkd(d)
                    ftp.cwd(d)
                except ftplib.error_perm,msg:
                    raise Exception,msg
        for filename in filenames:
            pname,fname = os.path.split(filename)
            cmd = "STOR " + fname
            try:
                wd = os.getcwd()
                os.chdir(pname)
                ftp.storbinary(cmd,open(fname,"rb"),1024) #actually send the file
                os.chdir(wd)
            except Exception,msg:
                os.chdir(wd)
        ftp.quit()
    except Exception,msg:
        raise Exception,msg

    urlpaths = []
    for file in filenames:
        p,f = os.path.split(filename)
        if not ftpstr.endswith('/'):
            ftpstr = ftpstr+'/'
        urlpath = urlparse.urljoin(ftpstr,f)
        urlpaths.append(urlpath)
    return urlpaths

def getWeeks(pdefolder,isfext,quakeext):
    allfiles = os.listdir(pdefolder)
    weeks = {}
    for tfile in allfiles:
        fullfile = os.path.join(pdefolder,tfile)
        if fullfile.endswith(isfext):
            ftype = 'isf'
        elif fullfile.endswith(quakeext):
            ftype = 'quakeml'
        else: #unknown file type - skip it
            continue
        ftime = datetime.datetime.fromtimestamp(os.path.getmtime(fullfile))
        parts = tfile.split('_')
        week = parts[0]
        if week not in weeks.keys():
            if ftype == 'isf':
                weeks[week] = ([fullfile],[],ftime)
            else:
                weeks[week] = ([],[fullfile],ftime)
        else:
            isffiles,quakemlfiles,weektime = weeks[week]
            if ftype == 'isf':
                isffiles.append(fullfile)
            else:
                quakemlfiles.append(fullfile)
            if ftime > weektime:
                weektime = ftime
            weeks[week] = (isffiles,quakemlfiles,weektime)
            
    return weeks

def aggregateFiles(week,isffiles,quakemlfiles):
    pdepath,pdefile = os.path.split(isffiles[0])
    mycatfile = os.path.join(pdepath,'%s_cat.isf' % week)
    myzipfile = os.path.join(pdepath,'%s_cat_quakeml.zip' % week)
    fcat = open(mycatfile,'wt')
    for ifile in isffiles:
        fcat.write(open(ifile,'rt').read())
    fcat.close()
    myzip = zipfile.ZipFile(myzipfile,'w',zipfile.ZIP_DEFLATED)
    for qfile in quakemlfiles:
        arcpath,arcname = os.path.split(qfile)
        myzip.write(qfile,arcname)
    myzip.close()
    return (mycatfile,myzipfile)

def main(args):
    tnow = datetime.datetime.now()
    thisdir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
    homedir = os.path.expanduser('~')
    thiscfg = os.path.join(thisdir,CONFIG)
    homecfg = os.path.join(homedir,CONFIG)
    if not os.path.isfile(thiscfg) and not os.path.isfile(homecfg):
        print 'Cannot find a config file in either %s or %s. Exiting.'
        sys.exit(1)
    if os.path.isfile(thiscfg):
        configfile = thiscfg
    else:
        configfile = homecfg
    config = ConfigParser.ConfigParser()
    config.readfp(open(configfile))
    pdefolder = config.get('CONFIG','PDEFOLDER')
    timewindow = int(config.get('CONFIG','TIMEWINDOW'))*60 #we want this time window in minutes
    ftpserver = config.get('CONFIG','SERVER')
    isf_extension = config.get('CONFIG','ISF_EXTENSION')
    quakeml_extension = config.get('CONFIG','QUAKEML_EXTENSION')
    weeks = getWeeks(pdefolder,isf_extension,quakeml_extension)
    for week,weekdata in weeks.iteritems():
        isffiles,quakemlfiles,updateTime = weekdata
        dt = tnow - updateTime
        dtseconds = dt.days*86400 + dt.seconds
        if dtseconds > timewindow:
            catfile,zipfile = aggregateFiles(week,isffiles,quakemlfiles)
            urlpaths = pushFiles([catfile,zipfile],ftpserver)
            os.remove(catfile)
            os.remove(zipfile)
            if not args.noClean:
                for ifile in isffiles:
                    os.remove(ifile)
                for qfile in quakemlfiles:
                    os.remove(qfile)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Concatenate and transfer Hydra output files to FTP.')
    parser.add_argument('-n','--no-clean',dest='noClean', default=False,action='store_true',
                        help='Do NOT delete input ISF and QuakeML files after transfer')
    arguments = parser.parse_args()
    main(arguments)
    
    
