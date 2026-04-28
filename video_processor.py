import cv2
import numpy as np 
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
import os

class VideoPreprocessing:
    def __init__(self, path, white_threshold: int, black_threshold:int):
        self.path = path
        self.white_threshold = white_threshold
        self.black_threshold = black_threshold

    def frame_preprocessing(self):
        try:
            cap = cv2.VideoCapture(self.path)
            if not cap.isOpened():
                raise ValueError('Could not open the video')
            fps = cap.get(cv2.CAP_PROP_FPS)
            frames_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frames_count / fps 
            results = {
                'video_info': {
                    'fps': fps,
                    'frames_count': frames_count,
                    'duration': duration,
                    'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                },
                'frames_analysis': [],
            }

            frame_number = 0
            start_time = time.time()

            while (cap.isOpened()):
                ret, frame = cap.read()
                if ret is False:
                    break
            
                frame_description = self.analyze_frame(frame)
                frame_description['frame_number'] = frame_number
                frame_description['timestamp'] = frame_number / fps
                results['frames_analysis'].append(frame_description)
                frame_number += 1

                if time.time() - start_time > 300:
                    break
            
            cap.release()
            return results

        except Exception as e:
            print(f'Error: {e}')
            return None

    def analyze_frame(self, frame):
        gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        overexposed_mask = gray_image > self.white_threshold
        underexposed_mask = gray_image < self.black_threshold
        
        overexposed_pixels = np.sum(overexposed_mask)
        underexposed_pixels = np.sum(underexposed_mask)

        total_size = gray_image.size

        return {
            'average_brightness': np.mean(gray_image),
            'overexposed_area': (overexposed_pixels / total_size) * 100,
            'underexposed_area': (underexposed_pixels / total_size) * 100,
        }
    
    def analysis_plot(self, frame_analysis, preview_folder='previews'):
        times = [part['timestamp'] for part in frame_analysis]
        overexposed_areas = [part['overexposed_area'] for part in frame_analysis]
        underexposed_areas = [part['underexposed_area'] for part in frame_analysis]
        avg_brightness = [part['average_brightness'] for part in frame_analysis]

        plt.figure(figsize=(10,5))

        plt.plot(times, avg_brightness, color='y')
        plt.fill_between(times, 0, overexposed_areas, label='Overexposure', color='r', alpha=0.3)
        plt.fill_between(times, 0, underexposed_areas, label='Underexposure', color='b', alpha=0.3)
        plt.title('Video Brightness Analysis')
        plt.xlabel('Time, s')
        plt.ylabel('Brightness')
        plt.legend()

        os.makedirs(preview_folder, exist_ok=True)
            
        plot_path = os.path.join(preview_folder, 'analysis_plot.png')
        plt.savefig(plot_path, dpi=70, bbox_inches='tight')
        plt.close()
            
        return plot_path
        
    def create_zebralines(self, width, height, zebra_size=20):
        extra = zebra_size * 4
        mask_width = width + extra
        mask_height = height + extra
        
        zebra = Image.new("1", (mask_width, mask_height), "black")
        drawer = ImageDraw.Draw(zebra)

        for i in range(-mask_height, mask_width, 2 * zebra_size):
            drawer.line([(i, 0), (i + mask_height, mask_height)], 
                       fill='white', width=zebra_size)

        crop_zebra = zebra.crop((0, 0, width, height))
        zebra_array = np.array(crop_zebra)
        
        return zebra_array

    def apply_zebra(self, frame, problem_type, frame_number=0):
        frame_with_zebra = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        zebralines = self.create_zebralines(frame.shape[1], frame.shape[0])
        shift = frame_number % 40
        animated_zebra = np.roll(zebralines, shift, axis=1)

        if problem_type in ['both', 'underexposed']:
            underexposed_mask = gray < self.black_threshold
            frame_with_zebra[animated_zebra & underexposed_mask] = (255, 255, 255)
            frame_with_zebra[~animated_zebra & underexposed_mask] = (0, 0, 0)

        if problem_type in ['both', 'overexposed']:
            overexposed_mask = gray > self.white_threshold
            frame_with_zebra[animated_zebra & overexposed_mask] = (255, 255, 255)
            frame_with_zebra[~animated_zebra & overexposed_mask] = (0, 0, 0)
        
        return frame_with_zebra
    
    def create_video_with_zebra(self, output, problem_type='both'):
        try:
            cap = cv2.VideoCapture(self.path)
            if not cap.isOpened():
                return False
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if width > 1280 or height > 720:
                scale = min(1280.0 / width, 720.0 / height)
                width = int(width * scale)
                height = int(height * scale)
            
            codecs = [
                ('mp4v', '.mp4'),
                ('MJPG', '.avi'),
                ('XVID', '.avi'),
            ]
            
            output_path = None
            out = None
            
            for codec, ext in codecs:
                try:
                    output_path = output.replace('.mp4', f'_{codec}{ext}')
                    fourcc = cv2.VideoWriter_fourcc(*codec)
                    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
                    
                    if out.isOpened():
                        break
                    else:
                        out = None
                except:
                    continue
            
            if out is None:
                return False
                
            frame_number = 0
            max_frames = 3600 * 5
            
            while cap.isOpened() and frame_number < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                if frame.shape[1] != width or frame.shape[0] != height:
                    frame = cv2.resize(frame, (width, height))
                
                final_frame = self.apply_zebra(frame, problem_type, frame_number)
                out.write(final_frame)
                frame_number += 1
                
                if frame_number % 50 == 0:
                    import gc
                    gc.collect()
            
            cap.release()
            out.release()
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
                return output_path
            else:
                return False
                
        except Exception as e:
            print(f'Error: {e}')
            return False