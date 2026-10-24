import { CircleAlert, ExternalLink } from "lucide-react"
import { useState } from "react"

import { useSoundSettings } from "@/components/sound/use-sound-settings"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Field, FieldDescription, FieldLabel } from "@/components/ui/field"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import type { SoundDevice, SoundSnapshot, SoundStream } from "@/lib/types"

const NONE = "none"

/** Where your voice comes from, where it and the sounds go, and how loud each is */
export function DevicesCard({ sound }: { sound: SoundSnapshot }) {
  const save = useSoundSettings()
  const { settings, devices, state } = sound
  const hasCable = devices.outputs.some((device) => device.isCable)
  const gameIsCable = devices.outputs.find((device) => device.name === settings.gameDevice)?.isCable ?? false

  return (
    <Card size="sm">
      <CardHeader>
        <CardTitle>Devices</CardTitle>
        <CardDescription>
          Your voice and the sounds are mixed together and sent to a virtual cable, which the game uses as its
          microphone.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        {!hasCable && <CableMissing />}

        <div className="grid grid-cols-[repeat(auto-fit,minmax(13rem,1fr))] gap-4">
          <DeviceField
            label="Microphone"
            stream="mic"
            value={settings.micDevice}
            options={devices.inputs.filter((device) => !device.isCable)}
            state={state}
            noneLabel="No microphone"
            onChange={(micDevice) => save.mutate({ micDevice })}
          />
          <DeviceField
            label="Send to game"
            stream="game"
            value={settings.gameDevice}
            options={[...devices.outputs].sort((a, b) => Number(b.isCable) - Number(a.isCable))}
            state={state}
            noneLabel="Nothing"
            onChange={(gameDevice) => save.mutate({ gameDevice })}
          />
          <DeviceField
            label="Hear sounds on"
            stream="monitor"
            value={settings.monitorDevice}
            options={devices.outputs.filter((device) => !device.isCable)}
            state={state}
            noneLabel="Nothing"
            onChange={(monitorDevice) => save.mutate({ monitorDevice })}
          />
        </div>

        {settings.gameDevice && (
          <p className="rounded-lg bg-muted/50 px-3 py-2 text-sm text-muted-foreground">
            {gameIsCable ? (
              <>
                In the game (and Discord, if you like), set your microphone to{" "}
                <span className="font-medium text-foreground">{cableOutputName(settings.gameDevice)}</span>.
              </>
            ) : (
              <>That isn't a virtual cable, so the game won't be able to use it as a microphone.</>
            )}
          </p>
        )}

        <div className="grid grid-cols-[repeat(auto-fit,minmax(13rem,1fr))] gap-4">
          <VolumeField
            label="Microphone volume"
            key={settings.micVolume}
            value={settings.micVolume}
            onCommit={(micVolume) => save.mutate({ micVolume })}
          />
          <VolumeField
            label="Sounds in game"
            key={settings.clipVolume}
            value={settings.clipVolume}
            onCommit={(clipVolume) => save.mutate({ clipVolume })}
          />
          <VolumeField
            label="Sounds in your headphones"
            key={settings.monitorVolume}
            value={settings.monitorVolume}
            onCommit={(monitorVolume) => save.mutate({ monitorVolume })}
          />
        </div>
      </CardContent>
    </Card>
  )
}

/** VB-Cable's input becomes the matching output on the recording side */
function cableOutputName(name: string) {
  return name.replace(/\bCABLE Input\b/, "CABLE Output").replace(/\bInput\b/, "Output")
}

function CableMissing() {
  return (
    <div className="flex gap-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2.5 text-sm">
      <CircleAlert className="mt-0.5 size-4 shrink-0 text-amber-600 dark:text-amber-400" />
      <div className="flex flex-col gap-1">
        <p className="font-medium">No virtual cable found</p>
        <p className="text-muted-foreground">
          To send sounds into games, install VB-Audio Virtual Cable (free), then restart the panel. Push-to-talk works
          without it.
        </p>
        <a
          href="https://vb-audio.com/Cable/"
          target="_blank"
          rel="noreferrer"
          className="flex w-fit items-center gap-1 font-medium text-primary underline-offset-4 hover:underline"
        >
          Get VB-Audio Virtual Cable
          <ExternalLink className="size-3.5" />
        </a>
      </div>
    </div>
  )
}

function DeviceField({
  label,
  stream,
  value,
  options,
  state,
  noneLabel,
  onChange,
}: {
  label: string
  stream: SoundStream
  value: string | null
  options: SoundDevice[]
  state: SoundSnapshot["state"]
  noneLabel: string
  onChange: (device: string | null) => void
}) {
  const error = state.errors[stream]
  const running = state.running[stream] !== undefined
  // Keep showing a saved device that isn't plugged in, so it's clear what's chosen
  const all = value && !options.some((option) => option.name === value) ? [...options, { name: value, isCable: false, isDefault: false }] : options

  return (
    <Field>
      <div className="flex items-center justify-between gap-2">
        <FieldLabel>{label}</FieldLabel>
        {running && (
          <Badge variant="secondary" className="gap-1.5">
            <span className="size-1.5 rounded-full bg-emerald-500" />
            On
          </Badge>
        )}
      </div>
      <Select value={value ?? NONE} onValueChange={(next) => onChange(next === NONE ? null : next)}>
        <SelectTrigger className="w-full min-w-0">
          {/* Just the name - the items also show hints, which shouldn't repeat in the trigger */}
          <SelectValue>
            <span className="truncate">{value ?? noneLabel}</span>
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={NONE}>{noneLabel}</SelectItem>
          {all.map((option) => (
            <SelectItem key={option.name} value={option.name}>
              <span className="truncate">{option.name}</span>
              {option.isCable && <span className="text-xs text-muted-foreground">virtual cable</span>}
              {option.isDefault && <span className="text-xs text-muted-foreground">default</span>}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {error && <FieldDescription className="text-destructive">{error}</FieldDescription>}
      {!error && stream === "mic" && value && !running && (
        <FieldDescription>Only listened to when sending to the game or using push-to-talk.</FieldDescription>
      )}
    </Field>
  )
}

/** Keyed by the saved value, so the slider holds where it was let go until the saved value arrives */
function VolumeField({ label, value, onCommit }: { label: string; value: number; onCommit: (value: number) => void }) {
  const [draft, setDraft] = useState<number | null>(null)
  const shown = draft ?? value
  return (
    <Field>
      <div className="flex items-center justify-between">
        <FieldLabel>{label}</FieldLabel>
        <span className="text-sm text-muted-foreground tabular-nums">{Math.round(shown * 100)}%</span>
      </div>
      <Slider
        min={0}
        max={2}
        step={0.05}
        value={[shown]}
        onValueChange={([next]) => setDraft(next)}
        onValueCommit={([next]) => onCommit(next)}
        aria-label={label}
      />
    </Field>
  )
}
