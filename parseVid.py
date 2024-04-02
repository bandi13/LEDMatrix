#!/usr/bin/python3
import cv2
import numpy as np
import sys
import os
import datetime
import socket
import time
import requests
from math import ceil

UDP_PORT=21324

WIDTH=48
HEIGHT=48

MAX_FPS=10
# Brightness 0-255
BRIGHTNESS=250

# DNRGB limit is 489 LEDs per packet according to https://kno.wled.ge/interfaces/udp-realtime/
ROW_PER_PACKET=int(489 / WIDTH)
def sendPanel(sock, ip, port, p):
    num_packets = (HEIGHT + ROW_PER_PACKET - 1) // ROW_PER_PACKET

    for packet_index in range(num_packets):
        start_row = packet_index * ROW_PER_PACKET
        end_row = min(start_row + ROW_PER_PACKET, HEIGHT)
        
        # Packet format
        # byte0: 1- WARLS, 2-DRGB, 3-DRGBW, 4-DNRGB
        # byte1: Seconds to wait before return to normal (255-no timeout)
        # byte2: High-Byte Index of pixel to change
        # byte3: Low-Byte Index of pixel to change
        # byte4+n*3: Red value
        # byte5+n*3: Green value
        # byte6+n*3: Blue value
        m = [4, 1, start_row * WIDTH // 256, start_row * WIDTH % 256]
        
        for row in range(start_row, end_row):
            m.extend(p[row, :, 2::-1].flatten())

        m = bytes(m)
        sock.sendto(m, (ip, port))

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
        print("Usage: {} [--loop | --preview]* <filename> [<hostname>]".format(sys.argv[0]))
        sys.exit()

    opts = [opt for opt in sys.argv[1:] if opt.startswith("-")]
    args = [arg for arg in sys.argv[1:] if not arg.startswith("-")]

    filename = args[0]
    hostname = 'wled.local'
    if len(args) > 1:
        hostname = args[1]

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ip = socket.gethostbyname(hostname)
    print("Sending to: {}".format(ip))

    url = "http://"+str(ip)+"/win&A="+str(BRIGHTNESS)
    print("Setting brightness: {}".format(url))
    requests.get(url)

    # Open the video file
    cap = cv2.VideoCapture(filename)

    # Check if the video file is opened successfully
    if not cap.isOpened():
        print("Error: Could not open video file.")
        sys.exit()

    # Get the frames per second
    fps = cap.get(cv2.CAP_PROP_FPS) 
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
    if frame_count < 0: # single image
        fps = 1
        frame_count = 1
        ret, frame = cap.read()
    print("File FPS={0}, Frame count={1}".format(fps,frame_count))

    startT = datetime.datetime.now()
    lastT = startT
    while ( cap.isOpened() ):
        curT = datetime.datetime.now()
        if 1 / (curT - lastT).total_seconds() > min(MAX_FPS,fps):
            time.sleep(1.0/min(MAX_FPS,fps) - (curT.timestamp() - lastT.timestamp()))
            curT = datetime.datetime.now()

        print("Current FPS={0:5.2f}     ".format(1 / (curT - lastT).total_seconds()), end='\r', flush=True)
        lastT = curT

        delta = curT - startT
        timestamp = int(delta.total_seconds() * 1000)
        if "--loop" in opts:
            if (timestamp >= 1000.0 * frame_count / fps): # loop video
                timestamp = 0
                startT = datetime.datetime.now()

        if frame_count > 1:
            frame = get_frame_at_timestamp(cap, timestamp)
#        print(len(frame))

        if frame is not None:
            # Resize the frame to 48 by 48
            resized_frame = resize_frame(frame, WIDTH, HEIGHT)
            sendPanel(sock,ip,UDP_PORT,resized_frame)
#            print(len(resized_frame))
#            print2d(resized_frame)

            if "--preview" in opts:
                preview_frame = resize_frame(resized_frame, 800, 600)
                cv2.imshow('frame', preview_frame)
                cv2.waitKey(1)

        else:
            print("Exit loop")
            break

    # Release the video capture object
    cap.release()

    # Release all space and windows once done
    cv2.destroyAllWindows()
