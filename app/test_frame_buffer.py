import threading
import time
import unittest
from frame_buffer import FrameBuffer


class FakeBuffer(FrameBuffer):
    def decode(self,token,path,size,duration,fps):
        self.rate_changed(token,24)
        for index in range(96):
            yield bytes([1 if path.name=='first' else 2])*size*size*4


def wait_for(predicate,timeout=2):
    until=time.monotonic()+timeout
    while not predicate():
        if time.monotonic()>=until:raise AssertionError('等待条件超时')
        time.sleep(.005)


class BufferTests(unittest.TestCase):
    def setUp(self):
        self.buffer=FakeBuffer()
    def tearDown(self):
        self.buffer.close()

    def test_capacity_and_timed_consumption(self):
        self.buffer.play('first',4,4,6)
        wait_for(lambda:self.buffer.statistics()['buffered']==6)
        self.assertEqual(self.buffer.statistics()['bytes'],6*4*4*4)
        self.assertEqual(self.buffer.take(0)[0],0)
        wait_for(lambda:self.buffer.statistics()['buffered']==6)
        self.assertEqual(self.buffer.take(3/24)[0],3)
        self.assertLessEqual(self.buffer.statistics()['buffered'],6)

    def test_switch_discards_old_frames(self):
        self.buffer.play('first',4,4,6)
        wait_for(lambda:self.buffer.statistics()['buffered']==6)
        self.buffer.play('second',2,4,12)
        wait_for(lambda:self.buffer.statistics()['buffered']==12)
        self.assertEqual(self.buffer.take(0),(0,0,bytes([2])*16))

    def test_pause_and_resume(self):
        self.buffer.pause(True);self.buffer.play('first',4,4,6)
        self.assertIsNone(self.buffer.take(0))
        self.buffer.pause(False)
        wait_for(lambda:self.buffer.statistics()['buffered']==6)
        self.buffer.pause(True)
        self.buffer.take(10)
        # At most one already-started decode can complete after pausing.
        time.sleep(.03)
        self.assertLessEqual(self.buffer.statistics()['buffered'],1)
        self.buffer.pause(False)
        wait_for(lambda:self.buffer.statistics()['buffered']==6)

    def test_close_unblocks_full_queue(self):
        self.buffer.play('first',4,4,6)
        wait_for(lambda:self.buffer.statistics()['buffered']==6)
        self.buffer.close()
        self.assertFalse(self.buffer.worker.is_alive())
        self.assertEqual(self.buffer.statistics()['buffered'],0)

    def test_eof_reports_actual_count(self):
        self.buffer.play('first',4,4,120)
        wait_for(lambda:self.buffer.statistics()['ended'])
        self.assertEqual(self.buffer.statistics()['count'],96)
        self.assertEqual(self.buffer.take(10)[0],95)

    def test_cancelled_decode_cannot_publish(self):
        entered=threading.Event();release=threading.Event()
        original=self.buffer.decode
        def slow(token,path,size,duration,fps):
            if path.name=='first':entered.set();release.wait(2)
            yield from original(token,path,size,duration,fps)
        self.buffer.decode=slow
        self.buffer.play('first',4,4,6)
        self.assertTrue(entered.wait(2))
        self.buffer.play('second',2,4,6);release.set()
        wait_for(lambda:self.buffer.statistics()['buffered']==6)
        self.assertEqual(self.buffer.take(0)[2],bytes([2])*16)

    def test_whole_preload_waits_for_completion_and_retains_buffer_setting(self):
        entered=threading.Event();release=threading.Event()
        original=self.buffer.decode
        def slow(token,path,size,duration,fps):
            for index,raw in enumerate(original(token,path,size,duration,fps)):
                if index==10:entered.set();release.wait(2)
                yield raw
        self.buffer.decode=slow
        self.buffer.play('first',2,4,6,preload_whole=True)
        try:
            self.assertTrue(entered.wait(2))
            self.assertIsNone(self.buffer.take(0))
            self.assertGreater(self.buffer.statistics()['buffered'],6)
        finally:
            release.set()
        wait_for(lambda:self.buffer.statistics()['ended'])
        stats=self.buffer.statistics()
        self.assertEqual((stats['buffered'],stats['count'],stats['capacity']),(96,96,6))
        self.assertEqual(self.buffer.take(0)[0],0)
        self.buffer.play('second',2,4,6,preload_whole=False)
        wait_for(lambda:self.buffer.statistics()['buffered']==6)
        self.assertFalse(self.buffer.statistics()['preloadWhole'])
        self.assertEqual(self.buffer.take(0)[2],bytes([2])*16)

    def test_cancelled_preload_cannot_publish_into_new_stream(self):
        entered=threading.Event();release=threading.Event()
        original=self.buffer.decode
        def slow(token,path,size,duration,fps):
            if path.name=='first':entered.set();release.wait(2)
            yield from original(token,path,size,duration,fps)
        self.buffer.decode=slow
        self.buffer.play('first',2,4,6,preload_whole=True)
        self.assertTrue(entered.wait(2))
        self.buffer.play('second',2,4,6,preload_whole=False);release.set()
        wait_for(lambda:self.buffer.statistics()['buffered']==6)
        self.assertEqual(self.buffer.take(0)[2],bytes([2])*16)


if __name__=='__main__':unittest.main()
