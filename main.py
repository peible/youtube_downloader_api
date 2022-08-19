from queue import Empty
from typing import List
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
import youtube_dl, os, shutil, time
from zipfile import ZipFile

from pydantic import BaseModel

app = FastAPI()

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
# ROOT_DIR=os.path.dirname(__file__)
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
    "outtmpl": f"{TMP_DIR}{os.path.sep}%(title)s.%(ext)s",
    "logger": MyLogger(),
    "progress_hooks": [my_hook],
    "verbose": True,
}

class Video(BaseModel):
    url: List[str]
    filter_info: List[str] = None
    format: str = None

@app.get("/")
def index():
    return {"Lorem": "Ipsum"}

@app.post("/download")
def download(video: Video):
    media_type = None
    if video.format == "mp3":
        ydl_opts["format"] = "best"
        ydl_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "256",
            }
        ]
        media_type = "audio/mpeg"
    elif video.format == "mp4":
        ydl_opts["format"] = "bestvideo/best"
        media_type = "video/mp4"
        
    # if len(video.url) > 1:
    #     folder_name = int(round(time.time() * 1000))
    #     os.mkdir(folder_name)
    #     TMP_DIR = os.path.join(TMP_DIR, folder_name)
    #     ydl_opts["outtmpl"]= f"{TMP_DIR}{os.path.sep}%(title)s.%(ext)s"
    #     after looping file-->shutil.make_archive(folder_name, 'zip', TMP_DIR)

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        folder_name = int(round(time.time() * 1000))
        with ZipFile(f"{TMP_DIR}{os.path.sep}{folder_name}.zip", "w") as zip:
            for url in video.url:
                video_title = ydl.extract_info(url, download=True)["title"]
                zip.write(f"{TMP_DIR}{os.path.sep}{video_title}.{video.format}", f"{video_title}.{video.format}")
        return FileResponse(
            path=f"{TMP_DIR}{os.path.sep}{folder_name}.zip",
            filename=f"{folder_name}.zip",
            media_type=media_type,
        )

@app.post("/search")
def search(video: Video, request: Request):
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        extracted_info = {}
        for idx, url in enumerate(video.url):
            video_info = ydl.extract_info(url, download=False)
            if video.filter_info:
                for key_info in video.filter_info:
                    if video_info.get(key_info):
                        if type(video_info.get(key_info)) is str:
                            extracted_info[idx][key_info] = video_info[key_info]
                        else:
                            extracted_info[idx][key_info] = video_info[key_info][-1]
            else:
                extracted_info[idx] = video_info

    return extracted_info