import { useMutation } from "@tanstack/react-query"
import { Radar, ScanLine, WifiOff } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import { useSearchParams } from "react-router"
import { toast } from "sonner"

import { ActivityFeed } from "@/components/activity-feed"
import { ControlInspector } from "@/components/panel/control-inspector"
import { PanelView } from "@/components/panel/panel-view"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Empty, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"
import { useLive } from "@/lib/live"
import { useActivity, useConfiguration, useControls, useStatus } from "@/lib/queries"

export function PanelPage() {
  const { data: status } = useStatus()
  const { data: controls } = useControls()
  const { data: configuration } = useConfiguration(status?.activeConfigurationId)
  const { data: activity = [] } = useActivity()
  const { lastPressed } = useLive()
  const [searchParams, setSearchParams] = useSearchParams()
  const learning = useLearnMode((control) => setSearchParams({ control }))

  const selectedId = searchParams.get("control")
  const selected = controls?.find((control) => control.id === selectedId)
  const bindings = configuration?.bindings ?? []

  if (!status || !controls || !configuration) {
    return (
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_380px]">
        <Skeleton className="h-96 rounded-2xl" />
        <Skeleton className="h-96 rounded-xl" />
      </div>
    )
  }

  return (
    <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_380px]">
      <div className="flex min-w-0 flex-col gap-4">
        {!status.online && <OfflineNotice scanning={status.scanning} />}

        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h1 className="text-xl font-semibold">{configuration.name}</h1>
            <p className="text-sm text-muted-foreground">
              {configuration.description || "Select a control to see or change what it does."}
            </p>
          </div>
          <Button variant="outline" onClick={learning.start} disabled={learning.active}>
            <ScanLine data-icon="inline-start" />
            {learning.active ? `Use a control on the box… ${learning.secondsLeft}` : "Pick from the box"}
          </Button>
        </div>

        <PanelView
          controls={controls}
          states={status.states}
          bindings={bindings}
          display={status.display}
          lastPressed={lastPressed}
          selected={selectedId}
          onSelect={(control) => setSearchParams({ control })}
        />

        <Card size="sm">
          <CardHeader>
            <CardTitle>Recent activity</CardTitle>
          </CardHeader>
          <CardContent>
            <ActivityFeed entries={activity.slice(0, 8)} />
          </CardContent>
        </Card>
      </div>

      <div className="lg:sticky lg:top-4">
        {selected ? (
          <ControlInspector
            control={selected}
            state={status.states[selected.id]}
            bindings={bindings.filter((binding) => binding.control === selected.id)}
            configurationId={configuration.id}
          />
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Choose a control</CardTitle>
              <CardDescription>
                Click a control on the panel, or use "Pick from the box" and press it for real.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Empty className="border border-dashed">
                <EmptyHeader>
                  <EmptyMedia variant="icon">
                    <Radar />
                  </EmptyMedia>
                  <EmptyTitle>Nothing selected</EmptyTitle>
                  <EmptyDescription>
                    Each control can do something when it's pressed or switched on, and when it's released or switched
                    off.
                  </EmptyDescription>
                </EmptyHeader>
              </Empty>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

function OfflineNotice({ scanning }: { scanning: boolean }) {
  const find = useMutation({
    mutationFn: api.findBox,
    onSuccess: (status) => toast.success(`Found the box at ${status.buttonBoxIp}`),
    onError: (e: Error) => toast.error(e.message),
  })
  const busy = scanning || find.isPending

  return (
    <div className="flex flex-wrap items-center gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm">
      <WifiOff className="size-4 text-amber-600 dark:text-amber-400" />
      <p className="flex-1">
        {busy ? "Looking for the box on your network…" : "The box isn't responding. Presses won't arrive until it's back."}
      </p>
      <Button size="sm" variant="outline" onClick={() => find.mutate()} disabled={busy}>
        Find box
      </Button>
    </div>
  )
}

/** Learn mode: the next control used on the box is reported (and its actions skipped) */
function useLearnMode(onLearned: (control: string) => void) {
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
