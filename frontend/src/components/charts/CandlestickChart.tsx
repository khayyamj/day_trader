import { useEffect, useRef, useState } from 'react'
import { createChart, IChartApi, ISeriesApi, CandlestickData, HistogramData, LineData, SeriesMarker, Time } from 'lightweight-charts'
import { marketDataAPI, indicatorsAPI, signalsAPI } from '@services/api'
import type { OHLCVData, Signal } from '@types/index'

interface CandlestickChartProps {
  symbol: string
}

export default function CandlestickChart({ symbol }: CandlestickChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null)
  const ema20SeriesRef = useRef<ISeriesApi<'Line'> | null>(null)
  const ema50SeriesRef = useRef<ISeriesApi<'Line'> | null>(null)
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

    const volumeSeries = chart.addHistogramSeries({
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: 'volume',
    })

    chart.priceScale('volume').applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    })

    const ema20Series = chart.addLineSeries({
      color: '#2962FF',
      lineWidth: 2,
      title: 'EMA 20',
    })

    const ema50Series = chart.addLineSeries({
      color: '#FF6D00',
      lineWidth: 2,
      title: 'EMA 50',
    })

    chartRef.current = chart
    seriesRef.current = candlestickSeries
    volumeSeriesRef.current = volumeSeries
    ema20SeriesRef.current = ema20Series
    ema50SeriesRef.current = ema50Series

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
      if (!seriesRef.current || !volumeSeriesRef.current) return

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

        const volumeData: HistogramData[] = data.map((item: OHLCVData, index: number) => {
          const isUp = index === 0 || item.close >= item.open
          return {
            time: new Date(item.time).getTime() / 1000,
            value: item.volume,
            color: isUp ? '#26a69a80' : '#ef535080',
          }
        })

        seriesRef.current.setData(formattedData)
        volumeSeriesRef.current.setData(volumeData)

        try {
          const indicators = await indicatorsAPI.calculate(symbol, ['ema_20', 'ema_50'])

          if (indicators.ema_20 && ema20SeriesRef.current) {
            const ema20Data: LineData[] = indicators.ema_20.map((item) => ({
              time: new Date(item.timestamp).getTime() / 1000,
              value: item.value,
            }))
            ema20SeriesRef.current.setData(ema20Data)
          }

          if (indicators.ema_50 && ema50SeriesRef.current) {
            const ema50Data: LineData[] = indicators.ema_50.map((item) => ({
              time: new Date(item.timestamp).getTime() / 1000,
              value: item.value,
            }))
            ema50SeriesRef.current.setData(ema50Data)
          }
        } catch (indicatorErr) {
          console.warn('Indicators not available:', indicatorErr)
        }

        try {
          const signals = await signalsAPI.getRecent(symbol, 50)
          const markers: SeriesMarker<Time>[] = signals.map((signal: Signal) => ({
            time: new Date(signal.timestamp).getTime() / 1000 as Time,
            position: signal.signal_type === 'buy' ? 'belowBar' : 'aboveBar',
            color: signal.signal_type === 'buy' ? '#26a69a' : '#ef5350',
            shape: signal.signal_type === 'buy' ? 'arrowUp' : 'arrowDown',
            text: signal.signal_type === 'buy' ? 'BUY' : 'SELL',
          }))

          if (seriesRef.current && markers.length > 0) {
            seriesRef.current.setMarkers(markers)
          }
        } catch (signalErr) {
          console.warn('Signals not available:', signalErr)
        }

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
