import React, { useRef, useState } from 'react';
import Editor from '@monaco-editor/react';
import type { OnMount } from '@monaco-editor/react';
import {
  Play,
  RotateCcw,
  Copy,
  Download,
  Sparkles,
  Trash2,
  FileCode2,
  ZoomIn,
  ZoomOut,
  MapPin
} from 'lucide-react';
import type { Language } from '../lib/types';
import { toast } from 'sonner';

interface CodeEditorProps {
  language: Language;
  code: string;
  onChange: (value: string) => void;
  onRun: () => void;
  onDebugAI: () => void;
  isRunning: boolean;
  theme: 'dark' | 'light';
  fontSize: number;
  onFontSizeChange: (size: number) => void;
  onResetTemplate: () => void;
  onClear: () => void;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({
  language,
  code,
  onChange,
  onRun,
  onDebugAI,
  isRunning,
  theme,
  fontSize,
  onFontSizeChange,
  onResetTemplate,
  onClear,
}) => {
  const [showMinimap, setShowMinimap] = useState(true);
  const editorRef = useRef<any>(null);

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;

    // Ctrl+Enter to Run shortcut
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
      onRun();
    });
  };

  const getMonacoLanguage = (langId: string) => {
    if (langId === 'cpp') return 'cpp';
    if (langId === 'python') return 'python';
    if (langId === 'java') return 'java';
    return 'plaintext';
  };

  const copyCode = () => {
    navigator.clipboard.writeText(code);
    toast.success('Code copied to clipboard!');
  };

  const downloadCode = () => {
    const blob = new Blob([code], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = language.filename;
    link.click();
    URL.revokeObjectURL(url);
    toast.success(`Downloaded ${language.filename}`);
  };

  return (
    <div className="h-full flex flex-col bg-dark-bg border-r border-dark-border select-none">
      {/* File Tab Header */}
      <div className="h-10 px-3 bg-dark-card/60 border-b border-dark-border flex items-center justify-between text-xs">
        {/* Active File Tab */}
        <div className="flex items-center space-x-2 bg-dark-bg px-3 py-1.5 rounded-t-md border-t-2 border-emerald-500 border-x border-dark-border text-slate-100 font-mono text-[12px]">
          <FileCode2 className="w-3.5 h-3.5 text-emerald-400" />
          <span>{language.filename}</span>
        </div>

        {/* Editor Controls */}
        <div className="flex items-center space-x-1 text-slate-400">
          <button
            onClick={() => onFontSizeChange(Math.max(11, fontSize - 1))}
            title="Decrease Font Size"
            className="p-1 hover:text-slate-100 hover:bg-dark-hover rounded transition-colors"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <span className="text-[11px] font-mono px-1 text-slate-300">{fontSize}px</span>
          <button
            onClick={() => onFontSizeChange(Math.min(24, fontSize + 1))}
            title="Increase Font Size"
            className="p-1 hover:text-slate-100 hover:bg-dark-hover rounded transition-colors"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <div className="h-3 w-[1px] bg-dark-border mx-1" />
          <button
            onClick={() => setShowMinimap(!showMinimap)}
            title="Toggle Minimap"
            className={`p-1 rounded transition-colors ${showMinimap ? 'text-emerald-400' : 'hover:text-slate-100'}`}
          >
            <MapPin className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={copyCode}
            title="Copy Code"
            className="p-1 hover:text-slate-100 hover:bg-dark-hover rounded transition-colors"
          >
            <Copy className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={downloadCode}
            title="Download Source Code"
            className="p-1 hover:text-slate-100 hover:bg-dark-hover rounded transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onResetTemplate}
            title="Reset to Starter Template"
            className="p-1 hover:text-slate-100 hover:bg-dark-hover rounded transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Monaco Editor Container */}
      <div className="flex-1 relative overflow-hidden">
        <Editor
          height="100%"
          language={getMonacoLanguage(language.id)}
          value={code}
          theme={theme === 'dark' ? 'vs-dark' : 'light'}
          onChange={(val) => onChange(val || '')}
          onMount={handleEditorDidMount}
          options={{
            fontSize: fontSize,
            fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
            minimap: { enabled: showMinimap },
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            bracketPairColorization: { enabled: true },
            cursorBlinking: 'smooth',
            smoothScrolling: true,
            automaticLayout: true,
            tabSize: 4,
            padding: { top: 12, bottom: 12 },
            renderLineHighlight: 'all',
          }}
        />
      </div>

      {/* Editor Action Bottom Bar */}
      <div className="h-13 px-4 py-2 bg-dark-card/90 border-t border-dark-border flex items-center justify-between">
        <div className="flex items-center space-x-2 text-xs text-slate-400">
          <button
            onClick={onClear}
            title="Clear Editor"
            className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded bg-dark-hover hover:bg-slate-800 text-slate-300 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5 text-slate-400" />
            <span>Clear</span>
          </button>
          <span className="text-[11px] font-mono text-slate-500 hidden sm:inline">
            Shortcuts: <kbd className="px-1 py-0.5 bg-slate-800 rounded text-slate-300">Ctrl+Enter</kbd> to run
          </span>
        </div>

        <div className="flex items-center space-x-2">
          {/* Debug with AI Button */}
          <button
            onClick={onDebugAI}
            title="Analyze code with AI Detective & Sentinel"
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-400 border border-indigo-500/20 text-xs font-medium transition-all"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
            <span>Debug with AI</span>
          </button>

          {/* Big Green Run Button */}
          <button
            onClick={onRun}
            disabled={isRunning}
            className={`flex items-center space-x-2 px-5 py-1.5 rounded-md font-semibold text-xs text-white shadow-lg transition-all ${
              isRunning
                ? 'bg-emerald-700 cursor-not-allowed opacity-80'
                : 'bg-emerald-600 hover:bg-emerald-500 hover:shadow-emerald-500/25 active:scale-95'
            }`}
          >
            {isRunning ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                <span>Running...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Run</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
