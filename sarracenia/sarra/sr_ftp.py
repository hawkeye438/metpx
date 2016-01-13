#!/usr/bin/python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# sarracenia repository: git://git.code.sf.net/p/metpx/git
# Documentation: http://metpx.sourceforge.net/#SarraDocumentation
#
# sr_ftp.py : python3 utility tools for ftp usage in sarracenia
#             Since python3.2 supports ftps (RFC 4217)
#             I tested it and works for all our ftps pull/sender as of today
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Dec 30 11:34:07 EST 2015
#
########################################################################
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful, 
#  but WITHOUT ANY WARRANTY; without even the implied warranty of 
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA
#

import ftplib,os,sys,time

#============================================================
# ftp protocol in sarracenia supports/uses :
#
# connect
# close
#
# if a source    : get    (remote,local)
#                  ls     ()
#                  cd     (dir)
#                  delete (path)
#
# if a sender    : put    (local,remote)
#                  cd     (dir)
#                  mkdir  (dir)
#                  umask  ()
#                  chmod  (perm)
#                  rename (old,new)
#
# FTP : no remote file seek... so 'I' part impossible
#

class sr_ftp():
    def __init__(self, parent) :
        self.logger = parent.logger
        self.logger.debug("sr_ftp __init__")

        self.parent      = parent 
        self.connected   = False 
        self.ftp         = None

    # cd
    def cd(self, path):
        self.logger.debug("sr_ftp cd %s" % path)
        self.ftp.cwd(self.originalDir)
        self.ftp.cwd(path)
        self.pwd = path

    def cd_forced(self,perm,path) :
        self.logger.debug("sr_ftp cd_forced %d %s" % (perm,path))

        # try to go directly to path

        self.ftp.cwd(self.originalDir)
        try   :
                self.ftp.cwd(path)
                return
        except: pass

        # need to create subdir

        subdirs = path.split("/")
        if path[0:1] == "/" : subdirs[0] = "/" + subdirs[0]

        for d in subdirs :
            if d == ''   : continue
            # try to go directly to subdir
            try   :
                    self.ftp.cwd(d)
                    continue
            except: pass

            # create and go to subdir
            self.ftp.mkd(d)
            self.ftp.voidcmd('SITE CHMOD ' + str(perm) + ' ' + d)
            self.ftp.cwd(d)

    # chmod
    def chmod(self,perm,path):
        self.logger.debug("sr_ftp chmod %s %s" % (str(perm),path))
        self.ftp.voidcmd('SITE CHMOD ' + str(perm) + ' ' + path)

    # close
    def close(self):
        self.logger.debug("sr_ftp close")
        self.connected = False
        if self.ftp == None : return
        self.ftp.quit()

    # connect...
    def connect(self):
        self.logger.debug("sr_ftp connect %s" % self.parent.destination)

        self.connected   = False
        self.destination = self.parent.destination

        try:
                ok, details = self.parent.credentials.get(self.destination)
                if details  : url = details.url

                host        = url.hostname
                port        = url.port
                user        = url.username
                password    = url.password
                passive     = details.passive
                self.binary = details.binary
                self.tls    = details.tls
                self.prot_p = details.prot_p

                self.bufsize   = 8192
                self.kbytes_ps = 0

                if hasattr(self.parent,'kbytes_ps') : self.kbytes_ps = self.parent.kbytes_ps
                if hasattr(self.parent,'bufsize')   : self.bufsize   = self.parent.bufsize

        except:
                (stype, svalue, tb) = sys.exc_info()
                self.logger.error("Unable to get credentials for %s" % self.destination)
                self.logger.error("(Type: %s, Value: %s)" % (stype ,svalue))
                return False

        try:
                if port == '' or port == None : port = 21

                if not self.tls :
                   ftp = ftplib.FTP()
                   ftp.connect(host,port,timeout=-999)
                   ftp.login(user, password)
                else :
                   # ftplib supports FTPS with TLS 
                   ftp = ftplib.FTP_TLS(host,user,password,timeout=None)
                   if self.prot_p : ftp.prot_p()
                   # needed only if prot_p then set back to prot_c
                   #else          : ftp.prot_c()

                ftp.set_pasv(passive)

                self.originalDir = '.'

                try   : self.originalDir = ftp.pwd()
                except:
                        (stype, svalue, tb) = sys.exc_info()
                        self.logger.warning("Unable to ftp.pwd (Type: %s, Value: %s)" % (stype ,svalue))

                self.pwd = self.originalDir

                self.connected = True

                self.ftp = ftp

                return True

        except:
            (stype, svalue, tb) = sys.exc_info()
            self.logger.error("Unable to connect to %s (user:%s). Type: %s, Value: %s" % (host,user, stype,svalue))
        return False

    # delete
    def delete(self, path):
        self.logger.debug("sr_ftp rm %s" % path)
        self.ftp.delete(path)

    # get
    def get(self, remote_file, local_file, remote_offset=0, local_offset=0, length=0):
        self.logger.debug("sr_ftp get %s %s %d" % (remote_file,local_file,local_offset))
        if not os.path.isfile(local_file) :
           fp = open(local_file,'w')
           fp.close()

        # fixme : get trottled.... instead of fp.write... call get_trottle(buf) which calls fp.write
        if self.binary :
           fp = open(local_file,'r+b')
           if local_offset != 0 : fp.seek(local_offset,0)
           self.ftp.retrbinary('RETR ' + remote_file, fp.write, self.bufsize )
           fp.close()
        else :
           fp = open(local_file,'r+')
           if local_offset != 0 : fp.seek(local_offset,0)
           self.ftp.retrlines ('RETR ' + remote_file, fp.write )
           fp.close()

    # ls
    def ls(self):
        self.logger.debug("sr_ftp ls")
        self.entries = {}
        self.ftp.retrlines('LIST',self.line_callback )
        self.logger.debug("sr_ftp ls = %s" % self.entries )
        return self.entries

    # line_callback: entries[filename] = 'stripped_file_description'
    def line_callback(self,iline):
        self.logger.debug("sr_ftp line_callback %s" % iline)

        oline  = iline
        oline  = oline.strip('\n')
        oline  = oline.strip()
        oline  = oline.replace('\t',' ')
        opart1 = oline.split(' ')
        opart2 = []

        for p in opart1 :
            if p == ''  : continue
            opart2.append(p)

        fil  = opart2[-1]
        line = ' '.join(opart2)

        self.entries[fil] = line

    # mkdir
    def mkdir(self, remote_dir):
        self.logger.debug("sr_ftp mkdir %s" % remote_dir)
        self.ftp.mkd(remote_dir)

    # put
    def put(self, local_file, remote_file, local_offset = 0, remote_offset = 0, length = 0):
        self.logger.debug("sr_ftp put %s %s" % (local_file,remote_file))
        cb        = None

        if self.kbytes_ps > 0.0 :
           cb = self.trottle
           d1,d2,d3,d4,now = os.times()
           self.tbytes     = 0.0
           self.tbegin     = now + 0.0
           self.bytes_ps   = self.kbytes_ps * 1024.0

        if self.binary :
           fp = open(local_file, 'rb')
           if local_offset != 0 : fp.seek(local_offset,0)
           self.ftp.storbinary("STOR " + remote_file, fp, self.bufsize, cb)
           fp.close()
        else :
           fp=open(local_file,'r')
           if local_offset != 0 : fp.seek(local_offset,0)
           self.ftp.storlines ("STOR " + remote_file, fp, cb)
           fp.close()

    # rename
    def rename(self,remote_old,remote_new) :
        self.logger.debug("sr_ftp rename %s %s" % (remote_old,remote_new))
        self.ftp.rename(remote_old,remote_new)

    # rmdir
    def rmdir(self, path):
        self.logger.debug("sr_ftp rmdir %s" % path)
        self.ftp.rmd(path)

    # trottle
    def trottle(self,buf) :
        self.logger.debug("sr_ftp trottle")
        self.tbytes = self.tbytes + len(buf)
        span = self.tbytes / self.bytes_ps
        d1,d2,d3,d4,now = os.times()
        rspan = now - self.tbegin
        if span > rspan :
           time.sleep(span-rspan)

    # umask
    def umask(self) :
        self.logger.debug("sr_ftp umask")
        self.ftp.voidcmd('SITE UMASK 777')


#============================================================
#
# wrapping of sr_ftp in ftp_download
#
#============================================================

def ftp_download( parent ):
    logger = parent.logger
    msg    = parent.msg

    # seek not supported
    if msg.partflg == 'i' :
       logger.error("ftp, inplace part file not supported")
       msg.log_publish(499,'ftp download problem')
       return False

    url         = msg.url
    urlstr      = msg.urlstr
    token       = msg.url.path[1:].split('/')
    cdir        = '/'.join(token[:-1])
    remote_file = token[-1]

    try :
            parent.destination = msg.urlcred
            ftp = sr_ftp(parent)
            ftp.connect()
            ftp.cd(cdir)

            #download file
            logger.info('Downloads: %s into %s %d-%d' % 
                       (urlstr,msg.local_file,msg.local_offset,msg.local_offset+msg.length-1))

            ftp.get(remote_file,msg.local_file,msg.local_offset)

            msg.log_publish(201,'Downloaded')

            ftp.close()

            return True
            
    except:
            try    : ftp.close()
            except : pass

            (stype, svalue, tb) = sys.exc_info()
            msg.logger.error("Download failed %s. Type: %s, Value: %s" % (urlstr, stype ,svalue))
            msg.log_publish(499,'ftp download problem')

            return False

    msg.log_publish(499,'ftp download problem')

    return False

#============================================================
#
# wrapping of sr_ftp in ftp_send
#
#============================================================

def ftp_send( parent ):
    logger = parent.logger
    msg    = parent.msg

    local_file = parent.local_path
    remote_dir = parent.remote_dir

    try :
            ftp = sr_ftp(parent)
            ftp.connect()

            ftp.cd_forced(775,remote_dir)

            offset = 0

            # 'i' cannot be supported by ftp/ftps
            # we cannot offset in the remote file to inject data
            #
            # FIXME instead of dropping the message
            # the inplace part could be delivered as 
            # a separate partfile and message set to 'p'
            if  msg.partflg == 'i':
                logger.error("ftp, inplace part file not supported")
                msg.log_publish(499,'ftp delivery problem')
                return False

            str_range = ''

            # deliver file

            msg.logger.info('Sends: %s %s into %s %d-%d' % 
                (parent.local_file,str_range,parent.remote_path,offset,offset+msg.length-1))

            if parent.lock == None :
               ftp.put(local_file, parent.remote_file)
            elif parent.lock == '.' :
               remote_lock = '.'  + parent.remote_file
               ftp.put(local_file, remote_lock)
               ftp.rename(remote_lock, parent.remote_file)
            elif parent.lock[0] == '.' :
               remote_lock = parent.remote_file + parent.lock
               ftp.put(local_file, remote_lock)
               ftp.rename(remote_lock, parent.remote_file)
            elif parent.lock == 'umask' :
               ftp.umask()
               ftp.put(local_file, parent.remote_file)

            try   : ftp.chmod(parent.chmod,parent.remote_file)
            except: pass

            msg.log_publish(201,'Delivered')

            ftp.close()

            return True
            
    except:
            try    : ftp.close()
            except : pass

            (stype, svalue, tb) = sys.exc_info()
            msg.logger.error("Delivery failed %s. Type: %s, Value: %s" % (parent.remote_urlstr, stype ,svalue))
            msg.log_publish(499,'ftp delivery problem')

            return False

    msg.log_publish(499,'ftp delivery problem')

    return False
                 
                 

# ===================================
# self_test
# ===================================

try    : from sr_config         import *
except : from sarra.sr_config   import *

class test_logger:
      def silence(self,str):
          pass
      def __init__(self):
          self.debug   = self.silence
          self.error   = print
          self.info    = self.silence
          self.warning = print

def self_test():

    logger = test_logger()

    # config setup
    cfg = sr_config()
    cfg.defaults()
    cfg.general()
    cfg.debug  = True
    opt1 = "destination ftp://localhost"
    cfg.option( opt1.split()  )
    cfg.logger = logger

    try:
           ftp = sr_ftp(cfg)
           ftp.connect()
           ftp.mkdir("tztz")
           ftp.chmod(775,"tztz")
           ftp.cd("tztz")
       
           ftp.umask()
           f = open("aaa","wb")
           f.write(b"1\n")
           f.write(b"2\n")
           f.write(b"3\n")
           f.close()
       
           ftp.put("aaa", "bbb")
           ls = ftp.ls()
           logger.info("ls = %s" % ls )
       
           ftp.chmod(775,"bbb")
           ls = ftp.ls()
           logger.info("ls = %s" % ls )
       
           ftp.rename("bbb", "ccc")
           ls = ftp.ls()
           logger.info("ls = %s" % ls )
       
           ftp.get("ccc", "bbb")
           f = open("bbb","rb")
           data = f.read()
           f.close()
       
           if data != b"1\n2\n3\n" :
              logger.error("sr_ftp TEST FAILED")
              sys.exit(1)
       
           ftp.delete("ccc")
           logger.info("%s" % ftp.originalDir)
           ftp.cd("")
           logger.info("%s" % ftp.ftp.pwd())
           ftp.rmdir("tztz")
       
           ftp.close()
    except:
           logger.error("sr_ftp TEST FAILED")
           sys.exit(2)

    os.unlink('aaa')
    os.unlink('bbb')

    print("sr_ftp TEST PASSED")
    sys.exit(0)

# ===================================
# MAIN
# ===================================

def main():

    self_test()
    sys.exit(0)

# =========================================
# direct invocation : self testing
# =========================================

if __name__=="__main__":
   main()
