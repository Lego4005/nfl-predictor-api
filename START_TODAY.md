# 🚀 Start Your 4-Expert Pilot TODAY

Your system is ready! You have OpenRouter configured with access to all the models needed.

## ⚡ Super Quick Start (5 minutes)

### 1. Setup System
```bash
python3 scripts/start_pilot_system.py --mode setup
```
This will:
- ✅ Test OpenRouter connection (Claude, DeepSeek, Gemini, Grok)
- ✅ Test Supabase database connection
- ✅ Initialize 4 expert bankrolls
- ✅ Setup calibration priors
- ✅ Run system health check

### 2. Quick Test (Optional)
```bash
python3 scripts/start_pilot_system.py --mode test
```
This will:
- ✅ Test LLM prediction generation
- ✅ Test database writes
- ✅ Verify end-to-end functionality

### 3. Start Training (2020-2023)
```bash
python3 scripts/pilot_training_runner.py \
  --run-id run_2025_pilot4 \
  --seasons 2020,2021,2022,2023 \
  --experts conservative_analyzer,momentum_rider,contrarian_rebel,value_hunter \
  --stakes 0 --reflections off --tools off
```

### 4. Check Training Progress
```bash
python3 scripts/check_training_completion.py --run-id run_2025_pilot4
```

### 5. Run 2024 Backtest
```bash
python3 scripts/pilot_backtest_runner.py \
  --run-id run_2025_pilot4 \
  --season 2024 --week 1 \
  --experts conservative_analyzer,momentum_rider,contrarian_rebel,value_hunter \
  --baselines coin_flip,market_only,one_shot,deliberate \
  --stakes 1.0
```

## 🎯 What You'll Get

### Expert Models (via OpenRouter)
- **conservative_analyzer** → Claude 3.5 Sonnet (high-quality reasoning)
- **momentum_rider** → DeepSeek Chat (fast, cost-effective)
- **contrarian_rebel** → DeepSeek Chat (contrarian analysis)
- **value_hunter** → Claude 3.5 Sonnet (value identification)

### Baseline Comparisons
- **Coin-flip**: Random 50/50 predictions (sanity check)
- **Market-only**: Pure market odds predictions
- **One-shot**: Single LLM call without memory
- **Deliberate**: Rule-based heuristics

### Performance Metrics
- **Brier Score**: Prediction accuracy for binary/enum
- **MAE**: Mean absolute error for numeric predictions
- **ROI**: Return on investment tracking
- **Schema Compliance**: JSON validation rates

## 📊 Monitor Progress

### System Status
```bash
python3 scripts/system_status.py
```

### API Health
```bash
curl http://localhost:8000/api/smoke-test/health
```

### Expert Leaderboard
```bash
curl http://localhost:8000/api/leaderboard
```

### Performance Metrics
```bash
curl http://localhost:8000/api/smoke-test/validate/performance
```

## 🎉 Your Advantages

### ✅ Already Configured
- OpenRouter API key ✅
- Supabase database ✅
- Odds API access ✅
- Run ID isolation ✅

### ✅ Production Ready
- Error handling & recovery
- Performance monitoring
- Baseline A/B testing
- Comprehensive logging

### ✅ Multiple Models
- Claude 3.5 Sonnet (premium reasoning)
- DeepSeek Chat (fast & free)
- Gemini Pro (shadow testing)
- Grok Beta (contrarian views)

## 🚀 Just Run This Now

```bash
# 1. Setup (5 minutes)
python3 scripts/start_pilot_system.py --mode setup

# 2. Quick test (1 minute)
python3 scripts/start_pilot_system.py --mode test

# 3. Start getting results!
python3 scripts/pilot_training_runner.py \
  --run-id run_2025_pilot4 \
  --seasons 2020,2021,2022,2023 \
  --experts conservative_analyzer,momentum_rider,contrarian_rebel,value_hunter \
  --stakes 0 --reflections off --tools off
```

**You'll have learning curves and baseline comparisons running within the hour!** 🎯

## 🛡️ Safety Features Built-In

- **Schema Validation**: ≥98.5% JSON compliance
- **Performance Monitoring**: Vector <100ms, E2E <6s
- **Error Recovery**: Auto-retry with fallback models
- **Model Switching**: Auto-route poor performers to baselines
- **Run Isolation**: Clean separation with run_2025_pilot4

**Your system is ready to generate real predictions and compare against baselines immediately!** 🚀
