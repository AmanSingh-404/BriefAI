import yt_dlp
# pyrefly: ignore [missing-import]
from pydub import AudioSegment
import os

DWONLOAD_DIR = 'downloades' 
os.makedirs(DWONLOAD_DIR,exist_ok=True)

def download_audio(youtube_url: str) -> str:
    output_path = os.path.join(DWONLOAD_DIR,"%(title)s.%(ext)s")
    
    ydl_opts ={
        'format':"bestaudio/best",
        'outtmpl' : output_path,
        "postprocessors":[{
            'key':"FFmpegExtractAudio",
            "preferredcodec":"wav",
            "preferredquality":"192",
        }],
        "quiet":True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        filename = ydl.prepare_filename(info).replace(".webm", ".wav").replace(".m4a", ".wav")
    return filename

data = download_audio("https://youtu.be/_hdUddANh_o?si=lWg4-Qq2TDgXHofO")

def convert_to_wav(input_path:str) -> str:
    """convert any audio/video file to WAV format using pydub"""
    output_path=os.path.splitext(input_path)[0]+"_converted.wav"
    audio=AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(output_path,format="wav")
    return output_path

print(convert_to_wav(data))