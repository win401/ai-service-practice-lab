# AI Service Practice Lab

광주 인공지능 사관학교 수업 실습을 관리하면서, 결과물을 AI 서비스 프로토타입과 취업 포트폴리오로 발전시키는 저장소입니다.

이 저장소는 단순 수업 백업용이 아닙니다. 데이터 분석, 머신러닝, 자연어 처리, Next.js 프로토타입을 한 흐름으로 연결해 `AI 서비스 기획자 / 주니어 PM / 프로토타입 빌더 / 데이터 기반 서비스 기획` 포지션을 보여주는 실습 기록으로 운영합니다.

Repository:

```text
https://github.com/win401/ai-service-practice-lab
```

## Workflow

새 수업 실습은 `Python-first, Next.js-frontend` 원칙으로 진행합니다.

- Python/Jupyter: 수업 코드, 데이터 처리, ML/NLP 로직
- FastAPI: Python 로직을 API로 제공
- Next.js: 사용자 화면과 결과 시각화

자세한 기준은 [docs/practice-workflow.md](docs/practice-workflow.md)를 따릅니다.

## Current Projects

### 1. Seoul Apartment Price Map

3억 투자금을 가진 초보 부동산 투자자를 페르소나로 설정하고, 서울 아파트 실거래 데이터를 분석해 3년 후 가격을 예측한 뒤 지도 서비스로 시각화한 머신러닝 프로젝트입니다.

- Live Demo: https://nextjs-map-prototype.vercel.app
- Project Path: `data-analysis/machine-learning/2026-06-04-ml-practice/`
- Web App: `data-analysis/machine-learning/2026-06-04-ml-practice/nextjs-map-prototype/`

핵심 작업:

- 서울 아파트 실거래 데이터 EDA
- 거래가/평당 단가 단위 정리
- 이상치 탐지 및 기준 정리
- 2014년 기준 3억 이하 후보 추출
- 2017년 실제 가격과 비교하는 3년 후 예측 백테스트
- 예측 결과를 Next.js + Leaflet 지도 서비스로 구현
- GitHub + Vercel 배포

### 2. Korean TF-IDF News Search

한글 TF-IDF 뉴스 검색 수업 노트북을 Gradio 대신 Next.js dev 화면으로 재구성한 자연어 처리 실습 프로젝트입니다.

- Local App: `http://localhost:3011`
- Project Path: `data-analysis/natural-language-processing/2026-06-05-korean-tokenization-practice/`
- Web App: `data-analysis/natural-language-processing/2026-06-05-korean-tokenization-practice/nextjs-news-search/`

핵심 작업:

- 네이버 검색 Open API 연동
- RSS XML 뉴스 피드 파싱
- 한글 간이 토큰화
- TF-IDF 벡터 생성
- 코사인 유사도 기반 뉴스 랭킹
- Open API / RSS 데이터 소스 비교 UI
- RSS description HTML 정제

### 3. Korean Menu Recommender

맛집 메뉴 CSV 데이터를 이용해 `해장 잘되는 음식`, `칼칼한 음식`, `다이어트에 좋은 음식` 같은 자연어 입력에 맞는 메뉴를 추천하고, 레시피/칼로리/영양 포인트를 함께 보여주는 자연어 처리 실습 프로젝트입니다.

- Local App: `http://localhost:3012`
- Project Path: `data-analysis/natural-language-processing/2026-06-05-korean-tokenization-practice/`
- Web App: `data-analysis/natural-language-processing/2026-06-05-korean-tokenization-practice/nextjs-menu-recommender/`

핵심 작업:

- CSV 메뉴 데이터 앱 폴더 포함
- Python FastAPI 추천 backend 구현
- 한국어 간이 토큰화와 조사/어미 정규화
- TF-IDF 벡터 생성
- 코사인 유사도 기반 메뉴 랭킹
- 해장/칼칼함/다이어트 등 의도 키워드 확장
- 레시피, 예상 칼로리, 영양 포인트 정보 노출
- 음식 이미지 업로드 기능은 추후 재활성화를 위해 주석 처리
- 추천 이유와 점수 분해 UI 구현

### 4. Few-Shot Movie Recommendation Chatbot

영화 리뷰 감성분석 데이터를 이용해 사용자의 취향 문장과 유사한 리뷰를 검색하고, few-shot 예제와 함께 추천 프롬프트를 구성하는 실무 응용 프로젝트입니다.

- Project Path: `data-analysis/practical_application/`
- Web App: `data-analysis/practical_application/nextjs-movie-recommender/`
- Backend: `data-analysis/practical_application/backend/`

핵심 작업:

- 수업 DOCX의 추천 챗봇 흐름을 코드로 재구성
- `ratings_train.txt` 영화 리뷰 데이터 로딩
- 간단한 한국어 토큰화
- TF-IDF style 유사 리뷰 검색
- 긍정/부정/중립 few-shot 예제 구성
- 유사 리뷰와 few-shot 예제를 조합한 최종 프롬프트 생성
- OpenAI API 키가 없을 때도 동작하는 fallback 추천
- FastAPI backend + Next.js dev 화면 구현

### 5. Multilingual Translation Lab

Seq2Seq, BLEU, 사전학습 번역 모델 수업 예제를 바탕으로 Hugging Face NLLB 다국어 번역 모델, OpenAI 번역 비교, 파파고 기준 BLEU 평가, 법률 도메인 분석을 연결한 자연어 처리 실습 프로젝트입니다.

- Local App: `http://localhost:3014`
- Project Path: `data-analysis/natural-language-processing/2026-06-09-multilingual-translation/`
- Backend: `data-analysis/natural-language-processing/2026-06-09-multilingual-translation/backend/`
- Frontend: `data-analysis/natural-language-processing/2026-06-09-multilingual-translation/frontend/`

핵심 작업:

- 수업 제공 Seq2Seq / BLEU / pretrained translation 노트북 정리
- Hugging Face `facebook/nllb-200-distilled-600M` 다국어 번역 API 구현
- FastAPI backend + Next.js frontend 분리
- 기준 번역문 입력 시 BLEU 점수와 품질 해석 표시
- 파파고 기준 번역문 대비 NLLB / OpenAI 번역 품질 비교 페이지 구현
- 도메인 실험실에서 일반, 법률, 금융, 의류/쇼핑 문장 처리
- 법률 도메인에서 `EunB2/KL-RoBERTa` 기반 법률 문맥 유사도와 용어 매칭 분석
- `.env` 기반 OpenAI API 키 관리와 `.env.example` 제공

### 6. YOLO Object Detection + Face Recognition

YOLO 예제 노트북을 참고해 YOLOv8 객체 탐지와 `face_recognition` 기반 얼굴 인식을 결합한 컴퓨터 비전 실습 프로젝트입니다. Gradio 대신 FastAPI + Next.js로 구성했습니다.

- Local App: `http://localhost:3001`
- Project Path: `data-analysis/computer-vision/2026-06-15-yolo-image-detector/`
- Backend: `data-analysis/computer-vision/2026-06-15-yolo-image-detector/backend/`
- Frontend: `data-analysis/computer-vision/2026-06-15-yolo-image-detector/nextjs-face-detector/`

핵심 작업:

- 수업 제공 YOLO 노트북 3개 참고 자료 보관
- `ultralytics` YOLOv8n Detection / Segmentation 모델 기반 객체 탐지
- 이미지 드래그 업로드 후 원본 · 탐지 결과 이미지 나란히 표시
- Detection Box, Segmentation Mask, 라벨, confidence score 표시
- 객체 그룹 필터 · 클래스 키워드 필터 · confidence threshold 슬라이더 제공
- UI에서 얼굴 사진 드래그 + 이름 입력으로 얼굴 DB 등록 (같은 이름 여러 장 등록 시 인식률 향상)
- `face_recognition` + `num_jitters=5` 고품질 인코딩으로 다른 각도/조명 사진도 인식
- FastAPI backend + Next.js 다크 테마 UI

## Repository Structure

```text
data-analysis/
  computer-vision/
    2026-06-15-yolo-image-detector/
      notebooks/              # YOLO 수업 참고 노트북
      app/                    # (구) Gradio 이미지 객체 탐지 앱
      backend/                # FastAPI YOLO + face_recognition API
      nextjs-face-detector/   # 객체 탐지 · 얼굴 등록/인식 Next.js 앱
      samples/known_faces/    # 등록용 얼굴 샘플 이미지

  machine-learning/
    2026-06-04-ml-practice/
      notebooks/              # Jupyter 머신러닝 실습 노트북
      reports/                # 분석 결과 리포트
      outputs/                # 시각화 이미지
      notes/                  # 수업 요약 노트
      nextjs-map-prototype/   # 서울 아파트 예측 지도 서비스

  natural-language-processing/
    2026-06-05-korean-tokenization-practice/
      notebooks/              # 한국어 토큰화 / TF-IDF 실습 노트북
      notes/                  # 수업 요약 노트
      reports/                # 실습 결과 리포트
      outputs/                # 시각화/결과 이미지
      nextjs-news-search/     # TF-IDF 뉴스 검색 Next.js 앱
      nextjs-menu-recommender/ # Python backend + Next.js 메뉴 추천 앱
    2026-06-09-multilingual-translation/
      notebooks/              # Seq2Seq / BLEU / pretrained translation 수업 노트북
      backend/                # NLLB, OpenAI, BLEU, 법률 도메인 분석 FastAPI
      frontend/               # 다국어 번역기 / 평가 / 도메인 실험실 Next.js 앱
      data/                   # raw / processed placeholder
      reports/                # 실습 리포트
      outputs/                # 결과 산출물
      notes/                  # 실습 노트

  practical_application/
    docs/                      # 실습 지시서 DOCX
    data/                      # 영화 리뷰 데이터
    notebooks/                 # Few-shot 추천 실습 노트북
    backend/                   # Python FastAPI 추천 backend
    nextjs-movie-recommender/  # Few-shot 영화 추천 Next.js 앱

ai-service-planning/          # AI 서비스 기획 수업 자료
assignments/                  # 과제 제출물
notes/                        # 공통 수업 노트
portfolio-candidates/         # 포트폴리오 후보
```

## Operating Rule

수업 실습은 처음에는 이 저장소에서 관리합니다.

결과물이 쓸만해지면 아래 중 하나로 승격합니다.

- 취업 포트폴리오 후보
- 사업 아이디어 후보
- 기존 프로젝트와 연결되는 실험 자산
- 별도 GitHub 레포 / Vercel 배포 프로젝트

현재 연결 가능한 외부 프로젝트:

- `business-idea-lab`: 사업 아이디어/전략 정리
- `Kmong_project`: 첫 수익화를 위한 랜딩페이지 제작 포트폴리오
- `roomy_project`: 고시원 SaaS 검증
- `job_simulator_pj`: 취업/교육용 AI 서비스 자산

## Portfolio Direction

이 저장소는 다음 역량을 보여주는 근거 자료로 발전시킵니다.

- 데이터를 보고 문제를 정의하는 능력
- 머신러닝 모델을 서비스 시나리오와 연결하는 능력
- 자연어 처리 개념을 실제 검색/추천 UI로 구현하는 능력
- Jupyter 실습을 Next.js 프로토타입으로 전환하는 능력
- GitHub, Vercel, API, RSS 같은 실무 도구를 연결하는 능력

## Next Project Ideas

### AI 고시문 모니터링 RAG 지도 서비스

경기도청 고시·공고 같은 관공서의 최신 고시문을 수집해 도시개발구역 지정, 개발계획 변경, 지구단위계획 등 신규 지정 현황을 빠르게 확인하는 프로젝트입니다.

초기 MVP:

- 경기도청 고시·공고 페이지에서 최신 문서 목록 수집
- `도시개발구역`, `개발계획`, `지구단위계획`, `산업단지`, `정비구역` 키워드 필터링
- PDF/HWP 첨부파일 다운로드 및 텍스트 추출
- RAG 기반 문서 검색과 핵심 내용 요약
- 주소/지번 추출 후 카카오 로컬 API 또는 네이버 Geocoding API로 좌표 변환
- Next.js 지도 화면에서 신규 고시 위치와 요약 정보 표시
- 추후 특정 키워드 고시가 올라오면 알림을 보내는 크롤링 봇으로 확장

## Run Examples

서울 아파트 예측 지도:

```bash
cd data-analysis/machine-learning/2026-06-04-ml-practice/nextjs-map-prototype
npm install
npm run dev -- --port 3000
```

TF-IDF 뉴스 검색:

```bash
cd data-analysis/natural-language-processing/2026-06-05-korean-tokenization-practice/nextjs-news-search
npm install
npm run dev -- --port 3011
```

네이버 뉴스 검색 API를 사용하려면 `nextjs-news-search/.env.local`에 아래 값을 추가합니다.

```bash
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret
```

음식 메뉴 추천:

```bash
cd data-analysis/natural-language-processing/2026-06-05-korean-tokenization-practice/nextjs-menu-recommender
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8000
```

다른 터미널에서:

```bash
cd data-analysis/natural-language-processing/2026-06-05-korean-tokenization-practice/nextjs-menu-recommender
npm install
npm run dev -- --port 3012
```

다국어 번역 실습:

```bash
cd data-analysis/natural-language-processing/2026-06-09-multilingual-translation/backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8000
```

다른 터미널에서:

```bash
cd data-analysis/natural-language-processing/2026-06-09-multilingual-translation/frontend
npm install
npm run dev -- --port 3014
```

OpenAI 비교 평가와 도메인 실험실을 사용하려면 `backend/.env`에 아래 값을 추가합니다.

```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-5.2
```

YOLO 객체 탐지 · 얼굴 인식:

```bash
cd data-analysis/computer-vision/2026-06-15-yolo-image-detector/backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000
```

다른 터미널에서:

```bash
cd data-analysis/computer-vision/2026-06-15-yolo-image-detector/nextjs-face-detector
npm install
npm run dev -- --port 3001
```
