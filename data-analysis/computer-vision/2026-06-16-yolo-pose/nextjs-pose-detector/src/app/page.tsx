'use client';

import { useRef, useState } from 'react';
import styles from './page.module.css';

const API = 'http://127.0.0.1:8001';

type Keypoint = { name: string; x: number; y: number; conf: number };
type Person = {
  id: number;
  pose: string;
  det_confidence: number;
  pose_confidence: number;
  reason: string;
  visible_keypoints: number;
  keypoints: Keypoint[];
};
type DetectRow = { class: string; group: string; confidence: number; box: string };
type Result = {
  original: string;
  annotated: string;
  people: Person[];
  person_count: number;
  detect_rows: DetectRow[];
  detect_count: number;
  pose_summary: Record<string, number>;
  det_summary: Record<string, number>;
};

const POSE_EMOJI: Record<string, string> = {
  '서있는 자세': '🧍',
  '앉은 자세':   '🪑',
  '누운 자세':   '🛏️',
  '만세 자세':   '🙌',
  '알 수 없음':  '❓',
};

function ConfBar({ value }: { value: number }) {
  return (
    <div className={styles.confBar}>
      <div className={styles.confBarTrack}>
        <div className={styles.confBarFill} style={{ width: `${Math.round(value * 100)}%` }} />
      </div>
      <span className={styles.confNum}>{Math.round(value * 100)}%</span>
    </div>
  );
}

function Toggle({ label, on, onChange }: { label: string; on: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      className={`${styles.toggle} ${on ? styles.toggleOn : ''}`}
      onClick={() => onChange(!on)}
    >
      <span className={styles.toggleDot} />
      {label}
    </button>
  );
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [confidence, setConfidence] = useState(0.5);
  const [useDetect,  setUseDetect]  = useState(true);
  const [useSegment, setUseSegment] = useState(false);
  const [usePose,    setUsePose]    = useState(true);
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const onFile = (f: File) => {
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
  };

  const analyze = async () => {
    if (!file) return;
    if (!useDetect && !useSegment && !usePose) {
      alert('최소 하나의 분석 모드를 켜주세요.');
      return;
    }
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append('image', file);
      fd.append('confidence', String(confidence));
      fd.append('use_detect',  String(useDetect));
      fd.append('use_segment', String(useSegment));
      fd.append('use_pose',    String(usePose));
      const res = await fetch(`${API}/analyze`, { method: 'POST', body: fd });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (e) {
      alert('분석 실패: ' + (e instanceof Error ? e.message : e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <h1>YOLO Pose 자세 알림 서비스</h1>
        <p>Computer Vision Practice · 2026-06-16</p>
      </header>

      <div className={styles.workspace}>
        {/* ── 왼쪽: 입력 영역 ── */}
        <div className={styles.inputPanel}>
          <div className={styles.panelLabel}>[ 입력 영역 ]</div>

          {/* 이미지 업로드 */}
          <div
            className={`${styles.dropzone} ${dragOver ? styles.dropzoneActive : ''}`}
            onDragOver={e => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={e => { e.preventDefault(); setDragOver(false); const f = e.dataTransfer.files[0]; if (f) onFile(f); }}
            onClick={() => inputRef.current?.click()}
          >
            <input ref={inputRef} type="file" accept="image/*" style={{ display: 'none' }}
              onChange={e => { const f = e.target.files?.[0]; if (f) onFile(f); }} />
            {preview
              ? <img src={preview} alt="선택된 이미지" />
              : <>
                  <div style={{ fontSize: 40 }}>🧍</div>
                  <div style={{ fontSize: 15, fontWeight: 600 }}>이미지 업로드</div>
                  <div className={styles.dropzoneHint}>jpg / png / webp</div>
                </>}
          </div>

          {/* 분석 모드 토글 */}
          <div className={styles.toggleSection}>
            <div className={styles.toggleSectionLabel}>분석 모드</div>
            <div className={styles.toggleGroup}>
              <Toggle label="🔍 객체 탐지" on={useDetect}  onChange={setUseDetect}  />
              <Toggle label="🎨 세그멘테이션" on={useSegment} onChange={setUseSegment} />
              <Toggle label="🦴 자세 분석" on={usePose}   onChange={setUsePose}   />
            </div>
          </div>

          {/* 슬라이더 */}
          <div className={styles.sliderRow}>
            <div className={styles.sliderHeader}>
              <span className={styles.sliderLabel}>탐지 신뢰도 임계값</span>
              <span className={styles.sliderValue}>{confidence.toFixed(2)}</span>
            </div>
            <input type="range" min={0.1} max={0.9} step={0.05}
              value={confidence} onChange={e => setConfidence(Number(e.target.value))} />
          </div>

          {/* 분석 버튼 */}
          <button className={styles.btnAnalyze} onClick={analyze} disabled={!file || loading}>
            {loading ? '분석 중…' : '분석 시작'}
          </button>
        </div>

        {/* ── 오른쪽: 출력 영역 ── */}
        <div className={styles.outputPanel}>
          <div className={styles.panelLabel}>[ 출력 영역 ]</div>

          {!result ? (
            <div className={styles.emptyState}>
              <div style={{ fontSize: 48 }}>📊</div>
              <div>이미지를 업로드하고 분석을 시작하면 결과가 여기에 표시됩니다.</div>
            </div>
          ) : (
            <>
              {/* 이미지 + 요약 카드 */}
              <div className={styles.resultTop}>
                <div className={styles.resultImageWrap}>
                  <span>결과 이미지 · 오버레이</span>
                  <img src={`data:image/jpeg;base64,${result.annotated}`} alt="결과" />
                </div>

                <div className={styles.summaryCard}>
                  {result.person_count > 0 && (
                    <>
                      <div className={styles.summaryTotal}>
                        🦴 자세 분석 — {result.person_count}명<br />
                        <span style={{ fontSize: 12, color: 'var(--muted)', fontWeight: 400 }}>
                          {Object.entries(result.pose_summary).map(([p, c]) => `${p} ${c}명`).join(' / ')}
                        </span>
                      </div>
                      <div className={styles.summaryRows}>
                        {result.people.map(p => (
                          <div key={p.id} className={styles.summaryRow}>
                            <span className={styles.summaryPose}>
                              {POSE_EMOJI[p.pose] ?? ''} #{p.id} {p.pose}
                            </span>
                            <span className={styles.summaryCount}>
                              {Math.round(p.pose_confidence * 100)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    </>
                  )}
                  {result.detect_count > 0 && (
                    <>
                      <div className={`${styles.summaryTotal} ${result.person_count > 0 ? styles.summaryTotalBorder : ''}`}>
                        🔍 객체 탐지 — {result.detect_count}개<br />
                        <span style={{ fontSize: 12, color: 'var(--muted)', fontWeight: 400 }}>
                          {Object.entries(result.det_summary).map(([g, c]) => `${g} ${c}개`).join(' / ')}
                        </span>
                      </div>
                    </>
                  )}
                  {result.person_count === 0 && result.detect_count === 0 && (
                    <div style={{ color: 'var(--muted)', fontSize: 13, textAlign: 'center' }}>탐지된 객체 없음</div>
                  )}
                </div>
              </div>

              {/* 자세 분석 표 */}
              {result.person_count > 0 && (
                <div className={styles.dataframeSection}>
                  <div className={styles.dataframeTitle}>자세 분석 상세 결과</div>
                  <div className={styles.dataframeTable}>
                    <table>
                      <thead>
                        <tr>
                          <th>번호</th>
                          <th>자세</th>
                          <th>탐지신뢰도</th>
                          <th>자세신뢰도</th>
                          <th>판별 근거</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.people.map(p => (
                          <tr key={p.id}>
                            <td>{p.id}</td>
                            <td>{POSE_EMOJI[p.pose] ?? ''} {p.pose}</td>
                            <td><ConfBar value={p.det_confidence} /></td>
                            <td><ConfBar value={p.pose_confidence} /></td>
                            <td style={{ color: 'var(--muted)', fontSize: 12 }}>{p.reason}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* 객체 탐지 표 */}
              {result.detect_count > 0 && (
                <div className={styles.dataframeSection}>
                  <div className={styles.dataframeTitle}>객체 탐지 상세 결과</div>
                  <div className={styles.quickTable}>
                    <table>
                      <thead>
                        <tr><th>#</th><th>클래스</th><th>그룹</th><th>신뢰도</th></tr>
                      </thead>
                      <tbody>
                        {result.detect_rows.map((r, i) => (
                          <tr key={i}>
                            <td>{i + 1}</td>
                            <td>{r.class}</td>
                            <td>{r.group}</td>
                            <td><ConfBar value={r.confidence} /></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
