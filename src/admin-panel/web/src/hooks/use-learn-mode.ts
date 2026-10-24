import { useEffect, useRef, useState } from "react"
import { toast } from "sonner"

import { api } from "@/lib/api"
import { useLive } from "@/lib/live"

/** Puts the box in learn mode: the next control used on it is reported, instead of running its actions */
export function useLearnMode(onLearned: (control: string) => void) {
  const { onLearned: subscribe } = useLive()
  const [deadline, setDeadline] = useState<number | null>(null)
  const [now, setNow] = useState(() => Date.now())
  const onLearnedRef = useRef(onLearned)
  useEffect(() => {
    onLearnedRef.current = onLearned
  })

  useEffect(() => {
    if (deadline === null) return
    const unsubscribe = subscribe((control) => {
      setDeadline(null)
      onLearnedRef.current(control)
    })
    const timer = setInterval(() => {
      setNow(Date.now())
      if (Date.now() > deadline) {
        setDeadline(null)
        toast("Nothing was pressed on the box")
      }
    }, 250)
    return () => {
      unsubscribe()
      clearInterval(timer)
    }
  }, [deadline, subscribe])

  const start = async () => {
    try {
      const { seconds } = await api.startLearning()
      setNow(Date.now())
      setDeadline(Date.now() + seconds * 1000)
    } catch (e) {
      toast.error((e as Error).message)
    }
  }

  return {
    active: deadline !== null,
    secondsLeft: deadline === null ? 0 : Math.max(0, Math.ceil((deadline - now) / 1000)),
    start,
  }
}
