'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function InfrastructureRedirect() {
  const router = useRouter()
  useEffect(() => { router.replace('/infrastructure') }, [router])
  return null
}
