import os
import secrets

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

app = FastAPI()
security = HTTPBasic()


@app.get("/")
def home():
    return {"message": "DevOps Status App is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/version")
def version():
    return {"version": "1.0.0"}


def require_login(credentials: HTTPBasicCredentials = Depends(security)):
    user = os.getenv("DASH_USER", "")
    password = os.getenv("DASH_PASS", "")
    ok = (
        bool(user and password)
        and secrets.compare_digest(credentials.username.encode(), user.encode())
        and secrets.compare_digest(credentials.password.encode(), password.encode())
    )
    if not ok:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )


DASHBOARD = """<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>DevOps Dashboard</title>
<style>
body{font-family:system-ui,sans-serif;margin:0;background:#0d1117;color:#e6edf3}
nav{display:flex;gap:8px;padding:12px;background:#161b22}
nav button{background:#21262d;color:#e6edf3;border:0;padding:8px 14px;border-radius:6px;cursor:pointer}
nav button.on{background:#2f81f7}
section{display:none;padding:20px;max-width:760px;margin:auto}
section.on{display:block}
.card{background:#161b22;border-radius:8px;padding:14px;margin-bottom:12px}
.ok{color:#3fb950}.bad{color:#f85149}.warn{color:#d29922}
table{width:100%;border-collapse:collapse}td,th{padding:6px;text-align:left;border-bottom:1px solid #30363d}
</style></head><body>
<nav>
<button data-t="app" class="on">App Health</button>
<button data-t="pipe">Pipeline</button>
<button data-t="rep">Report</button>
</nav>

<section id="app" class="on">
<div class="card">Status: <b id="health">...</b></div>
<div class="card">Version: <b id="version">...</b></div>
<div class="card" id="checked"></div>
</section>

<section id="pipe">
<div class="card"><button id="refresh">Refresh</button></div>
<table><thead><tr><th>Commit</th><th>Result</th><th>Time</th></tr></thead><tbody id="runs"></tbody></table>
</section>

<section id="rep">
<div class="card" id="summary">Loading...</div>
<table><thead><tr><th>Job</th><th>Step</th><th>Result</th><th>Time</th></tr></thead><tbody id="steps"></tbody></table>
</section>

<script>
const API="https://api.github.com/repos/codewroteit/CI-CD-pipeline/actions/runs";
document.querySelectorAll("nav button").forEach(b=>b.onclick=()=>{
  document.querySelectorAll("nav button,section").forEach(e=>e.classList.remove("on"));
  b.classList.add("on");document.getElementById(b.dataset.t).classList.add("on");
});
function setText(id,t,c){const e=document.getElementById(id);e.textContent=t;if(c)e.className=c;}
function color(r){return r==="success"?"ok":r==="failure"?"bad":"warn";}
function row(tbody,cells,colorIndex,cls){
  const tr=document.createElement("tr");
  cells.forEach((t,i)=>{const td=document.createElement("td");td.textContent=t;if(i===colorIndex)td.className=cls;tr.appendChild(td);});
  tbody.appendChild(tr);
}
async function checkApp(){
  try{
    const h=await (await fetch("/health")).json();
    setText("health",h.status,h.status==="healthy"?"ok":"bad");
    const v=await (await fetch("/version")).json();
    setText("version",v.version);
  }catch(e){setText("health","unreachable","bad");}
  setText("checked","Last checked: "+new Date().toLocaleTimeString());
}
async function loadPipeline(){
  const body=document.getElementById("runs");
  try{
    const d=await (await fetch(API+"?per_page=5")).json();
    body.textContent="";
    d.workflow_runs.forEach(r=>{
      const res=r.conclusion||r.status;
      row(body,[r.head_commit.message.split("\\n")[0],res,new Date(r.created_at).toLocaleString()],1,color(r.conclusion));
    });
    loadReport(d.workflow_runs[0]);
  }catch(e){setText("summary","Could not load runs (GitHub rate limit?)");}
}
async function loadReport(run){
  const body=document.getElementById("steps");
  const j=await (await fetch(run.jobs_url)).json();
  body.textContent="";
  let rolled=false;
  j.jobs.forEach(job=>{
    job.steps.forEach(s=>{
      if(s.name.indexOf("Rollback")===0&&s.conclusion==="success")rolled=true;
      const secs=s.completed_at?Math.round((new Date(s.completed_at)-new Date(s.started_at))/1000)+"s":"-";
      row(body,[job.name,s.name,s.conclusion||s.status,secs],2,color(s.conclusion));
    });
  });
  setText("summary","Latest run: "+(run.conclusion||run.status)+" | Rollback triggered: "+(rolled?"yes":"no"));
}
document.getElementById("refresh").onclick=loadPipeline;
checkApp();setInterval(checkApp,5000);loadPipeline();
</script></body></html>"""


@app.get("/dashboard", response_class=HTMLResponse, dependencies=[Depends(require_login)])
def dashboard():
    return DASHBOARD