import os
os.environ['QT_QPA_PLATFORM']='offscreen'
import tempfile
import unittest
import time
from unittest.mock import patch
from PySide6.QtWidgets import QApplication,QTextBrowser,QPushButton
from chat_backend import CodexSession
from chat_ui import ChatController
from pet import Pet

app=QApplication.instance() or QApplication([])

class SummaryTests(unittest.TestCase):
    def test_public_sections_only_and_final_deduplication(self):
        events=[];s=CodexSession('.',emit=lambda k,v:events.append((k,v)))
        for index,text in [(0,'核对需求'),(1,'检查文件')]:
            s.event({'method':'item/reasoning/summaryTextDelta','params':{'itemId':'r','summaryIndex':index,'delta':text}})
        s.event({'method':'item/completed','params':{'item':{'id':'r','type':'reasoning','summary':['核对需求','检查文件'],'content':['PRIVATE-MUST-NOT-SHOW']}}})
        self.assertEqual(events[-1],('summary_update','核对需求\n\n检查文件'))
        self.assertNotIn('PRIVATE-MUST-NOT-SHOW',str(events))

class UiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.pet=Pet();cls.pet.show()
        cls.c=ChatController(cls.pet,cls.temp.name);cls.pet.chat=cls.c
    @classmethod
    def tearDownClass(cls):
        cls.c.shutdown();cls.pet.close();cls.temp.cleanup()
    def test_summary_and_one_success_notification(self):
        c=self.c;p=self.pet
        c.active=c.store.new(self.temp.name);c.running_chat=c.active
        c.running_turn={'prompt':'测试','created':'now','status':'running','output':'','events':[]}
        c.active['turns'].append(c.running_turn)
        p.play(p.work_slots[1],'working')
        c.receive('summary_update','正在核对主人的需求。');c.preview_reply();c.render()
        self.assertIn('思考摘要（公开）',c.window.view.toPlainText())
        self.assertTrue(p.bubble.isVisible())
        self.assertTrue(p.bubble.is_task_progress)
        long='完整任务结果\n'*100
        result={'threadId':'test','text':long,'transcript':long}
        with patch.object(p,'play_click_sound') as sound:
            c.completed(result);c.completed(result)
            sound.assert_called_once()
        self.assertEqual(p.mode,'task-celebration');self.assertEqual(p.current['id'],'18')
        view=p.bubble.findChild(QTextBrowser);self.assertEqual(view.toPlainText(),long)
        app.processEvents();self.assertGreater(view.verticalScrollBar().maximum(),0)
        button=next(b for b in p.bubble.findChildren(QPushButton) if b.text()=='详情')
        button.click();self.assertTrue(c.window.isVisible())
        # Advance after the first decoded frame; notification tests do not wait for FFmpeg.
        p.loading=False;p.started=time.monotonic()-p.current['durationMs']/1000-1
        with patch.object(p.stream,'take',return_value=None):p.animate()
        self.assertEqual(p.mode,'idle')
    def test_failure_has_no_success_sound_or_animation(self):
        c=self.c;p=self.pet
        c.active=c.store.new(self.temp.name);c.running_chat=c.active
        c.running_turn={'prompt':'失败测试','created':'now','status':'running','output':'','events':[]}
        c.active['turns'].append(c.running_turn)
        with patch.object(p,'task_completed') as success,patch.object(p,'play_click_sound') as sound:
            c.failed('未完成',False);success.assert_not_called();sound.assert_not_called()

    def test_tool_activity_is_visible_but_never_saved_as_history(self):
        c=self.c;p=self.pet
        c.active=c.store.new(self.temp.name);c.running_chat=c.active
        c.running_turn={'prompt':'工具测试','created':'now','status':'running','output':'','events':[]}
        c.active['turns'].append(c.running_turn)
        c.receive('activity','命令执行失败（返回码 1）\nrg app');c.preview_reply();c.render();c.flush()
        self.assertIn('命令执行失败',c.window.view.toPlainText())
        self.assertNotIn('rg app',c.store.path.read_text(encoding='utf-8'))
        self.assertEqual(c.running_turn['status'],'running')
        c.receive('activity','正在调用工具\nfunctions.exec');c.preview_reply();c.render()
        self.assertIn('functions.exec',c.window.view.toPlainText())
        self.assertNotIn('rg app',c.window.view.toPlainText())
        with patch.object(p,'task_completed'):
            c.completed({'threadId':'test','text':'已修复','transcript':'已修复'})
        self.assertNotIn('functions.exec',c.store.path.read_text(encoding='utf-8'))
        self.assertNotIn('工具进度',c.window.view.toPlainText())

if __name__=='__main__':unittest.main()
