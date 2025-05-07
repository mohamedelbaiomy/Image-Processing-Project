import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties


def plot_frequency_components(image, fft_shifted, filter_mask=None, title=None):
    """
    Visualize frequency components and filter mask.

    Args:
        image: Original image
        fft_shifted: Shifted FFT coefficients
        filter_mask: Optional filter mask to visualize
        title: Plot title

    Returns:
        Matplotlib figure
    """
    # Compute magnitude spectrum
    magnitude = cv2.magnitude(fft_shifted[:, :, 0], fft_shifted[:, :, 1])
    magnitude_spectrum = 20 * np.log(magnitude + 1)

    # Set up figure
    fig, axes = plt.subplots(1, 2 + (1 if filter_mask is not None else 0),
                             figsize=(15, 5))

    # Configure font
    font = FontProperties()
    font.set_family('serif')
    font.set_size(12)

    # Plot original image
    axes[0].imshow(image, cmap='gray')
    axes[0].set_title('Original Image', fontproperties=font)
    axes[0].axis('off')

    # Plot magnitude spectrum
    axes[1].imshow(magnitude_spectrum, cmap='gray')
    axes[1].set_title('Frequency Spectrum', fontproperties=font)
    axes[1].axis('off')

    # Plot filter mask if provided
    if filter_mask is not None:
        mask_vis = cv2.magnitude(filter_mask[:, :, 0], filter_mask[:, :, 1])
        axes[2].imshow(mask_vis, cmap='gray')
        axes[2].set_title('Filter Mask', fontproperties=font)
        axes[2].axis('off')

    if title:
        fig.suptitle(title, fontsize=14, fontweight='bold')

    plt.tight_layout()
    return fig


def plot_filter_comparison(original, filtered_images, titles):
    """
    Compare multiple filtered versions of an image.

    Args:
        original: Original image
        filtered_images: List of filtered images
        titles: List of titles for each filtered image

    Returns:
        Matplotlib figure
    """
    num_filters = len(filtered_images)
    fig, axes = plt.subplots(1, num_filters + 1, figsize=(15, 5))

    # Configure font
    font = FontProperties()
    font.set_family('serif')
    font.set_size(10)

    # Plot original
    axes[0].imshow(original, cmap='gray')
    axes[0].set_title('Original', fontproperties=font)
    axes[0].axis('off')

    # Plot filtered images
    for i in range(num_filters):
        axes[i + 1].imshow(filtered_images[i], cmap='gray')
        axes[i + 1].set_title(titles[i], fontproperties=font)
        axes[i + 1].axis('off')

    plt.tight_layout()
    return fig