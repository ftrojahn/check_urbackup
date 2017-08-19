#!/usr/bin/python3
# Written By:Tal Bar-Or'
# Created - 21/12/2016
# check_urbackup for backup status
#Ver 0.3import urbackup_api
#simple script to check Urbackup backup status used by https://github.com/uroni/urbackup-server-python-web-api-wrapper
#original source code found at https://bitbucket.org/tal_bar_or/check_urbackup
#fork source code found at https://github.com/pluspol-interactive/check_urbackup.git
import urbackup_api
import datetime,sys
import time,argparse

ClientPrint = ""
GlobalStatus = []
Globalstat = ""

# critical:
# last backup < lastseen -7 days
#
# warning: 
#  last backup < lastseen - 1 days
#  last image  < lastseen - 4 days
#
# TODO: add args --warning --critical

def Statuscheck(client):
    global ClientPrint
    global args
    name = '{:<20}'.format(client["name"]+",")
    online = client["online"] == True
    active = client["delete_pending"]==''
    criticalbackuptime = int(args.critical[0])*24*60*60 # 7 days
    criticalimagetime = (int(args.critical[0])+4)*24*60*60 # 11 days
    warningbackuptime = int(args.warning[0])*24*60*60 # 1 days
    warningimagetime = (int(args.warning[0])+7)*24*60*60 # 4 days
    filescritical = client["lastbackup"]!="-" and client["lastbackup"]>0 and client["lastbackup"] < client["lastseen"] - criticalbackuptime
    fileswarning = client["lastbackup"]=="-" or client["lastbackup"]=="0" or client["lastbackup"] < client["lastseen"] - warningbackuptime
    if client["status"] > 0:
        imagecritical = False
        imagewarning = True
        ClientStatus = "Foreign"
        ClientPrint +="Host:"+name +"Status:"+ str(client["status"]) +"-Foreign,"
        ClientPrint +=" Online:"+ str(client["online"])
        ClientPrint +='\n'
        return ClientStatus
    elif not "os_simple" in client:
        imagecritical = False
        imagewarning = True
        ClientStatus = "Unknown"
        return ClientStatus
    elif client["os_simple"]=="windows":
        imagecritical = client["lastbackup"]=="-" or client["lastbackup_image"] < client["lastseen"] - criticalimagetime
        imagewarning = client["lastbackup"]=="0" or client["lastbackup_image"] < client["lastseen"] - warningimagetime
    else:
        imagecritical = False
        imagewarning = False
    fileok = client["file_ok"] == True or (not fileswarning and not filescritical)
    imageclient = client["os_simple"]=="windows"
    imageok = not imageclient or client["image_ok"] == True or ( not imagewarning and not imagecritical )

    lastbackup = datetime.datetime.fromtimestamp(client["lastbackup"]).strftime("%Y%m%d-%H:%M")
    lastimage = datetime.datetime.fromtimestamp(client["lastbackup_image"]).strftime("%Y%m%d-%H:%M")
    lastseen = datetime.datetime.fromtimestamp(client["lastseen"]).strftime("%Y%m%d-%H:%M")


    ClientStatus = ""
    if active and fileok and imageok:
        ClientStatus = "OK"
        ClientPrint +="Host:"+name +"Status:OK,"
        ClientPrint += " FileBackup:OK" 
        if imageclient:
            ClientPrint += ", ImageBackup:OK"
        else:
            ClientPrint += ", ImageBackup:none"
        ClientPrint += ", LastSeen:" + lastseen
        ClientPrint += ", LastBackup:" + lastbackup 
        if imageclient:
            ClientPrint += ", LastImage:" + lastimage
        ClientPrint +='\n'

        return ClientStatus

    elif active and ( filescritical or imagecritical ):
        ClientStatus = "CRITICAL"
        ClientPrint +="Host:"+name +"Status:Critical,"
        if filescritical:
            ClientPrint += " FilesBackup:Critical"
        elif fileswarning:
            ClientPrint += " FilesBackup:Warning"
        else:
            ClientPrint += " FilesBackup:OK"
        if imageclient and imagecritical:
            ClientPrint += ", ImageBackup:Critical"
        elif imageclient and imagewarning:
            ClientPrint += ", ImageBackup:Warning"
        elif imageclient:
            ClientPrint += ", ImageBackup:OK"
        else:
            ClientPrint += ", ImageBackup:none"
        ClientPrint += ", LastSeen:" + lastseen
        ClientPrint += ", LastBackup:" + lastbackup 
        if imageclient:
            ClientPrint += ", LastImage:" + lastimage
        ClientPrint +='\n'

        return ClientStatus

    elif active and ( fileswarning or imagewarning ):
        ClientStatus = "WARNING"
        ClientPrint += "Host:" + name + "Status:Warning,"
        if fileswarning:
            ClientPrint += " FilesBackup:Warning"
        else:
            ClientPrint += " FilesBackup:OK"
        if imageclient and imagewarning:
            ClientPrint += ", ImageBackup:Warning"
        elif imageclient:
            ClientPrint += ", ImageBackup:OK"
        else:
            ClientPrint += ", ImageBackup:none"
        ClientPrint += ", LastSeen:" + lastseen
        ClientPrint += ", LastBackup:" + lastbackup 
        if imageclient:
            ClientPrint += ", LastImage:" + lastimage
        ClientPrint +='\n'

        return ClientStatus

    else:
    # not active - may be delete_pending or other
        ClientStatus = "Unknown"
        ClientPrint +="Host:"+name +"Status:Unknown,"
        if filescritical:
            ClientPrint += " FilesBackup:Critical"
        elif fileswarning:
            ClientPrint += " FilesBackup:Warning"
        else:
            ClientPrint += " FilesBackup:OK"
        if imageclient and imagecritical:
            ClientPrint += ", ImageBackup:Critical"
        elif imageclient and imagewarning:
            ClientPrint += ", ImageBackup:Warning"
        elif imageclient:
            ClientPrint += ", ImageBackup:OK"
        else:
            ClientPrint += ", ImageBackup:none"
        ClientPrint += ", LastSeen:" + lastseen
        ClientPrint += ", LastBackup:" + lastbackup 
        if imageclient:
            ClientPrint += ", LastImage:" + lastimage
        ClientPrint += ", Delete Pending: " + client["delete_pending"]
        ClientPrint +='\n'



parser = argparse.ArgumentParser()
parser.add_argument('--version','-v',action="store_true",help='show agent version')
parser.add_argument('--host','-ho',action="append",help='host name or IP')
parser.add_argument('--user','-u',action="append",help='User name for Urbackup server')
parser.add_argument('--password','-p',action="append",help='user password for Urbackup server')
parser.add_argument('--critical','-c',action="append",help='critical days')
parser.add_argument('--warning','-w',action="append",help='warning days')
args = parser.parse_args()

if args.host and args.user and args.password and args.critical and args.warning:
    try:
    server = urbackup_api.urbackup_server("http://"+ args.host[0] +":55414/x", args.user[0], args.password[0])
    # TODO: make url as arg
    # server = urbackup_api.urbackup_server("https://"+ args.host[0] +"/urbackup/x", args.user[0], args.password[0])
    returnstatus = 0
    clients = server.get_status()
    # Debug:
    # print(clients)
    for client in clients:
        GlobalStatus.append(Statuscheck(client))
        Globalstat = set(GlobalStatus)
    from collections import Counter
    while True:
        if "CRITICAL" in Globalstat:
            #print(Globalstat)
            print("CRITICAL -", Counter(GlobalStatus)['CRITICAL'], "/", Counter(GlobalStatus)['WARNING'], "/", Counter(GlobalStatus)['OK'], "/", Counter(GlobalStatus)['Unknown'])
            returnstatus = 2
            break
        elif "WARNING" in Globalstat:
            #print(Globalstat)
            print("WARNING -", Counter(GlobalStatus)['CRITICAL'], "/", Counter(GlobalStatus)['WARNING'], "/", Counter(GlobalStatus)['OK'], "/", Counter(GlobalStatus)['Unknown'])
            returnstatus = 1
            break
        elif "OK" in Globalstat:
            #print(Globalstat)
            print("OK -", Counter(GlobalStatus)['CRITICAL'], "/", Counter(GlobalStatus)['WARNING'], "/", Counter(GlobalStatus)['OK'], "/", Counter(GlobalStatus)['Unknown'])
            break
        else:
            print("UNKOWN")
            returnstatus = -1
            break
    print(ClientPrint)
    sys.exit(returnstatus)
    

    except Exception as e:

        print("Error Occured: ",e)


elif args.version:
    print('2.0 Urback Check ,Written By:Tal Bar-Or and adjusted by Ppi')
    sys.exit()
else:
    print("please run check --host <IP OR HOSTNAME> --user <username> --password <password> --critical days --warning days"+ '\n or use --help')
    sys.exit()
