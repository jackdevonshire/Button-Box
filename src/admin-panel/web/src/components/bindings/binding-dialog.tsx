import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Check, ChevronsUpDown } from "lucide-react"
import { useMemo, useState } from "react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
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
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Switch } from "@/components/ui/switch"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { api } from "@/lib/api"
import { eventLabel, integrationIconById } from "@/lib/controls"
import { useActions, useControls, useIntegrations } from "@/lib/queries"
import type { Action, Binding, Control, ControlEvent } from "@/lib/types"
import { cn } from "@/lib/utils"

interface BindingDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  configurationId: number
  control: Control
  /** The binding being edited, or undefined to create one */
  binding?: Binding
  defaultEvent?: ControlEvent
}

export function BindingDialog({ open, onOpenChange, ...props }: BindingDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        {/* Dialog content unmounts when closed, so the form starts fresh each time it opens */}
        <BindingForm {...props} onDone={() => onOpenChange(false)} />
      </DialogContent>
    </Dialog>
  )
}

function BindingForm({
  configurationId,
  control,
  binding,
  defaultEvent,
  onDone,
}: Omit<BindingDialogProps, "open" | "onOpenChange"> & { onDone: () => void }) {
  const queryClient = useQueryClient()
  const { data: controls = [] } = useControls()
  const { data: actions = [] } = useActions()
  const { data: integrations = [] } = useIntegrations()

  const [actionId, setActionId] = useState(binding?.action.id)
  const [name, setName] = useState(binding?.name ?? "")
  const [event, setEvent] = useState<ControlEvent>(binding?.event ?? defaultEvent ?? "on")
  const [modifiers, setModifiers] = useState<string[]>(binding?.modifiers ?? [])
  const [enabled, setEnabled] = useState(binding?.enabled ?? true)
  const [error, setError] = useState<string | null>(null)

  const selectedAction = actions.find((action) => action.id === actionId)

  const save = useMutation({
    mutationFn: () => {
      const input = { name, event, actionId, modifiers, enabled, control: control.id }
      return binding ? api.updateBinding(binding.id, input) : api.createBinding(configurationId, input)
    },
    onSuccess: () => {
      queryClient.invalidateQueries()
      toast.success(binding ? "Binding saved" : "Binding added")
      onDone()
    },
    onError: (e: Error) => setError(e.message),
  })

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!actionId) {
      setError("Choose an action")
      return
    }
    save.mutate()
  }

  const toggleModifier = (id: string) =>
    setModifiers((current) => (current.includes(id) ? current.filter((m) => m !== id) : [...current, id]))

  const otherControls = controls.filter((c) => c.id !== control.id)
  const inactiveIntegrations = new Set(integrations.filter((i) => !i.active).map((i) => i.id))

  return (
    <form onSubmit={submit}>
      <DialogHeader>
        <DialogTitle>{binding ? "Edit binding" : "Add binding"}</DialogTitle>
        <DialogDescription>Choose what happens when you use {control.label} on the box.</DialogDescription>
      </DialogHeader>

      <FieldGroup className="py-4">
        <Field>
          <FieldLabel>When</FieldLabel>
          <ToggleGroup
            type="single"
            variant="outline"
            value={event}
            onValueChange={(value) => value && setEvent(value as ControlEvent)}
            className="w-full"
          >
            <ToggleGroupItem value="on" className="flex-1">{eventLabel(control.kind, "on")}</ToggleGroupItem>
            <ToggleGroupItem value="off" className="flex-1">{eventLabel(control.kind, "off")}</ToggleGroupItem>
          </ToggleGroup>
        </Field>

        <Field data-invalid={error === "Choose an action" || undefined}>
          <FieldLabel>Action</FieldLabel>
          <ActionPicker
            actions={actions}
            value={selectedAction}
            inactiveIntegrations={inactiveIntegrations}
            onChange={(action) => {
              setActionId(action.id)
              setError(null)
            }}
          />
        </Field>

        <Field>
          <FieldLabel htmlFor="binding-name">Label</FieldLabel>
          <Input
            id="binding-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder={selectedAction?.name ?? "Landing gear"}
          />
          <FieldDescription>Shown on the panel. Leave blank to use the action's name.</FieldDescription>
        </Field>

        <Field>
          <FieldLabel>Only while these are on</FieldLabel>
          <div className="flex flex-wrap gap-1.5">
            {otherControls.map((c) => {
              const active = modifiers.includes(c.id)
              return (
                <Button
                  key={c.id}
                  type="button"
                  size="xs"
                  variant={active ? "default" : "outline"}
                  aria-pressed={active}
                  onClick={() => toggleModifier(c.id)}
                >
                  {c.label}
                </Button>
              )
            })}
          </div>
          <FieldDescription>
            Optional. Gives {control.label} a different action while another control is held or switched on.
          </FieldDescription>
        </Field>

        <Field orientation="horizontal">
          <Switch id="binding-enabled" checked={enabled} onCheckedChange={setEnabled} />
          <FieldLabel htmlFor="binding-enabled">Enabled</FieldLabel>
        </Field>

        {error && <p className="text-sm text-destructive">{error}</p>}
      </FieldGroup>

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" disabled={save.isPending}>
          {binding ? "Save" : "Add binding"}
        </Button>
      </DialogFooter>
    </form>
  )
}

function ActionPicker({
  actions,
  value,
  inactiveIntegrations,
  onChange,
}: {
  actions: Action[]
  value: Action | undefined
  inactiveIntegrations: Set<number>
  onChange: (action: Action) => void
}) {
  const [open, setOpen] = useState(false)

  const groups = useMemo(() => {
    const byIntegration = new Map<string, Action[]>()
    for (const action of actions) {
      const group = byIntegration.get(action.integrationName) ?? []
      group.push(action)
      byIntegration.set(action.integrationName, group)
    }
    return [...byIntegration.entries()]
  }, [actions])

  const ValueIcon = value ? integrationIconById[value.integrationId] : null

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button type="button" variant="outline" role="combobox" aria-expanded={open} className="w-full justify-between font-normal">
          <span className="flex min-w-0 items-center gap-2">
            {ValueIcon && <ValueIcon className="text-muted-foreground" />}
            <span className={cn("truncate", !value && "text-muted-foreground")}>
              {value ? value.name : "Choose an action"}
            </span>
          </span>
          <ChevronsUpDown className="text-muted-foreground" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-(--radix-popover-trigger-width) p-0" align="start">
        <Command>
          <CommandInput placeholder="Search actions" />
          <CommandList>
            <CommandEmpty>No actions found. Create one from Actions in the sidebar.</CommandEmpty>
            {groups.map(([integrationName, groupActions]) => (
              <CommandGroup key={integrationName} heading={integrationName}>
                {groupActions.map((action) => {
                  const Icon = integrationIconById[action.integrationId]
                  return (
                    <CommandItem
                      key={action.id}
                      value={`${integrationName} ${action.name} ${action.id}`}
                      onSelect={() => {
                        onChange(action)
                        setOpen(false)
                      }}
                    >
                      {Icon && <Icon className="text-muted-foreground" />}
                      <span className="truncate">{action.name}</span>
                      {inactiveIntegrations.has(action.integrationId) && (
                        <span className="text-xs text-muted-foreground">(turned off)</span>
                      )}
                      <Check className={cn("ml-auto", value?.id === action.id ? "opacity-100" : "opacity-0")} />
                    </CommandItem>
                  )
                })}
              </CommandGroup>
            ))}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
