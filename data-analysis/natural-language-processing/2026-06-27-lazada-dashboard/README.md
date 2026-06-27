# Lazada 데이터 관리자 대시보드 with Text-to-SQL AI 챗봇

Lazada e-커머스 상품 데이터 1,000건을 SQLite DB에 저장하고, 자연어로 데이터를 조회하는 AI 관리자 대시보드를 Gradio로 구현한 프로젝트입니다.

## 기술 스택

| 구분 | 사용 기술 |
|------|----------|
| 데이터 | lazada-products.csv (1,000 상품 × 29 컬럼) |
| DB | SQLite3 |
| UI | Gradio |
| AI | OpenAI GPT-4o-mini (Text-to-SQL) |
| 시각화 | Plotly |
| 환경 | Google Colab |

## 시스템 구조

```
CSV 원본 데이터
    ↓ pandas 전처리
SQLite DB (lazada.db)
    ├── sellers (197건)
    ├── brands (78건)
    ├── categories (66건)
    └── products (1,000건)
    ↓
Gradio 대시보드
    ├── 📊 대시보드 탭 (KPI + 차트 5종)
    └── 💬 AI 챗봇 탭 (Text-to-SQL)
```

## 데이터 정제 전후 비교

| 항목 | 정제 전 | 정제 후 |
|------|--------|--------|
| 총 행수 | 1,000건 | 1,000건 |
| 평점 0 처리 | 296건 (0으로 기록) | 296건 → NULL 처리 |
| colors/color 결측치 | 500건 | '없음'으로 채움 |
| seller 관련 결측치 | 27~122건 | '없음'으로 채움 |
| breadcrumb | JSON 배열 문자열 | level1/level2/level3 분리 |
| 가격 이상치 | 0원 이하 없음 | 처리 불필요 |

## ERD 다이어그램

```
[sellers]           [brands]
    │ 1                │ 1
    │                  │
    │ N                │ N
    └──────[products]──┘
               │ N
               │
               │ 1
          [categories]
```

**테이블 관계 (1:N)**
- `sellers` (1) → `products` (N)
- `brands` (1) → `products` (N)
- `categories` (1) → `products` (N)

**제약조건**
- PRIMARY KEY: 각 테이블 id
- FOREIGN KEY: products → sellers, brands, categories
- UNIQUE: sellers.seller_name, products.sku
- CHECK: rating BETWEEN 0 AND 5, initial_price >= 0, final_price >= 0

## 구현한 차트 5종

| # | 차트명 | 설명 |
|---|--------|------|
| 1 | 카테고리별 매출 TOP 10 | level1 기준 GMV 합산, 가로 막대 |
| 2 | 슈퍼셀러 vs 일반셀러 비교 | 상품수 / 총판매수량 / 평균평점 비교 |
| 3 | 평점 분포 히스토그램 | 0.1 단위 평점별 상품 수 |
| 4 | 할인율 TOP 10 | (정가-판매가)/정가 기준 상위 10개 |
| 5 | 베스트셀러 TOP 10 | 판매량 기준 상위 10개 테이블 |

## AI 챗봇 테스트 결과

### ✅ 정상 답변 (5종)

| 질문 | 결과 |
|------|------|
| 가장 비싼 상품 5개 보여줘 | 정상 답변 |
| 슈퍼셀러 중 매출이 가장 높은 셀러는? | 정상 답변 |
| 카테고리별 평균 평점이 가장 높은 카테고리는? | 정상 답변 |
| 평점이 4.5 이상이면서 100건 이상 팔린 상품의 수 | 정상 답변 |
| Xiaomi 브랜드 상품의 평균 가격과 총 판매수량 | 정상 답변 |

### 🛡️ 가드레일 차단 확인

| 위험 요청 | 결과 |
|----------|------|
| products 테이블을 통째로 삭제해줘 | ⚠️ BLOCKED |
| 모든 데이터 삭제해줘 | ⚠️ BLOCKED |

## GMV 환율 처리

데이터에 5개 통화(MYR 586건, IDR 347건, PHP 53건, SGD 12건, THB 2건)가 혼재하여 실시간 환율 API를 통해 통화별 KRW 환산 후 합산.

- 환율 API: open.er-api.com
- 총 GMV: 약 ₩307억 (KRW 환산)

## 어려웠던 점 & 해결 방법

| 문제 | 해결 |
|------|------|
| SQLite 멀티스레드 오류 | chat 함수 내에서 `sqlite3.connect()` 새로 연결 |
| GPT가 SQL에 코드블록 추가 | `re.sub(r'\`\`\`sql\|\`\`\`', '', sql)` 로 제거 |
| 세션 재시작 시 UNIQUE 오류 | DB 생성 전 기존 파일 `os.remove()` 삭제 |
| 다통화 GMV 계산 오류 | 통화별 GMV 분리 후 각각 환율 적용해 합산 |

## 실행 방법

1. Google Colab에서 `lazada_dashboard.ipynb` 열기
2. `lazada-products.csv` 파일 업로드
3. Colab 비밀키에 `OPENAI_API_KEY` 등록
4. 셀 전체 실행
5. 출력된 Gradio 링크로 접속
