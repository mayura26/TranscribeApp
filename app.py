import os
import time
import threading
from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO
from pydub import AudioSegment
import wave
from openai import OpenAI
from dotenv import load_dotenv
import socket

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
socketio = SocketIO(app)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Set up OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Global variable to track cancellation
transcription_cancelled = False

MAX_CHUNK_SIZE = 24 * 1024 * 1024  # 24 MB to stay safely under the 25 MB limit

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        print("POST request received")
        print("Form data:", request.form)
        print("Files:", request.files)
        
        if 'file' not in request.files:
            print("No file part in the request")
            return jsonify({'error': 'No file part'})
        
        file = request.files['file']
        if file.filename == '':
            print("No selected file")
            return jsonify({'error': 'No selected file'})
        
        quick_test = request.form.get('quick_test') == 'true'
        print(f"Quick test: {quick_test}")  # Debug print
        
        if file:
            try:
                original_filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(original_filename)
                
                print(f"File saved at: {original_filename}")
                print(f"File exists: {os.path.exists(original_filename)}")
                print(f"File size: {os.path.getsize(original_filename)} bytes")  # Debug print
                
                # Convert to WAV if necessary
                wav_filename = convert_to_wav(original_filename)
                
                # Get audio duration
                audio = AudioSegment.from_wav(wav_filename)
                duration = len(audio) / 1000  # Duration in seconds
                print(f"Original duration: {duration:.2f} seconds")
                
                if quick_test:
                    print("Entering quick test mode")
                    # Limit duration to 60 seconds for quick test
                    duration = min(duration, 60)
                    audio = audio[:60000]  # Slice first 60 seconds
                    
                    # Save the shortened audio
                    shortened_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'shortened_' + os.path.basename(wav_filename))
                    audio.export(shortened_filename, format="wav")
                    
                    print(f"Shortened file saved at: {shortened_filename}")
                    print(f"Shortened file exists: {os.path.exists(shortened_filename)}")
                    print(f"Shortened file size: {os.path.getsize(shortened_filename)} bytes")  # Debug print
                    
                    # Verify the file length
                    with wave.open(shortened_filename, 'rb') as wav_file:
                        frames = wav_file.getnframes()
                        rate = wav_file.getframerate()
                        duration = frames / float(rate)
                    
                    print(f"Quick test: File shortened to {duration:.2f} seconds")
                    return jsonify({'message': 'File shortened', 'filename': os.path.basename(shortened_filename), 'quick_test': True})
                else:
                    print("Full file mode")
                    return jsonify({'message': 'File uploaded', 'filename': os.path.basename(wav_filename), 'quick_test': False})
            except Exception as e:
                # Print the full error traceback
                import traceback
                print(traceback.format_exc())
                return jsonify({'error': f'File processing error: {str(e)}'})
        else:
            print("File object is falsy")  # Debug print
            return jsonify({'error': 'No file provided'})
    
    return render_template('index.html')

def convert_to_wav(filename):
    try:
        audio = AudioSegment.from_file(filename)
        wav_filename = os.path.splitext(filename)[0] + '.wav'
        audio.export(wav_filename, format="wav")
        return wav_filename
    except Exception as e:
        print(f"Error converting file to WAV: {str(e)}")
        return filename  # Return original filename if conversion fails

@app.route('/play/<filename>')
def play_file(filename):
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    print(f"Attempting to play file: {full_path}")
    print(f"File exists: {os.path.exists(full_path)}")
    return send_file(full_path, as_attachment=True)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    filename = request.form.get('filename')
    language = request.form.get('language', 'en')  # Default to English if not specified
    if not filename:
        return jsonify({'error': 'No filename provided'})
    
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(full_path):
        return jsonify({'error': 'File not found'})
    
    quick_test = 'shortened_' in filename
    
    # Start a background task for transcription
    socketio.start_background_task(transcribe_audio, full_path, quick_test, language)
    
    return jsonify({'message': 'Transcription started'})

def transcribe_audio(filename, quick_test, language):
    global transcription_cancelled
    try:
        socketio.emit('transcription_progress', {'progress': 10})
        
        audio = AudioSegment.from_wav(filename)
        duration_ms = len(audio)
        chunk_size_ms = (MAX_CHUNK_SIZE / len(audio.raw_data)) * duration_ms
        
        chunks = []
        for start_ms in range(0, duration_ms, int(chunk_size_ms)):
            end_ms = min(start_ms + int(chunk_size_ms), duration_ms)
            chunk = audio[start_ms:end_ms]
            chunks.append(chunk)
        
        full_transcription = ""
        for i, chunk in enumerate(chunks):
            if transcription_cancelled:
                break
            
            chunk_file = f"temp_chunk_{i}.wav"
            chunk.export(chunk_file, format="wav")
            
            progress = 10 + (80 * i // len(chunks))
            socketio.emit('transcription_progress', {'progress': progress})
            
            with open(chunk_file, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file, 
                    language=language
                )
            
            full_transcription += transcript.text + " "
            
            os.remove(chunk_file)
        
        if not transcription_cancelled:
            socketio.emit('transcription_progress', {'progress': 90})
            socketio.emit('transcription_complete', {'transcription': full_transcription.strip(), 'quick_test': quick_test})
    except Exception as e:
        if not transcription_cancelled:
            socketio.emit('transcription_error', {'error': str(e)})
    finally:
        if not transcription_cancelled:
            socketio.emit('transcription_progress', {'progress': 100})
        transcription_cancelled = False

@socketio.on('cancel_transcription')
def handle_cancel_transcription():
    global transcription_cancelled
    transcription_cancelled = True
    socketio.emit('transcription_cancelled')

def get_local_ip():
    try:
        # This creates a socket and connects to a public DNS server
        # It doesn't actually send any data
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return '127.0.0.1'  # Fallback to localhost if we can't determine the IP

if __name__ == '__main__':
    local_ip = get_local_ip()
    print(f"Server running on http://{local_ip}:5000")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)