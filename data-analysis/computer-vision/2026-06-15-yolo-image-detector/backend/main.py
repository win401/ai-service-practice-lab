from __future__ import annotations

import base64
import io
from collections import Counter
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False

try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except Exception:
    DEEPFACE_AVAILABLE = False

EMOTION_EMOJI = {
    "happy": "😊", "sad": "😢", "angry": "😠",
    "fear": "😨", "surprise": "😲", "disgust": "🤢", "neutral": "😐",
}
EMOTION_KO = {
    "happy": "행복", "sad": "슬픔", "angry": "화남",
    "fear": "두려움", "surprise": "놀람", "disgust": "혐오", "neutral": "무표정",
}

app = FastAPI(title="YOLO Face Detector API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000",
                   "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 모델 ──────────────────────────────────────────────────────────────────────

MODEL_DIR = Path(__file__).parent.parent / "app"
_models: dict[str, YOLO] = {}

def get_model(mode: str) -> YOLO:
    path = str(MODEL_DIR / ("yolov8n-seg.pt" if mode == "seg" else "yolov8n.pt"))
    if path not in _models:
        _models[path] = YOLO(path)
    return _models[path]

# ── 얼굴 DB ───────────────────────────────────────────────────────────────────

known_encodings: list[np.ndarray] = []
known_names: list[str] = []

# ── 설정 ──────────────────────────────────────────────────────────────────────

CLASS_GROUPS: dict[str, set[str] | None] = {
    "전체": None,
    "사람": {"person"},
    "동물": {"cat", "dog", "bird", "sheep", "cow", "horse", "elephant", "bear", "zebra", "giraffe"},
    "차량": {"bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat"},
    "교통 신호": {"traffic light", "stop sign", "parking meter", "fire hydrant"},
    "스포츠": {"sports ball", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket"},
    "소지품": {"backpack", "umbrella", "handbag", "tie", "suitcase"},
    "전자기기": {"cell phone", "laptop", "mouse", "remote", "keyboard", "tv"},
    "음식": {"banana", "apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake"},
}

BOX_COLORS: dict[str, tuple[int, int, int]] = {
    "사람": (32, 180, 96),
    "동물": (42, 130, 218),
    "차량": (245, 156, 35),
    "교통 신호": (215, 68, 68),
    "스포츠": (147, 92, 224),
    "소지품": (32, 156, 166),
    "전자기기": (90, 90, 90),
    "음식": (190, 130, 40),
    "기타": (70, 120, 230),
}

FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def _load_font(size: int = 22) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()

LABEL_FONT = _load_font()


def _find_group(cls: str) -> str:
    for name, members in CLASS_GROUPS.items():
        if members and cls in members:
            return name
    return "기타"


def _draw_box(img: np.ndarray, box: list[int], label: str, conf: float, group: str) -> None:
    x1, y1, x2, y2 = box
    color = BOX_COLORS.get(group, BOX_COLORS["기타"])
    cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)

    caption = f"{label} {conf:.2f}" if conf < 1.0 else label
    pil = Image.fromarray(img)
    draw = ImageDraw.Draw(pil)
    l, t, r, b = draw.textbbox((0, 0), caption, font=LABEL_FONT)
    tw, th = r - l, b - t
    top = max(y1 - th - 12, 0)
    draw.rectangle((x1, top, x1 + tw + 12, top + th + 10), fill=color)
    draw.text((x1 + 6, top + 4), caption, font=LABEL_FONT, fill=(255, 255, 255))
    img[:] = np.array(pil)


def _draw_mask(img: np.ndarray, mask: np.ndarray, group: str, alpha: float = 0.42) -> None:
    color = np.array(BOX_COLORS.get(group, BOX_COLORS["기타"]), dtype=np.float32)
    if mask.shape[:2] != img.shape[:2]:
        mask = cv2.resize(mask, (img.shape[1], img.shape[0]))
    m = mask > 0.5
    if not np.any(m):
        return
    f = img.astype(np.float32)
    f[m] = f[m] * (1 - alpha) + color * alpha
    img[:] = f.astype(np.uint8)


def _analyze_emotion(img_rgb: np.ndarray, top: int, right: int, bottom: int, left: int) -> str | None:
    """얼굴 영역을 잘라 표정을 분석합니다."""
    if not DEEPFACE_AVAILABLE:
        return None
    try:
        face_crop = img_rgb[top:bottom, left:right]
        if face_crop.size == 0:
            return None
        result = DeepFace.analyze(face_crop, actions=["emotion"], enforce_detection=False, silent=True)
        emotion = result[0]["dominant_emotion"]
        emoji = EMOTION_EMOJI.get(emotion, "")
        ko = EMOTION_KO.get(emotion, emotion)
        return f"{emoji} {ko}"
    except Exception:
        return None


def _match_face(enc: np.ndarray, tolerance: float) -> str:
    if not known_encodings:
        return "Unknown"
    dists = face_recognition.face_distance(known_encodings, enc)
    idx = int(np.argmin(dists))
    return known_names[idx] if dists[idx] <= tolerance else "Unknown"


def _pil_to_b64(img: np.ndarray) -> str:
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode()


# ── API ───────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "ok": True,
        "face_recognition": FACE_RECOGNITION_AVAILABLE,
        "deepface": DEEPFACE_AVAILABLE,
        "registered_faces": known_names,
    }


@app.get("/faces")
def list_faces():
    from collections import Counter
    counts = Counter(known_names)
    return {"names": list(counts.keys()), "counts": dict(counts)}


@app.post("/faces/register")
async def register_face(image: UploadFile = File(...), name: str = Form(...)):
    if not FACE_RECOGNITION_AVAILABLE:
        raise HTTPException(status_code=400, detail="face_recognition 미설치")

    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="이름을 입력해주세요.")

    raw = await image.read()
    pil = Image.open(io.BytesIO(raw)).convert("RGB")
    img_rgb = np.array(pil)
    locs = face_recognition.face_locations(img_rgb)
    encs = face_recognition.face_encodings(img_rgb, locs, num_jitters=5)

    if not encs:
        raise HTTPException(status_code=422, detail="얼굴을 감지하지 못했습니다. 정면 사진을 사용해주세요.")

    known_encodings.append(encs[0])
    known_names.append(name)
    # 같은 이름으로 등록된 총 장수
    count = known_names.count(name)
    return {"registered": name, "count": count, "total": len(known_names), "names": list(dict.fromkeys(known_names))}


@app.delete("/faces/{name}")
def delete_face(name: str):
    indices = [i for i, n in enumerate(known_names) if n == name]
    if not indices:
        raise HTTPException(status_code=404, detail=f"'{name}' 을(를) 찾을 수 없습니다.")
    for i in reversed(indices):
        known_encodings.pop(i)
        known_names.pop(i)
    return {"deleted": name, "names": known_names}


@app.post("/detect")
async def detect(
    image: UploadFile = File(...),
    mode: str = Form("box"),
    confidence: float = Form(0.25),
    group: str = Form("전체"),
    keyword: str = Form(""),
    show_boxes: bool = Form(True),
    show_masks: bool = Form(True),
    show_faces: bool = Form(False),
    use_recognition: bool = Form(False),
    tolerance: float = Form(0.6),
):
    raw = await image.read()
    pil = Image.open(io.BytesIO(raw)).convert("RGB")
    original_rgb = np.array(pil)
    annotated = original_rgb.copy()

    model = get_model(mode)
    results = model.predict(source=original_rgb, conf=confidence, verbose=False)
    result = results[0]

    rows: list[dict[str, Any]] = []
    total_raw = 0
    masks = result.masks.data.cpu().numpy() if result.masks is not None else None

    if result.boxes is not None:
        boxes = result.boxes.xyxy.cpu().numpy()
        labels = result.boxes.cls.cpu().numpy()
        confs = result.boxes.conf.cpu().numpy()

        for idx, (box, lbl, conf_val) in enumerate(zip(boxes, labels, confs)):
            total_raw += 1
            cls_name = model.names[int(lbl)]

            grp_members = CLASS_GROUPS.get(group)
            if grp_members is not None and cls_name not in grp_members:
                continue
            kw = keyword.strip().lower()
            if kw and kw not in cls_name.lower():
                continue

            grp = _find_group(cls_name)
            x1, y1, x2, y2 = [int(v) for v in box]

            if show_masks and masks is not None and idx < len(masks):
                _draw_mask(annotated, masks[idx], grp)

            rows.append({
                "id": len(rows) + 1,
                "class": cls_name,
                "confidence": round(float(conf_val), 4),
                "group": grp,
                "box": f"{x1}, {y1}, {x2}, {y2}",
            })

            if show_boxes:
                _draw_box(annotated, [x1, y1, x2, y2], cls_name, float(conf_val), grp)

    face_results: list[dict[str, str]] = []
    if show_faces:
        if use_recognition and FACE_RECOGNITION_AVAILABLE:
            locs = face_recognition.face_locations(annotated)
            encs = face_recognition.face_encodings(annotated, locs)
            for (top, right, bottom, left), enc in zip(locs, encs):
                name = _match_face(enc, tolerance)
                emotion = _analyze_emotion(annotated, top, right, bottom, left)
                label = f"{name}  {emotion}" if emotion else name
                face_results.append({"name": name, "emotion": emotion or ""})
                _draw_box(annotated, [left, top, right, bottom], label, 1.0,
                          "사람" if name != "Unknown" else "기타")
        else:
            gray = cv2.cvtColor(annotated, cv2.COLOR_RGB2GRAY)
            faces = FACE_CASCADE.detectMultiScale(gray, 1.1, 5, minSize=(35, 35))
            for i, (x, y, w, h) in enumerate(faces, 1):
                top, right, bottom, left = int(y), int(x + w), int(y + h), int(x)
                emotion = _analyze_emotion(annotated, top, right, bottom, left)
                label = f"face {i}  {emotion}" if emotion else f"face {i}"
                face_results.append({"name": f"face {i}", "emotion": emotion or ""})
                _draw_box(annotated, [left, top, right, bottom], label, 1.0, "기타")

    # 요약
    if not rows:
        summary = "탐지된 객체가 없습니다." if total_raw == 0 else "필터 조건에 맞는 객체가 없습니다."
    else:
        grp_text = ", ".join(f"{n} {c}개" for n, c in Counter(r["group"] for r in rows).most_common())
        summary = f"총 {len(rows)}개 객체 | {grp_text}"

    if face_results:
        known_faces = [f["name"] for f in face_results if f["name"] != "Unknown" and not f["name"].startswith("face ")]
        unknown_count = sum(1 for f in face_results if f["name"] == "Unknown")
        parts = []
        if known_faces:
            parts.append(f"인식: {', '.join(known_faces)}")
        if unknown_count:
            parts.append(f"미인식 {unknown_count}명")
        summary += f" | 얼굴 {len(face_results)}개 ({', '.join(parts)})" if parts else f" | 얼굴 {len(face_results)}개"

    return {
        "original": _pil_to_b64(original_rgb),
        "annotated": _pil_to_b64(annotated),
        "rows": rows,
        "summary": summary,
        "face_count": len(face_results),
        "face_results": face_results,
    }
