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

print(download_audio("https://youtu.be/_hdUddANh_o?si=lWg4-Qq2TDgXHofO"))