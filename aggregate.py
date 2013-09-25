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
import subprocess
import glob

MYCONFIG = 'mygator.ini'
CONFIG = 'gator.ini'

def getCommandOutput(cmd):
    """
    Internal method for calling external command.
    @param cmd: String command ('ls -l', etc.)
    @return: Three-element tuple containing a boolean indicating success or failure, 
    the stdout from running the command, and stderr.
    """
    proc = subprocess.Popen(cmd,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                            )
    stdout,stderr = proc.communicate()
    retcode = proc.returncode
    if retcode == 0:
        retcode = True
    else:
        retcode = False
    return (retcode,stdout,stderr)

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

def getWeeks(isffolder,quakemlfolder,isfextension,quakemlextension):
    # isffiles = os.listdir(isffolder)
    # isffiles = [os.path.join(isffolder,ifile) for ifile in isffiles]
    isffiles = glob.glob(os.path.join(isffolder,'*.%s' % isfextension))
    # quakemlfiles = os.listdir(quakemlfolder)
    # quakemlfiles = [os.path.join(quakemlfolder,ifile) for ifile in quakemlfiles]
    quakemlfiles = glob.glob(os.path.join(quakemlfolder,'*.%s' % quakemlextension))
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

def writeLog(logfolder,state,catfile):
    tnow = datetime.datetime.utcnow()
    year = tnow.year
    month = tnow.month
    day = tnow.day
    logfilename = os.path.join(logfolder,'gator_%s.log' % tnow.strftime('%Y%m%d'))
    log = open(logfilename,'at')
    log.write('%s %s %s\n' % (state,tnow.strftime('%Y-%m-%dT%H:%M:%S'),catfile))
    log.close()

def pushWeeks(weeks,timewindow,mode,scpcmd,sshcmd,remote,logfolder,cleanUp=True,doCheck=False):
    tnow = datetime.datetime.now()
    for week,weekdata in weeks.iteritems():
        files,updateTime = weekdata
        dt = tnow - updateTime
        dtseconds = dt.days*86400 + dt.seconds
        if dtseconds > timewindow:
            catfile = aggregate(week,files,mode)
            cmd = '%s "%s" %s' % (scpcmd,catfile,remote)
            res,out,err = getCommandOutput(cmd)
            print 'Command "%s" result was %s with stdout "%s" and stderr "%s"' % (cmd,res,out,err)
            if doCheck:
                fsize = os.stat(catfile).st_size
                rparts = remote.split(':')
                userinfo = rparts[0]
                lpath,lfile = os.path.split(catfile)
                remotefile = os.path.join(rparts[1],lfile)
                cmd = '%s %s ls -l %s' % (sshcmd,userinfo,remotefile)
                res,out,err = getCommandOutput(cmd)
                print 'Command "%s" result was %s with stdout "%s" and stderr "%s"' % (cmd,res,out,err)
                rfsize = int(out.split()[4])
                if rfsize == fsize: #successful transfer
                    writeLog(logfolder,'INFO',catfile)
                else: #unsuccessful transfer
                    writeLog(logfolder,'ERROR',catfile)
                    cleanUp = False #don't delete the source files when something's wrong
            else:
                if res:
                    writeLog(logfolder,'INFO',catfile)
                else: #unsuccessful transfer
                    writeLog(logfolder,'ERROR',catfile)
                    cleanUp = False #don't delete the source files when something's wrong
            #do something like pssh user@remote md5sum
            os.remove(catfile)
            if cleanUp:
                for f in files:
                    os.remove(f)

def main(args):
    tnow = datetime.datetime.now()
    thisdir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
    homedir = os.path.expanduser('~')
    mycfg = os.path.join(thisdir,MYCONFIG)
    thiscfg = os.path.join(thisdir,CONFIG)
    homecfg = os.path.join(homedir,CONFIG)
    if not os.path.isfile(thiscfg) and not os.path.isfile(mycfg) and not os.path.isfile(homecfg):
        print 'Cannot find a config file in either %s, %s or %s. Exiting.' % (mycfg,thiscfg,homecfg)
        sys.exit(1)
    if os.path.isfile(mycfg):
        configfile = mycfg
    elif os.path.isfile(thiscfg):
        configfile = thiscfg
    else:
        configfile = homecfg
    config = ConfigParser.ConfigParser()
    config.readfp(open(configfile))
    isffolder = config.get('CONFIG','ISFFOLDER')
    quakemlfolder = config.get('CONFIG','QUAKEMLFOLDER')
    isfext = config.get('CONFIG','ISF_EXTENSION')
    quakemlext = config.get('CONFIG','QUAKEML_EXTENSION')
    timewindow = int(config.get('CONFIG','TIMEWINDOW'))*60 #we want this time window in minutes
    logfolder = config.get('CONFIG','LOGFOLDER')

    #get all of the information about the scp process
    scpcmd = config.get('CONFIG','COPY_EXE')
    sshcmd = config.get('CONFIG','SSH_EXE')
    remote = config.get('CONFIG','REMOTE_SYSTEM')
    user = config.get('CONFIG','COPY_USER')
    remoteroot = config.get('CONFIG','REMOTE_ROOT_FOLDER')
    remoteisf = '%s@%s:%s' % (user,remote,os.path.join(remoteroot,config.get('CONFIG','REMOTE_ISF_FOLDER')))
    remotequake = '%s@%s:%s' % (user,remote,os.path.join(remoteroot,config.get('CONFIG','REMOTE_QUAKEML_FOLDER')))

    #get toggle state for whether we want to check remote file size
    doCheck = bool(int(config.get('CONFIG','DOCHECK')))

    #get the information about the data that we have, and then push it
    quakeweeks,isfweeks = getWeeks(isffolder,quakemlfolder,isfext,quakemlext)
    pushWeeks(quakeweeks,timewindow,'quakeml',scpcmd,sshcmd,remotequake,logfolder,cleanUp=not args.noClean,doCheck=doCheck)
    pushWeeks(isfweeks,timewindow,'isf',scpcmd,sshcmd,remoteisf,logfolder,cleanUp=not args.noClean,doCheck=doCheck)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Concatenate and transfer Hydra output files to FTP.')
    parser.add_argument('-n','--no-clean',dest='noClean', default=False,action='store_true',
                        help='Do NOT delete input ISF and QuakeML files after transfer')
    arguments = parser.parse_args()
    main(arguments)
    
    
