import { Link } from "react-router-dom"
import { FileQuestion } from "lucide-react"

import { Empty, EmptyHeader, EmptyTitle, EmptyDescription, EmptyMedia, EmptyContent } from "./empty"
import { Button } from "./button"

export function NotFoundPage() {
  return (
    <div className="flex h-screen w-screen items-center justify-center p-6 bg-black">
      <Empty className="max-w-md border-zinc-800 bg-zinc-950/40 text-white">
        <EmptyHeader>
          <EmptyMedia variant="icon" className="bg-zinc-900 border border-zinc-800 text-blue-500">
            <FileQuestion className="size-6" />
          </EmptyMedia>
          <EmptyTitle className="text-xl font-bold font-rajdhani">404 - Page Not Found</EmptyTitle>
          <EmptyDescription className="text-zinc-400">
            The page you are looking for does not exist or has been relocated.
          </EmptyDescription>
        </EmptyHeader>
        <EmptyContent>
          <Button asChild variant="outline" className="border-zinc-800 hover:bg-zinc-900 text-white">
            <Link to="/dashboard">Back to Dashboard</Link>
          </Button>
        </EmptyContent>
      </Empty>
    </div>
  )
}
