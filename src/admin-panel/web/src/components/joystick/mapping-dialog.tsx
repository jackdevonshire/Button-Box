import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Keyboard, Mouse, Play } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"

import { ActionPicker } from "@/components/actions/action-picker"
import { KeyboardEditor } from "@/components/actions/keyboard-editor"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Field, FieldContent, FieldDescription, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { Switch } from "@/components/ui/switch"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { api } from "@/lib/api"
import {
  defaultMouseOutput,
  directionLabels,
  hatDirections,
  holdKeyOptions,
  inputKey,
  inputLabel,
} from "@/lib/joystick"
import { useActions, useIntegrations } from "@/lib/queries"
import type {
  ActionOutput,
  HatDirection,
  JoystickDevice,
  JoystickMapping,
  KeysOutput,
  MouseOutput,
} from "@/lib/types"

export interface MappingTarget {
  inputType: "hat" | "button"
  input: string
}

interface MappingDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  configurationId: number
  device: JoystickDevice
  /** The input to map when creating */
  target?: MappingTarget
  /** The mapping being edited, or undefined to create one */
  mapping?: JoystickMapping
}

export function MappingDialog({ open, onOpenChange, ...props }: MappingDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-h-[90vh] overflow-y-auto sm:max-w-lg"
        onEscapeKeyDown={(event) => {
          // Esc is a key you can record, so don't close the dialog while the key recorder has focus
          if (document.activeElement?.closest("[data-key-recorder]")) event.preventDefault()
        }}
      >
        {/* Dialog content unmounts when closed, so the form starts fresh each time it opens */}
        <MappingForm {...props} onDone={() => onOpenChange(false)} />
      </DialogContent>
    </Dialog>
  )
}

type OutputType = JoystickMapping["outputType"]

function MappingForm({
  configurationId,
  device,
  target,
  mapping,
  onDone,
}: Omit<MappingDialogProps, "open" | "onOpenChange"> & { onDone: () => void }) {
  const queryClient = useQueryClient()
  const { data: actions = [] } = useActions()
  const { data: integrations = [] } = useIntegrations()
  const keyboard = integrations.find((integration) => integration.actionEditor === "keyboard")

  const initialInput = mapping ? { inputType: mapping.inputType, input: mapping.input } : (target ?? { inputType: "hat" as const, input: "up" })
  const [input, setInput] = useState(inputKey(initialInput.inputType, initialInput.input))
  const [inputType, inputValue] = input.split(":") as ["hat" | "button", string]
  const hatDirection = inputType === "hat" ? (inputValue as HatDirection) : null

  const [name, setName] = useState(mapping?.name ?? "")
  const [outputType, setOutputType] = useState<OutputType>(mapping?.outputType ?? "mouse")
  const [mouse, setMouse] = useState<MouseOutput>(
    mapping?.outputType === "mouse" ? (mapping.output as MouseOutput) : defaultMouseOutput(null)
  )
  const [keys, setKeys] = useState<string[]>(mapping?.outputType === "keys" ? (mapping.output as KeysOutput).keys : [])
  const [action, setAction] = useState<ActionOutput | null>(
    mapping?.outputType === "action" ? (mapping.output as ActionOutput) : null
  )
  const [enabled, setEnabled] = useState(mapping?.enabled ?? true)
  const [error, setError] = useState<string | null>(null)

  // A hat direction looks that way by default; a button has to be told which way
  const lookDirection = mouse.direction ?? hatDirection ?? "right"

  const save = useMutation({
    mutationFn: () => {
      const output =
        outputType === "mouse"
          ? { ...mouse, direction: mouse.direction === hatDirection ? null : mouse.direction }
          : outputType === "keys"
            ? { keys }
            : action
      const body = { name, device: device.id, inputType, input: inputValue, outputType, output: output!, enabled }
      return mapping ? api.updateJoystickMapping(mapping.id, body) : api.createJoystickMapping(configurationId, body)
    },
    onSuccess: () => {
      queryClient.invalidateQueries()
      toast.success(mapping ? "Mapping saved" : "Mapping added")
      onDone()
    },
    onError: (e: Error) => setError(e.message),
  })

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (outputType === "keys" && keys.length === 0) return setError("Add at least one key to hold")
    if (outputType === "action" && !action) return setError("Choose an action")
    save.mutate()
  }

  const inputOptions = [
    ...(device.hasHat ? hatDirections.map((direction) => ({ value: inputKey("hat", direction), label: inputLabel("hat", direction) })) : []),
    ...Array.from({ length: Math.max(device.buttons, 1) }, (_, i) => ({
      value: inputKey("button", String(i + 1)),
      label: inputLabel("button", String(i + 1)),
    })),
  ]

  return (
    <form onSubmit={submit}>
      <DialogHeader>
        <DialogTitle>{mapping ? "Edit mapping" : "Add mapping"}</DialogTitle>
        <DialogDescription>Choose what happens while this is held on {device.name}.</DialogDescription>
      </DialogHeader>

      <FieldGroup className="py-4">
        <Field>
          <FieldLabel>Input</FieldLabel>
          <Select value={input} onValueChange={setInput}>
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {inputOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </Field>

        <Field>
          <FieldLabel>Does</FieldLabel>
          <ToggleGroup
            type="single"
            variant="outline"
            value={outputType}
            onValueChange={(value) => {
              if (!value) return
              setOutputType(value as OutputType)
              setError(null)
            }}
            className="w-full"
          >
            <ToggleGroupItem value="mouse" className="flex-1 gap-1.5">
              <Mouse />
              Look around
            </ToggleGroupItem>
            <ToggleGroupItem value="keys" className="flex-1 gap-1.5">
              <Keyboard />
              Hold keys
            </ToggleGroupItem>
            <ToggleGroupItem value="action" className="flex-1 gap-1.5">
              <Play />
              Run action
            </ToggleGroupItem>
          </ToggleGroup>
        </Field>

        {outputType === "mouse" && (
          <>
            <Field>
              <FieldLabel>Look</FieldLabel>
              <ToggleGroup
                type="single"
                variant="outline"
                value={lookDirection}
                onValueChange={(value) => value && setMouse({ ...mouse, direction: value as HatDirection })}
                className="w-full"
              >
                {hatDirections.map((direction) => (
                  <ToggleGroupItem key={direction} value={direction} className="flex-1">
                    {directionLabels[direction]}
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
            </Field>

            <Field>
              <div className="flex items-center justify-between">
                <FieldLabel>Speed</FieldLabel>
                <span className="text-sm text-muted-foreground tabular-nums">{mouse.speed} px/s</span>
              </div>
              <Slider
                min={100}
                max={5000}
                step={50}
                value={[mouse.speed]}
                onValueChange={([speed]) => setMouse({ ...mouse, speed })}
                aria-label="Speed"
              />
              <FieldDescription>How fast the view turns while held.</FieldDescription>
            </Field>

            <Field>
              <div className="flex items-center justify-between">
                <FieldLabel>Ramp up</FieldLabel>
                <span className="text-sm text-muted-foreground tabular-nums">
                  {mouse.rampMs === 0 ? "Instant" : `${mouse.rampMs} ms`}
                </span>
              </div>
              <Slider
                min={0}
                max={1000}
                step={25}
                value={[mouse.rampMs]}
                onValueChange={([rampMs]) => setMouse({ ...mouse, rampMs })}
                aria-label="Ramp up"
              />
              <FieldDescription>Starts slower and builds to full speed, so quick taps make small adjustments.</FieldDescription>
            </Field>

            <Field>
              <FieldLabel>Hold while looking</FieldLabel>
              <Select value={mouse.holdKey || "none"} onValueChange={(value) => setMouse({ ...mouse, holdKey: value === "none" ? "" : value })}>
                <SelectTrigger className="w-full">
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
              <FieldDescription>
                For Wardogs, holding Alt gives free look that recentres when you let go. To keep the view where you
                leave it, choose Nothing and lock free look first (double-tap Alt).
              </FieldDescription>
            </Field>

            <div className="grid gap-4 sm:grid-cols-2">
              <Field>
                <FieldLabel htmlFor="max-distance">Stop after</FieldLabel>
                <Input
                  id="max-distance"
                  type="number"
                  min={0}
                  max={20000}
                  step={50}
                  value={mouse.maxDistance}
                  onChange={(e) => setMouse({ ...mouse, maxDistance: Math.max(0, Number(e.target.value) || 0) })}
                />
                <FieldDescription>Pixels. 0 keeps turning while held.</FieldDescription>
              </Field>
              <Field orientation="horizontal" className="self-start sm:pt-6">
                <Switch
                  id="return-on-release"
                  checked={mouse.returnOnRelease}
                  onCheckedChange={(returnOnRelease) => setMouse({ ...mouse, returnOnRelease })}
                />
                <FieldContent>
                  <FieldLabel htmlFor="return-on-release">Return when let go</FieldLabel>
                  <FieldDescription>For games that don't recentre themselves.</FieldDescription>
                </FieldContent>
              </Field>
            </div>
          </>
        )}

        {outputType === "keys" && (
          <Field>
            <FieldLabel>Keys</FieldLabel>
            <KeyboardEditor
              value={keys.map((key) => ({ key, type: "tap" }))}
              onChange={(steps) => {
                setKeys(steps.map((step) => step.key))
                setError(null)
              }}
              keys={keyboard?.options?.keys ?? []}
              types={[]}
              showTypes={false}
            />
            <FieldDescription>
              Held down for as long as the input is - for example, the arrow keys for Wardogs' snap views.
            </FieldDescription>
          </Field>
        )}

        {outputType === "action" && (
          <>
            <Field>
              <FieldLabel>Action</FieldLabel>
              <ActionPicker
                actions={actions}
                value={actions.find((a) => a.id === action?.actionId)}
                inactiveIntegrations={new Set(integrations.filter((i) => !i.active).map((i) => i.id))}
                onChange={(picked) => {
                  setAction({ actionId: picked.id, when: action?.when ?? "press" })
                  setError(null)
                }}
              />
            </Field>
            <Field>
              <FieldLabel>Run when</FieldLabel>
              <ToggleGroup
                type="single"
                variant="outline"
                value={action?.when ?? "press"}
                onValueChange={(value) => value && action && setAction({ ...action, when: value as "press" | "release" })}
                className="w-full"
              >
                <ToggleGroupItem value="press" className="flex-1">
                  Pressed
                </ToggleGroupItem>
                <ToggleGroupItem value="release" className="flex-1">
                  Released
                </ToggleGroupItem>
              </ToggleGroup>
            </Field>
          </>
        )}

        <Field>
          <FieldLabel htmlFor="mapping-name">Label</FieldLabel>
          <Input id="mapping-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Free look" />
          <FieldDescription>Optional. Shown on the joystick view.</FieldDescription>
        </Field>

        <Field orientation="horizontal">
          <Switch id="mapping-enabled" checked={enabled} onCheckedChange={setEnabled} />
          <FieldLabel htmlFor="mapping-enabled">Enabled</FieldLabel>
        </Field>

        {error && <p className="text-sm text-destructive">{error}</p>}
      </FieldGroup>

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" disabled={save.isPending}>
          {mapping ? "Save" : "Add mapping"}
        </Button>
      </DialogFooter>
    </form>
  )
}
