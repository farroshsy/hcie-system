import { redirect } from 'next/navigation'

// Consolidated: task history lives in the learner dashboard (decision C).
export default function TasksRedirect() {
  redirect('/dashboard/learner')
}
