"""One decoder worker, a bounded look-ahead queue, and no GUI-thread I/O."""
from collections import deque
from pathlib import Path
import threading

from PIL import Image
from video_frames import rgba_frames
from performance_preferences import DEFAULT_BUFFER_FRAMES, DEFAULT_RESOLUTION, DEFAULT_FPS_LIMIT, decode_size, fps_cap


class FrameBuffer:
    def __init__(self):
        self.condition=threading.Condition()
        self.frames=deque()
        self.generation=0;self.request=None;self.closed=False;self.paused=False
        self.capacity=DEFAULT_BUFFER_FRAMES;self.size=decode_size(DEFAULT_RESOLUTION,1);self.duration=0
        self.rate=None;self.count=None;self.error=None;self.ended=False
        self.preload_whole=False
        self.process=None
        self.worker=threading.Thread(target=self.run,name='pet-frame-decoder',daemon=True)
        self.worker.start()

    def play(self,path,size,duration,capacity,fps=fps_cap(DEFAULT_FPS_LIMIT),preload_whole=False):
        with self.condition:
            if self.closed:raise RuntimeError('动画解码器已关闭')
            self.generation+=1
            self.frames.clear();self.rate=None;self.count=None;self.error=None;self.ended=False
            self.size=size;self.duration=duration;self.capacity=capacity
            self.preload_whole=preload_whole
            self.request=(self.generation,Path(path),size,duration,fps)
            if self.process and self.process.poll() is None:self.process.kill()
            self.process=None
            self.condition.notify_all()

    def pause(self,paused):
        with self.condition:
            self.paused=paused;self.condition.notify_all()

    def take(self,elapsed):
        with self.condition:
            if self.error:raise RuntimeError(self.error)
            if self.preload_whole and not self.ended:return None
            result=None
            while self.frames and self.frames[0][1]<=elapsed:
                result=self.frames.popleft()
            if result is not None:self.condition.notify_all()
            return result

    def statistics(self):
        with self.condition:
            return dict(buffered=len(self.frames),bytes=sum(len(frame[2]) for frame in self.frames),
                        capacity=self.capacity,rate=self.rate,count=self.count,ended=self.ended,
                        preloadWhole=self.preload_whole,
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

    def decode(self,token,path,size,duration,fps):
        if path.suffix.lower()=='.webm':
            yield from rgba_frames(path,size,
                process_changed=lambda process:self.process_changed(token,process),
                rate_changed=lambda rate:self.rate_changed(token,rate),fps=fps)
        else:
            # Keep the original WebP asset path supported, without retaining a clip.
            with Image.open(path) as source:
                source_rate=source.n_frames/duration
                output_rate=source_rate if fps is None else min(source_rate,fps)
                self.rate_changed(token,output_rate)
                for index in range(max(1,round(duration*output_rate))):
                    source.seek(min(source.n_frames-1,int(index*source_rate/output_rate)))
                    yield source.convert('RGBA').resize((size,size),Image.Resampling.LANCZOS).tobytes()

    def run(self):
        while True:
            with self.condition:
                self.condition.wait_for(lambda:self.closed or self.request is not None)
                if self.closed:return
                token,path,size,duration,fps=self.request;self.request=None
            frames=self.decode(token,path,size,duration,fps)
            index=0
            try:
                while True:
                    with self.condition:
                        self.condition.wait_for(lambda:self.closed or token!=self.generation or
                                                (not self.paused and (self.preload_whole or len(self.frames)<self.capacity)))
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
