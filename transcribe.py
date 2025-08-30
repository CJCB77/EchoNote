"""
Send audio files to openai transcription models
and write text files based on response.
Handles large audio files by compressing, splitting on silence,
and transcribing in chunks.
"""
from openai import OpenAI
from dotenv import load_dotenv
from pydub import AudioSegment, silence
import os
import tempfile
import shutil

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OPENAI_MODEL = "gpt-4o-transcribe"

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

def transcribe_large_audio(audio_path):
    """
    Splits a large audio file into manageable chunks based on silence,
    transcribes them using OpenAI's Transcribe API, and saves the combined transcript.
    """
    print("Transcribing large audio file. This may take some time...")
    audio = AudioSegment.from_file(audio_path)

    # --- FIX: Create a temporary directory instead of a single locked file ---
    temp_dir = tempfile.mkdtemp()
    try:
        # 1. --- Compress and Convert Audio to M4A ---
        print(f"Step 1/4: Loading and compressing audio file: {audio_path}")
        temp_m4a_path = os.path.join(temp_dir, "compressed.m4a")
        audio.export(temp_m4a_path, format="ipod")
        compressed_audio = AudioSegment.from_file(temp_m4a_path, format="m4a")

        # 2. --- Split Audio on Silence ---
        print("Step 2/4: Splitting audio into chunks based on silence...")
        chunks = silence.split_on_silence(
            compressed_audio,
            min_silence_len=700,
            silence_thresh=compressed_audio.dBFS - 16,
            keep_silence=300
        )
        if not chunks:
            print("Could not find any chunks to split.")
            return None

        # 3. --- Group Small Chunks into Larger Segments ---
        print("Step 3/4: Grouping chunks into processable segments...")
        target_length_ms = 5 * 60 * 1000
        processed_chunks = []
        current_chunk = AudioSegment.empty()
        for chunk in chunks:
            if len(current_chunk) + len(chunk) < target_length_ms:
                current_chunk += chunk
            else:
                processed_chunks.append(current_chunk)
                current_chunk = chunk
        if len(current_chunk) > 0:
            processed_chunks.append(current_chunk)
        print(f"-> Split into {len(processed_chunks)} segments for transcription.")

        # 4. --- Transcribe Each Processed Chunk ---
        full_transcript = ""
        num_chunks = len(processed_chunks)
        for i, chunk in enumerate(processed_chunks, start=1):
            print(f"Step 4/4: Transcribing segment {i} of {num_chunks}...")
            
            # --- FIX: Use our temporary directory for chunk files ---
            chunk_path = os.path.join(temp_dir, f"chunk_{i}.m4a")
            chunk.export(chunk_path, format="ipod")

            # Transcribe
            with open(chunk_path, "rb") as audio_file:
                try:
                    res = client.audio.transcriptions.create(
                        model=OPENAI_MODEL,
                        file=audio_file
                    )
                    full_transcript += res.text + " "
                except Exception as e:
                    print(f"   -> Error transcribing chunk {i}: {e}")

    finally:
        # --- FIX: Clean up the temporary directory and all its contents ---
        print("Cleaning up temporary files...")
        shutil.rmtree(temp_dir)

    # --- Save the final transcript ---
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    txt_path = f"./transcriptions/{base_name}.txt"
    os.makedirs(os.path.dirname(txt_path), exist_ok=True)
    with open(txt_path, "w", encoding='utf-8') as f: # Added encoding for broader compatibility
        f.write(full_transcript.strip())
        
    return txt_path
