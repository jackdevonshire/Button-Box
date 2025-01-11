import time
import base64

try:
    import broadlink
except:
    print("Error! Before running this, please install the 'broadlink' pip module")


ip = input("Enter IP of Broadlink Device: ")
device = broadlink.hello(ip)
          
try:
    device.auth()
except:
    print("Error! Please setup the broadlink device in the app, and make sure to UNLOCK the device in settings")

while True:
    check = input("Press enter to start learning: ")
    device.enter_learning()
    check = input("Press the IR button you want to learn, then press enter: ")
    packet = device.check_data()
    print("-- COPY IR CODE BELOW --")
    print(str(base64.b64encode(packet))[1:].replace("'", ""))
    print("----")
