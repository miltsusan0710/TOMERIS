$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Speech
$taskWave=Join-Path $PSScriptRoot 'v066_speech_test.wav'
$synth=New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
 $voice=$synth.GetInstalledVoices() | Where-Object {$_.VoiceInfo.Culture.Name -eq 'ja-JP'} | Select-Object -First 1
 $synth.SelectVoice($voice.VoiceInfo.Name)
 $synth.SetOutputToWaveFile($taskWave)
 $synth.Speak('こんにちは。今日は良い天気です。')
} finally {$synth.Dispose()}
$info=[System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers() | Where-Object {$_.Culture.Name -eq 'ja-JP'} | Select-Object -First 1
$engine=New-Object System.Speech.Recognition.SpeechRecognitionEngine($info)
try {
 $engine.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))
 $engine.SetInputToWaveFile($taskWave)
 $result=$engine.Recognize()
 if ($null -eq $result) {throw 'No recognition result'}
 $result.Text | Set-Content -Encoding utf8 (Join-Path $PSScriptRoot 'v066_speech_live.txt')
 $result.Text
} finally {$engine.Dispose()}
