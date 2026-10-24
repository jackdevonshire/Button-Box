import { cn } from "@/lib/utils"

const FLOOR = -60  // dB at the left of the bar
const AUDIBLE = -50 // Louder than this counts as something playing

/** A live level bar for what comes out of the virtual cable - exactly what the game hears */
export function CableMeter({ level, className }: { level: number | null; className?: string }) {
  if (level === null) return null
  const audible = level > AUDIBLE
  const width = Math.min(100, Math.max(0, ((level - FLOOR) / -FLOOR) * 100))

  return (
    <div className={cn("flex items-center gap-3", className)}>
      <span className="w-24 shrink-0 text-xs text-muted-foreground">Game hears</span>
      <div
        className="relative h-2 flex-1 overflow-hidden rounded-full bg-muted"
        role="meter"
        aria-label="What the game hears"
        aria-valuemin={FLOOR}
        aria-valuemax={0}
        aria-valuenow={Math.max(FLOOR, level)}
      >
        <span
          className={cn(
            "absolute inset-y-0 left-0 rounded-full transition-[width] duration-100 ease-linear",
            audible ? "bg-emerald-500" : "bg-foreground/25"
          )}
          style={{ width: `${width}%` }}
        />
      </div>
      <span className={cn("w-14 shrink-0 text-right text-xs tabular-nums", audible ? "text-emerald-600 dark:text-emerald-400" : "text-muted-foreground")}>
        {audible ? `${Math.round(level)} dB` : "Silent"}
      </span>
    </div>
  )
}
