import cv2
import numpy as np

from utils.image_utils import normalize_image


def compute_fft(image):
    """
    Compute the 2D Fourier Transform of an image with proper scaling.

    Args:
        image: Input image (grayscale)

    Returns:
        Tuple of (magnitude_spectrum, phase_spectrum, fft_shifted)
    """
    # Convert to float32 and normalize to [0,1]
    float_img = image.astype(np.float32) / 255.0

    # Apply 2D DFT
    dft = cv2.dft(float_img, flags=cv2.DFT_COMPLEX_OUTPUT)

    # Shift the zero frequency component to center
    dft_shifted = np.fft.fftshift(dft)

    # Compute magnitude and phase spectra
    magnitude, phase = cv2.cartToPolar(dft_shifted[:, :, 0], dft_shifted[:, :, 1])

    # Log scale for visualization
    magnitude_spectrum = 20 * np.log(magnitude + 1e-5)  # Add small value to avoid log(0)

    return magnitude_spectrum, phase, dft_shifted


class FourierTransformer:
    """Handles Fourier Transform operations with proper scaling"""

    @staticmethod
    def compute_ifft(fft_shifted):
        """
        Compute inverse Fourier Transform with proper scaling.

        Args:
            fft_shifted: Shifted FFT coefficients

        Returns:
            Reconstructed image in uint8 format
        """
        # Unshift the frequencies
        fft_unshifted = np.fft.ifftshift(fft_shifted)

        # Compute inverse DFT
        img_back = cv2.idft(fft_unshifted)
        img_back = cv2.magnitude(img_back[:, :, 0], img_back[:, :, 1])

        # Normalize and convert to uint8
        img_back = cv2.normalize(img_back, None, 0, 255, cv2.NORM_MINMAX)
        return img_back.astype(np.uint8)

    # ... rest of the class remains the same ...
    def create_filter_mask(self, shape, filter_type='lowpass', filter_class='ideal',
                           cutoff=30, order=2, band_width=10):
        """
        Create frequency domain filter mask.

        Args:
            shape: Shape of the mask (rows, cols, 2)
            filter_type: 'lowpass', 'highpass', or 'bandpass'
            filter_class: 'ideal', 'butterworth', or 'gaussian'
            cutoff: Cutoff frequency (D0)
            order: Order for Butterworth filter
            band_width: Width for bandpass filter

        Returns:
            Filter mask
        """
        rows, cols = shape[:2]
        center_row, center_col = rows // 2, cols // 2
        mask = np.zeros(shape, np.float32)

        for u in range(rows):
            for v in range(cols):
                D = np.sqrt((u - center_row) ** 2 + (v - center_col) ** 2)

                if filter_type == 'lowpass':
                    if filter_class == 'ideal':
                        if D <= cutoff:
                            mask[u, v] = (1.0, 1.0)
                    elif filter_class == 'butterworth':
                        H = 1 / (1 + (D / cutoff) ** (2 * order))
                        mask[u, v] = (H, H)
                    elif filter_class == 'gaussian':
                        H = np.exp(-(D ** 2) / (2 * (cutoff ** 2)))
                        mask[u, v] = (H, H)

                elif filter_type == 'highpass':
                    if filter_class == 'ideal':
                        if D > cutoff:
                            mask[u, v] = (1.0, 1.0)
                    elif filter_class == 'butterworth':
                        H = 1 / (1 + (cutoff / D) ** (2 * order)) if D > 0 else 0
                        mask[u, v] = (H, H)
                    elif filter_class == 'gaussian':
                        H = 1 - np.exp(-(D ** 2) / (2 * (cutoff ** 2)))
                        mask[u, v] = (H, H)

                elif filter_type == 'bandpass':
                    if filter_class == 'ideal':
                        if cutoff - band_width / 2 <= D <= cutoff + band_width / 2:
                            mask[u, v] = (1.0, 1.0)
                    elif filter_class == 'butterworth':
                        H = 1 / (1 + ((D * band_width) / (D ** 2 - cutoff ** 2)) ** (2 * order))
                        mask[u, v] = (H, H)
                    elif filter_class == 'gaussian':
                        H = np.exp(-((D ** 2 - cutoff ** 2) / (D * band_width)) ** 2)
                        mask[u, v] = (H, H)

        return mask