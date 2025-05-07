import os
import json
import time
from datetime import datetime
import shutil


class HistoryManager:
    """
    Manages the history of processed images, including their parameters and timestamps.
    """

    def __init__(self, history_folder, results_folder):
        """
        Initialize the history manager.

        Args:
            history_folder: Path to the folder where history data is stored
            results_folder: Path to the folder where result images are stored
        """
        self.history_folder = history_folder
        self.results_folder = results_folder
        self.history_file = os.path.join(history_folder, 'history.json')

        # Create folders if they don't exist
        os.makedirs(history_folder, exist_ok=True)

        # Initialize history data
        self.history = self._load_history()

    def _load_history(self):
        """Load history data from the history file."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading history: {e}")
                return []
        return []

    def _save_history(self):
        """Save history data to the history file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_entry(self, original_filename, result_filename, params):
        """
        Add a new entry to the history.

        Args:
            original_filename: Name of the original image file
            result_filename: Name of the enhanced image file
            params: Parameters used for enhancement

        Returns:
            The ID of the new history entry
        """
        # Generate a unique ID for this entry
        entry_id = str(int(time.time() * 1000))

        # Create a readable timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Create a descriptive name based on parameters
        descriptive_name = self._generate_descriptive_name(params)

        # Create the entry
        entry = {
            'id': entry_id,
            'timestamp': timestamp,
            'original_filename': original_filename,
            'result_filename': result_filename,
            'descriptive_name': descriptive_name,
            'params': params
        }

        # Add to history
        self.history.append(entry)

        # Save history
        self._save_history()

        return entry_id

    def get_history(self, limit=20):
        """
        Get the most recent history entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of history entries, most recent first
        """
        # Return entries in reverse chronological order
        return sorted(self.history, key=lambda x: x['timestamp'], reverse=True)[:limit]

    def get_entry(self, entry_id):
        """
        Get a specific history entry by ID.

        Args:
            entry_id: ID of the entry to retrieve

        Returns:
            The history entry, or None if not found
        """
        for entry in self.history:
            if entry['id'] == entry_id:
                return entry
        return None

    def delete_entry(self, entry_id):
        """
        Delete a history entry and its associated result file.

        Args:
            entry_id: ID of the entry to delete

        Returns:
            True if successful, False otherwise
        """
        entry = self.get_entry(entry_id)
        if not entry:
            return False

        # Remove the result file if it exists
        result_path = os.path.join(self.results_folder, entry['result_filename'])
        if os.path.exists(result_path):
            try:
                os.remove(result_path)
            except Exception as e:
                print(f"Error removing result file: {e}")

        # Remove the entry from history
        self.history = [e for e in self.history if e['id'] != entry_id]

        # Save history
        self._save_history()

        return True

    def clear_history(self):
        """
        Clear all history entries and remove associated result files.

        Returns:
            Number of entries cleared
        """
        count = len(self.history)

        # Remove all result files
        for entry in self.history:
            result_path = os.path.join(self.results_folder, entry['result_filename'])
            if os.path.exists(result_path):
                try:
                    os.remove(result_path)
                except Exception as e:
                    print(f"Error removing result file: {e}")

        # Clear history
        self.history = []

        # Save history
        self._save_history()

        return count

    def _generate_descriptive_name(self, params):
        """
        Generate a descriptive name based on enhancement parameters.

        Args:
            params: Enhancement parameters

        Returns:
            A descriptive name string
        """
        parts = []

        # Add filter type and class
        filter_type = params.get('filter_type', 'lowpass')
        filter_class = params.get('filter_class', 'butterworth')
        parts.append(f"{filter_class.capitalize()} {filter_type}")

        # Add cutoff frequency if present
        if 'cutoff' in params:
            parts.append(f"Cutoff: {params['cutoff']}")

        # Add order if present
        if 'order' in params and filter_class == 'butterworth':
            parts.append(f"Order: {params['order']}")

        # Add bandwidth if bandpass
        if filter_type == 'bandpass' and 'band_width' in params:
            parts.append(f"BW: {params['band_width']}")

        return " - ".join(parts)