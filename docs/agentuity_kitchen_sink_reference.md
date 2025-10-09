# Agentuity Kitchen Sink Reference

> **Source**: [github.com/agentuity/kitchen-sink-ts](https://github.com/agentuity/kitchen-sink-ts)
> **Last Updated**: October 8, 2025
> **Estimated Tokens**: 31,000

## Overview

The Agentuity Kitchen Sink is an **interactive playground and reference implementation** that showcases all features of the Agentuity SDK. It provides live, working agents that demonstrate SDK capabilities without requiring extensive documentation.

### Key Benefits

- **Interactive Learning**: Send messages to agents and see exactly how features work
- **Code-Along Experience**: View source code while testing to understand implementation
- **Zero to Running**: Minimal setup to start exploring (~5 minutes)
- **Living Documentation**: The agents themselves explain their features

## Quick Start

```bash
# 1. Deploy to your account (or fork the repo)
# Use the "Deploy w/ Agentuity" button on GitHub

# 2. Install Agentuity CLI
npm install -g @agentuity/cli

# 3. Test locally
agentuity dev

# 4. Set any required secrets (optional)
agentuity env set --secret ANTHROPIC_API_KEY your-key-here

# 5. Deploy your changes
agentuity deploy
```

## Prerequisites

### Required
- **Bun**: Version 1.2.4 or higher
- **Agentuity CLI**: `npm install -g @agentuity/cli`
- **Agentuity account**: Sign up at [agentuity.com](https://app.agentuity.com/sign-up)

### Optional (for specific agents)
- **Object Storage bucket**: For "Object Store" agent demo
- **`ANTHROPIC_API_KEY`**: For "Bring-Your-Own-Token" agent demo
- **`COMPOSIO_API_KEY`**: For Composio integration (composio.dev)
- **`DISCORD_WEBHOOK_URL`**: For Discord bot demo
- **`SLACK_SIGNING_SECRET`** and **`SLACK_BOT_TOKEN`**: For Slack bot demo
- **Twilio phone number**: For SMS demo (requires verified account)

---

## Available Agents

### Core Handler Agents

#### **kitchen-sink**
Ask questions about any Agentuity feature. This is the main help agent powered by gpt-5-mini.

**Features**:
- Fetches and caches Agentuity docs (`https://agentuity.dev/llms.txt`)
- Maintains chat history in KV storage
- Auto-compacts conversation when token limit reached (350k tokens)
- Streams responses in markdown format

#### **handler-request**
Demonstrates accessing request data, content types, and triggers.

**Key Concepts**:
- `req.data.contentType` - Get content type
- `req.data.json()` / `req.data.text()` - Parse data
- `req.trigger` - Determine trigger type (manual, webhook, cron, etc.)
- `req.metadata.headers` - Access custom headers

#### **handler-response**
Shows different response formats (text, images, streams, etc.).

**Response Types**:
- `resp.text()` - Plain text
- `resp.png()` / `resp.jpeg()` / `resp.gif()` - Images
- `resp.stream()` - Streaming content
- `resp.json()` - JSON data
- `resp.html()` - HTML pages
- `resp.markdown()` - Markdown content
- Audio: `resp.mp3()`, `resp.wav()`, `resp.ogg()`, `resp.m4a()`
- Video: `resp.mp4()`, `resp.webm()`

#### **handler-context**
Session data and agent context access.

---

### Framework & Gateway Agents

#### **frameworks-provider**
Run multiple AI frameworks side-by-side.

#### **gateway-provider**
AI Gateway with multiple LLM providers (OpenAI, Anthropic, etc.).

#### **gateway-byo-token**
Demonstrates using your own LLM provider API keys instead of Agentuity's gateway.

---

### I/O Agents

#### **io-agent**
Agent-to-agent communication & handoffs.

**Methods**:
```typescript
// Handoff processing to another agent
return resp.handoff(
  { name: 'other-agent' },
  { data: 'message' }
);

// Run and wait for response
const agent = await ctx.getAgent({ name: 'other-agent' });
const result = await agent.run({ data: 'message' });

// Fetch from public agents
const response = await fetch('https://agentuity.ai/api/agent-id', {
  method: 'POST',
  headers: { 'Content-Type': 'text/plain' },
  body: 'message'
});
```

#### **io-api**
Synchronous API request handling.

#### **io-cron**
Scheduled execution with cron triggers.

#### **io-email**
Receive and respond to emails.

#### **io-sms**
SMS messaging via Twilio.

#### **io-webhook**
Asynchronous webhook processing (fire-and-forget).

---

### Storage Agents

#### **storage-key-value**
Fast KV storage for session state & caching.

**Usage**:
```typescript
const bucket = 'my-bucket'; // Auto-created if doesn't exist
const key = 'my-key';

// Set with TTL
await ctx.kv.set(bucket, key, 'value', {
  ttl: 60, // seconds (optional, defaults to forever)
  contentType: 'text/plain' // optional
});

// Get
const result = await ctx.kv.get(bucket, key);
if (result.exists) {
  const value = await result.data.text(); // or .json()
}

// Delete
await ctx.kv.delete(bucket, key);
```

#### **storage-object-store**
Store files, images, and large objects.

#### **storage-vector**
Semantic search with vector embeddings.

**Methods**:
```typescript
// Upsert vectors
await ctx.vector.upsert(name, ...documents);

// Search
const results = await ctx.vector.search(name, params);

// Delete
await ctx.vector.delete(name, ...ids);
```

---

### Observability Agents

#### **observability-logging**
Structured logging at different levels.

**Usage**:
```typescript
ctx.logger.debug('Debug message: %s', variable);
ctx.logger.info('Info message');
ctx.logger.warn('Warning message');
ctx.logger.error('Error message', error);

// Child logger with context
const childLogger = ctx.logger.child({ requestId: '123' });
```

#### **observability-tracing**
OpenTelemetry tracing with spans and events.

---

### Example Agents

#### **example-chat**
Conversational AI with persistent chat history.

#### **example-composio**
Integration with Composio tools (Hacker News demo).

#### **example-discord**
Discord webhook notifications.

#### **example-slack**
Slack bot integration with thread support.

---

## Project Structure

```
kitchen-sink-ts/
├── src/
│   ├── agents/                    # Agent implementations
│   │   ├── kitchen-sink/          # Main help agent
│   │   ├── handler-request/       # Request handling demo
│   │   ├── handler-response/      # Response types demo
│   │   ├── handler-context/       # Context access demo
│   │   ├── frameworks-provider/   # Multi-framework demo
│   │   ├── gateway-provider/      # AI Gateway demo
│   │   ├── gateway-byo-token/     # BYO token demo
│   │   ├── io-agent/              # Agent-to-agent comm
│   │   ├── io-api/                # API handling
│   │   ├── io-cron/               # Cron triggers
│   │   ├── io-email/              # Email I/O
│   │   ├── io-sms/                # SMS I/O
│   │   ├── io-webhook/            # Webhook handling
│   │   ├── storage-key-value/     # KV storage
│   │   ├── storage-object-store/  # Object storage
│   │   ├── storage-vector/        # Vector storage
│   │   ├── observability-logging/ # Logging
│   │   ├── observability-tracing/ # Tracing
│   │   ├── example-chat/          # Chat demo
│   │   ├── example-composio/      # Composio integration
│   │   ├── example-discord/       # Discord bot
│   │   ├── example-slack/         # Slack bot
│   │   └── test-suite/            # Automated tests
│   └── lib/
│       └── utils.ts               # Shared utilities
├── node_modules/                  # Dependencies
├── package.json                   # Project dependencies
├── agentuity.yaml                 # Agentuity configuration
├── index.ts                       # Entry point
├── tsconfig.json                  # TypeScript config
├── biome.json                     # Linter config
├── .env                           # Local environment vars
├── .env.example                   # Example env vars
├── AGENTS.md                      # Agent development guide
└── README.md                      # Project documentation
```

---

## Core Concepts

### Agent Handler Function

Every agent exports a default handler function:

```typescript
import type { AgentRequest, AgentResponse, AgentContext } from "@agentuity/sdk";

export default async function Agent(
  req: AgentRequest,
  resp: AgentResponse,
  ctx: AgentContext
) {
  // Your agent logic
  return resp.json({ hello: 'world' });
}
```

### AgentRequest Interface

- `request.trigger` - Get trigger type
- `request.metadata(key, defaultValue)` - Get metadata
- `request.get(key, defaultValue)` - Get metadata value
- `request.data.contentType` - Get content type
- `request.data.json()` - Parse as JSON
- `request.data.text()` - Parse as text
- `request.data.buffer()` - Get as ArrayBuffer
- `request.data.binary()` - Get as ArrayBuffer
- `request.data.object<T>()` - Parse as typed object

### AgentResponse Interface

- `response.json(data, metadata)` - JSON response
- `response.text(data, metadata)` - Text response
- `response.binary(data, metadata)` - Binary response
- `response.html(data, metadata)` - HTML response
- `response.empty(metadata)` - Empty response
- `response.handoff(agent, args?)` - Redirect to another agent

### AgentContext Interface

- `context.logger` - Logging functionality
- `context.kv` - Key-Value storage
- `context.vector` - Vector storage
- `context.getAgent(params)` - Get handle to remote agent
- `context.tracer` - OpenTelemetry tracing

---

## Configuration (agentuity.yaml)

```yaml
# Project metadata
version: ">=0.0.166"
project_id: proj_2e801790c37b125c0565ea69bad3e9f4
name: kitchen-sink-ts
description: A demo project that showcases all of Agentuity's SDK functionality

# Development configuration
development:
  port: 3500
  watch:
    enabled: true
    files:
      - src/**
  command: bun
  args:
    - run
    - --silent
    - --env-file=.env
    - --env-file=.env.development
    - .agentuity/index.js

# Deployment configuration
deployment:
  command: bun
  args:
    - run
    - --no-install
    - --prefer-offline
    - --silent
    - .agentuity/index.js
  resources:
    memory: 2Gi
    cpu: 2000M
    disk: 250Mi
  mode:
    type: on-demand # or provisioned

# Bundler configuration
bundler:
  enabled: true
  identifier: bunjs
  language: javascript
  runtime: bunjs
  agents:
    dir: src/agents
  ignore:
    - "**/*"
    - "!/.agentuity/**"
    - "!/agentuity.yaml"

# Agents list
agents:
  - id: agent_92281cf4dfa7c96dcd10f0a0a0d497b8
    name: kitchen-sink
    description: Overview agent
  # ... (21 more agents)
```

---

## Common Patterns

### Welcome Messages

Each agent can export a `welcome()` function for DevMode:

```typescript
export const welcome = () => {
  return {
    welcome: `Welcome message in HTML/markdown`,
    prompts: [
      {
        data: `Sample prompt`,
        contentType: 'text/plain',
        metadata: { /* optional */ }
      }
    ]
  };
};
```

### Help Messages

The Kitchen Sink uses a shared helper for "help" commands:

```typescript
import { handleHelpMessage } from '../../lib/utils';

export default async function Agent(req, resp, ctx) {
  const help = await handleHelpMessage(req, resp, ctx, 'feature-name');
  if (help) return help;

  // Your agent logic
}
```

### Error Handling

```typescript
try {
  // Your logic
} catch (error) {
  ctx.logger.error('Error description:', error);
  return new Response('Internal Server Error', { status: 500 });
}
```

### Streaming Responses

```typescript
import { streamText } from 'ai';
import { openai } from '@ai-sdk/openai';

const result = await streamText({
  model: openai('gpt-5-mini'),
  prompt: 'Your prompt'
});

return resp.stream(result.textStream, 'text/markdown');
```

---

## DevMode Usage

### Getting Help
Type "help" in any agent (except `example-*` agents) for feature overview.

### Following Along
Keep the source code open in `src/agents/[agent-name]` while testing.

### Interactive Prompts
Most agents suggest prompts when you first select them.

---

## Resources

- **Documentation**: [agentuity.dev](https://agentuity.dev)
- **JavaScript SDK Reference**: [JavaScript SDK](https://agentuity.dev/SDKs/javascript)
- **Python SDK Reference**: [Python SDK](https://agentuity.dev/SDKs/python)
- **Discord Community**: [Join our Discord](https://discord.gg/agentuity)
- **GitHub Repository**: [kitchen-sink-ts](https://github.com/agentuity/kitchen-sink-ts)

---

## Key Takeaways

1. **Agent Pattern**: Every agent is a function that receives `(req, resp, ctx)` and returns a response
2. **Storage Options**: KV for fast ephemeral data, Object Store for files, Vector for semantic search
3. **Communication**: Agents can handoff, run, or fetch from other agents
4. **Observability**: Built-in structured logging and OpenTelemetry tracing
5. **Flexibility**: Support for multiple content types, streaming, and custom responses
6. **DevMode**: Interactive playground for testing features before building

---

## Relevance to Quickaroo

The Agentuity Kitchen Sink provides patterns that could be valuable for Quickaroo:

1. **Agent Architecture**: Clean handler pattern with typed requests/responses
2. **Storage Patterns**: KV storage for caching (like QB data), Vector storage for semantic search
3. **Agent Communication**: Handoffs between agents (e.g., Taskaroo → QuickBooks workflow)
4. **Observability**: Structured logging and tracing for production workflows
5. **DevMode Pattern**: Interactive testing interface similar to CopilotKit's approach
6. **Response Streaming**: For real-time AG-UI updates to frontend

The Kitchen Sink demonstrates production-ready patterns for building agent platforms, which aligns with Quickaroo's goal of orchestrating QuickBooks and Taskaroo operations through LangGraph agents.

