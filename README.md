## Writeup Template

### You use this file as a template for your writeup.

---

**Lane Finding Project**

The goals / steps of this project are the following:

* Compute the camera calibration matrix and distortion coefficients given a set of chessboard images.
* Apply a distortion correction to raw images.
* Use color transforms, gradients, etc., to create a thresholded binary image.
* Apply a perspective transform to rectify binary image ("birds-eye view").
* Detect lane pixels and fit to find the lane boundary.
* Determine the curvature of the lane and vehicle position with respect to center.
* Warp the detected lane boundaries back onto the original image.
* Output visual display of the lane boundaries and numerical estimation of lane curvature and vehicle position.

[//]: # (Image References)

[image1]: ./examples/undistort_output.png "Undistorted"
[image2]: ./test_images/test1.jpg "Road Transformed"
[image3]: ./examples/binary_combo_example.jpg "Binary Example"
[image4]: ./examples/warped_straight_lines.jpg "Warp Example"
[image5]: ./examples/color_fit_lines.jpg "Fit Visual"
[image6]: ./examples/example_output.jpg "Output"
[video1]: ./project_video.mp4 "Video"

---

### Writeup / README

#### 1. Provide a Writeup that includes all the rubric points and how you addressed each one.

You're reading it!

### Camera Calibration

#### 1. Briefly state how you computed the camera matrix and distortion coefficients. Provide an example of a distortion corrected calibration image.
    In the "calibrate" function

    1.1 Preparing Object Points:
        A 3D grid of real-world coordinates is created to represent the chessboard's corner positions on the calibration pattern, assuming all z-coordinates are 0.

    1.2 Detecting Chessboard Corners:
        - Each calibration image is read and resized to a consistent resolution (1280x720).
        - The image is converted to grayscale to simplify processing and enhance detection accuracy.
        - Using cv2.findChessboardCorners() to detect the inner corners

    1.3 Calibrate the Camera
        - Passing object points and image points alongside the image size to cv2.calibrateCamera()
        - This function calculates camera matrix, distortion coefficients and rotation/translation vectors required to map real-world coordinates to the image plane.

| Before | After |
| ------------- | ------------- |
| ![Chessboard_image](camera_cal/calibration1.jpg) | ![Calibrated_chessboard_image](undistorted_chessboard.jpg) |

#### 2. Describe how (and identify where in your code) you used color transforms, gradients or other methods to create a thresholded binary image.  Provide an example of a binary image result.

    In the "binary_threshold" function

    2.1 Color Transforms :
        - Converting input image from RGB to HLS color space.
        - L channel is used for detecting edges via gradients as it represents lightness 
        - S channel is used to isolate lane lines based on their color intensity

    2.2 Edge Detection :
        - Applying Sobel operator to grayscale L channel in the x-direction (lines are vertical)
        - Threshold is as such to keep only strong edges, that way the lines will stand out

    2.3 Combining Thresholds
        - Ensures lines detection in different conditions

    2.4 RoI Masking :
        - Applying polygonal mask to limit the region of interest, in road images it is a trapezoidal covering the road.

| Before  | After |
| ------------- | ------------- |
| ![Binary Threshold](test_images/test2.jpg)| ![Binary Threshold Applied](masked.jpg) |

#### 3. Describe how (and identify where in your code) you performed a perspective transform and provide an example of a transformed image.

In the "warp" function

A perspective transform was applied to the binary thresholded image to create a bird's-eye view of the road. Process involved mapping a region of interest in the original image to a new perspective.

    3.1 Defining the Source and Destination Points :
        - Source points represent a trapezoidal region in the original image where lane lines are located
        - Destination points define the corresponding points in a rectangle in the bird's-eye view image
        - Source and destination points were calculated so that we can warp images of different size with same efficiency 

    3.2 Perspective Transform Function :
        - cv2.getPerspectiveTransform() computes the transformation matrix that maps the source points to destination points
        - cv2.warpPerspective() applies the transformation matrix to the image, warping it to the new perspective


![Bird's-eye view](warped.jpg "Bird's-eye view")

#### 4. Describe how (and identify where in your code) you identified lane-line pixels and fit their positions with a polynomial?

In the "calculate_histogram" "find_lane_bases" "sliding_window" functions

Lane-line pixels were identified and their positions were fit using a histogram-based sliding window tehnique followed by polynomial fitting.

    4.1 Creating a Histogram to Locate Lane Bases :
        -Histogram is created as the sum of pixel intensities along the vertical axis for the bottom half of the warped binary image. Peaks in the histogram indicate the lines on the side of the lane.

    4.2 Identifying Lane Pixels using Sliding Windows : 
        - Sliding window method identifies pixels belonging to the left and right lane lines. Process is next:
            - Window Initialization: dividing binary image into nwindows vertical segments, setting window height and width, initializing starting x-positions for the left and right lane lines using find_lane_bases()
            - Iterating Through Windows: for each window, we define its boundaries in x and y directions, identify all non-zero pixels within each window, if enough pixels are detected, recenter the window to the mean x-position of detected pixels for the next level

    4.3 Fit Lane Line Pixels with a Polynomial : np.polyfit()

#### 5. Describe how (and identify where in your code) you calculated the radius of curvature of the lane and the position of the vehicle with respect to center.

In the "draw_lane" function

    5.1 Radius of Curvature :
        - Converting pixel values to real-world space using scaling factors (example: ym_per_pix - meters per pixel in the y-direction (30 meters for 720 pixels)). Fitting a new polynomial (np.polyfit()) for both lane lines in a real-world space. Using the formula for radius of curvature to calculate the radius
    
    5.2 Vehicle Position with Respect to the Center :
        - Calculating the lane center as the midpoint between the bottom x-intercepts of the left and right polynomials
        - Subtract the image center (assuming to align with the vehicle's camera center) from the lane center
        - Convert the offset to meters using xm_per_pix


#### 6. Provide an example image of your result plotted back down onto the road such that the lane area is identified clearly.

![Lane detection output](final_image.jpg "Final output")

### Pipeline (video)

#### 1. Provide a link to your final video output.  Your pipeline should perform reasonably well on the entire project video (wobbly lines are ok but no catastrophic failures that would cause the car to drive off the road!).

TODO: Add your text here!!!

### Discussion

#### 1. Briefly discuss any problems / issues you faced in your implementation of this project.  Where will your pipeline likely fail?  What could you do to make it more robust?

Shadows were a challenge in detecting lanes on some images, as they made distinguishing the lane markings more difficult. Additionally, calculating the necessary matrices was a complex and time-consuming process.
Weather conditions, such as rain or fog, as well as nighttime scenarios, would likely make the pipeline fail. Since there were no test images with strong curves, I couldn't evaluate how well the pipeline would handle those situations, but it’s likely that bigger curves could cause issues.
To further enhance the robustness of the system, combining data from multiple sensors, such as lidar, radar, infrared sensors etc. could provide additional information and make the pipeline more adaptable to different road conditions.

