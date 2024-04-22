import argparse
import pathlib
from pydub import AudioSegment
import math
from datetime import timedelta
from subprocess import Popen, call, PIPE, STDOUT, DEVNULL
from tinytag import TinyTag


def check_bash_package_installed(package_name):
    if call(["which", package_name], stdin=PIPE, stdout=DEVNULL, stderr=STDOUT, timeout=60) == 0:
        return True
    return False


def time_format(seconds):
    if not isinstance(seconds, int):
        print('🛑 time_format(): Variable is not int')
        return '00:00:00'
    if seconds < 0:
        print('🛑 time_format(): Variable is < 0 ')
        return '00:00:00'

    return '{:0>8}'.format(str(timedelta(seconds=int(seconds))))


def get_m4a_duration_slow(path: pathlib.Path):
    path = pathlib.Path(path)
    try:
        audio = AudioSegment.from_file(path)
    except Exception as e:
        print('🛑 Some Error in get_m4a_duration(): ', e)
        return 0

    return len(audio) / 1000


def get_m4a_duration_fast(path: pathlib.Path):
    path = pathlib.Path(path)
    try:
        audio = TinyTag.get(path)
    except Exception as e:
        print('🛑 Some Error in get_m4a_duration(): ', e)
        return 0

    return audio.duration


def get_m4a_duration(path: pathlib.Path):
    duration = get_m4a_duration_fast(path)
    if duration is None:
        duration = get_m4a_duration_slow(path)
    return math.ceil(duration)


def make_salad(
        input_m4a: pathlib.Path,
        duration: int = 12,
        delta: int = 7,
        bitrate: int = 48,
        timeout_subprocess: int = 600,
):
    if not check_bash_package_installed('ffmpeg'):
        print('🛑 Error! Package FFMPEG is not installed!')
        return

    input_m4a = pathlib.Path(input_m4a)
    if not input_m4a.exists():
        print('🛑 Error! Your .m4a file is not exist! Check it')
        return

    if input_m4a.suffix not in ['.m4a']:
        print('🛑 Error! Audio Book file is not .m4a')
        return

    if duration < 1:
        duration = 1
    elif duration > 241:
        duration = 241
    duration = duration * 60

    if delta < 0:
        delta = 0
    if delta > 299:
        delta = 299

    if bitrate < 16:
        bitrate = 16
    elif bitrate > 256:
        bitrate = 256

    print('🥗 Salad Long Audio Books. Your input audio: ')
    audio_length = get_m4a_duration(input_m4a)
    print(f'🔹 {input_m4a.name} \t {time_format(get_m4a_duration(input_m4a))}')

    parts = []
    time = 0
    while time < audio_length:
        if time == 0:
            parts.append([time, time + duration + delta])
        elif time + duration > audio_length:
            # Golden ration
            if duration / (audio_length - time + delta) > 1.618:
                parts[-1][1] = audio_length
            else:
                # Add one second to add all
                parts.append([time - delta, audio_length+1])
        else:
            parts.append([time - delta, time + duration + delta])
        time += duration

    output_dir = input_m4a.parent.joinpath(input_m4a.stem)
    if not output_dir.exists():
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print('🛑 Some Error. output_dir.mkdir(): ', e)

    cmds_list = []
    for idx, part in enumerate(parts):
        # print('🔹', part, ' len: ', (part[1] - part[0]) / 60)
        output_path = output_dir.joinpath(f'{input_m4a.stem}-{idx + 1}-{len(parts)}.m4a')
        if output_path.exists():
            try:
                output_path.unlink()
            except Exception as e:
                print('🛑 Some Error unlinking last .m4a: ', e)

        compress_cmd = ''
        if bitrate:
            compress_cmd = f'-c:a aac -b:a {bitrate}k'

        cmd = f'ffmpeg -i {input_m4a.as_posix()} -ss {time_format(part[0])} -to {time_format(part[1])} {compress_cmd} {output_path.as_posix()}'
        # print(cmd)
        # print()

        cmds_list.append(cmd.split(' '))

    print('🟢 Cooking your salad. Wait it it will be finished, I notify your :) ')
    print('...')
    processes = [Popen(cmd, stdout=PIPE, stderr=PIPE) for cmd in cmds_list]

    if processes:
        last_process = processes[-1]
        last_process.wait(timeout=timeout_subprocess)

    print("🟢 All Done! Lets see .m4a files and their length")
    for m4a_file in sorted(list(filter(lambda f: (f.suffix in ['.m4a']), output_dir.iterdir()))):
        print(f'🔹 {m4a_file.name} \t {time_format(get_m4a_duration(m4a_file))}')
    print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='🥗 Salad Long Audio Books',
        description='🥗 It splits your .m4a file into several parts by duration',
        add_help=True
    )

    parser.add_argument('-d', '--duration', type=int, default=12, help='Duration (in minutes) [Default is 12 minutess]')
    parser.add_argument('--delta', type=int, default=7, help='Delta time bounds around cutting place (in seconds) [Default is 7 seconds]')
    parser.add_argument('--bitrate', type=int, default=48, help='Bitrate like: 48 - means 48k. [Default is 48]')
    parser.add_argument('--timeout-subprocess', type=int, default=600, help='Timeout fo Subprocess FFMPEG (in seconds). [Default 600 seconds]')
    parser.add_argument('path', type=pathlib.Path, help='Audio Book path in format .m4a')

    args = parser.parse_args()
    make_salad(args.path, args.duration, args.delta, args.bitrate, args.timeout_subprocess)
