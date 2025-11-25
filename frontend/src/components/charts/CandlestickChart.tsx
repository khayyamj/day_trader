import { useEffect, useRef, useState } from 'react'
import { createChart, IChartApi, ISeriesApi, CandlestickData } from 'lightweight-charts'
import { marketDataAPI } from '@services/api'
import type { OHLCVData } from '@types/index'

interface CandlestickChartProps {
  symbol: string
}

export default function CandlestickChart({ symbol }: CandlestickChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!chartContainerRef.current) return

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 500,
      layout: {
        background: { color: '#ffffff' },
        textColor: '#333',
      },
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
      },
      crosshair: {
        mode: 1,
      },
      timeScale: {
        borderColor: '#cccccc',
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: '#cccccc',
      },
    })

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    })

    chartRef.current = chart
    seriesRef.current = candlestickSeries

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        })
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [])

  useEffect(() => {
    const fetchData = async () => {
      if (!seriesRef.current) return

      setIsLoading(true)
      setError(null)

      try {
        const data = await marketDataAPI.getOHLCV(symbol, '1d', 100)

        const formattedData: CandlestickData[] = data.map((item: OHLCVData) => ({
          time: new Date(item.time).getTime() / 1000,
          open: item.open,
          high: item.high,
          low: item.low,
          close: item.close,
        }))

        seriesRef.current.setData(formattedData)

        if (chartRef.current && formattedData.length > 0) {
          chartRef.current.timeScale().fitContent()
        }
      } catch (err) {
        console.error('Error fetching OHLCV data:', err)
        setError('Failed to load chart data. Please check if the backend is running.')
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
  }, [symbol])

  return (
    <div className="relative">
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-50 bg-opacity-75 z-10">
          <div className="text-gray-600">Loading chart data...</div>
        </div>
      )}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-red-50 z-10">
          <div className="text-red-600 text-center p-4">
            <p className="font-semibold mb-2">Error Loading Chart</p>
            <p className="text-sm">{error}</p>
          </div>
        </div>
      )}
      <div ref={chartContainerRef} className="w-full" />
    </div>
  )
}
