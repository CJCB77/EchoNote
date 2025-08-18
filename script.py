import sounddevice as sd
import logging
import wavio

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

# ─── 2) List available devices ──────────────────────────────────────
# for idx, dev in enumerate(sd.query_devices()):
#     print(
#       f"{idx:>2}: {dev['name']:<40}"
#       f"in={dev['max_input_channels']:<2}  "
#       f"out={dev['max_output_channels']:<2}"
#     )

# ─── 3) Record and playback sound ──────────────────────────────────
virtual_cable = 3

sd.default.device = virtual_cable

info = sd.query_devices(virtual_cable, 'input')
fs = info['default_samplerate']
channels = info['max_input_channels']

logger.info(f"Using input device: {info['name']}")
logger.info(f"Default samplerate: {fs}")
logger.info(f"Default channels: {channels}")

duration = 15 # seconds

# Record audio
logger.info(f"Recording for {duration} seconds @ {fs} Hz..")
my_recording = sd.rec(int(duration * fs), samplerate=fs, channels=channels)
sd.wait()

# Write it into a WAV file
wavio.write("recording.wav", my_recording, fs, sampwidth=2)



