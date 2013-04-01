"""
 Easy Backup Shell
 Authors: Ana Gomes, Andre Freitas
 Description: This is a class that runs the shell to manage the peer. 
 It uses the Shell class that is the core.
"""
from shell import Shell
import os
print "Welcome to Easy Backup Shell!"
print "Type \"help\" to see available commands"
shell=Shell()

# Read commands
while(True):
    command=raw_input("> ").split(" ")
    operation=command[0]
    if (operation == "help"):
        print "    - backup <file> (<replication degree>)"
        print "    - restore <file>"
        print "    - delete <file>"
        print "    - delete2 <file> : enhancement of delete"
        print "    - exit"
    elif (operation=="backup"):
        file_name=command[1]
        
        replication_degree=2
        if (len(command)==3):
            replication_degree=int(command[2])
        if(os.path.exists(file_name)):
            shell.backup_file(file_name, replication_degree)
        else:
            print "ERROR - Invalid file path"
    elif (operation=="restore"):
        file_name=command[1]
        shell.restore_file(file_name)
    elif (operation=="delete"):
        file_name=command[1]
        shell.delete_file(file_name)
    elif (operation=="delete2"):
        file_name=command[1]
        shell.delete2_file(file_name)
    elif(operation=="exit"):
        break
        