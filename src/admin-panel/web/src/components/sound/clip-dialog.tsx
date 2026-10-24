import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Field, FieldDescription, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Slider } from "@/components/ui/slider"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { api } from "@/lib/api"
import type { ClipAgain, SoundClip } from "@/lib/types"

const againOptions: { value: ClipAgain; label: string; hint: string }[] = [
  { value: "restart", label: "Restart", hint: "Starts it again from the beginning." },
  { value: "stop", label: "Stop", hint: "Stops it, so the same button starts and stops it." },
  { value: "overlap", label: "Play over", hint: "Plays another copy on top." },
]

export function ClipDialog({ clip, onOpenChange }: { clip: SoundClip | null; onOpenChange: (open: boolean) => void }) {
  return (
    <Dialog open={clip !== null} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        {/* Remounts for each clip, so the form starts from its saved values */}
        {clip && <ClipForm key={clip.id} clip={clip} onDone={() => onOpenChange(false)} />}
      </DialogContent>
    </Dialog>
  )
}

function ClipForm({ clip, onDone }: { clip: SoundClip; onDone: () => void }) {
  const queryClient = useQueryClient()
  const [name, setName] = useState(clip.name)
  const [volume, setVolume] = useState(clip.volume ?? 1)
  const [again, setAgain] = useState<ClipAgain>(clip.again ?? "restart")
  const [error, setError] = useState<string | null>(null)

  const save = useMutation({
    mutationFn: () => api.updateClip(clip.id, { name, volume, again }),
    onSuccess: () => {
      queryClient.invalidateQueries()
      toast.success("Sound saved")
      onDone()
    },
    onError: (e: Error) => setError(e.message),
  })

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        save.mutate()
      }}
    >
      <DialogHeader>
        <DialogTitle>Edit sound</DialogTitle>
        <DialogDescription>The name is also what the box's screen shows while it plays.</DialogDescription>
      </DialogHeader>

      <FieldGroup className="py-4">
        <Field>
          <FieldLabel htmlFor="clip-name">Name</FieldLabel>
          <Input id="clip-name" value={name} onChange={(e) => setName(e.target.value)} />
        </Field>

        <Field>
          <div className="flex items-center justify-between">
            <FieldLabel>Volume</FieldLabel>
            <span className="text-sm text-muted-foreground tabular-nums">{Math.round(volume * 100)}%</span>
          </div>
          <Slider min={0} max={2} step={0.05} value={[volume]} onValueChange={([next]) => setVolume(next)} aria-label="Volume" />
          <FieldDescription>For evening out sounds that are louder or quieter than the rest.</FieldDescription>
        </Field>

        <Field>
          <FieldLabel>Pressed again while playing</FieldLabel>
          <ToggleGroup
            type="single"
            variant="outline"
            value={again}
            onValueChange={(value) => value && setAgain(value as ClipAgain)}
            className="w-full"
          >
            {againOptions.map((option) => (
              <ToggleGroupItem key={option.value} value={option.value} className="flex-1">
                {option.label}
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
          <FieldDescription>{againOptions.find((option) => option.value === again)?.hint}</FieldDescription>
        </Field>

        {error && <p className="text-sm text-destructive">{error}</p>}
      </FieldGroup>

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" disabled={save.isPending}>
          Save
        </Button>
      </DialogFooter>
    </form>
  )
}
