# -*- coding: utf-8 -*-

import argparse
import asyncio
import logging
import math
import time

from collections import namedtuple
from pathlib import Path
from struct import pack, calcsize
from typing import Awaitable, List, Tuple

import aiohttp
import humanize

from aiohttp.formdata import FormData

from jinja2 import Environment, FileSystemLoader
from jinja2.environment import Template

from yarl import URL

from il2fb.maps.heightmaps.constants import HEIGHT_PACK_FORMAT
from il2fb.maps.heightmaps.constants import MAP_SCALE
from il2fb.maps.heightmaps.constants import MAX_OBJECTS_IN_MISSION
from il2fb.maps.heightmaps.logging import setup_logging


__here__ = Path(__file__).parent.absolute()


LOG = logging.getLogger(__name__)


PointsPartition = namedtuple('PointsPartition', ['start', 'end'])


def load_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create heightmap for a given location of "
            "«IL-2 Sturmovik: Forgotten Battles»"
        ),
    )
    parser.add_argument(
        '-l', '--loader',
        dest='loader',
        type=str,
        help="Map loader, e.g. 'Hawaii/load.ini'",
        required=True,
    )
    parser.add_argument(
        '--height',
        dest='height',
        type=int,
        required=True,
        help=f"Map height in meters. Must be proportional to {MAP_SCALE}",
    )
    parser.add_argument(
        '--width',
        dest='width',
        type=int,
        required=True,
        help=f"Map width in meters. Must be proportional to {MAP_SCALE}",
    )
    parser.add_argument(
        '-o', '--out',
        dest='output_file_path',
        type=lambda x: Path(x).resolve(),
        default="heightmap.raw",
        help="Output file path. Default: 'heightmap.raw'",
    )
    parser.add_argument(
        '-s', '--servers',
        dest='server_addresses',
        type=URL,
        nargs='+',
        required=True,
    )

    args = parser.parse_args()

    if args.height % MAP_SCALE != 0:
        parser.error(f"Map height must be proportional to {MAP_SCALE}")

    if args.width % MAP_SCALE != 0:
        parser.error(f"Map width must be proportional to {MAP_SCALE}")

    return args


def log_input_data(args: argparse.Namespace) -> None:
    map_name = args.loader.split('/', 1)[0]

    LOG.debug(f"map to query: {map_name}")
    LOG.debug(f"  height, m: {args.height}")
    LOG.debug(f"   width, m: {args.width}")
    LOG.debug(f"output file: {args.output_file_path}")
    LOG.debug(f"servers:")

    for s in args.server_addresses:
        LOG.debug(f"  - {s}")


def get_mission_template() -> Template:
    jinja_env = Environment(
        loader=FileSystemLoader(str(__here__ / 'templates'))
    )
    return jinja_env.get_template('mission.j2')


def get_total_points_number(height: int, width: int) -> int:
    return (height // MAP_SCALE) * (width // MAP_SCALE)


def partition_points(
    total_points: int,
    partitions: int,
) -> List[PointsPartition]:

    current_id = 0
    last_id = total_points - 1

    step = min(
        MAX_OBJECTS_IN_MISSION,
        math.ceil(total_points / partitions),
    )

    for start_id in range(step, last_id, step):
        yield PointsPartition(current_id, start_id - 1)
        current_id = start_id

    if current_id != last_id:
        yield PointsPartition(current_id, last_id)


async def process_partitions_queue(
    loop: asyncio.BaseEventLoop,
    partitions_queue: asyncio.Queue,
    results_queue: asyncio.Queue,
    server_address: URL,
    mission_template: Template,
    mission_loader: str,
    width: int,
    scale: int,
) -> Awaitable[None]:

    mission_name = mission_loader.split('/', 1)[0]

    async with aiohttp.ClientSession() as http:
        while True:
            partition = await partitions_queue.get()

            if partition is None:
                partitions_queue.task_done()
                return

            await process_partition(
                loop=loop,
                results_queue=results_queue,
                server_address=server_address,
                http=http,
                partition=partition,
                mission_template=mission_template,
                mission_loader=mission_loader,
                mission_name=mission_name,
                width=width,
                scale=scale,
            )
            partitions_queue.task_done()


def index_to_point(idx: int, width: int, scale: int) -> Tuple[int, int]:
    y, x = divmod(idx * scale, width)
    y *= scale
    return (x, y)


async def process_partition(
    loop: asyncio.BaseEventLoop,
    results_queue: asyncio.Queue,
    server_address: URL,
    http: aiohttp.ClientSession,
    partition: PointsPartition,
    mission_template: Template,
    mission_loader: str,
    mission_name: str,
    width: int,
    scale: int,
) -> Awaitable[None]:
    LOG.debug(
        f"query range [{partition.start}:{partition.end}] on server "
        f"{server_address}"
    )

    file_name = f"{mission_name}_{partition.start}_{partition.end}.mis"
    missions_url = server_address / "missions"
    mission_dir_url = missions_url / "heightmap"
    mission_url = mission_dir_url / file_name

    points = (
        index_to_point(i, width, scale)
        for i in range(partition.start, partition.end + 1)
    )
    mission = mission_template.render(
        loader=mission_loader,
        points=points,
    )

    data = FormData()
    data.add_field(
        'mission',
        mission.encode(),
        filename=file_name,
        content_type='plain/text',
    )

    await http.post(mission_dir_url, data=data)
    await http.post(mission_url / "load")
    await http.post(missions_url / "current" / "begin")

    async with http.get(server_address / "radar" / "stationary-objects") as response:
        data = await response.json()
        data = [
            pack(HEIGHT_PACK_FORMAT, int(point['pos']['z']))
            for point in data
        ]
        data = b''.join(data)

    await http.post(missions_url / "current" / "unload")
    await http.delete(mission_url)

    await results_queue.put((partition, data))


async def process_results_queue(
    results_queue: asyncio.Queue,
    total_points: int,
    output_file_path: Path,
) -> Awaitable[None]:

    point_size = calcsize(HEIGHT_PACK_FORMAT)
    output_size = point_size * total_points

    natural_size = humanize.naturalsize(
        output_size,
        binary=True,
        format='%.3f',
    )
    LOG.debug(f"output size: {natural_size}")

    output_file_path.parent.parent.mkdir(parents=True, exist_ok=True)

    with output_file_path.open('wb') as f:
        f.truncate(output_size)

        while True:
            data = await results_queue.get()
            if not data:
                results_queue.task_done()
                return

            partition, values = data
            start = partition.start * point_size

            LOG.debug(
                f"gather results for range [{partition.start}:{partition.end}]"
            )

            f.seek(start)
            f.write(values)

            results_queue.task_done()


async def run(
    loop: asyncio.BaseEventLoop,
    server_addresses: List[URL],
    mission_template: Template,
    mission_loader: str,
    height: int,
    width: int,
    scale: int,
    output_file_path: Path,
) -> Awaitable[None]:

    total_points = get_total_points_number(height, width)
    LOG.debug(f"total points to query: {total_points}")

    results_queue = asyncio.Queue(loop=loop)
    future = process_results_queue(
        results_queue=results_queue,
        total_points=total_points,
        output_file_path=output_file_path,
    )
    asyncio.ensure_future(future, loop=loop)

    servers_count = len(server_addresses)
    partitions_queue = asyncio.Queue(servers_count, loop=loop)

    for server_address in server_addresses:
        future = process_partitions_queue(
            loop=loop,
            partitions_queue=partitions_queue,
            results_queue=results_queue,
            server_address=server_address,
            mission_template=mission_template,
            mission_loader=mission_loader,
            width=width,
            scale=scale,
        )
        asyncio.ensure_future(future, loop=loop)

    start_time = time.monotonic()

    partitions = partition_points(total_points, servers_count)
    for partition in partitions:
        await partitions_queue.put(partition)

    for i in range(servers_count):
        await partitions_queue.put(None)

    await partitions_queue.join()

    await results_queue.put(None)
    await results_queue.join()

    run_time = time.monotonic() - start_time
    LOG.debug(f"run time: {run_time:.3f} s")


def main() -> None:
    args = load_args()
    loop = asyncio.get_event_loop()

    setup_logging()
    log_input_data(args)

    mission_template = get_mission_template()
    loop.run_until_complete(run(
        loop=loop,
        server_addresses=args.server_addresses,
        mission_template=mission_template,
        mission_loader=args.loader,
        height=args.height,
        width=args.width,
        scale=MAP_SCALE,
        output_file_path=args.output_file_path,
    ))


if __name__ == '__main__':
    main()
