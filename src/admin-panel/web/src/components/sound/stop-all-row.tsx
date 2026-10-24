import { Settings2, Square } from "lucide-react"
import { useState } from "react"

import { ClipTriggers } from "@/components/sound/clip-triggers"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { controlLabel } from "@/lib/controls"
import { inputLabel } from "@/lib/joystick"
import { shortcutLabel } from "@/lib/keys"
import { useConfiguration, useControls, useStatus } from "@/lib/queries"
import type { ActionOutput, SoundClip } from "@/lib/types"

/** What stops every sound - a keyboard shortcut, box and joystick buttons - with a dialog to set them up */
export function StopAllRow({ clip }: { clip: SoundClip }) {
  const [open, setOpen] = useState(false)
  const { data: status } = useStatus()
  const { data: configuration } = useConfiguration(status?.activeConfigurationId)
  const { data: controls } = useControls()

  const triggers = [
    ...(clip.hotkey ? [shortcutLabel(clip.hotkey)] : []),
    ...(configuration?.bindings ?? [])
      .filter((binding) => binding.action.id === clip.id)
      .map((binding) => controlLabel(controls, binding.control)),
    ...(configuration?.joystickMappings ?? [])
      .filter((mapping) => mapping.outputType === "action" && (mapping.output as ActionOutput).actionId === clip.id)
      .map((mapping) => `Joystick ${inputLabel(mapping.inputType, mapping.input).toLowerCase()}`),
  ]

  return (
    <>
      <div className="flex w-full flex-wrap items-center gap-x-3 gap-y-2">
        <span className="flex items-center gap-2 text-sm whitespace-nowrap text-muted-foreground">
          <Square className="size-3.5" />
          Stop all sounds
        </span>
        <span className="flex min-w-0 flex-1 flex-wrap gap-1.5">
          {triggers.length > 0 ? (
            triggers.map((trigger) => (
              <Badge key={trigger} variant="secondary">
                {trigger}
              </Badge>
            ))
          ) : (
            <span className="text-sm whitespace-nowrap text-muted-foreground">Not set up</span>
          )}
        </span>
        <Button size="sm" variant="outline" onClick={() => setOpen(true)}>
          <Settings2 data-icon="inline-start" />
          Set up
        </Button>
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent
          className="max-h-[90vh] overflow-y-auto sm:max-w-lg"
          onEscapeKeyDown={(event) => {
            // Esc can be part of a shortcut, so don't close while recording one
            if (document.activeElement?.closest("[data-key-recorder]")) event.preventDefault()
          }}
        >
          <DialogHeader>
            <DialogTitle>Stop all sounds</DialogTitle>
            <DialogDescription>Stops every sound that's playing, from the keyboard, the box or the joystick.</DialogDescription>
          </DialogHeader>
          <ClipTriggers clip={clip} title="Stop them with" />
        </DialogContent>
      </Dialog>
    </>
  )
}
