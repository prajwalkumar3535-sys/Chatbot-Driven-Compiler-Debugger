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
  MapPin,
  Plus,
  X,
  FolderOpen,
  Upload,
  Folder,
  File,
  Edit2
} from 'lucide-react';
import type { Language, EditorFile } from '../lib/types';
import { toast } from 'sonner';

interface CodeEditorProps {
  language: Language;
  files: EditorFile[];
  activeFileId: string;
  onSelectFile: (fileId: string) => void;
  onAddFile: (name?: string, language?: string, content?: string) => void;
  onCloseFile: (fileId: string) => void;
  onRenameFile: (fileId: string, newName: string) => void;
  onCodeChange: (value: string) => void;
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
  files,
  activeFileId,
  onSelectFile,
  onAddFile,
  onCloseFile,
  onRenameFile,
  onCodeChange,
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
  const [showExplorer, setShowExplorer] = useState(false);
  const [folderName, setFolderName] = useState<string | null>(null);
  const [folderFiles, setFolderFiles] = useState<{ name: string; content: string; path: string }[]>([]);
  const [editingTabId, setEditingTabId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');

  const editorRef = useRef<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  const activeFile = files.find((f) => f.id === activeFileId) || files[0];

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;

    // Ctrl+Enter to Run shortcut
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
      onRun();
    });
  };

  const detectLanguageFromFilename = (filename: string): string => {
    const ext = filename.split('.').pop()?.toLowerCase();
    if (ext === 'cpp' || ext === 'cc' || ext === 'cxx' || ext === 'h' || ext === 'hpp') return 'cpp';
    if (ext === 'py') return 'python';
    if (ext === 'java') return 'java';
    return language.id;
  };

  const getMonacoLanguage = (filename: string) => {
    const lang = detectLanguageFromFilename(filename);
    if (lang === 'cpp') return 'cpp';
    if (lang === 'python') return 'python';
    if (lang === 'java') return 'java';
    return 'plaintext';
  };

  const copyCode = () => {
    if (!activeFile) return;
    navigator.clipboard.writeText(activeFile.content);
    toast.success(`Copied ${activeFile.name} to clipboard!`);
  };

  const downloadCode = () => {
    if (!activeFile) return;
    const blob = new Blob([activeFile.content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = activeFile.name;
    link.click();
    URL.revokeObjectURL(url);
    toast.success(`Downloaded ${activeFile.name}`);
  };

  // Open Single or Multiple Files from PC
  const handleOpenFiles = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    if (!selectedFiles || selectedFiles.length === 0) return;

    Array.from(selectedFiles).forEach((file) => {
      const reader = new FileReader();
      reader.onload = (event) => {
        const content = event.target?.result as string;
        const lang = detectLanguageFromFilename(file.name);
        onAddFile(file.name, lang, content);
      };
      reader.readAsText(file);
    });

    toast.success(`Opened ${selectedFiles.length} file(s) from PC`);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // Open Entire Folder from PC
  const handleOpenFolder = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    if (!selectedFiles || selectedFiles.length === 0) return;

    const loadedFiles: { name: string; content: string; path: string }[] = [];
    const rootName = selectedFiles[0].webkitRelativePath.split('/')[0] || 'Project Folder';
    setFolderName(rootName);
    setShowExplorer(true);

    let count = 0;
    Array.from(selectedFiles).forEach((file) => {
      // Filter out non-code or massive files
      const ext = file.name.split('.').pop()?.toLowerCase();
      if (!['cpp', 'h', 'hpp', 'py', 'java', 'txt', 'json', 'md', 'c', 'cs'].includes(ext || '')) {
        return;
      }

      const reader = new FileReader();
      reader.onload = (event) => {
        const content = event.target?.result as string;
        loadedFiles.push({
          name: file.name,
          path: file.webkitRelativePath,
          content,
        });

        // Open first code file into editor tabs
        if (count === 0) {
          const lang = detectLanguageFromFilename(file.name);
          onAddFile(file.name, lang, content);
        }
        count++;
        setFolderFiles([...loadedFiles]);
      };
      reader.readAsText(file);
    });

    toast.success(`Opened folder: ${rootName}`);
    if (folderInputRef.current) folderInputRef.current.value = '';
  };

  const handleStartRename = (file: EditorFile, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingTabId(file.id);
    setEditName(file.name);
  };

  const handleFinishRename = (fileId: string) => {
    if (editName.trim()) {
      onRenameFile(fileId, editName.trim());
    }
    setEditingTabId(null);
  };

  return (
    <div className="h-full flex flex-col bg-white dark:bg-dark-bg border-r border-slate-300 dark:border-dark-border select-none">
      {/* Hidden File Inputs for PC Access */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        className="hidden"
        onChange={handleOpenFiles}
      />
      <input
        ref={folderInputRef}
        type="file"
        // @ts-ignore
        webkitdirectory="true"
        directory="true"
        className="hidden"
        onChange={handleOpenFolder}
      />

      {/* Top File Tab Header with Tab Management */}
      <div className="h-10 px-2 bg-slate-100 dark:bg-dark-card/60 border-b border-slate-300 dark:border-dark-border flex items-center justify-between text-xs">
        {/* Left: Tab List & Add Tab */}
        <div className="flex items-center space-x-1 overflow-x-auto max-w-[65%] py-1">
          {files.map((file) => {
            const isActive = file.id === activeFileId;
            const isEditing = editingTabId === file.id;

            return (
              <div
                key={file.id}
                onClick={() => onSelectFile(file.id)}
                className={`group flex items-center space-x-1.5 px-3 py-1.5 rounded-t font-mono text-[11px] cursor-pointer transition-all border-b-2 shrink-0 ${
                  isActive
                    ? 'bg-white dark:bg-dark-bg border-emerald-600 dark:border-emerald-500 text-slate-900 dark:text-slate-100 font-bold shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-200/70 dark:hover:bg-dark-hover border-transparent'
                }`}
              >
                <FileCode2 className={`w-3.5 h-3.5 ${isActive ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-500'}`} />

                {isEditing ? (
                  <input
                    type="text"
                    value={editName}
                    autoFocus
                    onChange={(e) => setEditName(e.target.value)}
                    onBlur={() => handleFinishRename(file.id)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleFinishRename(file.id);
                      if (e.key === 'Escape') setEditingTabId(null);
                    }}
                    className="bg-white dark:bg-dark-card border border-indigo-500 px-1 py-0 rounded text-slate-900 dark:text-slate-100 outline-none w-24 text-[11px]"
                  />
                ) : (
                  <span
                    onDoubleClick={(e) => handleStartRename(file, e)}
                    title="Double-click to rename"
                    className="truncate max-w-[110px]"
                  >
                    {file.name}
                  </span>
                )}

                {/* Rename Pencil button */}
                {!isEditing && (
                  <button
                    onClick={(e) => handleStartRename(file, e)}
                    className="opacity-0 group-hover:opacity-100 p-0.5 hover:text-slate-900 dark:hover:text-slate-200 text-slate-500 transition-opacity"
                    title="Rename Tab"
                  >
                    <Edit2 className="w-2.5 h-2.5" />
                  </button>
                )}

                {/* Close Tab button */}
                {files.length > 1 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onCloseFile(file.id);
                    }}
                    className="p-0.5 hover:bg-slate-300 dark:hover:bg-slate-700/50 rounded-full text-slate-500 hover:text-rose-500 transition-colors"
                    title="Close Tab"
                  >
                    <X className="w-3 h-3" />
                  </button>
                )}
              </div>
            );
          })}

          {/* Plus Add Tab Button */}
          <button
            onClick={() => onAddFile()}
            title="Create New Tab"
            className="flex items-center space-x-1 px-2 py-1.5 rounded text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-200/70 dark:hover:bg-dark-hover transition-colors font-semibold text-xs shrink-0"
          >
            <Plus className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            <span className="text-[11px]">Tab</span>
          </button>
        </div>

        {/* Right: PC Open Options & Editor Controls */}
        <div className="flex items-center space-x-1 text-slate-600 dark:text-slate-400 shrink-0">
          {/* Open File from PC */}
          <button
            onClick={() => fileInputRef.current?.click()}
            title="Open File(s) from PC"
            className="flex items-center space-x-1 px-2 py-1 text-xs rounded hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-200/70 dark:hover:bg-dark-hover text-slate-700 dark:text-slate-300 transition-colors font-medium"
          >
            <Upload className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
            <span className="text-[11px] hidden sm:inline">Open File</span>
          </button>

          {/* Open Folder from PC */}
          <button
            onClick={() => folderInputRef.current?.click()}
            title="Open Folder from PC"
            className="flex items-center space-x-1 px-2 py-1 text-xs rounded hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-200/70 dark:hover:bg-dark-hover text-slate-700 dark:text-slate-300 transition-colors font-medium"
          >
            <FolderOpen className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
            <span className="text-[11px] hidden sm:inline">Open Folder</span>
          </button>

          {folderFiles.length > 0 && (
            <button
              onClick={() => setShowExplorer(!showExplorer)}
              title="Toggle Folder Explorer Sidebar"
              className={`p-1 rounded transition-colors ${showExplorer ? 'text-amber-600 dark:text-amber-400 bg-amber-500/15' : 'hover:text-slate-900 dark:hover:text-slate-100'}`}
            >
              <Folder className="w-3.5 h-3.5" />
            </button>
          )}

          <div className="h-3 w-[1px] bg-slate-300 dark:bg-dark-border mx-1" />

          {/* Font Scaling */}
          <button
            onClick={() => onFontSizeChange(Math.max(11, fontSize - 1))}
            title="Decrease Font Size"
            className="p-1 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-200/70 dark:hover:bg-dark-hover rounded transition-colors text-slate-700 dark:text-slate-300"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <span className="text-[11px] font-mono px-0.5 text-slate-900 dark:text-slate-200 font-bold">{fontSize}px</span>
          <button
            onClick={() => onFontSizeChange(Math.min(24, fontSize + 1))}
            title="Increase Font Size"
            className="p-1 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-200/70 dark:hover:bg-dark-hover rounded transition-colors text-slate-700 dark:text-slate-300"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>

          <div className="h-3 w-[1px] bg-slate-300 dark:bg-dark-border mx-1" />

          {/* Minimap Toggle */}
          <button
            onClick={() => setShowMinimap(!showMinimap)}
            title="Toggle Minimap"
            className={`p-1 rounded transition-colors ${showMinimap ? 'text-emerald-600 dark:text-emerald-400 font-bold' : 'hover:text-slate-900 dark:hover:text-slate-100 text-slate-700 dark:text-slate-300'}`}
          >
            <MapPin className="w-3.5 h-3.5" />
          </button>

          {/* Copy Code */}
          <button
            onClick={copyCode}
            title="Copy Code"
            className="p-1 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-200/70 dark:hover:bg-dark-hover rounded transition-colors text-slate-700 dark:text-slate-300"
          >
            <Copy className="w-3.5 h-3.5" />
          </button>

          {/* Download Code */}
          <button
            onClick={downloadCode}
            title="Download Source Code"
            className="p-1 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-200/70 dark:hover:bg-dark-hover rounded transition-colors text-slate-700 dark:text-slate-300"
          >
            <Download className="w-3.5 h-3.5" />
          </button>

          {/* Reset Template */}
          <button
            onClick={onResetTemplate}
            title="Reset to Starter Template"
            className="p-1 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-200/70 dark:hover:bg-dark-hover rounded transition-colors text-slate-700 dark:text-slate-300"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Body: Monaco Editor + Optional Folder Explorer Sidebar */}
      <div className="flex-1 relative overflow-hidden flex">
        {/* Folder Explorer Sidebar (if folder opened) */}
        {showExplorer && folderFiles.length > 0 && (
          <div className="w-52 h-full bg-slate-50 dark:bg-dark-card border-r border-slate-300 dark:border-dark-border flex flex-col shrink-0 text-xs">
            <div className="p-2 border-b border-slate-300 dark:border-dark-border flex items-center justify-between font-bold text-slate-800 dark:text-slate-200">
              <div className="flex items-center space-x-1.5 truncate">
                <Folder className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 shrink-0" />
                <span className="truncate">{folderName || 'Folder'}</span>
              </div>
              <button
                onClick={() => setShowExplorer(false)}
                className="p-1 hover:text-slate-900 dark:hover:text-slate-100 text-slate-500 rounded"
              >
                <X className="w-3 h-3" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-1.5 space-y-0.5">
              {folderFiles.map((ff, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    const lang = detectLanguageFromFilename(ff.name);
                    onAddFile(ff.name, lang, ff.content);
                  }}
                  className="w-full text-left px-2 py-1 rounded text-[11px] font-mono text-slate-700 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-200/70 dark:hover:bg-dark-hover flex items-center space-x-1.5 truncate transition-colors"
                >
                  <File className="w-3 h-3 text-slate-500 shrink-0" />
                  <span className="truncate">{ff.name}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Monaco Editor Container */}
        <div className="flex-1 relative overflow-hidden bg-white dark:bg-dark-bg">
          <Editor
            height="100%"
            language={getMonacoLanguage(activeFile?.name || language.filename)}
            value={activeFile?.content || ''}
            theme={theme === 'dark' ? 'vs-dark' : 'light'}
            onChange={(val) => onCodeChange(val || '')}
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
      </div>

      {/* Editor Action Bottom Bar */}
      <div className="h-13 px-4 py-2 bg-slate-100 dark:bg-dark-card/90 border-t border-slate-300 dark:border-dark-border flex items-center justify-between">
        <div className="flex items-center space-x-2 text-xs text-slate-600 dark:text-slate-400">
          <button
            onClick={onClear}
            title="Clear Current Tab"
            className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded bg-slate-200 dark:bg-dark-hover hover:bg-slate-300 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200 font-medium transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5 text-slate-600 dark:text-slate-400" />
            <span>Clear</span>
          </button>
          <span className="text-[11px] font-mono text-slate-600 dark:text-slate-400 font-medium hidden sm:inline">
            Shortcuts: <kbd className="px-1 py-0.5 bg-slate-200 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded text-slate-800 dark:text-slate-300 font-semibold">Ctrl+Enter</kbd> to run
          </span>
        </div>

        <div className="flex items-center space-x-2">
          {/* Debug with AI Button */}
          <button
            onClick={onDebugAI}
            title="Analyze active tab with AI Detective & Sentinel"
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-indigo-50 dark:bg-indigo-600/10 hover:bg-indigo-100 dark:hover:bg-indigo-600/20 text-indigo-700 dark:text-indigo-400 border border-indigo-300 dark:border-indigo-500/20 text-xs font-semibold transition-all shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400 animate-pulse" />
            <span>Debug with AI</span>
          </button>

          {/* Big Green Run Button */}
          <button
            onClick={onRun}
            disabled={isRunning}
            className={`flex items-center space-x-2 px-5 py-1.5 rounded-md font-bold text-xs text-white shadow-lg transition-all ${
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
