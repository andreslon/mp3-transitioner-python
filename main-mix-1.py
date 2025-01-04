import os
import subprocess
import numpy as np
from scipy.io import wavfile

def convert_to_wav(mp3_path, wav_path):
    command = f"ffmpeg -i {mp3_path} {wav_path} -y"
    subprocess.run(command, shell=True, check=True)

def get_audio_duration(wav_path):
    result = subprocess.run(
        f"ffprobe -i {wav_path} -show_entries format=duration -v quiet -of csv=\"p=0\"",
        shell=True, capture_output=True, text=True
    )
    return float(result.stdout.strip())

def detect_low_activity_segment(wav_path, segment_duration=2):
    rate, data = wavfile.read(wav_path)
    if len(data.shape) > 1:
        data = np.mean(data, axis=1)
    segment_samples = int(rate * segment_duration)
    min_energy = float('inf')
    start_sample = 0
    for i in range(0, len(data) - segment_samples, segment_samples):
        segment = data[i:i + segment_samples]
        energy = np.sum(np.abs(segment))
        if energy < min_energy:
            min_energy = energy
            start_sample = i
    return start_sample, rate

def create_transition(wav1_path, wav2_path, output_path):
    fade_duration_s = 5

    duration1 = get_audio_duration(wav1_path)
    duration2 = get_audio_duration(wav2_path)

    # Ensure fade duration is within bounds
    fade_out_start = max(0, duration1 - fade_duration_s)
    fade_in_start = 0

    command = (
        f"ffmpeg -i {wav1_path} -i {wav2_path} -filter_complex "
        f"[0:a]afade=t=out:st={fade_out_start}:d={fade_duration_s}[a0];"
        f"[1:a]atrim=start={fade_in_start},afade=t=in:st=0:d={fade_duration_s}[a1];"
        f"[a0][a1]concat=n=2:v=0:a=1[a] "
        f"-map [a] -b:a 320k {output_path} -y"
    )
    subprocess.run(command, shell=True, check=True)

def smooth_transition(audio1_path, audio2_path, output_path):
    wav1_path = "temp1.wav"
    wav2_path = "temp2.wav"

    convert_to_wav(audio1_path, wav1_path)
    convert_to_wav(audio2_path, wav2_path)

    create_transition(wav1_path, wav2_path, output_path)

    # Clean up temporary files
    os.remove(wav1_path)
    os.remove(wav2_path)

    print(f"Transition completed and exported to: {output_path}")

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
