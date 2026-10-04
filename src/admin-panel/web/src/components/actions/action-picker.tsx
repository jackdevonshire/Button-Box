import { Check, ChevronsUpDown } from "lucide-react"
import { useMemo, useState } from "react"

import { Button } from "@/components/ui/button"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { integrationIconById } from "@/lib/controls"
import type { Action } from "@/lib/types"
import { cn } from "@/lib/utils"

/** Searchable list of every action, grouped by integration */
export function ActionPicker({
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
