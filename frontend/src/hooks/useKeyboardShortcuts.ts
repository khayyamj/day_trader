import { useEffect } from 'react'

interface KeyboardShortcuts {
  onRefresh?: () => void
  onPauseToggle?: () => void
}

export function useKeyboardShortcuts({ onRefresh, onPauseToggle }: KeyboardShortcuts) {
  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
        return
      }

      switch (event.key.toLowerCase()) {
        case 'r':
          event.preventDefault()
          onRefresh?.()
          break
        case 'p':
          event.preventDefault()
          onPauseToggle?.()
          break
      }
    }

    window.addEventListener('keydown', handleKeyPress)

    return () => {
      window.removeEventListener('keydown', handleKeyPress)
    }
  }, [onRefresh, onPauseToggle])
}
