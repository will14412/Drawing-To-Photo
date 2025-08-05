from pathlib import Path
from typing import Optional

from fastapi import (
    FastAPI, Request, UploadFile, Depends,
    Response, HTTPException
)
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel, Session, select, create_engine
from datetime import datetime
from app.models import User
from app.auth   import (
    get_current_user, hash_pw, verify_pw, create_token
)
from app.ai_client import turn_sketch_into_photo

# ── FastAPI / Jinja setup ─────────────────────────────────
BASE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE / "templates"))
templates.env.globals["now"] = datetime.utcnow
app = FastAPI(title="Draw → Photo")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

# ── DB setup (SQLite for now) ─────────────────────────────
engine = create_engine("sqlite:///app.db", echo=False)
SQLModel.metadata.create_all(engine)

# ── context helper ────────────────────────────────────────
def ctx(request: Request, **extra):
    return {"request": request, **extra}

# ── routes ────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def home(request: Request, user: Optional[int] = Depends(get_current_user)):
    return templates.TemplateResponse("index.html", ctx(request, user=user))

# ── auth: register ────────────────────────────────────────
@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("auth/register.html", ctx(request))

@app.post("/register")
async def register(request: Request):
    form = await request.form()
    email = form.get("email") or ""
    pw    = form.get("password") or ""
    cpw   = form.get("confirm_password") or ""

    if pw != cpw:
        return templates.TemplateResponse(
            "auth/register.html",
            ctx(request, messages=[{"category": "error", "text": "Passwords do not match"}]),
            status_code=400,
        )

    with Session(engine) as db:
        if db.exec(select(User).where(User.email == email)).first():
            return templates.TemplateResponse(
                "auth/register.html",
                ctx(request, messages=[{"category": "error", "text": "Email already in use"}]),
                status_code=400,
            )
        u = User(email=email, hashed_password=hash_pw(pw))
        db.add(u); db.commit(); db.refresh(u)

    token = create_token(u.id)
    resp = Response(status_code=302, headers={"Location": "/generate"})
    resp.set_cookie("token", token, httponly=True, max_age=60*60*24*7)
    return resp

# ── auth: login ───────────────────────────────────────────
@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("auth/login.html", ctx(request))

@app.post("/login")
async def login(request: Request):
    form  = await request.form()
    email = form.get("email") or ""
    pw    = form.get("password") or ""

    with Session(engine) as db:
        user = db.exec(select(User).where(User.email == email)).first()

    if not user or not verify_pw(pw, user.hashed_password):
        return templates.TemplateResponse(
            "auth/login.html",
            ctx(request, messages=[{"category": "error", "text": "Invalid email or password"}]),
            status_code=400,
        )

    token = create_token(user.id)
    resp = Response(status_code=302, headers={"Location": "/generate"})
    resp.set_cookie("token", token, httponly=True, max_age=60*60*24*7)
    return resp

# ── image generation ─────────────────────────────────────
@app.get("/generate", response_class=HTMLResponse)
def generate_form(request: Request, user: Optional[int] = Depends(get_current_user)):
    if not user:
        return RedirectResponse("/login")
    return templates.TemplateResponse("generate.html", ctx(request, user=user))


@app.post("/generate")
async def generate(
    file: UploadFile,
    user: Optional[int] = Depends(get_current_user)
):
    if not user:
        raise HTTPException(401, "Login required")
    if file.content_type not in ("image/png", "image/jpeg"):
        raise HTTPException(400, "PNG/JPEG only")

    photo = await turn_sketch_into_photo(await file.read())
    return StreamingResponse(
        iter([photo]),
        media_type="image/png",
        headers={"Content-Disposition": 'inline; filename="result.png"'},
    )

# ── gallery ───────────────────────────────────────────────
@app.get("/gallery", response_class=HTMLResponse)
def gallery(request: Request, user: Optional[int] = Depends(get_current_user)):
    return templates.TemplateResponse("gallery.html", ctx(request, user=user))

# ── auth: logout ──────────────────────────────────────────
@app.post("/logout")
def logout():
    resp = Response(status_code=302, headers={"Location": "/"})
    resp.delete_cookie("token")
    return resp

# ── custom 404 page ───────────────────────────────────────
@app.exception_handler(404)
def not_found(request: Request, exc):
    return templates.TemplateResponse("404.html", ctx(request), status_code=404)
