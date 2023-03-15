from cgitb import text
from google.cloud import texttospeech
from pathlib import Path

def talk(text):
    
    # Instantiates a client
    client = texttospeech.TextToSpeechClient.from_service_account_json(
        'F:\\Projects\\Python\\googlevoice\\service_account.json')

    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Build the voice request
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Neural2-E",
        #ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Perform the text-to-speech requested with the selected parameters
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # The response's audio_content is binary
    with open("output.mp3", "wb") as out:
        out.write(response.audio_content)
        print('Audio content written to file "Output.mp3')
