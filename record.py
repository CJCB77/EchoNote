import sounddevice as sd
import soundfile as sf
import logging
import queue
import argparse
import sys
import numpy as np
from datetime import datetime
from transcribe import transcribe_and_save

# ─── 1) Configure the root logger ───────────────────────────────────
LOG_FORMAT = "%(asctime)s %(levelname)-8s %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[
        logging.StreamHandler(),                       # console
        # logging.FileHandler("recorder.log"),         # uncomment to log to file
    ]
)
logger = logging.getLogger(__name__)

# List available audio devices argument
early_parser = argparse.ArgumentParser(add_help=False)
early_parser.add_argument('-l', '--list-devices', action='store_true',
                    help="List available audio devices")
args, remaining = early_parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    sys.exit(0)

# Real parser
parser = argparse.ArgumentParser(
    prog='EchoNote',
    description="Record audio from the system's default audio device",
    parents=[early_parser],
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument('-d', '--device', type=int, help="Input device ID", required=True)
parser.add_argument('-r', '--samplerate', type=int, help="Sampling rate")
parser.add_argument('-c', '--channels', type=int, help="Number of channels")
parser.add_argument('-f', '--filename', metavar='FILENAME', nargs='?',
                    help="Output audio file name")
parser.add_argument('-t', '--subtype', metavar='SUBTYPE', help="Sound file subtype(e.g. 'PCM_24')")
args = parser.parse_args(remaining)

# A thread-safe queue to transport audio blocks
q = queue.Queue()

def audio_callback(indata:np.ndarray, frames:int, time, status):
    """
    User-supplied function to consume audio in response to requests from an active stream
    """
    if status:
        logger.error(f"Stream error: {status}")
    # Deep copy the audio data
    q.put(indata.copy())

def main():
    """ Program that records system audio and writes it to a WAV file """
    device_info = sd.query_devices(args.device, 'input')
    if args.samplerate is None:
        args.samplerate = int(device_info['default_samplerate'])
    if args.channels is None:
        args.channels = int(device_info['max_input_channels'])
    if args.filename is None:
        args.filename = f"./recordings/rec-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.wav"
    if args.subtype is None:
        args.subtype = "PCM_24"

    try:
        # Sound files can be opened as SoundFile objects
        file = sf.SoundFile(
            file=args.filename,
            mode='x',
            samplerate=args.samplerate,
            channels=args.channels,
            subtype=args.subtype
        )
    except Exception as e:
        logger.error(f"Failed to open {args.filename} for writing: {e}")
        sys.exit(1)
    
    # Start the InputStream with our callback
    stream = sd.InputStream(
        device = args.device,
        samplerate = args.samplerate,
        channels = args.channels,
        callback = audio_callback
    )

    try:
        with stream:
            logger.info("Press Ctrl+C to stop the recording...")
            # Pull blocks fromt he queue
            while True:
                block = q.get()
                file.write(block)
    except KeyboardInterrupt:
        logger.info("Recording finished...")
    
    except Exception as e:
        logger.error(f"Error occurred during recording: {e}")
    
    finally:
        file.close()
        logger.info(f"Recording saved to {args.filename}")
    
    # Transcribe the audio file
    logger.info("Transcribing audio...")
    txt_path = transcribe_and_save(args.filename)
    logger.info(f"Transcript saved to {txt_path}")

if __name__ == "__main__":
    main()


