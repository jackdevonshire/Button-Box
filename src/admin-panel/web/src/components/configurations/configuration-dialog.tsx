import { useMutation, useQueryClient } from "@tanstack/react-query"
import { MonitorUp } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"

import { Lcd } from "@/components/panel/panel-view"
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
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import { api } from "@/lib/api"
import type { Configuration } from "@/lib/types"

const LCD_COLS = 20
const defaultLines = (name: string) => ["", "Current Mode", name, ""]

interface ConfigurationDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** The configuration being edited, or undefined to create one */
  configuration?: Configuration
}

export function ConfigurationDialog({ open, onOpenChange, configuration }: ConfigurationDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        {/* Dialog content unmounts when closed, so the form starts fresh each time it opens */}
        <ConfigurationForm configuration={configuration} onDone={() => onOpenChange(false)} />
      </DialogContent>
    </Dialog>
  )
}

function ConfigurationForm({ configuration, onDone }: { configuration?: Configuration; onDone: () => void }) {
  const queryClient = useQueryClient()
  const [name, setName] = useState(configuration?.name ?? "")
  const [description, setDescription] = useState(configuration?.description ?? "")
  const [customDisplay, setCustomDisplay] = useState(configuration?.customDisplay ?? false)
  const [lines, setLines] = useState<string[]>(configuration?.displayLines ?? defaultLines(""))
  const [error, setError] = useState<string | null>(null)

  const screen = customDisplay ? lines : defaultLines(name)

  const save = useMutation({
    mutationFn: () => {
      const input = { name, description, displayLines: customDisplay ? lines : null }
      return configuration ? api.updateConfiguration(configuration.id, input) : api.createConfiguration(input)
    },
    onSuccess: () => {
      queryClient.invalidateQueries()
      toast.success(configuration ? "Configuration saved" : "Configuration created")
      onDone()
    },
    onError: (e: Error) => setError(e.message),
  })

  const preview = useMutation({
    mutationFn: () => api.previewDisplay(screen, 5),
    onSuccess: () => toast("Showing on the box for 5 seconds"),
    onError: (e: Error) => toast.error(e.message),
  })

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) {
      setError("Enter a name")
      return
    }
    save.mutate()
  }

  return (
    <form onSubmit={submit}>
      <DialogHeader>
        <DialogTitle>{configuration ? "Edit configuration" : "New configuration"}</DialogTitle>
        <DialogDescription>
          A configuration is a set of bindings. Switch between them from the panel or with the box's mode button.
        </DialogDescription>
      </DialogHeader>

      <FieldGroup className="py-4">
        <Field data-invalid={error === "Enter a name" || undefined}>
          <FieldLabel htmlFor="configuration-name">Name</FieldLabel>
          <Input
            id="configuration-name"
            value={name}
            onChange={(e) => {
              setName(e.target.value)
              setError(null)
            }}
            placeholder="Flight sim"
            autoFocus
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="configuration-description">Description</FieldLabel>
          <Textarea
            id="configuration-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Controls for Microsoft Flight Simulator"
            rows={2}
          />
        </Field>

        <Field orientation="horizontal">
          <Switch
            id="custom-display"
            checked={customDisplay}
            onCheckedChange={(checked) => {
              // Start editing from what the screen shows now, rather than a blank template
              if (checked && !configuration?.customDisplay) setLines(defaultLines(name))
              setCustomDisplay(checked)
            }}
          />
          <FieldLabel htmlFor="custom-display">Custom screen</FieldLabel>
        </Field>

        <div className="flex flex-col gap-3 rounded-xl bg-zinc-950 p-3">
          <Lcd lines={screen} />
          {customDisplay && (
            <div className="grid grid-cols-2 gap-2">
              {lines.map((line, index) => (
                <Input
                  key={index}
                  value={line}
                  maxLength={LCD_COLS}
                  onChange={(e) =>
                    setLines((current) => current.map((l, i) => (i === index ? e.target.value : l)))
                  }
                  placeholder={`Line ${index + 1}`}
                  aria-label={`Screen line ${index + 1}`}
                  className="border-zinc-700 bg-zinc-900 font-mono text-zinc-100"
                />
              ))}
            </div>
          )}
        </div>
        <FieldDescription className="-mt-2 flex items-center justify-between gap-2">
          <span>
            {customDisplay
              ? `Shown on the box while this configuration is active. Up to ${LCD_COLS} characters a line.`
              : "The box shows the configuration's name while it's active."}
          </span>
          <Button type="button" size="xs" variant="ghost" onClick={() => preview.mutate()}>
            <MonitorUp data-icon="inline-start" />
            Show on box
          </Button>
        </FieldDescription>

        {error && <p className="text-sm text-destructive">{error}</p>}
      </FieldGroup>

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" disabled={save.isPending}>
          {configuration ? "Save" : "Create"}
        </Button>
      </DialogFooter>
    </form>
  )
}
