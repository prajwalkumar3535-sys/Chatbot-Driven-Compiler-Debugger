import React from 'react';
import {
  Cpu,
  Layers,
  Settings,
  Sun,
  Moon,
  History,
  Terminal,
  ShieldCheck,
  Sparkles,
  ChevronDown
} from 'lucide-react';
import type { Language, Model, PlatformMode, HealthStatus } from '../lib/types';

interface NavbarProps {
  languages: Language[];
  selectedLanguage: string;
  onSelectLanguage: (lang: string) => void;
  platformMode: PlatformMode;
  onSelectPlatformMode: (mode: PlatformMode) => void;
  models: Model[];
  selectedModel: string;
  onSelectModel: (mod: string) => void;
  health: HealthStatus | null;
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
  onOpenSettings: () => void;
  onOpenHistory: () => void;
  historyCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  languages,
  selectedLanguage,
  onSelectLanguage,
  platformMode,
  onSelectPlatformMode,
  models,
  selectedModel,
  onSelectModel,
  health,
  theme,
  onToggleTheme,
  onOpenSettings,
  onOpenHistory,
  historyCount,
}) => {
  const activeSandbox = health?.sandboxes?.[selectedLanguage] || `${selectedLanguage}-sandbox`;

  return (
    <header className="h-14 border-b border-dark-border bg-dark-bg/80 backdrop-blur-md px-4 flex items-center justify-between z-30 select-none">
      {/* Brand Logo & Name */}
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-emerald-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-emerald-500/20">
          <Cpu className="w-5 h-5 text-white" />
        </div>
        <div className="flex flex-col">
          <div className="flex items-center space-x-1.5">
            <span className="font-semibold text-sm tracking-tight text-slate-100">
              Multi-Agent Sandbox
            </span>
            <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              v2.0
            </span>
          </div>
          <span className="text-[10px] text-slate-400 font-mono hidden sm:inline">
            Codeforces • CodeChef • Programiz Standard
          </span>
        </div>
      </div>

      {/* Center Selectors */}
      <div className="flex items-center space-x-2 sm:space-x-3">
        {/* Language Dropdown */}
        <div className="relative flex items-center bg-dark-card border border-dark-border rounded-md px-2.5 py-1 text-xs hover:border-slate-600 transition-colors">
          <Terminal className="w-3.5 h-3.5 text-emerald-400 mr-1.5" />
          <select
            value={selectedLanguage}
            onChange={(e) => onSelectLanguage(e.target.value)}
            className="bg-transparent text-slate-200 outline-none cursor-pointer pr-4 font-medium appearance-none"
          >
            {languages.map((l) => (
              <option key={l.id} value={l.id} className="bg-slate-900 text-slate-100">
                {l.name}
              </option>
            ))}
          </select>
          <ChevronDown className="w-3 h-3 text-slate-400 pointer-events-none absolute right-2" />
        </div>

        {/* Platform Mode Selector */}
        <div className="relative flex items-center bg-dark-card border border-dark-border rounded-md px-2.5 py-1 text-xs hover:border-slate-600 transition-colors">
          <Layers className="w-3.5 h-3.5 text-indigo-400 mr-1.5" />
          <select
            value={platformMode}
            onChange={(e) => onSelectPlatformMode(e.target.value as PlatformMode)}
            className="bg-transparent text-slate-200 outline-none cursor-pointer pr-4 font-medium appearance-none"
          >
            <option value="single" className="bg-slate-900 text-slate-100">
              Single Agent Mode
            </option>
            <option value="council" className="bg-slate-900 text-slate-100">
              🏛️ Multi-Model Council (Llama • Phi-3 • Qwen)
            </option>
          </select>
          <ChevronDown className="w-3 h-3 text-slate-400 pointer-events-none absolute right-2" />
        </div>

        {/* Primary Model Dropdown (when single mode) */}
        {platformMode === 'single' && (
          <div className="relative hidden md:flex items-center bg-dark-card border border-dark-border rounded-md px-2.5 py-1 text-xs hover:border-slate-600 transition-colors">
            <Sparkles className="w-3.5 h-3.5 text-amber-400 mr-1.5" />
            <select
              value={selectedModel}
              onChange={(e) => onSelectModel(e.target.value)}
              className="bg-transparent text-slate-200 outline-none cursor-pointer pr-4 font-medium appearance-none max-w-[160px] truncate"
            >
              {models.map((m) => (
                <option key={m.id} value={m.id} className="bg-slate-900 text-slate-100">
                  {m.name}
                </option>
              ))}
            </select>
            <ChevronDown className="w-3 h-3 text-slate-400 pointer-events-none absolute right-2" />
          </div>
        )}
      </div>

      {/* Far Right Status & Controls */}
      <div className="flex items-center space-x-2">
        {/* Ollama Status Pill */}
        <div
          title={health?.ollama_online ? 'Ollama daemon is active' : 'Ollama is offline. Run `ollama serve`.'}
          className={`flex items-center space-x-1.5 px-2 py-1 rounded-full text-[11px] font-mono border ${
            health?.ollama_online
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
              : 'bg-red-500/10 text-red-400 border-red-500/20'
          }`}
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              health?.ollama_online ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'
            }`}
          />
          <span className="hidden lg:inline">{health?.ollama_online ? 'Ollama Online' : 'Ollama Offline'}</span>
        </div>

        {/* Sandbox Status Pill */}
        <div
          title={`Active Container Engine: ${activeSandbox}`}
          className="hidden xl:flex items-center space-x-1 px-2 py-1 rounded-full text-[11px] font-mono bg-indigo-500/10 text-indigo-300 border border-indigo-500/20"
        >
          <ShieldCheck className="w-3 h-3 text-indigo-400" />
          <span>{activeSandbox}</span>
        </div>

        {/* Run History Trigger */}
        <button
          onClick={onOpenHistory}
          title="Execution Run History"
          className="relative p-1.5 text-slate-400 hover:text-slate-100 hover:bg-dark-hover rounded-md transition-colors"
        >
          <History className="w-4 h-4" />
          {historyCount > 0 && (
            <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-emerald-500 ring-2 ring-dark-bg" />
          )}
        </button>

        {/* Theme Toggle */}
        <button
          onClick={onToggleTheme}
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Theme`}
          className="p-1.5 text-slate-400 hover:text-slate-100 hover:bg-dark-hover rounded-md transition-colors"
        >
          {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-400" />}
        </button>

        {/* Settings Drawer Trigger */}
        <button
          onClick={onOpenSettings}
          title="Open Platform Settings & Setup Guide"
          className="p-1.5 text-slate-400 hover:text-slate-100 hover:bg-dark-hover rounded-md transition-colors"
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
