# VectorCode Integration Guide - NFL Predictor API

**Complete guide for semantic code search and intelligent context management**

> **Quick Reference**: See [CLAUDE.md](../CLAUDE.md) for essential commands  
> **Related**: [CLAUDE_FLOW_AGENTS.md](./CLAUDE_FLOW_AGENTS.md) | [SPARC_METHODOLOGY.md](./SPARC_METHODOLOGY.md)

---

## 🔍 VectorCode Overview

VectorCode is your **primary search and discovery tool** for the NFL Predictor API:

1. **ALWAYS use VectorCode first** before starting any coding task
2. **Search existing code patterns** before implementing new features
3. **Find documentation** using semantic search across 58+ markdown files in `.qoder/repowiki/en/content/`
4. **Discover related implementations** across the entire codebase
5. **Use domain-specific queries** for NFL Predictor features

---

## 🚨 CRITICAL: TOKEN MANAGEMENT - PREVENT OVERFLOW

**TOKEN OVERFLOW EMERGENCY PROTOCOL**:

If VectorCode queries exceed 25k tokens, follow this protocol:

1. **IMMEDIATELY STOP** current search approach
2. **Switch to 3-Phase Progressive Search** methodology
3. **Use domain-specific patterns** instead of vague queries
4. **Limit results to 1-2 per phase** maximum

---

## 🎯 3-PHASE PROGRESSIVE SEARCH METHODOLOGY

### Phase 1: Exploration (2-3 results max)

```bash
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "AI expert council voting"
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "self-healing learning loop"
```

### Phase 2: Targeted Search (3 results max)

```bash
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 3 --query "weighted consensus voting mechanism"
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 3 --query "expert performance tracking metrics"
```

### Phase 3: Deep Dive (1-2 results max)

```bash
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "merit based expert rotation algorithm"
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "WebSocket real-time prediction updates"
```

---

## ⚡ SAFE TOKEN LIMITS

- **Phase 1**: 2-3 results = ~3,000 tokens
- **Phase 2**: 3 results = ~4,000 tokens  
- **Phase 3**: 1-2 results = ~2,000 tokens
- **Total per session**: ~9,000 tokens maximum

---

## 🏈 NFL Predictor API Specific Queries

### Expert Council System

```bash
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "AI expert council weighted voting consensus"
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "merit based expert rotation performance"
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "expert performance tracking accuracy metrics"
```

### S³L (Self-Healing Learning Loop)

```bash
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "self healing learning loop monitoring"
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "automated expert rotation threshold"
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "S3L performance analysis continuous improvement"
```

### Real-Time Predictions

```bash
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "WebSocket real-time prediction updates"
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "live game updates broadcasting"
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "enhanced prediction service real data"
```

### Data Integration

```bash
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "SportsData.io connector rate limiting"
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "intelligent caching TTL strategy"
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "data quality confidence scoring"
```

---

## 🚨 QUERY FORMULATION RULES

### ✅ DO:
- Use 2-4 specific keywords per query
- Include domain context ("expert council", "S3L", "WebSocket")
- Limit results with `-n 1` to `-n 3`
- Start narrow, expand if needed

### ❌ DON'T:
- Use single generic words ("function", "data", "api")
- Search without context
- Use more than `-n 5` results
- Make vague queries

---

## 🔗 Related Documentation

- **[CLAUDE.md](../CLAUDE.md)** - Essential commands and quick reference
- **[CLAUDE_FLOW_AGENTS.md](./CLAUDE_FLOW_AGENTS.md)** - Agent types and coordination
- **[SPARC_METHODOLOGY.md](./SPARC_METHODOLOGY.md)** - Development workflow

---

**🏈 For quick reference, see [CLAUDE.md](../CLAUDE.md) for the most common queries!**
