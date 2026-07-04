// Enable MSW in development (browser only)
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  // Dynamic import to avoid SSR issues
  import('./browser').then(({ worker }) => {
    worker.start({
      onUnhandledRequest: 'bypass',
    })
  })
}

export {}
