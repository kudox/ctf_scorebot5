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
    return

if __name__ == "__main__":
    CtfUtil.main(score)