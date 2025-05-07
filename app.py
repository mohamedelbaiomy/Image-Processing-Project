import os
import cv2
import threading
import time

import numpy as np
from flask import Flask, render_template, request, jsonify, send_from_directory
from matplotlib import pyplot as plt
from werkzeug.utils import secure_filename
from datetime import datetime
from filters.frequency_enhancement import FrequencyDomainEnhancement
from utils.image_utils import load_image, save_image
from utils.history_manager import HistoryManager
from utils.transform_utils import FourierTransformer
from utils.visualization import plot_frequency_components

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join('static', 'uploads')
RESULT_FOLDER = os.path.join('static', 'results')
VISUALIZATION_FOLDER = os.path.join('static', 'visualizations')
HISTORY_FOLDER = os.path.join('static', 'history')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)
os.makedirs(VISUALIZATION_FOLDER, exist_ok=True)
os.makedirs(HISTORY_FOLDER, exist_ok=True)

enhancer = FrequencyDomainEnhancement()
history_manager = HistoryManager(HISTORY_FOLDER, RESULT_FOLDER)
processing_tasks = {}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        cleanup_old_files(UPLOAD_FOLDER, max_files=50)

        if 'image' not in request.files:
            return jsonify(success=False, error='No file part')

        file = request.files['image']

        if file.filename == '':
            return jsonify(success=False, error='No selected file')

        allowed_extensions = {'png', 'jpg', 'jpeg', 'bmp', 'tif', 'tiff'}
        if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return jsonify(success=False, error='File type not allowed')

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{timestamp}_{secure_filename(file.filename)}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        file.save(file_path)

        if not os.path.exists(file_path):
            return jsonify(success=False, error='Failed to save file')

        try:
            test_image = cv2.imread(file_path)
            if test_image is None or test_image.size == 0:
                os.remove(file_path)
                return jsonify(success=False, error='File is not a valid image')
        except Exception as e:
            os.remove(file_path)
            return jsonify(success=False, error=f'Error opening image: {str(e)}')

        return jsonify(success=True, filename=filename)
    except Exception as e:
        print(f"Unexpected error in upload_file: {str(e)}")
        return jsonify(success=False, error=f'Server error: {str(e)}')


@app.route('/enhance', methods=['POST'])
def enhance_image():
    try:
        data = request.get_json()
        if not data:
            return jsonify(success=False, error='No JSON data received')

        filename = data.get('filename')
        if not filename:
            return jsonify(success=False, error='Filename is required')

        # Validate filename to prevent path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify(success=False, error='Invalid filename')

        params = data.get('params', {})

        # Validate enhancement parameters
        valid_filter_types = {'lowpass', 'highpass', 'bandpass'}
        if params.get('filter_type') not in valid_filter_types:
            return jsonify(success=False, error='Invalid filter type')

        task_id = f"task_{int(time.time() * 1000)}"
        task = {
            'id': task_id,
            'filename': filename,
            'params': params,
            'status': 'processing',
            'progress': 0,
            'start_time': time.time()
        }
        processing_tasks[task_id] = task

        thread = threading.Thread(
            target=process_enhancement_task,
            args=(task_id, filename, params)
        )
        thread.start()

        return jsonify(success=True, task_id=task_id)

    except Exception as e:
        return jsonify(success=False, error=str(e))


def process_enhancement_task(task_id, filename, params):
    task = processing_tasks.get(task_id)
    if not task:
        return

    try:
        # Initialize task with default values
        task.update({
            'status': 'processing',
            'progress': 0,
            'result_filename': None,
            'error': None,
            'last_update': time.time()
        })

        # Step 1: Load and validate source image (20% progress)
        task['progress'] = 20
        image_path = os.path.join(UPLOAD_FOLDER, filename)

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Source image not found at {image_path}")

        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if image is None:
            raise ValueError("Failed to decode image - possibly corrupt file")
        if image.size == 0:
            raise ValueError("Loaded image is empty")

        # Step 2: Apply enhancement (50% progress)
        task['progress'] = 50
        enhanced = enhancer.enhance(image, params)

        if enhanced is None:
            raise ValueError("Enhancement returned null result")
        if enhanced.size == 0:
            raise ValueError("Enhanced image is empty")

        # Convert to uint8 if needed
        if enhanced.dtype != np.uint8:
            enhanced = cv2.normalize(enhanced, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

        # Step 3: Save result with verification (80% progress)
        task['progress'] = 80
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        result_filename = f"enhanced_{timestamp}_{secure_filename(filename)}"
        result_path = os.path.join(RESULT_FOLDER, result_filename)

        # Ensure the directory exists
        os.makedirs(RESULT_FOLDER, exist_ok=True)

        # Save with explicit format and verification
        if not cv2.imwrite(result_path, enhanced):
            raise IOError("Failed to write enhanced image to disk")

        # Verify the saved image
        saved_img = cv2.imread(result_path)
        if saved_img is None or saved_img.size == 0:
            os.remove(result_path)
            raise IOError("Saved image verification failed - possibly corrupt")

        # Step 4: Finalize task (100% progress)
        task.update({
            'status': 'completed',
            'progress': 100,
            'result_filename': result_filename,
            'last_update': time.time()
        })

    except Exception as e:
        task.update({
            'status': 'failed',
            'error': str(e),
            'progress': 100,
            'last_update': time.time()
        })
        print(f"Task {task_id} failed: {str(e)}")
def create_visualization(original, enhanced, params, output_path):
    if len(original.shape) > 2:
        original = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)

    transformer = FourierTransformer()
    _, _, fft_shifted = transformer.compute_fft(original)

    mask = transformer.create_filter_mask(
        fft_shifted.shape,
        params.get('filter_type', 'lowpass'),
        params.get('filter_class', 'butterworth'),
        params.get('cutoff', 30),
        params.get('order', 2),
        params.get('band_width', 10)
    )

    title = f"{params.get('filter_class', 'butterworth').capitalize()} {params.get('filter_type', 'lowpass')} Filter"
    fig = plot_frequency_components(original, fft_shifted, mask, title)

    fig.savefig(output_path)
    plt.close(fig)


@app.route('/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    task = processing_tasks.get(task_id)
    if not task:
        return jsonify(success=False, error='Task not found'), 404

    # Check for stale tasks (older than 30 minutes)
    if time.time() - task.get('last_update', 0) > 1800:
        task['status'] = 'failed'
        task['error'] = 'Task timed out'

    response = {
        'success': True,
        'status': task['status'],
        'progress': task['progress'],
        'last_update': task.get('last_update')
    }

    if task['status'] == 'completed':
        # Verify the result file exists and is valid
        result_path = os.path.join(RESULT_FOLDER, task['result_filename'])
        try:
            img = cv2.imread(result_path)
            if img is None or img.size == 0:
                raise ValueError("Result image is invalid")
        except Exception as e:
            task['status'] = 'failed'
            task['error'] = f'Result verification failed: {str(e)}'
            return jsonify({
                'success': False,
                'status': 'failed',
                'error': task['error']
            }), 500

        response['result_filename'] = task['result_filename']

    elif task['status'] == 'failed':
        response['error'] = task.get('error', 'Unknown error')

    return jsonify(response)

@app.route('/history', methods=['GET'])
def get_history():
    try:
        history = history_manager.get_history()
        return jsonify(success=True, history=history)
    except Exception as e:
        return jsonify(success=False, error=str(e))


@app.route('/history/<entry_id>', methods=['GET'])
def get_history_entry(entry_id):
    try:
        entry = history_manager.get_entry(entry_id)
        if not entry:
            return jsonify(success=False, error='History entry not found')
        return jsonify(success=True, entry=entry)
    except Exception as e:
        return jsonify(success=False, error=str(e))


@app.route('/history/<entry_id>', methods=['DELETE'])
def delete_history_entry(entry_id):
    try:
        success = history_manager.delete_entry(entry_id)
        if not success:
            return jsonify(success=False, error='History entry not found')
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))


@app.route('/history', methods=['DELETE'])
def clear_history():
    try:
        count = history_manager.clear_history()
        return jsonify(success=True, count=count)
    except Exception as e:
        return jsonify(success=False, error=str(e))


def cleanup_old_files(folder, max_files=50):
    try:
        files = [os.path.join(folder, f) for f in os.listdir(folder)
                 if os.path.isfile(os.path.join(folder, f))]
        files.sort(key=lambda x: os.path.getmtime(x))
        if len(files) > max_files:
            for file_to_remove in files[:-max_files]:
                try:
                    os.remove(file_to_remove)
                except Exception as e:
                    print(f"Error removing file {file_to_remove}: {str(e)}")
    except Exception as e:
        print(f"Error cleaning up old files: {str(e)}")


@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)


if __name__ == '__main__':
    app.run(debug=True)
