import { useEffect, useRef, useState } from 'react';
import { CHAT_CHIPS } from '../../mocks/chatScripts';
import { useCaseStore } from '../../state/caseStore';

export function ChatPane() {
  const address = useCaseStore((s) => s.caseData.physical.address.value);
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
        <div className="title">Trò chuyện với PAA</div>
        <div className="sub">{address}</div>
      </div>

      {!chatStarted && (
        <div className="chat-welcome">
          <div className="welcome-avatar">🏠</div>
          <div className="welcome-title">Xin chào, tôi là PAA 👋</div>
          <div className="welcome-text">
            Trợ lý thẩm định bất động sản. Tôi có thể tra cứu dữ liệu khu vực, định giá và đánh giá rủi ro giúp bạn.
            Bạn có thể sửa trực tiếp trên form hoặc nhờ tôi sửa qua chat — mọi thay đổi sẽ hiện màu xanh lá sau khi
            bạn bấm Xác nhận ở từng bước.
          </div>
          <div className="suggest-label">Câu hỏi gợi ý</div>
          <div className="suggest-chips">
            {CHAT_CHIPS.map((chip) => (
              <button key={chip.flow} type="button" className="chip" onClick={() => void selectChip(chip.flow)}>
                <span className="ic">{chip.icon}</span>
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
