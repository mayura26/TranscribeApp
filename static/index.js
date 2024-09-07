$(document).ready(function () {
    var socket = io();
    var transcriptionInProgress = false;
    var currentFilename = null;
    var isQuickTest = false;

    // Initialize audio player
    const audioPlayer = document.getElementById('audioPlayer');

    socket.on('transcription_progress', function (data) {
        $('#progress').width(data.progress + '%').text(data.progress + '%');
    });

    socket.on('transcription_complete', function (data) {
        $('#progress').width('100%').text('100%');
        var transcriptionText = data.transcription;
        if (data.quick_test) {
            transcriptionText = "(Quick Test - First Minute Only)\n\n" + transcriptionText;
        }
        $('#transcription').text(transcriptionText);
        transcriptionInProgress = false;
        $('#cancel-button').hide();
        $('#play-button').show();
        $('#transcribe-button').show();
    });

    socket.on('transcription_error', function (data) {
        alert('Transcription error: ' + data.error);
        transcriptionInProgress = false;
        $('#cancel-button').hide();
        $('#play-button').show();
        $('#transcribe-button').show();
    });

    socket.on('transcription_cancelled', function () {
        alert('Transcription cancelled');
        $('#progress').width('0%').text('0%');
        $('#transcription').text('');
        transcriptionInProgress = false;
        $('#cancel-button').hide();
        $('#play-button').show();
        $('#transcribe-button').show();
    });

    $('#upload-form').on('submit', function (e) {
        e.preventDefault();
        var formData = new FormData(this);

        // Explicitly set the quick_test value
        formData.set('quick_test', $('#quick-test').prop('checked'));

        $.ajax({
            url: '/',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            xhr: function() {
                var xhr = new window.XMLHttpRequest();
                xhr.upload.addEventListener("progress", function(evt) {
                    if (evt.lengthComputable) {
                        var percentComplete = evt.loaded / evt.total;
                        $('#uploadProgress').show().val(percentComplete * 100);
                    }
                }, false);
                return xhr;
            }
        })
        .done(function(data) {
            $('#uploadStatus').text('Upload successful!').show();
            $('#uploadProgress').hide();
            
            console.log("Server response:", data);  // Debug log
            
            if (data.audio_url) {
                audioPlayer.src = data.audio_url;
                audioPlayer.style.display = 'block';
                audioPlayer.load();
                console.log("Audio URL set:", audioPlayer.src);  // Debug log
            } else {
                console.error("No audio URL provided in the response");
            }

            currentFilename = data.filename;
            isQuickTest = data.quick_test;
            $('#transcribe-button').show();
            $('#progress').width('0%').text('0%');
            $('#transcription').text(isQuickTest ?
                'File shortened to 1 minute. Audio ready to play. Click "Transcribe" to start transcription.' :
                'File uploaded. Audio ready to play. Click "Transcribe" to start transcription.');
        })
        .fail(function(jqXHR, textStatus, errorThrown) {
            $('#uploadStatus').text('Upload failed: ' + textStatus).show();
            $('#uploadProgress').hide();
            console.error("Upload error:", errorThrown);  // Debug log
        });
    });

    $('#play-button').on('click', function () {
        if (currentFilename) {
            window.location.href = '/play/' + currentFilename;
        }
    });

    $('#transcribe-button').on('click', function () {
        if (currentFilename && !transcriptionInProgress) {
            $.ajax({
                url: '/transcribe',
                type: 'POST',
                data: { filename: currentFilename },
                success: function (data) {
                    if (data.error) {
                        alert(data.error);
                    } else {
                        $('#progress').width('0%').text('0%');
                        $('#transcription').text('Transcription in progress...');
                        transcriptionInProgress = true;
                        $('#cancel-button').show();
                        $('#transcribe-button').hide();
                    }
                },
                error: function () {
                    alert('An error occurred while starting the transcription.');
                }
            });
        }
    });

    $('#cancel-button').on('click', function () {
        if (transcriptionInProgress) {
            socket.emit('cancel_transcription');
        }
    });

    $('#upload-form').submit(function(e) {
        e.preventDefault();
        var formData = new FormData(this);

        // Explicitly set the quick_test value
        formData.set('quick_test', $('#quick-test').prop('checked'));

        $.ajax({
            url: '/',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function (data) {
                if (data.error) {
                    alert(data.error);
                } else {
                    currentFilename = data.filename;
                    isQuickTest = data.quick_test;
                    $('#play-button').show();
                    $('#transcribe-button').show();
                    $('#progress').width('0%').text('0%');
                    $('#transcription').text(isQuickTest ?
                        'File shortened to 1 minute. Click "Play Audio" to listen or "Transcribe" to start transcription.' :
                        'File uploaded. Click "Play Audio" to listen or "Transcribe" to start transcription.');
                }
            },
            error: function () {
                alert('An error occurred during the file upload.');
            }
        }).done(function(data) {
            $('#uploadStatus').text('Upload successful!').show();
            $('#uploadProgress').hide();
            
            // Set the audio source and show the player
            audioPlayer.src = data.audio_url; // Assuming the server returns the audio URL
            audioPlayer.style.display = 'block';
            audioPlayer.load(); // Important: reload the audio element
        });
    });
});
