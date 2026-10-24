import { useMutation, useQueryClient } from "@tanstack/react-query"
import { X } from "lucide-react"
import { toast } from "sonner"

import { KeySlot } from "@/components/actions/key-slot"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { api } from "@/lib/api"
import { outputSummary } from "@/lib/joystick"
import { useActions, useIntegrations } from "@/lib/queries"
import type { JoystickDevice, JoystickMapping, KeysOutput } from "@/lib/types"
import { cn } from "@/lib/utils"

/**
 * Turns joystick buttons into keyboard keys, one row per button: click a button's slot and press a key (or a
 * combination). Buttons left alone go straight to the game, to be bound there.
 */
export function ButtonKeysCard({
  configurationId,
  device,
  mappings,
  held,
}: {
  configurationId: number
  device: JoystickDevice
  mappings: JoystickMapping[]
  held: number[]
}) {
  const buttons = Array.from({ length: device.buttons }, (_, i) => i + 1)
  if (buttons.length === 0) return null

  return (
    <Card size="sm">
      <CardHeader>
        <CardTitle>Buttons to keys</CardTitle>
        <CardDescription>
          Give a button a key and it presses that key for as long as it's held. Buttons left on "In game" go straight to
          the game to bind there. The game still sees buttons you give a key, so leave those unbound in game.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="grid gap-1.5 sm:grid-cols-2 xl:grid-cols-3">
          {buttons.map((button) => {
            const buttonMappings = mappings.filter((m) => m.inputType === "button" && m.input === String(button))
            return (
              <ButtonKeyRow
                key={button}
                configurationId={configurationId}
                device={device}
                button={button}
                held={held.includes(button)}
                keysMapping={buttonMappings.find((m) => m.outputType === "keys")}
                others={buttonMappings.filter((m) => m.outputType !== "keys")}
              />
            )
          })}
        </ul>
      </CardContent>
    </Card>
  )
}

function ButtonKeyRow({
  configurationId,
  device,
  button,
  held,
  keysMapping,
  others,
}: {
  configurationId: number
  device: JoystickDevice
  button: number
  held: boolean
  keysMapping?: JoystickMapping
  others: JoystickMapping[]
}) {
  const queryClient = useQueryClient()
  const { data: actions = [] } = useActions()
  const { data: integrations = [] } = useIntegrations()
  const supported = new Set(integrations.find((i) => i.actionEditor === "keyboard")?.options?.keys ?? [])

  const keys = keysMapping ? (keysMapping.output as KeysOutput).keys : []

  const save = useMutation({
    mutationFn: (next: string[]) => {
      if (next.length === 0) return keysMapping ? api.deleteJoystickMapping(keysMapping.id) : Promise.resolve()
      const output = { keys: next }
      return keysMapping
        ? api.updateJoystickMapping(keysMapping.id, { output, enabled: true })
        : api.createJoystickMapping(configurationId, {
            name: "",
            device: device.id,
            inputType: "button",
            input: String(button),
            outputType: "keys",
            output,
            enabled: true,
          })
    },
    onSuccess: () => queryClient.invalidateQueries(),
    onError: (e: Error) => toast.error(e.message),
  })

  return (
    <li
      className={cn(
        "flex h-10 items-center gap-2 rounded-lg border px-1.5",
        keysMapping && !keysMapping.enabled && "opacity-60"
      )}
    >
      <span
        className={cn(
          "flex h-7 w-8 shrink-0 items-center justify-center rounded-md border bg-muted/40 text-xs tabular-nums transition-colors",
          held && "border-emerald-500 bg-emerald-500/20 text-emerald-700 dark:text-emerald-300"
        )}
        aria-label={`Button ${button}${held ? ", held" : ""}`}
      >
        {button}
      </span>
      <KeySlot
        label={`Key for button ${button}`}
        keys={keys}
        supported={supported}
        placeholder={others.length > 0 ? outputSummary(others[0], actions) : "In game"}
        onRecord={(next) => save.mutate(next)}
      />
      {keys.length > 0 && (
        <Button
          size="icon-xs"
          variant="ghost"
          aria-label={`Send button ${button} to the game instead`}
          onClick={() => save.mutate([])}
          disabled={save.isPending}
        >
          <X />
        </Button>
      )}
    </li>
  )
}
