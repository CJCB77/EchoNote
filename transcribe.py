"""
Send audio files to openai transcription models
and write text files based on response
"""
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OPENAI_MODEL = "gpt-4o-mini-transcribe"
audio_file = open("./recording.wav", "rb")

transcription = client.audio.transcriptions.create(
    model=OPENAI_MODEL,
    file=audio_file,
)

print(transcription.text)