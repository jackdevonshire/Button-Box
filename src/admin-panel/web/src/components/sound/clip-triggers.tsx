import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Box, Gamepad2, Keyboard, ScanLine, X } from "lucide-react"
import type { ReactNode } from "react"
import { toast } from "sonner"

import { KeySlot } from "@/components/actions/key-slot"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useLearnMode } from "@/hooks/use-learn-mode"
import { usePickFromStick } from "@/hooks/use-pick-from-stick"
import { api } from "@/lib/api"
import { controlLabel, shortEventLabel } from "@/lib/controls"
import { inputLabel } from "@/lib/joystick"
import { useConfiguration, useControls, useJoystick, useSound, useStatus } from "@/lib/queries"
import type { ActionOutput, SoundClip } from "@/lib/types"

/**
 * Everything that plays a sound in one place: a keyboard shortcut (works in any app), and box and joystick buttons
 * (part of the active configuration). Changes here save straight away.
 */
export function ClipTriggers({ clip, title = "Play it from" }: { clip: SoundClip; title?: string }) {
  const { data: status } = useStatus()
  const { data: configuration } = useConfiguration(status?.activeConfigurationId)

  return (
    <div className="flex flex-col gap-3">
      <div>
        <h3 className="text-sm font-medium">{title}</h3>
        <p className="text-sm text-muted-foreground">
          These save straight away. Box and joystick buttons belong to{" "}
          <span className="font-medium text-foreground">{configuration?.name ?? "the active configuration"}</span>.
        </p>
      </div>
      <ShortcutRow clip={clip} />
      {configuration && <BoxRow clip={clip} configurationId={configuration.id} />}
      {configuration && <JoystickRow clip={clip} configurationId={configuration.id} />}
    </div>
  )
}

function TriggerRow({ icon, label, children }: { icon: ReactNode; label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-2 rounded-lg border px-3 py-2.5">
      <div className="flex items-center gap-2 text-sm font-medium">
        {icon}
        {label}
      </div>
      {children}
    </div>
  )
}

function useSaveShortcut(clip: SoundClip) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (hotkey: string[] | null) => api.updateClip(clip.id, { hotkey }),
    onSuccess: (updated) => {
      queryClient.invalidateQueries()
      if (updated.hotkeyError) toast.error(updated.hotkeyError)
    },
    onError: (e: Error) => toast.error(e.message),
  })
}

/** A keyboard shortcut for a sound - also used for Stop all sounds */
export function ShortcutSlot({ clip, className }: { clip: SoundClip; className?: string }) {
  const { data: sound } = useSound()
  const save = useSaveShortcut(clip)
  const keys = clip.hotkey ?? []
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-1">
        <KeySlot
          label={`Shortcut for ${clip.name}`}
          keys={keys}
          supported={new Set(sound?.hotkeyKeys ?? [])}
          placeholder="Click, then press a shortcut"
          className={className ?? "h-8 border"}
          onRecord={(next) => save.mutate(next)}
        />
        {keys.length > 0 && (
          <Button size="icon-sm" variant="ghost" aria-label="Remove the shortcut" onClick={() => save.mutate(null)}>
            <X />
          </Button>
        )}
      </div>
      {clip.hotkeyError && <p className="text-xs text-destructive">{clip.hotkeyError}</p>}
    </div>
  )
}

function ShortcutRow({ clip }: { clip: SoundClip }) {
  return (
    <TriggerRow icon={<Keyboard className="size-4 text-muted-foreground" />} label="Keyboard shortcut">
      <ShortcutSlot clip={clip} />
      <p className="text-xs text-muted-foreground">
        Works in any app. The app in front won't see that key combination, so pick one the game doesn't use - like
        Ctrl + a numpad key.
      </p>
    </TriggerRow>
  )
}

function BoxRow({ clip, configurationId }: { clip: SoundClip; configurationId: number }) {
  const queryClient = useQueryClient()
  const { data: configuration } = useConfiguration(configurationId)
  const { data: controls = [] } = useControls()
  const bindings = configuration?.bindings?.filter((binding) => binding.action.id === clip.id) ?? []

  const add = useMutation({
    mutationFn: (control: string) => api.createBinding(configurationId, { control, event: "on", actionId: clip.id }),
    onSuccess: (binding) => {
      queryClient.invalidateQueries()
      toast.success(`${controlLabel(controls, binding.control)} → ${clip.name}`)
    },
    onError: (e: Error) => toast.error(e.message),
  })
  const remove = useMutation({
    mutationFn: (id: number) => api.deleteBinding(id),
    onSuccess: () => queryClient.invalidateQueries(),
    onError: (e: Error) => toast.error(e.message),
  })
  const learning = useLearnMode((control) => add.mutate(control))

  return (
    <TriggerRow icon={<Box className="size-4 text-muted-foreground" />} label="Button box">
      {bindings.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {bindings.map((binding) => {
            const control = controls.find((c) => c.id === binding.control)
            return (
              <Badge key={binding.id} variant="secondary" className="gap-1 pr-0.5">
                {controlLabel(controls, binding.control)}
                {binding.event === "off" && <span className="text-muted-foreground">({shortEventLabel(control?.kind, "off")})</span>}
                <button
                  type="button"
                  className="rounded-sm p-0.5 hover:bg-background/60"
                  aria-label={`Remove ${controlLabel(controls, binding.control)}`}
                  onClick={() => remove.mutate(binding.id)}
                >
                  <X className="size-3" />
                </button>
              </Badge>
            )
          })}
        </div>
      )}
      <div className="flex flex-wrap gap-2">
        <Button type="button" size="sm" variant="outline" onClick={learning.start} disabled={learning.active}>
          <ScanLine data-icon="inline-start" />
          {learning.active ? `Press it on the box… ${learning.secondsLeft}` : "Press a box button"}
        </Button>
        <Select value="" onValueChange={(control) => add.mutate(control)}>
          <SelectTrigger size="sm" className="w-40">
            <SelectValue placeholder="Or choose one" />
          </SelectTrigger>
          <SelectContent>
            {controls.map((control) => (
              <SelectItem key={control.id} value={control.id}>
                {control.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </TriggerRow>
  )
}

function JoystickRow({ clip, configurationId }: { clip: SoundClip; configurationId: number }) {
  const queryClient = useQueryClient()
  const { data: configuration } = useConfiguration(configurationId)
  const { data: joystick } = useJoystick()
  const device = joystick?.devices[0]
  const mappings =
    configuration?.joystickMappings?.filter(
      (mapping) => mapping.outputType === "action" && (mapping.output as ActionOutput).actionId === clip.id
    ) ?? []

  const add = useMutation({
    mutationFn: (key: string) => {
      const [inputType, input] = key.split(":") as ["hat" | "button", string]
      return api.createJoystickMapping(configurationId, {
        name: "",
        device: device!.id,
        inputType,
        input,
        outputType: "action",
        output: { actionId: clip.id, when: "press" },
        enabled: true,
      })
    },
    onSuccess: (mapping) => {
      queryClient.invalidateQueries()
      toast.success(`${inputLabel(mapping.inputType, mapping.input)} → ${clip.name}`)
    },
    onError: (e: Error) => toast.error(e.message),
  })
  const remove = useMutation({
    mutationFn: (id: number) => api.deleteJoystickMapping(id),
    onSuccess: () => queryClient.invalidateQueries(),
    onError: (e: Error) => toast.error(e.message),
  })
  const picking = usePickFromStick(device ? joystick?.states[device.id] : undefined, (key) => add.mutate(key))

  return (
    <TriggerRow icon={<Gamepad2 className="size-4 text-muted-foreground" />} label="Joystick">
      {mappings.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {mappings.map((mapping) => (
            <Badge key={mapping.id} variant="secondary" className="gap-1 pr-0.5">
              {inputLabel(mapping.inputType, mapping.input)}
              <button
                type="button"
                className="rounded-sm p-0.5 hover:bg-background/60"
                aria-label={`Remove ${inputLabel(mapping.inputType, mapping.input)}`}
                onClick={() => remove.mutate(mapping.id)}
              >
                <X className="size-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
      {device ? (
        <div className="flex flex-wrap items-center gap-2">
          <Button type="button" size="sm" variant="outline" onClick={picking.start} disabled={picking.active}>
            <ScanLine data-icon="inline-start" />
            {picking.active ? `Press it on the stick… ${picking.secondsLeft}` : "Press a joystick button"}
          </Button>
          <span className="truncate text-xs text-muted-foreground">{device.name}</span>
        </div>
      ) : (
        <p className="text-xs text-muted-foreground">Plug in a joystick to add one.</p>
      )}
    </TriggerRow>
  )
}
