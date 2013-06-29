#!/usr/bin/python -u

import os, random, time, sys, string

from utility import pybrowse, browserpersonality, CtfUtil
    
def fail():    
    sys.exit(2)
    
def alsoFail():    
    sys.exit(1)
    
def success():    
    sys.exit(0)
       
def score(ip,flag,cookie):
    fd = os.open("./var/"+ip+".txt",os.O_RDWR | os.O_CREAT)
    f = os.fdopen(fd,"r+")
    #s = ip+" "+flag
    

    # get old flag
    oldFlag = ""

    if cookie != None:
        oldFlag = f.read()
        print "FLAG:",oldFlag
        
    # set new flag
    #cookie = eaddr + ":" + caseid
    eaddr = 'rob@test.com'
    cookie = eaddr + ":" + "caseid"
    f.seek(0)
    f.write(flag)
    f.truncate()
    print "COOKIE:",cookie
    f.close()

if __name__ == "__main__":
    CtfUtil.main(score)