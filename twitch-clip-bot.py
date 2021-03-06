#!/usr/bin/env python3

import re
import socket
import ssl
import sys
import threading
import time

import config
import debug
import twitch
import utility

COMMANDS = [
    #	[r"!discord", "the official discord: ____"]
]

TWITCH_MSG = re.compile(r"(:tmi\.twitch\.tv \w+ \w+ :|:\w+.tmi\.twitch\.tv \w+ \w+ |:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :)")

CHAT_NAMES_TO_ID = {}

#	Connecting to Twitch IRC
try:
    s_p = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s = ssl.wrap_socket(s_p)
    s.connect((config.TWITCH_HOST, config.TWITCH_PORT))

    s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    s.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
    s.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 5)
    if sys.platform != 'darwin':
        s.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 1)

    s.send("PASS {}\r\n".format(config.TWITCH_PASS).encode("utf-8"))
    s.send("NICK {}\r\n".format(config.TWITCH_NICK).encode("utf-8"))

    for channel_name in config.CHANNEL_NAMES:

        time.sleep(0.2)

#       Getting channels id from channels names
        channel_id = twitch.get_channel_id(channel_name)

        channel_name = "#" + channel_name
        CHAT_NAMES_TO_ID[channel_name] = str(channel_id)

        s.send("JOIN {}\r\n".format(channel_name).encode("utf-8"))
        utility.print_toscreen(channel_name + " : " + channel_id)

    connected = True  # Socket succefully connected
except Exception as e:
    debug.output_error(debug.lineno() + " - " + str(e))
    connected = False  # Socket failed to connect
    utility.restart()


#	BOT LOOP
#	--------

def bot_loop():
    time.sleep(1)
    utility.print_toscreen("Starting Bot Loop")

    while connected:

        response = ""

        try:
            response = s.recv(1024).decode("utf-8")

        except Exception as e:
            debug.output_error(debug.lineno() + " - " + str(e))
            utility.restart()

#	PING-PONG
        if re.search("PING :tmi.twitch.tv",response):

            try:
                s.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
# 		 utility.print_toscreen("Pong")
#                debug.output_debug ("PONG")
                utility.print_usertoscreen("server", "twitch", "ping")
            except IOError as e:
                debug.output_error(debug.lineno() + " - " + "PONG error " + str(e))
                utility.restart()

        find_all_twitch = re.findall(TWITCH_MSG, response)
        for found in find_all_twitch:
            username = ""
            channel = ""
            message = ""

            try:

                message = response[response.find(found) + len(found):]

                start = re.search(TWITCH_MSG, message)
                if start:
                    message = message[0:start.start()]
                else:
                    message = message

                if re.search("PRIVMSG",found):
                    channel = re.search(r"#\w+", found).group(0)
                    username = re.search(r"\w+", found).group(0)

                    utility.print_usertoscreen(channel, username, message.rstrip())
                else:
                    utility.print_usertoscreen("server", "twitch", message.strip())

                message = message.lower().rstrip()

            except Exception as e:
                debug.output_error(debug.lineno() + " - " + str(e))


            #			clip | !clip
            if message == "!clip" or message == "clip" or message == "clip it":

                channel_id = CHAT_NAMES_TO_ID[channel]
                debug.output_debug(channel + " | " + username + ": " + message)

                clip_thread = threading.Timer(5, create_clip, args=[channel, channel_id, username])
                clip_thread.start()

            #           			!Hey
#            if message == "!hey" or message == "hi" or message == "hey" or message == "hello" or message == "heyguys":
#               utility.chat(s, channel, "Hey " + username + ", Welcome to the stream!")
#				utility.print_toscreen(CHAT_NAMES_TO_ID[channel])

            #			!help
            if message == "!help":
                utility.chat(s, channel,
                             "Hi, I'm the clipping bot. type \"clip\" or \"!clip\" in chat, I'll clip the last 25 sec and post the link.")

            if re.search(config.TWITCH_NICK, message):
                debug.output_debug(channel + " | " + username + ": " + message)


#        for pattern in COMMANDS:
#            if re.match(pattern[0], message):
#                utility.chat(s, channel, pattern[1])


#	Thread for creating clip
def create_clip(channel, channel_id, username):
       
#   if twitch.is_stream_live(channel_id):
    if True:
        clip_id = twitch.create_clip(channel_id)
        time.sleep(5)
    
        if clip_id and twitch.is_there_clip(clip_id):
    
            clip_proccess_thread = threading.Timer(0, proccess_clip, args=[clip_id, username, channel])
            clip_proccess_thread.start()
        
        else:
            debug.output_debug("Second try")
            clip_id = twitch.create_clip(channel_id)
            time.sleep(10)

            if (clip_id):
    
                clip_proccess_thread = threading.Timer(0, proccess_clip, args=[clip_id, username, channel])
                clip_proccess_thread.start()
            else:
                utility.chat(s, channel, "Sorry " + username + ", couldn't make your clip")
    else:
        utility.chat(s, channel, username + ", the stream is offline, clipping is disabled.")


#	Thread for proccessing clip after X time
def proccess_clip(clip_id, username, channel_name):

    if twitch.is_there_clip(clip_id):
        clip_url = "https://clips.twitch.tv/" + clip_id

        utility.chat(s, channel_name, clip_url)
        utility.write_tofile(clip_url + "\n")

    else:
        utility.chat(s, channel_name, "Sorry " + username + ", Twitch couldn't make the clip.")


#  ---------
#    MAIN  
#  ---------

if __name__ == "__main__":
    bot_loop()

#TODO - add constant colors to  twitch and bot


