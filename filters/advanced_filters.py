import cv2
import numpy as np
from utils.transform_utils import FourierTransformer, compute_fft
from utils.image_utils import normalize_image

import cv2
import numpy as np
from utils.transform_utils import FourierTransformer, compute_fft
from utils.image_utils import normalize_image


class FrequencyDomainFilters:
    """Implements various frequency domain filters with proper initialization"""

    def __init__(self):
        self.transformer = FourierTransformer()  # Initialize transformer here

    def apply_filter(self, image, filter_type='lowpass', filter_class='ideal',
                    cutoff=30, order=2, band_width=10):
        """
        Apply frequency domain filter to image with proper scaling.

        Args:
            image: Input image (normalized float32 in [0,1])
            filter_type: 'lowpass', 'highpass', or 'bandpass'
            filter_class: 'ideal', 'butterworth', or 'gaussian'
            cutoff: Cutoff frequency
            order: Order for Butterworth filter
            band_width: Width for bandpass filter

        Returns:
            Filtered image in float32 [0,1] range
        """
        # Compute FFT
        _, _, fft_shifted = compute_fft(image)

        # Create filter mask
        mask = self.transformer.create_filter_mask(
            fft_shifted.shape, filter_type, filter_class,
            cutoff, order, band_width
        )

        # Apply mask to both real and imaginary parts
        filtered_fft = np.zeros_like(fft_shifted)
        filtered_fft[:,:,0] = fft_shifted[:,:,0] * mask[:,:,0]
        filtered_fft[:,:,1] = fft_shifted[:,:,1] * mask[:,:,1]

        # Compute inverse FFT
        filtered_image = self.transformer.compute_ifft(filtered_fft)

        return filtered_image


    def ideal_lowpass(self, image, cutoff=30):
        """Apply ideal lowpass filter"""
        return self.apply_filter(image, 'lowpass', 'ideal', cutoff)

    def butterworth_lowpass(self, image, cutoff=30, order=2):
        """Apply Butterworth lowpass filter"""
        return self.apply_filter(image, 'lowpass', 'butterworth', cutoff, order)

    def gaussian_lowpass(self, image, cutoff=30):
        """Apply Gaussian lowpass filter"""
        return self.apply_filter(image, 'lowpass', 'gaussian', cutoff)

    def ideal_highpass(self, image, cutoff=30):
        """Apply ideal highpass filter"""
        return self.apply_filter(image, 'highpass', 'ideal', cutoff)

    def butterworth_highpass(self, image, cutoff=30, order=2):
        """Apply Butterworth highpass filter"""
        return self.apply_filter(image, 'highpass', 'butterworth', cutoff, order)

    def gaussian_highpass(self, image, cutoff=30):
        """Apply Gaussian highpass filter"""
        return self.apply_filter(image, 'highpass', 'gaussian', cutoff)

    def ideal_bandpass(self, image, cutoff=30, band_width=10):
        """Apply ideal bandpass filter"""
        return self.apply_filter(image, 'bandpass', 'ideal', cutoff, 2, band_width)

    def butterworth_bandpass(self, image, cutoff=30, band_width=10, order=2):
        """Apply Butterworth bandpass filter"""
        return self.apply_filter(image, 'bandpass', 'butterworth', cutoff, order, band_width)

    def gaussian_bandpass(self, image, cutoff=30, band_width=10):
        """Apply Gaussian bandpass filter"""
        return self.apply_filter(image, 'bandpass', 'gaussian', cutoff, 2, band_width)