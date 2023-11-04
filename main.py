import sys
from urllib.parse import urlencode
from urllib.request import urlopen, Request
import time

import numpy as np
import redis
import cv2


def draw_flow(img, flow, step=16):
    h, w = img.shape[:2]
    y, x = np.mgrid[step/2:h:step, step/2:w:step].reshape(2,-1).astype(int)
    fx, fy = flow[y,x].T
    lines = np.vstack([x, y, x+fx, y+fy]).T.reshape(-1, 2, 2)
    lines = np.int32(lines + 0.5)
    vis = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    cv2.polylines(vis, lines, 0, (0, 255, 0))
    for (x1, y1), (x2, y2) in lines:
        cv2.circle(vis, (x1, y1), 1, (0, 255, 0), -1)
    return vis

def draw_hsv(flow):
    h, w = flow.shape[:2]
    fx, fy = flow[:,:,0], flow[:,:,1]
    ang = np.arctan2(fy, fx) + np.pi
    v = np.sqrt(fx*fx+fy*fy)
    hsv = np.zeros((h, w, 3), np.uint8)
    hsv[...,0] = ang*(180/np.pi/2)
    hsv[...,1] = 255
    hsv[...,2] = np.minimum(v*4, 255)
    bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    return bgr

def warp_flow(img, flow):
    h, w = flow.shape[:2]
    flow = -flow
    flow[:, :, 0] += np.arange(w)
    flow[:, :, 1] += np.arange(h)[:, np.newaxis]
    res = cv2.remap(img, flow, None, cv2.INTER_LINEAR)

    return res

def main(MINUS_THRESHOLD, PLUS_THRESHOLD, thre_rate):
    cam = cv2.VideoCapture("./movie/pair3.mp4")

    width = cam.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cam.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cam.get(cv2.CAP_PROP_FPS)

    ret, prev = cam.read()
    prevgray = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
    show_hsv = False
    show_glitch = False
    use_spatial_propagation = False
    use_temporal_propagation = True
    cur_glitch = prev.copy()
    inst = cv2.DISOpticalFlow.create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    inst.setUseSpatialPropagation(use_spatial_propagation)
    flow = None

    minus_thre = width*height*thre_rate*MINUS_THRESHOLD
    plus_thre = width*height*thre_rate*PLUS_THRESHOLD

    redis_queue = redis.Redis(host='localhost', port=6379, db=0)

    wait_status = 0
    start_time = None
    end_time = None

    i = 0

    while True:
        ret, img = cam.read()

        if ret == False:
            break

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        if flow is not None and use_temporal_propagation:
            #warp previous flow to get an initial approximation for the current flow:
            flow = inst.calc(prevgray, gray, warp_flow(flow,flow))
        else:
            flow = inst.calc(prevgray, gray, None)
        prevgray = gray


        result = draw_flow(gray, flow)
        cv2.imshow('flow', result)
        #cv2.imwrite(f'./result/{str(i).zfill(3)}.png',result)
        i+=1

        if show_hsv:
            cv2.imshow('flow HSV', draw_hsv(flow))
        if show_glitch:
            cur_glitch = warp_flow(cur_glitch, flow)
            cv2.imshow('glitch', cur_glitch)

        ch = 0xFF & cv2.waitKey(10)

        if ch == 27:
            break
        if ch == ord('1'):
            show_hsv = not show_hsv
            print('HSV flow visualization is', ['off', 'on'][show_hsv])
        if ch == ord('2'):
            show_glitch = not show_glitch
            if show_glitch:
                cur_glitch = img.copy()
            print('glitch is', ['off', 'on'][show_glitch])
        if ch == ord('3'):
            use_spatial_propagation = not use_spatial_propagation
            inst.setUseSpatialPropagation(use_spatial_propagation)
            print('spatial propagation is', ['off', 'on'][use_spatial_propagation])
        if ch == ord('4'):
            use_temporal_propagation = not use_temporal_propagation
            print('temporal propagation is', ['off', 'on'][use_temporal_propagation])

        # 出入りを確認し、検知をした場合はRedisにステータスを入れる
        flow_sum = np.sum(flow[:, :, 0])

        if(wait_status == 0):
            if(flow_sum < minus_thre):
                print('-1')
                redis_queue.rpush('queue', '-1')

            elif(flow_sum > plus_thre):
                print('1')
                redis_queue.rpush('queue', '1')

            start_time = time.time()
            wait_status = 1

        else:
            end_time = time.time()
            if((end_time-start_time) > 1):
                start_time = None
                wait_status = 0

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    MINUS_THRESHOLD = -2
    PLUS_THRESHOLD = 3
    #thre_rate = 0.005 # enter
    thre_rate = 0.01 # exit

    main(MINUS_THRESHOLD, PLUS_THRESHOLD, thre_rate)
