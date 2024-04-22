import argparse
import pathlib
from pydub import AudioSegment
from mutagen.mp4 import MP4
import math
from datetime import timedelta
from subprocess import Popen, PIPE


# Max delta seconds
MAX_DELTA = 59
MIN_LAST_AUDIO_SEGMENT_DURATION = 300


def make_salad(path: pathlib.Path, duration: int = 12, delta: int = 7, compress_bitrate: str = '48k'):
    path = pathlib.Path(path)
    if duration < 0:
        duration = 0
    if delta < 0:
        delta = 0
    if delta > MAX_DELTA:
        delta = MAX_DELTA
    if not path.exists():
        print('🛑 Error! Audio Book file not exists!')
        return
    if path.suffix not in ['.m4a']:
        print('🛑 Error! Audio Book file is not .m4a')
        return

    duration = duration * 60

    output_dir = path.parent.joinpath(path.stem)
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    audio = MP4(path)

    audio_length = math.ceil(audio.info.length)

    parts = []
    step_time = audio_length % duration
    time = 0
    while time < audio_length:
        if time == 0:
            parts.append([time, time + duration + delta])
        elif time + duration > audio_length:
            # Golden ration
            if duration / (audio_length - time + delta) > 1.618:
                parts[-1][1] = audio_length
            else:
                parts.append([time - delta, audio_length])
        else:
            parts.append([time - delta, time + duration + delta])
        time += duration

    cmds_list = []
    for idx, part in enumerate(parts):
        print('🔹', part, ' len: ', (part[1] - part[0]) / 60)
        output_path = output_dir.joinpath(f'{path.stem}-{idx + 1}-{len(parts)}.m4a')

        compress_cmd = ''
        if compress_bitrate:
            compress_cmd = f'-c:a aac -b:a {compress_bitrate}'

        def time_format(seconds):
            return '{:0>8}'.format(str(timedelta(seconds=seconds)))
        cmd = f'/opt/homebrew/bin/ffmpeg -i {path.as_posix()} -ss {time_format(part[0])} -to {time_format(part[1])} {compress_cmd} {output_path.as_posix()}'
        print(cmd)
        print()

        cmds_list.append(cmd.split(' '))

    print('🏀 Run in parallel')
    processes = [Popen(cmd, stdout=PIPE, stderr=PIPE) for cmd in cmds_list]

    if processes:
        last_process = processes[-1]
        last_process.wait()

    print("🟢 Last subprocess job finished.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=pathlib.Path, help='Audio Book path in format .m4a')
    parser.add_argument('-d', '--duration', type=int, default=12, help='Duration Minutes')
    parser.add_argument( '--delta', type=int, default=7, help='Delta around cut time in seconds')
    parser.add_argument('--bitrate', type=str, default='48k', help='Bitrate like: 48k')

    args = parser.parse_args()
    make_salad(args.path, args.duration, args.delta, args.bitrate)
