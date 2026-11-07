import os
os.environ['QT_QPA_PLATFORM']='offscreen'
import unittest, time
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtTest import QTest
from pet import Pet,clamp_position
from quota import quota_windows

app=QApplication.instance() or QApplication([])
class Tests(unittest.TestCase):
    def setUp(self):self.pet=Pet();self.pet.show();self.ready()
    def ready(self):
        deadline=time.monotonic()+5
        while self.pet.loading:
            self.assertLess(time.monotonic(),deadline)
            self.pet.animate();QTest.qWait(5)
    def tearDown(self):
        self.pet.tick.stop();self.pet.bubble.close();self.pet.hide()
        self.pet.stream.close();self.pet.frames=[];self.pet.transition=None
        self.pet.deleteLater();app.processEvents()
    def test_all_assets_and_idle_weights(self):
        self.assertEqual(len(self.pet.variants),15)
        for item in self.pet.idles+self.pet.variants:
            self.pet.play(item,'variant');self.ready()
            self.assertEqual(self.pet.frames[0].width(),self.pet.frame_size)
            self.assertLessEqual(self.pet.stream.statistics()['buffered'],self.pet.buffer_capacity)
        with patch('pet.random.choices',return_value=[self.pet.idles[1]]) as choice:
            self.pet.idle();self.assertEqual(choice.call_args.kwargs['weights'],[4,1])
    def test_click_disambiguation(self):
        with patch.object(self.pet,'single_click') as single,patch.object(self.pet,'quota') as quota:
            # Timer slot was connected earlier; inspect resulting state instead below.
            QTest.mouseClick(self.pet,Qt.MouseButton.LeftButton,pos=QPoint(160,160))
            QTest.qWait(80);QTest.mouseClick(self.pet,Qt.MouseButton.LeftButton,pos=QPoint(160,160))
            quota.assert_called_once();self.pet.click_timer.stop()
        self.pet.last_click=None
        QTest.mouseClick(self.pet,Qt.MouseButton.LeftButton,pos=QPoint(160,160));QTest.qWait(300)
        self.assertEqual(self.pet.mode,'variant');self.assertTrue(self.pet.bubble.isVisible())
        self.assertLessEqual(self.pet.bubble_timer.remainingTime(),4000)
    def test_variant_return_and_quota_stale(self):
        self.pet.choose(self.pet.variants[0]);self.ready();self.pet.started=time.monotonic()-4.01;self.pet.animate()
        self.assertEqual(self.pet.mode,'idle')
        self.pet.quota_generation=1;self.pet.generation=2
        self.pet.quota_failed('obsolete');self.assertNotIn('obsolete',self.pet.bubble.findChildren(__import__('PySide6.QtWidgets',fromlist=['QLabel']).QLabel)[0].text())
    def test_quota_parsing(self):
        data={'rateLimitsByLimitId':{'codex':{'primary':{'usedPercent':23,'windowDurationMins':300},'secondary':{'usedPercent':10,'windowDurationMins':10080}}}}
        windows=quota_windows(data);self.assertEqual([w['remaining'] for w in windows],[77,90]);self.assertEqual(windows[1]['name'],'一周')
        with self.assertRaises(RuntimeError):quota_windows({})
    def test_loading_then_progress_and_resume(self):
        with patch('pet.QuotaWorker') as worker:
            self.pet.quota()
            self.ready()
            self.assertEqual(self.pet.mode,'quota')
            self.assertEqual(self.pet.current['id'],self.pet.manifest.get('quotaAnimation',self.pet.idles[0])['id'])
            from PySide6.QtWidgets import QLabel,QProgressBar
            self.assertEqual(self.pet.bubble.findChildren(QLabel)[0].text(),'让我看看额度还有多少。。。。。。')
            self.pet.quota_ready([{'name':'5小时','remaining':76,'resetsAt':None},{'name':'一周','remaining':91,'resetsAt':None}])
            self.assertEqual([b.value() for b in self.pet.bubble.findChildren(QProgressBar)],[76,91])
            self.pet.started=time.monotonic()-4.1;self.pet.animate()
            self.assertEqual(self.pet.mode,'idle');self.assertTrue(self.pet.bubble.isVisible())
            self.pet.dismiss_bubble();self.assertEqual(self.pet.mode,'idle')
            self.pet.worker=None
    def test_menu_contains_all_variants_and_exit(self):
        actions=[]
        def inspect():
            menu=app.activePopupWidget()
            actions.extend(a.text() for a in menu.actions() if not a.isSeparator());menu.close()
        QTimer.singleShot(100,inspect)
        QTest.mouseClick(self.pet,Qt.MouseButton.RightButton,pos=QPoint(160,160))
        self.assertEqual(actions,['隐藏桌宠','全屏时自动隐藏','打开对话模式','查看历史对话','对话框大小…','互动差分动画','工作差分动画','待机差分动画','移动差分','禁用自移动','桌宠大小…','禁用音效','性能设置…','性能统计…','关于…','退出桌宠'])
        self.assertEqual(actions[-1],'退出桌宠')
    def test_drag_landing_and_click_suppression(self):
        from types import SimpleNamespace
        from PySide6.QtCore import QPointF
        press=SimpleNamespace(button=lambda:Qt.MouseButton.LeftButton,globalPosition=lambda:QPointF(200,200))
        move=SimpleNamespace(buttons=lambda:Qt.MouseButton.LeftButton,globalPosition=lambda:QPointF(240,230))
        self.pet.mousePressEvent(press);self.pet.mouseMoveEvent(move)
        self.assertEqual(self.pet.mode,'drag');self.assertEqual(self.pet.current['id'],'drag')
        self.ready()
        self.pet.started=time.monotonic()-4.1;self.pet.animate();self.assertEqual(self.pet.mode,'drag')
        self.pet.mouseReleaseEvent(press)
        self.assertEqual(self.pet.mode,'landing');self.ready();self.assertEqual(self.pet.stream.statistics()['count'],48)
        self.assertEqual(self.pet.current['durationMs'],2000);self.assertFalse(self.pet.click_timer.isActive())
        self.pet.started=time.monotonic()-2.1;self.pet.animate();self.assertEqual(self.pet.mode,'idle')
    def test_reference_frame_survives_action_switches(self):
        reference=self.pet.reference_frame.cacheKey()
        for item in self.pet.variants[:3]:self.pet.play(item,'variant');self.ready()
        self.assertEqual(self.pet.reference_frame.cacheKey(),reference)
        self.assertEqual(len(self.pet.frames),1)
    def test_variant_buffer_bounded_and_idle_return(self):
        for item in self.pet.variants:
            self.pet.choose(item)
            self.ready()
            self.assertLessEqual(self.pet.stream.statistics()['buffered'],self.pet.buffer_capacity)
            self.pet.started=time.monotonic()-item['durationMs']/1000-.1
            self.pet.animate()
            self.assertIn(self.pet.mode,('idle','return-idle'))
    def test_quota_zero_percent_is_readable_outside_bar(self):
        from PySide6.QtWidgets import QLabel,QProgressBar
        self.pet.bubble.quota([{'name':'5小时','remaining':0,'resetsAt':None}])
        self.assertTrue(any('剩余 0%' in label.text() for label in self.pet.bubble.findChildren(QLabel)))
        self.assertFalse(self.pet.bubble.findChildren(QProgressBar)[0].isTextVisible())

class BoundaryTests(unittest.TestCase):
    def test_edges_and_corners(self):
        from PySide6.QtCore import QRect,QSize
        area=QRect(0,0,1920,1040);size=QSize(256,256)
        for point in [QPoint(-500,-500),QPoint(3000,-500),QPoint(-500,3000),QPoint(3000,3000),QPoint(800,300)]:
            bounded=clamp_position(point,size,area)
            self.assertTrue(area.contains(QRect(bounded,size)))
        self.assertEqual(clamp_position(QPoint(3000,3000),size,area),QPoint(1664,784))
    def test_negative_monitor_coordinates(self):
        from PySide6.QtCore import QRect,QSize
        area=QRect(-1920,-200,1920,1040);size=QSize(256,256)
        self.assertEqual(clamp_position(QPoint(-4000,-1000),size,area),QPoint(-1920,-200))
        self.assertTrue(area.contains(QRect(clamp_position(QPoint(20,1000),size,area),size)))

if __name__=='__main__':unittest.main()
