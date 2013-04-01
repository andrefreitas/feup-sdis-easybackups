==== README ====
EasyBackup is a cross-plataform application developed in Python to do Backups in 
a P2P Architecture. Every peer have a daemon that is running in background and 
listening and processing requests in multi-threading. All the configurations of 
the daemon are in the file "settings.cfg". By default a Peer offer 5 GB of space 
to receive backups requests from another peers. 

==== AUTHORS ====
This project was done by two MIEIC students: Ana Gomes and Andre Freitas in the 
Distributed Systems course.

==== THANKS ====
We would like to thank all the teachers support and their availability to answer all 
the questions we had. It was a great journey and we learned a lot. 

==== INSTALL ====
Extract the zip and put the folder wherever you want. If you are in Windows or Mac, 
please download and install  Python 2.7 in http://www.python.org/download/ in case 
you don't have it yet.

==== RUN ====
To start EasyBackup you just need to run the "easybackupd.py" that is the Daemon. 
To request backups and so on, run the "easybackups.py" that is the Shell, whenever 
you want. There is an "help" command to retrieve the list of actions available.