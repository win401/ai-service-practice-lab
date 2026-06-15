from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import cv2
import gradio as gr
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False


MODEL_OPTIONS = {
    "Detection Box": "yolov8n.pt",
    "Segmentation Mask": "yolov8n-seg.pt",
}
models: dict[str, YOLO] = {}


def get_model(model_mode: str) -> YOLO:
    model_name = MODEL_OPTIONS[model_mode]
    if model_name not in models:
        models[model_name] = YOLO(model_name)
    return models[model_name]


CLASS_GROUPS = {
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

BOX_COLORS = {
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


def load_label_font(size: int = 22) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_paths = [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/System/Library/Fonts/Supplemental/NotoSansGothic-Regular.ttf",
    ]
    for font_path in font_paths:
        try:
            return ImageFont.truetype(font_path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


LABEL_FONT = load_label_font()
FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# ── 얼굴 인식 DB (런타임 메모리) ───────────────────────────────────────────────
known_face_encodings: list[np.ndarray] = []
known_face_names: list[str] = []


def register_face(image: Image.Image | None, name: str) -> str:
    """UI에서 업로드한 이미지와 이름으로 얼굴을 DB에 등록합니다."""
    global known_face_encodings, known_face_names

    if not FACE_RECOGNITION_AVAILABLE:
        return "face_recognition 라이브러리가 설치되지 않았습니다."
    if image is None:
        return "이미지를 업로드해주세요."

    name = name.strip()
    if not name:
        return "이름을 입력해주세요."

    image_rgb = np.array(image.convert("RGB"))
    encs = face_recognition.face_encodings(image_rgb)

    if not encs:
        return "얼굴을 감지하지 못했습니다. 정면이 잘 보이는 사진을 사용해주세요."

    known_face_encodings.append(encs[0])
    known_face_names.append(name)
    return _registered_list_text()


def remove_face(name: str) -> str:
    """이름으로 DB에서 얼굴을 삭제합니다."""
    global known_face_encodings, known_face_names

    name = name.strip()
    indices = [i for i, n in enumerate(known_face_names) if n == name]
    if not indices:
        return f"'{name}' 을(를) 찾을 수 없습니다."

    for i in reversed(indices):
        known_face_encodings.pop(i)
        known_face_names.pop(i)
    return _registered_list_text()


def _registered_list_text() -> str:
    if not known_face_names:
        return "등록된 얼굴이 없습니다."
    lines = [f"등록된 얼굴 ({len(known_face_names)}명):"]
    for name in known_face_names:
        lines.append(f"  • {name}")
    return "\n".join(lines)


# ── 그리기 헬퍼 ───────────────────────────────────────────────────────────────

def find_group(class_name: str) -> str:
    for group_name, class_names in CLASS_GROUPS.items():
        if class_names and class_name in class_names:
            return group_name
    return "기타"


def should_keep(class_name: str, selected_group: str, class_keyword: str) -> bool:
    group_classes = CLASS_GROUPS.get(selected_group)
    if group_classes is not None and class_name not in group_classes:
        return False
    keyword = class_keyword.strip().lower()
    if keyword and keyword not in class_name.lower():
        return False
    return True


def get_display_label(class_name: str, custom_person_label: str) -> str:
    label = custom_person_label.strip()
    if class_name == "person" and label:
        return label
    return class_name


def draw_detection(
    image_rgb: np.ndarray,
    box: list[int],
    label: str,
    confidence: float,
    group_name: str,
) -> None:
    x1, y1, x2, y2 = box
    color = BOX_COLORS.get(group_name, BOX_COLORS["기타"])

    cv2.rectangle(image_rgb, (x1, y1), (x2, y2), color, 3)

    caption = f"{label} {confidence:.2f}" if confidence < 1.0 else label
    pil_image = Image.fromarray(image_rgb)
    draw = ImageDraw.Draw(pil_image)

    left, top, right, bottom = draw.textbbox((0, 0), caption, font=LABEL_FONT)
    text_w = right - left
    text_h = bottom - top
    label_top = max(y1 - text_h - 12, 0)
    label_bottom = label_top + text_h + 10

    draw.rectangle((x1, label_top, x1 + text_w + 12, label_bottom), fill=color)
    draw.text((x1 + 6, label_top + 4), caption, font=LABEL_FONT, fill=(255, 255, 255))
    image_rgb[:] = np.array(pil_image)


def draw_segmentation_mask(
    image_rgb: np.ndarray,
    mask: np.ndarray,
    group_name: str,
    alpha: float = 0.42,
) -> None:
    color = np.array(BOX_COLORS.get(group_name, BOX_COLORS["기타"]), dtype=np.float32)

    if mask.shape[:2] != image_rgb.shape[:2]:
        mask = cv2.resize(mask, (image_rgb.shape[1], image_rgb.shape[0]))

    mask_bool = mask > 0.5
    if not np.any(mask_bool):
        return

    image_float = image_rgb.astype(np.float32)
    image_float[mask_bool] = image_float[mask_bool] * (1 - alpha) + color * alpha
    image_rgb[:] = image_float.astype(np.uint8)


def _match_face(encoding: np.ndarray, tolerance: float) -> str:
    if not known_face_encodings:
        return "Unknown"
    distances = face_recognition.face_distance(known_face_encodings, encoding)
    best_idx = int(np.argmin(distances))
    if distances[best_idx] <= tolerance:
        return known_face_names[best_idx]
    return "Unknown"


def detect_and_draw_faces(
    image_rgb: np.ndarray,
    use_recognition: bool = False,
    tolerance: float = 0.6,
) -> tuple[int, list[str]]:
    recognized_names: list[str] = []

    if use_recognition and FACE_RECOGNITION_AVAILABLE:
        face_locations = face_recognition.face_locations(image_rgb)
        face_encodings = face_recognition.face_encodings(image_rgb, face_locations)

        for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
            name = _match_face(encoding, tolerance)
            recognized_names.append(name)
            draw_detection(
                image_rgb,
                [left, top, right, bottom],
                name,
                1.0,
                "사람" if name != "Unknown" else "기타",
            )

        return len(face_locations), recognized_names

    # Haar Cascade fallback
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    faces = FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(35, 35))

    for index, (x, y, w, h) in enumerate(faces, start=1):
        label = f"face {index}"
        draw_detection(image_rgb, [int(x), int(y), int(x + w), int(y + h)], label, 1.0, "기타")
        recognized_names.append(label)

    return len(faces), recognized_names


def build_summary(
    rows: list[list[Any]],
    total_raw_count: int,
    face_count: int = 0,
    recognized_names: list[str] | None = None,
) -> str:
    recognized_names = recognized_names or []

    if not rows:
        if total_raw_count == 0:
            base = "탐지된 객체가 없습니다. confidence 값을 낮추거나 더 선명한 이미지를 넣어보세요."
        else:
            base = "선택한 필터 조건에 맞는 객체가 없습니다. 그룹 또는 클래스 키워드를 바꿔보세요."
        if face_count:
            return f"{base}\n얼굴 탐지: {face_count}개"
        return base

    group_counter = Counter(row[4] for row in rows)
    label_counter = Counter(row[2] for row in rows)
    group_text = ", ".join(f"{name} {count}개" for name, count in group_counter.most_common())
    label_text = ", ".join(f"{name} {count}개" for name, count in label_counter.most_common(8))

    lines = [
        f"총 {len(rows)}개 객체를 표시했습니다.",
        f"그룹 요약: {group_text}",
        f"라벨 요약: {label_text}",
        f"얼굴 탐지: {face_count}개",
    ]

    if recognized_names:
        known = [n for n in recognized_names if n != "Unknown" and not n.startswith("face ")]
        unknown = [n for n in recognized_names if n == "Unknown"]
        if known:
            lines.append(f"인식된 인물: {', '.join(known)}")
        if unknown:
            lines.append(f"미인식 얼굴: {len(unknown)}개")

    return "\n".join(lines)


def detect_image(
    image: Image.Image | None,
    model_mode: str,
    confidence_threshold: float,
    selected_group: str,
    class_keyword: str,
    custom_person_label: str,
    show_boxes: bool,
    show_masks: bool,
    show_faces: bool,
    use_face_recognition: bool,
    face_tolerance: float,
) -> tuple[Image.Image | None, Image.Image | None, list[list[Any]], str]:
    if image is None:
        return None, None, [], "이미지를 업로드해주세요."

    original = image.convert("RGB")
    image_rgb = np.array(original)
    annotated = image_rgb.copy()

    active_model = get_model(model_mode)
    results = active_model.predict(source=image_rgb, conf=confidence_threshold, verbose=False)
    result = results[0]

    rows: list[list[Any]] = []
    total_raw_count = 0
    masks = result.masks.data.cpu().numpy() if result.masks is not None else None

    if result.boxes is not None:
        boxes = result.boxes.xyxy.cpu().numpy()
        labels = result.boxes.cls.cpu().numpy()
        confidences = result.boxes.conf.cpu().numpy()

        for index, (box, label, confidence) in enumerate(zip(boxes, labels, confidences)):
            total_raw_count += 1
            class_id = int(label)
            class_name = active_model.names[class_id]

            if not should_keep(class_name, selected_group, class_keyword):
                continue

            group_name = find_group(class_name)
            display_label = get_display_label(class_name, custom_person_label)
            x1, y1, x2, y2 = [int(v) for v in box]

            if show_masks and masks is not None and index < len(masks):
                draw_segmentation_mask(annotated, masks[index], group_name)

            rows.append([len(rows) + 1, class_name, display_label, round(float(confidence), 4), group_name, f"{x1}, {y1}, {x2}, {y2}"])

            if show_boxes:
                draw_detection(annotated, [x1, y1, x2, y2], display_label, float(confidence), group_name)

    face_count = 0
    recognized_names: list[str] = []
    if show_faces:
        face_count, recognized_names = detect_and_draw_faces(
            annotated,
            use_recognition=use_face_recognition,
            tolerance=face_tolerance,
        )

    summary = build_summary(rows, total_raw_count, face_count, recognized_names)
    return original, Image.fromarray(annotated), rows, summary


# ── UI ────────────────────────────────────────────────────────────────────────

with gr.Blocks(title="YOLO 이미지 객체 탐지기") as demo:
    gr.Markdown("# YOLO 이미지 객체 탐지기")

    with gr.Row():
        # ── 왼쪽 컨트롤 패널 ──
        with gr.Column(scale=1):
            image_input = gr.Image(type="pil", label="이미지 업로드")
            model_mode_input = gr.Radio(choices=list(MODEL_OPTIONS.keys()), value="Detection Box", label="탐지 방식")
            confidence_input = gr.Slider(minimum=0.05, maximum=0.95, value=0.25, step=0.05, label="Confidence threshold")
            group_input = gr.Dropdown(choices=list(CLASS_GROUPS.keys()), value="전체", label="객체 그룹 필터")
            keyword_input = gr.Textbox(label="클래스 키워드 필터", placeholder="예: person, car")
            custom_person_label_input = gr.Textbox(label="person 라벨 덮어쓰기 (얼굴 인식 미사용 시)", placeholder="예: 손흥민")
            show_boxes_input = gr.Checkbox(value=True, label="Detection Box 및 라벨 표시")
            show_masks_input = gr.Checkbox(value=True, label="Segmentation Mask 표시")

            gr.Markdown("---")
            gr.Markdown("### 얼굴 탐지 / 인식")
            show_faces_input = gr.Checkbox(value=False, label="얼굴 탐지 활성화")
            use_face_recognition_input = gr.Checkbox(
                value=FACE_RECOGNITION_AVAILABLE,
                label="등록된 얼굴 DB로 인식",
                interactive=FACE_RECOGNITION_AVAILABLE,
            )
            face_tolerance_input = gr.Slider(minimum=0.3, maximum=0.8, value=0.6, step=0.05, label="인식 민감도 (tolerance) — 낮을수록 엄격")

            detect_button = gr.Button("탐지하기", variant="primary")

        # ── 오른쪽 결과 패널 ──
        with gr.Column(scale=2):
            with gr.Row():
                original_output = gr.Image(type="pil", label="원본 이미지")
                annotated_output = gr.Image(type="pil", label="탐지 결과 이미지")

            result_table = gr.Dataframe(
                headers=["순번", "YOLO 클래스", "표시 라벨", "신뢰도", "그룹", "Box 좌표"],
                datatype=["number", "str", "str", "number", "str", "str"],
                label="탐지 결과",
                interactive=False,
            )
            summary_output = gr.Textbox(label="결과 요약", lines=5)

    gr.Markdown("---")
    gr.Markdown("## 얼굴 등록 / 관리")
    gr.Markdown("사진을 드래그하고 이름을 입력한 뒤 **등록** 버튼을 누르면 탐지 시 해당 이름으로 인식됩니다.")

    with gr.Row():
        with gr.Column(scale=1):
            reg_image_input = gr.Image(type="pil", label="등록할 얼굴 사진 (정면 사진 권장)")
            reg_name_input = gr.Textbox(label="이름", placeholder="예: 손흥민")
            reg_button = gr.Button("등록", variant="primary")

        with gr.Column(scale=1):
            reg_status_output = gr.Textbox(label="등록 현황", lines=6, value=_registered_list_text())
            del_name_input = gr.Textbox(label="삭제할 이름", placeholder="예: 손흥민")
            del_button = gr.Button("삭제", variant="stop")

    # ── 이벤트 연결 ──
    detect_button.click(
        fn=detect_image,
        inputs=[
            image_input, model_mode_input, confidence_input, group_input,
            keyword_input, custom_person_label_input,
            show_boxes_input, show_masks_input,
            show_faces_input, use_face_recognition_input, face_tolerance_input,
        ],
        outputs=[original_output, annotated_output, result_table, summary_output],
    )

    reg_button.click(
        fn=register_face,
        inputs=[reg_image_input, reg_name_input],
        outputs=[reg_status_output],
    )

    del_button.click(
        fn=remove_face,
        inputs=[del_name_input],
        outputs=[reg_status_output],
    )


if __name__ == "__main__":
    demo.launch()
