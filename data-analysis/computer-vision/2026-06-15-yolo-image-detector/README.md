# YOLO Image Detector Practice

YOLO 예제 노트북을 참고해 이미지 업로드 기반 객체 탐지 Gradio 앱을 만드는 실습입니다.

## Goal

- 이미지 파일 업로드
- 원본 이미지 표시
- YOLOv8 객체 탐지 실행
- Detection Box 및 라벨 표시
- Segmentation Mask 표시
- 탐지 결과 표와 요약 출력
- 객체 그룹, 클래스 키워드, confidence threshold 필터 제공
- 특정 선수 이미지 업로드 후 `person` 라벨을 선수 이름으로 표시
- 얼굴 위치를 `face 1`, `face 2`처럼 표시하는 비식별 얼굴 탐지 옵션 제공

## Reference Notebooks

수업 예제 원본은 `notebooks/` 폴더에 참고용으로 보관했습니다.

- `00_reference_yolo_2.ipynb`: 특정 객체 필터링, segmentation 예제
- `00_reference_yolo_3.ipynb`: 사람/동물 그룹 분류와 카운트 예제
- `00_reference_yolo_4.ipynb`: 다중 이미지 탐색과 객체 조합 탐지 예제

## Project Structure

```text
2026-06-15-yolo-image-detector/
  app/
    app.py              # Gradio YOLO detector app
    requirements.txt
  notebooks/
    00_reference_yolo_2.ipynb
    00_reference_yolo_3.ipynb
    00_reference_yolo_4.ipynb
  data/
  outputs/
  samples/
```

## Run

```bash
cd data-analysis/computer-vision/2026-06-15-yolo-image-detector/app
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python app.py
```

처음 실행하면 `yolov8n.pt` 가중치가 자동 다운로드됩니다.

## Practice Notes

YOLO 결과에서 중요한 값은 다음과 같습니다.

- `boxes.xyxy`: 객체 위치 좌표
- `boxes.cls`: 탐지 클래스 번호
- `boxes.conf`: confidence score
- `masks.data`: segmentation 모델이 만든 객체별 픽셀 마스크
- `model.names[class_id]`: 클래스 이름

이번 실습의 핵심 함수는 `detect_image()`입니다. 업로드된 이미지를 받아 YOLO 탐지 결과를 만들고, 원본 이미지, 박스가 그려진 이미지, 결과 표, 요약 텍스트를 반환합니다.

## Detection vs Segmentation

- Detection: 객체 위치를 사각형 박스로 표시합니다.
- Segmentation: 객체의 실제 형태를 따라 픽셀 영역을 마스크로 칠합니다.

앱의 `탐지 방식` 옵션에서 `Detection Box` 또는 `Segmentation Mask`를 선택할 수 있습니다.

## Custom Athlete Label

YOLO 기본 모델은 특정 인물의 이름을 직접 식별하지 않고 `person` 클래스로 탐지합니다.

이번 실습에서는 특정 선수 이미지를 업로드한 뒤 `선수 이름 라벨`에 이름을 입력하면, 탐지된 `person` 박스의 표시 라벨을 해당 이름으로 바꿔 보여줍니다.

예:

```text
YOLO 클래스: person
표시 라벨: 손흥민
```

여러 사람 중 특정 선수만 자동 구분하려면 이후 단계에서 얼굴 인식, 이미지 임베딩, 또는 커스텀 데이터셋 기반 fine-tuning이 필요합니다.

## Face Detection Option

앱의 `얼굴 위치 표시` 옵션은 사람의 신원을 맞히지 않고 얼굴의 위치만 표시합니다.

```text
face 1
face 2
```

처럼 비식별 라벨을 사용합니다.
