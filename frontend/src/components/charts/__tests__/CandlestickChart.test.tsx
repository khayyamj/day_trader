import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import CandlestickChart from '../CandlestickChart';
import { marketDataAPI, indicatorsAPI, signalsAPI } from '@services/api';

vi.mock('@services/api', () => ({
  marketDataAPI: {
    getOHLCV: vi.fn(),
  },
  indicatorsAPI: {
    calculate: vi.fn(),
  },
  signalsAPI: {
    getRecent: vi.fn(),
  },
}));

vi.mock('lightweight-charts', () => ({
  createChart: vi.fn(() => ({
    addCandlestickSeries: vi.fn(() => ({
      setData: vi.fn(),
      setMarkers: vi.fn(),
    })),
    addHistogramSeries: vi.fn(() => ({
      setData: vi.fn(),
    })),
    addLineSeries: vi.fn(() => ({
      setData: vi.fn(),
    })),
    priceScale: vi.fn(() => ({
      applyOptions: vi.fn(),
    })),
    timeScale: vi.fn(() => ({
      fitContent: vi.fn(),
    })),
    applyOptions: vi.fn(),
    remove: vi.fn(),
  })),
}));

describe('CandlestickChart', () => {
  const mockOHLCVData = [
    {
      time: '2024-01-01T00:00:00Z',
      open: 100,
      high: 105,
      low: 99,
      close: 103,
      volume: 1000000,
    },
    {
      time: '2024-01-02T00:00:00Z',
      open: 103,
      high: 108,
      low: 102,
      close: 107,
      volume: 1200000,
    },
  ];

  const mockIndicators = {
    ema_20: [
      { timestamp: '2024-01-01T00:00:00Z', value: 101 },
      { timestamp: '2024-01-02T00:00:00Z', value: 104 },
    ],
    ema_50: [
      { timestamp: '2024-01-01T00:00:00Z', value: 100 },
      { timestamp: '2024-01-02T00:00:00Z', value: 102 },
    ],
  };

  const mockSignals = [
    {
      timestamp: '2024-01-01T00:00:00Z',
      signal_type: 'buy',
      price: 100,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(marketDataAPI.getOHLCV).mockResolvedValue(mockOHLCVData);
    vi.mocked(indicatorsAPI.calculate).mockResolvedValue(mockIndicators);
    vi.mocked(signalsAPI.getRecent).mockResolvedValue(mockSignals);
  });

  it('renders loading state initially', () => {
    render(<CandlestickChart symbol="AAPL" />);
    expect(screen.getByText('Loading chart data...')).toBeInTheDocument();
  });

  it('fetches and displays chart data', async () => {
    render(<CandlestickChart symbol="AAPL" />);

    await waitFor(() => {
      expect(marketDataAPI.getOHLCV).toHaveBeenCalledWith('AAPL', '1d', 100);
    });

    await waitFor(() => {
      expect(screen.queryByText('Loading chart data...')).not.toBeInTheDocument();
    });
  });

  it('displays error message when data fetch fails', async () => {
    vi.mocked(marketDataAPI.getOHLCV).mockRejectedValue(new Error('Network error'));

    render(<CandlestickChart symbol="AAPL" />);

    await waitFor(() => {
      expect(screen.getByText('Error Loading Chart')).toBeInTheDocument();
      expect(screen.getByText(/Failed to load chart data/)).toBeInTheDocument();
    });
  });

  it('fetches indicators data', async () => {
    render(<CandlestickChart symbol="AAPL" />);

    await waitFor(() => {
      expect(indicatorsAPI.calculate).toHaveBeenCalledWith('AAPL', ['ema_20', 'ema_50']);
    });
  });

  it('fetches signals data', async () => {
    render(<CandlestickChart symbol="AAPL" />);

    await waitFor(() => {
      expect(signalsAPI.getRecent).toHaveBeenCalledWith('AAPL', 50);
    });
  });

  it('handles indicator fetch failure gracefully', async () => {
    vi.mocked(indicatorsAPI.calculate).mockRejectedValue(new Error('Indicator error'));

    render(<CandlestickChart symbol="AAPL" />);

    await waitFor(() => {
      expect(screen.queryByText('Loading chart data...')).not.toBeInTheDocument();
    });
  });

  it('handles signal fetch failure gracefully', async () => {
    vi.mocked(signalsAPI.getRecent).mockRejectedValue(new Error('Signal error'));

    render(<CandlestickChart symbol="AAPL" />);

    await waitFor(() => {
      expect(screen.queryByText('Loading chart data...')).not.toBeInTheDocument();
    });
  });

  it('refetches data when symbol changes', async () => {
    const { rerender } = render(<CandlestickChart symbol="AAPL" />);

    await waitFor(() => {
      expect(marketDataAPI.getOHLCV).toHaveBeenCalledWith('AAPL', '1d', 100);
    });

    rerender(<CandlestickChart symbol="GOOGL" />);

    await waitFor(() => {
      expect(marketDataAPI.getOHLCV).toHaveBeenCalledWith('GOOGL', '1d', 100);
    });
  });
});
