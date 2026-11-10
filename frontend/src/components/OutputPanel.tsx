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
  Copy,
  GitFork,
  Cpu,
  Leaf,
  Timer,
  HardDrive,
  Zap,
  Globe2,
  TrendingDown,
  TrendingUp,
  Minus
} from 'lucide-react';
import type { RunResult, ASTAnalysis } from '../lib/types';
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
  const [activeTab, setActiveTab] = useState<'output' | 'input' | 'ast' | 'metrics'>('output');

  const copyOutput = () => {
    const text = (result?.stdout || '') + '\n' + (result?.stderr || '');
    navigator.clipboard.writeText(text.trim());
    toast.success('Terminal output copied!');
  };

  const copyAST = () => {
    if (result?.ast?.tree_text) {
      navigator.clipboard.writeText(result.ast.tree_text);
      toast.success('AST Syntax Tree copied!');
    }
  };

  const formatDelta = (val?: number, unit: string = '') => {
    if (val === undefined || val === null || val === 0) {
      return (
        <span className="flex items-center text-[10px] text-slate-500">
          <Minus className="w-2.5 h-2.5 mr-0.5" /> same
        </span>
      );
    }
    const isGood = val < 0;
    return (
      <span className={`flex items-center text-[10px] ${isGood ? 'text-emerald-400' : 'text-amber-400'}`}>
        {isGood ? <TrendingDown className="w-2.5 h-2.5 mr-0.5" /> : <TrendingUp className="w-2.5 h-2.5 mr-0.5" />}
        {val > 0 ? `+${val}` : val} {unit}
      </span>
    );
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
  const ast: ASTAnalysis | undefined = result?.ast;

  return (
    <div className="h-full flex flex-col bg-white dark:bg-dark-bg border-b border-slate-300 dark:border-dark-border select-none">
      {/* Top Header with Tabs */}
      <div className="h-10 px-3 bg-slate-100 dark:bg-dark-card/60 border-b border-slate-300 dark:border-dark-border flex items-center justify-between text-xs overflow-x-auto">
        <div className="flex items-center space-x-1">
          {/* Tab 1: Terminal Output */}
          <button
            onClick={() => setActiveTab('output')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-t font-semibold transition-colors ${
              activeTab === 'output'
                ? 'bg-white dark:bg-dark-bg border-t-2 border-indigo-600 dark:border-indigo-500 text-slate-900 dark:text-slate-100 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-200/70 dark:hover:bg-dark-hover'
            }`}
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>Output</span>
          </button>

          {/* Tab 2: Input (stdin) */}
          <button
            onClick={() => setActiveTab('input')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-t font-semibold transition-colors ${
              activeTab === 'input'
                ? 'bg-white dark:bg-dark-bg border-t-2 border-indigo-600 dark:border-indigo-500 text-slate-900 dark:text-slate-100 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-200/70 dark:hover:bg-dark-hover'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Input (stdin)</span>
            {stdin.trim() && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />}
          </button>

          {/* Tab 3: Syntax Tree (AST) */}
          <button
            onClick={() => setActiveTab('ast')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-t font-semibold transition-colors ${
              activeTab === 'ast'
                ? 'bg-white dark:bg-dark-bg border-t-2 border-indigo-600 dark:border-indigo-500 text-slate-900 dark:text-slate-100 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-200/70 dark:hover:bg-dark-hover'
            }`}
          >
            <GitFork className="w-3.5 h-3.5" />
            <span>Syntax Tree (AST)</span>
            {ast && (
              <span className={`w-1.5 h-1.5 rounded-full ${ast.syntax_valid ? 'bg-cyan-500' : 'bg-rose-500'}`} />
            )}
          </button>

          {/* Tab 4: Carbon & Eco Metrics */}
          <button
            onClick={() => setActiveTab('metrics')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-t font-semibold transition-colors ${
              activeTab === 'metrics'
                ? 'bg-white dark:bg-dark-bg border-t-2 border-emerald-600 dark:border-emerald-500 text-emerald-700 dark:text-emerald-400 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-emerald-700 dark:hover:text-emerald-400 hover:bg-slate-200/70 dark:hover:bg-dark-hover'
            }`}
          >
            <Leaf className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            <span>Carbon Metrics</span>
            {result?.eco_score && (
              <span className="text-[10px] font-mono px-1 bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 rounded font-bold">
                {result.eco_score}
              </span>
            )}
          </button>
        </div>

        {/* Status Chip & Quick Actions */}
        <div className="flex items-center space-x-2 shrink-0">
          {isRunning && (
            <span className="flex items-center space-x-1.5 text-[11px] text-amber-600 dark:text-amber-400 font-mono font-bold">
              <span className="w-2 h-2 rounded-full bg-amber-500 animate-ping" />
              <span>Executing...</span>
            </span>
          )}
          {!isRunning && result && getStatusBadge(result)}
          {result && activeTab === 'output' && (
            <button
              onClick={copyOutput}
              title="Copy Output"
              className="p-1 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-200/70 dark:hover:bg-dark-hover rounded transition-colors"
            >
              <Copy className="w-3.5 h-3.5" />
            </button>
          )}
          {ast && activeTab === 'ast' && (
            <button
              onClick={copyAST}
              title="Copy AST"
              className="p-1 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-200/70 dark:hover:bg-dark-hover rounded transition-colors"
            >
              <Copy className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Main Panel Body */}
      <div className="flex-1 relative overflow-auto p-3 font-mono text-xs bg-white dark:bg-dark-bg">
        {/* INPUT TAB */}
        {activeTab === 'input' && (
          <textarea
            value={stdin}
            onChange={(e) => onStdinChange(e.target.value)}
            placeholder="Type standard input lines here (e.g. test cases, numbers)..."
            className="w-full h-full bg-transparent text-slate-900 dark:text-slate-100 placeholder-slate-500 dark:placeholder-slate-500 outline-none resize-none font-mono text-xs leading-relaxed font-medium"
          />
        )}

        {/* OUTPUT TAB */}
        {activeTab === 'output' && (
          <div className="h-full flex flex-col justify-between">
            {/* Terminal Streams */}
            <div className="space-y-2 select-text overflow-auto">
              {!result && !isRunning && (
                <div className="text-slate-600 dark:text-slate-400 font-medium italic py-4">
                  Hit <kbd className="px-1.5 py-0.5 bg-slate-200 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded text-slate-800 dark:text-slate-200 font-semibold">Run</kbd> or press{' '}
                  <kbd className="px-1.5 py-0.5 bg-slate-200 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded text-slate-800 dark:text-slate-200 font-semibold">Ctrl+Enter</kbd> to compile and execute your program.
                </div>
              )}

              {result && (
                <>
                  {result.stdout && (
                    <div>
                      <div className="text-[10px] text-slate-700 dark:text-slate-400 font-bold uppercase tracking-wider mb-1">Standard Output</div>
                      <pre className="text-emerald-800 dark:text-emerald-400 font-mono font-medium whitespace-pre-wrap bg-emerald-50 dark:bg-slate-900/40 p-2.5 rounded border border-emerald-300 dark:border-emerald-500/10 leading-relaxed shadow-sm">
                        {result.stdout}
                      </pre>
                    </div>
                  )}

                  {result.stderr && (
                    <div>
                      <div className="text-[10px] text-rose-700 dark:text-rose-400 font-bold uppercase tracking-wider mb-1">Error Stream (stderr)</div>
                      <pre className="text-rose-800 dark:text-rose-400 font-mono font-medium whitespace-pre-wrap bg-rose-50 dark:bg-rose-950/20 p-2.5 rounded border border-rose-300 dark:border-rose-500/20 leading-relaxed shadow-sm">
                        {result.stderr}
                      </pre>
                    </div>
                  )}

                  {!result.stdout && !result.stderr && (
                    <div className="text-slate-600 dark:text-slate-400 italic py-2">(Program finished with exit code {result.exit_code} and produced no output)</div>
                  )}
                </>
              )}
            </div>

            {/* Error Quick Action: Ask AI to fix this */}
            {hasError && !isRunning && (
              <div className="mt-3 pt-2 border-t border-slate-300 dark:border-dark-border/60 flex items-center justify-between bg-rose-50 dark:bg-rose-950/20 p-2 rounded border border-rose-300 dark:border-rose-500/20">
                <div className="flex items-center space-x-2 text-xs text-rose-800 dark:text-rose-300 font-medium">
                  <AlertTriangle className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0" />
                  <span>
                    {result.error_category ? `Error: ${result.error_category}` : 'Compilation or execution failed.'}
                  </span>
                </div>
                <button
                  onClick={onAskAIFix}
                  className="flex items-center space-x-1.5 px-3 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-md shadow-indigo-600/30 transition-all shrink-0"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Ask AI to Fix This</span>
                </button>
              </div>
            )}
          </div>
        )}

        {/* AST TAB */}
        {activeTab === 'ast' && (
          <div className="h-full flex flex-col space-y-3 select-text overflow-auto">
            {!ast ? (
              <div className="text-slate-500 italic py-6 text-center space-y-2">
                <GitFork className="w-8 h-8 text-slate-600 mx-auto" />
                <p>Run your program to inspect the Abstract Syntax Tree (AST).</p>
                <p className="text-[11px] text-slate-600">The AST is automatically passed to the Detective, Repair, and Council LLMs for faster syntax and logic detection.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {/* AST Metrics Header */}
                <div className="flex flex-wrap items-center justify-between gap-2 p-2.5 rounded bg-slate-50 dark:bg-dark-card border border-slate-300 dark:border-dark-border">
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-0.5 rounded text-[11px] font-bold border ${
                      ast.syntax_valid
                        ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-500/30'
                        : 'bg-rose-500/15 text-rose-700 dark:text-rose-400 border-rose-500/30'
                    }`}>
                      {ast.syntax_valid ? 'AST Valid' : 'Syntax Error'}
                    </span>
                    <span className="text-slate-700 dark:text-slate-400 text-[11px] font-sans font-medium">
                      {ast.language.toUpperCase()} • {ast.node_count} nodes parsed
                    </span>
                  </div>

                  <div className="flex items-center space-x-2 text-[11px] font-mono text-slate-700 dark:text-slate-400 font-semibold">
                    <span className="px-1.5 py-0.5 bg-white dark:bg-dark-bg rounded border border-slate-300 dark:border-dark-border/50">
                      fn: {ast.symbols?.functions?.length || 0}
                    </span>
                    <span className="px-1.5 py-0.5 bg-white dark:bg-dark-bg rounded border border-slate-300 dark:border-dark-border/50">
                      class: {ast.symbols?.classes?.length || 0}
                    </span>
                    <span className="px-1.5 py-0.5 bg-white dark:bg-dark-bg rounded border border-slate-300 dark:border-dark-border/50">
                      branches: {ast.control_flow?.branches || 0}
                    </span>
                    <span className="px-1.5 py-0.5 bg-white dark:bg-dark-bg rounded border border-slate-300 dark:border-dark-border/50">
                      loops: {ast.control_flow?.loops || 0}
                    </span>
                  </div>
                </div>

                {/* Pinpoint Syntax Error Box if Invalid */}
                {!ast.syntax_valid && ast.syntax_error && (
                  <div className="p-2.5 rounded bg-rose-50 dark:bg-rose-950/30 border border-rose-300 dark:border-rose-500/30 text-rose-800 dark:text-rose-300">
                    <div className="flex items-center space-x-1.5 font-bold text-rose-700 dark:text-rose-400 mb-1 text-[11px]">
                      <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                      <span>Line {ast.syntax_error.line}, Col {ast.syntax_error.column}: {ast.syntax_error.message}</span>
                    </div>
                    {ast.syntax_error.snippet && (
                      <pre className="mt-1 text-[11px] text-rose-900 dark:text-rose-200 bg-rose-100/70 dark:bg-black/40 p-2 rounded border border-rose-300 dark:border-rose-500/20 overflow-x-auto whitespace-pre font-mono">
                        {ast.syntax_error.snippet}
                      </pre>
                    )}
                  </div>
                )}

                {/* Rendered Syntax Tree */}
                <div>
                  <div className="text-[10px] text-slate-700 dark:text-slate-400 uppercase tracking-wider mb-1 flex items-center justify-between font-bold">
                    <span>Parsed Hierarchy Tree</span>
                    <span className="text-[10px] text-indigo-600 dark:text-cyan-400 lowercase flex items-center space-x-1 font-sans font-semibold">
                      <Cpu className="w-3 h-3 inline" />
                      <span>Supplied to Multi-Agent LLMs</span>
                    </span>
                  </div>
                  <pre className="font-mono text-emerald-400 text-xs whitespace-pre bg-[#0b1120] p-3 rounded-lg border border-slate-700 leading-relaxed overflow-x-auto max-h-72 shadow-inner">
                    {ast.tree_text}
                  </pre>
                </div>
              </div>
            )}
          </div>
        )}

        {/* CARBON & GREEN METRICS TAB */}
        {activeTab === 'metrics' && (
          <div className="h-full select-text overflow-auto space-y-3 font-sans">
            {/* Top Eco Score Banner */}
            <div className="flex items-center justify-between p-3 rounded-lg bg-gradient-to-r from-emerald-500/10 via-slate-50 to-slate-50 dark:from-emerald-950/30 dark:via-dark-card dark:to-dark-card border border-emerald-500/30">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 rounded-full bg-emerald-500/20 text-emerald-600 dark:text-emerald-400">
                  <Leaf className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-900 dark:text-slate-100">Green Sandbox Rating</div>
                  <div className="text-[11px] text-slate-600 dark:text-slate-400 font-medium">Hardware-monitored energy & carbon emissions tracking</div>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <div className="text-right">
                  <div className="text-[10px] uppercase font-bold text-emerald-700 dark:text-emerald-400 tracking-wider">Eco Score</div>
                  <div className="text-xs font-semibold text-slate-800 dark:text-slate-300">{result?.eco_label || 'Optimal'}</div>
                </div>
                <div className="px-3 py-1 bg-emerald-500/20 border border-emerald-500/40 text-emerald-700 dark:text-emerald-300 rounded font-mono font-black text-xl">
                  {result?.eco_score || 'A+'}
                </div>
              </div>
            </div>

            {/* 4 Cards Grid */}
            <div className="grid grid-cols-2 gap-2.5">
              {/* Card 1: Latency */}
              <div className="p-3 rounded-lg bg-slate-50 dark:bg-dark-card border border-slate-300 dark:border-dark-border flex flex-col justify-between shadow-sm">
                <div className="flex items-center justify-between text-slate-600 dark:text-slate-400 mb-1">
                  <span className="text-[11px] font-bold uppercase tracking-wider">Execution Latency</span>
                  <Timer className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                </div>
                <div className="flex items-baseline space-x-1 my-1">
                  <span className="text-xl font-bold font-mono text-slate-900 dark:text-slate-100">
                    {(result?.time_ms ?? 0).toFixed(1)}
                  </span>
                  <span className="text-xs font-mono text-slate-600 dark:text-slate-400 font-medium">ms</span>
                </div>
                <div className="text-[11px]">
                  {formatDelta(result?.delta_time_ms, 'ms')}
                </div>
              </div>

              {/* Card 2: Memory */}
              <div className="p-3 rounded-lg bg-slate-50 dark:bg-dark-card border border-slate-300 dark:border-dark-border flex flex-col justify-between shadow-sm">
                <div className="flex items-center justify-between text-slate-600 dark:text-slate-400 mb-1">
                  <span className="text-[11px] font-bold uppercase tracking-wider">Peak Memory</span>
                  <HardDrive className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                </div>
                <div className="flex items-baseline space-x-1 my-1">
                  <span className="text-xl font-bold font-mono text-slate-900 dark:text-slate-100">
                    {(result?.memory_kb ?? 0).toLocaleString()}
                  </span>
                  <span className="text-xs font-mono text-slate-600 dark:text-slate-400 font-medium">KB</span>
                </div>
                <div className="text-[11px] text-slate-600 dark:text-slate-500 font-medium">
                  Docker Cgroup cap: 256 MB
                </div>
              </div>

              {/* Card 3: Energy */}
              <div className="p-3 rounded-lg bg-slate-50 dark:bg-dark-card border border-slate-300 dark:border-dark-border flex flex-col justify-between shadow-sm">
                <div className="flex items-center justify-between text-slate-600 dark:text-slate-400 mb-1">
                  <span className="text-[11px] font-bold uppercase tracking-wider">Energy Consumed</span>
                  <Zap className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                </div>
                <div className="flex items-baseline space-x-1 my-1">
                  <span className="text-xl font-bold font-mono text-slate-900 dark:text-slate-100 truncate" title={`${result?.energy_wh ?? 0} Wh`}>
                    {(result?.energy_wh ?? 0).toFixed(6)}
                  </span>
                  <span className="text-xs font-mono text-slate-600 dark:text-slate-400 font-medium">Wh</span>
                </div>
                <div className="text-[11px]">
                  {formatDelta(result?.delta_energy_wh, 'Wh')}
                </div>
              </div>

              {/* Card 4: Carbon */}
              <div className="p-3 rounded-lg bg-slate-50 dark:bg-dark-card border border-slate-300 dark:border-dark-border flex flex-col justify-between shadow-sm">
                <div className="flex items-center justify-between text-slate-600 dark:text-slate-400 mb-1">
                  <span className="text-[11px] font-bold uppercase tracking-wider">Carbon Footprint</span>
                  <Globe2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                </div>
                <div className="flex items-baseline space-x-1 my-1">
                  <span className="text-xl font-bold font-mono text-slate-900 dark:text-slate-100 truncate" title={`${result?.carbon_g ?? 0} g CO2eq`}>
                    {(result?.carbon_g ?? 0).toFixed(6)}
                  </span>
                  <span className="text-xs font-mono text-slate-600 dark:text-slate-400 font-medium">g CO₂e</span>
                </div>
                <div className="text-[11px] text-slate-600 dark:text-slate-500 font-medium">
                  Grid Average: ~475 g/kWh
                </div>
              </div>
            </div>

            {/* Informational Guidance */}
            <div className="p-3 rounded-lg bg-slate-100 dark:bg-dark-card/60 border border-slate-300 dark:border-dark-border text-xs text-slate-700 dark:text-slate-400 leading-relaxed space-y-1">
              <div className="font-bold text-slate-900 dark:text-slate-200 flex items-center space-x-1.5">
                <Leaf className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                <span>Why Software Carbon Tracking Matters</span>
              </div>
              <p>
                Every code execution incurs a real-world energy cost. By measuring CPU cycle duration and memory wattage,
                the Green Sandbox empowers developers to optimize algorithms (e.g. reducing O(N²) loops to O(N log N))
                to directly lower energy consumption and greenhouse gas emissions.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
