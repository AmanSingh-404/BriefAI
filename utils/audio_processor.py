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

data_final = convert_to_wav(data)

def chunk_audio(wav_path : str, chunk_minutes : int = 10) -> list:
    audio = AudioSegment.from_wav(wav_path)
    chunk_milliseconds = int(chunk_minutes * 60 * 1000) # convert minutes → milliseconds
    
    chunks = []
    
    for i, start in enumerate(range(0,len(audio),chunk_milliseconds)):
        chunk = audio[start : start + chunk_milliseconds]
        chunk_path =f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_path,format="wav")
        chunks.append(chunk_path)
    return chunks

print(chunk_audio(data_final))
    