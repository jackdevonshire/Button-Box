import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { toast } from "sonner"

import { KeyboardEditor } from "@/components/actions/keyboard-editor"
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
import { Textarea } from "@/components/ui/textarea"
import { api } from "@/lib/api"
import type { Action, Integration, KeyStep } from "@/lib/types"

interface ActionDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  integration: Integration
  /** The action being edited, or undefined to create one */
  action?: Action
}

export function ActionDialog({ open, onOpenChange, integration, action }: ActionDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="sm:max-w-xl"
        onEscapeKeyDown={(event) => {
          // Esc is a key you can record, so don't close the dialog while the key recorder has focus
          if (document.activeElement?.closest("[data-key-recorder]")) event.preventDefault()
        }}
      >
        {/* Dialog content unmounts when closed, so the form starts fresh each time it opens */}
        <ActionForm integration={integration} action={action} onDone={() => onOpenChange(false)} />
      </DialogContent>
    </Dialog>
  )
}

const editorCopy = {
  keyboard: {
    title: "keyboard action",
    description: "Presses keys on this PC, as if you'd typed them.",
    placeholder: "Landing gear",
  },
  command: {
    title: "command",
    description: "Runs a command on this PC, like in the Run box or Command Prompt.",
    placeholder: "Open Spotify",
  },
  script: {
    title: "Python script",
    description: "Runs Python code on this PC.",
    placeholder: "Toggle smart lights",
  },
}

function ActionForm({ integration, action, onDone }: { integration: Integration; action?: Action; onDone: () => void }) {
  const queryClient = useQueryClient()
  const editor = integration.actionEditor ?? "command"
  const copy = editorCopy[editor]

  const [name, setName] = useState(action?.name ?? "")
  const [description, setDescription] = useState(action?.description ?? "")
  const [steps, setSteps] = useState<KeyStep[]>(editor === "keyboard" ? ((action?.configuration as KeyStep[]) ?? []) : [])
  const [text, setText] = useState(editor === "keyboard" ? "" : ((action?.configuration as string) ?? ""))
  const [error, setError] = useState<string | null>(null)

  const save = useMutation({
    mutationFn: () => {
      const input = { name, description, configuration: editor === "keyboard" ? steps : text }
      return action ? api.updateAction(action.id, input) : api.createAction({ ...input, integrationId: integration.id })
    },
    onSuccess: () => {
      queryClient.invalidateQueries()
      toast.success(action ? "Action saved" : "Action created")
      onDone()
    },
    onError: (e: Error) => setError(e.message),
  })

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return setError("Enter a name")
    if (editor === "keyboard" && steps.length === 0) return setError("Add at least one key")
    if (editor !== "keyboard" && !text.trim()) return setError(editor === "script" ? "Enter a script" : "Enter a command")
    save.mutate()
  }

  return (
    <form onSubmit={submit}>
      <DialogHeader>
        <DialogTitle>{action ? `Edit ${copy.title}` : `New ${copy.title}`}</DialogTitle>
        <DialogDescription>{copy.description}</DialogDescription>
      </DialogHeader>

      <FieldGroup className="py-4">
        <Field>
          <FieldLabel htmlFor="action-name">Name</FieldLabel>
          <Input
            id="action-name"
            value={name}
            onChange={(e) => {
              setName(e.target.value)
              setError(null)
            }}
            placeholder={copy.placeholder}
            autoFocus
          />
          <FieldDescription>Shown on the panel and on the box's screen when it runs.</FieldDescription>
        </Field>
        <Field>
          <FieldLabel htmlFor="action-description">Description</FieldLabel>
          <Input
            id="action-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Optional"
          />
        </Field>

        {editor === "keyboard" && (
          <Field>
            <FieldLabel>Keys</FieldLabel>
            <KeyboardEditor
              value={steps}
              onChange={(next) => {
                setSteps(next)
                setError(null)
              }}
              keys={integration.options?.keys ?? []}
              types={integration.options?.types ?? []}
            />
            <FieldDescription>
              Tapped keys are pressed together, so Ctrl and C make Ctrl + C. Use hold and release to keep a key down
              between presses - for example, hold W when a button is pressed and release it when it's let go.
            </FieldDescription>
          </Field>
        )}

        {editor === "command" && (
          <Field>
            <FieldLabel htmlFor="action-command">Command</FieldLabel>
            <Textarea
              id="action-command"
              value={text}
              onChange={(e) => {
                setText(e.target.value)
                setError(null)
              }}
              placeholder='start "" "C:\Program Files\Spotify\Spotify.exe"'
              rows={3}
              className="font-mono text-sm"
              spellCheck={false}
            />
            <FieldDescription>
              Runs in Command Prompt without waiting for it to finish. Apps it starts open as normal.
            </FieldDescription>
          </Field>
        )}

        {editor === "script" && (
          <Field>
            <FieldLabel htmlFor="action-script">Script</FieldLabel>
            <Textarea
              id="action-script"
              value={text}
              onChange={(e) => {
                setText(e.target.value)
                setError(null)
              }}
              onKeyDown={insertTabAsSpaces}
              placeholder={'import requests\nrequests.post("http://192.168.1.20/api/lights/toggle")'}
              rows={12}
              className="font-mono text-sm"
              spellCheck={false}
            />
            <FieldDescription>
              Runs in the background with the panel's Python. Scripts can use <code>action</code>,{" "}
              <code>display</code> (for example <code>display.display_temporary_message([...], 3)</code>) and{" "}
              <code>button_box</code>. Errors appear in the activity log.
            </FieldDescription>
          </Field>
        )}

        {error && <p className="text-sm text-destructive">{error}</p>}
      </FieldGroup>

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" disabled={save.isPending}>
          {action ? "Save" : "Create"}
        </Button>
      </DialogFooter>
    </form>
  )
}

/** Tab indents with four spaces in the script editor, instead of moving focus */
function insertTabAsSpaces(event: React.KeyboardEvent<HTMLTextAreaElement>) {
  if (event.key !== "Tab" || event.shiftKey) return
  event.preventDefault()
  const target = event.currentTarget
  const { selectionStart, selectionEnd } = target
  target.setRangeText("    ", selectionStart, selectionEnd, "end")
  target.dispatchEvent(new Event("input", { bubbles: true }))
}
