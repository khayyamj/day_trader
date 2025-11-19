"""Test runner for all Phase 5 trading system manual tests."""
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Test configurations
TESTS = [
    {
        'name': 'IBKR Connection',
        'script': 'test_ibkr_connection.py',
        'phase': 1,
        'description': 'Verify connection to IBKR paper account',
        'required': True
    },
    {
        'name': 'Position Sizer',
        'script': 'test_position_sizer.py',
        'phase': 1,
        'description': 'Validate 2% risk rule calculations',
        'required': True
    },
    {
        'name': 'Market Order Submission',
        'script': 'test_order_submission.py',
        'phase': 2,
        'description': 'Test market order placement',
        'required': False
    },
    {
        'name': 'Stop-Loss Order',
        'script': 'test_stop_loss_order.py',
        'phase': 2,
        'description': 'Test broker-level stop-loss placement',
        'required': False
    },
    {
        'name': 'Risk Manager',
        'script': 'test_risk_manager.py',
        'phase': 3,
        'description': 'Validate all risk management rules',
        'required': True
    },
    {
        'name': 'Loss Limit Detector',
        'script': 'test_loss_limit.py',
        'phase': 3,
        'description': 'Test consecutive loss tracking and auto-pause',
        'required': True
    },
    {
        'name': 'Position Reconciliation',
        'script': 'test_position_reconciliation.py',
        'phase': 3,
        'description': 'Test broker/DB position reconciliation',
        'required': False
    },
    {
        'name': 'Full Execution Flow',
        'script': 'test_full_execution.py',
        'phase': 4,
        'description': 'Complete signal-to-order execution flow',
        'required': False
    }
]


def print_header(text):
    """Print formatted header."""
    print("\n" + "="*80)
    print(text.center(80))
    print("="*80)


def print_phase_header(phase_num):
    """Print phase header."""
    phase_names = {
        1: "Foundation Tests",
        2: "Order Submission Tests",
        3: "Risk Management Tests",
        4: "Integration Tests"
    }
    print(f"\n{'='*80}")
    print(f"PHASE {phase_num}: {phase_names.get(phase_num, 'Unknown')}".center(80))
    print(f"{'='*80}")


def run_test(test_info):
    """
    Run a single test script.

    Returns:
        tuple: (success: bool, output: str)
    """
    script_path = Path(__file__).parent / test_info['script']

    if not script_path.exists():
        return False, f"Script not found: {test_info['script']}"

    print(f"\n📋 Running: {test_info['name']}")
    print(f"   Description: {test_info['description']}")
    print(f"   Script: {test_info['script']}")
    print("-" * 80)

    try:
        # Run the test script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )

        # Print output
        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print("STDERR:", result.stderr)

        success = result.returncode == 0

        return success, result.stdout + result.stderr

    except subprocess.TimeoutExpired:
        return False, "Test timed out after 120 seconds"

    except Exception as e:
        return False, f"Test failed with error: {str(e)}"


def run_all_tests(skip_optional=False):
    """
    Run all tests in sequence.

    Args:
        skip_optional: Skip non-required tests (manual verification tests)
    """
    start_time = datetime.now()

    print_header("PHASE 5 TRADING SYSTEM - TEST SUITE")
    print(f"\nStart Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'Required tests only' if skip_optional else 'All tests'}")

    results = []
    current_phase = None

    for test in TESTS:
        # Skip optional tests if requested
        if skip_optional and not test['required']:
            print(f"\n⏭️  Skipping optional test: {test['name']}")
            continue

        # Print phase header when phase changes
        if test['phase'] != current_phase:
            current_phase = test['phase']
            print_phase_header(current_phase)

        # Run the test
        success, output = run_test(test)

        results.append({
            'name': test['name'],
            'script': test['script'],
            'success': success,
            'required': test['required'],
            'output': output
        })

        # Print immediate result
        if success:
            print(f"\n✅ PASSED: {test['name']}")
        else:
            print(f"\n❌ FAILED: {test['name']}")

            # Stop on required test failure
            if test['required']:
                print("\n⚠️  CRITICAL: Required test failed. Stopping test suite.")
                break

    # Print summary
    end_time = datetime.now()
    duration = end_time - start_time

    print_header("TEST SUMMARY")

    print(f"\nExecution Time: {duration.total_seconds():.2f} seconds")
    print(f"Total Tests: {len(results)}")

    passed = sum(1 for r in results if r['success'])
    failed = sum(1 for r in results if not r['success'])
    required_passed = sum(1 for r in results if r['success'] and r['required'])
    required_failed = sum(1 for r in results if not r['success'] and r['required'])

    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"\nRequired Tests: {required_passed} passed, {required_failed} failed")

    # Detailed results
    print("\n" + "="*80)
    print("DETAILED RESULTS")
    print("="*80)

    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        required = "REQUIRED" if result['required'] else "OPTIONAL"
        print(f"\n{status} [{required}] {result['name']}")
        print(f"   Script: {result['script']}")

    # Final verdict
    print("\n" + "="*80)

    if required_failed > 0:
        print("❌ CRITICAL FAILURES DETECTED")
        print("="*80)
        print("\nSome required tests failed. Please review and fix before proceeding.")
        return False
    elif failed > 0:
        print("⚠️  OPTIONAL TEST FAILURES")
        print("="*80)
        print("\nAll required tests passed, but some optional tests failed.")
        print("Review failures and perform manual verification where needed.")
        return True
    else:
        print("✅ ALL TESTS PASSED")
        print("="*80)
        print("\nExcellent! All tests passed successfully.")
        print("Your Phase 5 implementation is working correctly.")
        return True


def main():
    """Main entry point."""
    print("\n" + "="*80)
    print("PHASE 5 TRADING SYSTEM - AUTOMATED TEST RUNNER")
    print("="*80)

    print("\nThis script will run all Phase 5 manual tests in sequence.")
    print("\nTest Categories:")
    print("  1. Foundation Tests (REQUIRED) - Connection & calculations")
    print("  2. Order Tests (OPTIONAL) - Actual orders in paper account")
    print("  3. Risk Tests (REQUIRED) - Risk management validation")
    print("  4. Integration Tests (OPTIONAL) - Full execution flow")

    print("\n⚠️  WARNING:")
    print("  - Some tests submit real orders to your paper account")
    print("  - Ensure IB Gateway/TWS is running")
    print("  - Ensure you have sufficient buying power")

    print("\nOptions:")
    print("  1. Run all tests (required + optional)")
    print("  2. Run required tests only")
    print("  3. Cancel")

    choice = input("\nSelect option (1-3): ").strip()

    if choice == '1':
        run_all_tests(skip_optional=False)
    elif choice == '2':
        run_all_tests(skip_optional=True)
    else:
        print("\nTest run cancelled.")


if __name__ == "__main__":
    main()
