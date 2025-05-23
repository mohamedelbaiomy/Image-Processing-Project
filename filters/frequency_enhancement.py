import cv2
import numpy as np
from utils.image_utils import normalize_image
from filters.advanced_filters import FrequencyDomainFilters


class FrequencyDomainEnhancement:
    """
    Comprehensive frequency domain image enhancement pipeline.
    Implements various frequency domain filters and enhancement techniques.
    """

    def __init__(self):
        self.filters = FrequencyDomainFilters()  # Initialize filters here

    def enhance(self, image, params=None):
        """
        Apply frequency domain enhancement based on parameters.

        Args:
            image: Input image
            params: Dictionary of enhancement parameters

        Returns:
            Enhanced image
        """
        if params is None:
            params = self.get_default_params()

        # Convert to grayscale if needed and ensure proper type
        if len(image.shape) > 2:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image = image.astype(np.float32) / 255.0  # Normalize to [0,1]

        # Apply selected filter
        result = self.filters.apply_filter(
            image,
            params.get('filter_type', 'lowpass'),
            params.get('filter_class', 'butterworth'),
            params.get('cutoff', 30),
            params.get('order', 2),
            params.get('band_width', 10)
        )

        # Post-processing
        if params.get('normalize', True):
            result = normalize_image(result)

        if params.get('sharpen', False):
            result = self._apply_sharpening(result)

        # Convert back to 8-bit
        return (result * 255).astype(np.uint8)

    def _apply_sharpening(self, image):
        """Apply mild sharpening to enhance filtered results"""
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        return cv2.filter2D(image, -1, kernel)

    def get_default_params(self):
        """Get default enhancement parameters"""
        return {
            'filter_type': 'lowpass',
            'filter_class': 'butterworth',
            'cutoff': 30,
            'order': 2,
            'band_width': 10,
            'normalize': True,
            'sharpen': False
        }