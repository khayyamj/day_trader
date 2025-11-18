#!/usr/bin/env python
"""Test all API endpoints."""
import requests

print('\n=== Complete API Integration Test ===\n')

endpoints = [
    ('Health Check', 'GET', 'http://localhost:8000/health'),
    ('List Stocks', 'GET', 'http://localhost:8000/api/stocks/'),
    ('List Strategies', 'GET', 'http://localhost:8000/api/strategies/'),
    ('Get Strategy #1', 'GET', 'http://localhost:8000/api/strategies/1'),
    ('List Backtests', 'GET', 'http://localhost:8000/api/backtests/'),
    ('Get Backtest #2', 'GET', 'http://localhost:8000/api/backtests/2'),
    ('Get Backtest Trades', 'GET', 'http://localhost:8000/api/backtests/2/trades'),
    ('Get Equity Curve', 'GET', 'http://localhost:8000/api/backtests/2/equity-curve'),
]

tests = []

for name, method, url in endpoints:
    try:
        r = requests.request(method, url, timeout=5)
        status = '✓' if r.status_code == 200 else '✗'
        tests.append((status, name, r.status_code))

        # Show sample data for successful requests
        if r.status_code == 200:
            data = r.json()
            if 'total' in data:
                print(f"{status} {name:<25} → {data['total']} items")
            elif 'symbol' in data:
                if 'metrics' in data:
                    print(f"{status} {name:<25} → {data['symbol']}: {data['metrics']['total_return_pct']:.2f}% return")
                else:
                    print(f"{status} {name:<25} → {data['symbol']}")
            elif 'status' in data and data['status'] == 'healthy':
                print(f"{status} {name:<25} → {data['service']}")
            elif 'name' in data:
                params_count = len(data['parameters']) if isinstance(data['parameters'], dict) else 0
                print(f"{status} {name:<25} → {data['name']} ({params_count} params)")
            else:
                print(f"{status} {name:<25} → OK")
        else:
            print(f"{status} {name:<25} → Status {r.status_code}")
    except Exception as e:
        tests.append(('✗', name, 'ERROR'))
        print(f"✗ {name:<25} → {str(e)[:30]}")

passed = sum(1 for s, _, _ in tests if s == '✓')
print(f"\n{'='*60}")
print(f"Results: {passed}/{len(tests)} endpoints working")
print(f"{'='*60}\n")

if passed == len(tests):
    print("🎉 All API endpoints working correctly!")
else:
    print(f"⚠️  {len(tests) - passed} endpoint(s) need attention")
