"""
A module for the AudioVisualizer class.
"""

# project modules
from music_machine import audio_info_extractor
from music_machine import miscellany
# installed modules
from matplotlib import animation
from matplotlib import pyplot
# default modules
import numpy
import os
import subprocess
import yaml


class AudioVisualizer(object):
    """
    A class to generate audio-inspired visuals.
    """

    def __init__(self, config_filename):

        config_file = open(config_filename, 'r')
        config = yaml.load(config_file)
        config_file.close()

        self.audio_files_dir = \
            os.environ['MUSIC_MACHINE_DIR'] + '/' + config['audio_files_dir']
        self.intermediate_files_dir = \
            os.environ['MUSIC_MACHINE_DIR'] + '/' + config['intermediate_files_dir']
        self.video_files_dir = \
            os.environ['MUSIC_MACHINE_DIR'] + '/' + config['video_files_dir']

        self.extractor = audio_info_extractor.AudioInfoExtractor(config_filename)

        self.animation_data = {}


    def freq_bars(self, audio_filename, mp4_filename,
                  num_of_buckets=10, lowest_freq=20, highest_freq=10000, fps=10,
                  bar_width=0.9):
        """
        """

        freq_data = self.extractor.get_freq_data(
            audio_filename, num_of_buckets, lowest_freq, highest_freq, fps)

        miscellany.log('Creating frequency-bar mp4 for %s.' % audio_filename)

        print 'Preparing animation function.'

        panel = pyplot.figure()

        self.animation_data = {
            'freq_data': freq_data,
            'panel': panel,
            'num_of_buckets': len(freq_data[0]),
            'bars': None,
            'bar_width': bar_width}

        visual = animation.FuncAnimation(
            panel,
            self._freq_bars_animator,
            init_func=self._freq_bars_initializer,
            frames=len(freq_data),
            interval=1000/fps,
            blit=False)

        print 'Saving animation...'
        visual.save(
            self.intermediate_files_dir + '/' + mp4_filename, fps=fps,
            extra_args=['-vcodec', 'mpeg4'])

        print 'Success!'

        miscellany.log('Adding audio to frequency-bar mp4 for %s.' % audio_filename)

        print 'Converting audio...'
        cmd = ['ffmpeg',
               '-i', self.audio_files_dir + '/' + audio_filename,
               self.intermediate_files_dir + '/' + audio_filename.replace('mp3', 'wav')]
        subprocess.call(cmd)

        print 'Merging audio with animation...'
        cmd = ['ffmpeg',
               '-i', self.intermediate_files_dir + '/' + audio_filename.replace('mp3', 'wav'),
               '-i', self.intermediate_files_dir + '/' + mp4_filename,
               '-strict', '-2',
               self.video_files_dir + '/' + mp4_filename]
        subprocess.call(cmd)

        pyplot.close(panel)
        print 'Success!'


    def _freq_bars_initializer(self):
        bar_width = self.animation_data['bar_width']
        pyplot.axes(
            xlim=(-bar_width, self.animation_data['num_of_buckets'] + bar_width),
            ylim=(0, 100))
        pyplot.axis('off')


    def _freq_bars_animator(self, i):
        bar_heights = self.animation_data['freq_data'][i]
        if not self.animation_data['bars']:
            self.animation_data['bars'] = pyplot.bar(
                numpy.arange(self.animation_data['num_of_buckets']),
                bar_heights,
                color='#579BFF', linewidth=0)
        if self.animation_data['bars']:
            for (bar_, bar_height) in zip(self.animation_data['bars'], bar_heights):
                bar_.set_height(bar_height)
