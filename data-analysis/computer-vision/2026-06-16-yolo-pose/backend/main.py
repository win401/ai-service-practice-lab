from __future__ import annotations

import base64
import io
import math
from collections import Counter
from typing import Any

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO

app = FastAPI(title="YOLO Pose API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:3002", "http://127.0.0.1:3002",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 모델 ──────────────────────────────────────────────────────────────────────

_models: dict[str, YOLO] = {}

def get_model(name: str) -> YOLO:
    if name not in _models:
        _models[name] = YOLO(name)
    return _models[name]

# ── 키포인트 설정 ─────────────────────────────────────────────────────────────

KP_NAMES = [
    "코","왼눈","오른눈","왼귀","오른귀",
    "왼어깨","오른어깨","왼팔꿈치","오른팔꿈치",
    "왼손목","오른손목","왼엉덩이","오른엉덩이",
    "왼무릎","오른무릎","왼발목","오른발목",
]

SKELETON = [
    (0,1),(0,2),(1,3),(2,4),
    (5,6),
    (5,7),(7,9),
    (6,8),(8,10),
    (5,11),(11,12),(6,12),
    (11,13),(13,15),
    (12,14),(14,16),
]

_FACE   = (255,220, 50)
_CENTER = ( 80,220,130)
_LEFT   = ( 80,160,255)
_RIGHT  = (255,100, 80)

PART_COLORS = [
    _FACE,_FACE,_FACE,_FACE,
    _CENTER,
    _LEFT,_LEFT,
    _RIGHT,_RIGHT,
    _LEFT,_CENTER,_RIGHT,
    _LEFT,_LEFT,
    _RIGHT,_RIGHT,
]

# ── 객체 탐지 색상 ────────────────────────────────────────────────────────────

CLASS_GROUPS: dict[str, set[str] | None] = {
    "사람":    {"person"},
    "동물":    {"cat","dog","bird","sheep","cow","horse","elephant","bear","zebra","giraffe"},
    "차량":    {"bicycle","car","motorcycle","airplane","bus","train","truck","boat"},
    "전자기기":{"cell phone","laptop","mouse","remote","keyboard","tv"},
    "음식":    {"banana","apple","sandwich","orange","broccoli","carrot","hot dog","pizza","donut","cake"},
}

BOX_COLORS: dict[str, tuple[int,int,int]] = {
    "사람":    ( 32,180, 96),
    "동물":    ( 42,130,218),
    "차량":    (245,156, 35),
    "전자기기":(  90, 90, 90),
    "음식":    (190,130, 40),
    "기타":    ( 70,120,230),
}

SEG_ALPHA = 0.40

# ── 폰트 ──────────────────────────────────────────────────────────────────────

def _load_font(size: int = 18) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
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

POSE_COLORS = {
    "서있는 자세":(32,180,96),
    "앉은 자세":  (245,156,35),
    "누운 자세":  (42,130,218),
    "만세 자세":  (147,92,224),
    "알 수 없음": (120,120,120),
}

# ── 자세 분류 ─────────────────────────────────────────────────────────────────

def _angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    ba, bc = a-b, c-b
    cos = np.dot(ba,bc)/(np.linalg.norm(ba)*np.linalg.norm(bc)+1e-6)
    return math.degrees(math.acos(np.clip(cos,-1,1)))

def classify_pose(kps: np.ndarray, confs: np.ndarray, thr: float=0.3) -> tuple[str,float,str]:
    def v(i): return confs[i] >= thr
    def pt(i): return kps[i]

    if not (v(5) and v(6)):
        return "알 수 없음", 0.0, "어깨 키포인트 미감지"

    if v(11) and v(12):
        sm = (pt(5)+pt(6))/2
        hm = (pt(11)+pt(12))/2
        body_angle = math.degrees(math.atan2(abs(sm[1]-hm[1]), abs(sm[0]-hm[0])+1e-6))
        if body_angle < 30:
            return "누운 자세", round(1.0-body_angle/30,2), f"몸통 기울기 {body_angle:.1f}°"

    if v(11) and v(12) and v(13) and v(14) and v(15) and v(16):
        avg = (_angle(pt(11),pt(13),pt(15))+_angle(pt(12),pt(14),pt(16)))/2
        if avg < 120:
            return "앉은 자세", round((120-avg)/120,2), f"무릎 평균 각도 {avg:.1f}°"

        # 무릎은 펴있지만 골반이 발목보다 현저히 높고 몸통이 기울어진 경우 → 걸터앉은 자세
        if v(15) and v(16):
            ankle_y  = (pt(15)[1] + pt(16)[1]) / 2
            hip_y    = (pt(11)[1] + pt(12)[1]) / 2
            height   = ankle_y - hip_y
            sm       = (pt(5) + pt(6)) / 2
            hm       = (pt(11) + pt(12)) / 2
            body_ang = math.degrees(math.atan2(abs(sm[1]-hm[1]), abs(sm[0]-hm[0])+1e-6))
            body_h   = abs(pt(0)[1] - ankle_y) + 1e-6
            ratio    = height / body_h
            print(f"[DEBUG] body_ang={body_ang:.1f}° ratio={ratio:.2f} height={height:.1f} body_h={body_h:.1f} knee_avg={avg:.1f}°")
            # body_ang > 88° + knee > 150° 는 진짜 서있는 자세
            if ratio < 0.65 and body_ang >= 30 and not (body_ang > 88 and avg > 150):
                conf = round(0.5 + (75 - body_ang) / 100, 2)
                return "앉은 자세", conf, f"몸통 기울기 {body_ang:.1f}° + 골반-발목 비율 {ratio:.2f} → 걸터앉은 자세"

        if v(9) and v(10) and pt(9)[1]<pt(5)[1] and pt(10)[1]<pt(6)[1]:
            return "만세 자세", 0.9, "양 손목이 어깨보다 위"
        return "서있는 자세", round(min((avg-120)/60,1.0),2), f"무릎 평균 각도 {avg:.1f}°"

    if v(9) and v(10) and pt(9)[1]<pt(5)[1] and pt(10)[1]<pt(6)[1]:
        return "만세 자세", 0.85, "양 손목이 어깨보다 위"
    return "서있는 자세", 0.6, "하체 키포인트 미감지 — 상체 기준 추정"

# ── 그리기 헬퍼 ───────────────────────────────────────────────────────────────

def _find_group(cls: str) -> str:
    for g, members in CLASS_GROUPS.items():
        if members and cls in members:
            return g
    return "기타"

def _draw_label(img: np.ndarray, x1:int, y1:int, text:str, color:tuple) -> None:
    pil = Image.fromarray(img)
    draw = ImageDraw.Draw(pil)
    l,t,r,b = draw.textbbox((0,0), text, font=LABEL_FONT)
    top = max(y1-( b-t)-10, 0)
    draw.rectangle((x1, top, x1+(r-l)+12, top+(b-t)+8), fill=color)
    draw.text((x1+6, top+4), text, font=LABEL_FONT, fill=(255,255,255))
    img[:] = np.array(pil)

def _draw_skeleton(img: np.ndarray, kps: np.ndarray, confs: np.ndarray,
                   pose:str, pose_conf:float, person_id:int,
                   box: tuple[int,int,int,int] | None = None, thr:float=0.3) -> None:
    for i,(a,b) in enumerate(SKELETON):
        if confs[a]>=thr and confs[b]>=thr:
            cv2.line(img,(int(kps[a][0]),int(kps[a][1])),(int(kps[b][0]),int(kps[b][1])),
                     PART_COLORS[i],3,cv2.LINE_AA)
    for idx,(x,y) in enumerate(kps):
        if confs[idx]>=thr:
            cv2.circle(img,(int(x),int(y)),5,(255,255,255),-1,cv2.LINE_AA)
            cv2.circle(img,(int(x),int(y)),5,(50,50,50),1,cv2.LINE_AA)

    color = POSE_COLORS.get(pose, (120, 120, 120))
    label = f"#{person_id} {pose}  {int(pose_conf*100)}%"
    pil = Image.fromarray(img)
    draw = ImageDraw.Draw(pil)
    l, t, r, b = draw.textbbox((0, 0), label, font=LABEL_FONT)

    if box:
        # 탐지 박스 상단에 라벨 고정
        bx1, by1, bx2, by2 = box
        cv2.rectangle(img, (bx1, by1), (bx2, by2), color, 2)
        lx, ly = bx1, max(by1 - (b - t) - 8, 0)
    else:
        visible = [(int(kps[i][0]), int(kps[i][1])) for i in range(17) if confs[i] >= thr]
        if not visible:
            return
        lx = max(min(v[0] for v in visible) - (r - l) // 2, 4)
        ly = max(min(v[1] for v in visible) - (b - t) - 12, 4)

    draw.rectangle((lx, ly, lx + (r - l) + 12, ly + (b - t) + 8), fill=color)
    draw.text((lx + 6, ly + 4), label, font=LABEL_FONT, fill=(255, 255, 255))
    img[:] = np.array(pil)

def _draw_seg_mask(img: np.ndarray, mask: np.ndarray, color: tuple) -> None:
    c = np.array(color, dtype=np.float32)
    if mask.shape[:2] != img.shape[:2]:
        mask = cv2.resize(mask, (img.shape[1], img.shape[0]))
    m = mask > 0.5
    if not np.any(m):
        return
    f = img.astype(np.float32)
    f[m] = f[m]*(1-SEG_ALPHA) + c*SEG_ALPHA
    img[:] = f.astype(np.uint8)

def _to_b64(img: np.ndarray) -> str:
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="JPEG", quality=92)
    return base64.b64encode(buf.getvalue()).decode()

# ── API ───────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"ok": True}


@app.post("/analyze")
async def analyze(
    image: UploadFile = File(...),
    confidence: float  = Form(0.5),
    use_detect:  bool  = Form(True),
    use_segment: bool  = Form(False),
    use_pose:    bool  = Form(True),
):
    raw = await image.read()
    pil = Image.open(io.BytesIO(raw)).convert("RGB")
    original_rgb = np.array(pil)
    annotated = original_rgb.copy()

    detect_rows: list[dict[str, Any]] = []
    people:      list[dict[str, Any]] = []

    # ── 세그멘테이션 (가장 먼저 — 배경처럼 깔림) ──
    if use_segment:
        seg_model = get_model("yolov8n-seg.pt")
        seg_res = seg_model.predict(source=original_rgb, conf=confidence, verbose=False)[0]
        if seg_res.masks is not None and seg_res.boxes is not None:
            masks  = seg_res.masks.data.cpu().numpy()
            labels = seg_res.boxes.cls.cpu().numpy()
            for idx, (mask, lbl) in enumerate(zip(masks, labels)):
                cls   = seg_model.names[int(lbl)]
                group = _find_group(cls)
                color = BOX_COLORS.get(group, BOX_COLORS["기타"])
                _draw_seg_mask(annotated, mask, color)

    # ── 객체 탐지 ──
    if use_detect:
        det_model = get_model("yolov8n.pt")
        det_res = det_model.predict(source=original_rgb, conf=confidence, verbose=False)[0]
        if det_res.boxes is not None:
            boxes  = det_res.boxes.xyxy.cpu().numpy()
            labels = det_res.boxes.cls.cpu().numpy()
            confs  = det_res.boxes.conf.cpu().numpy()
            person_counter = 0
            for box, lbl, c in zip(boxes, labels, confs):
                cls   = det_model.names[int(lbl)]
                group = _find_group(cls)
                color = BOX_COLORS.get(group, BOX_COLORS["기타"])
                x1,y1,x2,y2 = [int(v) for v in box]
                cv2.rectangle(annotated,(x1,y1),(x2,y2),color,2)
                if cls == "person":
                    person_counter += 1
                    if use_pose:
                        continue  # 자세분석 ON이면 person 라벨은 자세 레이어에서 표시
                    display_cls = f"person{person_counter}"
                else:
                    display_cls = cls
                _draw_label(annotated, x1, y1, f"{display_cls} {c:.2f}", color)
                detect_rows.append({
                    "class": cls,
                    "group": group,
                    "confidence": round(float(c),2),
                    "box": f"{x1},{y1},{x2},{y2}",
                })

    # ── 자세 분석 ──
    if use_pose:
        pose_model = get_model("yolov8n-pose.pt")
        pose_res = pose_model.predict(source=original_rgb, conf=confidence, verbose=False)[0]
        if pose_res.keypoints is not None and len(pose_res.keypoints) > 0:
            kps_all  = pose_res.keypoints.xy.cpu().numpy()
            conf_all = pose_res.keypoints.conf.cpu().numpy()
            det_conf = pose_res.boxes.conf.cpu().numpy() if pose_res.boxes is not None else [1.0]*len(kps_all)
            boxes_all = pose_res.boxes.xyxy.cpu().numpy() if pose_res.boxes is not None else [None]*len(kps_all)

            # chair 박스 수집: 탐지 결과 + 낮은 confidence(0.2)로 재탐지 병행
            chair_boxes: list[tuple[int,int,int,int]] = []
            if use_detect:
                for r in detect_rows:
                    if r["class"] == "chair":
                        x1,y1,x2,y2 = [int(float(v)) for v in r["box"].split(",")]
                        chair_boxes.append((x1,y1,x2,y2))
            # 탐지 결과에 chair 없으면 낮은 confidence로 재탐지
            if not chair_boxes:
                det_model = get_model("yolov8n.pt")
                low_res = det_model.predict(source=original_rgb, conf=0.2, verbose=False)[0]
                if low_res.boxes is not None:
                    for box, lbl in zip(low_res.boxes.xyxy.cpu().numpy(), low_res.boxes.cls.cpu().numpy()):
                        if det_model.names[int(lbl)] == "chair":
                            x1,y1,x2,y2 = [int(float(v)) for v in box]
                            chair_boxes.append((x1,y1,x2,y2))

            for idx,(kps,confs,dc,pbox) in enumerate(zip(kps_all,conf_all,det_conf,boxes_all)):
                pose,pose_conf,reason = classify_pose(kps,confs)

                # 골반 중심이 chair 박스 안에 있으면 앉은 자세로 보정
                if chair_boxes and confs[11] >= 0.3 and confs[12] >= 0.3:
                    hx = int((kps[11][0] + kps[12][0]) / 2)
                    hy = int((kps[11][1] + kps[12][1]) / 2)
                    print(f"[DEBUG] hip center: {hx},{hy}  chair_boxes: {chair_boxes}")
                    for cx1,cy1,cx2,cy2 in chair_boxes:
                        pad = int((cy2 - cy1) * 0.4)  # 의자 높이의 40% 위까지 허용
                        if cx1 <= hx <= cx2 and (cy1 - pad) <= hy <= cy2:
                            pose      = "앉은 자세"
                            pose_conf = round(min(pose_conf + 0.2, 0.99), 2)
                            reason    = reason + " → 골반이 의자 위에 위치해 앉은 자세로 보정"
                            break

                pb = tuple(int(v) for v in pbox) if pbox is not None else None
                _draw_skeleton(annotated, kps, confs, pose, pose_conf, idx + 1, box=pb)
                people.append({
                    "id":               idx+1,
                    "pose":             pose,
                    "det_confidence":   round(float(dc),2),
                    "pose_confidence":  pose_conf,
                    "reason":           reason,
                    "visible_keypoints":int(np.sum(confs>=0.3)),
                    "keypoints": [
                        {"name":KP_NAMES[i],"x":round(float(kps[i][0])),"y":round(float(kps[i][1])),"conf":round(float(confs[i]),2)}
                        for i in range(17) if confs[i]>=0.3
                    ],
                })

    # 요약
    pose_summary = Counter(p["pose"] for p in people)
    det_summary  = Counter(r["group"] for r in detect_rows)

    return {
        "original":    _to_b64(original_rgb),
        "annotated":   _to_b64(annotated),
        "people":      people,
        "person_count":len(people),
        "detect_rows": detect_rows,
        "detect_count":len(detect_rows),
        "pose_summary":dict(pose_summary),
        "det_summary": dict(det_summary),
    }
