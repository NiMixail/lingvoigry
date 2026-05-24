import torch
import scipy.io.wavfile as wavfile
import numpy as np
import os

text = "шесть"
output_filename = "test_audio.wav"

model, _ = torch.hub.load(
    repo_or_dir='snakers4/silero-models',
    model='silero_tts',
    language='ru',
    speaker='ru_v3'
)

audio = model.apply_tts(text=text, speaker='baya', sample_rate=48000)

audio_numpy = (audio.numpy() * 32767).astype(np.int16)
wavfile.write(output_filename, 48000, audio_numpy)

import parselmouth

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set()  # Use seaborn's default style to make attractive graphs

# Plot nice figures using Python's "standard" matplotlib library
snd = parselmouth.Sound("test_audio.wav")


# plt.figure()
# plt.plot(snd.xs(), snd.values.T)
# plt.xlim([snd.xmin, snd.xmax])
# plt.xlabel("time [s]")
# plt.ylabel("amplitude")
# plt.show() # or plt.savefig("sound.png"), or plt.savefig("sound.pdf")
def draw_spectrogram(spectrogram, dynamic_range=70):
    X, Y = spectrogram.x_grid(), spectrogram.y_grid()
    sg_db = 10 * np.log10(spectrogram.values)
    plt.pcolormesh(X, Y, sg_db, vmin=sg_db.max() - dynamic_range, cmap='Greys')
    plt.ylim([spectrogram.ymin, spectrogram.ymax])
    plt.xlabel("time [s]")
    plt.ylabel("frequency [Hz]")


def draw_intensity(intensity):
    plt.plot(intensity.xs(), intensity.values.T, linewidth=3, color='w')
    plt.plot(intensity.xs(), intensity.values.T, linewidth=1, color='Red')
    plt.grid(False)
    plt.ylim(0)
    plt.ylabel("intensity [dB]")


intensity = snd.to_intensity()
spectrogram = snd.to_spectrogram()
plt.figure()
draw_spectrogram(spectrogram)
plt.twinx()
draw_intensity(intensity)
plt.xlim([snd.xmin, snd.xmax])
plt.show()  # or plt.savefig("spectrogram.pdf")