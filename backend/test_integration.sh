#!/bin/bash
echo "=== Backend Integration Test ==="
echo ""

echo "1. Health Check..."
curl -s http://localhost:8000/health | python -c "import sys, json; data=json.load(sys.stdin); print(f\"  ✓ {data['status']} - {data['service']} v{data['version']}\")"

echo ""
echo "2. List Stocks..."
curl -s http://localhost:8000/api/stocks | python -c "import sys, json; data=json.load(sys.stdin); print(f\"  ✓ Found {data['total']} stocks: {', '.join([s['symbol'] for s in data['stocks']])}\")"

echo ""
echo "3. Get AAPL Market Data (last 5 days)..."
curl -s "http://localhost:8000/api/market-data/AAPL?days=5" | python -c "import sys, json; data=json.load(sys.stdin); print(f\"  ✓ Retrieved {len(data['data'])} bars, latest close: \${data['data'][-1]['close']}\")"

echo ""
echo "4. Get Strategy..."
curl -s http://localhost:8000/api/strategies/1 | python -c "import sys, json; data=json.load(sys.stdin); print(f\"  ✓ Strategy: {data['name']}, Status: {data['status']}\")"

echo ""
echo "5. List Backtests..."
curl -s http://localhost:8000/api/backtests/ | python -c "import sys, json; data=json.load(sys.stdin); print(f\"  ✓ Found {data['total']} completed backtests\")"

echo ""
echo "6. Get Best Backtest Result (GOOGL)..."
curl -s http://localhost:8000/api/backtests/2 | python -c "import sys, json; data=json.load(sys.stdin); m=data['metrics']; print(f\"  ✓ {data['symbol']}: Return {m['total_return_pct']:.2f}%, Sharpe {m['sharpe_ratio']:.2f}, Drawdown {m['max_drawdown_pct']:.2f}%\")"

echo ""
echo "7. Generate Signal for GOOGL..."
curl -s -X POST http://localhost:8000/api/signals/generate \
  -H "Content-Type: application/json" \
  -d '{"strategy_id": 1, "symbol": "GOOGL"}' | python -c "import sys, json; data=json.load(sys.stdin); print(f\"  ✓ Signal: {data['signal_type']}, Reason: {data['trigger_reason'][:50]}...\")"

echo ""
echo "=== All Tests Complete ==="
