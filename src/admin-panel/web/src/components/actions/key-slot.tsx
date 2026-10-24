import { Keyboard } from "lucide-react"
import { useRef, useState } from "react"

import { Kbd } from "@/components/ui/kbd"
import { keyFromEvent, keyLabel } from "@/lib/keys"
import { cn } from "@/lib/utils"

/** Modifier flags on a key event, and the key names that count as that modifier being recorded */
const modifiers: ["ctrlKey" | "shiftKey" | "altKey", string[]][] = [
  ["ctrlKey", ["ctrl", "ctrlleft", "ctrlright"]],
  ["shiftKey", ["shift", "shiftleft", "shiftright"]],
  ["altKey", ["alt", "altleft", "altright"]],
]

/**
 * Click, then press a key or a combination - it's recorded once every key is let go. Click away or press nothing
 * to leave it as it was.
 */
export function KeySlot({
  label,
  keys,
  supported,
  placeholder,
  single = false,
  className,
  onRecord,
}: {
  label: string
  keys: string[]
  supported: Set<string>
  placeholder: string
  /** Record just one key rather than a combination - the last one pressed */
  single?: boolean
  className?: string
  onRecord: (keys: string[]) => void
}) {
  const [recording, setRecording] = useState(false)
  const [pressed, setPressed] = useState<string[]>([])
  const down = useRef(new Set<string>())
  const [problem, setProblem] = useState<string | null>(null)

  const onKeyDown = (event: React.KeyboardEvent) => {
    // Capture everything, including Tab and Esc, rather than letting the page act on it
    event.preventDefault()
    event.stopPropagation()
    if (event.repeat) return
    const key = keyFromEvent(event)
    if (!key || (supported.size > 0 && !supported.has(key))) {
      setProblem(`${key ? keyLabel(key) : "That key"} can't be sent`)
      return
    }
    setProblem(null)
    down.current.add(key)
    if (single) return setPressed([key])
    setPressed((current) => {
      // Some tools (remote desktop, macros) send a key with Ctrl/Shift/Alt flagged but never the modifier's own press
      const held = modifiers.filter(
        ([flag, names]) => event[flag] && !names.includes(key) && !names.some((name) => current.includes(name))
      )
      const next = [...current, ...held.map(([, names]) => names[0])]
      return next.includes(key) ? next : [...next, key]
    })
  }

  const onKeyUp = (event: React.KeyboardEvent) => {
    event.preventDefault()
    const key = keyFromEvent(event)
    if (key) down.current.delete(key)
    if (down.current.size === 0 && pressed.length > 0) {
      onRecord(pressed)
      ;(event.currentTarget as HTMLElement).blur()
    }
  }

  const shown = recording && pressed.length > 0 ? pressed : keys

  return (
    <button
      type="button"
      onKeyDown={onKeyDown}
      onKeyUp={onKeyUp}
      onFocus={() => {
        setRecording(true)
        setPressed([])
        setProblem(null)
        down.current.clear()
      }}
      onBlur={() => {
        setRecording(false)
        setPressed([])
        down.current.clear()
      }}
      aria-label={label}
      title={problem ?? (keys.length ? "Click, then press a different key" : "Click, then press a key")}
      className={cn(
        "flex h-7 min-w-0 flex-1 items-center gap-1 rounded-md px-2 text-left text-sm outline-none transition-colors hover:bg-muted",
        recording && "bg-primary/5 ring-2 ring-primary",
        className
      )}
    >
      {problem && recording ? (
        <span className="truncate text-xs text-destructive">{problem}</span>
      ) : recording && shown.length === 0 ? (
        <span className="flex items-center gap-1.5 truncate text-xs text-foreground">
          <Keyboard className="size-3.5 shrink-0" />
          Press a key…
        </span>
      ) : shown.length > 0 ? (
        shown.map((key, index) => (
          <span key={key} className="flex items-center gap-1">
            {index > 0 && <span className="text-xs text-muted-foreground">+</span>}
            <Kbd>{keyLabel(key)}</Kbd>
          </span>
        ))
      ) : (
        <span className="truncate text-xs text-muted-foreground">{placeholder}</span>
      )}
    </button>
  )
}
