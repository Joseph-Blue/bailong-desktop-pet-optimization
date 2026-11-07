"""One decoder worker, a bounded look-ahead queue, and no GUI-thread I/O."""
from collections import deque
from pathlib import Path
import threading

from PIL import Image
from video_frames import rgba_frames


class FrameBuffer:
    def __init__(self):
        self.condition=threading.Condition()
        self.frames=deque()
        self.generation=0;self.request=None;self.closed=False;self.paused=False
        self.capacity=24;self.size=512;self.duration=0
        self.rate=None;self.count=None;self.error=None;self.ended=False
        self.process=None
        self.worker=threading.Thread(target=self.run,name='pet-frame-decoder',daemon=True)
        self.worker.start()

    def play(self,path,size,duration,capacity):
        with self.condition:
            if self.closed:raise RuntimeError('动画解码器已关闭')
            self.generation+=1
            self.frames.clear();self.rate=None;self.count=None;self.error=None;self.ended=False
            self.size=size;self.duration=duration;self.capacity=capacity
            self.request=(self.generation,Path(path),size,duration)
            if self.process and self.process.poll() is None:self.process.kill()
            self.process=None
            self.condition.notify_all()

    def pause(self,paused):
        with self.condition:
            self.paused=paused;self.condition.notify_all()

    def take(self,elapsed):
        with self.condition:
            if self.error:raise RuntimeError(self.error)
            result=None
            while self.frames and self.frames[0][1]<=elapsed:
                result=self.frames.popleft()
            if result is not None:self.condition.notify_all()
            return result

    def statistics(self):
        with self.condition:
            return dict(buffered=len(self.frames),bytes=sum(len(frame[2]) for frame in self.frames),
                        capacity=self.capacity,rate=self.rate,count=self.count,ended=self.ended,
                        pid=self.process.pid if self.process and self.process.poll() is None else None)

    def close(self):
        with self.condition:
            self.closed=True;self.generation+=1;self.request=None;self.frames.clear()
            if self.process and self.process.poll() is None:self.process.kill()
            self.condition.notify_all()
        self.worker.join(timeout=3)
        if self.worker.is_alive():raise RuntimeError('动画解码线程未能结束')

    def process_changed(self,token,process):
        with self.condition:
            if token==self.generation and not self.closed:self.process=process
            elif process and process.poll() is None:process.kill()

    def rate_changed(self,token,rate):
        with self.condition:
            if token==self.generation:
                self.rate=rate;self.count=round(self.duration*rate)

    def decode(self,token,path,size,duration):
        if path.suffix.lower()=='.webm':
            yield from rgba_frames(path,size,
                process_changed=lambda process:self.process_changed(token,process),
                rate_changed=lambda rate:self.rate_changed(token,rate))
        else:
            # Keep the original WebP asset path supported, without retaining a clip.
            with Image.open(path) as source:
                self.rate_changed(token,source.n_frames/duration)
                for index in range(source.n_frames):
                    source.seek(index)
                    yield source.convert('RGBA').resize((size,size),Image.Resampling.LANCZOS).tobytes()

    def run(self):
        while True:
            with self.condition:
                self.condition.wait_for(lambda:self.closed or self.request is not None)
                if self.closed:return
                token,path,size,duration=self.request;self.request=None
            frames=self.decode(token,path,size,duration)
            index=0
            try:
                while True:
                    with self.condition:
                        self.condition.wait_for(lambda:self.closed or token!=self.generation or
                                                (not self.paused and len(self.frames)<self.capacity))
                        if self.closed or token!=self.generation:break
                    raw=next(frames,None)
                    with self.condition:
                        if token!=self.generation or self.closed:break
                        if raw is None:
                            if not index:raise RuntimeError('动画没有可播放帧：'+str(path))
                            self.count=index;self.ended=True;break
                        self.frames.append((index,index/self.rate,raw));index+=1
            except (OSError,ValueError,RuntimeError) as error:
                with self.condition:
                    if token==self.generation and not self.closed:self.error=str(error)
            finally:
                frames.close()
