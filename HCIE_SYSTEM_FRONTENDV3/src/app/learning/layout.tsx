/**
 * Learning Layout
 *
 * Layout for learning pages with consistent navigation and structure.
 * Uses Next.js App Router layout conventions.
 */

export default function LearningLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      <main>{children}</main>
    </div>
  )
}
