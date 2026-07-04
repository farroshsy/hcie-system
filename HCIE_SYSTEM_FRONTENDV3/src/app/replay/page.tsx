import { redirect } from 'next/navigation'

// Consolidated: researcher replay/trace is /review/replay (decision C).
export default function ReplayRedirect() {
  redirect('/review/replay')
}
