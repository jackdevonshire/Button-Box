import { useMutation, useQueryClient } from "@tanstack/react-query"
import { MoreHorizontal, Pencil, Play, Plus, PowerOff, Trash2 } from "lucide-react"
import { useState } from "react"
import { Navigate, useParams } from "react-router"
import { toast } from "sonner"

import { ActionDialog } from "@/components/actions/action-dialog"
import { KeySequence } from "@/components/actions/keyboard-editor"
import { IntegrationIcon } from "@/components/integration-icon"
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
import { Card } from "@/components/ui/card"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { api } from "@/lib/api"
import { useActions, useIntegrations } from "@/lib/queries"
import type { Action, Integration, KeyStep } from "@/lib/types"

export function ActionsPage() {
  const { editor } = useParams()
  const { data: integrations } = useIntegrations()
  const { data: actions } = useActions()
  const [editing, setEditing] = useState<Action | "new" | null>(null)
  const [deleting, setDeleting] = useState<Action | null>(null)

  if (!integrations || !actions) return <Skeleton className="h-96 rounded-xl" />

  const integration = integrations.find((i) => i.actionEditor === editor)
  if (!integration) return <Navigate to="/" replace />

  const integrationActions = actions.filter((action) => action.integrationId === integration.id)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-lg bg-muted">
            <IntegrationIcon icon={integration.icon} className="size-5" />
          </div>
          <div>
            <h1 className="text-xl font-semibold">{integration.name}</h1>
            <p className="text-sm text-muted-foreground">{integration.description}</p>
          </div>
        </div>
        <Button onClick={() => setEditing("new")}>
          <Plus data-icon="inline-start" />
          New action
        </Button>
      </div>

      {!integration.active && <InactiveNotice integration={integration} />}

      {integrationActions.length === 0 ? (
        <Empty className="border border-dashed">
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <IntegrationIcon icon={integration.icon} />
            </EmptyMedia>
            <EmptyTitle>Create your first {integration.name.toLowerCase()} action</EmptyTitle>
            <EmptyDescription>Actions are what the box's controls do. Once you've made one, bind it to a control on the panel.</EmptyDescription>
          </EmptyHeader>
          <EmptyContent>
            <Button onClick={() => setEditing("new")}>
              <Plus data-icon="inline-start" />
              New action
            </Button>
          </EmptyContent>
        </Empty>
      ) : (
        <Card className="py-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="pl-4">Name</TableHead>
                <TableHead>Does</TableHead>
                <TableHead className="w-28">Used by</TableHead>
                <TableHead className="w-12" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {integrationActions.map((action) => (
                <ActionRow
                  key={action.id}
                  action={action}
                  editor={integration.actionEditor}
                  onEdit={() => setEditing(action)}
                  onDelete={() => setDeleting(action)}
                />
              ))}
            </TableBody>
          </Table>
        </Card>
      )}

      <ActionDialog
        open={editing !== null}
        onOpenChange={(open) => !open && setEditing(null)}
        integration={integration}
        action={editing === "new" ? undefined : (editing ?? undefined)}
      />
      <DeleteActionDialog action={deleting} onClose={() => setDeleting(null)} />
    </div>
  )
}

function ActionRow({
  action,
  editor,
  onEdit,
  onDelete,
}: {
  action: Action
  editor: Integration["actionEditor"]
  onEdit: () => void
  onDelete: () => void
}) {
  const test = useMutation({
    mutationFn: () => api.testAction(action.id),
    onSuccess: () => toast.success(`Ran ${action.name}`),
    onError: (e: Error) => toast.error(e.message),
  })

  return (
    <TableRow>
      <TableCell className="max-w-56 pl-4">
        <p className="truncate font-medium">{action.name}</p>
        {action.description && <p className="truncate text-xs text-muted-foreground">{action.description}</p>}
      </TableCell>
      <TableCell className="max-w-80">
        <ActionSummary action={action} editor={editor} />
      </TableCell>
      <TableCell>
        {action.bindingCount > 0 ? (
          <Badge variant="secondary">{action.bindingCount === 1 ? "1 binding" : `${action.bindingCount} bindings`}</Badge>
        ) : (
          <span className="text-sm text-muted-foreground">Unused</span>
        )}
      </TableCell>
      <TableCell className="pr-4 text-right">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button size="icon-sm" variant="ghost" aria-label={`${action.name} options`}>
              <MoreHorizontal />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onSelect={() => test.mutate()}>
              <Play />
              Run now
            </DropdownMenuItem>
            <DropdownMenuItem onSelect={onEdit}>
              <Pencil />
              Edit
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem variant="destructive" onSelect={onDelete}>
              <Trash2 />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </TableCell>
    </TableRow>
  )
}

function ActionSummary({ action, editor }: { action: Action; editor: Integration["actionEditor"] }) {
  if (editor === "keyboard") return <KeySequence steps={action.configuration as KeyStep[]} />
  const text = String(action.configuration ?? "")
  if (editor === "script") {
    const lines = text.split("\n").filter((line) => line.trim())
    return (
      <span className="flex items-center gap-2">
        <code className="truncate font-mono text-xs">{lines[0]}</code>
        {lines.length > 1 && <span className="shrink-0 text-xs text-muted-foreground">+{lines.length - 1} lines</span>}
      </span>
    )
  }
  return <code className="block truncate font-mono text-xs">{text}</code>
}

function InactiveNotice({ integration }: { integration: Integration }) {
  const queryClient = useQueryClient()
  const enable = useMutation({
    mutationFn: () => api.setIntegrationActive(integration.id, true),
    onSuccess: () => {
      queryClient.invalidateQueries()
      toast.success(`${integration.name} turned on`)
    },
    onError: (e: Error) => toast.error(e.message),
  })
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm">
      <PowerOff className="size-4 text-amber-600 dark:text-amber-400" />
      <p className="flex-1">{integration.name} is turned off, so these actions won't run when their controls are used.</p>
      <Button size="sm" variant="outline" onClick={() => enable.mutate()} disabled={enable.isPending}>
        Turn on
      </Button>
    </div>
  )
}

function DeleteActionDialog({ action, onClose }: { action: Action | null; onClose: () => void }) {
  const queryClient = useQueryClient()
  const remove = useMutation({
    mutationFn: (id: number) => api.deleteAction(id),
    onSuccess: () => {
      queryClient.invalidateQueries()
      toast.success("Action deleted")
      onClose()
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const count = action?.bindingCount ?? 0
  return (
    <AlertDialog open={action !== null} onOpenChange={(open) => !open && onClose()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete {action?.name}?</AlertDialogTitle>
          <AlertDialogDescription>
            {count > 0
              ? `It's used by ${count === 1 ? "1 binding" : `${count} bindings`}, which will be removed too.`
              : "It isn't used by any bindings."}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            variant="destructive"
            onClick={(e) => {
              e.preventDefault()
              if (action) remove.mutate(action.id)
            }}
          >
            Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
