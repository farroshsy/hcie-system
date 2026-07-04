import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from './providers'
import { WebVitals } from '@/components/analytics/WebVitals'
import { GlobalLanguageToggle } from '@/components/i18n/GlobalLanguageToggle'

// Enable MSW in development
if (process.env.NODE_ENV === 'development') {
  import('@/mocks')
}

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'HCIE - Adaptive Learning Platform',
  description: 'Hierarchical Contextual Intelligence Engine for Adaptive Learning',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        {/* Preload KaTeX fonts for better performance */}
        <link rel="preload" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/fonts/KaTeX_Main-Regular.woff2" as="font" type="font/woff2" crossOrigin="anonymous" />
        <link rel="preload" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/fonts/KaTeX_Math-Italic.woff2" as="font" type="font/woff2" crossOrigin="anonymous" />
        <link rel="preload" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/fonts/KaTeX_Size2-Regular.woff2" as="font" type="font/woff2" crossOrigin="anonymous" />
      </head>
      <body className={inter.className}>
        <WebVitals />
        <a href="#main-content" className="skip-to-main">
          Skip to main content
        </a>
        {/*
          GlobalLanguageToggle is rendered OUTSIDE <Providers> so it survives
          any provider hydration delay or error in the rest of the tree. It
          reads/writes localStorage directly and the LanguageProvider listens
          for the same custom event, so the two stay in sync. The result: the
          floating EN | ID control is present on every route, every paint.
        */}
        <GlobalLanguageToggle />
        <Providers>
          <main id="main-content">
            {children}
          </main>
        </Providers>
      </body>
    </html>
  )
}
