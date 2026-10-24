import { useMutation, useQueryClient } from "@tanstack/react-query"
import { FileAudio, MoreHorizontal, Pencil, Play, Square, Trash2, Upload } from "lucide-react"
import { useRef, useState } from "react"
import { toast } from "sonner"

import { CableMeter } from "@/components/sound/cable-meter"
import { ClipDialog } from "@/components/sound/clip-dialog"
import { StopAllRow } from "@/components/sound/stop-all-row"
import { Button } from "@/components/ui/button"
import { Card, CardAction, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty"
import { api } from "@/lib/api"
import { shortcutLabel } from "@/lib/keys"
import type { SoundClip, SoundSnapshot } from "@/lib/types"
import { cn } from "@/lib/utils"

const ACCEPT = ".wav,.mp3,.m4a,.aac,.ogg,.flac,audio/wav,audio/mpeg,audio/mp4,audio/aac,audio/ogg,audio/flac"

/** The sounds: click one to play it, drop files on to add them */
export function SoundboardCard({ sound }: { sound: SoundSnapshot }) {
  const queryClient = useQueryClient()
  const input = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)

  const clips = sound.clips.filter((clip) => !clip.stopAll)
  const stopAllClip = sound.clips.find((clip) => clip.stopAll)
  // Looked up each time, so the dialog shows changes made from it (like a new shortcut)
  const editing = clips.find((clip) => clip.id === editingId) ?? null
  const playing = new Set(sound.state.playing)

  const upload = useMutation({
    mutationFn: api.uploadClips,
    onSuccess: (added) => {
      queryClient.invalidateQueries()
      toast.success(added.length === 1 ? `Added ${added[0].name}` : `Added ${added.length} sounds`)
    },
    onError: (e: Error) => toast.error(e.message),
  })
  const stopAll = useMutation({
    mutationFn: api.stopSounds,
    onError: (e: Error) => toast.error(e.message),
  })

  const add = (files: FileList | null) => {
    if (files && files.length > 0) upload.mutate([...files])
  }

  return (
    <Card
      size="sm"
      className={cn("transition-colors", dragging && "border-primary bg-primary/5")}
      onDragOver={(e) => {
        if (!e.dataTransfer.types.includes("Files")) return
        e.preventDefault()
        setDragging(true)
      }}
      onDragLeave={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node)) setDragging(false)
      }}
      onDrop={(e) => {
        e.preventDefault()
        setDragging(false)
        add(e.dataTransfer.files)
      }}
    >
      <CardHeader>
        <CardTitle>Soundboard</CardTitle>
        <CardDescription>
          Click to play. Box and joystick buttons can play them too.
        </CardDescription>
        <CardAction className="flex gap-2">
          {playing.size > 0 && (
            <Button size="icon-sm" variant="outline" onClick={() => stopAll.mutate()} aria-label="Stop all sounds" title="Stop all sounds">
              <Square />
            </Button>
          )}
          <Button size="sm" onClick={() => input.current?.click()} disabled={upload.isPending}>
            <Upload data-icon="inline-start" />
            {upload.isPending ? "Adding…" : "Add sounds"}
          </Button>
          <input
            ref={input}
            type="file"
            accept={ACCEPT}
            multiple
            hidden
            onChange={(e) => {
              add(e.target.files)
              e.target.value = ""
            }}
          />
        </CardAction>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <CableMeter level={sound.state.cableLevel} className="rounded-lg border px-3 py-2" />
        {clips.length === 0 ? (
          <Empty className="border border-dashed">
            <EmptyHeader>
              <EmptyMedia variant="icon">
                <FileAudio />
              </EmptyMedia>
              <EmptyTitle>No sounds yet</EmptyTitle>
              <EmptyDescription>Drop WAV, MP3, M4A, OGG or FLAC files here, or choose some.</EmptyDescription>
            </EmptyHeader>
            <EmptyContent>
              <Button size="sm" variant="outline" onClick={() => input.current?.click()}>
                <Upload data-icon="inline-start" />
                Choose files
              </Button>
            </EmptyContent>
          </Empty>
        ) : (
          <ul className="grid grid-cols-[repeat(auto-fill,minmax(10rem,1fr))] gap-2">
            {clips.map((clip) => (
              <ClipTile key={clip.id} clip={clip} playing={playing.has(clip.id)} onEdit={() => setEditingId(clip.id)} />
            ))}
          </ul>
        )}
      </CardContent>

      {stopAllClip && clips.length > 0 && (
        <CardFooter className="border-t">
          <StopAllRow clip={stopAllClip} />
        </CardFooter>
      )}

      <ClipDialog clip={editing} onOpenChange={(open) => !open && setEditingId(null)} />
    </Card>
  )
}

function ClipTile({ clip, playing, onEdit }: { clip: SoundClip; playing: boolean; onEdit: () => void }) {
  const queryClient = useQueryClient()
  const missing = clip.duration === null

  const play = useMutation({
    mutationFn: () => api.playClip(clip.id),
    onError: (e: Error) => toast.error(e.message),
  })
  const remove = useMutation({
    mutationFn: () => api.deleteClip(clip.id),
    onSuccess: ({ removedBindings }) => {
      queryClient.invalidateQueries()
      toast.success(
        removedBindings ? `Removed ${clip.name} and ${removedBindings} binding${removedBindings === 1 ? "" : "s"}` : `Removed ${clip.name}`
      )
    },
    onError: (e: Error) => toast.error(e.message),
  })

  return (
    <li
      className={cn(
        "group relative flex min-w-0 items-stretch overflow-hidden rounded-lg border bg-muted/30 transition-colors",
        playing && "border-emerald-500 bg-emerald-500/10"
      )}
    >
      <button
        type="button"
        onClick={() => play.mutate()}
        disabled={missing}
        aria-label={playing ? `Stop ${clip.name}` : `Play ${clip.name}`}
        className="flex min-w-0 flex-1 items-center gap-2.5 px-3 py-2.5 text-left hover:bg-muted/60 disabled:cursor-not-allowed disabled:opacity-60"
      >
        <span
          className={cn(
            "flex size-8 shrink-0 items-center justify-center rounded-full border bg-background",
            playing && "border-emerald-500 text-emerald-600 dark:text-emerald-300"
          )}
        >
          {playing ? <Square className="size-3.5" /> : <Play className="size-3.5" />}
        </span>
        <span className="flex min-w-0 flex-col">
          <span className="truncate text-sm font-medium">{clip.name}</span>
          <span className="truncate text-xs text-muted-foreground">
            {missing ? "File missing" : clipDetails(clip)}
          </span>
        </span>
      </button>
      {playing && <span className="absolute inset-x-0 bottom-0 h-0.5 animate-pulse bg-emerald-500" />}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button size="icon-sm" variant="ghost" className="my-auto mr-1 shrink-0" aria-label={`${clip.name} options`}>
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

function clipDetails(clip: SoundClip) {
  const parts = [formatDuration(clip.duration ?? 0)]
  if (clip.hotkey) parts.push(shortcutLabel(clip.hotkey))
  if (clip.volume !== undefined && clip.volume !== 1) parts.push(`${Math.round(clip.volume * 100)}%`)
  if (clip.bindingCount > 0) parts.push(`${clip.bindingCount} binding${clip.bindingCount === 1 ? "" : "s"}`)
  return parts.join(" · ")
}

function formatDuration(seconds: number) {
  if (seconds < 60) return `${seconds < 10 ? seconds.toFixed(1) : Math.round(seconds)}s`
  return `${Math.floor(seconds / 60)}:${String(Math.round(seconds % 60)).padStart(2, "0")}`
}
