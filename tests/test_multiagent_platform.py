"""
tests/test_multiagent_platform.py - Tests for Multi-Agent APR Platform
Verifies:
  1. Model Registry configuration (Llama, Phi-3, Qwen)
  2. Model alias resolution & default affinities
  3. DiagnosticAgent error classification & prompt formation
  4. RepairAgent synthesis & code fence extraction
  5. SecurityAuditorAgent 13-layer defense verification & feedback rejection
  6. TutorAgent pedagogical explanation generation
  7. MultiAgentOrchestrator Swarm collaboration & feedback retry loop
  8. MultiModel Council (Llama vs Phi-3 vs Qwen comparison)
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from multiagent_platform import (
    MODEL_REGISTRY,
    DEFAULT_FAMILY_MODELS,
    resolve_model_alias,
    DiagnosticAgent,
    RepairAgent,
    SecurityAuditorAgent,
    TutorAgent,
    MultiAgentOrchestrator,
    AgentMessage,
    MultiAgentPlan
)

class TestMultiAgentPlatform(unittest.TestCase):

    def test_01_model_registry_contains_phi3_qwen_llama(self):
        """Verifies Phi-3, Qwen, and Llama are registered with proper metadata."""
        # Phi-3 models
        self.assertIn("phi3:mini", MODEL_REGISTRY)
        self.assertIn("phi3:medium", MODEL_REGISTRY)
        self.assertEqual(MODEL_REGISTRY["phi3:mini"]["family"], "Phi-3")
        self.assertIn("ollama pull phi3:mini", MODEL_REGISTRY["phi3:mini"]["pull_cmd"])

        # Qwen models
        self.assertIn("qwen2.5:coder", MODEL_REGISTRY)
        self.assertIn("qwen2.5-coder:1.5b", MODEL_REGISTRY)
        self.assertEqual(MODEL_REGISTRY["qwen2.5:coder"]["family"], "Qwen")
        self.assertIn("ollama pull qwen2.5:coder", MODEL_REGISTRY["qwen2.5:coder"]["pull_cmd"])

        # Llama models
        self.assertIn("llama3.2:1b", MODEL_REGISTRY)
        self.assertEqual(MODEL_REGISTRY["llama3.2:1b"]["family"], "Llama")

        # Default family mappings
        self.assertEqual(DEFAULT_FAMILY_MODELS["Phi-3"], "phi3:mini")
        self.assertEqual(DEFAULT_FAMILY_MODELS["Qwen"], "qwen2.5:coder")
        self.assertEqual(DEFAULT_FAMILY_MODELS["Llama"], "llama3.2:1b")

    def test_02_resolve_model_alias(self):
        """Tests model nickname and family resolution."""
        self.assertEqual(resolve_model_alias("phi3:mini"), "phi3:mini")
        self.assertEqual(resolve_model_alias("phi-3"), "phi3:mini")
        self.assertEqual(resolve_model_alias("qwen"), "qwen2.5:coder")
        self.assertEqual(resolve_model_alias("llama"), "llama3.2:1b")

    def test_03_diagnostic_agent(self):
        """Tests Diagnostic Agent classification and report generation."""
        agent = DiagnosticAgent(default_model="phi3:mini")
        code = '#include <iostream>\nint main() { std::cout << "Missing semicolon" return 0; }'
        err = "solution.cpp:2:46: error: expected ';' before 'return'"

        msg = agent.diagnose(code, err, language="cpp")
        self.assertIsInstance(msg, AgentMessage)
        self.assertEqual(msg.role, "Error Detective 🔍")
        self.assertEqual(msg.metadata["category"], "Syntax Error")
        self.assertIn("Fault Localization", msg.content.title())

    def test_04_repair_agent_extracts_code(self):
        """Tests Repair Agent synthesizing fix with markdown extraction."""
        agent = RepairAgent(default_model="qwen2.5:coder")
        
        # Test simulated LLM repair response
        simulated_response = """
### REPAIR SUMMARY
Added missing semicolon before return.

### FIXED CODE
```cpp
#include <iostream>
int main() {
    std::cout << "Fixed!" << std::endl;
    return 0;
}
```
"""
        with patch.object(agent, "call_model", return_value=simulated_response):
            msg = agent.synthesize_repair(
                code='int main(){ std::cout << "test" return 0; }',
                error="expected ';'",
                diagnosis="Missing semicolon on line 1",
                language="cpp"
            )
            self.assertEqual(msg.status, "success")
            self.assertIsNotNone(msg.metadata.get("extracted_code"))
            self.assertIn("Fixed!", msg.metadata["extracted_code"])

    def test_05_security_auditor_agent_approves_safe_code(self):
        """Verifies Security Sentinel approves secure fixes."""
        auditor = SecurityAuditorAgent(default_model="llama3.2:1b")
        safe_code = """
#include <iostream>
int main() {
    std::cout << "Safe code execution" << std::endl;
    return 0;
}
"""
        msg = auditor.audit(safe_code, raw_response="", language="cpp")
        self.assertEqual(msg.status, "approved")
        self.assertTrue(msg.metadata["is_secure"])

    def test_06_security_auditor_agent_rejects_insecure_code(self):
        """Verifies Security Sentinel blocks dangerous functions like system() or gets()."""
        auditor = SecurityAuditorAgent(default_model="llama3.2:1b")
        insecure_code = """
#include <cstdlib>
int main() {
    system("rm -rf /");
    return 0;
}
"""
        msg = auditor.audit(insecure_code, raw_response="", language="cpp")
        self.assertEqual(msg.status, "rejected")
        self.assertFalse(msg.metadata["is_secure"])
        self.assertIn("system()", msg.metadata["violation"])

    def test_07_tutor_agent_generates_pedagogical_lesson(self):
        """Tests Tutor Agent lesson structure."""
        tutor = TutorAgent(default_model="phi3:mini")
        with patch.object(tutor, "call_model", return_value="### CONCEPT\nSemicolons terminate C++ statements."):
            msg = tutor.teach("cpp", "int main(){}", "Syntax error", "int main(){ return 0; }")
            self.assertIn("CONCEPT", msg.content)
            self.assertEqual(msg.role, "Pedagogical Mentor 🎓")

    def test_08_orchestrator_swarm_pipeline(self):
        """Tests full 4-agent collaborative swarm pipeline."""
        orchestrator = MultiAgentOrchestrator(
            diagnostic_model="phi3:mini",
            repair_model="qwen2.5:coder",
            security_model="llama3.2:1b",
            tutor_model="phi3:mini"
        )
        buggy_code = 'print("Hello world"'
        err = 'SyntaxError: unexpected EOF while parsing'

        safe_repair = """
### REPAIR SUMMARY
Closed parentheses.

### FIXED CODE
```python
print("Hello world")
```
"""
        with patch.object(orchestrator.repair_agent, "call_model", return_value=safe_repair):
            plan = orchestrator.run_collaborative_swarm(buggy_code, err, language="python")
            self.assertIsInstance(plan, MultiAgentPlan)
            self.assertEqual(plan.execution_mode, "swarm")
            self.assertTrue(plan.is_secure)
            self.assertIsNotNone(plan.final_code)
            self.assertIn("print(\"Hello world\")", plan.final_code)
            self.assertEqual(len(plan.all_messages), 4)

    def test_09_orchestrator_council_pipeline(self):
        """Tests Multi-Model Council running Llama, Phi-3, and Qwen."""
        orchestrator = MultiAgentOrchestrator()
        buggy_code = 'print("Council Test"'
        err = 'SyntaxError: unexpected EOF'

        mock_repair = """
### FIXED CODE
```python
print("Council Test Fixed")
```
"""
        with patch.object(orchestrator.repair_agent, "call_model", return_value=mock_repair):
            plan = orchestrator.run_multi_model_council(buggy_code, err, language="python")
            self.assertEqual(plan.execution_mode, "council")
            self.assertIn("Meta Llama 3", plan.council_proposals)
            self.assertIn("Microsoft Phi-3", plan.council_proposals)
            self.assertIn("Alibaba Qwen", plan.council_proposals)
            self.assertTrue(plan.is_secure)

if __name__ == "__main__":
    unittest.main()

