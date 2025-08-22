"""
Send audio files to openai transcription models
and write text files based on response
"""
from openai import OpenAI
from dotenv import load_dotenv
import os
from pydub import AudioSegment

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OPENAI_MODEL = "gpt-4o-transcribe"

def compress_to_mp3(wav_path, mp3_path,bitrate="128k"):
    audio = AudioSegment.from_wav(wav_path)
    audio.export(mp3_path, format="mp3", bitrate=bitrate)
    size_mb = os.path.getsize(mp3_path) / (1024 * 1024)
    print(f"Compressed {wav_path} to {mp3_path} ({size_mb:.2f} MB)")
    return size_mb

def split_into_chunks(mp3_path, chunk_length_ms=10 * 60 * 1000):
    """Split into N-minutes chunks (default 10 minutes)"""
    audio = AudioSegment.from_file(mp3_path, format="mp3")
    base, _ = os.path.splitext(mp3_path)
    chunk_paths = []
    for i, start in enumerate(range(0, len(audio), chunk_length_ms)):
        chunk = audio[start: start + chunk_length_ms]
        chunk_path = f"{base}_{i}.mp3"
        chunk.export(chunk_path, format="mp3", bitrate="128k")
        size_mb = os.path.getsize(chunk_path) / (1024 * 1024)
        print(f" Chunk {i+1}: {chunk_path} ({size_mb:.2f} MB)")
        chunk_paths.append(chunk_path)

    return chunk_paths

def transcribe_and_save(audio_path):
    # Read binary file
    with open(audio_path, "rb") as audio_file:
        res = client.audio.transcriptions.create(
            model=OPENAI_MODEL,
            file=audio_file
        )

        # Buil a .txt filename
        base = "./transcriptions/test.txt"
        txt_path = base

        # Write a raw transcript
        with open(txt_path, "w") as f:
            f.write(res.text)
        
        return txt_path

