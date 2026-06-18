'use client';

import { useCallback, useRef, useState } from 'react';
import styles from './page.module.css';

const API = 'http://127.0.0.1:8000';

const CLASS_GROUPS = ['전체', '사람', '동물', '차량', '교통 신호', '스포츠', '소지품', '전자기기', '음식'];

type DetectRow = { id: number; class: string; confidence: number; group: string; box: string };
type FaceResult = { name: string; emotion: string };
type DetectResult = { original: string; annotated: string; rows: DetectRow[]; summary: string; face_results: FaceResult[] };
type FaceCounts = { [name: string]: number };

export default function Home() {
  const [tab, setTab] = useState<'detect' | 'register'>('detect');

  // ── 탐지 설정 ──
  const [mode, setMode] = useState('box');
  const [confidence, setConfidence] = useState(0.25);
  const [group, setGroup] = useState('전체');
  const [keyword, setKeyword] = useState('');
  const [showBoxes, setShowBoxes] = useState(true);
  const [showMasks, setShowMasks] = useState(true);
  const [showFaces, setShowFaces] = useState(false);
  const [useRecognition, setUseRecognition] = useState(false);
  const [tolerance, setTolerance] = useState(0.6);

  // ── 탐지 상태 ──
  const [detectFile, setDetectFile] = useState<File | null>(null);
  const [detectPreview, setDetectPreview] = useState<string | null>(null);
  const [result, setResult] = useState<DetectResult | null>(null);
  const [detecting, setDetecting] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const detectInputRef = useRef<HTMLInputElement>(null);

  // ── 등록 상태 ──
  const [regFile, setRegFile] = useState<File | null>(null);
  const [regPreview, setRegPreview] = useState<string | null>(null);
  const [regName, setRegName] = useState('');
  const [registering, setRegistering] = useState(false);
  const [regStatus, setRegStatus] = useState<{ ok: boolean; msg: string } | null>(null);
  const [faces, setFaces] = useState<string[]>([]);
  const [faceCounts, setFaceCounts] = useState<FaceCounts>({});
  const [regDragOver, setRegDragOver] = useState(false);

  const loadFaces = useCallback(async () => {
    try {
      const res = await fetch(`${API}/faces`);
      const data = await res.json();
      setFaces(data.names ?? []);
      setFaceCounts(data.counts ?? {});
    } catch { /* 서버 미시작 */ }
  }, []);

  // 탭 전환 시 얼굴 목록 갱신
  const switchTab = (t: 'detect' | 'register') => {
    setTab(t);
    if (t === 'register') loadFaces();
  };

  // ── 탐지 이미지 선택 ──
  const onDetectFile = (file: File) => {
    setDetectFile(file);
    setDetectPreview(URL.createObjectURL(file));
    setResult(null);
  };

  const onDetectDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) onDetectFile(f);
  };

  // ── 탐지 실행 ──
  const detect = async () => {
    if (!detectFile) return;
    setDetecting(true);
    try {
      const fd = new FormData();
      fd.append('image', detectFile);
      fd.append('mode', mode);
      fd.append('confidence', String(confidence));
      fd.append('group', group);
      fd.append('keyword', keyword);
      fd.append('show_boxes', String(showBoxes));
      fd.append('show_masks', String(showMasks));
      fd.append('show_faces', String(showFaces));
      fd.append('use_recognition', String(useRecognition));
      fd.append('tolerance', String(tolerance));

      const res = await fetch(`${API}/detect`, { method: 'POST', body: fd });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (e) {
      alert('탐지 실패: ' + (e instanceof Error ? e.message : e));
    } finally {
      setDetecting(false);
    }
  };

  // ── 얼굴 등록 ──
  const onRegFile = (file: File) => {
    setRegFile(file);
    setRegPreview(URL.createObjectURL(file));
    setRegStatus(null);
  };

  const registerFace = async () => {
    if (!regFile || !regName.trim()) return;
    setRegistering(true);
    setRegStatus(null);
    try {
      const fd = new FormData();
      fd.append('image', regFile);
      fd.append('name', regName.trim());
      const res = await fetch(`${API}/faces/register`, { method: 'POST', body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? '등록 실패');
      setRegStatus({ ok: true, msg: `${data.registered} 등록 완료 (${data.count}장 누적 — 장수가 많을수록 인식률 향상)` });
      await loadFaces();
      setRegName('');
      setRegFile(null);
      setRegPreview(null);
    } catch (e) {
      setRegStatus({ ok: false, msg: e instanceof Error ? e.message : '오류 발생' });
    } finally {
      setRegistering(false);
    }
  };

  const deleteFace = async (name: string) => {
    try {
      const res = await fetch(`${API}/faces/${encodeURIComponent(name)}`, { method: 'DELETE' });
      const data = await res.json();
      setFaces(data.names);
    } catch { /* ignore */ }
  };

  return (
    <div className={styles.app}>
      {/* ── 헤더 ── */}
      <header className={styles.header}>
        <h1>YOLO 객체 탐지 · 얼굴 인식</h1>
        <p>Computer Vision Practice · 2026-06-15</p>
      </header>

      {/* ── 사이드바 ── */}
      <aside className={styles.sidebar}>
        <div className={styles.section}>
          <div className={styles.sectionTitle}>탐지 설정</div>

          <div className={styles.field}>
            <span className={styles.fieldLabel}>탐지 방식</span>
            <select value={mode} onChange={e => setMode(e.target.value)}>
              <option value="box">Detection Box</option>
              <option value="seg">Segmentation Mask</option>
            </select>
          </div>

          <div className={styles.field}>
            <span className={styles.fieldLabel}>Confidence: {confidence.toFixed(2)}</span>
            <div className={styles.rangeRow}>
              <input type="range" min={0.05} max={0.95} step={0.05}
                value={confidence} onChange={e => setConfidence(Number(e.target.value))} />
              <span>{confidence.toFixed(2)}</span>
            </div>
          </div>

          <div className={styles.field}>
            <span className={styles.fieldLabel}>객체 그룹</span>
            <select value={group} onChange={e => setGroup(e.target.value)}>
              {CLASS_GROUPS.map(g => <option key={g}>{g}</option>)}
            </select>
          </div>

          <div className={styles.field}>
            <span className={styles.fieldLabel}>클래스 키워드</span>
            <input placeholder="예: person, car" value={keyword}
              onChange={e => setKeyword(e.target.value)} />
          </div>

          <label className={styles.toggle}>
            <input type="checkbox" checked={showBoxes} onChange={e => setShowBoxes(e.target.checked)} />
            Detection Box 표시
          </label>
          <label className={styles.toggle}>
            <input type="checkbox" checked={showMasks} onChange={e => setShowMasks(e.target.checked)} />
            Segmentation Mask 표시
          </label>
        </div>

        <div className={styles.section}>
          <div className={styles.sectionTitle}>얼굴 인식</div>

          <label className={styles.toggle}>
            <input type="checkbox" checked={showFaces} onChange={e => setShowFaces(e.target.checked)} />
            얼굴 탐지 활성화
          </label>
          <label className={styles.toggle}>
            <input type="checkbox" checked={useRecognition} onChange={e => setUseRecognition(e.target.checked)} />
            등록된 얼굴 DB 사용
          </label>

          <div className={styles.field}>
            <span className={styles.fieldLabel}>인식 민감도 (tolerance)</span>
            <div className={styles.rangeRow}>
              <input type="range" min={0.3} max={0.8} step={0.05}
                value={tolerance} onChange={e => setTolerance(Number(e.target.value))} />
              <span>{tolerance.toFixed(2)}</span>
            </div>
          </div>
        </div>

        <button className={styles.btnPrimary} onClick={detect}
          disabled={!detectFile || detecting}>
          {detecting ? '탐지 중…' : '탐지하기'}
        </button>
      </aside>

      {/* ── 메인 ── */}
      <main className={styles.main}>
        <div className={styles.tabs}>
          <button className={`${styles.tab} ${tab === 'detect' ? styles.tabActive : ''}`}
            onClick={() => switchTab('detect')}>탐지</button>
          <button className={`${styles.tab} ${tab === 'register' ? styles.tabActive : ''}`}
            onClick={() => switchTab('register')}>얼굴 등록</button>
        </div>

        {/* ── 탐지 탭 ── */}
        {tab === 'detect' && (
          <div className={styles.detectTab}>
            <div
              className={`${styles.dropzone} ${dragOver ? styles.dropzoneActive : ''}`}
              onDragOver={e => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={onDetectDrop}
              onClick={() => detectInputRef.current?.click()}
            >
              <input ref={detectInputRef} type="file" accept="image/*" style={{ display: 'none' }}
                onChange={e => { const f = e.target.files?.[0]; if (f) onDetectFile(f); }} />
              {detectPreview
                ? <img src={detectPreview} alt="선택된 이미지" style={{ maxHeight: 160, maxWidth: '100%', borderRadius: 8 }} />
                : <>
                    <div style={{ fontSize: 32 }}>🖼️</div>
                    <div>이미지를 드래그하거나 클릭해서 업로드</div>
                    <div className={styles.dropzoneHint}>JPG, PNG, WEBP 지원</div>
                  </>}
            </div>

            {result && (
              <>
                <div className={styles.previewRow}>
                  <div className={styles.imageCard}>
                    <span>원본</span>
                    <img src={`data:image/jpeg;base64,${result.original}`} alt="원본" />
                  </div>
                  <div className={styles.imageCard}>
                    <span>탐지 결과</span>
                    <img src={`data:image/jpeg;base64,${result.annotated}`} alt="결과" />
                  </div>
                </div>

                <div className={styles.summary}>{result.summary}</div>

                {result.rows.length > 0 && (
                  <div className={styles.table}>
                    <table>
                      <thead>
                        <tr>
                          <th>#</th>
                          <th>클래스</th>
                          <th>신뢰도</th>
                          <th>그룹</th>
                          <th>좌표</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.rows.map(row => (
                          <tr key={row.id}>
                            <td>{row.id}</td>
                            <td>{row.class}</td>
                            <td>{row.confidence}</td>
                            <td>{row.group}</td>
                            <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{row.box}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {result.face_results?.length > 0 && (
                  <div className={styles.table}>
                    <table>
                      <thead>
                        <tr>
                          <th>#</th>
                          <th>인식 이름</th>
                          <th>표정</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.face_results.map((f, i) => (
                          <tr key={i}>
                            <td>{i + 1}</td>
                            <td>{f.name}</td>
                            <td>{f.emotion || '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* ── 등록 탭 ── */}
        {tab === 'register' && (
          <div className={styles.registerTab}>
            <div className={styles.registerForm}>
              <h2>얼굴 등록</h2>
              <p>정면 얼굴이 잘 보이는 사진을 드래그하고 이름을 입력한 뒤 등록하세요.<br />
                <strong style={{color: 'var(--accent)'}}>같은 이름으로 여러 장 등록할수록 인식률이 높아집니다.</strong><br />
                등록 후 탐지 탭에서 "등록된 얼굴 DB 사용"을 켜면 해당 이름으로 인식됩니다.</p>

              <div
                className={`${styles.faceDropzone} ${regDragOver ? styles.faceDropzoneActive : ''}`}
                onDragOver={e => { e.preventDefault(); setRegDragOver(true); }}
                onDragLeave={() => setRegDragOver(false)}
                onDrop={e => { e.preventDefault(); setRegDragOver(false); const f = e.dataTransfer.files[0]; if (f) onRegFile(f); }}
              >
                <input type="file" accept="image/*"
                  onChange={e => { const f = e.target.files?.[0]; if (f) onRegFile(f); }} />
                {regPreview
                  ? <img src={regPreview} alt="등록 사진" />
                  : <>
                      <div style={{ fontSize: 40, marginBottom: 8 }}>👤</div>
                      <div>얼굴 사진을 드래그하거나 클릭</div>
                    </>}
              </div>

              <div className={styles.field}>
                <span className={styles.fieldLabel}>이름</span>
                <input placeholder="예: 손흥민" value={regName}
                  onChange={e => setRegName(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') registerFace(); }} />
              </div>

              <button className={styles.btnRegister} onClick={registerFace}
                disabled={!regFile || !regName.trim() || registering}>
                {registering ? '등록 중…' : '등록하기'}
              </button>

              {regStatus && (
                <div className={`${styles.statusMsg} ${regStatus.ok ? styles.statusOk : styles.statusErr}`}>
                  {regStatus.msg}
                </div>
              )}
            </div>

            <div className={styles.faceList}>
              <h2>등록된 얼굴 ({faces.length}명)</h2>
              {faces.length === 0
                ? <div className={styles.empty}>아직 등록된 얼굴이 없습니다.</div>
                : faces.map((name, i) => (
                    <div key={i} className={styles.faceItem}>
                      <span className={styles.faceName}>{name} <span style={{color:'var(--muted)', fontSize:12}}>({faceCounts[name] ?? 1}장)</span></span>
                      <button className={styles.btnDanger} onClick={() => deleteFace(name)}>삭제</button>
                    </div>
                  ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
