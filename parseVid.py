#!/usr/bin/python3
import cv2
import numpy as np
import sys
import os
import datetime
import socket
import time

UDP_PORT=21324

WIDTH=48
HEIGHT=48
ROW_PER_PACKET=10
DELAY_PER_PIXEL=0.0003

def sendPanel(sock, ip, port, p):
#    print("type={}, shape={}, len={}".format(type(p),p.shape,len(p)))
#    os.system('cls' if os.name == 'nt' else 'clear')
    for row in range(int(HEIGHT / ROW_PER_PACKET)):
        m = []
        m.append(4) # 1- WARLS, 2-DRGB, 3-DRGBW, 4-DNRGB
        m.append(1) # Seconds to wait before return to normal (255-no timeout)
        i_offset = row * WIDTH * ROW_PER_PACKET
        m.append(int(i_offset / 256))  # High-Byte Index of pixel to change
        m.append(int(i_offset % 256))  # Low-Byte Index of pixel to change
#        print("{0:3},{1:3}={2:5}:".format(m[2],m[3],i_offset), end='')
        for n in range(ROW_PER_PACKET):
            for col in range(WIDTH):
                m.append(p[row*ROW_PER_PACKET+n,col,2])  # Pixel blue value
                m.append(p[row*ROW_PER_PACKET+n,col,1])  # Pixel green value
                m.append(p[row*ROW_PER_PACKET+n,col,0])  # Pixel red value
#                print(" {0:5},{1:5},{2:5}".format(p[row*ROW_PER_PACKET+n,col,0],p[row*ROW_PER_PACKET+n,col,1],p[row*ROW_PER_PACKET+n,col,2]), end='')
        m = bytes(m)
#        print("({})".format(len(m)))
        sock.sendto(m, (ip, port))
        time.sleep(DELAY_PER_PIXEL * WIDTH)

def get_frame_at_timestamp(cap, timestamp):
    # Set the video capture position to the specified timestamp (in milliseconds)
    ret = cap.set(cv2.CAP_PROP_POS_MSEC, timestamp)
    if not ret:
        print("Error: Could not seek to frame at timestamp {}.".format(timestamp))
        return None

    # Read a frame at the specified timestamp
    ret, frame = cap.read()

    # Check if the frame is read successfully
    if not ret:
        print("Error: Could not read frame at timestamp {}.".format(timestamp))
        return None

    return frame

def resize_frame(frame, width, height):
    # Resize the frame to the specified width and height
    resized_frame = cv2.resize(frame, (width, height))
    return resized_frame

def print2d(arr):
    for i in arr:
        for j in i:
            print(j, end=" ")
        print()

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print("Usage: {} <filename>".format(sys.argv[0]))
        sys.exit()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ip = socket.gethostbyname('wled.local')
    print("Sending to: {}".format(ip))

    # Open the video file
    cap = cv2.VideoCapture(sys.argv[1])

    # Check if the video file is opened successfully
    if not cap.isOpened():
        print("Error: Could not open video file.")
        sys.exit()

    # Get the frames per second
    fps = cap.get(cv2.CAP_PROP_FPS) 
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
    print("File FPS={0}, Frame count={1}".format(fps,frame_count))

    startT = datetime.datetime.now()
    lastT = startT
    while ( cap.isOpened() ):
        curT = datetime.datetime.now()
        delta = curT - startT
        timestamp = int(delta.total_seconds() * 1000)
        if (timestamp > 1000.0 * frame_count / fps): # loop video
            timestamp = 0
            startT = datetime.datetime.now()
        frame = get_frame_at_timestamp(cap, timestamp)
#        print(len(frame))

        if frame is not None:
            # Resize the frame to 48 by 48
            resized_frame = resize_frame(frame, WIDTH, HEIGHT)
            sendPanel(sock,ip,UDP_PORT,resized_frame)
#            print(len(resized_frame))
#            print2d(resized_frame)

            preview_frame = resize_frame(resized_frame, 800, 600)
            cv2.imshow('frame', preview_frame)
            cv2.waitKey(1)
            delta = curT - lastT
            print("Current FPS={0:5.2f}     ".format(1 / delta.total_seconds()), end='\r', flush=True)
            lastT = curT
        else:
            print("Exit loop")
            break

    # Release the video capture object
    cap.release()

    # Release all space and windows once done
    cv2.destroyAllWindows()
