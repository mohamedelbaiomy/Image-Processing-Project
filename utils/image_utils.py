import cv2
import numpy as np


def load_image(file_path):
    """Load an image from file path"""
    image = cv2.imread(file_path)
    if image is None:
        raise ValueError(f"Could not load image from {file_path}")
    return image


def save_image(image, file_path):
    """Save an image to file path"""
    return cv2.imwrite(file_path, image)


def convert_to_grayscale(image):
    """Convert image to grayscale"""
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def normalize_image(image):
    """Normalize image to 0-255 range"""
    min_val = np.min(image)
    max_val = np.max(image)

    if max_val == min_val:
        return np.zeros_like(image, dtype=np.uint8)

    normalized = 255 * (image - min_val) / (max_val - min_val)
    return normalized.astype(np.uint8)


def clip_and_normalize(image):
    """Clip values to [0, 255] range and convert to uint8"""
    return np.clip(image, 0, 255).astype(np.uint8)