from __future__ import print_function
import time, math, threading
# Dronekit Import
from dronekit import VehicleMode, LocationGlobalRelative
from pymavlink import mavutil # Needed for command message definitions

# Local Import
import koneksi, get_attributes, get_params
from cv import qrs, qr_target_identifier

verified = qrs.verified
vehicle = koneksi.vehicle

def armMotor():

    # Get Vehicle Home location - will be `None` until first set by autopilot
    print("Getting Home Location...")
    while not vehicle.home_location:
        cmds = vehicle.commands
        cmds.download()
        cmds.wait_ready()
        if not vehicle.home_location:
            print(" Waiting for home location ...")

    # We have a home location.
    print ("Home location: %s" % vehicle.home_location)
    global initialHeading
    initialHeading = vehicle.heading
    print ("Initial Heading: %s" %initialHeading)

    print("Basic pre-arm checks")
    # Don't try to arm until autopilot is ready
    while not vehicle.is_armable:
        print("Waiting for vehicle to initialise...")
        time.sleep(1)

    print("Arming motors")
    # Copter should arm in GUIDED mode
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    # Confirm vehicle armed before attempting to take off
    while not vehicle.armed:
        print("Waiting for arming...")
        time.sleep(1)

    print("Ready to Fly!")

def takeOff(target_altitude=10):
    print("Taking off!")
    vehicle.simple_takeoff(target_altitude)  # Take off to target altitude

    # Wait until the vehicle reaches a safe height before processing the goto
    #  (otherwise the command after Vehicle.simple_takeoff will execute
    #   immediately).
    while True:
        print(" Altitude: %0.2f meter" %vehicle.location.global_relative_frame.alt)
        # Break and return from function just below target altitude.
        if vehicle.location.global_relative_frame.alt >= target_altitude:
            print("Reached target altitude")
            break
        time.sleep(1)

def getJarak(lokasi_terkini, lokasi_target):
    dlat = lokasi_terkini.lat - lokasi_target.lat
    dlong = lokasi_terkini.lon - lokasi_target.lon
    return math.sqrt((dlat*dlat) + (dlong*dlong)) * 1.113195e5

def terbangKe(lokasi_target):
    print("Menuju : ", lokasi_target)
    lokasi_terkini = vehicle.location.global_relative_frame
    jarak_target = getJarak(lokasi_terkini, lokasi_target)
    vehicle.simple_goto(lokasi_target)
    
    while vehicle.mode.name=="GUIDED": #Berhenti apabila keluar dari mode Guided
        jarak_terkini = getJarak(vehicle.location.global_relative_frame, lokasi_target)
        print("%0.2f meter menuju lokasi." %jarak_terkini)
        if jarak_terkini<=jarak_target*0.01:
            print("Sampai di lokasi kakak :)")
            break
        time.sleep(1)

def condition_yaw(heading, relative=False):
    if relative:
        is_relative=1 #yaw relative to direction of travel
    else:
        is_relative=0 #yaw is an absolute angle
    # create the CONDITION_YAW command using command_long_encode()
    msg = vehicle.message_factory.command_long_encode(
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_CMD_CONDITION_YAW, #command
        0, #confirmation
        heading,    # param 1, yaw in degrees
        0,          # param 2, yaw speed deg/s
        1,          # param 3, direction -1 ccw, 1 cw
        is_relative, # param 4, relative offset 1, absolute angle 0
        0, 0, 0)    # param 5 ~ 7 not used
    # send command to vehicle
    vehicle.send_mavlink(msg)

def set_roi(location):
    # create the MAV_CMD_DO_SET_ROI command
    msg = vehicle.message_factory.command_long_encode(
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_CMD_DO_SET_ROI, #command
        0, #confirmation
        0, 0, 0, 0, #params 1-4
        location.lat,
        location.lon,
        location.alt
        )
    # send command to vehicle
    vehicle.send_mavlink(msg)
    
def RTL():
    vehicle.mode = VehicleMode('RTL')
    while vehicle.armed:
        jarak = getJarak(vehicle.location.global_relative_frame,vehicle.home_location)
        if jarak<1:
            if abs(vehicle.heading-initialHeading)>5:
                condition_yaw(initialHeading,0)
            print("Descending... Altitude: %0.2f meter" %vehicle.location.global_relative_frame.alt)
        else:
            print("OTW RTL... %0.2f meter menuju Home..." %jarak)
        time.sleep(1)
    print("RTL Selesai!")

def align():
    try:
        print("Mode: "+vehicle.mode.name)
        vehicle.channels.overrides['3'] = 1500
        vehicle.mode = VehicleMode('LOITER')
        print("Ubah mode ke LOITER")
        print("Mode: "+vehicle.mode.name)
        print("Emulating Joystick Control...")
        while verified.confirmed is False:
            print(verified.confirmed)
            while verified.x and verified.y:
                x, y=verified.x , verified.y
                print(str(x)+','+str(y))
                if x<50 and x>-50 and y<50 and y>-50:
                    # vehicle.channels.overrides = {}
                    vehicle.mode = VehicleMode('GUIDED')
                    set_roi(location=vehicle.home_location)
                    vehicle.channels.overrides['7']=1800
                    print("Tunggu bentar...")
                    time.sleep(10)
                    verified.confirmed=True
                    print("Misi Selesai!")
                    break
                elif x>50: #kiri
                    vehicle.channels.overrides['1']=1300
                    print('kiri')
                elif x<-50: #kanan
                    vehicle.channels.overrides['1']=1700
                    print('kanan')
                elif y>50: #mundur
                    vehicle.channels.overrides['2']=1300
                    print('mundur')
                elif y<-50: #maju
                    vehicle.channels.overrides['2']=1700            
                    print('maju')
                vehicle.flush()
                time.sleep(1)
            else:
                print("Looking for QRCode...")
                vehicle.channels.overrides = {}
                vehicle.channels.overrides['3'] = 1500
                time.sleep(1)
    except:
        print("ERROR.")
        vehicle.channels.overrides = {}

################################################# Manggil FUNGSI DI SINI SEMUA YGY (biar rapih)

#get_params.getParams(vehicle)
#get_attributes.getAttributes(vehicle)

print("\n\nVerifikasi Misi...")
identifiedQRDict = None
missionValid = False

while identifiedQRDict is None:
    identifiedQRDict= qr_target_identifier.main()

targetLat = float(identifiedQRDict['lat'])
targetLon = float(identifiedQRDict['lon'])
targetAlt = 10

targetLocation = LocationGlobalRelative(targetLat, targetLon, targetAlt)

print("\nTarget Location: "+str(targetLocation))
distanceToTarget= getJarak(vehicle.location.global_relative_frame,targetLocation)
print("Distance to Target: %0.2f meter" %distanceToTarget)

if distanceToTarget>100.0:
    missionValid = False
else:
    missionValid=True

if missionValid:
    if input("\n\nArm Motors? y/n: ")=="y":
        armMotor()
        if input("\nTake Off? y/n: ")=="y":
            takeOff(10)
            if input("\nLanjutkan ke Target? y/n: ")=="y":
                terbangKe(targetLocation)
                vehicleAlignment = threading.Thread(target=align) #Threading agar fungsi align dapat berjalan di latar belakang
                vehicleAlignment.daemon = True
                vehicleAlignment.start()
                qrs.init(vehicle, str(identifiedQRDict['id']))
                vehicleAlignment.join()
                RTL()
            else:
                RTL()
        else:
            vehicle.armed = False
            print("Mission Cancelled.")
    else:
        print("Mission Cancelled.")
else:
    print("Too Far... Mission Impossible.")
# Sequence:
# 1. Scan QR-Code
# 2. Verifying QR-Code
# 3. Aligning QR-Code
# 4. Secondary Verifying QR-Code
# 5. IF VERIFIED>Decent Altitude
# 6. ELSE>RTL
# 7. RTL
