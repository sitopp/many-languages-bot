# -*- coding: utf-8 -*-
import os
import speech_recognition as sr
import googleapiclient.discovery #翻訳APIを使うためのライブラリ
import requests
# speech to text
import subprocess
from google.cloud import texttospeech
# Google AI Studio
import google.generativeai as genai
# text to speech
import pygame
pygame.mixer.init() # Pygameの初期化
import time
import json  # Used for working with JSON data
from langdetect import detect


# Initialize chat history and last interaction time
chat_history = []
last_interaction_time = time.time()

# APIキーの設定
genai.configure(api_key='xxxxx')

# レコーダーのインスタンス化
r = sr.Microphone()

# # Define constants for 11labs 
# CHUNK_SIZE = 1024  # Size of chunks to read/write at a time
# XI_API_KEY = "xxxxx"  # Your API key for authentication
# VOICE_ID = "xxxxx"  # ID of the voice model to use
# OUTPUT_PATH = "output.mp3"  # Path to save the output audio file
# # Construct the URL for the Text-to-Speech API request
# # tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"
# tts_url = "https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
# # Set up headers for the API request, including the API key for authentication
# elevenlabs_headers = {
#   "Accept": "audio/mpeg",
#   "Content-Type": "application/json",
#   "xi-api-key": XI_API_KEY
# }

# Function to get response from Gemini
def get_gemini_response(text, chat_history, detected_language):
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        # model_name="gemini-1.5-flash",
        model_name="gemini-1.5-pro",
        generation_config=generation_config,
    )

    # Convert chat history to the correct format
    formatted_history = [
        {"role": "user" if i % 2 == 0 else "model", "parts": [{"text": msg}]}
        for i, msg in enumerate(chat_history)
    ]

    # chat_session = model.start_chat(history=chat_history)
    chat = model.start_chat(history=formatted_history)

    prompt = f"Reply in {detected_language}. \
        140 characters or less. \
        Respond helpful way. \
        If you do not know the answer, do not answer halcination and answer honestly that you do not know. \
        content is ={text}\
        安全性に抵触する場合、Exceptionせずに、「答えられません」と回答してください。\
        You can not use emoji." 
        
        # Do not use emojis in your answers because it will be read by google text-to-speech. \
        # If it conflicts with the safety of google, please answer 'I can not answer' without Exception. \
        # 安全性に抵触する場合、Exceptionせずに、「答えられません」と回答してください。\
        # If you don't know the correct answer, you don't say lie. \

    response = chat.send_message(prompt)
    return response.text

# Function to reset conversation if timeout occurred
def reset_conversation_if_timeout():
    global chat_history, last_interaction_time
    current_time = time.time()
    if current_time - last_interaction_time > 30:  # 30 seconds timeout
        print("30秒以上経過したため、会話をリセットします。")
        chat_history = []
    last_interaction_time = current_time


while True:
    # Reset conversation if timeout occurred
    reset_conversation_if_timeout()


    # マイクからの音声を取得
    with r as source:
        print("話してください")
        audio = sr.Recognizer().record(source, duration=5) #待ち時間=5秒

    try:
        # GoogleのWebスピーチAPIを使用して音声をテキストに変換
        text = sr.Recognizer().recognize_google(audio, language='ja-JP')
        print("あなたが言ったこと: " + text)

        # 言語を検出
        detected_language = detect(text)
        print(f"検出された言語: {detected_language}")

        # Geminiから回答を得る
        response = get_gemini_response(text, chat_history,detected_language)
        print(response)

        # チャット履歴に追加 
        # chat_history.append({"role": "user", "content": text})
        # chat_history.append({"role": "assistant", "content": response})

        chat_history.append(text)
        chat_history.append(response)

        # Update last interaction time
        last_interaction_time = time.time()

        #回答内容を画面出力
        print("回答内容: " + response)

       
        # # google のText to speechの設定 (コメントアウトして残しとく)
        # Text-to-speech
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'xxx.json'
        client = texttospeech.TextToSpeechClient()
        

        # 言語に応じて音声設定を変更
        if detected_language.startswith('ja'):
            voice = texttospeech.VoiceSelectionParams(
                language_code="ja-JP",
                name="ja-JP-Wavenet-A",
            )
        elif detected_language.startswith('en'):
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name="en-US-News-K",
            )
        else:
            # その他の言語の場合はデフォルトの設定を使用
            voice = texttospeech.VoiceSelectionParams(
                language_code=detected_language
            )

        # 音声合成の設定
        synthesis_input = texttospeech.SynthesisInput(text=response)
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )


        # 音声合成の実行
        tts_response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        # 音声データを保存
        with open('output.mp3', 'wb') as out:
            out.write(tts_response.audio_content)


        # # elevenlabs の Text to speechの設定 コメントアウトして残しとく
        # TEXT_TO_SPEAK = response  # Text you want to convert to speech
        # # Set up the data payload for the API request, including the text and voice settings
        # data = {
        #     "text": TEXT_TO_SPEAK,
        #     "model_id": "eleven_turbo_v2_5",
        #     "voice_settings": {
        #         "stability": 0.5,
        #         "similarity_boost": 0.8,
        #         "style": 0.0,
        #         "use_speaker_boost": True
        #     }
        # }
        # # Make the POST request to the TTS API with headers and data, enabling streaming response
        # # response = requests.post(tts_url, headers=elevenlabs_headers, json=data, stream=True)
        # response = requests.post(tts_url, headers=elevenlabs_headers, json=data)
        # with open('output.mp3', 'wb') as f:
        #     for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
        #         if chunk:
        #             f.write(chunk)
                    
        # # Check if the request was successful
        # if response.ok:
        #     # Open the output file in write-binary mode
        #     with open(OUTPUT_PATH, "wb") as f:
        #         # Read the response in chunks and write to the file
        #         for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
        #             f.write(chunk)
        #     # Inform the user of success
        #     print("Audio stream saved successfully.")
        # else:
        #     # Print the error message if the request was not successful
        #     print(response.text)

            
        # 音声ファイルの再生
        pygame.mixer.music.load("output.mp3")
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            

    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))


