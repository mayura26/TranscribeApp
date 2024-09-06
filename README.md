# TranscribeApp

TranscribeApp is an audio-to-text conversion application that helps users transcribe audio files into written text.

## Features

- Audio file upload
- Transcription of audio to text
- Support for multiple audio formats
- User-friendly interface
- Quick test mode for transcribing the first minute of audio
- Progress bar for transcription status
- Ability to cancel ongoing transcription

## Getting Started

### Prerequisites

- Python 3.7 or higher
- Flask
- Flask-SocketIO
- OpenAI API key
- pydub
- FFmpeg (for audio conversion)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/mayura26/TranscribeApp.git
   ```
2. Navigate to the project directory:
   ```bash
   cd TranscribeApp
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up your OpenAI API key:
   - Create a `.env` file in the project root
   - Add your API key: `OPENAI_API_KEY=your_api_key_here`

## Usage

1. Start the application:
   ```bash
   python app.py
   ```
2. Open a web browser and go to `http://localhost:5000` or the IP address displayed in the console.
3. Upload an audio file using the file input.
4. (Optional) Check the "Quick Test" box to transcribe only the first minute.
5. Click "Upload" to process the file.
6. Use the "Play Audio" button to listen to the uploaded file.
7. Click "Transcribe" to start the transcription process.
8. Monitor the progress bar for transcription status.
9. Once complete, the transcription will appear on the page.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Acknowledgments

- OpenAI for providing the Whisper API for audio transcription
- Flask and Flask-SocketIO for the web framework
- pydub for audio processing
