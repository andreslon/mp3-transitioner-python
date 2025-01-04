import os
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

def smooth_transition(audio1_path, audio2_path, output_path, transition_duration_ms=5000):
    audio1 = load_audio(audio1_path)
    audio2 = load_audio(audio2_path)

    audio1_duration = len(audio1)
    audio2_duration = len(audio2)

    fade_out_start = max(0, audio1_duration - transition_duration_ms)
    fade_in_end = min(transition_duration_ms, audio2_duration)

    combined = (
        audio1[:fade_out_start] + 
        crossfade(audio1[fade_out_start:], audio2[:fade_in_end]) + 
        audio2[fade_in_end:]
    )

    save_audio(combined, output_path, {**get_metadata(audio1_path), **get_metadata(audio2_path)})
    print(f"File exported to: {output_path}")

def load_audio(audio_path):
    audio = MP3(audio_path)
    with open(audio_path, "rb") as f:
        return f.read()

def save_audio(audio_data, output_path, metadata):
    with open(output_path, "wb") as f:
        f.write(audio_data)
    audio = MP3(output_path)
    valid_keys = EasyID3.valid_keys.keys()
    for key, value in metadata.items():
        if key in valid_keys:
            try:
                audio[key] = str(value) if not isinstance(value, list) else [str(v) for v in value]
            except Exception as e:
                print(f"Error saving metadata {key}: {e}")
    audio.save()

def crossfade(audio1_data, audio2_data):
    length = min(len(audio1_data), len(audio2_data))
    return bytes(
        int(a1 * (1 - i / length) + a2 * (i / length)) for i, (a1, a2) in enumerate(zip(audio1_data, audio2_data))
    )

def get_metadata(audio_path):
    try:
        audio = EasyID3(audio_path)
        return {k: (v[0] if isinstance(v, list) else v) for k, v in dict(audio).items()}
    except Exception as e:
        print(f"Error loading metadata: {e}")
        return {}

def main():
    audio1_path = "songs/00000111011025_T53_audtrk.mp3"
    audio2_path = "songs/00000411011022_T14_audtrk.mp3"
    output_path = "transitioned_song.mp3"

    if not os.path.exists(audio1_path) or not os.path.exists(audio2_path):
        print("Error: One or both songs do not exist.")
        return

    smooth_transition(audio1_path, audio2_path, output_path)

if __name__ == "__main__":
    main()
