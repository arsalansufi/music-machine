"""
A module for the AudioManipulator class.
"""

# project modules
from music_machine import audio_info_extractor
# installed modules
from echonest.remix import audio
# default modules
import os
import yaml


class AudioManipulator(object):
    """
    A class to manipulate audio files. Has an instance of the AudioInfoExtractor class as one of
    its attributes.
    """

    def __init__(self, config_filename):

        config_file = open(config_filename, 'r')
        config = yaml.load(config_file)
        config_file.close()

        self.audio_files_dir = \
            os.environ['MUSIC_MACHINE_DIR'] + '/' + config['audio_files_dir']

        self.extractor = audio_info_extractor.AudioInfoExtractor(config_filename)


    def reverse_audio(self, input_filename, output_filename):
        """
        description:
        A method that quasi-reverses an audio file by splitting it at each beat and playing the
        pieces in reverse.

        inputs:
        -- str input_filename -- The name of the input audio file.
        -- str output_filename -- The name of the audio file to be outputted.

        return info:
        -- return type -- void
        """
        audio_file = self.extractor.get_audio_file(input_filename)
        beats = audio_file.analysis.beats
        beats.reverse()
        audio.getpieces(audio_file, beats).encode(self.audio_files_dir + '/' + output_filename)
