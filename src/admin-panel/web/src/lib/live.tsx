import { useQueryClient } from "@tanstack/react-query"
import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react"

import { queryKeys } from "@/lib/queries"
import type {
  ActivityEntry,
  ControlEvent,
  ControlId,
  JoystickSnapshot,
  PressEvent,
  SoundLiveState,
  SoundSnapshot,
  Status,
} from "@/lib/types"

type LearnedListener = (control: ControlId, event: ControlEvent) => void

interface LiveContextValue {
  /** Whether the live event stream from the panel server is connected */
  connected: boolean
  /** When each control was last used on the box, for flashing it in the UI */
  lastPressed: Record<ControlId, number>
  /** Subscribe to the next control learned in learn mode */
  onLearned: (listener: LearnedListener) => () => void
}

const LiveContext = createContext<LiveContextValue | null>(null)

/**
 * Listens to the server's event stream and keeps the query cache up to date, so presses on the box and changes made
 * elsewhere (another tab, the box's mode button) show up straight away.
 */
export function LiveEventsProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [connected, setConnected] = useState(false)
  const [lastPressed, setLastPressed] = useState<Record<ControlId, number>>({})
  const learnedListeners = useRef(new Set<LearnedListener>())

  useEffect(() => {
    const source = new EventSource("/api/events")

    source.onopen = () => {
      setConnected(true)
      // Anything could have changed while disconnected
      queryClient.invalidateQueries()
    }
    source.onerror = () => setConnected(false)

    const on = <T,>(type: string, handler: (data: T) => void) =>
      source.addEventListener(type, (message) => handler(JSON.parse((message as MessageEvent).data).data))

    on<Status>("status", (status) => queryClient.setQueryData(queryKeys.status, status))

    on<PressEvent>("press", ({ control, event }) => {
      queryClient.setQueryData<Status>(queryKeys.status, (status) =>
        status ? { ...status, states: { ...status.states, [control]: event }, lastEvent: new Date().toISOString() } : status
      )
      if (event === "on") setLastPressed((previous) => ({ ...previous, [control]: Date.now() }))
    })

    on<ActivityEntry>("activity", (entry) => {
      queryClient.setQueryData<ActivityEntry[]>(queryKeys.activity, (entries) =>
        entries ? [entry, ...entries.filter((e) => e.id !== entry.id)].slice(0, 100) : entries
      )
      queryClient.invalidateQueries({ queryKey: queryKeys.activityLog })
    })

    on("configuration", () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.status })
      queryClient.invalidateQueries({ queryKey: queryKeys.configurations })
    })

    on<JoystickSnapshot>("joystick", (snapshot) =>
      queryClient.setQueryData<JoystickSnapshot>(queryKeys.joystick, (current) => ({ ...current, ...snapshot }))
    )

    on<SoundLiveState>("sound", (state) =>
      queryClient.setQueryData<SoundSnapshot>(queryKeys.sound, (current) =>
        current ? { ...current, state: { ...current.state, ...state } } : current
      )
    )

    on("changed", () => queryClient.invalidateQueries())

    on<{ control: ControlId; event: ControlEvent }>("learned", ({ control, event }) =>
      learnedListeners.current.forEach((listener) => listener(control, event))
    )

    return () => source.close()
  }, [queryClient])

  const onLearned = useCallback((listener: LearnedListener) => {
    learnedListeners.current.add(listener)
    return () => {
      learnedListeners.current.delete(listener)
    }
  }, [])

  return <LiveContext.Provider value={{ connected, lastPressed, onLearned }}>{children}</LiveContext.Provider>
}

export function useLive() {
  const context = useContext(LiveContext)
  if (!context) throw new Error("useLive must be used inside LiveEventsProvider")
  return context
}
