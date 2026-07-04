import { redirect } from 'next/navigation'

// Retired: the old /cold-start hit a legacy /api/research/* route that no longer
// exists (always rendered empty). Cold-start AUC-vs-window is now live on
// /dashboard/benchmarks (the cold-start line chart). Redirect, don't fabricate.
export default function ColdStartRedirect() {
  redirect('/dashboard/benchmarks')
}
