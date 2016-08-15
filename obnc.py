###################################################################################
# obnc @ opensource irc bouncer @ https://github.com/m5it/obnc 2016
###################################################################################

import time
import datetime
import mysql.connector

import socket
import ssl
import threading
import SocketServer
import os
import hashlib
import getopt
import sys

import requests
import urllib
import re

from threading import Thread

###################################################################################
import f as f          # random functions
import f_net as fnet   # socket functions
import f_help as fhelp # usage
import f_bnc as fbnc   #
###################################################################################

server       = 0
server_port  = 11337
server_addr  = "0.0.0.0"
server_run   = 1

#irch="tepper.freenode.net"
#tepper.freenode.net[192.186.157.43/6667]

ircs="192.186.157.43"
ircp=6667
username="t3ch"
password="skrlat"

###
# SERVER FUNCTIONS
####   
#class threaded_server_handler(SocketServer.BaseRequestHandler):
class threaded_server_handler(SocketServer.StreamRequestHandler):
    def handle(self):
        global aClients, ircs, ircp
        
        self.request.settimeout(1)
        
        ### registration with bnc
        step =0
        x    =-1    # array position of client parameters
        
        ###
        run=1
        run_irc=1
        
        ###
        aclient=0
        auser=[]
        apass=[]
        anick=[]
        auserhost=[]
        amode=[]
        anickserv=[]
        
        while run:
            try:
                #self.data = self.request.recv(1024).strip()
                self.data = self.rfile.readline().strip()
                data = self.data
            
                if len(data)>0:
                    print "{} wrote: {}\n".format(self.client_address[0], data)
                    
                    ###
                    if step==0:
                        print "step 0"
                        # USER t3ch t3ch 127.0.0.1 :t3ch
                        if f.rmatch("USER.*",data)==1:
                            auser=data.split(" ") # user paramteres
                        elif f.rmatch("NICK.*",data)==1:
                            anick=data.split(" ") # irc nick parameters
                        elif f.rmatch("PASS.*",data)==1:
                            apass=data.split(" ") # irc server password
                    
                    ###
                    elif step==1:
                        print "step 1"
                        # waiting for autentication with obnc
                        #         
                        print "user: {}".format(auser[1])
                        if username==auser[1]:
                            print "username ok"
                            x=fbnc.client_search(username)
                            if x==-1:
                                print "creating new client"
                                aclient=fbnc.Clients(username)
                            else:
                                print "using aclient at: {}".format(x)
                                #aclient=aClients[x]
                                aclient=fbnc.client_get(x)
                            
                            step=2
                        else:
                            print "failed: userauth"
                                
                    ###
                    elif step==2:
                        print "step 2"
                        # waiting for authentication with password
                        # PRIVMSG obnc :pass:hello
                        if f.rmatch("PRIVMSG.*",data)==1:
                            tmppassword=":login:{}".format(password)
                            if aclient.password!="":
                                tmppassword=":login:{}".format(aclient.password)
                                
                            a=data.split(" ")
                            print "password match: {}=={}".format(a[2],tmppassword)
                            if a[2]==tmppassword:
                                print "logedin with password: {}".format(password)
                                aclient.password=password
                                aclient.online = 1
                                aclient.irc_user = auser[1]
                                aclient.irc_pass = apass[1]
                                aclient.irc_nick = anick[1]
                                step=3
                                
                                
                    ###
                    if step==3:
                        # bounc
                        print "step 3"
                        if aclient.socket==0:
                            aclient.socket=fbnc.init(apass[1], anick[1], auser[1], ircs, ircp)
                        
                            # save aclient
                            if x==-1:
                                #aClients.append( aclient )
                                x=fbnc.client_set(aclient,x)
                                #x=len(aClients)-1
                            else:
                                #aClients[x]=aclient
                                fbnc.client_set(aclient,x)
                        else:
                            print "reusing sockets at aclient x: {}".format(x)
                            fbnc.imaginary_join(self.request,x)

                        ###
                        while run_irc:
                            idata = fnet.recv_timeout( aclient.socket, 1)
                            if len(idata)>0:
                                print "idata: {}".format(idata)
                                self.request.sendall("{}\r\n".format(idata))
                            
                            cdata=""
                            try:
                                cdata = self.rfile.readline().strip()
                            except:
                                print "no cdata."
                                
                            if len(cdata)>0:
                                print "cdata: {}".format(cdata)
                                check=fbnc.handle_client_data(cdata,x)
                                if check==-1:
                                    print "client closed connection..."
                                    run_irc=0
                                    break
                                elif check==-2:
                                    print "client closed bnc... thread is still running?? :)"
                                    run_irc=0
                                    run_bnc=0
                                    break
                    
                    ### supported commands for bnc without authentication & connection with irc ###
                    if f.rmatch("PING.*",data)==1:
                        print "PONG!!!"
                        self.request.sendall("PONG\r\n")
            ### ###            
            except:
                if step==0:
                    print "step 0..."
                    # 
                    self.request.sendall(":obnc NOTICE * :*** Looking up your hostname...\r\n")
                    self.request.sendall(":obnc NOTICE * :*** Checking Ident\r\n")
                    self.request.sendall(":obnc NOTICE * :*** Couldn't look up your hostname\r\n")
                    self.request.sendall(":obnc NOTICE * :*** No Ident response\r\n")
                    self.request.sendall(":obnc 372 {} :Welcome to obnc, use password: /msg obnc login:your_password\r\n".format(anick[1]))
                    self.request.sendall(":obnc 376 {} :End of /MOTD command\r\n".format(anick[1]))
                    self.request.sendall(":{} MODE {} :+i\r\n".format(anick[1],anick[1]))
                    step=1
                
                print "except... step: {}".format(step)

                
class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass
    
      
###
def serv():
    global server, server_addr, server_port, server_run
    ###
    HOST, PORT = server_addr, server_port
    ThreadedTCPServer.allow_reuse_address = True
    server = ThreadedTCPServer((HOST,PORT), threaded_server_handler)
    ip, port = server.server_address

    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print "obnc v{} on thread: {}".format(fbnc.version, server_thread.name)
    
    ### 
    while server_run:
        time.sleep(2)
    
    print "obnc down."
    server.shutdown()
    server.server_close()  

### main function
def main(argv):
    global server, server_addr, server_port
    
    try:                                
        opts, args = getopt.getopt(argv,"dhp:a:",["p","a"])
    except getopt.GetoptError,e:
        print e
        fhelp.help()
        
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            fhelp.help()
        elif opt in ('-d','--debug'):
            debug=1
        elif opt in ('-p','--port'):
            server_port = int(arg)
        elif opt in ('-a','--address'):
            server_addr = arg

    ### bnc()
    pbnc = Thread( target=fbnc.bnc, args=("pbnc", ) )
    pbnc.start()
    
    ###
    serv()
    
#############
### start ###
#############
if __name__ == "__main__":
    main(sys.argv[1:])
