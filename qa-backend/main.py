import os
import threading
import shutil
import zipfile
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

from database import init_db, get_db, Scan, Bug, Notification
from scanner import QAPlatformScanner

# Initialize DB on Startup
init_db()

app = FastAPI(title="AI-Powered QA SaaS API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Screenshots & Uploaded Static Directories
ROOT_DIR = Path(__file__).parent.parent
SCREENSHOT_PATH = ROOT_DIR / "reports"
SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
app.mount("/reports", StaticFiles(directory=str(SCREENSHOT_PATH)), name="reports")

UPLOAD_PATH = ROOT_DIR / "data" / "uploads"
UPLOAD_PATH.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_PATH)), name="uploads")

# Pydantic Schemas
class ScanRequest(BaseModel):
    url: str

class BugResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    severity: str
    page_url: str = None
    xpath_or_selector: str = None
    screenshot_path: str = None
    root_cause: str = None
    suggested_fix: str = None
    approved: bool

    class Config:
        from_attributes = True

class ScanResponse(BaseModel):
    id: int
    url: str
    status: str
    created_at: datetime
    total_pages: int
    total_bugs: int
    duration_seconds: int

    class Config:
        from_attributes = True

# Background Scan Runner
def run_background_scan(scan_id: int, url: str):
    db = next(get_db())
    try:
        scanner = QAPlatformScanner(db)
        scanner.scan_website(scan_id, url)
    except Exception as e:
        print(f"Scan execution failed for scan {scan_id}: {str(e)}")

# Endpoints
@app.post("/api/scan", response_model=ScanResponse)
def trigger_scan(request: ScanRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # 1. Create PENDING scan record
    scan = Scan(
        url=request.url,
        status="PENDING",
        total_pages=0,
        total_bugs=0,
        duration_seconds=0
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    
    # 2. Spawn background thread
    background_tasks.add_task(run_background_scan, scan.id, request.url)
    
    return scan

@app.post("/api/scan-zip", response_model=ScanResponse)
def trigger_scan_zip(file: UploadFile = File(...), background_tasks: BackgroundTasks = None, db: Session = Depends(get_db)):
    # 1. Create PENDING scan record
    scan = Scan(
        url=file.filename,
        status="PENDING",
        total_pages=0,
        total_bugs=0,
        duration_seconds=0
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    
    # 2. Save ZIP file and extract
    scan_upload_dir = UPLOAD_PATH / f"scan_{scan.id}"
    scan_upload_dir.mkdir(parents=True, exist_ok=True)
    
    zip_filepath = scan_upload_dir / "project.zip"
    with open(zip_filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
            zip_ref.extractall(scan_upload_dir)
    except Exception as e:
        scan.status = "FAILED"
        db.commit()
        raise HTTPException(status_code=400, detail=f"Failed to extract zip file: {str(e)}")
        
    # Check if index.html exists, if not find any HTML file or root
    local_url = f"http://localhost:8000/uploads/scan_{scan.id}/index.html"
    found_html = False
    for p in scan_upload_dir.glob("**/index.html"):
        relative = p.relative_to(UPLOAD_PATH)
        local_url = f"http://localhost:8000/uploads/{relative.as_posix()}"
        found_html = True
        break
        
    if not found_html:
        # Fallback to the first html file found
        for p in scan_upload_dir.glob("**/*.html"):
            relative = p.relative_to(UPLOAD_PATH)
            local_url = f"http://localhost:8000/uploads/{relative.as_posix()}"
            found_html = True
            break
            
    # If still not found, just point to the directory root
    if not found_html:
        relative = scan_upload_dir.relative_to(UPLOAD_PATH)
        local_url = f"http://localhost:8000/uploads/{relative.as_posix()}/"
        
    # Update scan URL to the local URL
    scan.url = local_url
    db.commit()
    
    # 3. Spawn background thread
    background_tasks.add_task(run_background_scan, scan.id, local_url)
    
    return scan

@app.get("/api/scans", response_model=List[ScanResponse])
def get_all_scans(db: Session = Depends(get_db)):
    return db.query(Scan).order_by(Scan.created_at.desc()).all()

@app.get("/api/scan/{scan_id}")
def get_scan_details(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan execution record not found")
        
    bugs = db.query(Bug).filter(Bug.scan_id == scan_id).all()
    
    return {
        "id": scan.id,
        "url": scan.url,
        "status": scan.status,
        "created_at": scan.created_at,
        "total_pages": scan.total_pages,
        "total_bugs": scan.total_bugs,
        "duration_seconds": scan.duration_seconds,
        "bugs": [BugResponse.from_orm(b) for b in bugs]
    }

@app.post("/api/scans/{scan_id}/approve-bug/{bug_id}")
def approve_bug(scan_id: int, bug_id: int, db: Session = Depends(get_db)):
    bug = db.query(Bug).filter(Bug.id == bug_id, Bug.scan_id == scan_id).first()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug record not found")
        
    bug.approved = True
    
    # Simulate Developer Slack & Email Notification Creation
    msg = f"🚨 *CRITICAL BUG APPROVED* on {bug.page_url or '/'}\n*Title*: {bug.title}\n*Description*: {bug.description}\n*Suggested Fix*: {bug.suggested_fix}"
    slack_notif = Notification(
        scan_id=scan_id,
        target_channel="Slack",
        message=msg,
        status="SENT"
    )
    email_notif = Notification(
        scan_id=scan_id,
        target_channel="Email",
        message=msg,
        status="SENT"
    )
    db.add(slack_notif)
    db.add(email_notif)
    db.commit()
    
    return {"status": "success", "message": "Bug approved and developer notifications dispatched"}

@app.get("/api/notifications")
def get_notifications(db: Session = Depends(get_db)):
    notifs = db.query(Notification).order_by(Notification.sent_at.desc()).all()
    return [{
        "id": n.id,
        "scan_id": n.scan_id,
        "target_channel": n.target_channel,
        "message": n.message,
        "status": n.status,
        "sent_at": n.sent_at
    } for n in notifs]

@app.get("/api/analytics")
def get_analytics(db: Session = Depends(get_db)):
    total_scans = db.query(Scan).count()
    total_bugs = db.query(Bug).count()
    approved_bugs = db.query(Bug).filter(Bug.approved == True).count()
    
    # Bug distribution by severity
    critical = db.query(Bug).filter(Bug.severity == "CRITICAL").count()
    high = db.query(Bug).filter(Bug.severity == "HIGH").count()
    medium = db.query(Bug).filter(Bug.severity == "MEDIUM").count()
    low = db.query(Bug).filter(Bug.severity == "LOW").count()
    
    # Bug distribution by category
    ui_bugs = db.query(Bug).filter(Bug.category == "UI").count()
    api_bugs = db.query(Bug).filter(Bug.category == "API").count()
    console_bugs = db.query(Bug).filter(Bug.category == "CONSOLE").count()
    res_bugs = db.query(Bug).filter(Bug.category == "RESOURCE").count()
    perf_bugs = db.query(Bug).filter(Bug.category == "PERFORMANCE").count()
    
    # Get last 10 scans for trends
    scans = db.query(Scan).order_by(Scan.created_at.asc()).all()[-10:]
    trend = []
    for s in scans:
        critical_count = db.query(Bug).filter(Bug.scan_id == s.id, Bug.severity == "CRITICAL").count()
        high_count = db.query(Bug).filter(Bug.scan_id == s.id, Bug.severity == "HIGH").count()
        other_count = db.query(Bug).filter(Bug.scan_id == s.id, Bug.severity.in_(["MEDIUM", "LOW"])).count()
        trend.append({
            "name": f"Scan #{s.id}",
            "Critical": critical_count,
            "High": high_count,
            "Medium/Low": other_count
        })
        
    return {
        "summary": {
            "total_scans": total_scans,
            "total_bugs": total_bugs,
            "approved_bugs": approved_bugs
        },
        "severity": [
            {"name": "Critical", "value": critical},
            {"name": "High", "value": high},
            {"name": "Medium", "value": medium},
            {"name": "Low", "value": low}
        ],
        "category": [
            {"name": "UI Errors", "value": ui_bugs},
            {"name": "API Failures", "value": api_bugs},
            {"name": "Console Errors", "value": console_bugs},
            {"name": "Broken Assets", "value": res_bugs},
            {"name": "Performance", "value": perf_bugs}
        ],
        "trend": trend
    }
