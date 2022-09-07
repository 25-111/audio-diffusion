import warnings

warnings.filterwarnings('ignore')

import librosa
import numpy as np
from PIL import Image


class Mel:

    def __init__(
        self,
        x_res=256,
        y_res=256,
        sample_rate=22050,
        n_fft=2048,
        hop_length=512,
        top_db=80,
    ):
        """Class to convert audio to mel spectrograms and vice versa.

        Args:
            x_res (int): x resolution of spectrogram (time)
            y_res (int): y resolution of spectrogram (frequency bins)
            sample_rate (int): sample rate of audio
            n_fft (int): number of Fast Fourier Transforms
            hop_length (int): hop length (a higher number is recommended for lower than 256 y_res)
            top_db (int): loudest in decibels
        """
        self.x_res = x_res
        self.y_res = y_res
        self.sr = sample_rate
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.n_mels = self.y_res
        self.slice_size = self.x_res * self.hop_length - 1
        self.fmax = self.sr / 2
        self.top_db = top_db
        self.y = None

    def load_audio(self, audio_file):
        """Load audio.

        Args:
            file (str): must be a file on disk due to Librosa limitation
        """
        self.y, _ = librosa.load(audio_file, mono=True)

    def get_number_of_slices(self):
        """Get number of slices in audio.

        Returns:
            int: number of spectograms audio can be sliced into
        """
        return len(self.y) // self.slice_size

    def get_sample_rate(self):
        """Get sample rate:

        Returns:
            int: sample rate of audio
        """
        return self.sr

    def audio_slice_to_image(self, slice):
        """Convert slice of audio to spectrogram.

        Args:
            slice (int): slice number of audio to convert (out of get_number_of_slices())

        Returns:
            PIL Image: grayscale image of x_res x y_res
        """
        S = librosa.feature.melspectrogram(
            y=self.y[self.slice_size * slice:self.slice_size * (slice + 1)],
            sr=self.sr,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            n_mels=self.n_mels,
            fmax=self.fmax,
        )
        log_S = librosa.power_to_db(S, ref=np.max, top_db=self.top_db)
        bytedata = (((log_S + self.top_db) * 255 / self.top_db).clip(0, 255) +
                    0.5).astype(np.uint8)
        image = Image.frombytes("L", log_S.shape, bytedata.tobytes())
        return image

    def image_to_audio(self, image):
        """Converts spectrogram to audio.

        Args:
            image (PIL Image): x_res x y_res grayscale image

        Returns:
            audio (array): raw audio
        """
        bytedata = np.frombuffer(image.tobytes(), dtype="uint8").reshape(
            (image.width, image.height))
        log_S = bytedata.astype("float") * self.top_db / 255 - self.top_db
        S = librosa.db_to_power(log_S)
        audio = librosa.feature.inverse.mel_to_audio(
            S, sr=self.sr, n_fft=self.n_fft, hop_length=self.hop_length)
        return audio