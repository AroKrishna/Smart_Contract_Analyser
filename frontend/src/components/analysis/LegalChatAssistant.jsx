import { useState } from 'react';
import {
  Send,
  Bot,
  User,
  Sparkles,
  ShieldCheck,
  Loader2,
} from 'lucide-react';
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
      text: `Hello! I am your AI Legal Assistant, strictly scoped to **${contractName}**. I can explain specific clauses in plain language, evaluate statutory compliance (GDPR / Consumer Protection), or suggest safer legal standard clauses. How can I assist you?`,
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
        engineLabel: response.engineLabel || (response.isGenerativeAi ? 'Generative AI (External LLM)' : 'Limited Offline Explanation (Deterministic Analysis)'),
        sourceEvidence: response.sourceEvidence || response.verifiedFindings || [],
        modelPredictedRisks: response.modelPredictedRisks || [],
        remediation: response.remediation,
        disclaimer: response.disclaimer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const errorMsg = {
        id: `err-${Date.now()}`,
        sender: 'assistant',
        text: `Unable to process query: ${err.message}. Please verify the analysis backend is running.`,
        isError: true,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <Card className="border-slate-800 bg-slate-900/60 p-5 space-y-4">
      {/* Assistant Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-blue-600/10 border border-blue-500/20 text-blue-400">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              Interactive AI Legal Assistant
              <span className="px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[10px] font-mono">
                Scoped to {contractName}
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Context-grounded legal inquiry and clause remediation assistant
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1 text-[11px] text-slate-400">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Strict Contract Isolation</span>
        </div>
      </div>

      {/* Suggested Quick Prompt Chips */}
      <div className="flex flex-wrap items-center gap-2 pt-1">
        <span className="text-[11px] text-slate-400 flex items-center gap-1 mr-1">
          <Sparkles className="w-3 h-3 text-amber-400" /> Suggested queries:
        </span>
        {SAMPLE_PROMPTS.map((prompt, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => handleSendMessage(prompt)}
            className="text-[11px] px-2.5 py-1 rounded-full bg-slate-950/80 border border-slate-800 text-slate-300 hover:text-white hover:border-blue-500/50 hover:bg-slate-900 transition-colors"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Message History Feed */}
      <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4 min-h-[260px] max-h-[420px] overflow-y-auto space-y-4 text-xs font-sans">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start gap-2.5 ${
              msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'
            }`}
          >
            <div
              className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-xs font-semibold ${
                msg.sender === 'user'
                  ? 'bg-blue-600/30 border border-blue-500/40 text-blue-300'
                  : 'bg-emerald-600/20 border border-emerald-500/30 text-emerald-400'
              }`}
            >
              {msg.sender === 'user' ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
            </div>

            <div
              className={`max-w-[85%] rounded-xl p-3.5 space-y-2.5 ${
                msg.sender === 'user'
                  ? 'bg-blue-600 text-white rounded-tr-none'
                  : 'bg-slate-900/90 border border-slate-800 text-slate-200 rounded-tl-none'
              } ${msg.isError ? 'border-red-500/30 text-red-300 bg-red-950/20' : ''}`}
            >
              <div className="flex items-center justify-between gap-4 text-[10px] opacity-75">
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="font-semibold">
                    {msg.sender === 'user' ? 'You' : 'AI Legal Assistant'}
                  </span>
                  {msg.category && (
                    <span className="px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 font-mono">
                      {msg.category}
                    </span>
                  )}
                  {msg.sender === 'assistant' && !msg.isError && (
                    <span
                      className={`px-1.5 py-0.2 rounded font-mono text-[9px] border ${
                        msg.isGenerativeAi
                          ? 'bg-purple-500/10 border-purple-500/30 text-purple-300'
                          : 'bg-blue-500/10 border-blue-500/30 text-blue-300'
                      }`}
                    >
                      {msg.engineLabel || (msg.isGenerativeAi ? 'Generative AI' : 'Deterministic Legal KB')}
                    </span>
                  )}
                </div>
                <span>{msg.timestamp}</span>
              </div>

              {/* Source Evidence & Contract Indicators Section */}
              {msg.sourceEvidence && msg.sourceEvidence.length > 0 && (
                <div className="bg-slate-950/80 rounded-lg p-2.5 border border-slate-800 text-[11px] space-y-1">
                  <div className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-1">
                    <ShieldCheck className="w-3 h-3" /> Source Evidence & Contract Indicators ({msg.sourceEvidence.length})
                  </div>
                  {msg.sourceEvidence.map((f, i) => (
                    <div key={i} className="text-slate-300">
                      • <span className="font-semibold text-slate-200">[{f.category || 'Observation'}]</span>: {f.description} {f.lineStart ? `(Lines ${f.lineStart}-${f.lineEnd})` : ''}
                    </div>
                  ))}
                </div>
              )}

              {/* Assistant-Generated Explanation */}
              <div className="space-y-1">
                {msg.sender === 'assistant' && !msg.isError && (
                  <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                    {msg.isGenerativeAi ? '🤖 Generative AI Explanation (External LLM)' : '📋 Assistant-Generated Explanation (Limited Offline)'}
                  </div>
                )}
                <p className="whitespace-pre-line leading-relaxed">{msg.text}</p>
              </div>

              {/* Remediation Block */}
              {msg.remediation && (
                <div className="bg-blue-950/40 rounded-lg p-2.5 border border-blue-500/25 text-[11px] text-blue-200">
                  <span className="font-semibold text-blue-300">💡 Remediation: </span>
                  {msg.remediation}
                </div>
              )}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex items-center gap-2 text-slate-400 text-xs italic">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400" />
            <span>AI Legal Assistant is evaluating clause semantics...</span>
          </div>
        )}
      </div>

      {/* Input bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSendMessage();
        }}
        className="flex items-center gap-2"
      >
        <input
          type="text"
          placeholder="Ask a question about this contract's clauses, risks, or compliance..."
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          disabled={isTyping}
          className="flex-1 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 px-3.5 py-2.5 focus:outline-none focus:border-blue-500 placeholder-slate-500"
        />
        <Button
          type="submit"
          variant="primary"
          size="sm"
          icon={Send}
          isLoading={isTyping}
          disabled={!inputQuery.trim() || isTyping}
        >
          Send
        </Button>
      </form>
    </Card>
  );
};

export default LegalChatAssistant;
