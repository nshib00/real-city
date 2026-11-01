import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'

import { App } from './app/App'
import { queryClient } from './app/providers/queryClient'
import './app/styles/index.css'
import './app/styles/layout.css'
import './app/styles/context-panels.css'
import './app/styles/responsive-controls.css'
import './app/styles/motion.css'
import './app/styles/aeolian.css'
import './app/styles/control-states.css'
import './app/styles/object-marks.css'
import './app/styles/start.css'
import { clientTelemetry, installClientTelemetry } from './shared/telemetry/clientTelemetry'

installClientTelemetry()

createRoot(document.getElementById('root') as HTMLElement, {
  onUncaughtError: () => clientTelemetry.record('render_error'),
  onCaughtError: () => clientTelemetry.record('render_error'),
}).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
)
