import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import PositionsTable from '../PositionsTable';
import { positionsAPI } from '@services/api';

vi.mock('@services/api', () => ({
  positionsAPI: {
    getAll: vi.fn(),
  },
}));

vi.mock('@hooks/useRealTimeData', () => ({
  useRealTimeData: () => ({
    getPrice: vi.fn((symbol: string) => {
      const prices: Record<string, number> = {
        AAPL: 150,
        GOOGL: 2800,
      };
      return prices[symbol];
    }),
  }),
}));

describe('PositionsTable', () => {
  const mockPositions = [
    {
      id: 1,
      symbol: 'AAPL',
      quantity: 10,
      entry_price: 145,
      current_price: 150,
      entry_time: '2024-01-01T10:00:00Z',
      status: 'open',
      stop_loss: 140,
      take_profit: 160,
      entry_reason: 'EMA crossover',
    },
    {
      id: 2,
      symbol: 'GOOGL',
      quantity: 5,
      entry_price: 2850,
      current_price: 2800,
      entry_time: '2024-01-02T10:00:00Z',
      status: 'open',
      stop_loss: 2750,
      take_profit: 2950,
      entry_reason: 'RSI oversold',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    vi.mocked(positionsAPI.getAll).mockImplementation(
      () => new Promise(() => {})
    );

    render(<PositionsTable />);
    expect(screen.getByText('Loading positions...')).toBeInTheDocument();
  });

  it('renders positions table with data', async () => {
    vi.mocked(positionsAPI.getAll).mockResolvedValue(mockPositions);

    render(<PositionsTable />);

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('GOOGL')).toBeInTheDocument();
    });
  });

  it('displays "No open positions" when no positions exist', async () => {
    vi.mocked(positionsAPI.getAll).mockResolvedValue([]);

    render(<PositionsTable />);

    await waitFor(() => {
      expect(screen.getByText('No open positions')).toBeInTheDocument();
    });
  });

  it('displays error message when fetch fails', async () => {
    vi.mocked(positionsAPI.getAll).mockRejectedValue(new Error('Network error'));

    render(<PositionsTable />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load positions')).toBeInTheDocument();
    });
  });

  it('calculates P&L correctly for profit position', async () => {
    vi.mocked(positionsAPI.getAll).mockResolvedValue(mockPositions);

    render(<PositionsTable />);

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
    });

    const pnl = (150 - 145) * 10;
    expect(screen.getByText(`$${pnl.toFixed(2)}`)).toBeInTheDocument();

    const pnlPercent = ((150 - 145) / 145) * 100;
    expect(screen.getByText(`+${pnlPercent.toFixed(2)}%`)).toBeInTheDocument();
  });

  it('calculates P&L correctly for loss position', async () => {
    vi.mocked(positionsAPI.getAll).mockResolvedValue(mockPositions);

    render(<PositionsTable />);

    await waitFor(() => {
      expect(screen.getByText('GOOGL')).toBeInTheDocument();
    });

    const pnl = (2800 - 2850) * 5;
    expect(screen.getByText(`-$${Math.abs(pnl).toFixed(2)}`)).toBeInTheDocument();

    const pnlPercent = ((2800 - 2850) / 2850) * 100;
    expect(screen.getByText(`${pnlPercent.toFixed(2)}%`)).toBeInTheDocument();
  });

  it('applies correct color class for profit', async () => {
    vi.mocked(positionsAPI.getAll).mockResolvedValue([mockPositions[0]]);

    render(<PositionsTable />);

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
    });

    const pnlCells = screen.getAllByText(/\$50\.00|3\.45%/);
    pnlCells.forEach((cell) => {
      expect(cell).toHaveClass('text-green-600');
    });
  });

  it('applies correct color class for loss', async () => {
    vi.mocked(positionsAPI.getAll).mockResolvedValue([mockPositions[1]]);

    render(<PositionsTable />);

    await waitFor(() => {
      expect(screen.getByText('GOOGL')).toBeInTheDocument();
    });

    const pnlCells = screen.getAllByText(/-?\$250\.00|-?1\.75%/);
    pnlCells.forEach((cell) => {
      expect(cell).toHaveClass('text-red-600');
    });
  });

  it('expands position details when expand button is clicked', async () => {
    vi.mocked(positionsAPI.getAll).mockResolvedValue([mockPositions[0]]);

    render(<PositionsTable />);

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
    });

    expect(screen.queryByText('Entry Reason:')).not.toBeInTheDocument();

    const expandButton = screen.getByText('▼');
    fireEvent.click(expandButton);

    await waitFor(() => {
      expect(screen.getByText('Entry Reason:')).toBeInTheDocument();
      expect(screen.getByText('EMA crossover')).toBeInTheDocument();
      expect(screen.getByText('Stop Loss:')).toBeInTheDocument();
      expect(screen.getByText('$140.00')).toBeInTheDocument();
    });

    expect(screen.getByText('▲')).toBeInTheDocument();
  });

  it('collapses position details when collapse button is clicked', async () => {
    vi.mocked(positionsAPI.getAll).mockResolvedValue([mockPositions[0]]);

    render(<PositionsTable />);

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
    });

    const expandButton = screen.getByText('▼');
    fireEvent.click(expandButton);

    await waitFor(() => {
      expect(screen.getByText('Entry Reason:')).toBeInTheDocument();
    });

    const collapseButton = screen.getByText('▲');
    fireEvent.click(collapseButton);

    await waitFor(() => {
      expect(screen.queryByText('Entry Reason:')).not.toBeInTheDocument();
    });
  });

  it('filters out closed positions', async () => {
    const positionsWithClosed = [
      ...mockPositions,
      {
        id: 3,
        symbol: 'TSLA',
        quantity: 5,
        entry_price: 700,
        current_price: 720,
        entry_time: '2024-01-03T10:00:00Z',
        status: 'closed',
      },
    ];

    vi.mocked(positionsAPI.getAll).mockResolvedValue(positionsWithClosed);

    render(<PositionsTable />);

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('GOOGL')).toBeInTheDocument();
    });

    expect(screen.queryByText('TSLA')).not.toBeInTheDocument();
  });

  it('displays all table headers', async () => {
    vi.mocked(positionsAPI.getAll).mockResolvedValue(mockPositions);

    render(<PositionsTable />);

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
    });

    expect(screen.getByText('Symbol')).toBeInTheDocument();
    expect(screen.getByText('Qty')).toBeInTheDocument();
    expect(screen.getByText('Entry')).toBeInTheDocument();
    expect(screen.getByText('Current')).toBeInTheDocument();
    expect(screen.getByText('P&L')).toBeInTheDocument();
    expect(screen.getByText('P&L%')).toBeInTheDocument();
    expect(screen.getByText('Actions')).toBeInTheDocument();
  });
});
