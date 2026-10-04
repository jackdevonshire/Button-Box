import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Copy, MoreHorizontal, Pencil, Plus, Trash2 } from "lucide-react"
import { useState } from "react"
import { Link } from "react-router"
import { toast } from "sonner"

import { ConfigurationDialog } from "@/components/configurations/configuration-dialog"
import { Lcd } from "@/components/panel/panel-view"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardAction, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"
import { useConfigurations } from "@/lib/queries"
import type { Configuration } from "@/lib/types"

export function ConfigurationsPage() {
  const { data: configurations } = useConfigurations()
  const [editing, setEditing] = useState<Configuration | "new" | null>(null)
  const [deleting, setDeleting] = useState<Configuration | null>(null)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-xl font-semibold">Configurations</h1>
          <p className="text-sm text-muted-foreground">Sets of bindings you can switch between.</p>
        </div>
        <Button onClick={() => setEditing("new")}>
          <Plus data-icon="inline-start" />
          New configuration
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {configurations
          ? configurations.map((configuration) => (
              <ConfigurationCard
                key={configuration.id}
                configuration={configuration}
                onEdit={() => setEditing(configuration)}
                onDelete={() => setDeleting(configuration)}
              />
            ))
          : [0, 1, 2].map((i) => <Skeleton key={i} className="h-64 rounded-xl" />)}
      </div>

      <ConfigurationDialog
        open={editing !== null}
        onOpenChange={(open) => !open && setEditing(null)}
        configuration={editing === "new" ? undefined : (editing ?? undefined)}
      />
      <DeleteConfigurationDialog configuration={deleting} onClose={() => setDeleting(null)} />
    </div>
  )
}

function ConfigurationCard({
  configuration,
  onEdit,
  onDelete,
}: {
  configuration: Configuration
  onEdit: () => void
  onDelete: () => void
}) {
  const queryClient = useQueryClient()
  const activate = useMutation({
    mutationFn: () => api.activateConfiguration(configuration.id),
    onSuccess: () => {
      queryClient.invalidateQueries()
      toast.success(`Switched to ${configuration.name}`)
    },
    onError: (e: Error) => toast.error(e.message),
  })
  const duplicate = useMutation({
    mutationFn: () => api.duplicateConfiguration(configuration.id),
    onSuccess: (copy) => {
      queryClient.invalidateQueries()
      toast.success(`Created ${copy.name}`)
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const count = configuration.bindingCount ?? 0

  return (
    <Card className={configuration.active ? "ring-2 ring-primary/60" : undefined}>
      <CardHeader>
        <CardTitle className="truncate">{configuration.name}</CardTitle>
        <CardDescription className="line-clamp-2 min-h-10">
          {configuration.description || "No description"}
        </CardDescription>
        <CardAction>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button size="icon-sm" variant="ghost" aria-label={`${configuration.name} options`}>
                <MoreHorizontal />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onSelect={onEdit}>
                <Pencil />
                Edit
              </DropdownMenuItem>
              <DropdownMenuItem onSelect={() => duplicate.mutate()}>
                <Copy />
                Duplicate
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem variant="destructive" onSelect={onDelete} disabled={configuration.active}>
                <Trash2 />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </CardAction>
      </CardHeader>
      <CardContent>
        <div className="rounded-lg bg-zinc-950 p-2">
          <Lcd lines={configuration.displayLines} />
        </div>
      </CardContent>
      <CardFooter className="justify-between gap-2">
        <span className="text-sm text-muted-foreground">
          {count === 1 ? "1 binding" : `${count} bindings`}
          {(configuration.joystickMappingCount ?? 0) > 0 &&
            ` · ${configuration.joystickMappingCount} joystick`}
        </span>
        {configuration.active ? (
          <div className="flex items-center gap-2">
            <Badge>Active</Badge>
            <Button size="sm" variant="outline" asChild>
              <Link to="/">Open panel</Link>
            </Button>
          </div>
        ) : (
          <Button size="sm" variant="outline" onClick={() => activate.mutate()} disabled={activate.isPending}>
            Switch to
          </Button>
        )}
      </CardFooter>
    </Card>
  )
}

function DeleteConfigurationDialog({ configuration, onClose }: { configuration: Configuration | null; onClose: () => void }) {
  const queryClient = useQueryClient()
  const remove = useMutation({
    mutationFn: (id: number) => api.deleteConfiguration(id),
    onSuccess: () => {
      queryClient.invalidateQueries()
      toast.success("Configuration deleted")
      onClose()
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const count = configuration?.bindingCount ?? 0

  return (
    <AlertDialog open={configuration !== null} onOpenChange={(open) => !open && onClose()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete {configuration?.name}?</AlertDialogTitle>
          <AlertDialogDescription>
            {count > 0
              ? `Its ${count === 1 ? "binding" : `${count} bindings`} will be deleted too. `
              : ""}
            Any buttons set to switch to it will stop working. Your actions aren't affected.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            variant="destructive"
            onClick={(e) => {
              e.preventDefault()
              if (configuration) remove.mutate(configuration.id)
            }}
          >
            Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
