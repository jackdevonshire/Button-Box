import { useMutation, useQueryClient } from "@tanstack/react-query"
import { MoreHorizontal, Pencil, Play, Plus, Trash2 } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"

import { BindingDialog } from "@/components/bindings/binding-dialog"
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
import { Switch } from "@/components/ui/switch"
import { api } from "@/lib/api"
import { controlLabel, eventLabel, integrationIconById, kindLabels } from "@/lib/controls"
import { useControls } from "@/lib/queries"
import type { Binding, Control, ControlEvent } from "@/lib/types"
import { cn } from "@/lib/utils"

interface ControlInspectorProps {
  control: Control
  state: ControlEvent | undefined
  bindings: Binding[]
  configurationId: number
}

export function ControlInspector({ control, state, bindings, configurationId }: ControlInspectorProps) {
  const [dialog, setDialog] = useState<{ binding?: Binding; event: ControlEvent } | null>(null)

  return (
    <Card>
      <CardHeader>
        <CardTitle>{control.label}</CardTitle>
        <CardDescription>
          {kindLabels[control.kind]} · <span className="font-mono text-xs">{control.id}</span>
        </CardDescription>
        <CardAction>
          <Badge variant={state === "on" ? "default" : "outline"}>
            {state ? (state === "on" ? "On" : "Off") : "State unknown"}
          </Badge>
        </CardAction>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        {(["on", "off"] as const).map((event) => {
          const eventBindings = bindings.filter((binding) => binding.event === event)
          return (
            <section key={event} className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium">{eventLabel(control.kind, event)}</h3>
                <Button size="xs" variant="ghost" onClick={() => setDialog({ event })}>
                  <Plus data-icon="inline-start" />
                  Add
                </Button>
              </div>
              {eventBindings.length === 0 ? (
                <p className="rounded-lg border border-dashed px-3 py-2.5 text-sm text-muted-foreground">
                  Nothing happens yet.
                </p>
              ) : (
                <ul className="divide-y rounded-lg border">
                  {eventBindings.map((binding) => (
                    <BindingRow key={binding.id} binding={binding} onEdit={() => setDialog({ binding, event })} />
                  ))}
                </ul>
              )}
            </section>
          )
        })}
      </CardContent>

      <BindingDialog
        open={dialog !== null}
        onOpenChange={(open) => !open && setDialog(null)}
        configurationId={configurationId}
        control={control}
        binding={dialog?.binding}
        defaultEvent={dialog?.event}
      />
    </Card>
  )
}

function BindingRow({ binding, onEdit }: { binding: Binding; onEdit: () => void }) {
  const queryClient = useQueryClient()
  const { data: controls } = useControls()
  const Icon = integrationIconById[binding.action.integrationId]

  const update = useMutation({
    mutationFn: (enabled: boolean) => api.updateBinding(binding.id, { enabled }),
    onSuccess: () => queryClient.invalidateQueries(),
    onError: (e: Error) => toast.error(e.message),
  })
  const remove = useMutation({
    mutationFn: () => api.deleteBinding(binding.id),
    onSuccess: () => {
      queryClient.invalidateQueries()
      toast.success("Binding removed")
    },
    onError: (e: Error) => toast.error(e.message),
  })
  const test = useMutation({
    mutationFn: () => api.testAction(binding.action.id),
    onSuccess: () => toast.success(`Ran ${binding.action.name}`),
    onError: (e: Error) => toast.error(e.message),
  })

  return (
    <li className={cn("flex items-center gap-3 px-3 py-2.5", !binding.enabled && "opacity-60")}>
      {Icon && <Icon className="size-4 shrink-0 text-muted-foreground" />}
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{binding.name || binding.action.name}</p>
        <p className="truncate text-xs text-muted-foreground">
          {binding.action.integrationName}
          {binding.name && binding.name !== binding.action.name && ` · ${binding.action.name}`}
        </p>
        {binding.modifiers.length > 0 && (
          <div className="mt-1 flex flex-wrap gap-1">
            {binding.modifiers.map((modifier) => (
              <Badge key={modifier} variant="secondary" className="text-[11px]">
                while {controlLabel(controls, modifier)} on
              </Badge>
            ))}
          </div>
        )}
      </div>
      <Switch
        checked={binding.enabled}
        onCheckedChange={(enabled) => update.mutate(enabled)}
        aria-label={binding.enabled ? "Disable binding" : "Enable binding"}
      />
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button size="icon-sm" variant="ghost" aria-label="Binding options">
            <MoreHorizontal />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onSelect={onEdit}>
            <Pencil />
            Edit
          </DropdownMenuItem>
          <DropdownMenuItem onSelect={() => test.mutate()}>
            <Play />
            Test action
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
