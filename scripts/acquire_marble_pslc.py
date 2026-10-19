#!/usr/bin/env python3
"""Download the public PSLC Tulalip 2013 bare-earth mosaic, without outreach.

HTTP range downloads are resumable. GDAL's OpenFileGDB raster driver reads the
original mosaic; source metadata specifies EPSG:2926 and US survey foot heights.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import errno
from pathlib import Path
import subprocess
import sys
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from karstfinder.gis import sha

URL = 'https://pugetsoundlidar.ess.washington.edu/lidardata/restricted/filegeodatabase/pslc2013/tulalip/2013tulalip_be.gdb.7z'
SIZE = 5841853674


def main():
    raw = ROOT / 'data/raw/marble_v001'
    raw.mkdir(parents=True, exist_ok=True)
    for name, url in [
            ('pslc_tulalip.html', 'https://pugetsoundlidar.ess.washington.edu/lidardata/restricted/projects/2013tulalip.html'),
            ('2013tulalip_deliv2_be.html', 'https://pugetsoundlidar.ess.washington.edu/lidardata/metadata/2013tulalip_deliv2_be.html')]:
        if not (raw / name).exists():
            response = requests.get(url, timeout=120); response.raise_for_status()
            (raw / name).write_bytes(response.content)
    archive = raw / '2013tulalip_be.gdb.7z'
    part = archive.with_suffix('.7z.part')
    progress = raw / 'pslc_download_progress.json'
    if not archive.exists():
        if progress.exists():
            checkpoint = json.loads(progress.read_text())
        else:
            checkpoint = {'prefix_bytes': part.stat().st_size if part.exists() else 0, 'completed_ranges': []}
            progress.write_text(json.dumps(checkpoint))
        with part.open('ab') as stream:
            stream.truncate(SIZE)
        step = 64 * 1024 * 1024
        completed = {tuple(x) for x in checkpoint['completed_ranges']}
        ranges = [(n, min(n+step, SIZE)-1) for n in range(checkpoint['prefix_bytes'], SIZE, step)]

        def fetch(bounds):
            start, end = bounds
            for attempt in range(4):
                try:
                    with requests.get(URL, headers={'Range': f'bytes={start}-{end}'}, stream=True, timeout=(30, 120)) as response:
                        response.raise_for_status()
                        assert response.status_code == 206
                        assert response.headers['Content-Range'] == f'bytes {start}-{end}/{SIZE}'
                        with part.open('r+b') as stream:
                            stream.seek(start); total = 0
                            for block in response.iter_content(1024*1024):
                                stream.write(block); total += len(block)
                        assert total == end-start+1
                    return bounds
                except (requests.RequestException, AssertionError):
                    if attempt == 3:
                        raise

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(fetch, r) for r in ranges if r not in completed]
            for future in as_completed(futures):
                completed.add(future.result())
                checkpoint['completed_ranges'] = sorted(completed)
                progress.write_text(json.dumps(checkpoint))
                print(f'{len(completed)}/{len(ranges)} ranges complete', flush=True)
        assert set(ranges) == completed
        try:
            part.replace(archive)
        except OSError as error:
            if error.errno != errno.ENOSPC:
                raise
            # All requested byte ranges are present. A filename change is not
            # needed to read/CRC-verify this completed public archive. Preserve
            # the actual path in provenance rather than bypassing catalog writes.
            archive = part
    subprocess.run(['7z', 't', str(archive)], check=True, stdout=subprocess.DEVNULL)
    folder = raw / 'pslc_gdb'
    complete = raw / 'pslc_extraction_complete.json'
    if not complete.exists():
        # A failed extraction may leave a directory. Its existence alone must
        # never authorize using a partially extracted source geodatabase.
        subprocess.run(['7z', 'x', '-y', '-o'+str(folder), str(archive)], check=True, stdout=subprocess.DEVNULL)
        complete.write_text(json.dumps({'archive_sha256': sha(archive), 'extraction_exit_code': 0})+'\n')
    else:
        assert json.loads(complete.read_text())['archive_sha256'] == sha(archive)
    record = {'url': URL, 'path': str(archive.relative_to(ROOT)), 'bytes': archive.stat().st_size,
              'sha256': sha(archive), 'archive_crc_verified': True,
              'source_page': 'https://pugetsoundlidar.ess.washington.edu/lidardata/restricted/projects/2013tulalip.html',
              'metadata_path': 'data/raw/marble_v001/2013tulalip_deliv2_be.html',
              'metadata_sha256': sha(raw / '2013tulalip_deliv2_be.html'),
              'horizontal_crs': 'EPSG:2926', 'vertical_datum': 'NAVD88 / Geoid03',
              'horizontal_and_vertical_units': 'US survey feet', 'native_cell_size_ftUS': 3,
              'acquisition_year': 2013, 'restrictions': 'No outreach; public PSLC data download only.'}
    (ROOT / 'docs/experiments/marble_v001_pslc_acquisition.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record, indent=2), flush=True)


if __name__ == '__main__':
    main()
