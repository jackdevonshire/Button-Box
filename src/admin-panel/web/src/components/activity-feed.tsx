import { AlertCircle, Info, MousePointerClick, Play } from "lucide-react"

import type { ActivityEntry } from "@/lib/types"
import { cn } from "@/lib/utils"

const kindIcons = {
  press: MousePointerClick,
  action: Play,
  error: AlertCircle,
  system: Info,
}

export function formatTime(timestamp: string) {
  return new Date(timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
}

export function ActivityFeed({ entries, className }: { entries: ActivityEntry[]; className?: string }) {
  if (entries.length === 0) {
    return <p className="py-6 text-center text-sm text-muted-foreground">Presses on the box will show up here.</p>
  }

  return (
    <ol className={cn("flex flex-col", className)}>
      {entries.map((entry) => {
        const Icon = kindIcons[entry.kind] ?? Info
        const error = entry.kind === "error"
        return (
          <li key={entry.id} className="flex items-start gap-3 py-1.5 text-sm">
            <time className="w-16 shrink-0 pt-px font-mono text-xs text-muted-foreground tabular-nums">
              {formatTime(entry.timestamp)}
            </time>
            <Icon className={cn("mt-0.5 size-3.5 shrink-0", error ? "text-destructive" : "text-muted-foreground")} />
            <div className="min-w-0">
              <p className={cn("truncate", error && "text-destructive")}>{entry.title}</p>
              {entry.detail && <p className="truncate text-xs text-muted-foreground">{entry.detail}</p>}
            </div>
          </li>
        )
      })}
    </ol>
  )
}
