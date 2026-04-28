document.addEventListener('DOMContentLoaded', function() {
    initializeFileInput();
    
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleFormSubmit);
    }
});

function initializeFileInput() {
    const fileInput = document.getElementById('videoFile');
    const fileLabel = document.querySelector('.file-label');
    
    if (fileInput && fileLabel) {
        fileInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                fileLabel.textContent = this.files[0].name;
                fileLabel.style.color = '#27ae60';
                fileLabel.style.borderColor = '#27ae60';
            } else {
                fileLabel.textContent = 'SELECT VIDEO FILE';
                fileLabel.style.color = '#3498db';
                fileLabel.style.borderColor = '#3498db';
            }
        });
    }
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const submitBtn = this.querySelector('.submit-btn');
    const originalText = submitBtn.textContent;

    try {
        submitBtn.textContent = 'PROCESSING...';
        submitBtn.disabled = true;

        const response = await fetch('/process', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            window.location.href = result.preview_url;
        } else {
            showError(result.message || 'Processing failed');
        }
        
    } catch (error) {
        showError('Network error: ' + error.message);
    } finally {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
}

function showError(message) {
    alert('ERROR: ' + message);
}