interface StockSelectorProps {
  selectedStock: string
  onStockChange: (stock: string) => void
}

export default function StockSelector({ selectedStock, onStockChange }: StockSelectorProps) {
  const stocks = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA']

  return (
    <div className="flex items-center gap-2">
      <label htmlFor="stock-selector" className="text-sm font-medium text-gray-700">
        Symbol:
      </label>
      <select
        id="stock-selector"
        value={selectedStock}
        onChange={(e) => onStockChange(e.target.value)}
        className="px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
      >
        {stocks.map((stock) => (
          <option key={stock} value={stock}>
            {stock}
          </option>
        ))}
      </select>
    </div>
  )
}
