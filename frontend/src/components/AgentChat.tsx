import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  GraduationCap,
  Search,
  Wrench,
  ShieldAlert,
  Send,
  Square,
  Sparkles,
  Trash2,
  Copy,
  ArrowRight,
  ShieldCheck,
  Layers,
  Bot
} from 'lucide-react';
import type { Agent, AgentId, ChatMessage, PlatformMode } from '../lib/types';
import { toast } from 'sonner';

interface AgentChatProps {
  agents: Agent[];
  selectedAgent: AgentId;
  onSelectAgent: (agentId: AgentId) => void;
  platformMode: PlatformMode;
  messages: ChatMessage[];
  onSendMessage: (query: string) => void;
  onApplyCode: (code: string) => void;
  onClearChat: () => void;
  isStreaming: boolean;
  onStopStreaming: () => void;
  activeLanguage: string;
}

export const AgentChat: React.FC<AgentChatProps> = ({
  agents,
  selectedAgent,
  onSelectAgent,
  platformMode,
  messages,
  onSendMessage,
  onApplyCode,
  onClearChat,
  isStreaming,
  onStopStreaming,
  activeLanguage,
}) => {
  const [input, setInput] = useState('');
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isStreaming]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isStreaming) return;
    const query = input.trim();
    setInput('');
    onSendMessage(query);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const getAgentIcon = (id: string, className: string = 'w-4 h-4') => {
    switch (id) {
      case 'tutor':
        return <GraduationCap className={className} />;
      case 'detective':
        return <Search className={className} />;
      case 'repair':
        return <Wrench className={className} />;
      case 'security':
        return <ShieldAlert className={className} />;
      default:
        return <Bot className={className} />;
    }
  };

  const quickActions = [
    { label: 'Explain my code', query: 'Please explain the algorithm, logic, and complexity of my current code.' },
    { label: 'Find the bug', query: 'Analyze my code and compiler output. Where is the bug and what causes it?' },
    { label: 'Fix this error', query: 'Fix this compilation/runtime error and provide the complete working code.' },
    { label: 'Security scan', query: 'Run a security audit on this code for buffer overflows, memory safety, and command injection risks.' },
    { label: 'Optimize', query: 'How can I optimize the runtime performance and memory of this program?' },
  ];

  return (
    <div className="flex-1 flex flex-col bg-dark-bg select-none min-h-0">
      {/* Top Header: Agent Segmented Control */}
      <div className="h-12 px-3 bg-dark-card/60 border-b border-dark-border flex items-center justify-between shrink-0">
        {platformMode === 'council' ? (
          <div className="flex items-center space-x-2 text-xs font-semibold text-indigo-400 bg-indigo-500/10 px-3 py-1.5 rounded-md border border-indigo-500/20 w-full justify-between">
            <div className="flex items-center space-x-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              <span>Multi-Model Council (Meta Llama 3 • Microsoft Phi-3 • Alibaba Qwen 2.5)</span>
            </div>
            <span className="text-[10px] font-mono uppercase bg-indigo-500/20 text-indigo-300 px-1.5 py-0.5 rounded">
              Consensus APR
            </span>
          </div>
        ) : (
          <div className="flex items-center space-x-1.5 overflow-x-auto py-1">
            {agents.map((agent) => {
              const isActive = selectedAgent === agent.id;
              return (
                <button
                  key={agent.id}
                  onClick={() => onSelectAgent(agent.id)}
                  title={agent.description}
                  className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all shrink-0 ${
                    isActive
                      ? 'bg-slate-800 text-white shadow-sm ring-1 ring-white/10'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-dark-hover'
                  }`}
                  style={{ borderLeft: isActive ? `3px solid ${agent.accent_color}` : 'none' }}
                >
                  <span style={{ color: agent.accent_color }}>{getAgentIcon(agent.id, 'w-3.5 h-3.5')}</span>
                  <span>{agent.name}</span>
                </button>
              );
            })}
          </div>
        )}

        {messages.length > 0 && (
          <button
            onClick={() => setShowClearConfirm(true)}
            title="Clear Chat History"
            className="p-1.5 text-slate-400 hover:text-slate-100 hover:bg-dark-hover rounded transition-colors ml-2 shrink-0"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Confirmation Dialog for Clearing Chat */}
      {showClearConfirm && (
        <div className="p-2.5 bg-rose-950/40 border-b border-rose-500/30 flex items-center justify-between text-xs text-rose-300">
          <span>Are you sure you want to clear chat history?</span>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => {
                onClearChat();
                setShowClearConfirm(false);
                toast.success('Chat history cleared');
              }}
              className="px-2 py-0.5 rounded bg-rose-600 hover:bg-rose-500 text-white font-medium"
            >
              Clear
            </button>
            <button
              onClick={() => setShowClearConfirm(false)}
              className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Messages Scroll Area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 select-text">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center py-8 text-slate-400 select-none">
            <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-3">
              <Sparkles className="w-6 h-6 text-indigo-400" />
            </div>
            <h4 className="text-sm font-semibold text-slate-200 mb-1">Collaborative Multi-Agent Debugger</h4>
            <p className="text-xs text-slate-500 max-w-sm mb-4">
              Select an agent above or run your code. You can ask for error diagnosis, code fixes, security audits, or conceptual tutoring.
            </p>
            {/* Quick action chips */}
            <div className="flex flex-wrap gap-1.5 justify-center max-w-md">
              {quickActions.map((qa, i) => (
                <button
                  key={i}
                  onClick={() => onSendMessage(qa.query)}
                  className="px-2.5 py-1 rounded-full text-[11px] bg-dark-card border border-dark-border text-slate-300 hover:text-white hover:border-slate-500 transition-colors"
                >
                  {qa.label}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'} space-y-1`}
            >
              <div className="flex items-center space-x-1.5 text-[10px] text-slate-500 font-mono">
                {msg.role === 'user' ? (
                  <span>You</span>
                ) : (
                  <span className="flex items-center space-x-1 text-indigo-400 font-semibold">
                    <Sparkles className="w-3 h-3" />
                    <span>{msg.agent ? msg.agent.toUpperCase() : 'AI TUTOR'}</span>
                    {msg.model && <span className="text-slate-500 font-normal">({msg.model})</span>}
                  </span>
                )}
                <span>• {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
              </div>

              {/* Message Bubble */}
              <div
                className={`max-w-[92%] rounded-xl px-4 py-3 text-xs leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-slate-800 text-slate-100 rounded-tr-none'
                    : 'bg-dark-card border border-dark-border text-slate-200 rounded-tl-none shadow-md'
                }`}
              >
                {/* Multi-Model Council proposals if present */}
                {msg.council_results && msg.council_results.length > 0 ? (
                  <div className="space-y-3 mb-2">
                    <div className="text-[11px] font-semibold text-indigo-300 border-b border-indigo-500/20 pb-1 flex items-center justify-between">
                      <span>Council Proposals Comparison:</span>
                      <span className="text-[10px] text-slate-400 font-normal">3 Models Evaluated</span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                      {msg.council_results.map((cRes, cIdx) => (
                        <div key={cIdx} className="bg-slate-900/60 p-2.5 rounded border border-dark-border flex flex-col justify-between">
                          <div>
                            <div className="flex items-center justify-between mb-1.5">
                              <span className="font-semibold text-[11px] text-slate-200">{cRes.model_name}</span>
                              <span
                                className={`text-[10px] px-1.5 py-0.2 rounded font-mono ${
                                  cRes.is_safe ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
                                }`}
                              >
                                {cRes.is_safe ? 'Verified' : 'Flagged'}
                              </span>
                            </div>
                            <div className="text-[11px] text-slate-300 font-mono line-clamp-4 mb-2">
                              {cRes.content}
                            </div>
                          </div>
                          {cRes.code && (
                            <button
                              onClick={() => {
                                onApplyCode(cRes.code!);
                                toast.success(`Applied ${cRes.model_name} fix to editor!`);
                              }}
                              className="w-full flex items-center justify-center space-x-1 py-1 rounded bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 text-[10px] font-medium transition-colors"
                            >
                              <ArrowRight className="w-3 h-3" />
                              <span>Apply {cRes.model_name}</span>
                            </button>
                          )}
                        </div>
                      ))}
                    </div>

                    {msg.consensus && (
                      <div className="mt-3 pt-2 border-t border-dark-border">
                        <div className="text-[11px] font-semibold text-emerald-400 mb-1 flex items-center space-x-1">
                          <ShieldCheck className="w-3.5 h-3.5" />
                          <span>Council Consensus & Pedagogical Takeaway:</span>
                        </div>
                        <div className="prose prose-invert prose-xs max-w-none text-slate-200">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.consensus}</ReactMarkdown>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="prose prose-invert prose-xs max-w-none text-slate-200">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        code({ node, inline, className, children, ...props }: any) {
                          const match = /language-(\w+)/.exec(className || '');
                          const codeString = String(children).replace(/\n$/, '');

                          if (!inline && match) {
                            return (
                              <div className="my-2 rounded-lg overflow-hidden border border-slate-700 bg-slate-950">
                                <div className="h-7 px-3 bg-slate-900 border-b border-slate-800 flex items-center justify-between text-[11px] text-slate-400 font-mono">
                                  <span>{match[1].toUpperCase()}</span>
                                  <div className="flex items-center space-x-2">
                                    <button
                                      onClick={() => {
                                        navigator.clipboard.writeText(codeString);
                                        toast.success('Code block copied!');
                                      }}
                                      title="Copy code"
                                      className="flex items-center space-x-1 hover:text-slate-100 transition-colors"
                                    >
                                      <Copy className="w-3 h-3" />
                                      <span>Copy</span>
                                    </button>
                                    <button
                                      onClick={() => {
                                        onApplyCode(codeString);
                                        toast.success('Code applied to editor!');
                                      }}
                                      title="Apply directly to editor"
                                      className="flex items-center space-x-1 text-emerald-400 hover:text-emerald-300 font-semibold transition-colors"
                                    >
                                      <ArrowRight className="w-3 h-3" />
                                      <span>Apply to Editor</span>
                                    </button>
                                  </div>
                                </div>
                                <pre className="p-3 text-[11px] font-mono overflow-x-auto text-emerald-300">
                                  <code>{children}</code>
                                </pre>
                              </div>
                            );
                          }
                          return (
                            <code className="px-1 py-0.5 rounded bg-slate-800 text-emerald-300 font-mono text-[11px]" {...props}>
                              {children}
                            </code>
                          );
                        },
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                )}

                {/* Verified Fix Card for Repair Agent */}
                {msg.extracted_code && (
                  <div className="mt-3 pt-2 border-t border-dark-border flex items-center justify-between bg-emerald-950/20 p-2.5 rounded border border-emerald-500/20">
                    <div className="flex items-center space-x-2 text-xs text-emerald-300">
                      <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                      <span>{msg.security_note || 'Verified Safe by 13-Layer Defense'}</span>
                    </div>
                    <button
                      onClick={() => {
                        onApplyCode(msg.extracted_code!);
                        toast.success('Verified fix applied to editor!');
                      }}
                      className="flex items-center space-x-1.5 px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs shadow-md shadow-emerald-600/30 transition-all shrink-0"
                    >
                      <ArrowRight className="w-3.5 h-3.5" />
                      <span>Apply to Editor</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {isStreaming && (
          <div className="flex items-center space-x-2 text-xs text-indigo-400 font-mono py-2">
            <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping" />
            <span>AI agent is generating response...</span>
          </div>
        )}
      </div>

      {/* Input Box Area */}
      <div className="p-3 bg-dark-card/90 border-t border-dark-border shrink-0 select-none">
        <form onSubmit={handleSubmit} className="flex flex-col space-y-2">
          {/* Quick chips below input */}
          <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 text-[11px]">
            {quickActions.slice(0, 3).map((qa, i) => (
              <button
                key={i}
                type="button"
                onClick={() => onSendMessage(qa.query)}
                className="px-2 py-0.5 rounded bg-dark-bg text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-dark-border transition-colors whitespace-nowrap"
              >
                {qa.label}
              </button>
            ))}
          </div>

          <div className="flex items-end space-x-2 bg-dark-bg border border-dark-border rounded-lg p-2 focus-within:border-indigo-500 transition-colors">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={`Ask ${selectedAgent.toUpperCase()} about your ${activeLanguage.toUpperCase()} code... (Enter to send, Shift+Enter for newline)`}
              rows={2}
              className="flex-1 bg-transparent text-slate-200 text-xs placeholder-slate-500 outline-none resize-none font-sans leading-relaxed"
            />
            {isStreaming ? (
              <button
                type="button"
                onClick={onStopStreaming}
                title="Stop generating"
                className="p-2 rounded-md bg-rose-600 hover:bg-rose-500 text-white shadow-md transition-colors"
              >
                <Square className="w-3.5 h-3.5 fill-current" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim()}
                title="Send query"
                className={`p-2 rounded-md transition-all ${
                  input.trim()
                    ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/30'
                    : 'bg-slate-800 text-slate-500 cursor-not-allowed'
                }`}
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};
