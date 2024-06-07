import uvicorn
import random
import uuid
import os
import asyncio

from fastapi import FastAPI, BackgroundTasks
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from pytube import YouTube

app = FastAPI()


class PlayRequest(BaseModel):
    url: str


SAVE_PATH = "downloads"
STREAM_URL = "rtmp://localhost:1935/live/mystream"


async def download_and_stream_video(video_url: str):
    try:
        yt = YouTube(video_url)
    except:
        raise HTTPException(status_code=500, detail="Unable to fetch video")
    stream = yt.streams.get_by_itag(22)
    filename = ""
    while True:
        filename = f"{str(uuid.uuid4())}.mp4"
        if not os.path.exists(f"{SAVE_PATH}/{filename}"):
            break
    try:
        # Downloading the video
        await asyncio.to_thread(stream.download, SAVE_PATH, filename=filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Unable to download video")

    command = ["ffmpeg", "-re", "-i", f"./downloads/{filename}",
               "-c:v", "libx264", "-preset", "veryfast", "-tune",
               "zerolatency", "-c:a", "aac", "-ar", "44100", "-f", "flv",
               STREAM_URL]
    process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await process.wait()


@app.post("/play")
async def play(play_request: PlayRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(
        asyncio.run, download_and_stream_video(play_request.url))

    return ({"message": "streaming video soon: rtmp://localhost:1935/live/mystream", })


if __name__ == "__main__":
    uvicorn.run("server:app", port=5000, reload=True)
