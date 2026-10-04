import { ChevronsUpDown, Keyboard, Plus, X } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command"
import { Kbd } from "@/components/ui/kbd"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { keyFromEvent, keyLabel } from "@/lib/keys"
import type { KeyStep } from "@/lib/types"
import { cn } from "@/lib/utils"

const typeHints: Record<string, string> = {
  tap: "Press and release",
  infinite: "Hold down until released",
  off: "Release a held key",
  toggle: "Hold down, or release if held",
}

interface KeyboardEditorProps {
  value: KeyStep[]
  onChange: (steps: KeyStep[]) => void
  keys: string[]
  types: { value: string; label: string }[]
}

/** Builds a key sequence: record keys by pressing them, or pick ones the keyboard doesn't have */
export function KeyboardEditor({ value, onChange, keys, types }: KeyboardEditorProps) {
  const [recording, setRecording] = useState(false)
  const [problem, setProblem] = useState<string | null>(null)
  const supported = new Set(keys)

  const add = (key: string) => {
    if (!supported.has(key)) {
      setProblem(`${keyLabel(key)} can't be sent`)
      return
    }
    setProblem(null)
    onChange([...value, { key, type: "tap" }])
  }

  const onKeyDown = (event: React.KeyboardEvent) => {
    // Capture everything, including Tab and Esc, rather than letting the page or dialog act on it
    event.preventDefault()
    event.stopPropagation()
    if (event.repeat) return
    const key = keyFromEvent(event)
    if (key) add(key)
    else setProblem("That key can't be sent")
  }

  return (
    <div className="flex flex-col gap-3">
      <button
        type="button"
        data-key-recorder
        onKeyDown={onKeyDown}
        onFocus={() => setRecording(true)}
        onBlur={() => setRecording(false)}
        className={cn(
          "flex h-16 items-center justify-center gap-2 rounded-lg border-2 border-dashed text-sm text-muted-foreground outline-none transition-colors",
          recording && "border-primary bg-primary/5 text-foreground"
        )}
      >
        <Keyboard className="size-4" />
        {recording ? "Recording - press keys to add them. Click away to stop." : "Click here, then press keys"}
      </button>
      {problem && <p className="-mt-1 text-xs text-destructive">{problem}</p>}

      {value.length > 0 && (
        <ol className="divide-y rounded-lg border">
          {value.map((step, index) => (
            <li key={index} className="flex items-center gap-3 px-3 py-2">
              <span className="w-5 text-xs text-muted-foreground tabular-nums">{index + 1}</span>
              <Kbd className="min-w-12 justify-center">{keyLabel(step.key)}</Kbd>
              <Select
                value={step.type}
                onValueChange={(type) => onChange(value.map((s, i) => (i === index ? { ...s, type } : s)))}
              >
                <SelectTrigger size="sm" className="ml-auto w-44" aria-label={`What to do with ${keyLabel(step.key)}`}>
                  {/* Just the label - the items also show a hint, which shouldn't repeat in the trigger */}
                  <SelectValue>{types.find((type) => type.value === step.type)?.label}</SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {types.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      <span>{type.label}</span>
                      <span className="text-xs text-muted-foreground">{typeHints[type.value]}</span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                type="button"
                size="icon-sm"
                variant="ghost"
                aria-label={`Remove ${keyLabel(step.key)}`}
                onClick={() => onChange(value.filter((_, i) => i !== index))}
              >
                <X />
              </Button>
            </li>
          ))}
        </ol>
      )}

      <KeyPicker keys={keys} onPick={add} />
    </div>
  )
}

function KeyPicker({ keys, onPick }: { keys: string[]; onPick: (key: string) => void }) {
  const [open, setOpen] = useState(false)
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button type="button" variant="outline" size="sm" className="self-start">
          <Plus data-icon="inline-start" />
          Add a key from the list
          <ChevronsUpDown data-icon="inline-end" className="text-muted-foreground" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-64 p-0" align="start">
        <Command>
          <CommandInput placeholder="Search keys" />
          <CommandList>
            <CommandEmpty>No key with that name.</CommandEmpty>
            <CommandGroup>
              {keys.map((key) => (
                <CommandItem
                  key={key}
                  value={`${keyLabel(key)} ${key}`}
                  onSelect={() => {
                    onPick(key)
                    setOpen(false)
                  }}
                >
                  {keyLabel(key)}
                  <span className="ml-auto font-mono text-xs text-muted-foreground">{key}</span>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}

/** Short summary of an action's keys for tables, e.g. "Left Ctrl + C" */
export function KeySequence({ steps }: { steps: KeyStep[] }) {
  return (
    <span className="flex flex-wrap items-center gap-1">
      {steps.map((step, index) => (
        <span key={index} className="flex items-center gap-1">
          {index > 0 && <span className="text-xs text-muted-foreground">+</span>}
          <Kbd>{keyLabel(step.key)}</Kbd>
          {step.type !== "tap" && (
            <span className="text-xs text-muted-foreground">
              {step.type === "infinite" ? "hold" : step.type === "off" ? "release" : "toggle"}
            </span>
          )}
        </span>
      ))}
    </span>
  )
}
