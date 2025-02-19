import cv2
import numpy as np
import glob
import matplotlib.pyplot as plt

nx, ny = 9, 6


def calibrate(images, nx, ny):
    objpoints = [] 
    imgpoints = []

    objp = np.zeros(shape=(nx*ny, 3), dtype=np.float32)
    objp[:, :2] = np.mgrid[0:nx, 0:ny].T.reshape(-1, 2)

    
    for path_name in images:
        img = cv2.imread(path_name)
        if img.shape[0] != 720:
            img = cv2.resize(img,(1280, 720))
        gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray_image,(nx,ny))
        
        if ret:
            objpoints.append(objp)
            imgpoints.append(corners)
        
    return cv2.calibrateCamera(objpoints, imgpoints, gray_image.shape[::-1], None, None)


def binary_threshold(img, sobel_kernel=7, mag_thresh=(9, 255), s_thresh=(170, 255)):
    
    hls = cv2.cvtColor(img, cv2.COLOR_RGB2HLS)
    gray = hls[:,:,1]
    s_channel = hls[:, :, 2]

    sobel_binary = np.zeros(shape=gray.shape, dtype=bool)
    s_binary = sobel_binary
    combined_binary = s_binary.astype(np.float32)

    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=sobel_kernel)
    sobely = 0

    sobel_abs = np.abs(sobelx**2 + sobely**2)
    sobel_abs = np.uint8(255 * sobel_abs / np.max(sobel_abs))

    sobel_binary[(sobel_abs > mag_thresh[0]) & (sobel_abs <= mag_thresh[1])] = 1

    s_binary[(s_channel >= s_thresh[0]) & (s_channel <= s_thresh[1])] = 1

    combined_binary[(s_binary == 1) | (sobel_binary == 1)] = 1
    combined_binary = np.uint8(255 * combined_binary / np.max(combined_binary))

    #offset = 100
    offset = 50 
    mask_polyg = np.array([[(0 + offset, img.shape[0]),
                            (img.shape[1] / 2.5, img.shape[0] / 1.6),
                            (img.shape[1] / 1.8, img.shape[0] / 1.6),
                            (img.shape[1], img.shape[0])]],
                          dtype=np.int32)


    
    mask_img = np.zeros_like(combined_binary)
    ignore_mask_color = 255


    cv2.fillPoly(mask_img, mask_polyg, ignore_mask_color)
    masked_edges = cv2.bitwise_and(combined_binary, mask_img)

    return masked_edges

def warp(img, src, dst):
    
    src_f32 = np.float32([src])
    dst_f32 = np.float32([dst])

    return cv2.warpPerspective(img, cv2.getPerspectiveTransform(src_f32, dst_f32),
                               dsize=img.shape[0:2][::-1], flags=cv2.INTER_LINEAR)

def calculate_histogram(binary_warped):
    histogram = np.sum(binary_warped[binary_warped.shape[0]//2:, :], axis=0)
    return histogram

def find_lane_bases(histogram):
    midpoint = np.int32(histogram.shape[0] // 2)
    left_base = np.argmax(histogram[:midpoint]) 
    right_base = np.argmax(histogram[midpoint:]) + midpoint 
    return left_base, right_base

def sliding_window(binary_warped, hist, nwindows=9):
   
    window_height = np.int32(binary_warped.shape[0] // nwindows)

    left_current, right_current = find_lane_bases(histogram=hist)

    margin = 100
    minpix = 50

    nonzero = binary_warped.nonzero()
    nonzeroy = np.array(nonzero[0])  
    nonzerox = np.array(nonzero[1])

    left_lane_inds = []
    right_lane_inds = []

    for window in range(nwindows):

        win_y_low = binary_warped.shape[0] - (window + 1) * window_height
        win_y_high = binary_warped.shape[0] - window * window_height
        win_xleft_low = left_current - margin
        win_xleft_high = left_current + margin
        win_xright_low = right_current - margin
        win_xright_high = right_current + margin

        good_left_inds = ((nonzeroy >= win_y_low) & (nonzeroy < win_y_high) &
                        (nonzerox >= win_xleft_low) & (nonzerox < win_xleft_high)).nonzero()[0]
        good_right_inds = ((nonzeroy >= win_y_low) & (nonzeroy < win_y_high) &
                        (nonzerox >= win_xright_low) & (nonzerox < win_xright_high)).nonzero()[0]

        left_lane_inds.append(good_left_inds)
        right_lane_inds.append(good_right_inds)

        if len(good_left_inds) > minpix:
            left_current = np.int32(np.mean(nonzerox[good_left_inds]))
        if len(good_right_inds) > minpix:
            right_current = np.int32(np.mean(nonzerox[good_right_inds]))

    left_lane_inds = np.concatenate(left_lane_inds)
    right_lane_inds = np.concatenate(right_lane_inds)

    leftx = nonzerox[left_lane_inds]
    lefty = nonzeroy[left_lane_inds]
    rightx = nonzerox[right_lane_inds]
    righty = nonzeroy[right_lane_inds]

    left_fit = np.polyfit(lefty, leftx, 2)
    right_fit = np.polyfit(righty, rightx, 2)

    return left_fit, right_fit

def draw_lane(original_img, binary_warped, left_fit, right_fit, Minv):
    shape = original_img.shape[:]
    ploty = np.linspace(0, binary_warped.shape[0] - 1, binary_warped.shape[0])

    left_fitx = left_fit[0] * ploty**2 + left_fit[1] * ploty + left_fit[2]
    right_fitx = right_fit[0] * ploty**2 + right_fit[1] * ploty + right_fit[2]

    lane_img = np.zeros_like(original_img)
    lane_color = (255,0,0)

    pts_left = np.array([np.transpose(np.vstack([left_fitx, ploty]))])
    pts_right = np.array([np.flipud(np.transpose(np.vstack([right_fitx, ploty])))])
    pts = np.hstack((pts_left, pts_right))

    cv2.fillPoly(lane_img, np.int_([pts]), lane_color)

    lane_img = cv2.warpPerspective(lane_img, Minv, (original_img.shape[1], original_img.shape[0]))
    original_img = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB) #Plt uses RGB and cv2 uses BGR
    result = cv2.addWeighted(original_img, 1, lane_img, 0.3, 0)

    ''' RADIUS '''
    ym_per_pix = 30 / 720  
    xm_per_pix = 3.7 / 700 
    img_height = shape[0]
    y_eval = img_height
    
    ploty = np.linspace(0, img_height - 1, img_height)

    left_fit_cr = np.polyfit(ploty * ym_per_pix, left_fitx * xm_per_pix, 2)
    right_fit_cr = np.polyfit(ploty * ym_per_pix, right_fitx * xm_per_pix, 2)

    left_curvature = ((1 + (2 * left_fit_cr[0] * y_eval * ym_per_pix + left_fit_cr[1])**2)**1.5) / np.abs(2 * left_fit_cr[0])
    right_curvature = ((1 + (2 * right_fit_cr[0] * y_eval * ym_per_pix + right_fit_cr[1])**2)**1.5) / np.abs(2 * right_fit_cr[0])

    radius = round((float(left_curvature) + float(right_curvature))/2.,2)

    center = (right_fit[2] - left_fit[2]) / 2
    off_center = round((center - shape[0] / 2.) * xm_per_pix,2)

    text = "radius = %s [m]\noffcenter = %s [m]" % (str(radius), str(off_center))

    for i, line in enumerate(text.split('\n')):
        i = 50 + 20 * i
        cv2.putText(result, line, (0,i), cv2.FONT_HERSHEY_DUPLEX, 0.5,(255,255,255),1,cv2.LINE_AA)

    return result

def main():    

    images = glob.glob('camera_cal/*.jpg')
    ret, camera_matrix, dist_coeffs, rvecs, tvecs = calibrate(images, nx, ny)

    test = cv2.imread('test_images/test1.jpg')
    chessboard_image = cv2.imread('camera_cal/calibration1.jpg')

    undistorted = cv2.undistort(test, camera_matrix, dist_coeffs, None, camera_matrix)
    undistorted_chessboard = cv2.undistort(chessboard_image, camera_matrix, dist_coeffs, None, camera_matrix)
    cv2.imwrite('undistorted.jpg', undistorted)
    cv2.imwrite('undistorted_chessboard.jpg', undistorted_chessboard)

    '''############################# Binary threshold #############################'''
    img_m = binary_threshold(undistorted)
    cv2.imwrite('masked.jpg', img_m)
    
    '''############################# Perspective #############################'''
    line_dst_offset = 150
    img_height, img_width = img_m.shape[:2]

    src = np.float32([
        [img_width * 0.15, img_height],             
        [img_width * 0.45, img_height * 0.65],       
        [img_width * 0.55, img_height * 0.65],        
        [img_width * 0.85, img_height]               
    ])
    
    dst = np.float32([
        [img_width * 0.2, img_height],            
        [img_width * 0.2, 0],                     
        [img_width * 0.8, 0],                         
        [img_width * 0.8, img_height]               
    ])

    img_w = warp(img_m, src, dst)
    cv2.imwrite('warped.jpg', img_w)
    hist = calculate_histogram(img_w)

    '''############################# Pixel detection #############################'''
    minv = cv2.getPerspectiveTransform(dst, src)
    left_fit, right_fit = sliding_window(img_w, hist)
    lane_overlay = draw_lane(test, img_w, left_fit, right_fit, minv)
    #Uncomment to see plot img
    #plt.imshow(lane_overlay)
    #plt.show()
    cv2.imwrite("final_image.jpg", cv2.cvtColor(lane_overlay, cv2.COLOR_RGB2BGR))


if __name__ == '__main__':
    main()