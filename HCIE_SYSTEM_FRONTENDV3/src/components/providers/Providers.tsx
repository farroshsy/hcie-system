'use client'

import { QueryClientProvider } from '@/components/providers/QueryClientProvider'
import { AuthProvider } from '@/components/providers/AuthProvider'
import { WebSocketProvider } from '@/components/providers/WebSocketProvider'
import { ReactNode } from 'react'

export function Providers({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider>
      <AuthProvider>
        <WebSocketProvider>
          {children}
        </WebSocketProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}
