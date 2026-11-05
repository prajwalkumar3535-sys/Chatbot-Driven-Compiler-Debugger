import React, { useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  ShieldAlert,
  Sparkles,
  Terminal,
  FileText,
  Copy
} from 'lucide-react';
import type { RunResult } from '../lib/types';
import { toast } from 'sonner';

interface OutputPanelProps {
  stdin: string;
  onStdinChange: (val: string) => void;
  result: RunResult | null;
  isRunning: boolean;
  onAskAIFix: () => void;
}

export const OutputPanel: React.FC<OutputPanelProps> = ({
  stdin,
  onStdinChange,
  result,
  isRunning,
  onAskAIFix,
}) => {
  const [activeTab, setActiveTab] = useState<'output' | 'input'>('output');

  const copyOutput = () => {
    const text = (result?.stdout || '') + '\n' + (result?.stderr || '');
    navigator.clipboard.writeText(text.trim());
    toast.success('Terminal output copied!');
  };

  const getStatusBadge = (res: RunResult) => {
    switch (res.status) {
      case 'accepted':
        return (
          <span className="flex items-center space-x-1.5 px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Accepted</span>
          </span>
        );
      case 'compile_error':
        return (
          <span className="flex items-center space-x-1.5 px-2 py-0.5 rounded text-[11px] font-semibold bg-red-500/10 text-red-400 border border-red-500/20">
            <XCircle className="w-3.5 h-3.5" />
            <span>Compilation Error</span>
          </span>
        );
      case 'runtime_error':
        return (
          <span className="flex items-center space-x-1.5 px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Runtime Crash</span>
          </span>
        );
      case 'time_limit_exceeded':
        return (
          <span className="flex items-center space-x-1.5 px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Clock className="w-3.5 h-3.5" />
            <span>Time Limit Exceeded (10s)</span>
          </span>
        );
      case 'security_blocked':
        return (
          <span className="flex items-center space-x-1.5 px-2 py-0.5 rounded text-[11px] font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Security Blocked (Guardrail)</span>
          </span>
        );
      default:
        return (
          <span className="flex items-center space-x-1.5 px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/20">
            <span>Exit Code {res.exit_code}</span>
          </span>
        );
    }
  };

  const hasError = result && result.status !== 'accepted';

  return (
    <div className="h-full flex flex-col bg-dark-bg border-b border-dark-border select-none">
      {/* Top Header with Tabs */}
      <div className="h-10 px-3 bg-dark-card/60 border-b border-dark-border flex items-center justify-between text-xs">
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setActiveTab('output')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-t font-medium transition-colors ${
              activeTab === 'output'
                ? 'bg-dark-bg border-t-2 border-indigo-500 text-slate-100'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>Output</span>
          </button>
          <button
            onClick={() => setActiveTab('input')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-t font-medium transition-colors ${
              activeTab === 'input'
                ? 'bg-dark-bg border-t-2 border-indigo-500 text-slate-100'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Input (stdin)</span>
            {stdin.trim() && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />}
          </button>
        </div>

        {/* Status Chip & Quick Actions */}
        <div className="flex items-center space-x-2">
          {isRunning && (
            <span className="flex items-center space-x-1.5 text-[11px] text-amber-400 font-mono">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
              <span>Executing...</span>
            </span>
          )}
          {!isRunning && result && getStatusBadge(result)}
          {result && (
            <button
              onClick={copyOutput}
              title="Copy Output"
              className="p-1 text-slate-400 hover:text-slate-100 hover:bg-dark-hover rounded transition-colors"
            >
              <Copy className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Main Panel Body */}
      <div className="flex-1 relative overflow-auto p-3 font-mono text-xs">
        {activeTab === 'input' ? (
          <textarea
            value={stdin}
            onChange={(e) => onStdinChange(e.target.value)}
            placeholder="Type standard input lines here (e.g. test cases, numbers)..."
            className="w-full h-full bg-transparent text-slate-200 placeholder-slate-600 outline-none resize-none font-mono text-xs leading-relaxed"
          />
        ) : (
          <div className="h-full flex flex-col justify-between">
            {/* Terminal Streams */}
            <div className="space-y-2 select-text overflow-auto">
              {!result && !isRunning && (
                <div className="text-slate-500 italic py-4">
                  Hit <kbd className="px-1.5 py-0.5 bg-slate-800 rounded text-slate-400">Run</kbd> or press{' '}
                  <kbd className="px-1.5 py-0.5 bg-slate-800 rounded text-slate-400">Ctrl+Enter</kbd> to compile and execute your program.
                </div>
              )}

              {result && (
                <>
                  {result.stdout && (
                    <div>
                      <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Standard Output</div>
                      <pre className="text-emerald-400 font-mono whitespace-pre-wrap bg-slate-900/40 p-2.5 rounded border border-emerald-500/10 leading-relaxed">
                        {result.stdout}
                      </pre>
                    </div>
                  )}

                  {result.stderr && (
                    <div>
                      <div className="text-[10px] text-rose-400 uppercase tracking-wider mb-1">Error Stream (stderr)</div>
                      <pre className="text-rose-400 font-mono whitespace-pre-wrap bg-rose-950/20 p-2.5 rounded border border-rose-500/20 leading-relaxed">
                        {result.stderr}
                      </pre>
                    </div>
                  )}

                  {!result.stdout && !result.stderr && (
                    <div className="text-slate-500 italic py-2">(Program finished with exit code {result.exit_code} and produced no output)</div>
                  )}
                </>
              )}
            </div>

            {/* Error Quick Action: Ask AI to fix this */}
            {hasError && !isRunning && (
              <div className="mt-3 pt-2 border-t border-dark-border/60 flex items-center justify-between bg-rose-950/20 p-2 rounded border border-rose-500/20">
                <div className="flex items-center space-x-2 text-xs text-rose-300">
                  <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                  <span>
                    {result.error_category ? `Error: ${result.error_category}` : 'Compilation or execution failed.'}
                  </span>
                </div>
                <button
                  onClick={onAskAIFix}
                  className="flex items-center space-x-1.5 px-3 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-md shadow-indigo-600/30 transition-all shrink-0"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Ask AI to Fix This</span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
