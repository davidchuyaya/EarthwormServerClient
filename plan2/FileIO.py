import struct
import os
import calendar
import array
from collections import namedtuple

UNDEFINED = -12345          # undefined value
UNDEFINED_STR = "-12345  "  # undefined value for strings

SAC_HEADER_SIZE = 632
NUM_FLOAT = 70      # number of floats in header
MAX_INT = 40        # number of ints in header
MAX_STRING = 24     # number of strings in header
K_LEN = 8           # length of all other string fields
SAC_FORMAT = "={0}f{1}i".format(NUM_FLOAT, MAX_INT)
for i in range(0, MAX_STRING):
    SAC_FORMAT += "{0}s".format(K_LEN)


def get_sac_head(sac, file_size):
    """
    For information on the meaning behind each of the variables we read from the struct, refer to sachead.h
    within Earthworm source code.

    :param sac: Sac file read in byte mode
    :param int file_size: Size of sac file in bytes
    :return: SacHeader with fields specified below
    """
    SacHeader = namedtuple("SacHeader", ['delta', 'depmin', 'depmax', 'scale', 'odelta', 'b', 'e', 'o', 'a', 'internal1', 't0', 't1', 't2', 't3', 't4', 't5', 't6', 't7', 't8', 't9', 'f', 'resp0', 'resp1', 'resp2', 'resp3', 'resp4', 'resp5', 'resp6', 'resp7', 'resp8', 'resp9', 'stla', 'stlo', 'stel', 'stdp', 'evla', 'evlo', 'evel', 'evdp', 'blank1', 'user0', 'user1', 'user2', 'user3', 'user4', 'user5', 'user6', 'user7', 'user8', 'user9', 'dist', 'az', 'baz', 'gcarc', 'internal2', 'internal3', 'depmen', 'cmpaz', 'cmpinc', 'blank4', 'blank4_2', 'blank4_3', 'blank4_4', 'blank4_5', 'blank4_6', 'blank4_7', 'blank4_8', 'blank4_9', 'blank4_10', 'blank4_11', 'nzyear', 'nzjday', 'nzhour', 'nzmin', 'nzsec', 'nzmsec', 'internal4', 'internal5', 'internal6', 'npts', 'internal7', 'internal8', 'blank6', 'blank6_2', 'blank6_3', 'iftype', 'idep', 'iztype', 'iblank6a', 'iinst', 'istreg', 'ievreg', 'ievtyp', 'iqual', 'isynth', 'blank7', 'blank7_2', 'blank7_3', 'blank7_4', 'blank7_5', 'blank7_6', 'blank7_7', 'blank7_8', 'blank7_9', 'blank_10', 'leven', 'lpspol', 'lovrok', 'lcalda', 'lblank1', 'kstnm', 'kevnm', 'kevnm_2', 'khole', 'ko', 'ka', 'kt0', 'kt1', 'kt2', 'kt3', 'kt4', 'kt5', 'kt6', 'kt7', 'kt8', 'kt9', 'kf', 'kuser0', 'kuser1', 'kuser2', 'kcmpnm', 'knetwk', 'kdatrd', 'kinst'])

    sac_header = SacHeader._make(struct.unpack(SAC_FORMAT, sac.read(SAC_HEADER_SIZE)))
    # npts = number of points in trace
    data_size = sac_header.npts * 4     # 4 = size of float

    if data_size + SAC_HEADER_SIZE != file_size:
        print("Swapping is needed, exiting")
        exit(1)

    return sac_header


# 2 ints (pinno, nsamp)
# 3 doubles (starttime, endtime, samprate)
# 7 chars (station)
# 9 chars (network)
# 4 chars (channel)
# 3 chars (location)
# 2 chars (version)
# 3 chars (datatype)
# 2 chars (quality)
# 2 chars (padding)
TRACEBUF_FORMAT = "=2i3d7s9s4s3s2s3s2s2s"
MAX_TRACEBUF_SAMPLES = 100


def set_tracebuf_header(nsamp, starttime, endtime, samprate, station, network, channel, location):
    """
    Returns bytes that represent the a tracebuf's header

    :param int nsamp: Number of samples
    :param double starttime: Start epoch time of data collection
    :param double endtime: End epoch time of data collection
    :param double samprate: Sample rate
    :param str station: Station name of detector
    :param str network: Network name
    :param str channel: Channel name
    :param str location: Location name
    :return: Bytes
    """
    pinno = 0            # Pin number
    quality = b'\0'
    datatype = b"i4"     # intel
    version = b"20"      # Tracebuf version 2.0
    padding = b''
    tracebuf_bytes = struct.pack(TRACEBUF_FORMAT, pinno, nsamp, starttime, endtime, samprate, station.encode(), network.encode(), channel.encode(), location.encode(), version, datatype, quality, padding)
    return tracebuf_bytes


def convert_sac_to_tracebuf(sac_path, tracebuf_path):
    """
    Converts the sac file at the given path to a tracebuf file. Based on sac2tb.exe.
    Note that sac2tb also performs multiple sanity checks and checks for byte swapping, most of which are not done by this method. We assume most data we receive to be sanitary and not require byte swaps.
    There are multiple prints in the method for debugging. Comment them out to maximize speed.

    :param sac_path: Path to load .sac file from
    :param tracebuf_path: Path to write tracebuf file to
    :return:
    """
    with open(sac_path, "rb") as sac:
        sac_header = get_sac_head(sac, os.path.getsize(sac_path))

        if sac_header.delta < 0.001:
            print("SAC sample period too small")
            return

        station = sac_header.kstnm.decode().strip()
        print("Station: {0}.".format(station))
        channel = sac_header.kcmpnm.decode().strip()
        print("Channel: {0}.".format(channel))
        network = sac_header.knetwk.decode().strip()
        print("Network: {0}.".format(network))
        location = sac_header.khole.decode()
        if location != UNDEFINED_STR:
            location = location.strip()
            print("Location: {0}.".format(location))

        sample_interval = sac_header.delta
        sample_rate = 1.0 / sample_interval

        # find sac reference time
        start_time = calendar.timegm((sac_header.nzyear, 1, sac_header.nzjday, sac_header.nzhour, sac_header.nzmin, sac_header.nzsec, 0, 0, 0))
        start_time += sac_header.nzmsec / 1000.0
        print("Start time: {0}.".format(start_time))

        print("Number of parts: {0}.".format(sac_header.npts))

        # Gets all actual SAC data. Array of floats
        sac_data_array = array.array("f")
        sac_data_array.fromfile(sac, sac_header.npts)
        sac_data_floats = sac_data_array.tolist()
        # Convert to array of ints for tracebuf
        sac_data_ints = list(map(lambda data_float: int(data_float), sac_data_floats))
        print("Data: " + str(sac_data_ints) + ".")

        num_samples_remaining = sac_header.npts     # the number of samples we haven't converted yet
        sac_data_start_index = 0                    # the index of the next chunk of data to save

        while num_samples_remaining > 0:

            # the number of samples = either MAX or whatever is left. Each tracebuf can only have a certain number of samples.
            samples_in_tracebuf = min(MAX_TRACEBUF_SAMPLES, num_samples_remaining)

            temp_start_time = start_time + sample_interval * samples_in_tracebuf
            end_time = temp_start_time - sample_interval
            num_samples_remaining -= MAX_TRACEBUF_SAMPLES

            # Create Tracebuf header
            header = set_tracebuf_header(nsamp=samples_in_tracebuf, starttime=start_time, endtime=end_time, samprate=sample_rate, station=station, network=network, channel=channel, location=location)

            start_time = temp_start_time

            # write to file. Note that if the file originally existed, we append to the file instead of overwriting
            with open(tracebuf_path, "ab") as tracebuf:
                tracebuf.write(header)
                for i in range(0, samples_in_tracebuf):
                    data = struct.pack("i", sac_data_ints[i + sac_data_start_index])
                    tracebuf.write(data)
            sac_data_start_index += samples_in_tracebuf

        print("done")
