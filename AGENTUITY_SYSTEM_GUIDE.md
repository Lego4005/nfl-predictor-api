# Agentuity NFL Expert System - Complete Guide

## 🎯 System Overview

This is a 4-Expert NFL Prediction System built with Agentuity that orchestrates multiple AI agents to generate comprehensive game predictions.

## 📁 Project Structure

```
agentuity/pickiq/
├── src/agents/
│   ├── game-orchestrator/     # Main orchestrator agent
│   ├── the-analyst/           # Conservative data-driven expert
│   ├── the-rebel/             # Contrarian anti-consensus expert
│   ├── the-rider/             # Momentum-based trend expert
│   ├── the-hunter/            # Value-seeking market expert
│   └── [11 other experts...]  # Additional expert agents
├── agentuity.yaml            # Agent configuration
├── package.json              # Dependencies
└── .env                      # Environment variables
```

## 🤖 Agent Architecture

### Main Orchestrator: `game-orchestrator`
- **ID**: `agent_game_orchestrator`
- **Name**: `game-orchestrator`
- **Purpose**: Coordinates parallel execution of expert agents
- **Endpoint**: `http://localhost:3500/run/game-orchestrator`

### Expert Agents (4 Active)
1. **the-analyst** - Conservative, data-driven approach
2. **the-rebel** - Contrarian, anti-consensus predictions
3. **the-rider** - Momentum-based, trend-following
4. **the-hunter** - Value-seeking, market inefficiency focused

## 🚀 Current System Status

### ✅ What's Working
- Agentuity dev server running on port 3500
- All 17 agents built and available in dropdown
- Game orchestrator properly exported with default export
- Expert agents implemented with proper TypeScript structure

### ❌ Current Issues
- Game orchestrator shows as "Unknown Agent" in DevMode
- Only 1 session showing instead of 5 (orchestrator + 4 experts)
- Agent invocation failing to find expert agents

## 🔧 System Configuration

### Environment Setup
```bash
# Start Agentuity dev server
cd agentuity/pickiq
npm run dev
```

### DevMode URLs
- **Local**: http://127.0.0.1:3500
- **Public**: https://dev-mcjay76on.agentuity.run
- **DevMode Dashboard**: https://app.agentuity.com/devmode/8901a4234d7b3d57

## 📡 API Usage

### Test Orchestrator
```bash
curl -v http://localhost:3500/run/game-orchestrator --json '{
  "game_id": "test_game_chiefs_bills",
  "expert_ids": ["the-analyst", "the-rebel", "the-rider", "the-hunter"],
  "gameContext": {
    "homeTeam": "Kansas City Chiefs",
    "awayTeam": "Buffalo Bills",
    "gameTime": "2025-01-26T20:00:00Z"
  },
  "memories": [
    {
      "memoryId": "mem_001",
      "content": "Chiefs vs Bills playoff history shows close games",
      "similarity": 0.87
    }
  ],
  "run_id": "run_2025_pilot4"
}'
```

### Expected Response Flow
1. **Orchestrator** receives request
2. **Calls 4 experts in parallel** using `context.getAgent({ name: expertId })`
3. **Each expert** generates 83-assertion predictions
4. **Returns aggregated results** with orchestration summary

## 🏗️ Agent Implementation Pattern

### Required Exports (TypeScript)
```typescript
// Default export - main handler function
export default async function AgentName(
  request: AgentRequest,
  response: AgentResponse,
  context: AgentContext
) {
  // Agent logic here
  return response.json(result);
}

// Named export - welcome function
export const welcome = () => {
  return {
    welcome: "Agent description...",
    prompts: [
      {
        data: "Example prompt",
        contentType: "text/plain"
      }
    ]
  };
};

// Optional - agent configuration
export const config = {
  name: "agent-name",
  description: "Agent description"
};
```

### Agent Handler Signature
```typescript
async function Handler(
  request: AgentRequest,    // NOT req
  response: AgentResponse,  // NOT resp
  context: AgentContext     // NOT ctx
) {
  // Use request.data.json() to get payload
  // Use context.logger.info() for logging
  // Use context.getAgent() to call other agents
  // Return response.json() for JSON responses
}
```

## 🔍 Debugging Guide

### Common Issues

1. **"Unknown Agent" in DevMode**
   - Missing default export
   - Incorrect parameter names (must be request, response, context)
   - Need to restart dev server after code changes

2. **Agent Not Found Errors**
   - Check agent names match exactly (the-analyst, not conservative-analyzer)
   - Verify agents are built in .agentuity/src/agents/
   - Ensure proper exports in agent files

3. **404 Not Found on API Calls**
   - Use correct endpoint: `/run/{agent-name}` not `/orchestrate`
   - Agent name from agentuity.yaml, not agent ID
   - Server must be running on port 3500

### Verification Steps
```bash
# Check if agents are built
ls -la agentuity/pickiq/.agentuity/src/agents/

# Check server is running
curl http://localhost:3500/health

# Test individual agent
curl http://localhost:3500/run/the-analyst --json '{"test": "data"}'
```

## 🎯 Expected System Behavior

### Successful Orchestration Should Show:
- **DevMode Sessions**: 5 total (1 orchestrator + 4 experts)
- **Agent Names**: Proper names, not "Unknown Agent"
- **Parallel Execution**: All 4 experts running simultaneously
- **Prediction Results**: 332 total predictions (4 × 83 each)

### Performance Targets:
- **Response Time**: Sub-second for orchestration
- **Expert Execution**: 2-4 seconds per expert
- **Total Orchestration**: 5-8 seconds for all 4 experts

## 🛠️ MCP Integration

### Agentuity MCP Tools Available:
- `mcp_agentuity_list_agents` - List agents in project
- `mcp_agentuity_list_projects` - List user projects
- `mcp_agentuity_whoami` - Check authentication
- `mcp_agentuity_deploy` - Deploy agents to cloud

### Current MCP Status:
- Schema validation errors preventing usage
- Need to debug MCP connection in Cursor

## 📋 Next Steps

1. **Fix "Unknown Agent" Issue**
   - Verify all agents have proper default exports
   - Restart dev server completely
   - Test orchestrator endpoint

2. **Verify Expert Invocation**
   - Ensure orchestrator can find expert agents
   - Check agent name mapping is correct
   - Test parallel execution

3. **Scale to Full System**
   - Add remaining 11 expert agents
   - Implement council voting mechanism
   - Add prediction storage and retrieval

## 🔗 Key Files to Reference

- `agentuity/pickiq/src/agents/game-orchestrator/index.ts` - Main orchestrator
- `agentuity/pickiq/agentuity.yaml` - Agent configuration
- `agentuity/pickiq/package.json` - Dependencies and scripts
- `src/api/main.py` - FastAPI backend (if using local API)

## 📚 Documentation Links

- **Agentuity Docs**: https://agentuity.dev/
- **TypeScript SDK**: https://github.com/agentuity/sdk-js
- **Examples**: https://github.com/agentuity/examples
- **Kitchen Sink**: https://github.com/agentuity/kitchen-sink-ts

---

**This system represents a 4-expert pilot for a larger 15-expert NFL prediction platform with AI council voting and comprehensive betting analytics.**
