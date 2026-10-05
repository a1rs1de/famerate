import json
from faster_whisper import WhisperModel
m=WhisperModel("small",device="cpu",compute_type="int8")
seg,info=m.transcribe("ref/ref_audio.wav",language="ru",word_timestamps=True)
out=[]
for s in seg:
    out.append({"start":s.start,"end":s.end,"text":s.text,"words":[{"w":w.word,"s":w.start,"e":w.end} for w in s.words]})
    print(f"{s.start:.2f}-{s.end:.2f} {s.text}")
json.dump(out,open("ref/transcript.json","w"),ensure_ascii=False,indent=1)
