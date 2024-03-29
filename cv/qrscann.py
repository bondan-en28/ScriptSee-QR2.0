#import libraries
import cv2
from pyzbar import pyzbar
from ast import literal_eval

def read_barcodes(frame):
    barcodes = pyzbar.decode(frame)
    for barcode in barcodes:
        x, y , w, h = barcode.rect
        #1
        barcode_info = barcode.data.decode('utf-8')
        cv2.rectangle(frame, (x, y),(x+w, y+h), (0, 255, 0), 2)

        qr_dict=id=lat=lon=None
        try:
            qr_dict = literal_eval(barcode_info)
            id=str(qr_dict['id'])
            lat=str(qr_dict['lat'])
            lon=str(qr_dict['lon'])
        except:
            id = "QR Tidak dikenal"
            lat =lon = ""
            # print("QR tidak dikenal")
        print(id)
        print(lat)
        print(lon)

        #2
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, barcode_info, (x + 6, y - 6), font, 0.5, (255, 255, 255), 1)
        #3
        with open("barcode_result.txt", mode ='w') as file:
            file.write("Recognized Barcode:" + barcode_info)
    return frame

def main():
    #1
    camera = cv2.VideoCapture(0)
#    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
#    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cam_width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
    cam_height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))

    ret, frame = camera.read()

    alpha = 0.5     #KONTRAS
    beta = -50       #BRIGHTNESS

    #2
    while ret:
        ret, frame = camera.read()
#        frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)

        frame = read_barcodes(frame)
        cv2.putText(frame, "Frame: "+ str(cam_width)+"x" + str(cam_height),(10,20),cv2.FONT_HERSHEY_DUPLEX, 0.5, (0,255,0), 1) #resolusi frame
        cv2.imshow('Barcode/QR code reader', frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break
    #3
    camera.release()
    cv2.destroyAllWindows()
#4
if __name__ == '__main__':
    main()
