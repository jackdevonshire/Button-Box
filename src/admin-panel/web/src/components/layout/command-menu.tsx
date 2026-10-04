import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Activity, Check, Gamepad2, Layers, LayoutGrid, Moon, Plug, Radar, Settings, Sun } from "lucide-react"
import { useTheme } from "next-themes"
import { useNavigate } from "react-router"
import { toast } from "sonner"

import { IntegrationIcon } from "@/components/integration-icon"
import {
  Command,
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command"
import { api } from "@/lib/api"
import { useConfigurations, useControls, useIntegrations, useStatus } from "@/lib/queries"

export function CommandMenu({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: status } = useStatus()
  const { data: configurations = [] } = useConfigurations()
  const { data: controls = [] } = useControls()
  const { data: integrations = [] } = useIntegrations()
  const { resolvedTheme, setTheme } = useTheme()

  const run = (action: () => void) => {
    onOpenChange(false)
    action()
  }

  const activate = useMutation({
    mutationFn: (id: number) => api.activateConfiguration(id),
    onSuccess: () => queryClient.invalidateQueries(),
    onError: (e: Error) => toast.error(e.message),
  })
  const findBox = useMutation({
    mutationFn: api.findBox,
    onSuccess: (status) => toast.success(`Found the box at ${status.buttonBoxIp}`),
    onError: (e: Error) => toast.error(e.message),
  })

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange} title="Search" description="Jump to a page, control or configuration">
      {/* CommandDialog doesn't include the cmdk root, which every item needs */}
      <Command>
        <CommandInput placeholder="Search pages, controls and configurations" />
        <CommandList>
          <CommandEmpty>Nothing matches.</CommandEmpty>
          <CommandGroup heading="Pages">
            <CommandItem onSelect={() => run(() => navigate("/"))}>
              <LayoutGrid />
              Panel
            </CommandItem>
            <CommandItem onSelect={() => run(() => navigate("/?view=joystick"))}>
            <Gamepad2 />
            Joystick mappings
          </CommandItem>
          <CommandItem onSelect={() => run(() => navigate("/configurations"))}>
              <Layers />
              Configurations
            </CommandItem>
            {integrations
              .filter((integration) => integration.actionEditor)
              .map((integration) => (
                <CommandItem
                  key={integration.id}
                  value={`${integration.name} actions`}
                  onSelect={() => run(() => navigate(`/actions/${integration.actionEditor}`))}
                >
                  <IntegrationIcon icon={integration.icon} />
                  {integration.name} actions
                </CommandItem>
              ))}
            <CommandItem onSelect={() => run(() => navigate("/activity"))}>
              <Activity />
              Activity
            </CommandItem>
            <CommandItem onSelect={() => run(() => navigate("/integrations"))}>
              <Plug />
              Integrations
            </CommandItem>
            <CommandItem onSelect={() => run(() => navigate("/settings"))}>
              <Settings />
              Settings
            </CommandItem>
            <CommandItem onSelect={() => run(() => setTheme(resolvedTheme === "dark" ? "light" : "dark"))}>
              {resolvedTheme === "dark" ? <Sun /> : <Moon />}
              Switch to {resolvedTheme === "dark" ? "light" : "dark"} mode
            </CommandItem>
            <CommandItem onSelect={() => run(() => findBox.mutate())}>
              <Radar />
              Find the box on my network
            </CommandItem>
          </CommandGroup>
          <CommandSeparator />
          <CommandGroup heading="Switch configuration">
            {configurations.map((configuration) => (
              <CommandItem
                key={configuration.id}
                value={`switch ${configuration.name}`}
                onSelect={() => run(() => activate.mutate(configuration.id))}
              >
                <Layers />
                {configuration.name}
                {status?.activeConfigurationId === configuration.id && <Check className="ml-auto" />}
              </CommandItem>
            ))}
          </CommandGroup>
          <CommandSeparator />
          <CommandGroup heading="Controls">
            {controls.map((control) => (
              <CommandItem
                key={control.id}
                value={`${control.label} ${control.id}`}
                onSelect={() => run(() => navigate(`/?control=${control.id}`))}
              >
                {control.label}
                <span className="ml-auto font-mono text-xs text-muted-foreground">{control.id}</span>
              </CommandItem>
            ))}
          </CommandGroup>
        </CommandList>
      </Command>
    </CommandDialog>
  )
}
