import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import StrategyPanel from '../StrategyPanel';
import { strategyAPI } from '@services/api';

vi.mock('@services/api', () => ({
  strategyAPI: {
    getAll: vi.fn(),
    activate: vi.fn(),
    pause: vi.fn(),
    updateParameters: vi.fn(),
  },
}));

vi.mock('../StrategyConfig', () => ({
  default: ({ onClose, onSave }: { onClose: () => void; onSave: (params: Record<string, unknown>) => void }) => (
    <div data-testid="strategy-config-modal">
      <button onClick={onClose}>Close</button>
      <button onClick={() => onSave({ ema_short: 20, ema_long: 50 })}>Save</button>
    </div>
  ),
}));

describe('StrategyPanel', () => {
  const mockStrategy = {
    id: 1,
    name: 'EMA Crossover Strategy',
    status: 'active' as const,
    consecutive_losses: 0,
    is_warming_up: false,
    parameters: {
      ema_short: 20,
      ema_long: 50,
      rsi_period: 14,
      rsi_oversold: 30,
      rsi_overbought: 70,
      stop_loss_pct: 2,
      take_profit_pct: 4,
      max_consecutive_losses: 3,
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    vi.mocked(strategyAPI.getAll).mockImplementation(
      () => new Promise(() => {})
    );

    render(<StrategyPanel />);
    expect(screen.getByText('Loading strategy...')).toBeInTheDocument();
  });

  it('renders strategy information when loaded', async () => {
    vi.mocked(strategyAPI.getAll).mockResolvedValue([mockStrategy]);

    render(<StrategyPanel />);

    await waitFor(() => {
      expect(screen.getByText('EMA Crossover Strategy')).toBeInTheDocument();
    });
  });

  it('displays error message when fetch fails', async () => {
    vi.mocked(strategyAPI.getAll).mockRejectedValue(new Error('Network error'));

    render(<StrategyPanel />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load strategy')).toBeInTheDocument();
    });
  });

  it('displays "No strategy found" when no strategies exist', async () => {
    vi.mocked(strategyAPI.getAll).mockResolvedValue([]);

    render(<StrategyPanel />);

    await waitFor(() => {
      expect(screen.getByText('No strategy found')).toBeInTheDocument();
    });
  });

  it('displays active status badge correctly', async () => {
    vi.mocked(strategyAPI.getAll).mockResolvedValue([mockStrategy]);

    render(<StrategyPanel />);

    await waitFor(() => {
      const badge = screen.getByText('Active');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('bg-green-100', 'text-green-800');
    });
  });

  it('displays paused status badge correctly', async () => {
    const pausedStrategy = { ...mockStrategy, status: 'paused' as const };
    vi.mocked(strategyAPI.getAll).mockResolvedValue([pausedStrategy]);

    render(<StrategyPanel />);

    await waitFor(() => {
      const badge = screen.getByText('Paused');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('bg-yellow-100', 'text-yellow-800');
    });
  });

  it('displays error status badge correctly', async () => {
    const errorStrategy = { ...mockStrategy, status: 'error' as const };
    vi.mocked(strategyAPI.getAll).mockResolvedValue([errorStrategy]);

    render(<StrategyPanel />);

    await waitFor(() => {
      const badge = screen.getByText('Error');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('bg-red-100', 'text-red-800');
    });
  });

  it('displays warming status badge correctly', async () => {
    const warmingStrategy = { ...mockStrategy, status: 'warming' as const, is_warming_up: true };
    vi.mocked(strategyAPI.getAll).mockResolvedValue([warmingStrategy]);

    render(<StrategyPanel />);

    await waitFor(() => {
      const badge = screen.getByText('Warming Up');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('bg-blue-100', 'text-blue-800');
    });
  });

  it('displays consecutive losses count', async () => {
    const strategyWithLosses = { ...mockStrategy, consecutive_losses: 2 };
    vi.mocked(strategyAPI.getAll).mockResolvedValue([strategyWithLosses]);

    render(<StrategyPanel />);

    await waitFor(() => {
      expect(screen.getByText('2 / 3')).toBeInTheDocument();
    });
  });

  it('displays pause button when strategy is active', async () => {
    vi.mocked(strategyAPI.getAll).mockResolvedValue([mockStrategy]);

    render(<StrategyPanel />);

    await waitFor(() => {
      expect(screen.getByText('Pause')).toBeInTheDocument();
    });

    expect(screen.queryByText('Activate')).not.toBeInTheDocument();
  });

  it('displays activate button when strategy is paused', async () => {
    const pausedStrategy = { ...mockStrategy, status: 'paused' as const };
    vi.mocked(strategyAPI.getAll).mockResolvedValue([pausedStrategy]);

    render(<StrategyPanel />);

    await waitFor(() => {
      expect(screen.getByText('Activate')).toBeInTheDocument();
    });

    expect(screen.queryByText('Pause')).not.toBeInTheDocument();
  });

  it('calls activate API when activate button is clicked', async () => {
    const pausedStrategy = { ...mockStrategy, status: 'paused' as const };
    const activatedStrategy = { ...mockStrategy, status: 'active' as const };
    vi.mocked(strategyAPI.getAll).mockResolvedValue([pausedStrategy]);
    vi.mocked(strategyAPI.activate).mockResolvedValue(activatedStrategy);

    render(<StrategyPanel />);

    await waitFor(() => {
      expect(screen.getByText('Activate')).toBeInTheDocument();
    });

    const activateButton = screen.getByText('Activate');
    fireEvent.click(activateButton);

    await waitFor(() => {
      expect(strategyAPI.activate).toHaveBeenCalledWith(1);
    });
  });

  it('calls pause API when pause button is clicked', async () => {
    const pausedStrategy = { ...mockStrategy, status: 'paused' as const };
    vi.mocked(strategyAPI.getAll).mockResolvedValue([mockStrategy]);
    vi.mocked(strategyAPI.pause).mockResolvedValue(pausedStrategy);

    render(<StrategyPanel />);

    await waitFor(() => {
      expect(screen.getByText('Pause')).toBeInTheDocument();
    });

    const pauseButton = screen.getByText('Pause');
    fireEvent.click(pauseButton);

    await waitFor(() => {
      expect(strategyAPI.pause).toHaveBeenCalledWith(1);
    });
  });

  it('opens configuration modal when configure button is clicked', async () => {
    vi.mocked(strategyAPI.getAll).mockResolvedValue([mockStrategy]);

    render(<StrategyPanel />);

    await waitFor(() => {
      expect(screen.getByText('Configure')).toBeInTheDocument();
    });

    const configureButton = screen.getByText('Configure');
    fireEvent.click(configureButton);

    await waitFor(() => {
      expect(screen.getByTestId('strategy-config-modal')).toBeInTheDocument();
    });
  });

  it('closes configuration modal and updates strategy when saved', async () => {
    const updatedStrategy = { ...mockStrategy };
    vi.mocked(strategyAPI.getAll).mockResolvedValue([mockStrategy]);
    vi.mocked(strategyAPI.updateParameters).mockResolvedValue(updatedStrategy);

    render(<StrategyPanel />);

    await waitFor(() => {
      expect(screen.getByText('Configure')).toBeInTheDocument();
    });

    const configureButton = screen.getByText('Configure');
    fireEvent.click(configureButton);

    await waitFor(() => {
      expect(screen.getByTestId('strategy-config-modal')).toBeInTheDocument();
    });

    const saveButton = screen.getByText('Save');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(strategyAPI.updateParameters).toHaveBeenCalledWith(1, { ema_short: 20, ema_long: 50 });
    });

    await waitFor(() => {
      expect(screen.queryByTestId('strategy-config-modal')).not.toBeInTheDocument();
    });
  });

  it('displays warm-up status when strategy is warming up', async () => {
    const warmingStrategy = { ...mockStrategy, is_warming_up: true };
    vi.mocked(strategyAPI.getAll).mockResolvedValue([warmingStrategy]);

    render(<StrategyPanel />);

    await waitFor(() => {
      expect(screen.getByText('Warm-up Status')).toBeInTheDocument();
      expect(screen.getByText('In Progress')).toBeInTheDocument();
    });
  });

  it('displays loading state on activate button when activating', async () => {
    const pausedStrategy = { ...mockStrategy, status: 'paused' as const };
    vi.mocked(strategyAPI.getAll).mockResolvedValue([pausedStrategy]);
    vi.mocked(strategyAPI.activate).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    render(<StrategyPanel />);

    await waitFor(() => {
      expect(screen.getByText('Activate')).toBeInTheDocument();
    });

    const activateButton = screen.getByText('Activate');
    fireEvent.click(activateButton);

    expect(screen.getByText('Activating...')).toBeInTheDocument();
  });

  it('displays loading state on pause button when pausing', async () => {
    vi.mocked(strategyAPI.getAll).mockResolvedValue([mockStrategy]);
    vi.mocked(strategyAPI.pause).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    render(<StrategyPanel />);

    await waitFor(() => {
      expect(screen.getByText('Pause')).toBeInTheDocument();
    });

    const pauseButton = screen.getByText('Pause');
    fireEvent.click(pauseButton);

    expect(screen.getByText('Pausing...')).toBeInTheDocument();
  });
});
