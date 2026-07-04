import speech_recognition as sr

r = sr.Recognizer()

with sr.AudioFile("temp.wav") as source:
    audio = r.record(source)

text = r.recognize_google(audio)

print("Detected speech:")
print(text)