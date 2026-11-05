export type PlatformMode = 'single' | 'council';

export type AgentId = 'tutor' | 'detective' | 'repair' | 'security';

export interface Language {
  id: string;
  name: string;
  extension: string;
  filename: string;
  needs_compile: boolean;
  docker_image: string;
  memory_limit: string;
  template: string;
}

export interface Model {
  id: string;
  name: string;
  family: string;
  description: string;
  role_affinity: string;
  pull_cmd: string;
  is_installed: boolean;
}

export interface Agent {
  id: AgentId;
  name: string;
  icon: string;
  role: string;
  accent_color: string;
  default_model: string;
  description: string;
  prompt_template: string;
}

export interface RunResult {
  stdout: string;
  stderr: string;
  compile_output: string;
  exit_code: number;
  status: 'accepted' | 'compile_error' | 'runtime_error' | 'time_limit_exceeded' | 'security_blocked' | 'system_error';
  time_ms: number;
  memory_kb: number;
  energy_wh: number;
  carbon_g: number;
  eco_score: string;
  eco_label: string;
  delta_time_ms?: number;
  delta_energy_wh?: number;
  error_category?: string;
  error_strategy?: string;
}

export interface RunHistoryItem {
  id: string;
  timestamp: string;
  language: string;
  code: string;
  status: string;
  time_ms: number;
  eco_score: string;
}

export interface CouncilModelResult {
  model_name: string;
  model_tag: string;
  content: string;
  is_safe?: boolean;
  note?: string;
  code?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  agent?: AgentId;
  model?: string;
  timestamp: number;
  extracted_code?: string;
  is_safe?: boolean;
  security_note?: string;
  is_streaming?: boolean;
  council_results?: CouncilModelResult[];
  consensus?: string;
}

export interface HealthStatus {
  status: string;
  ollama_online: boolean;
  docker_online: boolean;
  sandboxes: Record<string, string>;
}
