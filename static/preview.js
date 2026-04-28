document.addEventListener('DOMContentLoaded', function() {
    initializePreview();
});

function initializePreview() {
    const video = document.getElementById('processedVideo');
    const downloadLink = document.getElementById('downloadLink');
    const brightnessPlot = document.getElementById('BrightnessPlot');

    const urlParams = new URLSearchParams(window.location.search);
    const videoFilename = urlParams.get('video');
    const plotFilename = urlParams.get('plot');
    
    console.log('Video filename from URL:', videoFilename);
    console.log('Plot filename from URL:', plotFilename);
    
    const videoUrl = videoFilename ? '/processed/' + videoFilename : '/processed/' + getFilenameFromPath();
    const plotUrl = plotFilename ? '/preview/' + plotFilename : '/preview/analysis_plot.png';

    console.log('Video URL:', videoUrl);
    console.log('Plot URL:', plotUrl);

    if (video && videoFilename) {
    const videoUrl = '/processed/' + videoFilename;
    video.src = videoUrl;
    
    if (downloadLink) {
        downloadLink.href = videoUrl;
        downloadLink.download = 'zebra_processed_' + videoFilename;
    }
    }

    if (brightnessPlot && plotUrl) {
        brightnessPlot.src = plotUrl;
        brightnessPlot.onerror = function() {
            console.error('Failed to load plot:', plotUrl);
            this.style.display = 'none';
        };
    }

    if (video) {
        video.addEventListener('canplay', function() {
            console.log('Video can play');
            updateVideoInfo(this);
        });

        video.addEventListener('loadedmetadata', function() {
            console.log('Video metadata loaded - dimensions:', this.videoWidth + 'x' + this.videoHeight);
            updateVideoInfo(this);
        });

        video.addEventListener('loadstart', function() {
            console.log('Video load started');
        });

        video.addEventListener('progress', function() {
            console.log('Video loading progress');
        });

        video.addEventListener('error', function(e) {
            console.error('Video error:', {
                error: e,
                networkState: this.networkState,
                readyState: this.readyState,
                errorCode: this.error ? this.error.code : 'no error code'
            });
            showError('Video format may not be supported by your browser');
        });


        video.addEventListener('play', function() {
            console.log('Video started playing');
        });
    }

    video.addEventListener('click', function() {
        if (this.paused) {
            this.play().catch(e => {
                console.log('Manual play blocked:', e);
                showError('Please click the play button to start video');
            });
        }
    });
}

function getFilenameFromPath() {
    const path = window.location.pathname;
    return path.split('/').pop() || 'video.mp4';
}

function updateVideoInfo(videoElement) {
    const durationElement = document.getElementById('videoDuration');
    const resolutionElement = document.getElementById('videoResolution');
    
    if (videoElement) {
        console.log('Updating video info:', {
            duration: videoElement.duration,
            width: videoElement.videoWidth,
            height: videoElement.videoHeight
        });
        
        if (durationElement) {
            durationElement.textContent = videoElement.duration ? 
                videoElement.duration.toFixed(1) + 's' : 'N/A';
        }
        if (resolutionElement) {
            resolutionElement.textContent = 
                videoElement.videoWidth + '×' + videoElement.videoHeight;
        }
    }
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #e74c3c;
        color: #fff;
        padding: 15px 20px;
        border-radius: 8px;
        font-size: 12px;
        z-index: 1000;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    `;
    errorDiv.textContent = 'ERROR: ' + message;
    
    document.body.appendChild(errorDiv);
    
    setTimeout(() => {
        if (document.body.contains(errorDiv)) {
            document.body.removeChild(errorDiv);
        }
    }, 5000);
}

