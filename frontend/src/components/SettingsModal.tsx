import React, { useState } from 'react';
import { X, Sparkles, Copy, Check } from 'lucide-react';
import type { Agent, Model } from '../lib/types';
import { toast } from 'sonner';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  models: Model[];
  agents: Agent[];
  agentModelRouting: Record<string, string>;
  onUpdateAgentModelRouting: (routing: Record<string, string>) => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  models,
  agents,
  agentModelRouting,
  onUpdateAgentModelRouting,
}) => {
  const [activeTab, setActiveTab] = useState<'routing' | 'prompts' | 'guide'>('routing');
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleModelChange = (agentId: string, modelTag: string) => {
    onUpdateAgentModelRouting({
      ...agentModelRouting,
      [agentId]: modelTag,
    });
    toast.success(`Updated ${agentId} model to ${modelTag}`);
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCmd(id);
    toast.success('Copied to clipboard!');
    setTimeout(() => setCopiedCmd(null), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 select-none">
      <div className="w-full max-w-2xl bg-dark-card border border-dark-border rounded-xl shadow-2xl flex flex-col max-h-[85vh] overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="h-14 px-5 border-b border-dark-border flex items-center justify-between bg-dark-bg/60">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <h3 className="font-semibold text-sm text-slate-100">Platform Settings & Architecture</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-100 hover:bg-dark-hover rounded-md transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Navigation Tabs */}
        <div className="px-5 border-b border-dark-border bg-dark-bg/40 flex space-x-4 text-xs font-medium">
          <button
            onClick={() => setActiveTab('routing')}
            className={`py-3 border-b-2 transition-colors ${
              activeTab === 'routing'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Model Routing
          </button>
          <button
            onClick={() => setActiveTab('prompts')}
            className={`py-3 border-b-2 transition-colors ${
              activeTab === 'prompts'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Agent Prompts (View Only)
          </button>
          <button
            onClick={() => setActiveTab('guide')}
            className={`py-3 border-b-2 transition-colors ${
              activeTab === 'guide'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Ollama Setup Guide
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-5 flex-1 overflow-y-auto space-y-4 text-xs select-text">
          {/* TAB 1: MODEL ROUTING */}
          {activeTab === 'routing' && (
            <div className="space-y-4">
              <p className="text-slate-400 text-xs">
                Assign specialized LLMs (Llama 3, Microsoft Phi-3, Alibaba Qwen 2.5) to individual multi-agent roles:
              </p>

              <div className="space-y-3">
                {agents.map((agent) => (
                  <div
                    key={agent.id}
                    className="p-3 bg-dark-bg rounded-lg border border-dark-border flex items-center justify-between"
                  >
                    <div className="flex items-center space-x-3">
                      <div
                        className="w-8 h-8 rounded-lg flex items-center justify-center"
                        style={{ backgroundColor: `${agent.accent_color}15`, color: agent.accent_color }}
                      >
                        <Sparkles className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="font-semibold text-slate-200">{agent.name}</div>
                        <div className="text-[11px] text-slate-400">{agent.role}</div>
                      </div>
                    </div>

                    <select
                      value={agentModelRouting[agent.id] || agent.default_model}
                      onChange={(e) => handleModelChange(agent.id, e.target.value)}
                      className="bg-dark-card border border-dark-border rounded-md px-3 py-1.5 text-xs text-slate-100 outline-none focus:border-indigo-500 font-mono"
                    >
                      {models.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.name} ({m.family})
                        </option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 2: AGENT PROMPTS */}
          {activeTab === 'prompts' && (
            <div className="space-y-4">
              <p className="text-slate-400 text-xs">
                Inspect the prompt instructions governing the 4 specialized agents in the APR pipeline:
              </p>

              <div className="space-y-3">
                {agents.map((agent) => (
                  <div key={agent.id} className="bg-dark-bg rounded-lg border border-dark-border overflow-hidden">
                    <div className="px-3 py-2 bg-dark-card/60 border-b border-dark-border font-semibold text-slate-200 flex items-center justify-between">
                      <span style={{ color: agent.accent_color }}>{agent.name}</span>
                      <span className="text-[10px] font-mono text-slate-400">Role: {agent.role}</span>
                    </div>
                    <div className="p-3 font-mono text-[11px] text-slate-300 leading-relaxed bg-slate-950/40 whitespace-pre-wrap">
                      {agent.prompt_template}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 3: OLLAMA SETUP GUIDE */}
          {activeTab === 'guide' && (
            <div className="space-y-4">
              <p className="text-slate-400 text-xs">
                Execute these commands in Windows 11 PowerShell to pull and run local LLMs with Ollama:
              </p>

              <div className="space-y-3 font-mono text-xs">
                <div className="bg-dark-bg p-3 rounded-lg border border-dark-border flex items-center justify-between">
                  <div>
                    <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">1. Start Ollama Daemon</div>
                    <code className="text-emerald-400">ollama serve</code>
                  </div>
                  <button
                    onClick={() => copyToClipboard('ollama serve', 'serve')}
                    className="p-1.5 text-slate-400 hover:text-white rounded hover:bg-dark-hover"
                  >
                    {copiedCmd === 'serve' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>

                <div className="bg-dark-bg p-3 rounded-lg border border-dark-border flex items-center justify-between">
                  <div>
                    <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">2. Pull Microsoft Phi-3 Mini</div>
                    <code className="text-emerald-400">ollama pull phi3:mini</code>
                  </div>
                  <button
                    onClick={() => copyToClipboard('ollama pull phi3:mini', 'phi3')}
                    className="p-1.5 text-slate-400 hover:text-white rounded hover:bg-dark-hover"
                  >
                    {copiedCmd === 'phi3' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>

                <div className="bg-dark-bg p-3 rounded-lg border border-dark-border flex items-center justify-between">
                  <div>
                    <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">3. Pull Alibaba Qwen 2.5 Coder</div>
                    <code className="text-emerald-400">ollama pull qwen2.5:coder</code>
                  </div>
                  <button
                    onClick={() => copyToClipboard('ollama pull qwen2.5:coder', 'qwen')}
                    className="p-1.5 text-slate-400 hover:text-white rounded hover:bg-dark-hover"
                  >
                    {copiedCmd === 'qwen' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>

                <div className="bg-dark-bg p-3 rounded-lg border border-dark-border flex items-center justify-between">
                  <div>
                    <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">4. Pull Meta Llama 3.2 1B</div>
                    <code className="text-emerald-400">ollama pull llama3.2:1b</code>
                  </div>
                  <button
                    onClick={() => copyToClipboard('ollama pull llama3.2:1b', 'llama')}
                    className="p-1.5 text-slate-400 hover:text-white rounded hover:bg-dark-hover"
                  >
                    {copiedCmd === 'llama' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="h-12 px-5 border-t border-dark-border bg-dark-bg/60 flex items-center justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
