def spectromaker(text, filename):
    from gtts import gTTS
    import miniaudio
    import numpy as np
    import io
    import parselmouth
    import matplotlib.pyplot as plt
    import seaborn as sns

    target_sample_rate = 48000
    tts = gTTS(text=text, lang='ru')
    mp3_buffer = io.BytesIO()
    tts.write_to_fp(mp3_buffer)
    mp3_buffer.seek(0)

    decoded = miniaudio.decode(mp3_buffer.read(), nchannels=1, sample_rate=target_sample_rate,
                               output_format=miniaudio.SampleFormat.SIGNED16)
    audio_numpy = np.frombuffer(decoded.samples, dtype=np.int16)
    audio_float = audio_numpy.astype(np.float32) / 32768.0

    sns.set()
    snd = parselmouth.Sound(audio_float, sampling_frequency=target_sample_rate)

    def draw_spectrogram(spectrogram, dynamic_range=70):
        X, Y = spectrogram.x_grid(), spectrogram.y_grid()
        with np.errstate(divide='ignore'):
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

    fig = plt.figure()
    draw_spectrogram(spectrogram)
    plt.twinx()
    draw_intensity(intensity)
    plt.xlim([snd.xmin, snd.xmax])
    plt.savefig(filename, dpi=300)
    plt.close(fig)
