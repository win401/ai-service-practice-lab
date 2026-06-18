'use client';

import { useRef, useState } from 'react';
import styles from './page.module.css';

const API = 'http://127.0.0.1:8000';

const EXAMPLES = [
  '배송이 3일째 오지 않아요. 어떻게 된 건가요?',
  '주문한 상품 주소를 잘못 입력했어요. 변경 가능한가요?',
  '환불 신청했는데 언제 처리되나요?',
  '구매한 지 5일 됐는데 환불 가능한가요?',
  '제품이 켜지지 않아요. 고장난 것 같아요.',
];

type Step = { label: string; done: boolean; time: number | null };

type AgentMessage = {
  type: 'agent';
  category: string;
  agent_name: string;
  agent_emoji: string;
  agent_color: string;
  answer: string;
  steps: Step[];
  classify_time: number;
  total_time: number;
};

type ChatMessage =
  | { type: 'user'; text: string }
  | { type: 'loading' }
  | AgentMessage;

const TAG_CLASS: Record<string, string> = {
  blue:   styles.tagBlue,
  orange: styles.tagOrange,
  purple: styles.tagPurple,
};

const CATEGORY_EMOJI: Record<string, string> = {
  '배송': '🚚',
  '환불': '💰',
  '제품': '📦',
};

const PENDING_STEPS: Step[] = [
  { label: '문의 분류',   done: false, time: null },
  { label: '전문가 배정', done: false, time: null },
  { label: '답변 생성',   done: false, time: null },
];

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [lastResult, setLastResult] = useState<AgentMessage | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () =>
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);

  const send = async (text: string) => {
    if (!text.trim() || loading) return;
    setInput('');
    setLoading(true);

    setMessages(prev => [...prev, { type: 'user', text }, { type: 'loading' }]);
    scrollToBottom();

    try {
      const res = await fetch(`${API}/inquiry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      const agentMsg: AgentMessage = { type: 'agent', ...data };
      setMessages(prev => [...prev.slice(0, -1), agentMsg]);
      setLastResult(agentMsg);
      scrollToBottom();
    } catch (e) {
      setMessages(prev => prev.slice(0, -1));
      alert('오류: ' + (e instanceof Error ? e.message : e));
    } finally {
      setLoading(false);
    }
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input); }
  };

  const panelSteps = lastResult?.steps ?? PENDING_STEPS;

  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <h1>🤖 AI 고객센터</h1>
        <p>CrewAI 멀티에이전트 라우팅 시스템 · 2026-06-18</p>
      </header>

      <div className={styles.workspace}>
        {/* ── 왼쪽: 채팅 ── */}
        <div className={styles.chatPanel}>
          <div className={styles.messages}>
            {messages.length === 0 && (
              <div className={styles.emptyState}>
                <div className={styles.icon}>💬</div>
                <div>고객 문의를 입력하면 AI가 분류 후 전문 에이전트가 답변합니다.</div>
              </div>
            )}

            {messages.map((msg, i) => {
              if (msg.type === 'user') return (
                <div key={i} className={styles.msgUser}>
                  <div className={styles.msgUserBubble}>{msg.text}</div>
                </div>
              );
              if (msg.type === 'loading') return (
                <div key={i} className={styles.msgAgent}>
                  <div className={styles.msgAgentHeader}>
                    <span>🤖</span><span>분석 중…</span>
                  </div>
                  <div className={styles.loadingBubble}>
                    <div className={styles.dot} />
                    <div className={styles.dot} />
                    <div className={styles.dot} />
                  </div>
                </div>
              );
              return (
                <div key={i} className={styles.msgAgent}>
                  <div className={styles.msgAgentHeader}>
                    <span>{msg.agent_emoji}</span>
                    <span>{msg.agent_name}</span>
                  </div>
                  <span className={`${styles.categoryTag} ${TAG_CLASS[msg.agent_color]}`}>
                    {CATEGORY_EMOJI[msg.category]} {msg.category}
                  </span>
                  <div className={styles.msgAgentBubble}>{msg.answer}</div>
                </div>
              );
            })}
            <div ref={bottomRef} />
          </div>

          {/* 예시 버튼 */}
          <div className={styles.examples}>
            {EXAMPLES.map((ex, i) => (
              <button key={i} className={styles.exampleBtn} onClick={() => send(ex)} disabled={loading}>
                {ex.length > 22 ? ex.slice(0, 22) + '…' : ex}
              </button>
            ))}
          </div>

          {/* 입력창 */}
          <div className={styles.inputRow}>
            <textarea
              placeholder="고객 문의를 입력하세요… (Enter 전송 / Shift+Enter 줄바꿈)"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              disabled={loading}
            />
            <button className={styles.sendBtn} onClick={() => send(input)} disabled={!input.trim() || loading}>
              {loading ? '처리 중…' : '전송'}
            </button>
          </div>
        </div>

        {/* ── 오른쪽: 분석 패널 ── */}
        <div className={styles.analysisPanel}>
          <div className={styles.panelLabel}>[ 분석 패널 ]</div>

          {!lastResult && !loading ? (
            <div className={styles.emptyAnalysis}>
              <div style={{ fontSize: 36 }}>📊</div>
              <div>문의를 보내면<br />라우팅 과정이 표시됩니다</div>
            </div>
          ) : (
            <div className={styles.analysisCard}>
              {/* 분류 결과 */}
              <div className={styles.analysisRow}>
                <div className={styles.analysisRowLabel}>분류 결과</div>
                <div className={styles.analysisRowValue}>
                  {lastResult
                    ? <span className={`${styles.categoryTag} ${TAG_CLASS[lastResult.agent_color]}`}>
                        {CATEGORY_EMOJI[lastResult.category]} {lastResult.category}
                      </span>
                    : <span style={{ color: 'var(--muted)' }}>분류 중…</span>}
                </div>
              </div>

              {/* 배정 에이전트 */}
              <div className={styles.analysisRow}>
                <div className={styles.analysisRowLabel}>배정 에이전트</div>
                <div className={styles.analysisRowValue}>
                  {lastResult
                    ? <>{lastResult.agent_emoji} {lastResult.agent_name}</>
                    : <span style={{ color: 'var(--muted)' }}>대기 중…</span>}
                </div>
              </div>

              {/* 처리 단계 */}
              <div className={styles.analysisRow}>
                <div className={styles.analysisRowLabel}>처리 단계</div>
                <div className={styles.steps}>
                  {panelSteps.map((step, i) => (
                    <div key={i} className={`${styles.step} ${step.done ? styles.stepDone : ''}`}>
                      <div className={`${styles.stepIcon} ${step.done ? styles.stepIconDone : loading ? styles.stepIconPending : ''}`}>
                        {step.done ? '✓' : i + 1}
                      </div>
                      {step.label}
                      {step.time && <span className={styles.stepTime}>{step.time}s</span>}
                    </div>
                  ))}
                </div>
              </div>

              {/* 총 소요시간 */}
              {lastResult && (
                <div className={styles.timerRow}>
                  <span>총 처리 시간</span>
                  <span className={styles.timerValue}>{lastResult.total_time}초</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
