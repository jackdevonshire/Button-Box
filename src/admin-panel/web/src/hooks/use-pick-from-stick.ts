import { useEffect, useRef, useState } from "react"
import { toast } from "sonner"

import { inputKey } from "@/lib/joystick"
import type { JoystickDeviceState } from "@/lib/types"

const PICK_SECONDS = 8

/** Selects the next hat direction or button pressed on the stick */
export function usePickFromStick(state: JoystickDeviceState | undefined, onPick: (key: string) => void) {
  const [deadline, setDeadline] = useState<number | null>(null)
  const [now, setNow] = useState(() => Date.now())
  const previous = useRef<Set<string>>(new Set())
  const onPickRef = useRef(onPick)
  useEffect(() => {
    onPickRef.current = onPick
  })

  // Watch for anything newly pressed while picking
  useEffect(() => {
    const current = new Set([
      ...(state?.hat ?? []).map((direction) => inputKey("hat", direction)),
      ...(state?.buttons ?? []).map((button) => inputKey("button", String(button))),
    ])
    if (deadline !== null) {
      const pressed = [...current].find((key) => !previous.current.has(key))
      if (pressed) {
        setDeadline(null)
        onPickRef.current(pressed)
      }
    }
    previous.current = current
  }, [state, deadline])

  useEffect(() => {
    if (deadline === null) return
    const timer = setInterval(() => {
      setNow(Date.now())
      if (Date.now() > deadline) {
        setDeadline(null)
        toast("Nothing was pressed on the stick")
      }
    }, 250)
    return () => clearInterval(timer)
  }, [deadline])

  return {
    active: deadline !== null,
    secondsLeft: deadline === null ? 0 : Math.max(0, Math.ceil((deadline - now) / 1000)),
    start: () => {
      setNow(Date.now())
      setDeadline(Date.now() + PICK_SECONDS * 1000)
    },
  }
}
