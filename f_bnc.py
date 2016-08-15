### f_bnc
import time
import socket
import SocketServer
import requests
from threading import Thread
import f as f                 # random functions
import f_net as fnet          # socket functions

#
version      = "16.8.15"
aClients  = [] # array of client objects
pbnc=0

# 
class Clients:
    def __init__(self, username):
        self.username  = username
        self.password  = ""  # retrived by /msg obnc login:yourpass
        self.online    = 0   # 0=offline, 1=online
        self.socket    = 0   # irc client/bnc socket
        self.user_host = ""
        self.channels  = []  # channels user have joined
        self.irc_pass  = ""  # set in step2, irc server pwd
        self.irc_nick  = ""
        self.irc_user  = ""

#
class Channel:
    def __init__(self,channel):
        self.channel = channel
        

###
def client_search(username):
    global aClients
    for i in range(0,len(aClients)):
        ac = aClients[i]
        print "{} vs {}\n".format( ac.username, username )
        if ac.username == username:
            return i
    return -1


###
def client_get(x):
    global aClients
    return aClients[x]


###
def client_set(client,x):
    global aClients
    if x==-1:
        aClients.append(client)
        return len(aClients)-1
    else:
        aClients[x]=client
        return x


###
def client_len():
    global aClients
    return len(aClients)

###
def channel_search(channels,channel):
    for i in range(0,len(channels)):
        oc = channels[i]
        print "{} vs {}\n".format( oc.channel, channel )
        if oc.channel == channel:
            return i
    return -1

###
def channel_set(channel,x):
    global aClients
    aClients[x].channels.append( Channel(channel) )

###
def channel_del(channel,x):
    global aClients
    channels=aClients[x].channels
    del channels[channel_search(channels,channel)]
    aClients[x].channels=channels

## executed in obnc.py => threaded_server_handle => step3
def init(spass, nick, user, host, port):
    global version
    ws = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ws.connect((host,port))
    ws.send("PASS {}\r\n".format(spass))
    ws.send("NICK {}\r\n".format(nick))
    ws.send("USER {} * * :obnc v{} at https://github.com/m5it/obnc\r\n".format(user,version))
    return ws

## when client reuse socket and have joined channels before, lets rejoin.. simulate join for client
def imaginary_join(request,x):
    global aClients
    channels=aClients[x].channels
    for i in range(0,len(channels)):
        oc=channels[i]
        print "imaginary_join channel: {}".format(oc.channel)
        request.sendall( ":{}!~{}@obnc JOIN {}\r\n".format(aClients[x].irc_nick, aClients[x].username, oc.channel) )
        aClients[x].socket.send("NAMES {}\r\n".format(oc.channel))
  
## executed in obnc.py => threaded_server_handle => step3 => while irc_run
def handle_client_data(data,x):
    global aClients,aChannels,pbnc
    if f.rmatch("QUIT.*",data)==1:
        aClients[x].online=0
        a=data.split(" ")
        if a[1]== ":stop":
            aClients[x].socket.send("{}\r\n".format(data))
            return -2 # stop the bnc on quit
        return -1     # just disconnect client from bnc
    if f.rmatch("JOIN.*",data)==1: # save channel for imaginary join and on part, delete
        a=data.split(" ")
        channel_set(a[1],x)
    if f.rmatch("PART.*",data)==1:
        a=data.split(" ")
        channel_del(a[1],x)
    aClients[x].socket.send("{}\r\n".format(data))
    return 0
    
    
### this runs when we are not online just we dont ping down
def bnc(name):
    global aClients
    cnt  =0
    max  =3
    sleep=2
    print "starting bnc, aClients len: {}".format( len(aClients) )
    while cnt<=max:
        for i in range(0,len(aClients)):
            ac = aClients[i]
    
            if ac.online==0: # offline
                idata = fnet.recv_timeout(ac.socket,0)
                if len(idata)>0:
                    print "bnc idata: {}".format(idata)
                    if f.rmatch("PING.*",idata)==1:
                        ac.socket.send("PONG\r\n")
                        print "bnc PONG"
                    #ADD: on privmsg send we are not here...
            else:
                 print "bnc user: {} online".format(ac.username)
                 
        print "sleeping {}s, cnt: {}".format(sleep,cnt)
        time.sleep(sleep)
        cnt+=1
        
    # starting new thread
    print "starting pbnc"    
    pbnc = Thread( target=bnc, args=("pbnc", ) )
    pbnc.start() 
    
               
#cdata: 
#whois t3ch
#idata: 
#:tepper.freenode.net 311 t3ch t3ch ~t3ch 178.139.99.101 * :obnc v16.8.14 at https://github.com/m5it/obnc
#:tepper.freenode.net 319 t3ch t3ch :@#obnc 
#:tepper.freenode.net 312 t3ch t3ch tepper.freenode.net :US
#:tepper.freenode.net 378 t3ch t3ch :is connecting from *@178.139.99.101 178.139.99.101
#:tepper.freenode.net 317 t3ch t3ch 2076 1471215350 :seconds idle, signon time
#:tepper.freenode.net 318 t3ch t3ch :End of /WHOIS list.

def get_my_host(s):
    print "host...:)"
