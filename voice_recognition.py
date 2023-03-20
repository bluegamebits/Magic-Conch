import pvporcupine
from pvrecorder import PvRecorder
import json

with open('file.json') as f:
        data = json.load(f)
        porcupine_api_key = data['api']

porcupine = pvporcupine.create(access_key=porcupine_api_key, keyword_paths=['./caracola-mágica_es_windows_v2_1_0.ppn'], model_path='./porcupine_params_es.pv')
recoder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)

try:
    recoder.start()

    while True:
        keyword_index = porcupine.process(recoder.read())
        if keyword_index >= 0:
            print(f"Detected keyword")

except KeyboardInterrupt:
    recoder.stop()
finally:
    porcupine.delete()
    recoder.delete()