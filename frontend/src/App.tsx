import { useState, useEffect, useRef } from 'react';
import { Group, Panel, Separator } from 'react-resizable-panels';
import { Toaster, toast } from 'sonner';
import { Navbar } from './components/Navbar';
import { CodeEditor } from './components/CodeEditor';
import { OutputPanel } from './components/OutputPanel';
import { GreenMetrics } from './components/GreenMetrics';
import { AgentChat } from './components/AgentChat';
import { SettingsModal } from './components/SettingsModal';
import { RunHistoryDrawer } from './components/RunHistoryDrawer';
import type {
  Language,
  Model,
  Agent,
  AgentId,
  PlatformMode,
  RunResult,
  RunHistoryItem,
  ChatMessage,
  HealthStatus,
  CouncilModelResult
} from './lib/types';
import {
  fetchHealth,
  fetchLanguages,
  fetchModels,
  fetchAgents,
  executeCode,
  streamChat
} from './lib/api';

const DEFAULT_LANGUAGES: Language[] = [
  {
    id: 'cpp',
    name: 'C++',
    extension: '.cpp',
    filename: 'main.cpp',
    needs_compile: true,
    docker_image: 'cpp-sandbox',
    memory_limit: '256m',
    template: `#include <iostream>
using namespace std;

int main() {
    cout << "Hello from C++ Sandbox!" << endl;
    return 0;
}`,
  },
  {
    id: 'python',
    name: 'Python',
    extension: '.py',
    filename: 'main.py',
    needs_compile: false,
    docker_image: 'python-sandbox',
    memory_limit: '256m',
    template: `# Python Execution
print("Hello from Python Sandbox!")
`,
  },
  {
    id: 'java',
    name: 'Java',
    extension: '.java',
    filename: 'Main.java',
    needs_compile: true,
    docker_image: 'java-sandbox',
    memory_limit: '256m',
    template: `public class Main {
    public static void main(String[] args) {
        System.out.println("Hello from Java Sandbox!");
    }
}`,
  },
];

const DEFAULT_MODELS: Model[] = [
  {
    id: 'qwen2.5:coder',
    name: 'Qwen 2.5 Coder 7B',
    family: 'Qwen',
    description: '💻 Alibaba SOTA code synthesis & repair',
    role_affinity: 'RepairAgent',
    pull_cmd: 'ollama pull qwen2.5:coder',
    is_installed: false,
  },
  {
    id: 'phi3:mini',
    name: 'Phi-3 Mini 3.8B',
    family: 'Phi-3',
    description: '🔬 Microsoft 3.8B high-density logical reasoning',
    role_affinity: 'DiagnosticAgent',
    pull_cmd: 'ollama pull phi3:mini',
    is_installed: false,
  },
  {
    id: 'llama3.2:1b',
    name: 'Llama 3.2 1B',
    family: 'Llama',
    description: '⚡ Ultra-fast 1B triage & security checks',
    role_affinity: 'SecurityAuditorAgent',
    pull_cmd: 'ollama pull llama3.2:1b',
    is_installed: false,
  },
];

const DEFAULT_AGENTS: Agent[] = [
  {
    id: 'tutor',
    name: 'Tutor Mentor',
    icon: 'GraduationCap',
    role: 'Pedagogical Mentor 🎓',
    accent_color: '#10b981',
    default_model: 'phi3:mini',
    description: 'Explains error mechanics, programming concepts, and Big-O complexity.',
    prompt_template: 'Friendly pedagogical tutoring explaining concepts clearly.',
  },
  {
    id: 'detective',
    name: 'Detective Agent',
    icon: 'Search',
    role: 'Error Detective 🔍',
    accent_color: '#3b82f6',
    default_model: 'phi3:mini',
    description: 'Fault localization specialist pinpointing line numbers and root compiler errors.',
    prompt_template: 'Crisp technical error localization and syntax/runtime analysis.',
  },
  {
    id: 'repair',
    name: 'Repair Agent',
    icon: 'Wrench',
    role: 'Code Architect 🛠️',
    accent_color: '#8b5cf6',
    default_model: 'qwen2.5:coder',
    description: 'Synthesizes minimal, clean, and bug-free code patches.',
    prompt_template: 'Precision code synthesis preserving original naming and intent.',
  },
  {
    id: 'security',
    name: 'Security Sentinel',
    icon: 'ShieldAlert',
    role: 'Security Sentinel 🛡️',
    accent_color: '#ef4444',
    default_model: 'llama3.2:1b',
    description: 'Enforces 13-layer defense checking memory vulnerabilities and dangerous APIs.',
    prompt_template: 'Automated 13-layer security audit checking OWASP/CWE standards.',
  },
];

export function App() {
  // Theme state
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    return (localStorage.getItem('sandbox_theme') as 'dark' | 'light') || 'dark';
  });

  // Languages & Selected Language
  const [languages, setLanguages] = useState<Language[]>(DEFAULT_LANGUAGES);
  const [selectedLanguage, setSelectedLanguage] = useState<string>(() => {
    return localStorage.getItem('sandbox_lang') || 'cpp';
  });

  // Code state per language
  const [codePerLang, setCodePerLang] = useState<Record<string, string>>(() => {
    const saved = localStorage.getItem('sandbox_code_store');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {}
    }
    return {
      cpp: DEFAULT_LANGUAGES[0].template,
      python: DEFAULT_LANGUAGES[1].template,
      java: DEFAULT_LANGUAGES[2].template,
    };
  });

  // Editor font size
  const [fontSize, setFontSize] = useState<number>(() => {
    const saved = localStorage.getItem('sandbox_font_size');
    return saved ? parseInt(saved, 10) : 13;
  });

  // Stdin state
  const [stdin, setStdin] = useState<string>('');

  // Execution state
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [result, setResult] = useState<RunResult | null>(null);

  // Platform Mode & Models
  const [platformMode, setPlatformMode] = useState<PlatformMode>(() => {
    return (localStorage.getItem('sandbox_platform_mode') as PlatformMode) || 'single';
  });
  const [models, setModels] = useState<Model[]>(DEFAULT_MODELS);
  const [selectedModel, setSelectedModel] = useState<string>(() => {
    return localStorage.getItem('sandbox_model') || 'qwen2.5:coder';
  });

  // Multi-Agent states
  const [agents, setAgents] = useState<Agent[]>(DEFAULT_AGENTS);
  const [selectedAgent, setSelectedAgent] = useState<AgentId>(() => {
    return (localStorage.getItem('sandbox_agent') as AgentId) || 'tutor';
  });
  const [agentModelRouting, setAgentModelRouting] = useState<Record<string, string>>({
    detective: 'phi3:mini',
    repair: 'qwen2.5:coder',
    security: 'llama3.2:1b',
    tutor: 'phi3:mini',
  });

  // Chat messages
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    const saved = localStorage.getItem('sandbox_chat_history');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {}
    }
    return [];
  });
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Health and Drawers
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState<boolean>(false);
  const [runHistory, setRunHistory] = useState<RunHistoryItem[]>(() => {
    const saved = localStorage.getItem('sandbox_run_history');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {}
    }
    return [];
  });

  // Mobile layout tab
  const [mobileTab, setMobileTab] = useState<'editor' | 'output' | 'chat'>('editor');

  // Persistence side effects
  useEffect(() => {
    localStorage.setItem('sandbox_theme', theme);
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
      document.documentElement.classList.remove('light');
    } else {
      document.documentElement.classList.add('light');
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  useEffect(() => {
    localStorage.setItem('sandbox_lang', selectedLanguage);
  }, [selectedLanguage]);

  useEffect(() => {
    localStorage.setItem('sandbox_code_store', JSON.stringify(codePerLang));
  }, [codePerLang]);

  useEffect(() => {
    localStorage.setItem('sandbox_platform_mode', platformMode);
  }, [platformMode]);

  useEffect(() => {
    localStorage.setItem('sandbox_model', selectedModel);
  }, [selectedModel]);

  useEffect(() => {
    localStorage.setItem('sandbox_agent', selectedAgent);
  }, [selectedAgent]);

  useEffect(() => {
    localStorage.setItem('sandbox_font_size', fontSize.toString());
  }, [fontSize]);

  useEffect(() => {
    localStorage.setItem('sandbox_chat_history', JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    localStorage.setItem('sandbox_run_history', JSON.stringify(runHistory));
  }, [runHistory]);

  // Initial Data Fetch
  useEffect(() => {
    const loadMetadata = async () => {
      try {
        const [healthData, langsData, modelsData, agentsData] = await Promise.allSettled([
          fetchHealth(),
          fetchLanguages(),
          fetchModels(),
          fetchAgents(),
        ]);

        if (healthData.status === 'fulfilled') setHealth(healthData.value);
        if (langsData.status === 'fulfilled' && langsData.value.length > 0) setLanguages(langsData.value);
        if (modelsData.status === 'fulfilled' && modelsData.value.models.length > 0) setModels(modelsData.value.models);
        if (agentsData.status === 'fulfilled' && agentsData.value.length > 0) setAgents(agentsData.value);
      } catch (err) {
        console.error('Failed to load initial metadata', err);
      }
    };

    loadMetadata();
    const interval = setInterval(async () => {
      try {
        const h = await fetchHealth();
        setHealth(h);
      } catch {}
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const currentLangObj = languages.find((l) => l.id === selectedLanguage) || DEFAULT_LANGUAGES[0];
  const currentCode = codePerLang[selectedLanguage] || currentLangObj.template;

  // Handle Run
  const handleRun = async () => {
    if (isRunning) return;
    setIsRunning(true);
    setMobileTab('output');

    try {
      const res = await executeCode(selectedLanguage, currentCode, stdin);
      setResult(res);

      const historyEntry: RunHistoryItem = {
        id: Math.random().toString(36).substring(7),
        timestamp: new Date().toLocaleTimeString(),
        language: selectedLanguage,
        code: currentCode,
        status: res.status,
        time_ms: res.time_ms,
        eco_score: res.eco_score,
      };

      setRunHistory((prev) => [historyEntry, ...prev.slice(0, 9)]);

      if (res.status === 'accepted') {
        toast.success(`Execution Succeeded in ${res.time_ms.toFixed(1)}ms!`);
      } else if (res.status === 'security_blocked') {
        toast.error('Security Guardrail Blocked Dangerous Payload!');
      } else {
        toast.error(`Execution failed (${res.status.replace('_', ' ')})`);
      }
    } catch (err: any) {
      toast.error(err.message || 'Execution error');
      setResult({
        stdout: '',
        stderr: err.message || 'System connection error',
        compile_output: '',
        exit_code: -1,
        status: 'system_error',
        time_ms: 0,
        memory_kb: 0,
        energy_wh: 0,
        carbon_g: 0,
        eco_score: 'N/A',
        eco_label: 'Error',
      });
    } finally {
      setIsRunning(false);
    }
  };

  // Handle Debug with AI
  const handleDebugAI = () => {
    setSelectedAgent('detective');
    setMobileTab('chat');
    handleSendMessage('Please analyze this code and provide root cause diagnosis and security verification.');
  };

  // Handle Ask AI to fix error
  const handleAskAIFix = () => {
    setSelectedAgent('repair');
    setMobileTab('chat');
    const errText = result?.stderr || 'Error during compilation/execution';
    handleSendMessage(`Please fix this error and explain the solution:\n\`\`\`\n${errText}\n\`\`\``);
  };

  // Handle Send Chat Query
  const handleSendMessage = async (queryText: string) => {
    if (isStreaming) return;

    const userMsg: ChatMessage = {
      id: Math.random().toString(36).substring(7),
      role: 'user',
      content: queryText,
      timestamp: Date.now(),
    };

    const assistantMsgId = Math.random().toString(36).substring(7);
    const initialAssistantMsg: ChatMessage = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      agent: selectedAgent,
      model: platformMode === 'council' ? 'Council' : agentModelRouting[selectedAgent] || selectedModel,
      timestamp: Date.now(),
      council_results: platformMode === 'council' ? [] : undefined,
    };

    const updatedMessages = [...messages, userMsg];
    setMessages([...updatedMessages, initialAssistantMsg]);
    setIsStreaming(true);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const activeModelTag = agentModelRouting[selectedAgent] || selectedModel;
    const lastOutputContext = result ? `STDOUT:\n${result.stdout}\nSTDERR:\n${result.stderr}` : '';

    let accumulatedContent = '';
    let councilResults: CouncilModelResult[] = [];

    await streamChat({
      agent: selectedAgent,
      mode: platformMode,
      model: activeModelTag,
      language: selectedLanguage,
      code: currentCode,
      lastRunOutput: lastOutputContext,
      messages: updatedMessages.map((m) => ({ role: m.role, content: m.content })),
      signal: abortController.signal,
      onToken: (token) => {
        accumulatedContent += token;
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantMsgId ? { ...m, content: accumulatedContent } : m))
        );
      },
      onAgentStart: (agent, model) => {
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantMsgId ? { ...m, agent: agent as AgentId, model } : m))
        );
      },
      onAgentDone: (data) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  extracted_code: data.extracted_code,
                  is_safe: data.is_safe,
                  security_note: data.security_note,
                }
              : m
          )
        );
      },
      onModelHeader: (mName, mTag) => {
        councilResults.push({
          model_name: mName,
          model_tag: mTag,
          content: '',
        });
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantMsgId ? { ...m, council_results: [...councilResults] } : m))
        );
      },
      onModelToken: (model, token) => {
        councilResults = councilResults.map((cr) =>
          cr.model_name === model ? { ...cr, content: cr.content + token } : cr
        );
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantMsgId ? { ...m, council_results: [...councilResults] } : m))
        );
      },
      onModelAudit: (data) => {
        councilResults = councilResults.map((cr) =>
          cr.model_name === data.model
            ? { ...cr, is_safe: data.is_safe, note: data.note, hasCode: data.has_code }
            : cr
        );
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantMsgId ? { ...m, council_results: [...councilResults] } : m))
        );
      },
      onConsensusToken: (token) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? { ...m, consensus: (m.consensus || '') + token }
              : m
          )
        );
      },
      onDone: () => {
        setIsStreaming(false);
      },
      onError: (err) => {
        setIsStreaming(false);
        toast.error(`Inference error: ${err.message}`);
      },
    });
  };

  const handleStopStreaming = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
    toast.info('Response generation stopped');
  };

  const handleApplyCode = (newCode: string) => {
    setCodePerLang((prev) => ({
      ...prev,
      [selectedLanguage]: newCode,
    }));
    toast.success('Verified fix applied to code editor!');
  };

  const handleResetTemplate = () => {
    setCodePerLang((prev) => ({
      ...prev,
      [selectedLanguage]: currentLangObj.template,
    }));
    toast.info(`Reset to starter ${currentLangObj.name} template`);
  };

  const handleClearCode = () => {
    setCodePerLang((prev) => ({
      ...prev,
      [selectedLanguage]: '',
    }));
  };

  return (
    <div className={`h-screen w-screen flex flex-col overflow-hidden bg-dark-bg text-slate-100 ${theme}`}>
      <Toaster richColors position="top-right" theme={theme} />

      {/* Top Navigation Bar */}
      <Navbar
        languages={languages}
        selectedLanguage={selectedLanguage}
        onSelectLanguage={setSelectedLanguage}
        platformMode={platformMode}
        onSelectPlatformMode={setPlatformMode}
        models={models}
        selectedModel={selectedModel}
        onSelectModel={setSelectedModel}
        health={health}
        theme={theme}
        onToggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenHistory={() => setIsHistoryOpen(true)}
        historyCount={runHistory.length}
      />

      {/* Desktop Main Resizable Area */}
      <div className="flex-1 hidden md:block overflow-hidden">
        <Group orientation="horizontal" className="h-full w-full">
          {/* Left Region: Code Editor (55%) */}
          <Panel defaultSize="55%" minSize="30%">
            <CodeEditor
              language={currentLangObj}
              code={currentCode}
              onChange={(val) =>
                setCodePerLang((prev) => ({
                  ...prev,
                  [selectedLanguage]: val,
                }))
              }
              onRun={handleRun}
              onDebugAI={handleDebugAI}
              isRunning={isRunning}
              theme={theme}
              fontSize={fontSize}
              onFontSizeChange={setFontSize}
              onResetTemplate={handleResetTemplate}
              onClear={handleClearCode}
            />
          </Panel>

          <Separator className="w-1.5 bg-dark-bg hover:bg-indigo-500/50 transition-colors cursor-col-resize flex items-center justify-center">
            <div className="h-8 w-0.5 bg-slate-700 rounded-full" />
          </Separator>

          {/* Right Region: Output, Green Metrics, and AI Chat (45%) */}
          <Panel defaultSize="45%" minSize="30%">
            <Group orientation="vertical" className="h-full w-full">
              {/* Right Top: Stdin & Output Panel */}
              <Panel defaultSize="40%" minSize="20%">
                <OutputPanel
                  stdin={stdin}
                  onStdinChange={setStdin}
                  result={result}
                  isRunning={isRunning}
                  onAskAIFix={handleAskAIFix}
                />
              </Panel>

              {/* Green Sandbox Metrics Strip (Always Visible) */}
              <div className="shrink-0">
                <GreenMetrics metrics={result} />
              </div>

              <Separator className="h-1.5 bg-dark-bg hover:bg-indigo-500/50 transition-colors cursor-row-resize flex items-center justify-center">
                <div className="w-8 h-0.5 bg-slate-700 rounded-full" />
              </Separator>

              {/* Right Bottom: Multi-Agent AI Chat */}
              <Panel defaultSize="60%" minSize="25%">
                <AgentChat
                  agents={agents}
                  selectedAgent={selectedAgent}
                  onSelectAgent={setSelectedAgent}
                  platformMode={platformMode}
                  messages={messages}
                  onSendMessage={handleSendMessage}
                  onApplyCode={handleApplyCode}
                  onClearChat={() => setMessages([])}
                  isStreaming={isStreaming}
                  onStopStreaming={handleStopStreaming}
                  activeLanguage={currentLangObj.name}
                />
              </Panel>
            </Group>
          </Panel>
        </Group>
      </div>

      {/* Mobile/Tablet Adaptive Tabs Layout */}
      <div className="flex-1 md:hidden flex flex-col overflow-hidden">
        <div className="flex-1 overflow-hidden">
          {mobileTab === 'editor' && (
            <CodeEditor
              language={currentLangObj}
              code={currentCode}
              onChange={(val) =>
                setCodePerLang((prev) => ({
                  ...prev,
                  [selectedLanguage]: val,
                }))
              }
              onRun={handleRun}
              onDebugAI={handleDebugAI}
              isRunning={isRunning}
              theme={theme}
              fontSize={fontSize}
              onFontSizeChange={setFontSize}
              onResetTemplate={handleResetTemplate}
              onClear={handleClearCode}
            />
          )}

          {mobileTab === 'output' && (
            <div className="h-full flex flex-col">
              <div className="flex-1 overflow-hidden">
                <OutputPanel
                  stdin={stdin}
                  onStdinChange={setStdin}
                  result={result}
                  isRunning={isRunning}
                  onAskAIFix={handleAskAIFix}
                />
              </div>
              <GreenMetrics metrics={result} />
            </div>
          )}

          {mobileTab === 'chat' && (
            <AgentChat
              agents={agents}
              selectedAgent={selectedAgent}
              onSelectAgent={setSelectedAgent}
              platformMode={platformMode}
              messages={messages}
              onSendMessage={handleSendMessage}
              onApplyCode={handleApplyCode}
              onClearChat={() => setMessages([])}
              isStreaming={isStreaming}
              onStopStreaming={handleStopStreaming}
              activeLanguage={currentLangObj.name}
            />
          )}
        </div>

        {/* Bottom Tab Bar for Mobile */}
        <div className="h-12 border-t border-dark-border bg-dark-card flex items-center justify-around text-xs font-semibold">
          <button
            onClick={() => setMobileTab('editor')}
            className={`flex-1 py-3 text-center ${mobileTab === 'editor' ? 'text-emerald-400 border-t-2 border-emerald-400' : 'text-slate-400'}`}
          >
            Editor
          </button>
          <button
            onClick={() => setMobileTab('output')}
            className={`flex-1 py-3 text-center ${mobileTab === 'output' ? 'text-indigo-400 border-t-2 border-indigo-400' : 'text-slate-400'}`}
          >
            Output & Metrics
          </button>
          <button
            onClick={() => setMobileTab('chat')}
            className={`flex-1 py-3 text-center ${mobileTab === 'chat' ? 'text-purple-400 border-t-2 border-purple-400' : 'text-slate-400'}`}
          >
            AI Chat
          </button>
        </div>
      </div>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        models={models}
        agents={agents}
        agentModelRouting={agentModelRouting}
        onUpdateAgentModelRouting={setAgentModelRouting}
      />

      {/* Run History Drawer */}
      <RunHistoryDrawer
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        history={runHistory}
        onRestore={(item) => {
          setSelectedLanguage(item.language);
          setCodePerLang((prev) => ({
            ...prev,
            [item.language]: item.code,
          }));
        }}
        onClearHistory={() => setRunHistory([])}
      />
    </div>
  );
}
export default App;
