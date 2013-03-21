from peer import Peer
from os.path import expanduser
import ConfigParser

""" This module runs the EasyBackup Daemon """

# Read Configurations
config = ConfigParser.ConfigParser()
try:
    config.readfp(open('settings.cfg'))
    easybackup_home = expanduser("~") + "/easybackup"
    mc_address=config.get("MC", "mc_address")
    mc_port=config.getint("MC", "mc_port")
    mdb_address=config.get("MDB", "mdb_address")
    mdb_port=config.getint("MDB", "mdb_port")
    mdr_address=config.get("MDR", "mdr_address")
    mdr_port=config.getint("MDR", "mdr_port")
    shell_port=config.getint("SHELL", "shell_port")
    # Init peer daemon
    p=Peer(easybackup_home , mc_address, mc_port, mdb_address, mdb_port, mdr_address, mdr_port,shell_port)
    p.listen_all()
    
except:
    print "Please run easybackupd.py from the folder..."
    raw_input()