# Copyright (c) 2024 FHNW University of Applied Sciences and Arts Northwestern Switzerland
# See LICENSE

import os
import shutil

from gtts import gTTS
from pydub import AudioSegment


TEXTS = [
  'Tutorial. Wenn du dich mit dem Blindenstock über einer Linie befindest, hörst du folgenden Ton.',
  'Wenn du dich stattdessen in der Nähe eines Code befindest, hörst du folgenden.',
  'Und wenn du dich nicht nur in der Nähe, sondern über einem Code befindest, folgenden.',
  '''
    Halte den Stock still, sobald du diesen Ton hörst, damit der Code gelesen werden kann.
    Anschliessend hörst du einen Audio Track mit Informationen für eine Kreuzung oder ein Werk.
    Du kannst die Audio-Ausgabe stoppen, indem du auf den Button am Audio-Player drückst.
  '''
]


os.chdir('template')
os.mkdir('temp')

for i, text in enumerate(TEXTS, 1):
  gtts = gTTS(text, lang='de')
  gtts.save(f'temp/part-{i}.mp3')

tutorial = AudioSegment.empty()

for i in range(1, 4):
  tutorial += AudioSegment.from_file(f'temp/part-{i}.mp3')
  tutorial += AudioSegment.from_file(f'beeps/beep-{i}.mp3')

tutorial += AudioSegment.from_file(f'temp/part-{4}.mp3')
tutorial.export('tutorial.mp3', format='mp3')

shutil.rmtree('temp', ignore_errors=True)
