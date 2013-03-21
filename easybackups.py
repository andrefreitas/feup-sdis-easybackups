from shell import Shell

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
        print "    - exit"
    elif (operation=="backup"):
        file_name=command[1]
        replication_degree=2
        if (len(command)==3):
            replication_degree=int(command[2])
        shell.backup_file(file_name, replication_degree)
        
    elif(operation=="exit"):
        break
        