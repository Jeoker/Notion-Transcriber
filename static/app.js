let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let currentMode = 'event';

const recordBtn = document.getElementById('record-btn');
const statusText = document.getElementById('status');
const modeOptions = document.querySelectorAll('.mode-option');
const reviewModal = document.getElementById('review-modal');
const entryForm = document.getElementById('entry-form');
const eventFields = document.getElementById('event-fields');
const loadingIndicator = document.getElementById('loading-indicator');

// Mode Selection
modeOptions.forEach(opt => {
    opt.addEventListener('click', () => {
        modeOptions.forEach(o => o.classList.remove('active'));
        opt.classList.add('active');
        currentMode = opt.dataset.mode;
        statusText.textContent = `Hold to record ${currentMode}...`;
    });
});

// Audio Recording
async function initAudio() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        // Find supported MIME type
        const mimeTypes = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/ogg;codecs=opus',
            'audio/ogg',
            'audio/mp4',
            ''
        ];
        
        let selectedMimeType = '';
        for (const type of mimeTypes) {
            if (type === '' || MediaRecorder.isTypeSupported(type)) {
                selectedMimeType = type;
                break;
            }
        }
        
        console.log(`DEBUG: Selected MIME type: ${selectedMimeType || 'default'}`);
        
        const options = selectedMimeType ? { mimeType: selectedMimeType } : {};
        mediaRecorder = new MediaRecorder(stream, options);
        
        mediaRecorder.ondataavailable = event => {
            console.log(`DEBUG: Data available: ${event.data.size} bytes`);
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = processAudio;
    } catch (err) {
        console.error("Error accessing microphone:", err);
        statusText.textContent = "Mic access denied.";
    }
}

// Button Events (Hold to Record)
function startRecording(e) {
    if (e.cancelable) e.preventDefault();
    if (isRecording || !mediaRecorder) return;
    
    audioChunks = [];
    mediaRecorder.start(100); // Collect 100ms chunks to ensure data availability
    isRecording = true;
    recordBtn.classList.add('recording');
    statusText.textContent = "Recording... Release to process.";
}

function stopRecording(e) {
    if (e.cancelable) e.preventDefault();
    if (!isRecording) return;
    
    mediaRecorder.stop();
    isRecording = false;
    recordBtn.classList.remove('recording');
    statusText.textContent = "Processing...";
}

// Mouse/Touch Events
recordBtn.addEventListener('mousedown', startRecording);
recordBtn.addEventListener('touchstart', startRecording);
document.addEventListener('mouseup', stopRecording);
document.addEventListener('touchend', stopRecording);

// Process Audio
async function processAudio() {
    // Determine MIME type
    const mimeType = mediaRecorder.mimeType || 'audio/webm';
    console.log(`DEBUG: Recorder MIME type: ${mimeType}`);
    
    // Simple heuristic to get extension
    let extension = 'webm';
    if (mimeType.includes('mp4')) extension = 'mp4';
    else if (mimeType.includes('ogg')) extension = 'ogg';
    else if (mimeType.includes('wav')) extension = 'wav';
    
    if (audioChunks.length === 0) {
        console.error("ERROR: No audio chunks recorded");
        alert("Error: No audio recorded. Please hold the button longer.");
        closeModal();
        return;
    }

    const audioBlob = new Blob(audioChunks, { type: mimeType });
    console.log(`DEBUG: Final Audio Blob size: ${audioBlob.size} bytes, type: ${mimeType}`);
    
    if (audioBlob.size === 0) {
         console.error("ERROR: Blob size is 0");
         alert("Error: Recorded audio is empty.");
         closeModal();
         return;
    }
    
    const formData = new FormData();
    formData.append('audio', audioBlob, `recording.${extension}`);
    formData.append('mode', currentMode);

    // Show loading UI
    reviewModal.classList.add('visible');
    entryForm.classList.add('hidden');
    loadingIndicator.classList.remove('hidden');
    
    try {
        const response = await fetch('/api/process-audio', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('Processing failed');
        
        const result = await response.json();
        populateForm(result.draft);
        
    } catch (err) {
        console.error(err);
        alert("Error processing audio: " + err.message);
        closeModal();
    }
}

function populateForm(data) {
    loadingIndicator.classList.add('hidden');
    entryForm.classList.remove('hidden');
    
    document.getElementById('title').value = data.title || '';
    document.getElementById('content').value = data.description || data.content || '';
    
    if (currentMode === 'event') {
        eventFields.classList.remove('hidden');
        if (data.start_time) document.getElementById('start_time').value = formatDateTime(data.start_time);
        if (data.end_time) document.getElementById('end_time').value = formatDateTime(data.end_time);
    } else {
        eventFields.classList.add('hidden');
    }
}

function formatDateTime(isoString) {
    if (!isoString) return '';
    // Ensure format is YYYY-MM-DDTHH:MM
    return isoString.substring(0, 16);
}

// Modal Actions
document.getElementById('cancel-btn').addEventListener('click', closeModal);

document.getElementById('confirm-btn').addEventListener('click', async () => {
    const formData = {
        title: document.getElementById('title').value,
        content: document.getElementById('content').value, // Acts as description for event or content for idea
        description: document.getElementById('content').value 
    };
    
    if (currentMode === 'event') {
        formData.start_time = document.getElementById('start_time').value;
        formData.end_time = document.getElementById('end_time').value || null;
    }
    
    try {
        const response = await fetch('/api/save-entry', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                mode: currentMode,
                data: formData
            })
        });
        
        if (!response.ok) throw new Error('Save failed');
        
        alert('Saved successfully!');
        closeModal();
        statusText.textContent = "Saved! Hold to record again.";
        
    } catch (err) {
        console.error(err);
        alert("Error saving: " + err.message);
    }
});

function closeModal() {
    reviewModal.classList.remove('visible');
    statusText.textContent = `Hold to record ${currentMode}...`;
}

// Initialize
initAudio();
