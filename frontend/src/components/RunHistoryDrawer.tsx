import React from 'react';
import { X, CheckCircle2, XCircle, AlertTriangle, Clock, RotateCcw } from 'lucide-react';
import type { RunHistoryItem } from '../lib/types';
import { toast } from 'sonner';

interface RunHistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  history: RunHistoryItem[];
  onRestore: (item: RunHistoryItem) => void;
  onClearHistory: () => void;
}

export const RunHistoryDrawer: React.FC<RunHistoryDrawerProps> = ({
  isOpen,
  onClose,
  history,
  onRestore,
  onClearHistory,
}) => {
  if (!isOpen) return null;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'accepted':
        return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />;
      case 'compile_error':
        return <XCircle className="w-3.5 h-3.5 text-red-400" />;
      case 'runtime_error':
        return <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />;
      default:
        return <Clock className="w-3.5 h-3.5 text-amber-400" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex justify-end select-none animate-in fade-in duration-150">
      <div className="w-full max-w-md bg-white dark:bg-dark-card border-l border-slate-300 dark:border-dark-border h-full flex flex-col shadow-2xl">
        {/* Drawer Header */}
        <div className="h-14 px-4 border-b border-slate-300 dark:border-dark-border flex items-center justify-between bg-slate-50 dark:bg-dark-bg/60">
          <div className="flex items-center space-x-2">
            <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100">Run History (Last 10)</h3>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-slate-800 dark:text-slate-300 font-bold">
              {history.length}
            </span>
          </div>
          <div className="flex items-center space-x-1">
            {history.length > 0 && (
              <button
                onClick={() => {
                  onClearHistory();
                  toast.success('Run history cleared');
                }}
                className="text-[11px] text-slate-600 dark:text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 px-2 py-1 rounded transition-colors font-semibold"
              >
                Clear
              </button>
            )}
            <button
              onClick={onClose}
              className="p-1.5 text-slate-500 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-200/70 dark:hover:bg-dark-hover rounded transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Drawer List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-white dark:bg-dark-card">
          {history.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-500 text-xs py-10">
              <Clock className="w-8 h-8 mb-2 stroke-1" />
              <span className="font-medium">No execution runs recorded yet.</span>
            </div>
          ) : (
            history.map((item) => (
              <div
                key={item.id}
                className="bg-slate-50 dark:bg-dark-bg p-3 rounded-lg border border-slate-300 dark:border-dark-border hover:border-slate-400 dark:hover:border-slate-700 transition-colors flex flex-col space-y-2 shadow-sm"
              >
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-1.5">
                    {getStatusIcon(item.status)}
                    <span className="font-bold uppercase tracking-wider text-[11px] text-slate-900 dark:text-slate-200">
                      {item.language}
                    </span>
                    <span className="text-[10px] font-mono text-slate-600 dark:text-slate-400 font-medium">
                      • {item.status.replace('_', ' ')}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono">{item.timestamp}</span>
                </div>

                <pre className="text-[11px] font-mono text-slate-800 dark:text-slate-400 bg-slate-200/70 dark:bg-slate-950 p-2 rounded line-clamp-3 overflow-hidden font-medium">
                  {item.code}
                </pre>

                <div className="flex items-center justify-between pt-1">
                  <div className="flex items-center space-x-2 text-[10px] font-mono text-slate-600 dark:text-slate-400 font-medium">
                    <span>{item.time_ms.toFixed(1)}ms</span>
                    <span>• Eco {item.eco_score}</span>
                  </div>
                  <button
                    onClick={() => {
                      onRestore(item);
                      onClose();
                      toast.success(`Restored ${item.language.toUpperCase()} code from history!`);
                    }}
                    className="flex items-center space-x-1 px-2.5 py-1 rounded bg-indigo-50 dark:bg-slate-800 hover:bg-indigo-600 hover:text-white text-indigo-700 dark:text-slate-300 text-[11px] font-semibold border border-indigo-200 dark:border-transparent transition-colors shadow-sm"
                  >
                    <RotateCcw className="w-3 h-3" />
                    <span>Restore Code</span>
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
