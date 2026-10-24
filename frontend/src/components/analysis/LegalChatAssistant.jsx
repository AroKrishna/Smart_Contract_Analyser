import { useState } from 'react';
import { Send, Loader2, Shield } from 'lucide-react';
import Card from '../common/Card';
import Button from '../common/Button';
import { api } from '../../services/api';

const SAMPLE_PROMPTS = [
  'Explain the emergency termination clause in plain terms',
  'Is this contract compliant with GDPR Article 17 (Right to Erasure)?',
  'How can I fix the unbounded fee modification clause?',
  'What makes this exculpatory disclaimer problematic under consumer law?',
];

const LegalChatAssistant = ({ contractId, contractName = 'Contract' }) => {
  const [messages, setMessages] = useState([
    {
      id: 'init-1',
      sender: 'assistant',
      text: `AI Legal Assistant scoped strictly to ${contractName}. I can explain specific clauses, statutory consumer protections, or suggest safer patterns.`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const handleSendMessage = async (textToSend) => {
    const query = textToSend || inputQuery;
    if (!query.trim() || isTyping) return;

    const userMsg = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setIsTyping(true);

    try {
      const response = await api.chatWithAssistant(contractId, query);
      const assistantMsg = {
        id: `asst-${Date.now()}`,
        sender: 'assistant',
        text: response.answer,
        category: response.category,
        isGenerativeAi: Boolean(response.isGenerativeAi),
        engineLabel: response.engineLabel || (response.isGenerativeAi ? 'Generative AI' : 'Deterministic Analysis'),
        sourceEvidence: response.sourceEvidence || response.verifiedFindings || [],
        modelPredictedRisks: response.modelPredictedRisks || [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'assistant',
          text: 'Unable to reach the assistant service. Please ensure the local backend service is running.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <Card
      title="AI Legal Assistant"
      subtitle={`Context-scoped question answering for ${contractName}`}
    >
      <div className="space-y-4 text-[13px]">
        {/* Sample Prompt Chips */}
        <div className="flex flex-wrap gap-1.5">
          {SAMPLE_PROMPTS.map((prompt, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSendMessage(prompt)}
              className="text-[12px] px-2.5 py-1 rounded-[3px] border border-[var(--border)] bg-[var(--surface-subtle)] text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--surface)] transition-colors focus-ring text-left cursor-pointer"
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Messages Stream */}
        <div className="border border-[var(--border)] rounded-[4px] bg-[var(--surface-subtle)] p-4 max-h-[360px] overflow-y-auto space-y-3">
          {messages.map((msg) => {
            const isUser = msg.sender === 'user';
            return (
              <div
                key={msg.id}
                className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-[4px] p-3 border text-[13px] leading-relaxed ${
                    isUser
                      ? 'bg-[var(--accent-tint)] border-[var(--accent)]/30 text-[var(--text-main)]'
                      : 'bg-[var(--surface)] border-[var(--border)] text-[var(--text-main)]'
                  }`}
                >
                  <div className="flex items-center justify-between gap-3 text-[10px] text-[var(--text-muted)] font-mono mb-1 select-none">
                    <span className="font-semibold text-[var(--text-secondary)]">
                      {isUser ? 'You' : 'Assistant'}
                    </span>
                    <span>{msg.timestamp}</span>
                  </div>

                  <p className="whitespace-pre-wrap">{msg.text}</p>

                  {msg.engineLabel && (
                    <div className="mt-2 pt-2 border-t border-[var(--border)] text-[10px] font-mono text-[var(--text-muted)]">
                      Engine: {msg.engineLabel}
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {isTyping && (
            <div className="flex items-center gap-2 p-2.5 rounded-[4px] bg-[var(--surface)] border border-[var(--border)] text-[12px] text-[var(--text-muted)] font-mono">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-[var(--accent)] shrink-0" />
              <span>Analyzing contract context...</span>
            </div>
          )}
        </div>

        {/* Input Form */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder="Ask a question about this contract..."
            className="flex-1 h-[36px] px-3 text-[14px] bg-[var(--surface)] text-[var(--text-main)] placeholder-[var(--text-muted)] border border-[var(--border-strong)] rounded-[4px] focus-ring"
          />
          <Button
            type="submit"
            variant="primary"
            size="md"
            icon={Send}
            disabled={!inputQuery.trim() || isTyping}
          >
            Send
          </Button>
        </form>

        <div className="pt-2 border-t border-[var(--border)] text-[11px] text-[var(--text-muted)] flex items-center gap-1.5">
          <Shield className="w-3.5 h-3.5 text-[var(--text-secondary)] shrink-0" />
          <span>Decision support only. Responses are not authoritative legal counsel.</span>
        </div>
      </div>
    </Card>
  );
};

export default LegalChatAssistant;
