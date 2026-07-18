import { useEffect, useRef, useState } from 'react';
import { CHAT_CHIPS } from '../../mocks/chatScripts';
import { useCaseStore } from '../../state/caseStore';
import { getFieldValue } from '../../utils/tab1Field';

export function ChatPane() {
  const address = useCaseStore((s) => getFieldValue(s.caseData.tab1Fields, 'address') || s.caseData.caseId);
  const chatStarted = useCaseStore((s) => s.chatStarted);
  const chatMessages = useCaseStore((s) => s.chatMessages);
  const isTyping = useCaseStore((s) => s.isTyping);
  const selectChip = useCaseStore((s) => s.selectChip);
  const sendFreeText = useCaseStore((s) => s.sendFreeText);

  const [draft, setDraft] = useState('');
  const threadRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (threadRef.current) threadRef.current.scrollTop = threadRef.current.scrollHeight;
  }, [chatMessages, isTyping]);

  function handleSend() {
    const text = draft.trim();
    if (!text) return;
    setDraft('');
    void sendFreeText(text);
  }

  return (
    <div className="chat-pane">
      <div className="pane-head">
        <div className="title">Collateral Assistant</div>
        <div className="sub">{address}</div>
      </div>

      {!chatStarted && (
        <div className="chat-welcome">
          <div className="agent-summary-card">
            <div className="agent-summary-top">
              <span className="welcome-avatar">CO</span>
              <div>
                <div className="welcome-title">Sẵn sàng thẩm định tài sản bảo đảm</div>
                <div className="welcome-text">
                  Tra cứu khu vực, pháp lý, định giá và rủi ro tài sản. Thay đổi chỉ áp dụng sau khi bấm Xác nhận ở từng bước.
                </div>
              </div>
            </div>
          </div>
          <div className="suggest-label">Suggested actions</div>
          <div className="suggest-chips">
            {CHAT_CHIPS.map((chip) => (
              <button key={chip.flow} type="button" className="chip" onClick={() => void selectChip(chip.flow)}>
                {chip.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {chatStarted && (
        <div className="chat-thread" ref={threadRef}>
          {chatMessages.map((m) => (
            <div key={m.id} className={'msg ' + m.role}>
              {m.role !== 'status' && <div className="who">{m.role === 'user' ? 'Bạn' : 'PAA'}</div>}
              {/* eslint-disable-next-line react/no-danger */}
              <div dangerouslySetInnerHTML={{ __html: m.html }} />
            </div>
          ))}
          {isTyping && (
            <div className="msg agent typing">
              <span />
              <span />
              <span />
            </div>
          )}
        </div>
      )}

      <div className="chat-input-bar">
        <input
          className="chat-input"
          placeholder="Nhập câu hỏi hoặc yêu cầu chỉnh sửa cho PAA…"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSend();
          }}
        />
        <button type="button" className="chat-send" onClick={handleSend}>
          ➤
        </button>
      </div>
    </div>
  );
}
