import os
import subprocess
import numpy as np
from scipy.io import wavfile

def convert_to_wav(mp3_path, wav_path):
    command = f"ffmpeg -i {mp3_path} {wav_path} -y"
    subprocess.run(command, shell=True, check=True)

def get_audio_energy(wav_path, segment_duration=0.1):
    rate, data = wavfile.read(wav_path)
    if len(data.shape) > 1:
        data = np.mean(data, axis=1)
    segment_samples = int(rate * segment_duration)
    energies = [
        np.sum(np.abs(data[i:i + segment_samples]))
        for i in range(0, len(data) - segment_samples, segment_samples)
    ]
    return np.array(energies), rate

def find_best_transition_point(wav1_path, wav2_path):
    energy1, rate1 = get_audio_energy(wav1_path)
    energy2, rate2 = get_audio_energy(wav2_path)

    # Normalize energies
    energy1 = energy1 / np.max(energy1)
    energy2 = energy2 / np.max(energy2)

    # Find peaks in energies
    peaks1 = np.where(energy1 > 0.7)[0]
    peaks2 = np.where(energy2 > 0.7)[0]

    if len(peaks1) == 0 or len(peaks2) == 0:
        return 0, 0  # Fallback to start of the songs

    # Use the last peak of song 1 and the first peak of song 2
    best_point1 = peaks1[-1] * (1 / 10)  # Convert index to time
    best_point2 = peaks2[0] * (1 / 10)  # Convert index to time

    return best_point1, best_point2

def extract_transition_sound(wav1_path, wav2_path, duration):
    rate1, data1 = wavfile.read(wav1_path)
    rate2, data2 = wavfile.read(wav2_path)

    if len(data1.shape) > 1:
        data1 = np.mean(data1, axis=1)
    if len(data2.shape) > 1:
        data2 = np.mean(data2, axis=1)

    transition1 = data1[-int(rate1 * duration):]
    transition2 = data2[:int(rate2 * duration)]

    combined_transition = (transition1 + transition2) / 2
    combined_transition = combined_transition.astype(np.int16)

    transition_wav = "transition_sound.wav"
    wavfile.write(transition_wav, rate1, combined_transition)
    return transition_wav

def create_transition(wav1_path, wav2_path, output_path):
    fade_duration_s = 5

    best_point1, best_point2 = find_best_transition_point(wav1_path, wav2_path)

    # Extract natural transition sound
    transition_wav = extract_transition_sound(wav1_path, wav2_path, fade_duration_s)

    command = (
        f"ffmpeg -i {wav1_path} -i {transition_wav} -i {wav2_path} -filter_complex "
        f"[0:a]atrim=start=0:end={best_point1 + fade_duration_s},afade=t=out:st={best_point1}:d={fade_duration_s}[a0];"
        f"[1:a]afade=t=in:st=0:d={fade_duration_s}[a1];"
        f"[2:a]atrim=start={best_point2},afade=t=in:st=0:d={fade_duration_s}[a2];"
        f"[a0][a1][a2]concat=n=3:v=0:a=1[a] "
        f"-map [a] -b:a 320k {output_path} -y"
    )
    subprocess.run(command, shell=True, check=True)

    os.remove(transition_wav)

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
    audio1_path = "songs/1_audtrk.mp3"
    audio2_path = "songs/3_audtrk.mp3"
    output_path = "transitioned_song.mp3"

    if not os.path.exists(audio1_path) or not os.path.exists(audio2_path):
        print("Error: One or both songs do not exist.")
        return

    smooth_transition(audio1_path, audio2_path, output_path)

if __name__ == "__main__":
    main()
