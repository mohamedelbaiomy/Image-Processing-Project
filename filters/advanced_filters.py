import cv2
import numpy as np
from utils.transform_utils import FourierTransformer, compute_fft
from utils.image_utils import normalize_image


class FrequencyDomainFilters:
    """Implements various frequency domain filters"""

    def __init__(self):
        self.transformer = FourierTransformer()

    def apply_filter(self, image, filter_type='lowpass', filter_class='ideal',
                     cutoff=30, order=2, band_width=10):
        """
        Apply frequency domain filter to image.

        Args:
            image: Input image
            filter_type: 'lowpass', 'highpass', or 'bandpass'
            filter_class: 'ideal', 'butterworth', or 'gaussian'
            cutoff: Cutoff frequency
            order: Order for Butterworth filter
            band_width: Width for bandpass filter

        Returns:
            Filtered image
        """
        # Convert to grayscale if needed
        if len(image.shape) > 2:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Compute FFT
        _, _, fft_shifted = compute_fft(image)

        # Create filter mask
        mask = self.transformer.create_filter_mask(
            fft_shifted.shape, filter_type, filter_class,
            cutoff, order, band_width
        )

        # Apply mask
        filtered_fft = fft_shifted * mask

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