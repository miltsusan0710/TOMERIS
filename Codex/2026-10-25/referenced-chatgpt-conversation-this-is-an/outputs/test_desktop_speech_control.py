import json,subprocess,sys,threading,time,unittest
from unittest.mock import Mock,patch
from tomeris_speech_control import speech,SpeechCancelled,finish_audio

class SpeechControlTests(unittest.TestCase):
 def test_pre_cancel_no_process(self):
  event=threading.Event();event.set()
  with patch('tomeris_speech_control.subprocess.Popen') as popen:
   with self.assertRaises(SpeechCancelled):speech('listen',cancel=event)
   popen.assert_not_called()
 def test_cancel_reaps_own_child(self):
  original=subprocess.Popen;children=[];event=threading.Event()
  def start(*args,**kwargs):
   child=original([sys.executable,'-c','import sys,time;sys.stdin.read();time.sleep(30)'],**kwargs);children.append(child);return child
  timer=threading.Timer(.3,event.set);timer.start()
  try:
   with patch('tomeris_speech_control.subprocess.Popen',side_effect=start):
    with self.assertRaises(SpeechCancelled):speech('listen',cancel=event)
   self.assertIsNotNone(children[0].poll())
  finally:
   timer.cancel()
   for child in children:
    if child.poll() is None:child.kill();child.communicate()
 def test_success_data_and_no_shell_interpolation(self):
  process=Mock();process.communicate.return_value=(json.dumps({'text':'こんにちは'}),'');process.returncode=0;process.poll.return_value=0
  with patch('tomeris_speech_control.subprocess.Popen',return_value=process) as start:
   self.assertEqual(speech('speak','$(example)')['text'],'こんにちは')
   self.assertNotIn('$(example)',str(start.call_args.args))
   self.assertIn('$(example)',process.communicate.call_args_list[0].kwargs['input'])
  process.kill.assert_not_called()
 def test_timeout_reaps_child(self):
  process=Mock();process.poll.return_value=None
  with patch('tomeris_speech_control.subprocess.Popen',return_value=process),patch('tomeris_speech_control.time.monotonic',side_effect=[0,21]):
   with self.assertRaisesRegex(ValueError,'時間制限'):speech('listen')
  process.kill.assert_called_once();process.communicate.assert_called_once()
 def test_queued_result_ignored_after_cancel(self):
  app=Mock();app.closing=False;cancel=threading.Event();cancel.set();done=Mock()
  finish_audio(app,cancel,done,('ok',{'text':'追加しない'}))
  done.assert_not_called();self.assertFalse(app.audio_active);app.append.assert_called_once()
 def test_close_no_delivery_and_error_clears_state(self):
  app=Mock();app.closing=True;done=Mock()
  finish_audio(app,threading.Event(),done,('ok',{'text':'追加しない'}));done.assert_not_called();app.append.assert_not_called()
  app.closing=False;finish_audio(app,threading.Event(),done,('error','失敗'));self.assertFalse(app.audio_active);app.append.assert_called_once_with('お知らせ','失敗')
