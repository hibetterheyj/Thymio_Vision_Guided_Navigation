import cv2
import matplotlib.pyplot as plt
import os
import pickle
import numpy as np

def delet_contours(contours, delete_list):
    delta = 0
    for i in range(len(delete_list)):
        del contours[delete_list[i] - delta]
        delta = delta + 1
    return contours

def mask_from_contours(ref_img, contours):
    mask = np.zeros((ref_img.shape[0],ref_img.shape[1],3), np.uint8)
    mask = cv2.drawContours(mask, contours, -1, (255,255,255), -1)
    return cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)

pink_lower = np.array([100, 95, 110])
pink_upper = np.array([150, 155, 200])
yellow_lower = np.array([85, 100, 170])
yellow_upper = np.array([120, 125, 210])
red_lower = np.array([100, 130, 145])
red_upper = np.array([132, 170, 215])
orange_lower = np.array([95, 124, 165])
orange_upper = np.array([115, 175, 205])
green_lower = np.array([30, 130, 90])
green_upper = np.array([60, 175, 132])
blue_lower = np.array([15, 175, 110])
blue_upper = np.array([25, 230, 165])

def transform_img(frame):
    HSV = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
    HSV_blur = cv2.GaussianBlur(HSV, (7, 7), 0)
    pink_mask=cv2.inRange(HSV_blur,pink_lower,pink_upper)
    pink_mask[70:350,:]=0 #remove the red which is similar to pink corners
    pink_mask[:,100:500]=0 #remove the red which is similar to pink corners
    contours, hierarchy = cv2.findContours(pink_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)  # for opencv3.4
    corner_points = []
    for i in range(len(contours)):
        if (cv2.contourArea(contours[i]) > 200):
            mom = cv2.moments(contours[i])
            corner_points.append((int(mom['m10'] / mom['m00']), int(mom['m01'] / mom['m00'])))
    if len(corner_points) != 4:
        print("failure in identifying corners")
        print(corner_points)
    corner_points=sorted(corner_points, key=lambda x: (int(x[1]), int(x[0]))) #topleft,topright,bottomleft,bottomright
    if corner_points[0][0] > corner_points[1][0]:
        corner_points[0], corner_points[1] = corner_points[1], corner_points[0]
    if corner_points[2][0] > corner_points[3][0]:
        corner_points[2], corner_points[3] = corner_points[3], corner_points[2]
    pts1 = np.float32(corner_points)
    pts2 = np.float32([[0, 0], [640, 0], [0, 480], [640, 480]])
    transform = cv2.getPerspectiveTransform(pts1, pts2)
    warpedimg = cv2.warpPerspective(frame, transform, (640, 480))
    return warpedimg

def color_mask(warpedimg,offset_thymio):
    HSV_warped = cv2.cvtColor(warpedimg, cv2.COLOR_RGB2HSV)
    HSV_warped_blur = cv2.GaussianBlur(HSV_warped, (7, 7), 0)
    
    red_mask_open=cv2.inRange(HSV_warped_blur,red_lower,red_upper)
    obstacles_mask = cv2.morphologyEx(red_mask_open, cv2.MORPH_CLOSE, np.ones((5,5), np.uint8),iterations=2)
    
    yellow_mask_open=cv2.inRange(HSV_warped_blur,yellow_lower,yellow_upper)
    yellow_mask_closed = cv2.morphologyEx(yellow_mask_open, cv2.MORPH_CLOSE, np.ones((5,5), np.uint8),iterations=2)
    contours, hierarchy = cv2.findContours(yellow_mask_closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)  # for opencv3.4
    for i in range(len(contours)):
        if (cv2.contourArea(contours[i]) > 100):
            mom = cv2.moments(contours[i])
            end_point=(int(mom['m01'] / mom['m00']),int(mom['m10'] / mom['m00']))
            break

    green_mask_open = cv2.inRange(HSV_warped_blur,green_lower,green_upper)
    green_mask_closed = cv2.morphologyEx(green_mask_open, cv2.MORPH_CLOSE, np.ones((5,5), np.uint8),iterations=2)
    contours, hierarchy = cv2.findContours(green_mask_closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)  # for opencv3.4
    for i in range(len(contours)):
        if (cv2.contourArea(contours[i]) > 100):
            mom = cv2.moments(contours[i])
            start_point_forward=(int(mom['m10'] / mom['m00']), int(mom['m01'] / mom['m00']))
            break
            
    blue_mask_open = cv2.inRange(HSV_warped_blur,blue_lower,blue_upper)
    blue_mask_closed = cv2.morphologyEx(blue_mask_open, cv2.MORPH_CLOSE, np.ones((5,5), np.uint8),iterations=2)
    contours, hierarchy = cv2.findContours(blue_mask_closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)  # for opencv3.4
    for i in range(len(contours)):
        if (cv2.contourArea(contours[i]) > 100):
            mom = cv2.moments(contours[i])
            start_point_hinter=(int(mom['m10'] / mom['m00']), int(mom['m01'] / mom['m00']))
            break
    
    start_point = (int((start_point_forward[1] + start_point_hinter[1])/2 + offset_thymio[1]) , int((start_point_forward[0] + start_point_hinter[0])/2 + offset_thymio[0]))
    start_direction = (start_point_forward[1] - start_point_hinter[1], start_point_forward[0] - start_point_hinter[0])
    return(obstacles_mask,start_point,end_point,start_direction)

def dilate_obstacle(obstacles_mask,ext_pixels):  
    contours, hierarchy = cv2.findContours(obstacles_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    delete_list = []
    for i in range(len(contours)):
        if (cv2.contourArea(contours[i]) < 100):
            delete_list.append(i)
    contours = delet_contours(contours, delete_list)
    obstacles_mask_filtered = mask_from_contours(obstacles_mask,contours)
    obstacles_mask_dilated = cv2.dilate(obstacles_mask_filtered, np.ones((int(ext_pixels*2-1),int(ext_pixels*2-1)), np.uint8), iterations=1)
    obstacles_mask_dilated[:6,:] = 255;
    obstacles_mask_dilated[:,:6] = 255;
    obstacles_mask_dilated[:,-1:-7:-1] = 255;
    obstacles_mask_dilated[-1:-7:-1,:] = 255; #add walls
    return(obstacles_mask_dilated)

def rasterize(obstacles_mask_dilated,real_width,real_height,grid_size,start_point,end_point):
    grid_output = obstacles_mask_dilated.copy()
    rows,cols = grid_output.shape
    grid_size_h = rows*grid_size/real_height #make sure this to be fully 
    grid_size_w = cols*grid_size/real_width
    grid_array_output = np.zeros([int(real_height/grid_size),int(real_width/grid_size)])
    grid_array_start = (int(start_point[0]//grid_size_h),int(start_point[1]//grid_size_w))
    grid_array_end = (int(end_point[0]//grid_size_h),int(end_point[1]//grid_size_w)) 
    for i in range(0,int(real_height/grid_size)):
        for j in range(0, int(real_width/grid_size)):
            sum = np.sum(grid_output[int(i*grid_size_h):int((i+1)*grid_size_h),int(j*grid_size_w):int((j+1)*grid_size_w)])
            if (sum >= 255 ): 
                grid_output[int(i*grid_size_h):int((i+1)*grid_size_h),int(j*grid_size_w):int((j+1)*grid_size_w)] = 255
                grid_array_output[i,j] = 1;
            else:
                grid_output[int(i*grid_size_h):int((i+1)*grid_size_h),int(j*grid_size_w):int((j+1)*grid_size_w)] = 0
    return(grid_output,grid_array_output,grid_array_start,grid_array_end)