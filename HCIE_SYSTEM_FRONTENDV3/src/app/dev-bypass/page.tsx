'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useT } from '@/contexts/language_context'

export default function DevBypassPage() {
  const t = useT()
  const [isEnabled, setIsEnabled] = useState(false)
  const [isDevelopment, setIsDevelopment] = useState(false)

  useEffect(() => {
    // Check if running in development mode
    setIsDevelopment(process.env.NODE_ENV === 'development')
    
    // Check if bypass is already enabled
    const bypass = document.cookie
      .split('; ')
      .find(row => row.startsWith('dev_bypass='))
    
    if (bypass === 'dev_bypass=true') {
      setIsEnabled(true)
    }
  }, [])

  const enableBypass = () => {
    document.cookie = 'dev_bypass=true; path=/; max-age=86400'
    setIsEnabled(true)
    window.location.href = '/admin'
  }

  const disableBypass = () => {
    document.cookie = 'dev_bypass=; path=/; max-age=0'
    setIsEnabled(false)
  }

  if (!isDevelopment) {
    return (
      <div className="container mx-auto p-6">
        <Card className="max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle>{t('devBypass.title')}</CardTitle>
            <CardDescription>{t('devBypass.eyebrow')}</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-red-600">
              {t('devBypass.eyebrow')}
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6">
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle>{t('devBypass.title')}</CardTitle>
          <CardDescription>
            {t('devBypass.eyebrow')}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-sm text-yellow-800">
              <strong>⚠️ Development Only:</strong> This bypass only works in development mode and should never be used in production.
            </p>
          </div>

          <div className="space-y-2">
            <p className="text-sm font-medium">Current Status:</p>
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${isEnabled ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-sm">{isEnabled ? 'Enabled' : 'Disabled'}</span>
            </div>
          </div>

          <div className="space-y-2">
            <p className="text-sm font-medium">Actions:</p>
            <div className="flex gap-2">
              {!isEnabled ? (
                <Button onClick={enableBypass}>Enable Bypass</Button>
              ) : (
                <>
                  <Button onClick={() => window.location.href = '/admin'}>
                    Go to Admin
                  </Button>
                  <Button variant="outline" onClick={disableBypass}>
                    Disable Bypass
                  </Button>
                </>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <p className="text-sm font-medium">Protected Routes:</p>
            <ul className="text-sm text-gray-600 list-disc list-inside">
              <li>/admin - Admin dashboard and analytics</li>
              <li>/learning - Learning interface</li>
              <li>/progress - Progress tracking</li>
              <li>/profile - User profile</li>
              <li>/settings - User settings</li>
            </ul>
          </div>

          <div className="space-y-2">
            <p className="text-sm font-medium">How it works:</p>
            <p className="text-sm text-gray-600">
              Setting the dev_bypass cookie allows access to protected routes without requiring an auth_token.
              This is only active when NODE_ENV=development and the bypass cookie is set to 'true'.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
