from fastapi import APIRouter
import subprocess, os

router = APIRouter()

def run_ps(script_path: str):
    cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -File "{script_path}"'
    proc = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return {"rc": proc.returncode, "out": proc.stdout, "err": proc.stderr}

@router.post("/block-simple")
def block_simple():
    basedir = os.path.abspath(os.path.join(os.getcwd(), "scripts"))
    kill_script = os.path.join(basedir, "kill_and_rename.ps1")
    hosts_script = os.path.join(basedir, "block_domains_hosts.ps1")
    r1 = run_ps(kill_script) if os.path.exists(kill_script) else {"rc":1,"err":"kill script not found","out":""}
    r2 = run_ps(hosts_script) if os.path.exists(hosts_script) else {"rc":1,"err":"hosts script not found","out":""}
    return {"ok": True, "kill": r1, "hosts": r2}

@router.post("/rollback")
def rollback():
    basedir = os.path.abspath(os.path.join(os.getcwd(), "scripts"))
    rb = os.path.join(basedir, "rollback_distraction_blocker.ps1")
    res = run_ps(rb) if os.path.exists(rb) else {"rc":1,"err":"rollback script not found","out":""}
    return {"ok": True, "rollback": res}