import { redirect } from 'next/navigation'

// Consolidated: "My Progress" is /dashboard/learner (decision C — redirect, not delete).
export default function ProgressRedirect() {
  redirect('/dashboard/learner')
}
