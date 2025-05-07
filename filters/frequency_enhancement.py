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
        self.filters = FrequencyDomainFilters()

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

        # Convert to grayscale if needed
        if len(image.shape) > 2:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Get filter parameters
        filter_type = params.get('filter_type', 'lowpass')
        filter_class = params.get('filter_class', 'butterworth')
        cutoff = params.get('cutoff', 30)
        order = params.get('order', 2)
        band_width = params.get('band_width', 10)

        # Apply selected filter
        result = self.filters.apply_filter(
            image, filter_type, filter_class, cutoff, order, band_width
        )

        # Post-processing
        if params.get('normalize', True):
            result = normalize_image(result)

        if params.get('sharpen', False):
            result = self._apply_sharpening(result)

        return result

    def _apply_sharpening(self, image):
        """Apply mild sharpening to enhance filtered results"""
        kernel = np.array([[-1, -1, -1],
                           [-1, 9, -1],
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