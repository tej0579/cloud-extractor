import sys
# Appending standard path for libtorrent access inside the workspace
sys.path.append('/usr/lib/python3/dist-packages')

import time
import shutil
import os
import libtorrent as lt

# 1. Initialize the Core Torrent Engine Session
ses = lt.session()
ses.listen_on(6881, 6891)

# Target magnet link string configuration plugged in
magnet_link = "magnet:?xt=urn:btih:DDD19A47023DF40F1653A601BC2B1A91D67A36C8&dn=F3+Fun+And+Frustration+2022+UNCUT+1080P+WEBRiP+H265+DDP2+0-5+1+%5BHINDI+%2B+TELUGU%5D+ESUB-SHB931&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A6969%2Fannounce&tr=udp%3A%2F%2Fp4p.arenabg.com%3A1337%2Fannounce&tr=udp%3A%2F%2Ftracker.cyberia.is%3A6969%2Fannounce&tr=udp%3A%2F%2Fbt1.archive.org%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.torrent.eu.org%3A451%2Fannounce&tr=udp%3A%2F%2Ftracker.bittor.pw%3A1337%2Fannounce&tr=udp%3A%2F%2Fopen.stealth.si%3A80%2Fannounce&tr=udp%3A%2F%2Ftracker.tiny-vps.com%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.swateam.org.uk%3A2710%2Fannounce&tr=udp%3A%2F%2Ftracker.dler.org%3A6969%2Fannounce&tr=udp%3A%2F%2Fexplodie.org%3A6969%2Fannounce&tr=udp%3A%2F%2Fexodus.desync.com%3A6969%2Fannounce&tr=udp%3A%2F%2Fopen.demonii.com%3A1337%2Fannounce&tr=udp%3A%2F%2Ftracker.ololosh.space%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.dump.cl%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker-udp.gbitt.info%3A80%2Fannounce&tr=udp%3A%2F%2Fretracker01-msk-virt.corbina.net%3A80%2Fannounce&tr=udp%3A%2F%2Fopen.free-tracker.ga%3A6969%2Fannounce&tr=udp%3A%2F%2Fns-1.x-fins.com%3A6969%2Fannounce&tr=udp%3A%2F%2Fleet-tracker.moe%3A1337%2Fannounce&tr=udp%3A%2F%2Ftracker.leechers-paradise.org%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.open-internet.nl%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.pirateparty.gr%3A6969%2Fannounce&tr=udp%3A%2F%2Fdenis.stalker.upeer.me%3A6969%2Fannounce"

# Create the dedicated download folder directly inside your /tmp directory
local_download_path = '/tmp/downloads'
os.makedirs(local_download_path, exist_ok=True)

# Map target path to the isolated /tmp storage partition
params = {
    'save_path': local_download_path,
    'storage_mode': lt.storage_mode_t.storage_mode_sparse
}

# 2. Add the tracking metadata hook to the session
handle = lt.add_magnet_uri(ses, magnet_link, params)
print("Connecting to the network swarm... Fetching torrent metadata structure...")

while not handle.has_metadata():
    time.sleep(1)
print("\n✅ Metadata retrieved successfully! Configuring local destination...")

# Force sequential download layout configuration
handle.set_flags(lt.torrent_flags.sequential_download)

print(f"Starting tracking monitor. Downloading blocks exclusively onto local /tmp disk...")
while not handle.status().is_seeding:
    s = handle.status()
    
    mb_down = s.download_rate / (1024 * 1024)
    progress_pct = s.progress * 100
    
    print(f"Progress: {progress_pct:.2f}% | Speed: {mb_down:.2f} MB/s | Peers: {s.num_peers}")
    
    # Simple real-time disk analysis tracker for monitoring /tmp limits
    total, used, free = shutil.disk_usage(local_download_path)
    free_gb = free / (1024**3)
    print(f"Available space on /tmp disk: {free_gb:.2f} GB")
    
    time.sleep(10)

print(f"🎉 Complete dataset package pulled down successfully and stored at: {local_download_path}")
