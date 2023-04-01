from flask import Flask, render_template, request, send_file, flash
from flask_bootstrap import Bootstrap
from pytube import YouTube
import openai

#Using socketIO to for js interaction:
from flask_socketio import SocketIO, emit
from flask import session
import os
import requests

#chucking video:
from moviepy.video.io.VideoFileClip import VideoFileClip
from pydub import AudioSegment
import math

#chucking words of over 4000 tokens:
import nltk
from nltk.tokenize import sent_tokenize
from nltk.tokenize import word_tokenize


# Use your own API key
#openai.api_key = os.environ["OPENAI_API_KEY"]

transcript = []

conversation_history = []

bot_response = None

prompt = None

filepath = None

current_filepath = None


app = Flask(__name__)
app.config['SECRET_KEY'] = 'divine'
app.config['UPLOAD_FOLDER'] = 'static'

socketio = SocketIO(app)
Bootstrap(app)

@app.route('/')
def index():
    flash(f"😎:\n\n Hey there! Just a heads up, processing a 30-minute video may take about 2 minutes, and processing a one-hour video can take roughly 5 minutes.\n\n And when we chat, keep in mind that the response time might be a bit longer for longer videos. \n If you don't hear back from me within 2 minutes, don't worry, it's probably just a temporary network issue. Feel free to resend your question, and I'll get back to you as soon as possible!")
    flash(f"😎:\n\n Oh, and by the way, my system isn't quite capable of processing multilingual videos yet, so if you upload a video with more than one language, it might lead to a crash.")
    return render_template('inputpage.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')


# Upload video page
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    global transcript
    global prompt
    global bot_response
    global conversation_history
    global filepath
    global current_filepath


    if request.method == 'POST':

        if 'file' in request.files:
            file = request.files['file']
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Transcribe video and generate timestamped transcript
            transcript = transcribe_video(filepath)
            print(transcript)
            current_filepath = filepath
            return render_template('videov.html', video_url=filepath, transcript=transcript)


        elif 'youtube_link' in request.form:
            youtube_link = request.form['youtube_link']

            # Use pytube to download the YouTube video
            yt = YouTube(youtube_link)
            stream = yt.streams.get_highest_resolution()
            file = stream.download(output_path='static', filename='my_video.mp4')
            filepath = os.path.join('static', 'my_video.mp4')

            # Transcribe video and generate timestamped transcript
            transcript = transcribe_video(filepath)
            print(transcript)
            current_filepath = filepath
            return render_template('videov.html', video_url=filepath, transcript=transcript)

        return render_template('videov.html')
    else:

        return render_template('videov.html')


# Play video page
@app.route('/play/<path:video_url>')
def play(video_url):
    # Remove the extra 'static' directory from the file path
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], video_url.replace('static/', '', 1))
    return send_file(file_path, mimetype='video/mp4')


#For generating the transcript with wisper
def transcribe_video(filepath):

    video = VideoFileClip(filepath)
    segment_duration = 10 * 60  # seconds
    transcripts = []
    num_segments = math.ceil(video.duration / segment_duration)

    # Loop through the segments
    for i in range(num_segments):
        start_time = i * segment_duration
        end_time = min((i + 1) * segment_duration, video.duration)
        segment = video.subclip(start_time, end_time)
        segment_name = f"segment_{i+1}.mp3"
        segment.audio.write_audiofile(segment_name)

        # Pass the audio segment to WISPR for speech recognition
        audio = open(segment_name, "rb")
        transcripting = openai.Audio.transcribe("whisper-1", audio).text
        transcripts.append(transcripting)
        os.remove(segment_name)

    transcript = "\n".join(transcripts)
    return transcript



#opeanAI for the chat converation:
nltk.download('punkt')

@socketio.on('user_input')
def handle_conversation(user_input):

    global bot_response

    if len(word_tokenize(transcript)) <= 3000:

        print("Token count less = ", len(word_tokenize(str(transcript))))

        bot_response = generate_response(transcript, user_input)
        print(f"less than 3000 tokens = {bot_response}\n")

    else:

        print("Token count more = ", len(word_tokenize(transcript)))
        chunk_size = 3000
        chunks = []
        sentences = sent_tokenize(transcript)
        current_chunk = ""

        for sentence in sentences:
            tokens = nltk.word_tokenize(sentence)

            if len(current_chunk.split()) + len(tokens) <= chunk_size:
                current_chunk += " " + sentence

            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence

            print(f"TOKEN LENT OF unsent CHUNK = \n\n{len(word_tokenize(str(current_chunk.strip())))}\n\n\n")

        if current_chunk:
            chunks.append(current_chunk.strip())


        responses = []
        for chunk in chunks:
            response = generate_response(chunk, user_input)

            print(f"TOKEN LENT OF CHUNK = \n\n{len(word_tokenize(str(response)))}\n\n\n")

            responses.append(response)

        joined_response = ' '.join(responses)
        bot_response = generate_final_response(joined_response, user_input)

        print(f"final response bove 4000 = {bot_response}\n")

    socketio.emit('bot_response', bot_response)




#passing transcript or each chucks to chatgpt
def generate_response(transcript, user_input):

    prompt = f"From {transcript}. {user_input}. If no reference was provide, say so and provide an answer without the reference."

    completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "system", "content": "You provide accurate answers to users questions, You make it easy to understand and concise, Don't say anything unnecessary also sound friendly and infomal"},
            {"role": "user", "content": prompt}
    ]
    )
    bot_first_response = completion.choices[0].message.content

    return bot_first_response



#making the chuncks a coherent answer:
def generate_final_response(transcript, user_input):

    prompt = f"Search this {transcript} for the answer to this quesion {user_input}."

    completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "system", "content": "You provide accurate answers to users questions, You make it easy to understand and concise, Don't say anything unnecessary also sound friendly and infomal"},
            {"role": "user", "content": prompt}
    ]
    )
    bot_final_response = completion.choices[0].message.content

    print(bot_response)

    return bot_final_response



#Automatic delete video
@app.route('/delete_video', methods=['POST'])
def delete_video():
    global current_filepath

    if os.path.exists(current_filepath):
        os.remove(current_filepath)
        print("Dead & Gone")

    return "Ooops! Time out"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)


