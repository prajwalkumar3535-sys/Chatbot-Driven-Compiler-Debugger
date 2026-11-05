import type { Language, Model, Agent, RunResult, HealthStatus } from './types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function fetchLanguages(): Promise<Language[]> {
  const res = await fetch(`${API_BASE}/api/languages`);
  if (!res.ok) throw new Error('Failed to fetch languages');
  return res.json();
}

export async function fetchModels(): Promise<{ models: Model[]; installed_tags: string[]; default_family_models: Record<string, string> }> {
  const res = await fetch(`${API_BASE}/api/models`);
  if (!res.ok) throw new Error('Failed to fetch models');
  return res.json();
}

export async function fetchAgents(): Promise<Agent[]> {
  const res = await fetch(`${API_BASE}/api/agents`);
  if (!res.ok) throw new Error('Failed to fetch agents');
  return res.json();
}

export async function executeCode(language: string, code: string, stdin: string): Promise<RunResult> {
  const res = await fetch(`${API_BASE}/api/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ language, code, stdin }),
  });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Run error (${res.status}): ${errorText}`);
  }
  return res.json();
}

export interface StreamChatParams {
  agent: string;
  mode: string;
  model?: string;
  language: string;
  code: string;
  lastRunOutput: string;
  messages: { role: string; content: string }[];
  signal?: AbortSignal;
  onToken: (token: string, agent?: string) => void;
  onAgentStart?: (agent: string, model: string) => void;
  onAgentDone?: (data: { has_code: boolean; extracted_code?: string; is_safe: boolean; security_note?: string }) => void;
  onModelHeader?: (modelName: string, modelTag: string) => void;
  onModelToken?: (model: string, token: string) => void;
  onModelAudit?: (data: { model: string; is_safe: boolean; note?: string; has_code: boolean }) => void;
  onConsensusToken?: (token: string) => void;
  onDone: () => void;
  onError: (err: Error) => void;
}

export async function streamChat(params: StreamChatParams) {
  const {
    agent,
    mode,
    model,
    language,
    code,
    lastRunOutput,
    messages,
    signal,
    onToken,
    onAgentStart,
    onAgentDone,
    onModelHeader,
    onModelToken,
    onModelAudit,
    onConsensusToken,
    onDone,
    onError
  } = params;

  try {
    const res = await fetch(`${API_BASE}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent,
        mode,
        model,
        language,
        code,
        last_run_output: lastRunOutput,
        messages,
      }),
      signal,
    });

    if (!res.ok || !res.body) {
      throw new Error(`Stream request failed (${res.status})`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      let currentEvent = 'message';
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;

        if (trimmed.startsWith('event:')) {
          currentEvent = trimmed.replace('event:', '').trim();
        } else if (trimmed.startsWith('data:')) {
          const rawData = trimmed.replace('data:', '').trim();
          try {
            const data = JSON.parse(rawData);

            if (currentEvent === 'token') {
              if (data.model && onModelToken) {
                onModelToken(data.model, data.token);
              } else {
                onToken(data.token, data.agent);
              }
            } else if (currentEvent === 'agent_start' && onAgentStart) {
              onAgentStart(data.agent, data.model);
            } else if (currentEvent === 'agent_done' && onAgentDone) {
              onAgentDone(data);
            } else if (currentEvent === 'model_header' && onModelHeader) {
              onModelHeader(data.model_name, data.model_tag);
            } else if (currentEvent === 'model_audit' && onModelAudit) {
              onModelAudit(data);
            } else if (currentEvent === 'consensus_token' && onConsensusToken) {
              onConsensusToken(data.token);
            } else if (currentEvent === 'done') {
              onDone();
            }
          } catch {
            onToken(rawData);
          }
        }
      }
    }
    onDone();
  } catch (err: any) {
    if (err.name === 'AbortError') {
      onDone();
      return;
    }
    onError(err);
  }
}
