"""
A module for the AudioInfoExtractor class.
"""

# project modules
from music_machine import data_structures
from music_machine import miscellany
# installed modules
from echonest.remix import audio
# default modules
import math
import numpy
import os
import pickle
import sys
import yaml


class AudioInfoExtractor(object):
    """
    A class to extract information from audio files.
    """

    def __init__(self, config_filename):

        config_file = open(config_filename, 'r')
        config = yaml.load(config_file)
        config_file.close()

        self.audio_files_dir = \
            os.environ['MUSIC_MACHINE_DIR'] + '/' + config['audio_files_dir']
        self.pickled_files_dir = \
            os.environ['MUSIC_MACHINE_DIR'] + '/' + config['pickled_objects_dir']

        self.audio_files = data_structures.DictionaryForUnhashables()


    # audio file processing -----------------------------------------------------------------------


    def get_audio_file(self, filename):
        """
        description:
        A method that returns the echonest.remix.audio.LocalAudioFile object associated with an
        audio file. If the file has been processed before, it is returned from memory. Otherwise,
        it is processed, stored in self.audio_files, and then returned.
        The method first looks for a previously pickled echonest.remix.audio.LocalAudioFile object.
        If it finds such an object, the object is unpickled and stored. (Pickled LocalAudioFile
        objects can be created using the pickle_audio_file method.) If no pickled LocalAudioFile
        object is found, the method processes the file from scratch using Echo Nest. An internet
        connection is necessary to perform the latter.

        inputs:
        -- str filename -- The name of the audio file.

        return info:
        -- return type -- echonest.remix.audio.LocalAudioFile
        """

        if self.audio_files.contains(filename):
            return self.audio_files.get(filename)
        else:
            try:
                miscellany.log('Processing %s.' % filename)
                pickled_audio_file = open(
                    self.pickled_files_dir + '/' + filename + '.pickled', 'r')
                print 'Found pickled audio file. Unpickling...'
                audio_file = pickle.load(pickled_audio_file)
                pickled_audio_file.close()
            except IOError:
                try:
                    audio_file = audio.LocalAudioFile(self.audio_files_dir + '/' + filename)
                except:
                    raise Exception('Unable to process %s.' % filename)
            self.audio_files.add(filename, audio_file)
            print 'Success!'
            return audio_file


    def pickle_audio_file(self, filename):
        """
        description:
        A method that pickles the echonest.remix.audio.LocalAudioFile object associated with an
        audio file. Pickling LocalAudioFile objects is useful for offline access as the
        LocalAudioFile constructor requires internet access.

        inputs:
        -- str filename -- The name of the audio file.

        return info:
        -- return type -- void
        """

        audio_file = self.get_audio_file(filename)
        pickled_audio_file = open(self.pickled_files_dir + '/' + filename + '.pickled', 'w')
        pickle.dump(audio_file, pickled_audio_file)
        pickled_audio_file.close()


    # audio file information extraction -----------------------------------------------------------


    def get_beat_times(self, filename):
        """
        description:
        A method that extracts the times of all of the beats in an audio file (the times being
        relative to the start of the audio file).

        inputs:
        -- str filename -- The name of the audio file.

        return info:
        -- returns -- [beat 1 time, beat 2 time, beat 3 time, ...]
        -- return type -- list of floats
        """

        audio_file = self.get_audio_file(filename)
        beats = audio_file.analysis.beats
        beat_times = []
        for i in xrange(len(beats)):
            beat_times.append(beats[i].start)
        return beat_times


    def get_freq_data(self, filename,
                      num_of_buckets=10, lowest_freq=20, highest_freq=10000, fps=10,
                      max_value=100):
        """
        description:
        A method that uses a Fourier transform to extract the frequency data from an audio file.
        See the method's helper methods (_get_freq_bucket_boundaries, _get_freq_bucket_values, and
        _scale) to better understand how it works.

        inputs:
        -- str filename -- The name of the audio file.
        -- int num_of_buckets -- The number of frequency buckets.
        -- int lowest_freq -- The lower bound on the frequencies to consider (in Hertz).
        -- int highest_freq -- The upper bound on the frequencies to consider (in Hertz).
        -- int fps -- The number of time frames to include per second of audio.
        -- int max_value -- The maximum value possible in a bucket. Used to normalize the raw
            values obtained.

        return info:
        -- returns --
            [time frame 1, time frame 2, time frame 3, ...]
            where each time frame is a list of bucket values
            time frame = [bucket 1 value, bucket 2 value, bucket 3 value, ...]
        -- return type -- list of lists of floats
        """

        if num_of_buckets < 1:
            raise Exception('Invalid number of buckets.')

        audio_file = self.get_audio_file(filename)
        boundaries = self._get_freq_bucket_boundaries(num_of_buckets, lowest_freq, highest_freq)

        miscellany.log('Extracting frequency data from %s.' % filename)

        step = int(float(audio_file.sampleRate) / fps)
        start = 0
        end = step

        num_of_steps = len(audio_file.data) / step
        previously_printed = None

        freq_data = []
        for i in xrange(num_of_steps):

            freq_data.append(self._get_freq_bucket_values(
                audio_file.data[start:end], boundaries, audio_file.sampleRate))
            start = start + step
            end = end + step

            progress = int(float(i) / num_of_steps * 100)
            if progress in [10, 20, 30, 40, 50, 60, 70, 80, 90] and \
               progress != previously_printed:
                sys.stdout.write(str(progress) + '% ')
                sys.stdout.flush()
                previously_printed = progress

        sys.stdout.write('100%\n')

        print 'Scaling data.'
        self._scale(freq_data, max_value)

        print 'Success!'
        return freq_data


    def _get_freq_bucket_boundaries(self, num_of_buckets, lowest_freq, highest_freq):
        """
        A helper method for get_freq_data. Its functionality is better described with an example.
        Given num_of_buckets = 10, lowest_freq = 20, and highest_freq = 20000, the method will
        return the list [20, 39, 79, 158, 316, 632, 1261, 2517, 5023, 10023, 20000]. Note that the
        list contains num_of_buckets + 1 values as each bucket is associated with two boundaries,
        one lower and one upper. Also note that the values lie along an exponential curve. In other
        words, the bucket ranges increase. This conscious decision involves how we perceive sounds
        of different frequencies.
        """

        if num_of_buckets == 1:
            return [lowest_freq, highest_freq]

        scaling_factor = (float(highest_freq) / lowest_freq) ** (1 / float(num_of_buckets))
        prev_boundary = lowest_freq

        boundaries = [lowest_freq]
        for dummy in xrange(num_of_buckets - 1):
            boundary = prev_boundary * scaling_factor
            boundaries.append(int(boundary))
            prev_boundary = boundary

        boundaries.append(highest_freq)

        return boundaries


    def _get_freq_bucket_values(self, data, boundaries, sample_rate):
        """
        A helper method for get_freq_data. It's in this method that the Fourier transform is
        actually performed. The transform is applied to the raw audio data provided to extract its
        frequency content, the frequency buckets being defined by the provided list of bucket
        boundaries.
        """

        # Use rfft (inseatd of fft) since the data is all real. When the input to a Fourier
        # transform is all real, the result is symmetric. The second half of the values are the
        # complex conjugates of the first half of values. rfft accordingly doesn't calculate this
        # second half of values, making it slightly more efficient than fft.
        coefficients = numpy.fft.rfft(data, axis=0)

        # Take the absolute values of the imaginary coefficients and average the values for the
        # left and right channels to get a more accessible measure of power.
        processed_coefficients = []
        for i in xrange(len(coefficients)):
            processed_coefficients.append(
                (abs(coefficients[i][0]) + abs(coefficients[i][1])) * 0.5)

        step = float(sample_rate) / len(data)
        start = int(boundaries[0] / step)

        # Average all of the coefficients that fall in a bucket to get the final value for that
        # bucket.
        values = []
        for i in range(1, len(boundaries)):
            end = int(boundaries[i] / step)
            values.append(sum(processed_coefficients[start:end]) / (end - start))
            start = end

        return values


    def _scale(self, freq_data, new_max_value):
        """
        A helper method for get_freq_data. Scales the frequency data produced by get_freq_data such
        that the new max is the value specified. The method also decreases the difference between
        small and large values by taking the square root of the original data.
        """

        self._map_to_nested_list(math.sqrt, freq_data)

        max_value = self._find_max(freq_data)
        scaling_factor = new_max_value / max_value
        self._map_to_nested_list(lambda x: x * scaling_factor, freq_data)

        return scaling_factor


    def _map_to_nested_list(self, function, nested_list):
        """
        A helper method to map a function to a nested list with one level of nesting
        ([[values], [values], [values], ...]).
        """
        for i in xrange(len(nested_list)):
            for j in xrange(len(nested_list[i])):
                nested_list[i][j] = function(nested_list[i][j])


    def _find_max(self, nested_list):
        """
        A helper method to find the maximum value in a nested list with one level of nesting
        ([[values], [values], [values], ...]).
        """
        global_max = 0
        for list_ in nested_list:
            local_max = max(list_)
            if local_max > global_max:
                global_max = local_max
        return global_max
