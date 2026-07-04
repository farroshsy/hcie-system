import { redirect } from 'next/navigation'

// Consolidated: the live adaptive tutor is /learn (decision C — redirect, not delete).
export default function LearningRedirect() {
  redirect('/learn')
}
