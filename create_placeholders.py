import os
import numpy as np
import cv2

# Create required directories if they don't exist
img_dir = os.path.join('static', 'img')
uploads_dir = os.path.join('static', 'uploads')
results_dir = os.path.join('static', 'results')

os.makedirs(img_dir, exist_ok=True)
os.makedirs(uploads_dir, exist_ok=True)
os.makedirs(results_dir, exist_ok=True)

# Create placeholder image
placeholder_path = os.path.join(img_dir, 'placeholder.png')
if not os.path.exists(placeholder_path):
    # Create a gradient background with purple theme
    height, width = 300, 400
    placeholder = np.zeros((height, width, 3), dtype=np.uint8)

    # Create a gradient background
    for y in range(height):
        for x in range(width):
            # Purple gradient
            b = int(123 + (x / width) * 132)  # 123 to 255
            g = int(44 + (y / height) * 34)  # 44 to 78
            r = int(191 - (y / height) * 100)  # 191 to 91
            placeholder[y, x] = [b, g, r]

    # Add text
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(placeholder, 'No Image', (120, 150), font, 1, (255, 255, 255), 2)
    cv2.putText(placeholder, 'Upload an image to start', (70, 180), font, 0.6, (255, 255, 255), 1)

    # Save the image
    cv2.imwrite(placeholder_path, placeholder)
    print(f"Created {placeholder_path}")

# Create loading image
loading_path = os.path.join(img_dir, 'loading.png')
if not os.path.exists(loading_path):
    # Create a gradient background with purple theme
    height, width = 300, 400
    loading = np.zeros((height, width, 3), dtype=np.uint8)

    # Create a gradient background
    for y in range(height):
        for x in range(width):
            # Purple gradient
            b = int(123 + (x / width) * 132)  # 123 to 255
            g = int(44 + (y / height) * 34)  # 44 to 78
            r = int(191 - (y / height) * 100)  # 191 to 91
            loading[y, x] = [b, g, r]

    # Add text
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(loading, 'Processing...', (100, 150), font, 1, (255, 255, 255), 2)
    cv2.putText(loading, 'Please wait', (140, 180), font, 0.6, (255, 255, 255), 1)

    # Save the image
    cv2.imwrite(loading_path, loading)
    print(f"Created {loading_path}")

# Create favicon
favicon_path = os.path.join(img_dir, 'favicon.png')
if not os.path.exists(favicon_path):
    # Create a small purple icon
    size = 32
    favicon = np.zeros((size, size, 3), dtype=np.uint8)

    # Create a circular gradient
    center = size // 2
    for y in range(size):
        for x in range(size):
            # Calculate distance from center
            distance = np.sqrt((x - center) ** 2 + (y - center) ** 2)
            if distance <= center:
                # Purple gradient based on distance
                factor = 1 - (distance / center)
                b = int(123 + factor * 132)  # 123 to 255
                g = int(44 + factor * 34)  # 44 to 78
                r = int(91 + factor * 100)  # 91 to 191
                favicon[y, x] = [b, g, r]

    # Save the image
    cv2.imwrite(favicon_path, favicon)
    print(f"Created {favicon_path}")

print("All placeholder images created successfully!")