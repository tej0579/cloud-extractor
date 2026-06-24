import sys
sys.path.append('/usr/lib/python3/dist-packages')

import os
import time
import shutil
import subprocess
import re
import requests
from fastapi import FastAPI, BackgroundTasks, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import libtorrent as lt

app = FastAPI()

# 1. Broad global CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. FORCE CUSTOM INJECTION MIDDLEWARE FOR NGROK AND CORS BYPASS
@app.middleware("http")
async def add_custom_headers(request: Request, call_next):
    if request.method == "OPTIONS":
        response = JSONResponse(content="OK")
    else:
        response = await call_next(request)
        
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response

# Global tracking flags
is_pipeline_active = False

engine_status = {
    "status": "Sleeping",
    "name": "None",
    "progress": "0.00",
    "speed": "0.00",
    "peers": 0,
    "disk_free": "0.00",
    "upload_progress": "0",
    "upload_speed": "0 B/s",
    "upload_eta": "-"
}

def download_and_push_worker(magnet_link: str):
    global engine_status, is_pipeline_active
    
    try:
        engine_status["status"] = "Connecting to Swarm Network..."
        
        ses = lt.session()
        ses.listen_on(6881, 6891)
        
        local_path = '/tmp/downloads'
        os.makedirs(local_path, exist_ok=True)
        
        params = {'save_path': local_path, 'storage_mode': lt.storage_mode_t.storage_mode_sparse}
        handle = lt.add_magnet_uri(ses, magnet_link, params)
        
        while not handle.has_metadata():
            time.sleep(1)
            
        handle.set_flags(lt.torrent_flags.sequential_download)
        torrent_info = handle.get_torrent_info()
        engine_status["name"] = torrent_info.name()
        engine_status["status"] = "Downloading on Cloud Instance..."
        
        while not handle.status().is_seeding:
            s = handle.status()
            engine_status["speed"] = f"{s.download_rate / (1024 * 1024):.2f}"
            engine_status["progress"] = f"{s.progress * 100:.2f}"
            engine_status["peers"] = s.num_peers
            
            _, _, free = shutil.disk_usage(local_path)
            engine_status["disk_free"] = f"{free / (1024**3):.2f}"
            time.sleep(2)
            
        engine_status["status"] = "Cloud download done! Transferring to Google Drive..."
        engine_status["speed"] = "0.00"
        engine_status["progress"] = "100.00"
        
        target_folder = engine_status["name"]
        source_dir = f"/tmp/downloads/{target_folder}"
        dest_dir = f"mygdrive:CodespaceDownloads/{target_folder}"
        
        # 🔥 UPGRADED CONFIGURATION BLOCK: Added 8 parallel multi-thread lanes for maximum network velocity
        rclone_cmd = [
            "rclone", "move", source_dir, dest_dir, 
            "--transfers", "4", 
            "--multi-thread-streams", "8", 
            "-P", 
            "--stats", "1s", 
            "--use-mmap"
        ]
        
        process = subprocess.Popen(
            rclone_cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            bufsize=1
        )
        
        progress_regex = re.compile(r"Transferred:\s+.*?\s+/\s+.*?,\s*(\d+)%")
        speed_regex = re.compile(r"Transferred:\s+.*?,\s*[\d.]+\s*[\w/]+,\s*([0-9.]+\s*[\w/]+)")
        eta_regex = re.compile(r"ETA\s+([\w\d\s:]+)")

        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
                
            if line:
                print(f"RCLONE OUT: {line.strip()}", flush=True)
                
                prog_match = progress_regex.search(line)
                if prog_match:
                    engine_status["upload_progress"] = prog_match.group(1)
                
                speed_match = speed_regex.search(line)
                if speed_match:
                    engine_status["upload_speed"] = speed_match.group(1)
                
                eta_match = eta_regex.search(line)
                if eta_match:
                    engine_status["upload_eta"] = eta_match.group(1)

        process.wait()
        exit_code = process.returncode
        
    except Exception as e:
        print(f"Subprocess wrapper failed: {str(e)}")
        exit_code = -1
    
    if exit_code == 0:
        engine_status["status"] = "Success! Content securely saved in Google Drive."
        engine_status["upload_progress"] = "100"
        engine_status["upload_speed"] = "0 B/s"
        engine_status["upload_eta"] = "0s"
        print("Upload finished perfectly. UI synchronization window open.")
        
        time.sleep(30)
        is_pipeline_active = False
        sys.exit(0)
    else:
        engine_status["status"] = "❌ Rclone transfer execution failure."
        is_pipeline_active = False
        print("Upload failed. Keeping instance online for log troubleshooting.")
        
    # 🔑 FIXED: Reads the token securely from the environment context instead of hardcoding it!
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  
    
    if not GITHUB_TOKEN:
        print("⚠️ Warning: GITHUB_TOKEN environment variable is not set.")
    
    # Smart URL Extractor
    full_url = "https://effective-space-funicular-5v7rrpv7w6pf4v7v.github.dev/"
    CODESPACE_NAME = full_url.replace("https://", "").split(".")[0]
    
    shutdown_url = f"https://api.github.com/user/codespaces/{CODESPACE_NAME}/stop"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    time.sleep(10)
    is_pipeline_active = False
    requests.post(shutdown_url, headers=headers)

@app.post("/api/v1/enqueue")
def enqueue_link(background_tasks: BackgroundTasks, magnet_link: str = Form(...)):
    global is_pipeline_active
    if is_pipeline_active:
        return {"status": "ignored", "message": "Pipeline busy."}
        
    is_pipeline_active = True
    background_tasks.add_task(download_and_push_worker, magnet_link)
    return {"message": "Pipeline triggered successfully on cloud worker."}

@app.get("/api/v1/status")
def get_engine_status():
    return engine_status
