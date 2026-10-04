import { useMutation, useQueryClient } from "@tanstack/react-query"
import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  Gamepad2,
  MoreHorizontal,
  Pencil,
  Plus,
  PowerOff,
  ScanLine,
  Trash2,
} from "lucide-react"
import { useEffect, useRef, useState } from "react"
import { useSearchParams } from "react-router"
import { toast } from "sonner"

import { HatLookCard } from "@/components/joystick/hat-look-card"
import { MappingDialog, type MappingTarget } from "@/components/joystick/mapping-dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Empty, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { api } from "@/lib/api"
import { hatDirections, inputKey, inputLabel, mappingTitle, outputSummary } from "@/lib/joystick"
import { useActions, useJoystick } from "@/lib/queries"
import type { Configuration, HatDirection, JoystickDevice, JoystickDeviceState, JoystickMapping } from "@/lib/types"
import { cn } from "@/lib/utils"

const PICK_SECONDS = 8
const hatIcons = { up: ArrowUp, down: ArrowDown, left: ArrowLeft, right: ArrowRight }

/** The joystick half of the panel page: a live view of the stick and this configuration's mappings */
export function JoystickView({ configuration }: { configuration: Configuration }) {
  const { data: joystick } = useJoystick()
  const { data: actions = [] } = useActions()
  const [searchParams, setSearchParams] = useSearchParams()
  const [dialog, setDialog] = useState<{ mapping?: JoystickMapping; target?: MappingTarget } | null>(null)

  const mappings = configuration.joystickMappings ?? []
  const devices = withDisconnected(joystick?.devices ?? [], mappings)
  const deviceId = searchParams.get("device") ?? devices[0]?.id
  const device = devices.find((d) => d.id === deviceId)
  const connected = joystick?.devices.some((d) => d.id === deviceId) ?? false
  const state = deviceId ? joystick?.states[deviceId] : undefined
  const deviceMappings = mappings.filter((mapping) => mapping.device === deviceId)

  const selected = searchParams.get("input")
  const select = (key: string) =>
    setSearchParams((params) => {
      params.set("view", "joystick")
      params.set("input", key)
      return params
    })
  const picking = usePickFromStick(state, select)

  if (!joystick) return null

  if (!device) {
    return (
      <Empty className="border border-dashed">
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <Gamepad2 />
          </EmptyMedia>
          <EmptyTitle>Plug in a joystick</EmptyTitle>
          <EmptyDescription>
            Once Windows can see it, it shows up here and you can map its hat and buttons for this configuration.
          </EmptyDescription>
        </EmptyHeader>
      </Empty>
    )
  }

  const [selectedType, selectedInput] = (selected ?? "").split(":") as ["hat" | "button" | "", string]

  return (
    <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_380px]">
      <div className="flex min-w-0 flex-col gap-4">
        {joystick.active === false && <InactiveNotice />}

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {devices.length > 1 ? (
                <Select
                  value={deviceId}
                  onValueChange={(id) =>
                    setSearchParams((params) => {
                      params.set("device", id)
                      params.delete("input")
                      return params
                    })
                  }
                >
                  <SelectTrigger size="sm" className="w-56">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {devices.map((d) => (
                      <SelectItem key={d.id} value={d.id}>
                        {d.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                device.name
              )}
              <Badge variant={connected ? "secondary" : "outline"}>{connected ? "Connected" : "Not connected"}</Badge>
            </CardTitle>
            <CardDescription>Use the stick and its controls light up here. Select one to map it.</CardDescription>
            <CardAction>
              <Button variant="outline" size="sm" onClick={picking.start} disabled={picking.active || !connected}>
                <ScanLine data-icon="inline-start" />
                {picking.active ? `Press something… ${picking.secondsLeft}` : "Pick from the stick"}
              </Button>
            </CardAction>
          </CardHeader>
          <CardContent className="flex flex-col gap-6 sm:flex-row sm:items-start">
            {device.hasHat && (
              <HatPad
                held={state?.hat ?? []}
                mapped={new Set(deviceMappings.filter((m) => m.inputType === "hat").map((m) => m.input))}
                selected={selectedType === "hat" ? selectedInput : null}
                onSelect={(direction) => select(inputKey("hat", direction))}
              />
            )}
            <div className="flex min-w-0 flex-1 flex-col gap-4">
              <ButtonGrid
                count={device.buttons}
                held={new Set(state?.buttons ?? [])}
                mapped={new Set(deviceMappings.filter((m) => m.inputType === "button").map((m) => Number(m.input)))}
                selected={selectedType === "button" ? Number(selectedInput) : null}
                onSelect={(button) => select(inputKey("button", String(button)))}
              />
              {state && <AxisBars axes={state.axes} />}
            </div>
          </CardContent>
        </Card>

        {device.hasHat && (
          <HatLookCard
            configurationId={configuration.id}
            device={device}
            mappings={deviceMappings}
            held={state?.hat ?? []}
          />
        )}

        <Card size="sm">
          <CardHeader>
            <CardTitle>Mappings in {configuration.name}</CardTitle>
            <CardDescription>Only active while this configuration is.</CardDescription>
          </CardHeader>
          <CardContent>
            {deviceMappings.length === 0 ? (
              <p className="text-sm text-muted-foreground">Nothing mapped yet. Select a hat direction or button to start.</p>
            ) : (
              <ul className="divide-y rounded-lg border">
                {deviceMappings.map((mapping) => (
                  <li key={mapping.id}>
                    <button
                      type="button"
                      onClick={() => select(inputKey(mapping.inputType, mapping.input))}
                      className={cn(
                        "flex w-full items-center gap-3 px-3 py-2 text-left text-sm hover:bg-muted/50",
                        !mapping.enabled && "opacity-60"
                      )}
                    >
                      <Badge variant="outline" className="w-20 shrink-0 justify-center">
                        {inputLabel(mapping.inputType, mapping.input)}
                      </Badge>
                      <span className="truncate">{mappingTitle(mapping, actions)}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="lg:sticky lg:top-4">
        {selectedType ? (
          <InputInspector
            device={device}
            inputType={selectedType}
            input={selectedInput}
            held={selectedType === "hat" ? !!state?.hat.includes(selectedInput as HatDirection) : !!state?.buttons.includes(Number(selectedInput))}
            mappings={deviceMappings.filter((m) => m.inputType === selectedType && m.input === selectedInput)}
            onAdd={() => setDialog({ target: { inputType: selectedType, input: selectedInput } })}
            onEdit={(mapping) => setDialog({ mapping })}
          />
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Choose an input</CardTitle>
              <CardDescription>
                Click a hat direction or button, or use "Pick from the stick" and press it. Each can look around with the
                mouse, hold keys, or run an action.
              </CardDescription>
            </CardHeader>
          </Card>
        )}
      </div>

      <MappingDialog
        open={dialog !== null}
        onOpenChange={(open) => !open && setDialog(null)}
        configurationId={configuration.id}
        device={device}
        mapping={dialog?.mapping}
        target={dialog?.target}
      />
    </div>
  )
}

/** Devices that have mappings but aren't plugged in still need to be listed, so their mappings can be managed */
function withDisconnected(devices: JoystickDevice[], mappings: JoystickMapping[]) {
  const all = [...devices]
  for (const mapping of mappings) {
    if (!all.some((device) => device.id === mapping.device)) {
      all.push({ id: mapping.device, name: `Joystick ${mapping.device}`, axes: 0, buttons: 32, hasHat: true })
    }
  }
  return all
}

function HatPad({
  held,
  mapped,
  selected,
  onSelect,
}: {
  held: HatDirection[]
  mapped: Set<string>
  selected: string | null
  onSelect: (direction: HatDirection) => void
}) {
  const positions = { up: "col-start-2 row-start-1", left: "col-start-1 row-start-2", right: "col-start-3 row-start-2", down: "col-start-2 row-start-3" }
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="grid grid-cols-3 grid-rows-3 gap-1">
        {hatDirections.map((direction) => {
          const Icon = hatIcons[direction]
          const isHeld = held.includes(direction)
          return (
            <button
              key={direction}
              type="button"
              onClick={() => onSelect(direction)}
              aria-label={`Hat ${direction}${mapped.has(direction) ? ", mapped" : ""}`}
              aria-pressed={selected === direction}
              className={cn(
                "relative flex size-11 items-center justify-center rounded-lg border bg-muted/40 transition-colors hover:bg-muted",
                positions[direction],
                isHeld && "border-emerald-500 bg-emerald-500/20 text-emerald-600 dark:text-emerald-300",
                selected === direction && "ring-2 ring-primary"
              )}
            >
              <Icon className="size-4" />
              {mapped.has(direction) && <span className="absolute top-1 right-1 size-1.5 rounded-full bg-primary" />}
            </button>
          )
        })}
        <span
          className={cn(
            "col-start-2 row-start-2 m-auto size-4 rounded-full border-2",
            held.length > 0 ? "border-emerald-500 bg-emerald-500/40" : "border-muted-foreground/40"
          )}
        />
      </div>
      <span className="text-xs text-muted-foreground">Hat</span>
    </div>
  )
}

function ButtonGrid({
  count,
  held,
  mapped,
  selected,
  onSelect,
}: {
  count: number
  held: Set<number>
  mapped: Set<number>
  selected: number | null
  onSelect: (button: number) => void
}) {
  return (
    <div className="flex flex-col gap-2">
      <div className="grid grid-cols-[repeat(auto-fill,minmax(2.5rem,1fr))] gap-1.5">
        {Array.from({ length: count }, (_, i) => i + 1).map((button) => (
          <button
            key={button}
            type="button"
            onClick={() => onSelect(button)}
            aria-label={`Button ${button}${mapped.has(button) ? ", mapped" : ""}`}
            aria-pressed={selected === button}
            className={cn(
              "relative flex h-9 items-center justify-center rounded-md border bg-muted/40 text-xs tabular-nums transition-colors hover:bg-muted",
              held.has(button) && "border-emerald-500 bg-emerald-500/20 text-emerald-700 dark:text-emerald-300",
              selected === button && "ring-2 ring-primary"
            )}
          >
            {button}
            {mapped.has(button) && <span className="absolute top-1 right-1 size-1.5 rounded-full bg-primary" />}
          </button>
        ))}
      </div>
      <span className="text-xs text-muted-foreground">Buttons</span>
    </div>
  )
}

function AxisBars({ axes }: { axes: Record<string, number> }) {
  return (
    <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 sm:grid-cols-4">
      {Object.entries(axes).map(([axis, value]) => (
        <div key={axis} className="flex items-center gap-2">
          <span className="w-3 text-xs text-muted-foreground uppercase">{axis}</span>
          <div className="relative h-1.5 flex-1 rounded-full bg-muted">
            <span
              className="absolute top-0 h-full w-1 -translate-x-1/2 rounded-full bg-foreground/70"
              style={{ left: `${((value + 1) / 2) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

function InputInspector({
  device,
  inputType,
  input,
  held,
  mappings,
  onAdd,
  onEdit,
}: {
  device: JoystickDevice
  inputType: "hat" | "button"
  input: string
  held: boolean
  mappings: JoystickMapping[]
  onAdd: () => void
  onEdit: (mapping: JoystickMapping) => void
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{inputLabel(inputType, input)}</CardTitle>
        <CardDescription>{device.name}</CardDescription>
        <CardAction>
          <Badge variant={held ? "default" : "outline"}>{held ? "Held" : "Released"}</Badge>
        </CardAction>
      </CardHeader>
      <CardContent className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium">While held</h3>
          <Button size="xs" variant="ghost" onClick={onAdd}>
            <Plus data-icon="inline-start" />
            Add
          </Button>
        </div>
        {mappings.length === 0 ? (
          <p className="rounded-lg border border-dashed px-3 py-2.5 text-sm text-muted-foreground">Nothing happens yet.</p>
        ) : (
          <ul className="divide-y rounded-lg border">
            {mappings.map((mapping) => (
              <MappingRow key={mapping.id} mapping={mapping} onEdit={() => onEdit(mapping)} />
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}

function MappingRow({ mapping, onEdit }: { mapping: JoystickMapping; onEdit: () => void }) {
  const queryClient = useQueryClient()
  const { data: actions = [] } = useActions()

  const update = useMutation({
    mutationFn: (enabled: boolean) => api.updateJoystickMapping(mapping.id, { enabled }),
    onSuccess: () => queryClient.invalidateQueries(),
    onError: (e: Error) => toast.error(e.message),
  })
  const remove = useMutation({
    mutationFn: () => api.deleteJoystickMapping(mapping.id),
    onSuccess: () => {
      queryClient.invalidateQueries()
      toast.success("Mapping removed")
    },
    onError: (e: Error) => toast.error(e.message),
  })

  return (
    <li className={cn("flex items-center gap-3 px-3 py-2.5", !mapping.enabled && "opacity-60")}>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{mappingTitle(mapping, actions)}</p>
        {mapping.name && <p className="truncate text-xs text-muted-foreground">{outputSummary(mapping, actions)}</p>}
      </div>
      <Switch
        checked={mapping.enabled}
        onCheckedChange={(enabled) => update.mutate(enabled)}
        aria-label={mapping.enabled ? "Disable mapping" : "Enable mapping"}
      />
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button size="icon-sm" variant="ghost" aria-label="Mapping options">
            <MoreHorizontal />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onSelect={onEdit}>
            <Pencil />
            Edit
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem variant="destructive" onSelect={() => remove.mutate()}>
            <Trash2 />
            Remove
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </li>
  )
}

function InactiveNotice() {
  const queryClient = useQueryClient()
  const enable = useMutation({
    mutationFn: () => api.setIntegrationActive(5, true),
    onSuccess: () => {
      queryClient.invalidateQueries()
      toast.success("Joystick turned on")
    },
    onError: (e: Error) => toast.error(e.message),
  })
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm">
      <PowerOff className="size-4 text-amber-600 dark:text-amber-400" />
      <p className="flex-1">The Joystick integration is turned off, so these mappings won't do anything.</p>
      <Button size="sm" variant="outline" onClick={() => enable.mutate()} disabled={enable.isPending}>
        Turn on
      </Button>
    </div>
  )
}

/** Selects the next hat direction or button pressed on the stick */
function usePickFromStick(state: JoystickDeviceState | undefined, onPick: (key: string) => void) {
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
