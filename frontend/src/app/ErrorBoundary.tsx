import { Component, type ErrorInfo, type ReactNode } from 'react'
import { StatusState } from '../shared/ui/StatusState'
import { clientTelemetry } from '../shared/telemetry/clientTelemetry'

type Props = {
  children: ReactNode
}

type State = {
  hasError: boolean
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    clientTelemetry.record('ui_error_boundary')
    console.error('ui.error_boundary', { error, info })
  }

  render() {
    if (this.state.hasError) {
      return <StatusState title="Интерфейс временно недоступен" variant="error" action={{ label: 'Перезагрузить страницу', onClick: () => window.location.reload() }}>Не удалось отобразить игру. Перезагрузите страницу, чтобы заново получить состояние мира.</StatusState>
    }

    return this.props.children
  }
}

