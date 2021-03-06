from spikeextractors import RecordingExtractor
from spikeextractors.extraction_tools import check_get_traces_args, check_get_ttl_args
import numpy as np
from pathlib import Path

try:
    import pyintan
    HAVE_INTAN = True
except ImportError:
    HAVE_INTAN = False


class IntanRecordingExtractor(RecordingExtractor):
    extractor_name = 'IntanRecording'
    has_default_locations = False
    is_writable = False
    mode = 'file'
    installed = HAVE_INTAN  # check at class level if installed or not
    installation_mesg = "To use the Intan extractor, install pyintan: \n\n pip install pyintan\n\n"  # error message when not installed

    def __init__(self, file_path, verbose=False):
        assert HAVE_INTAN, self.installation_mesg
        RecordingExtractor.__init__(self)
        assert Path(file_path).suffix == '.rhs' or Path(file_path).suffix == '.rhd', \
            "Only '.rhd' and '.rhs' files are supported"
        self._recording_file = file_path
        self._recording = pyintan.File(file_path, verbose)
        self._kwargs = {'file_path': str(Path(file_path).absolute()), 'verbose': verbose}

    def get_channel_ids(self):
        return list(range(self._recording.analog_signals[0].signal.shape[0]))

    def get_num_frames(self):
        return self._recording.analog_signals[0].signal.shape[1]

    def get_sampling_frequency(self):
        return float(self._recording.sample_rate.rescale('Hz').magnitude)

    @check_get_traces_args
    def get_traces(self, channel_ids=None, start_frame=None, end_frame=None):
        return self._recording.analog_signals[0].signal[channel_ids, start_frame:end_frame]

    @check_get_ttl_args
    def get_ttl_events(self, start_frame=None, end_frame=None, channel_id=0):
        channels = [np.unique(ev.channels)[0] for ev in self._recording.digital_in_events]
        assert channel_id in channels, f"Specified 'channel' not found. Available channels are {channels}"
        ev = self._recording.events[channels.index(channel_id)]

        ttl_frames = (ev.times.rescale("s") * self.get_sampling_frequency()).magnitude.astype(int)
        ttl_states = np.sign(ev.channel_states)
        ttl_valid_idxs = np.where((ttl_frames >= start_frame) & (ttl_frames < end_frame))[0]
        return ttl_frames[ttl_valid_idxs], ttl_states[ttl_valid_idxs]
