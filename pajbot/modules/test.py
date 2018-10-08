from dota2 import Dota2Client
from steam import SteamClient
from steam.enums.emsg import EMsg
from steam.enums import EResult
from steam import SteamID
from steam.client.user import SteamUser
from steam.core.msg import MsgProto
import gevent
import vdf
import re
import json
import socket

client = SteamClient()
dota = Dota2Client(client)
theSteamID = 76561198036748162
oldID = 0
game_modes = {
    "#DOTA_EventGameName_International2018": "The Underhollow",
    "#DOTA_lobby_type_name_ranked": "Ranked All Pick",
    "Overthrow": "Overthrow",
    "Underhollow": "Underhollow"
}
knownUsers = {
    '76561198049776766': 'ODPixel'
}

@client.on('logged_on')
def start_dota():
    dota.launch()

@dota.on('ready')
def start_scheduler():
    while True:
        fetch_party()
        gevent.sleep(300)
        

def fetch_party():
    global steam3id
    global oldID
    message = MsgProto(EMsg.ClientRichPresenceRequest)
    message.body.steamid_request.extend([theSteamID])
    message.header.routing_appid=570
    resp = client.send_message_and_wait(message, EMsg.ClientRichPresenceInfo)
    try:
        rp = vdf.binary_loads(resp.rich_presence[0].rich_presence_kv)['RP']
    
        if rp['WatchableGameID'] == oldID or 'param0' not in rp:
            return
    except KeyError:
        return
    
    oldID = rp['WatchableGameID']

    steamIDList = re.findall(r'steam_id: (\d*)', str(rp))
    messageSend = '{}: with '.format(game_modes[rp['param0']])
    
    if len(steamIDList) == 1 or not steamIDList:
        messageSend = '{}: Solo queue'.format(game_modes[rp['param0']])
        sendMessage(messageSend)
        return

    num = 0
    for steamID in steamIDList:
        num += 1
        userName = ''
        if int(steamID) == theSteamID:
            continue

        if steamID in knownUsers:
            userName = knownUsers[steamID]
        else:
            userName = client.get_user(steamID).name
        if len(steamIDList) == 2:
            messageSend += userName
            break

        if num == len(steamIDList):
            messageSend = messageSend[:-2]
            messageSend += ' and {}'.format(userName)
            break

        messageSend += '{}, '.format(userName)

    gevent.spawn(sendMessage, messageSend)

def sendMessage(messageSend):
    con = socket.socket()
    con.connect(("irc.twitch.tv", 6667))
    con.send(bytes('PASS oauth:nh9fqvh8c193lfd94rspqikwbozrxm\r\n', 'UTF-8'))
    con.send(bytes('NICK admiralbullbot\r\n', 'UTF-8'))
    con.send(bytes('JOIN #admiralbulldog\r\n', 'UTF-8'))
    print(messageSend)
    con.send(bytes('PRIVMSG #admiralbulldog :!multi {}\r\n'.format(messageSend), 'UTF-8'))
    con.close()
    
     
client.login(username='nammanvanpaja', password='Dismal5e')
client.run_forever()
