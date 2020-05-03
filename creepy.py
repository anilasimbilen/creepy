import socketio
import time
import sys
import getopt
from pynput.keyboard import Controller
from pynput.mouse import Button, Controller as MouseController
from mss import mss
import requests
import os
from requests_toolbelt.multipart.encoder import MultipartEncoder
import json
import getpass
import platform

keyboard = Controller()
mouse = MouseController()
sct = mss()



def click_left():
    mouse.press(Button.left)
    time.sleep(0.1)
    mouse.release(Button.left)


def click_right():
    mouse.press(Button.right)
    time.sleep(0.1)
    mouse.release(Button.right)

sio = socketio.Client()

@sio.event
def connect():
    print("I'm connected!")
@sio.event
def connect_error():
    print("Connection lost")
@sio.event
def disconnect():
    print("Disconnected")
    sys.exit()
@sio.on("test")
def test(data):
    print(data)
@sio.on("getSS")
def getSS(data):
    upload_image(takeSS(_from=[True, data["from"]]), _from=data["from"])
    return
@sio.on("mouse_click")
def handle_mouse_click(data):
    print(data)
    position = (data["position"][0], data["position"][1])
    mouse.position = position
    time.sleep(0.1)
    btn = data["button"]
    if btn == "left":
        click_left()
    elif btn == "right":
        click_right()
    if data["withImage"]:
        time.sleep(data["timeout"])
        upload_image(takeSS(_from=[True, data["from"]]), _from=data["from"])

def initialize():
    with open('config.json') as f:
        data = json.load(f)
        server_address = data["server"]["address"]
        return server_address
server_address = initialize()
def main(argv):
    #initialize()
    server_address = initialize()
    sio.connect(server_address)
    print(platform.platform())
    _uname = os.uname()
    print(_uname.sysname)
    sio.emit("post_connection", {
        "name": getpass.getuser(),
        "os": {
            "system_name": _uname.sysname,
            "nodename": _uname.nodename,
            "version": _uname.version,
            "machine": _uname.machine,
            "release": _uname.release
        }
    })
    opts, args = getopt.getopt(argv, "c:p:t:s", ["click=", "type=", "position-cursor=", "screenshot"])
    for opt, arg in opts:
        if opt == "TESTING":
            mouse.position = (1080, 1080)
        if opt in ("--click", "-c"):
            if arg == "left":
                click_left()
            elif arg == "right":
                click_right()
            else:
                print("Wrong click argument." + opt + " right or " + opt + " left are accepted.")
                sys.exit()
        elif opt in ("-t", "--type"):
            keyboard.type(arg)
        elif opt in ("-p", "--position-cursor"):
            mouse.position = (eval(arg))
        elif opt in ("-s", "--screenshot"):
            upload_image(takeSS())
            sys.exit()

def takeSS(_from = [False, ""]):
    nfilename = os.path.join('ss', sio.sid + ".png")
    if _from[0]:
        nfilename = os.path.join('ss', sio.sid + "-from-" + _from[1] + ".png")
    #with mss() as sct:
    filename = sct.shot()
    print(filename)
    os.rename(filename,nfilename)
    print(nfilename)
    return nfilename    
def upload_image(src, _from=""):
        img = open(src, 'rb')
        url = server_address + "/ss"
        
        mp_encoder = MultipartEncoder(
            fields={
                # plain file object, no filename or mime type produces a
                # Content-Disposition header with just the part name
                'image': (src, open(src, 'rb'), 'image/png'),
                'from': _from
            }
        )
        response = requests.post(url, data=mp_encoder, headers={'Content-Type': mp_encoder.content_type})
        sio.emit("uploaded_ss", {
            "filename": src.split("/")[-1]
        })
        print(response.json())
        return response

if __name__ == "__main__":
    main(sys.argv[1:])
