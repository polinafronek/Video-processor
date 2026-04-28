from flask import Flask, render_template, jsonify, request, send_file
from werkzeug.utils import secure_filename
from video_processor import VideoPreprocessing
import os
import cv2

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
app.config['PREVIEW_FOLDER'] = 'previews'

for folder in [app.config['UPLOAD_FOLDER'], app.config['PROCESSED_FOLDER'], app.config['PREVIEW_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('main.html')

@app.route('/process', methods=['POST'])
def process():
    if 'video' not in request.files:
        return jsonify({'success': False, 'message': 'No video file uploaded'})
    
    video = request.files['video']
    if video.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})

    if not allowed_file(video.filename):
        return jsonify({'success': False, 'message': 'Wrong type of file'})
    
    filename = secure_filename(video.filename)
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    video.save(video_path)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        os.remove(video_path)
        return jsonify({'success': False, 'message': 'Cannot open video file'})
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    
    if fps <= 0 or frame_count <= 0:
        os.remove(video_path)
        return jsonify({'success': False, 'message': 'Invalid video file'})

    white_threshold = int(request.form.get('white_threshold', 230))
    black_threshold = int(request.form.get('black_threshold', 25))
    problem_type = request.form.get('problem_type', 'both')

    try:
        video_processor = VideoPreprocessing(
            path=video_path,
            white_threshold=white_threshold,
            black_threshold=black_threshold
        )

        output_filename = f'processed_{filename}'
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        
        result_path = video_processor.create_video_with_zebra(output_path, problem_type)
        
        if result_path:
            video_processing = video_processor.frame_preprocessing()
            if video_processing:
                plot = video_processor.analysis_plot(video_processing['frames_analysis'], app.config['PREVIEW_FOLDER'])
                plot_filename = os.path.basename(plot) if plot else 'analysis_plot.png'
            else:
                plot_filename = 'analysis_plot.png'

            return jsonify({
                'success': True,
                'preview_url': f'/preview_video?video={output_filename}&plot={plot_filename}'
            })
        else:
            return jsonify({'success': False, 'message': 'Video processing failed'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Processing error: {str(e)}'})

@app.route('/preview_video')  
def preview_video():
    video_filename = request.args.get('video', '')
    plot_filename = request.args.get('plot', 'analysis_plot.png')
    
    if not video_filename:
        return "Video filename required", 400
    
    return render_template('preview.html')

@app.route('/processed/<filename>')
def serve_processed_video(filename):
    base_name = filename.replace('.mp4', '')
    possible_paths = [
        os.path.join(app.config['PROCESSED_FOLDER'], f'{base_name}_mp4v.mp4'),
        os.path.join(app.config['PROCESSED_FOLDER'], f'{base_name}_MJPG.avi'),
        os.path.join(app.config['PROCESSED_FOLDER'], f'{base_name}_XVID.avi'),
        os.path.join(app.config['PROCESSED_FOLDER'], filename),
    ]
    
    for file_path in possible_paths:
        if os.path.exists(file_path):
            if file_path.endswith('.mp4'):
                mimetype = 'video/mp4'
            else:
                mimetype = 'video/x-msvideo'
                
            return send_file(file_path, mimetype=mimetype)
    
    return "Video file not found", 404

@app.route('/preview/<filename>')
def serve_preview(filename):
    return send_file(os.path.join(app.config['PREVIEW_FOLDER'], filename))

@app.route('/download/<filename>')
def download_video(filename):
    base_name = filename.replace('.mp4', '')
    possible_paths = [
        os.path.join(app.config['PROCESSED_FOLDER'], f'{base_name}_mp4v.mp4'),
        os.path.join(app.config['PROCESSED_FOLDER'], f'{base_name}_MJPG.avi'),
        os.path.join(app.config['PROCESSED_FOLDER'], f'{base_name}_XVID.avi'),
        os.path.join(app.config['PROCESSED_FOLDER'], filename),
    ]
    
    for file_path in possible_paths:
        if os.path.exists(file_path):
            return send_file(
                file_path,
                as_attachment=True,
                download_name=f'zebra_{os.path.basename(file_path)}'
            )
    
    return "File not found", 404

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080, threaded=True)