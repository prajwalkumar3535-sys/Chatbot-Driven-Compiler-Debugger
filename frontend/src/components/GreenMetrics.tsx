import React from 'react';
import {
  Timer,
  HardDrive,
  Zap,
  Globe2,
  Leaf,
  TrendingDown,
  TrendingUp,
  Minus
} from 'lucide-react';
import type { RunResult } from '../lib/types';

interface GreenMetricsProps {
  metrics: RunResult | null;
}

export const GreenMetrics: React.FC<GreenMetricsProps> = ({ metrics }) => {
  // Default values when no run has occurred yet
  const timeMs = metrics?.time_ms ?? 0;
  const memoryKb = metrics?.memory_kb ?? 0;
  const energyWh = metrics?.energy_wh ?? 0;
  const carbonG = metrics?.carbon_g ?? 0;
  const ecoScore = metrics?.eco_score ?? 'A+';
  const ecoLabel = metrics?.eco_label ?? 'Optimal';

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

  return (
    <div className="h-16 px-3 bg-dark-card/90 border-b border-dark-border flex items-center justify-between select-none">
      <div className="grid grid-cols-4 gap-2 flex-1 mr-3">
        {/* Metric 1: Latency */}
        <div className="flex items-center space-x-2 bg-dark-bg/60 px-2.5 py-1.5 rounded-md border border-dark-border/70">
          <div className="p-1 rounded bg-blue-500/10 text-blue-400">
            <Timer className="w-3.5 h-3.5" />
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">Latency</span>
            <div className="flex items-baseline space-x-1">
              <span className="font-mono text-xs font-bold text-slate-100">{timeMs.toFixed(1)}</span>
              <span className="text-[10px] text-slate-500 font-mono">ms</span>
            </div>
            {metrics?.delta_time_ms !== undefined && formatDelta(metrics.delta_time_ms, 'ms')}
          </div>
        </div>

        {/* Metric 2: Memory */}
        <div className="flex items-center space-x-2 bg-dark-bg/60 px-2.5 py-1.5 rounded-md border border-dark-border/70">
          <div className="p-1 rounded bg-purple-500/10 text-purple-400">
            <HardDrive className="w-3.5 h-3.5" />
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">Memory</span>
            <div className="flex items-baseline space-x-1">
              <span className="font-mono text-xs font-bold text-slate-100">{memoryKb.toLocaleString()}</span>
              <span className="text-[10px] text-slate-500 font-mono">KB</span>
            </div>
            <span className="text-[10px] text-slate-500">256MB Cap</span>
          </div>
        </div>

        {/* Metric 3: Energy (Full Un-truncated Wh) */}
        <div className="flex items-center space-x-2 bg-dark-bg/60 px-2.5 py-1.5 rounded-md border border-dark-border/70">
          <div className="p-1 rounded bg-amber-500/10 text-amber-400">
            <Zap className="w-3.5 h-3.5" />
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">Energy Used</span>
            <div className="flex items-baseline space-x-1">
              {/* Full un-truncated number with complete precision */}
              <span className="font-mono text-xs font-bold text-slate-100 truncate" title={`${energyWh} Wh`}>
                {energyWh.toFixed(6)}
              </span>
              <span className="text-[10px] text-slate-500 font-mono">Wh</span>
            </div>
            {metrics?.delta_energy_wh !== undefined && formatDelta(metrics.delta_energy_wh, 'Wh')}
          </div>
        </div>

        {/* Metric 4: Carbon Emitted (Full Un-truncated Grams) */}
        <div className="flex items-center space-x-2 bg-dark-bg/60 px-2.5 py-1.5 rounded-md border border-dark-border/70">
          <div className="p-1 rounded bg-emerald-500/10 text-emerald-400">
            <Globe2 className="w-3.5 h-3.5" />
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">Carbon</span>
            <div className="flex items-baseline space-x-1">
              <span className="font-mono text-xs font-bold text-slate-100 truncate" title={`${carbonG} g CO2eq`}>
                {carbonG.toFixed(6)}
              </span>
              <span className="text-[10px] text-slate-500 font-mono">g</span>
            </div>
            <span className="text-[10px] text-slate-500">Grid ~475g/kWh</span>
          </div>
        </div>
      </div>

      {/* Eco Score Badge */}
      <div className="flex items-center space-x-2 bg-gradient-to-r from-emerald-950/40 to-dark-bg px-3 py-1.5 rounded-md border border-emerald-500/30 shadow-inner">
        <div className="p-1.5 rounded-full bg-emerald-500/20 text-emerald-400 animate-pulse">
          <Leaf className="w-4 h-4" />
        </div>
        <div className="flex flex-col text-right">
          <div className="flex items-center space-x-1">
            <span className="text-[10px] uppercase tracking-wider text-emerald-400 font-semibold">Eco Score</span>
            <span className="font-mono font-black text-sm text-emerald-300 px-1 py-0.2 bg-emerald-500/20 rounded">
              {ecoScore}
            </span>
          </div>
          <span className="text-[10px] text-slate-400 font-medium">{ecoLabel}</span>
        </div>
      </div>
    </div>
  );
};
