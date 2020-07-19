# bot.py
import os
import requests
import discord
import psycopg2
import json
import random
from dotenv import load_dotenv
from threading import Thread

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
steamapikey = os.getenv('steamapikey')
dbHost = os.getenv('dbHost')
dbPort = os.getenv('dbPort')
dbName = os.getenv('dbName')
dbUser = os.getenv('dbUser')
dbPassword = os.getenv('dbPassword')

client = discord.Client()

@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.type is discord.ChannelType.private:        
        discordId = message.author.id
        #will split out the url, last element will be either the steam id or the rich text id
        splitmessage = message.content.split('/')
        try:
            steamId = int(splitmessage[-1])            
            #add to postgress database
            AddUserToDB(discordId, steamId)
            await message.author.send("Steam ID successfully added!")
        except:
            #then call steam api
            steamId = GetSteamIDFromRichName(splitmessage[-1] if splitmessage[-1] != '' else  splitmessage[-2])
            if steamId != False:
                AddUserToDB(discordId, steamId)
                await message.author.send("Steam ID successfully added!")
            else:
                await message.author.send("Steam ID was unable to be found, please try again with your steam64 ID")

    else:        
        if message.content.lower() == "!games":
            print("finding games")
            possibleGames = await GetPlayableGames(message)
            if len(possibleGames) == 0:
                await message.channel.send('You fucking donkey')
            else:
                await message.channel.send(', '.join(GetGamesFromIds(possibleGames))[:2000])                        

        if message.content == "SPIN THE WHEEL":
            await message.channel.send("picking game that isnt age 2")
            possibleGames = await GetPlayableGames(message)
            await message.channel.send("The game you shall play is....... " + random.choice(GetGamesFromIds(possibleGames)))

async def GetPlayableGames(message):
    possibleGames = []
    playerGamesDict = {}
    channel = await getChannelFromMessage(message)                       
    if channel:
        threads = [None] * len(channel.members) 
        for i in range(len(channel.members)):
            steamid = GetSteamId(channel.members[i].id)
            if not steamid == False:
                playerGamesDict[i] = []
                threads[i] = Thread(target=GetOwnedGames, args=(steamid, playerGamesDict, i))
                threads[i].start()   
            else:
                await message.channel.send(channel.members[i].name + " has not sent me their steam link and wont be included")      
        for i in range(len(threads)):
            if threads[i] != None:
                threads[i].join()                
        for i in range(len(channel.members)):
            if len(possibleGames) == 0:
                if i in playerGamesDict:
                    possibleGames = playerGamesDict[i]                            
            else:
                if i in playerGamesDict:
                    possibleGames = list(set(possibleGames) & set(playerGamesDict[i]))
                        
    else:
        print("User not found")
    return possibleGames

async def getChannelFromMessage(message):
    for channel in message.guild.voice_channels:
            if len(channel.members) > 0 :
                for member in channel.members:
                    if member.id == message.author.id:
                        return channel
    return False

def AddUserToDB(discordId, steamId):
    try:
        dbconn = psycopg2.connect(host = dbHost, dbname = dbName, user = dbUser, password = dbPassword, port = dbPort)
        cur = dbconn.cursor()
        cur.execute("insert into steamids(discordid, steamid) values(%(discordid)s, %(steamid)s) on conflict (discordid) do update set steamid = %(steamid)s;",
        {"discordid":discordId, "steamid": steamId})
        dbconn.commit()
        cur.close()
        dbconn.close()
        print("insertion sucessful")
    except Exception as ex:
        print(ex)

def GetSteamId(discordId):
    dbconn = psycopg2.connect(host = dbHost, dbname = dbName, user = dbUser, password = dbPassword, port = dbPort)
    cur = dbconn.cursor()
    cur.execute("select steamid from steamids where discordid = %(discordid)s limit 1;", {"discordid":discordId})
    ret = cur.fetchall()
    cur.close()
    dbconn.close()
    for row in ret:
        return row[0]
    return False

#this doesnt work properly because steam api is shit
# def GetGamesFromIds(games):
#     ret = []
#     for game in games:
#         payload = {"key": steamapikey, "appid": game}
#         response = requests.get("http://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v2/", params = payload)
#         json = response.json()
#         if not json.get("game") is None:
#             if not json["game"].get("gameName") is None:
#                 ret.append(response.json()["game"]["gameName"])
#     return ret

def GetGamesFromIds(games):
    ret = []
    for game in games:
        ret.append(appList[game])
    return ret

# literally queries the entire steam library getting ALL apps and data back instead of being able to filter in the call
def GetAppList():
    response = requests.get("https://api.steampowered.com/ISteamApps/GetAppList/v2/")
    return {d["appid"]:d["name"] for d in response.json()["applist"]["apps"]}

def GetSteamIDFromRichName(name):
    print("making rich name call for: " + name)
    payload = {"key": steamapikey, "vanityurl": name}
    response = requests.get("https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/", params = payload)
    jsonresponse = response.json()
    print(response)
    if jsonresponse["response"]["success"] == 1:
        return response.json()["response"]["steamid"]
    else:
        return False    

def GetOwnedGames(steamid, result, index):
    print("steamid: " + str(steamid))
    payload = {"key": steamapikey, "steamid": steamid, "format": "json"}
    response = requests.get("http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/", params = payload)
    result[index] = list(map(lambda x: x["appid"], response.json()["response"]["games"]))

appList = GetAppList()
client.run(TOKEN)