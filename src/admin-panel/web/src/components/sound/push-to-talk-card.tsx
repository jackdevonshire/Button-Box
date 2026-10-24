import { useQuery } from "@tanstack/react-query"
import { Keyboard, Mic, MicOff } from "lucide-react"
import { useState } from "react"

import { KeySlot } from "@/components/actions/key-slot"
import { useSoundSettings } from "@/components/sound/use-sound-settings"
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Field, FieldContent, FieldDescription, FieldLabel } from "@/components/ui/field"
import { Kbd } from "@/components/ui/kbd"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { Switch } from "@/components/ui/switch"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { api } from "@/lib/api"
import { keyLabel } from "@/lib/keys"
import { useIntegrations } from "@/lib/queries"
import type { PushToTalkSettings, SoundSnapshot } from "@/lib/types"
import { cn } from "@/lib/utils"

const METER_FLOOR = -70 // dB at the left of the meter
const ANY_APP = "any"
const activeStyle = "border-emerald-500 bg-emerald-500/20 text-emerald-700 dark:text-emerald-300"

/**
 * Voice activation: either holds the game's push-to-talk key while you talk or a sound plays, or - with no simulated
 * key presses at all - gates your voice so it only reaches the game (set to open mic) while you talk
 */
export function PushToTalkCard({ sound }: { sound: SoundSnapshot }) {
  const save = useSoundSettings()
  const { data: integrations = [] } = useIntegrations()
  const supported = new Set(integrations.find((i) => i.actionEditor === "keyboard")?.options?.keys ?? [])
  const ptt = sound.settings.pushToTalk
  const update = (changes: Partial<PushToTalkSettings>) => save.mutate({ pushToTalk: changes })
  const gate = ptt.method === "gate"
  const routed = !!sound.settings.gameDevice

  return (
    <Card size="sm">
      <CardHeader>
        <CardTitle>Voice activation</CardTitle>
        <CardDescription>Talk in game without holding push-to-talk yourself.</CardDescription>
        <CardAction>
          <Switch checked={ptt.enabled} onCheckedChange={(enabled) => update({ enabled })} aria-label="Voice activation" />
        </CardAction>
      </CardHeader>
      <CardContent className={cn("flex flex-col gap-5", !ptt.enabled && "opacity-60")}>
        <Field>
          <FieldLabel>How</FieldLabel>
          <ToggleGroup
            type="single"
            variant="outline"
            value={ptt.method}
            onValueChange={(method) => method && update({ method: method as PushToTalkSettings["method"] })}
            className="w-full"
          >
            <ToggleGroupItem value="key" className="flex-1 gap-1.5">
              <Keyboard />
              Press a key
            </ToggleGroupItem>
            <ToggleGroupItem value="gate" className="flex-1 gap-1.5">
              <Mic />
              Mic gate
            </ToggleGroupItem>
          </ToggleGroup>
          <FieldDescription>
            {gate
              ? "No key presses. Your voice only reaches the game while you're talking - set the game to open mic (always on) or voice activation."
              : "Holds the game's push-to-talk key while you talk or a sound plays. The game sees it as a simulated key press."}
          </FieldDescription>
        </Field>

        {gate && !routed && (
          <p className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm">
            The mic gate works on your voice on its way to the game, so choose a device to send to below.
          </p>
        )}

        <StatusRow sound={sound} />

        {!gate && (
          <>
            <Field orientation="horizontal">
              <FieldContent>
                <FieldLabel>Key</FieldLabel>
                <FieldDescription>Wardogs uses K. Click and press a key to change it.</FieldDescription>
              </FieldContent>
              <KeySlot
                label="Push-to-talk key"
                keys={[ptt.key]}
                supported={supported}
                placeholder="Choose a key"
                single
                className="h-9 max-w-28 justify-center border"
                onRecord={([key]) => update({ key })}
              />
            </Field>

            <div className="flex flex-col gap-3">
              <Field orientation="horizontal">
                <Switch id="ptt-voice" checked={ptt.onVoice} onCheckedChange={(onVoice) => update({ onVoice })} />
                <FieldLabel htmlFor="ptt-voice">Hold it while I talk</FieldLabel>
              </Field>
              <Field orientation="horizontal">
                <Switch id="ptt-clips" checked={ptt.onClips} onCheckedChange={(onClips) => update({ onClips })} />
                <FieldLabel htmlFor="ptt-clips">Hold it while a sound plays</FieldLabel>
              </Field>
            </div>
          </>
        )}

        {(gate || ptt.onVoice) && (
          <>
            <ThresholdField key={ptt.threshold} sound={sound} onCommit={(threshold) => update({ threshold })} />

            <MsField
              key={`release-${ptt.releaseMs}`}
              label={gate ? "Keep the mic open after I stop" : "Keep holding after I stop"}
              value={ptt.releaseMs}
              max={2000}
              step={50}
              description={gate ? "So it doesn't cut out between words." : "So it doesn't let go between words."}
              onCommit={(releaseMs) => update({ releaseMs })}
            />

            <MsField
              key={`delay-${ptt.micDelayMs}`}
              label="Delay my voice"
              value={ptt.micDelayMs}
              max={400}
              step={10}
              disabled={!routed}
              description={
                !routed
                  ? "Only works when your voice goes to the game through the panel - choose a device to send to below."
                  : gate
                    ? "Gives the gate a moment to open, so the start of your first word isn't cut off."
                    : "Your voice reaches the game this much later, so the key is already down for your first word."
              }
              onCommit={(micDelayMs) => update({ micDelayMs })}
            />
          </>
        )}

        {!gate && <FocusAppField value={ptt.focusApp} onChange={(focusApp) => update({ focusApp })} />}
      </CardContent>
    </Card>
  )
}

/** What voice activation is doing right now: holding the key, or letting your voice through */
function StatusRow({ sound }: { sound: SoundSnapshot }) {
  const ptt = sound.settings.pushToTalk
  const { state } = sound
  const gate = ptt.method === "gate"
  const active = gate ? state.gateOpen : state.keyHeld
  const status = !ptt.enabled
    ? "Off"
    : gate
      ? state.gateOpen
        ? "Mic open"
        : "Mic muted"
      : ptt.focusApp && !state.focusOk
        ? `Waiting for ${ptt.focusApp}`
        : state.keyHeld
          ? "Holding"
          : "Ready"

  return (
    <div className="flex items-center gap-3 rounded-lg border px-3 py-2.5">
      {gate ? (
        <span
          className={cn(
            "flex h-5 min-w-10 items-center justify-center rounded-sm border bg-muted text-muted-foreground transition-colors",
            active && activeStyle
          )}
        >
          {active ? <Mic className="size-3.5" /> : <MicOff className="size-3.5" />}
        </span>
      ) : (
        <Kbd className={cn("min-w-10 justify-center transition-colors", active && activeStyle)}>{keyLabel(ptt.key)}</Kbd>
      )}
      <span className="flex-1 text-sm">{status}</span>
      <span className="text-xs text-muted-foreground">{state.talking ? "Talking" : state.level !== null ? "Quiet" : ""}</span>
    </div>
  )
}

/** A live mic meter with the threshold marked on it - talking is anything louder than the line */
function ThresholdField({ sound, onCommit }: { sound: SoundSnapshot; onCommit: (threshold: number) => void }) {
  const [threshold, setThreshold] = useState(sound.settings.pushToTalk.threshold)
  const level = sound.state.level
  const position = (db: number) => `${Math.min(100, Math.max(0, ((db - METER_FLOOR) / -METER_FLOOR) * 100))}%`

  return (
    <Field>
      <div className="flex items-center justify-between">
        <FieldLabel>Talking is louder than</FieldLabel>
        <span className="text-sm text-muted-foreground tabular-nums">{threshold} dB</span>
      </div>
      <div className="relative h-3 overflow-hidden rounded-full bg-muted" aria-hidden>
        <span
          className={cn(
            "absolute inset-y-0 left-0 rounded-full transition-[width] duration-100 ease-linear",
            level !== null && level >= threshold ? "bg-emerald-500" : "bg-foreground/30"
          )}
          style={{ width: level === null ? 0 : position(level) }}
        />
        <span className="absolute inset-y-0 w-0.5 -translate-x-1/2 bg-primary" style={{ left: position(threshold) }} />
      </div>
      <Slider
        min={METER_FLOOR}
        max={0}
        step={1}
        value={[threshold]}
        onValueChange={([next]) => setThreshold(next)}
        onValueCommit={([next]) => onCommit(next)}
        aria-label="Talking threshold"
      />
      <FieldDescription>
        {level === null ? (
          <span className="flex items-center gap-1.5">
            <Mic className="size-3.5" />
            Choose a microphone below to see its level.
          </span>
        ) : (
          "Talk normally and set the line just below where your voice reaches, and above the background noise."
        )}
      </FieldDescription>
    </Field>
  )
}

function MsField({
  label,
  value,
  max,
  step,
  description,
  disabled,
  onCommit,
}: {
  label: string
  value: number
  max: number
  step: number
  description: string
  disabled?: boolean
  onCommit: (value: number) => void
}) {
  const [draft, setDraft] = useState(value)
  return (
    <Field data-disabled={disabled}>
      <div className="flex items-center justify-between">
        <FieldLabel>{label}</FieldLabel>
        <span className="text-sm text-muted-foreground tabular-nums">{draft === 0 ? "Off" : `${draft} ms`}</span>
      </div>
      <Slider
        min={0}
        max={max}
        step={step}
        value={[draft]}
        disabled={disabled}
        onValueChange={([next]) => setDraft(next)}
        onValueCommit={([next]) => onCommit(next)}
        aria-label={label}
      />
      <FieldDescription>{description}</FieldDescription>
    </Field>
  )
}

function FocusAppField({ value, onChange }: { value: string; onChange: (app: string) => void }) {
  const [open, setOpen] = useState(false)
  // The list of apps is only fetched when the menu opens, so it's current
  const { data: apps = [] } = useQuery({ queryKey: ["sound-apps"], queryFn: api.soundApps, enabled: open, staleTime: 0 })
  const options = value && !apps.some((app) => app.exe.toLowerCase() === value.toLowerCase()) ? [{ exe: value, title: "" }, ...apps] : apps

  return (
    <Field>
      <FieldLabel>Only while this is in front</FieldLabel>
      <Select value={value || ANY_APP} onValueChange={(next) => onChange(next === ANY_APP ? "" : next)} onOpenChange={setOpen}>
        <SelectTrigger className="w-full min-w-0">
          <SelectValue>
            <span className="truncate">{value || "Any app"}</span>
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ANY_APP}>Any app</SelectItem>
          {options.map((app) => (
            <SelectItem key={app.exe} value={app.exe}>
              <span className="truncate">{app.exe}</span>
              {app.title && <span className="truncate text-xs text-muted-foreground">{app.title}</span>}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <FieldDescription>
        So the key isn't typed into Discord or chat when you talk with another window in front. Start the game first to
        find it in the list.
      </FieldDescription>
    </Field>
  )
}
