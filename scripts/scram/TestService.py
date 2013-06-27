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
    """
    This is the main function for testing to see if the service is up and for scoring
    We need to talk to the service and stash a flag, then call back at a later time to get the flag
    Our scram game is websocket based so this client needs to grok websockets
    The idea is to call the service, get the old flag, set the new flag
        - sys.exit controls success or failures; see the funcs above
        - this script is run on the command line via the task scheduler as a sevice task
        - make sure to have #!/usr/bin/python -u since we need to flush stdout
    """
    # get old flag
    oldFlag = ""
    if cookie != None:
        eaddr, caseid = cookie.split(":")
        try:
            pass
                
        except Exception, e:
            print "ERROR: got exception '%s' when getting flag" % (e)
            sys.exit(1)
        
    # set new flag
    try:
        pass
    
    except Exception, e:
        print "ERROR: got exception '%s' when setting flag" % (e)
        return

if __name__ == "__main__":
    CtfUtil.main(score)
