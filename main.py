from typing import List
from fastapi import FastAPI
from fastapi.responses import FileResponse
import os, uuid, yt_dlp
from zipfile import ZipFile
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
TMP_DIR = os.path.join(ROOT_DIR, "tmp_download")

class MyLogger(object):
    def debug(self, msg):
        print(msg)

    def warning(self, msg):
        print(msg)

    def error(self, msg):
        print(msg)

def my_hook(d):
    if d["status"] == "finished":
        print("Done downloading, now converting ...")

ydl_opts = {
    "outtmpl": f"{os.path.join(TMP_DIR, '')}%(title)s.%(ext)s",
    "logger": MyLogger(),
    "progress_hooks": [my_hook],
    "verbose": True
}

class Video_download(BaseModel):
    url: List[str]
    quality: str = None
    format: str


class Video_search(BaseModel):
    url: List[str]
    filter_info: List[str] = None

@app.get("/")
def index():
    return {"Welcome": "Visit /docs"}

@app.post("/download")
def download(video: Video_download):
    filename=None
    media_type = None
    if video.format == "mp3":
        ydl_opts["format"] = "bestaudio"
        ydl_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "256",
            }
        ]
        media_type = "audio/mpeg"
    elif video.format == "mp4":
        ydl_opts["format"] = "best"
        media_type = "video/mp4"
        
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        if len(video.url) > 1:
            media_type = "application/zip"
            filename = f"{uuid.uuid4()}.zip"
            
            with ZipFile(os.path.join(TMP_DIR, filename), "w") as zip:
                for url in video.url:
                    video_title = ydl.extract_info(url, download=True)["title"]
                    zip.write(os.path.join(TMP_DIR, f"{video_title}.{video.format}"), f"{video_title}.{video.format}")
                    os.remove(os.path.join(TMP_DIR, f"{video_title}.{video.format}"))
        else:
            video_title = ydl.extract_info(video.url[0], download=True)["title"]
            filename = f"{video_title}.{video.format}"

    return FileResponse(
        path=os.path.join(TMP_DIR, filename),
        filename=filename,
        media_type=media_type
    )

@app.post("/search")
def search(video: Video_search):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        extracted_info = {}
        for idx, url in enumerate(video.url):
            video_info = ydl.extract_info(url, download=False)
            print(type(video_info))
            if video.filter_info:
                extracted_info[idx] = {}
                for key_info in video.filter_info:
                    if video_info.get(key_info):
                        if type(video_info.get(key_info)) is str:
                            extracted_info[idx][key_info] = video_info[key_info]
                        else:
                            extracted_info[idx][key_info] = video_info[key_info][-1]
            else:
                extracted_info[idx] = video_info

    return extracted_info