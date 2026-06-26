'use client'

import { ServiceProvider } from '@/contexts/service_context'
import { ConfigProvider } from '@/contexts/config_context'
import { AuthProvider } from '@/contexts/auth_context'
import { LanguageProvider } from '@/contexts/language_context'
import { QueryClientProvider } from '@/components/providers/QueryClientProvider'
import { WebSocketProvider } from '@/components/providers/WebSocketProvider'
import { RouteGuard } from '@/components/auth/RouteGuard'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider>
      <ServiceProvider>
        <ConfigProvider>
          <AuthProvider>
            <LanguageProvider>
              <WebSocketProvider>
                <RouteGuard>{children}</RouteGuard>
              </WebSocketProvider>
            </LanguageProvider>
          </AuthProvider>
        </ConfigProvider>
      </ServiceProvider>
    </QueryClientProvider>
  )
}
