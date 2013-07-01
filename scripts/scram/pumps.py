#!/usr/bin/python -u

from utility import CtfUtil
from utility.flagclient import FlagClient

if __name__ == "__main__":
    flagClient = FlagClient(port=8083)
    CtfUtil.main(flagClient.score)