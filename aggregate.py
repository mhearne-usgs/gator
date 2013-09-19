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

def wipeFTP(ftpserver):
    urlparts = urlparse.urlparse(ftpserver)
    ftp = ftplib.FTP(urlparts.netloc)
    ftp.login()
    dirparts = urlparts.path.strip('/').split('/')
    for d in dirparts:
        try:
            ftp.cwd(d)
        except ftplib.error_perm,msg:
            raise Exception,msg
    ftpfiles = ftp.nlst()
    for f in ftpfiles:
        ftp.delete(f)
        continue
    return len(ftpfiles)

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
            ftp.storbinary(cmd,open(filename,"rb"),1024) #actually send the file
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

def getWeekInfo(flist):
    weeks = {}
    for fullfile in flist:
        ftime = datetime.datetime.fromtimestamp(os.path.getmtime(fullfile))
        fpath,tfile = os.path.split(fullfile)
        parts = tfile.split('_')
        week = parts[0]
        if week not in weeks.keys():
            weeks[week] = ([fullfile],ftime)
        else:
            tfiles,weektime = weeks[week]
            if ftime > weektime:
                weektime = ftime
            tfiles.append(fullfile)
            weeks[week] = (tfiles,weektime)
    return weeks

def getWeeks(isffolder,quakemlfolder):
    isffiles = os.listdir(isffolder)
    isffiles = [os.path.join(isffolder,ifile) for ifile in isffiles]
    quakemlfiles = os.listdir(quakemlfolder)
    quakemlfiles = [os.path.join(quakemlfolder,ifile) for ifile in quakemlfiles]
    isfweeks = getWeekInfo(isffiles)
    quakeweeks = getWeekInfo(quakemlfiles)
    return (quakeweeks,isfweeks)

def aggregate(week,files,mode):
    ppath,pfile = os.path.split(files[0])
    if mode == 'quakeml':
        mycatfile = os.path.join(ppath,'%s_cat_quakeml.zip' % week)
        myzip = zipfile.ZipFile(mycatfile,'w',zipfile.ZIP_DEFLATED)
        for qfile in files:
            arcpath,arcname = os.path.split(qfile)
            myzip.write(qfile,arcname)
        myzip.close()
    else:
        mycatfile = os.path.join(ppath,'%s_cat.isf' % week)
        fcat = open(mycatfile,'wt')
        for ifile in files:
            fcat.write(open(ifile,'rt').read())
        fcat.close()
    
    return mycatfile

def pushWeeks(weeks,timewindow,mode,ftpserver,cleanUp=True):
    tnow = datetime.datetime.now()
    for week,weekdata in weeks.iteritems():
        files,updateTime = weekdata
        dt = tnow - updateTime
        dtseconds = dt.days*86400 + dt.seconds
        if dtseconds > timewindow:
            catfile = aggregate(week,files,mode)
            urlpaths = pushFiles([catfile],ftpserver)
            os.remove(catfile)
            if cleanUp:
                for f in files:
                    os.remove(f)

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
    isffolder = config.get('CONFIG','ISFFOLDER')
    quakemlfolder = config.get('CONFIG','QUAKEMLFOLDER')
    timewindow = int(config.get('CONFIG','TIMEWINDOW'))*60 #we want this time window in minutes
    ftpserver = config.get('CONFIG','SERVER')

    #if they want to wipe out the ftp, do that and then quit
    if args.wipeFTP:
        resp = raw_input('Are you sure you want to erase the contents of FTP folder %s? y/[n] ' % ftpserver)
        if resp.strip().lower() != 'y':
            sys.exit(0)
        ndeleted = wipeFTP(ftpserver)
        print '%i files deleted.  Exiting.' % ndeleted
        sys.exit(0)
    
    quakeweeks,isfweeks = getWeeks(isffolder,quakemlfolder)
    isfloc = urlparse.urljoin(ftpserver,config.get('CONFIG','FTPISF'))
    quakeloc = urlparse.urljoin(ftpserver,config.get('CONFIG','FTPQUAKEML'))
    pushWeeks(quakeweeks,timewindow,'quakeml',quakeloc,cleanUp=not args.noClean)
    pushWeeks(isfweeks,timewindow,'isf',isfloc,cleanUp=not args.noClean)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Concatenate and transfer Hydra output files to FTP.')
    parser.add_argument('-n','--no-clean',dest='noClean', default=False,action='store_true',
                        help='Do NOT delete input ISF and QuakeML files after transfer')
    parser.add_argument('-w','--wipe-ftp',dest='wipeFTP', default=False,action='store_true',
                        help='Wipe out all files on destination FTP folder (use with caution!)')
    arguments = parser.parse_args()
    main(arguments)
    
    
