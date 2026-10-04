import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Crosshair, Mouse } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Field, FieldContent, FieldDescription, FieldLabel } from "@/components/ui/field"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { Switch } from "@/components/ui/switch"
import { api } from "@/lib/api"
import { defaultMouseOutput, hatDirections, holdKeyOptions } from "@/lib/joystick"
import type { HatDirection, JoystickDevice, JoystickMapping, MouseOutput } from "@/lib/types"

const opposite: Record<HatDirection, HatDirection> = { up: "down", down: "up", left: "right", right: "left" }
const vectors: Record<HatDirection, [number, number]> = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] }
const PREVIEW_SCALE = 0.1 // The test pad is small, so it moves at a tenth of the real speed

interface HatLook {
  speed: number
  rampMs: number
  holdKey: string
  invertX: boolean
  invertY: boolean
}

/** Where a hat direction should look, given the invert settings */
function lookDirection(direction: HatDirection, settings: Pick<HatLook, "invertX" | "invertY">) {
  const horizontal = direction === "left" || direction === "right"
  return (horizontal ? settings.invertX : settings.invertY) ? opposite[direction] : direction
}

/**
 * One place to tune how the hat looks around: speed, ramp, invert and the key held while looking - applied to all
 * four hat directions together - with a test pad to try it without opening the game.
 */
export function HatLookCard({
  configurationId,
  device,
  mappings,
  held,
}: {
  configurationId: number
  device: JoystickDevice
  mappings: JoystickMapping[]
  held: HatDirection[]
}) {
  const queryClient = useQueryClient()
  const looks = Object.fromEntries(
    mappings
      .filter((m) => m.device === device.id && m.inputType === "hat" && m.outputType === "mouse")
      .map((m) => [m.input, m])
  ) as Partial<Record<HatDirection, JoystickMapping>>
  const complete = hatDirections.every((direction) => looks[direction])

  const setUp = useMutation({
    mutationFn: async () => {
      for (const direction of hatDirections) {
        if (looks[direction]) continue
        await api.createJoystickMapping(configurationId, {
          name: `Free look ${direction}`,
          device: device.id,
          inputType: "hat",
          input: direction,
          outputType: "mouse",
          output: defaultMouseOutput(null),
          enabled: true,
        })
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries()
      toast.success("The hat now looks around")
    },
    onError: (e: Error) => toast.error(e.message),
  })

  if (!complete) {
    return (
      <Card size="sm">
        <CardHeader>
          <CardTitle>Hat look</CardTitle>
          <CardDescription>Turn the view with the hat by moving the mouse - like Joystick Gremlin's hat to mouse.</CardDescription>
          <CardAction>
            <Button size="sm" onClick={() => setUp.mutate()} disabled={setUp.isPending}>
              <Mouse data-icon="inline-start" />
              Set up hat look
            </Button>
          </CardAction>
        </CardHeader>
      </Card>
    )
  }

  const up = looks.up!.output as MouseOutput
  const left = looks.left!.output as MouseOutput
  const current: HatLook = {
    speed: up.speed,
    rampMs: up.rampMs,
    holdKey: up.holdKey,
    invertX: (left.direction ?? "left") === "right",
    invertY: (up.direction ?? "up") === "down",
  }

  return <HatLookSettings key={JSON.stringify(current)} looks={looks as Record<HatDirection, JoystickMapping>} saved={current} held={held} />
}

function HatLookSettings({
  looks,
  saved,
  held,
}: {
  looks: Record<HatDirection, JoystickMapping>
  saved: HatLook
  held: HatDirection[]
}) {
  const queryClient = useQueryClient()
  // Sliders change this draft as they move, and save when let go
  const [draft, setDraft] = useState(saved)

  const save = useMutation({
    mutationFn: async (settings: HatLook) => {
      for (const direction of hatDirections) {
        const mapping = looks[direction]
        const target = lookDirection(direction, settings)
        await api.updateJoystickMapping(mapping.id, {
          output: {
            ...(mapping.output as MouseOutput),
            speed: settings.speed,
            rampMs: settings.rampMs,
            holdKey: settings.holdKey,
            direction: target === direction ? null : target,
          },
        })
      }
    },
    onSuccess: () => queryClient.invalidateQueries(),
    onError: (e: Error) => toast.error(e.message),
  })

  const update = (changes: Partial<HatLook>, persist = true) => {
    const next = { ...draft, ...changes }
    setDraft(next)
    if (persist) save.mutate(next)
  }

  return (
    <Card size="sm">
      <CardHeader>
        <CardTitle>Hat look</CardTitle>
        <CardDescription>Applies to all four hat directions. Try it on the test pad - push the hat.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-6 md:grid-cols-[minmax(0,1fr)_minmax(0,16rem)]">
        <div className="flex flex-col gap-5">
          <Field>
            <div className="flex items-center justify-between">
              <FieldLabel>Speed</FieldLabel>
              <span className="text-sm text-muted-foreground tabular-nums">{draft.speed} px/s</span>
            </div>
            <Slider
              min={100}
              max={5000}
              step={50}
              value={[draft.speed]}
              onValueChange={([speed]) => update({ speed }, false)}
              onValueCommit={([speed]) => update({ speed })}
              aria-label="Look speed"
            />
          </Field>
          <Field>
            <div className="flex items-center justify-between">
              <FieldLabel>Ramp up</FieldLabel>
              <span className="text-sm text-muted-foreground tabular-nums">
                {draft.rampMs === 0 ? "Instant" : `${draft.rampMs} ms`}
              </span>
            </div>
            <Slider
              min={0}
              max={1000}
              step={25}
              value={[draft.rampMs]}
              onValueChange={([rampMs]) => update({ rampMs }, false)}
              onValueCommit={([rampMs]) => update({ rampMs })}
              aria-label="Ramp up"
            />
          </Field>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field orientation="horizontal">
              <Switch id="invert-x" checked={draft.invertX} onCheckedChange={(invertX) => update({ invertX })} />
              <FieldLabel htmlFor="invert-x">Invert left / right</FieldLabel>
            </Field>
            <Field orientation="horizontal">
              <Switch id="invert-y" checked={draft.invertY} onCheckedChange={(invertY) => update({ invertY })} />
              <FieldLabel htmlFor="invert-y">Invert up / down</FieldLabel>
            </Field>
          </div>
          <Field orientation="horizontal">
            <FieldContent>
              <FieldLabel>Hold while looking</FieldLabel>
              <FieldDescription>
                Alt snaps back to forward when you let go. Nothing keeps the view where you leave it, once free look is
                locked in game.
              </FieldDescription>
            </FieldContent>
            <Select value={draft.holdKey || "none"} onValueChange={(value) => update({ holdKey: value === "none" ? "" : value })}>
              <SelectTrigger size="sm" className="w-28">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {holdKeyOptions.map((option) => (
                  <SelectItem key={option.value || "none"} value={option.value || "none"}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>
        </div>
        <TestPad settings={draft} held={held} />
      </CardContent>
    </Card>
  )
}

/** Moves a crosshair the way the view would turn, using the same speed, ramp and invert as the real thing */
function TestPad({ settings, held }: { settings: HatLook; held: HatDirection[] }) {
  const pad = useRef<HTMLDivElement>(null)
  const dot = useRef<HTMLDivElement>(null)
  const position = useRef({ x: 0, y: 0 })
  const live = useRef({ settings, held })
  const pressedAt = useRef<Partial<Record<HatDirection, number>>>({})

  useEffect(() => {
    live.current = { settings, held }
    const now = performance.now()
    for (const direction of hatDirections) {
      if (held.includes(direction)) pressedAt.current[direction] ??= now
      else delete pressedAt.current[direction]
    }
  }, [settings, held])

  useEffect(() => {
    let frame = 0
    let last = performance.now()
    const step = (now: number) => {
      const seconds = (now - last) / 1000
      last = now
      const { settings: current, held: directions } = live.current
      for (const direction of directions) {
        const started = pressedAt.current[direction] ?? now
        const ramp = current.rampMs / 1000
        const elapsed = (now - started) / 1000
        // Same ramp as the panel: start at a quarter speed and build up
        const factor = ramp > 0 ? Math.min(1, 0.25 + (0.75 * elapsed) / ramp) : 1
        const [vx, vy] = vectors[lookDirection(direction, current)]
        const distance = current.speed * factor * PREVIEW_SCALE * seconds
        position.current.x += vx * distance
        position.current.y += vy * distance
      }
      const bounds = pad.current?.getBoundingClientRect()
      if (bounds) {
        const maxX = bounds.width / 2 - 8
        const maxY = bounds.height / 2 - 8
        position.current.x = Math.max(-maxX, Math.min(maxX, position.current.x))
        position.current.y = Math.max(-maxY, Math.min(maxY, position.current.y))
      }
      if (dot.current) dot.current.style.transform = `translate(${position.current.x}px, ${position.current.y}px)`
      frame = requestAnimationFrame(step)
    }
    frame = requestAnimationFrame(step)
    return () => cancelAnimationFrame(frame)
  }, [])

  return (
    <div className="flex flex-col gap-2">
      <div
        ref={pad}
        className="relative flex aspect-square w-full items-center justify-center overflow-hidden rounded-lg border bg-zinc-950"
        aria-label="Test pad: push the hat to move the crosshair"
      >
        <span className="absolute inset-x-0 top-1/2 h-px bg-zinc-800" />
        <span className="absolute inset-y-0 left-1/2 w-px bg-zinc-800" />
        <div ref={dot} className="relative text-emerald-400">
          <Crosshair className="size-4" />
        </div>
      </div>
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>Shown at a tenth of real speed</span>
        <Button
          size="xs"
          variant="ghost"
          onClick={() => {
            position.current = { x: 0, y: 0 }
          }}
        >
          Recentre
        </Button>
      </div>
    </div>
  )
}
