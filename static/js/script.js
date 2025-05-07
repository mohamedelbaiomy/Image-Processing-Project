document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    let currentFilename = null;
    let currentTaskId = null;
    let currentHistoryId = null;
    let currentParams = {};
    let activePreset = null;
    let processingInterval = null;

    // Initialize UI elements
    const uploadForm = document.getElementById('upload-form');
    const imageInput = document.getElementById('image-input');
    const fileNameSpan = document.getElementById('file-name');
    const originalImage = document.getElementById('original-image');
    const enhancedImage = document.getElementById('enhanced-image');
    const applyBtn = document.getElementById('apply-btn');
    const resetBtn = document.getElementById('reset-btn');
    const downloadBtn = document.getElementById('download-btn');
    const generateVisBtn = document.getElementById('generate-vis-btn');

    // Frequency domain presets
    const presets = {
        smooth: {
            filter_type: 'lowpass',
            filter_class: 'gaussian',
            cutoff: 20,
            order: 2,
            normalize: true,
            sharpen: false
        },
        sharpen: {
            filter_type: 'highpass',
            filter_class: 'butterworth',
            cutoff: 15,
            order: 3,
            normalize: true,
            sharpen: true,
            sharpen_amount: 1.5
        },
        bandpass: {
            filter_type: 'bandpass',
            filter_class: 'butterworth',
            cutoff: 30,
            band_width: 15,
            order: 2,
            normalize: true,
            sharpen: false
        }
    };

    // Initialize the application
    init();

    function init() {
        setupEventListeners();
        updateFilterTypeUI(document.querySelector('input[name="filter_type"]:checked').value);
        updateSharpenControls();
    }

    function setupEventListeners() {
        // File upload
        imageInput.addEventListener('change', handleFileSelect);
        uploadForm.addEventListener('submit', handleUpload);

        // Main buttons
        applyBtn.addEventListener('click', applyEnhancement);
        resetBtn.addEventListener('click', resetParameters);
        downloadBtn.addEventListener('click', downloadEnhancedImage);

        // Filter controls
        document.querySelectorAll('input[name="filter_type"]').forEach(radio => {
            radio.addEventListener('change', function() {
                updateFilterTypeUI(this.value);
            });
        });

        document.getElementById('sharpen').addEventListener('change', updateSharpenControls);

        // Parameter controls
        document.querySelectorAll('input[type="range"]').forEach(input => {
            input.addEventListener('input', updateParamValueDisplay);
            input.addEventListener('change', updateCurrentParams);
        });

        document.querySelectorAll('input[type="checkbox"]').forEach(input => {
            input.addEventListener('change', updateCurrentParams);
        });

        // Preset buttons
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                applyPreset(this.getAttribute('data-preset'));
            });
        });

        // Visualization button
        generateVisBtn.addEventListener('click', generateVisualization);

        // Main tabs
        document.querySelectorAll('.main-tab').forEach(tab => {
            tab.addEventListener('click', function() {
                switchTab(this.getAttribute('data-tab'));
            });
        });

        // Parameter tabs
        document.querySelectorAll('.tab-btn').forEach(tab => {
            tab.addEventListener('click', function() {
                switchParameterTab(this.getAttribute('data-tab'));
            });
        });
    }

    function handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            fileNameSpan.textContent = file.name;
            applyBtn.disabled = false;
            generateVisBtn.disabled = false;

            // Create preview
            const reader = new FileReader();
            reader.onload = function(e) {
                originalImage.src = e.target.result;
            };
            reader.readAsDataURL(file);
        }
    }

    // Fix for the file upload handling
function handleUpload(event) {
    event.preventDefault();

    if (!imageInput.files || imageInput.files.length === 0) {
        showError('Please select an image to upload.');
        return;
    }

    const file = imageInput.files[0];
    // Check file type
    if (!file.type.match('image.*')) {
        showError('Please select a valid image file.');
        return;
    }

    // Check file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
        showError('File is too large. Maximum size is 10MB.');
        return;
    }

    showLoading('Uploading image...');

    // Reset existing images
    if (enhancedImage.src) {
        enhancedImage.src = '/static/img/placeholder.jpg';
    }

    const formData = new FormData();
    formData.append('image', file);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server responded with status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Upload response:', data);
        if (data.success && data.filename) {
            currentFilename = data.filename;
            originalImage.src = `/static/uploads/${currentFilename}?t=${new Date().getTime()}`;
            showSuccess('Image uploaded successfully');
            applyBtn.disabled = false;
            generateVisBtn.disabled = false;
        } else {
            throw new Error(data.error || 'Error uploading image: No filename returned');
        }
    })
    .catch(error => {
        console.error('Upload error:', error);
        showError(`Error uploading image: ${error.message}`);
    })
    .finally(() => {
        hideLoading();
    });
}

    // Fix for the applyEnhancement function
    function applyEnhancement() {
    if (!currentFilename) {
        showError('Please upload an image first.');
        return;
    }

    showLoading('Applying enhancement...');
    applyBtn.disabled = true;
    downloadBtn.disabled = true; // Disable download until enhancement is complete

    const params = getCurrentParams();
    console.log('Enhancement parameters:', params);
    console.log('Current filename:', currentFilename);

    fetch('/enhance', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            filename: currentFilename,
            params: params
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server responded with status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Enhancement response:', data);
        if (data.success) {
            if (data.task_id) {
                currentTaskId = data.task_id;
                pollTaskStatus(data.task_id);
            } else if (data.result_filename) {
                updateEnhancedImage(data.result_filename);
                showSuccess('Enhancement completed');
                hideLoading();
            } else {
                throw new Error('No result filename or task ID in response');
            }
        } else {
            throw new Error(data.error || 'Error enhancing image');
        }
    })
    .catch(error => {
        console.error('Enhancement error:', error);
        showError(`Error enhancing image: ${error.message}`);
        hideLoading();
    })
    .finally(() => {
        applyBtn.disabled = false;
    });
}

// Fix for pollTaskStatus function
async function pollTaskStatus(taskId) {
    const MAX_ATTEMPTS = 120; // 2 minutes max
    const RETRY_DELAY = 1000; // 1 second
    let attempts = 0;
    let lastProgress = 0;

    // Show loading state
    showLoading('Processing image...');
    applyBtn.disabled = true;

    const checkStatus = async () => {
        attempts++;

        try {
            const response = await fetch(`/task/${taskId}`);
            if (!response.ok) throw new Error(`Server error: ${response.status}`);

            const data = await response.json();

            // Update progress if changed
            if (data.progress !== lastProgress) {
                lastProgress = data.progress;
                updateProgress(data.progress);

                // Update loading message based on progress
                if (data.progress < 50) {
                    showLoading('Loading and processing image...');
                } else if (data.progress < 80) {
                    showLoading('Applying enhancements...');
                } else {
                    showLoading('Finalizing results...');
                }
            }

            // Handle completion
            if (data.status === 'completed') {
                if (!data.result_filename) {
                    throw new Error('Server completed but provided no result');
                }

                // Load the enhanced image with verification
                const imgUrl = `/static/results/${data.result_filename}?t=${Date.now()}`;
                const img = await loadAndVerifyImage(imgUrl);

                // Update UI
                enhancedImage.src = imgUrl;
                downloadBtn.href = imgUrl;
                downloadBtn.download = `enhanced_${currentFilename || 'image.jpg'}`;

                showSuccess('Enhancement completed successfully!');
                return true; // Success
            }
            else if (data.status === 'failed') {
                throw new Error(data.error || 'Enhancement failed');
            }

            // Continue polling if not done
            if (attempts < MAX_ATTEMPTS) {
                setTimeout(checkStatus, RETRY_DELAY);
            } else {
                throw new Error('Processing timeout. Please try again.');
            }
        } catch (error) {
            showError(error.message);
            console.error('Task error:', error);
            return false; // Failure
        } finally {
            if (attempts >= MAX_ATTEMPTS ||
                (lastProgress === 100 && !enhancedImage.src.includes('placeholder'))) {
                hideLoading();
                applyBtn.disabled = false;
            }
        }
    };

    await checkStatus();
}

// Robust image loading with verification
function loadAndVerifyImage(url, maxRetries = 3) {
    return new Promise((resolve, reject) => {
        let retries = 0;

        function attemptLoad() {
            const img = new Image();
            img.onload = () => {
                // Additional verification for black images
                const canvas = document.createElement('canvas');
                canvas.width = img.width;
                canvas.height = img.height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0);

                // Check if image is completely black
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                const data = imageData.data;
                let allBlack = true;

                for (let i = 0; i < data.length; i += 4) {
                    if (data[i] !== 0 || data[i+1] !== 0 || data[i+2] !== 0) {
                        allBlack = false;
                        break;
                    }
                }

                if (allBlack) {
                    if (retries++ < maxRetries) {
                        console.warn('Received black image, retrying...');
                        setTimeout(attemptLoad, 1000 * retries);
                    } else {
                        reject(new Error('Enhanced image appears to be blank'));
                    }
                } else {
                    resolve(img);
                }
            };

            img.onerror = () => {
                if (retries++ < maxRetries) {
                    setTimeout(attemptLoad, 1000 * retries);
                } else {
                    reject(new Error('Failed to load image'));
                }
            };

            img.src = url;
        }

        attemptLoad();
    });
}
// Enhanced image verification with retries

 // Fix for the updateEnhancedImage function
function updateEnhancedImage(filename) {
    if (!filename) {
        console.error('No filename provided for enhanced image');
        showError('Error loading enhanced image: No filename received from server');
        return;
    }

    const timestamp = new Date().getTime();
    console.log(`Loading enhanced image: /static/results/${filename}?t=${timestamp}`);

    // Make sure the filename is valid
    enhancedImage.onerror = function() {
        console.error(`Failed to load enhanced image: ${filename}`);
        showError('Enhanced image could not be loaded. Please try again or check server logs.');
        enhancedImage.src = '/static/img/placeholder.jpg'; // Fallback image
    };

    enhancedImage.onload = function() {
        console.log('Enhanced image loaded successfully');
        downloadBtn.disabled = false;
    };

    enhancedImage.src = `/static/results/${filename}?t=${timestamp}`;
    downloadBtn.href = `/static/results/${filename}`;
    downloadBtn.download = `enhanced_${currentFilename || 'image'}`;
    }

    function downloadEnhancedImage() {
        if (!enhancedImage.src.includes('placeholder')) {
            // The download happens automatically via the anchor tag
            showSuccess('Download started');
        }
    }

    function generateVisualization() {
        if (!currentFilename) {
            showError('Please upload an image first.');
            return;
        }

        showLoading('Generating visualization...');

        const params = {
            visualize: true,
            spectrum_scale: document.getElementById('spectrum-scale').value,
            show_grid: document.getElementById('show-grid').checked,
            ...getCurrentParams()
        };

        fetch('/enhance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filename: currentFilename,
                params: params
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (data.task_id) {
                    currentTaskId = data.task_id;
                    pollVisualizationStatus(data.task_id);
                } else {
                    updateVisualizationImages(data);
                    showSuccess('Visualization generated');
                }
            } else {
                showError(data.error || 'Error generating visualization');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Error generating visualization');
        });
    }

    function pollVisualizationStatus(taskId) {
        const checkStatus = () => {
            fetch(`/task/${taskId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateProgress(data.progress);

                        if (data.status === 'completed') {
                            updateVisualizationImages(data);
                            showSuccess('Visualization generated');
                            clearInterval(statusInterval);
                            hideLoading();
                        } else if (data.status === 'failed') {
                            showError(data.error || 'Visualization failed');
                            clearInterval(statusInterval);
                            hideLoading();
                        }
                    } else {
                        showError(data.error || 'Error checking status');
                        clearInterval(statusInterval);
                        hideLoading();
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showError('Error checking status');
                    clearInterval(statusInterval);
                    hideLoading();
                });
        };

        const statusInterval = setInterval(checkStatus, 1000);
        checkStatus(); // Initial check
    }

    function updateVisualizationImages(data) {
        const timestamp = new Date().getTime();
        
        document.getElementById('vis-original-image').src = `/static/uploads/${currentFilename}?t=${timestamp}`;
        
        if (data.spectrum_filename) {
            document.getElementById('spectrum-image').src = `/static/visualizations/${data.spectrum_filename}?t=${timestamp}`;
        }
        
        if (data.mask_filename) {
            document.getElementById('mask-image').src = `/static/visualizations/${data.mask_filename}?t=${timestamp}`;
        }
    }

    function getCurrentParams() {
        return {
            filter_type: document.querySelector('input[name="filter_type"]:checked').value,
            filter_class: document.querySelector('input[name="filter_class"]:checked').value,
            cutoff: parseFloat(document.getElementById('cutoff-frequency').value),
            order: parseInt(document.getElementById('filter-order').value),
            band_width: parseInt(document.getElementById('bandwidth').value),
            normalize: document.getElementById('normalize').checked,
            sharpen: document.getElementById('sharpen').checked,
            sharpen_amount: parseFloat(document.getElementById('sharpen-amount').value)
        };
    }

    function updateCurrentParams() {
        currentParams = getCurrentParams();
    }

    function updateParamValueDisplay(event) {
        const input = event.target;
        const valueSpan = document.getElementById(`${input.id}-value`);
        if (valueSpan) {
            valueSpan.textContent = input.value;
        }
    }

    function updateFilterTypeUI(filterType) {
        const bandwidthGroup = document.getElementById('bandwidth-group');
        bandwidthGroup.style.display = filterType === 'bandpass' ? 'block' : 'none';

        const cutoffLabel = document.querySelector('label[for="cutoff-frequency"]');
        switch(filterType) {
            case 'lowpass':
                cutoffLabel.textContent = 'Cutoff Frequency (D0):';
                break;
            case 'highpass':
                cutoffLabel.textContent = 'Cutoff Frequency (D0):';
                break;
            case 'bandpass':
                cutoffLabel.textContent = 'Center Frequency (D0):';
                break;
        }
    }

    function updateSharpenControls() {
        const sharpenCheckbox = document.getElementById('sharpen');
        const sharpenAmount = document.getElementById('sharpen-amount');
        sharpenAmount.disabled = !sharpenCheckbox.checked;
    }

    function applyPreset(presetName) {
        if (!presets[presetName]) return;

        const preset = presets[presetName];
        activePreset = presetName;

        // Update UI to match preset
        document.querySelector(`input[name="filter_type"][value="${preset.filter_type}"]`).checked = true;
        document.querySelector(`input[name="filter_class"][value="${preset.filter_class}"]`).checked = true;

        document.getElementById('cutoff-frequency').value = preset.cutoff;
        document.getElementById('cutoff-frequency-value').textContent = preset.cutoff;

        document.getElementById('filter-order').value = preset.order;
        document.getElementById('filter-order-value').textContent = preset.order;

        if (preset.band_width) {
            document.getElementById('bandwidth').value = preset.band_width;
            document.getElementById('bandwidth-value').textContent = preset.band_width;
        }

        document.getElementById('normalize').checked = preset.normalize;
        document.getElementById('sharpen').checked = preset.sharpen;

        if (preset.sharpen_amount) {
            document.getElementById('sharpen-amount').value = preset.sharpen_amount;
            document.getElementById('sharpen-amount-value').textContent = preset.sharpen_amount;
        }

        updateFilterTypeUI(preset.filter_type);
        updateSharpenControls();
        updateCurrentParams();

        // Highlight active preset button
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`.preset-btn[data-preset="${presetName}"]`).classList.add('active');

        // Apply if image is loaded
        if (currentFilename) {
            applyEnhancement();
        }
    }

    function resetParameters() {
        // Reset to default values
        document.querySelector('input[name="filter_type"][value="lowpass"]').checked = true;
        document.querySelector('input[name="filter_class"][value="butterworth"]').checked = true;

        document.getElementById('cutoff-frequency').value = 30;
        document.getElementById('cutoff-frequency-value').textContent = '30';

        document.getElementById('filter-order').value = 2;
        document.getElementById('filter-order-value').textContent = '2';

        document.getElementById('bandwidth').value = 10;
        document.getElementById('bandwidth-value').textContent = '10';

        document.getElementById('normalize').checked = true;
        document.getElementById('sharpen').checked = false;
        document.getElementById('sharpen-amount').value = 1.0;
        document.getElementById('sharpen-amount-value').textContent = '1.0';

        updateFilterTypeUI('lowpass');
        updateSharpenControls();
        updateCurrentParams();

        // Clear active preset
        activePreset = null;
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // Apply if image is loaded
        if (currentFilename) {
            applyEnhancement();
        }
    }

    function switchTab(tabName) {
        // Update active tab
        document.querySelectorAll('.main-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`.main-tab[data-tab="${tabName}"]`).classList.add('active');

        // Show corresponding content
        document.querySelectorAll('.main-tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');

        // Load history if needed
        if (tabName === 'history') {
            loadHistory();
        }
    }

    function switchParameterTab(tabName) {
        // Update active tab
        document.querySelectorAll('.tab-btn').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`.tab-btn[data-tab="${tabName}"]`).classList.add('active');

        // Show corresponding content
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');
    }

    function loadHistory() {
        const historyList = document.getElementById('history-list');
        historyList.innerHTML = '<div class="history-empty">Loading history...</div>';

        fetch('/history')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.history && data.history.length > 0) {
                    historyList.innerHTML = '';
                    data.history.forEach(entry => {
                        const entryElement = createHistoryEntry(entry);
                        historyList.appendChild(entryElement);
                    });
                } else {
                    historyList.innerHTML = '<div class="history-empty">No history entries yet</div>';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                historyList.innerHTML = '<div class="history-empty">Error loading history</div>';
            });
    }

    function createHistoryEntry(entry) {
        const entryElement = document.createElement('div');
        entryElement.className = 'history-entry';
        entryElement.dataset.id = entry.id;

        entryElement.innerHTML = `
            <div class="history-entry-info">
                <div class="history-entry-title">${entry.filter_type} ${entry.filter_class}</div>
                <div class="history-entry-date">${new Date(entry.timestamp).toLocaleString()}</div>
            </div>
            <img class="history-entry-thumbnail" src="/static/results/${entry.result_filename}" alt="Enhanced image">
        `;

        entryElement.addEventListener('click', () => {
            showHistoryDetail(entry);
        });

        return entryElement;
    }

    function showHistoryDetail(entry) {
        currentHistoryId = entry.id;

        document.querySelectorAll('.history-entry').forEach(e => e.classList.remove('active'));
        document.querySelector(`.history-entry[data-id="${entry.id}"]`).classList.add('active');

        document.querySelector('.history-detail-empty').style.display = 'none';
        document.querySelector('.history-detail-content').style.display = 'block';

        document.getElementById('history-detail-title').textContent = 
            `${entry.filter_type} ${entry.filter_class} Filter`;

        document.getElementById('history-original-image').src = `/static/uploads/${entry.original_filename}`;
        document.getElementById('history-enhanced-image').src = `/static/results/${entry.result_filename}`;

        document.getElementById('history-download-btn').href = `/static/results/${entry.result_filename}`;
        document.getElementById('history-download-btn').download = `enhanced_${entry.original_filename}`;

        renderHistoryParameters(entry);
    }

    function renderHistoryParameters(entry) {
        const paramsList = document.getElementById('history-parameters-list');
        paramsList.innerHTML = '';

        const parameters = [
            { name: 'Filter Type', value: entry.filter_type },
            { name: 'Filter Class', value: entry.filter_class },
            { name: 'Cutoff Frequency', value: entry.cutoff },
            { name: 'Filter Order', value: entry.order },
            { name: 'Normalized', value: entry.normalize ? 'Yes' : 'No' },
            { name: 'Sharpened', value: entry.sharpen ? 'Yes' : 'No' }
        ];

        if (entry.filter_type === 'bandpass') {
            parameters.push({ name: 'Bandwidth', value: entry.band_width });
        }

        parameters.forEach(param => {
            const item = document.createElement('div');
            item.className = 'parameter-item';
            item.innerHTML = `
                <div class="parameter-name">${param.name}</div>
                <div class="parameter-value">${param.value}</div>
            `;
            paramsList.appendChild(item);
        });
    }

    function addToHistory(historyId) {
        // In a real app, we might update the history list
        // For now, we'll just reload the history if we're on that tab
        if (document.querySelector('.main-tab.active').getAttribute('data-tab') === 'history') {
            loadHistory();
        }
    }

    function showLoading(message) {
        const loadingOverlay = document.getElementById('loading-overlay');
        const loadingText = document.getElementById('loading-text');
        
        loadingText.textContent = message || 'Processing...';
        loadingOverlay.style.display = 'flex';
    }

    function hideLoading() {
        document.getElementById('loading-overlay').style.display = 'none';
    }

    function updateProgress(progress) {
        const progressBar = document.getElementById('progress-bar');
        const progressText = document.getElementById('progress-text');
        
        progressBar.style.width = `${progress}%`;
        progressText.textContent = `${progress}%`;
    }

    function showError(message) {
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.innerHTML = `
            ${message}
            <span class="close-error">&times;</span>
        `;

        document.body.appendChild(errorElement);

        errorElement.querySelector('.close-error').addEventListener('click', () => {
            errorElement.remove();
        });

        setTimeout(() => {
            if (document.body.contains(errorElement)) {
                errorElement.remove();
            }
        }, 5000);
    }

    function showSuccess(message) {
        const successElement = document.createElement('div');
        successElement.className = 'error-message';
        successElement.style.backgroundColor = '#4CAF50';
        successElement.innerHTML = `
            ${message}
            <span class="close-error">&times;</span>
        `;

        document.body.appendChild(successElement);

        successElement.querySelector('.close-error').addEventListener('click', () => {
            successElement.remove();
        });

        setTimeout(() => {
            if (document.body.contains(successElement)) {
                successElement.remove();
            }
        }, 3000);
    }
});
