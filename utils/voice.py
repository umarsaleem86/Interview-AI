import io
import os
import base64
import subprocess
import tempfile
from typing import Tuple, Optional
from openai import OpenAI


def get_openai_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY"),
        base_url=os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
    )


def text_to_speech(text: str, voice: str = "nova") -> Tuple[Optional[bytes], str]:
    from config import TTS_VOICE
    voice = TTS_VOICE
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-audio",
            modalities=["text", "audio"],
            audio={"voice": voice, "format": "wav"},
            messages=[
                {"role": "system", "content": "You are an assistant that performs text-to-speech."},
                {"role": "user", "content": f"Repeat the following text verbatim: {text}"},
            ],
        )
        audio_data = getattr(response.choices[0].message, "audio", None)
        if audio_data and hasattr(audio_data, "data"):
            return base64.b64decode(audio_data.data), ""
        return None, "No audio data received"
    except Exception as e:
        return None, f"Text-to-speech failed: {str(e)}"


def convert_to_wav(audio_bytes: bytes) -> bytes:
    if audio_bytes[:4] == b'RIFF':
        return audio_bytes

    with tempfile.NamedTemporaryFile(suffix=".audio", delete=False) as inp:
        inp.write(audio_bytes)
        inp_path = inp.name
    out_path = inp_path + ".wav"
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", inp_path, "-ar", "16000", "-ac", "1", "-f", "wav", out_path],
            capture_output=True, timeout=30
        )
        if result.returncode != 0 or not os.path.exists(out_path):
            return audio_bytes
        with open(out_path, "rb") as f:
            converted = f.read()
        return converted if converted else audio_bytes
    except Exception:
        return audio_bytes
    finally:
        for p in [inp_path, out_path]:
            try:
                os.unlink(p)
            except OSError:
                pass


def speech_to_text(audio_bytes: bytes) -> Tuple[str, str]:
    try:
        wav_bytes = convert_to_wav(audio_bytes)
        client = get_openai_client()
        audio_file = io.BytesIO(wav_bytes)
        audio_file.name = "recording.wav"
        response = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=audio_file,
            response_format="json"
        )
        text = response.text.strip() if response.text else ""
        if not text:
            return "", "Could not transcribe audio. Please try recording again."
        return text, ""
    except Exception as e:
        return "", f"Transcription failed: {str(e)}"
