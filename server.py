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


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.get("/flip-coin")
def flip_coin():
    val = random.random()
    head_tail = ""
    if (val <= 0.5):
        head_tail = "heads"
    else:
        head_tail = "tails"
    return ({"value": head_tail})


@app.get("/flip-coins")
def flip_coins(times: int):
    if times and times > 0:
        head_count = 0
        tail_count = 0
        for _ in range(times):
            val = random.random()
            if (val <= 0.5):
                head_count += 1
            else:
                tail_count += 1
        return ({"heads": head_count, "tails": tail_count})
    else:
        return ({"message": "you need to send valid times"})


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
