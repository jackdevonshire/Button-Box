import { useEffect, useState } from "react"

import { cn } from "@/lib/utils"
import type { Binding, Control, ControlEvent, ControlId } from "@/lib/types"

const FLASH_MS = 700

interface PanelViewProps {
  controls: Control[]
  states: Record<ControlId, ControlEvent>
  bindings: Binding[]
  display: string[]
  lastPressed: Record<ControlId, number>
  selected: ControlId | null
  onSelect: (control: ControlId) => void
}

/** A replica of the physical box: the LCD, push buttons, toggle switches and covered switches, lit up live */
export function PanelView({ controls, states, bindings, display, lastPressed, selected, onSelect }: PanelViewProps) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-4 shadow-inner sm:p-6">
      <div className="grid grid-cols-[repeat(5,minmax(0,1fr))_0.5rem_repeat(2,minmax(0,1fr))] grid-rows-[repeat(4,auto)] items-center gap-x-1 gap-y-3 sm:gap-x-2">
        <Lcd lines={display} className="col-span-4 col-start-2 row-span-2 row-start-1 mx-1 sm:mx-3" />
        {controls.map((control) => (
          <PanelControl
            key={control.id}
            control={control}
            state={states[control.id]}
            bindings={bindings.filter((binding) => binding.control === control.id)}
            pressedAt={lastPressed[control.id]}
            selected={selected === control.id}
            onSelect={() => onSelect(control.id)}
          />
        ))}
      </div>
    </div>
  )
}

export function Lcd({ lines, className }: { lines: string[]; className?: string }) {
  const rows = [...lines, "", "", "", ""].slice(0, 4)
  return (
    <div
      className={cn(
        "rounded-md border-4 border-zinc-800 bg-blue-950 px-2 py-3",
        className
      )}
      aria-label={`Screen: ${rows.filter(Boolean).join(", ") || "blank"}`}
    >
      {rows.map((line, index) => (
        <div
          key={index}
          className="h-[1.4em] truncate text-center font-mono text-xs tracking-[0.2em] whitespace-pre text-blue-200 sm:text-sm"
        >
          {line}
        </div>
      ))}
    </div>
  )
}

interface PanelControlProps {
  control: Control
  state: ControlEvent | undefined
  bindings: Binding[]
  pressedAt: number | undefined
  selected: boolean
  onSelect: () => void
}

function PanelControl({ control, state, bindings, pressedAt, selected, onSelect }: PanelControlProps) {
  const flashing = useRecent(pressedAt, FLASH_MS)
  const on = state === "on"
  const summary = bindingSummary(bindings)

  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      aria-label={`${control.label}, ${summary ?? "unmapped"}${state ? `, currently ${state}` : ""}`}
      style={{ gridRow: control.row, gridColumn: control.column }}
      className={cn(
        "group flex min-w-0 flex-col items-center gap-1.5 rounded-lg px-0.5 py-1.5 outline-none transition-colors",
        "hover:bg-white/5 focus-visible:ring-2 focus-visible:ring-sky-400",
        selected && "bg-white/10 ring-1 ring-white/30"
      )}
    >
      <span className="relative flex h-12 items-center justify-center">
        {control.kind === "button" && <PushButton on={on} />}
        {control.kind === "toggle" && <ToggleSwitch state={state} />}
        {control.kind === "protected" && <ProtectedSwitch state={state} />}
        {flashing && (
          <span
            key={pressedAt}
            className="pointer-events-none absolute inset-0 m-auto size-12 animate-[press-ripple_700ms_ease-out_forwards] rounded-full border-2 border-emerald-400"
          />
        )}
      </span>
      <span
        className={cn(
          "w-full truncate text-center text-[11px] leading-tight",
          summary ? "text-zinc-300" : "text-zinc-600 italic"
        )}
      >
        {summary ?? control.label}
      </span>
    </button>
  )
}

function PushButton({ on }: { on: boolean }) {
  return (
    <span
      className={cn(
        "flex size-10 items-center justify-center rounded-full border-2 transition-colors",
        on ? "border-emerald-400 bg-emerald-400/25" : "border-zinc-500 bg-zinc-800"
      )}
    >
      <span className={cn("size-6 rounded-full transition-colors", on ? "bg-emerald-300/80" : "bg-zinc-600")} />
    </span>
  )
}

function ToggleSwitch({ state }: { state: ControlEvent | undefined }) {
  return (
    <span className="relative flex h-12 w-7 justify-center rounded-md border-2 border-zinc-600 bg-zinc-900">
      <span
        className={cn(
          "absolute size-3.5 rounded-full transition-all",
          state === "on" && "top-1 bg-emerald-300",
          state === "off" && "bottom-1 bg-zinc-400",
          state === undefined && "top-1/2 -translate-y-1/2 bg-zinc-600"
        )}
      />
    </span>
  )
}

function ProtectedSwitch({ state }: { state: ControlEvent | undefined }) {
  return (
    <span
      className={cn(
        "flex h-12 w-8 items-start justify-center rounded-sm border-2 pt-1 transition-colors",
        state === "on" ? "border-red-300 bg-red-500" : "border-red-900 bg-red-700",
        state === undefined && "opacity-80"
      )}
    >
      <span className={cn("h-1 w-4 rounded-full", state === "on" ? "bg-red-100" : "bg-red-950/60")} />
    </span>
  )
}

function bindingSummary(bindings: Binding[]) {
  const enabled = bindings.filter((binding) => binding.enabled)
  if (enabled.length === 0) return null
  // Prefer what happens on a plain press/switch-on, as that's what the control is mostly "for"
  const primary =
    enabled.find((binding) => binding.event === "on" && binding.modifiers.length === 0) ?? enabled[0]
  const name = primary.name || primary.action.name
  return enabled.length > 1 ? `${name} +${enabled.length - 1}` : name
}

/** True for `duration` ms after `timestamp` */
function useRecent(timestamp: number | undefined, duration: number) {
  const [recent, setRecent] = useState(false)
  useEffect(() => {
    if (!timestamp) return
    const remaining = timestamp + duration - Date.now()
    if (remaining <= 0) return
    setRecent(true)
    const timer = setTimeout(() => setRecent(false), remaining)
    return () => clearTimeout(timer)
  }, [timestamp, duration])
  return recent
}
