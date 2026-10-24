import { Code, Gamepad2, Keyboard, Layers, Plug, Terminal, Volume2, type LucideIcon } from "lucide-react"

import type { Control, ControlEvent, ControlKind } from "@/lib/types"

/** How a control's events read in the UI - buttons are pressed and released, switches are switched on and off */
export function eventLabel(kind: ControlKind | undefined, event: ControlEvent) {
  if (kind === "button") return event === "on" ? "Pressed" : "Released"
  return event === "on" ? "Switched on" : "Switched off"
}

export function shortEventLabel(kind: ControlKind | undefined, event: ControlEvent) {
  if (kind === "button") return event === "on" ? "press" : "release"
  return event
}

export const kindLabels: Record<ControlKind, string> = {
  button: "Push button",
  toggle: "Toggle switch",
  protected: "Protected switch",
}

export function controlLabel(controls: Control[] | undefined, id: string) {
  return controls?.find((control) => control.id === id)?.label ?? id
}

const integrationIcons: Record<string, LucideIcon> = {
  keyboard: Keyboard,
  layers: Layers,
  terminal: Terminal,
  code: Code,
  gamepad: Gamepad2,
  volume: Volume2,
}

export function integrationIcon(icon: string | undefined): LucideIcon {
  return (icon && integrationIcons[icon]) || Plug
}

/** Icon for an action's integration, by integration id */
export const integrationIconById: Record<number, LucideIcon> = {
  1: Keyboard,
  2: Layers,
  3: Terminal,
  4: Code,
  6: Volume2,
}
