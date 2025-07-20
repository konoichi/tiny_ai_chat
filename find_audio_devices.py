# find_audio_devices.py
"""
Ein kleines Hilfsskript, um alle verfügbaren Audio-Ausgabegeräte
auf dem System mit ihren Indizes aufzulisten. Dies hilft dabei, den
korrekten 'audio_device_index' für die settings.yaml zu finden.

Benutzung: python find_audio_devices.py
"""
import pyaudio

p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')

print("Verfügbare Audio-Ausgabegeräte:\n")

for i in range(0, numdevices):
    device_info = p.get_device_info_by_host_api_device_index(0, i)
    # Wir listen nur Geräte auf, die auch Töne ausgeben können (maxOutputChannels > 0)
    if (device_info.get('maxOutputChannels')) > 0:
        print(f"Index: {device_info.get('index')}")
        print(f"  Name: {device_info.get('name')}")
        print("-" * 20)

p.terminate()
