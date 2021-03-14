from google.cloud import texttospeech
from ucm.models import Noted, Notem, Topic
import os, django, glob, sys, shelve
#import ucm.models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "base.settings")

def list_languages():
    client = texttospeech.TextToSpeechClient()
    voices = client.list_voices().voices
    languages = unique_languages_from_voices(voices)

    print(f" Languages: {len(languages)} ".center(60, "-"))
    for i, language in enumerate(sorted(languages)):
        print(f"{language:>10}", end="" if i % 5 < 4 else "\n")


def unique_languages_from_voices(voices):
    language_set = set()
    for voice in voices:
        for language_code in voice.language_codes:
            language_set.add(language_code)
    return language_set


def list_voices(language_code=None):
    client = texttospeech.TextToSpeechClient()
    response = client.list_voices(language_code=language_code)
    voices = sorted(response.voices, key=lambda voice: voice.name)

    print(f" Voices: {len(voices)} ".center(60, "-"))
    for voice in voices:
        languages = ", ".join(voice.language_codes)
        name = voice.name
        gender = texttospeech.SsmlVoiceGender(voice.ssml_gender).name
        rate = voice.natural_sample_rate_hertz
        print(f"{languages:<8} | {name:<24} | {gender:<8} | {rate:,} Hz")

def text_to_wav(voice_name, filename, text):
    language_code = "-".join(voice_name.split("-")[:2])
    text_input = texttospeech.SynthesisInput(text=text)
    voice_params = texttospeech.VoiceSelectionParams(
        language_code=language_code, name=voice_name
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    client = texttospeech.TextToSpeechClient()
    response = client.synthesize_speech(
        input=text_input, voice=voice_params, audio_config=audio_config
    )

#    filename = f"{language_code}.wav"
    with open(filename, "wb") as out:
        out.write(response.audio_content)
        print(f'Audio content written to "{filename}"')

#list_languages()
#list_voices()


#nn = Noted.objects.filter (ntype='title')
nn = Noted.objects.filter (ntype='example')

for n in nn:
#    text_to_wav("en-GB-Wavenet-B", str (n.id) + '_' + n.ndata + ".wav", n.ndata)
    text_to_wav("en-GB-Wavenet-B", str (n.id) + "_example.wav", n.ndata)
    print (n.ndata)
