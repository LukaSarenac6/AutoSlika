import cv2
import numpy as np
def warper(img, src, dst):

    # Compute and apply perpective transform
    img_size = (img.shape[1], img.shape[0])
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, img_size, flags=cv2.INTER_NEAREST)  # keep same size as input image

    return warped

image_path = "examples/grayscale.jpg"
output_path = "wraped_imapge.jpg"

image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

if image is None:
    print('Erorcina')
else:
    # Define source and destination points
    src_points = np.float32([[50, 50], [200, 50], [50, 200], [200, 200]])
    dst_points = np.float32([[10, 100], [250, 100], [10, 300], [250, 300]])

    # Apply warper
    warped_image = warper(image, src_points, dst_points)

    # Save the warped image
    cv2.imwrite(output_path, warped_image)
    print(f"Warped image saved to {output_path}")

