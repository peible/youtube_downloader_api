from typing import List
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
import youtube_dl, os

from pydantic import BaseModel

app = FastAPI()

ROOT_DIR=os.path.dirname(os.path.realpath(__file__))
#ROOT_DIR=os.path.dirname(__file__)
TMP_DIR=os.path.join(ROOT_DIR, 'tmp_download')

class MyLogger(object):
    def debug(self, msg):
        print(msg)

    def warning(self, msg):
        print(msg)

    def error(self, msg):
        print(msg)

def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')


ydl_opts = {
    'format': 'mp4',#'bestvideo/best',
    'outtmpl': f"{TMP_DIR}{os.path.sep}%(title)s.%(ext)s",
    # 'postprocessors': [{
    #     'key': 'FFmpegExtractAudio',
    #     'preferredcodec': 'mp3',
    #     'preferredquality': '192',
    # }],
    'logger': MyLogger(),
    'progress_hooks': [my_hook],
    'verbose': True
}

class Video(BaseModel):
    url: List[str]
    filter_info: List[str] = None
    quality: str = None

@app.get("/")
def index():
    return {"Lorem": "Ipsum"}


@app.post("/download")
def download(video : Video):
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        video_title = ydl.extract_info(video.url[0], download=True)['title']
        return FileResponse(path=f"{TMP_DIR}{os.path.sep}{video_title}.mp4", filename=f"{video_title}.mp4", media_type='video/mp4')

@app.post("/search")
def search(video : Video, request : Request):
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        video_info = ydl.extract_info(video.url, download=False)
        extracted_info={}
        for key_info in video.filter_info:
            if type(video_info.get(key_info)) is str:
                extracted_info[key_info] = video_info[key_info]
            else:
                extracted_info[key_info] = video_info[key_info][-1]

        # for key_info in request.query_params.values():
        #     if type(video_info.get(key_info)) is str:
        #         extracted_info[key_info] = video_info[key_info]
        #     else: 
        #         # if type(video_info.get(key_info)) is list:
        #         extracted_info[key_info] = video_info[key_info][-1]
                
    return extracted_info if extracted_info else video_info