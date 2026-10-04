import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Search } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Kbd } from "@/components/ui/kbd"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { api } from "@/lib/api"
import { useLive } from "@/lib/live"
import { useConfigurations, useStatus } from "@/lib/queries"
import type { Status } from "@/lib/types"
import { cn } from "@/lib/utils"

export function SiteHeader({ onSearch }: { onSearch: () => void }) {
  const queryClient = useQueryClient()
  const { data: status } = useStatus()
  const { data: configurations = [] } = useConfigurations()

  const activate = useMutation({
    mutationFn: (id: number) => api.activateConfiguration(id),
    onSuccess: (status) => {
      queryClient.setQueryData(["status"], status)
      queryClient.invalidateQueries()
    },
    onError: (e: Error) => toast.error(e.message),
  })

  return (
    <header className="sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b bg-background/80 px-4 backdrop-blur">
      <SidebarTrigger className="-ml-1" />
      <Separator orientation="vertical" className="mr-1 data-[orientation=vertical]:h-4" />

      {status && configurations.length > 0 && (
        <Select
          value={String(status.activeConfigurationId)}
          onValueChange={(value) => activate.mutate(Number(value))}
        >
          <SelectTrigger size="sm" className="w-full max-w-56 min-w-0 flex-1" aria-label="Active configuration">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {configurations.map((configuration) => (
              <SelectItem key={configuration.id} value={String(configuration.id)}>
                {configuration.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      <div className="ml-auto flex shrink-0 items-center gap-2">
        <BoxStatus status={status} />
        <Button variant="outline" size="sm" onClick={onSearch} className="text-muted-foreground">
          <Search data-icon="inline-start" />
          <span className="hidden lg:inline">Search</span>
          <Kbd className="hidden lg:inline-flex">Ctrl K</Kbd>
        </Button>
      </div>
    </header>
  )
}

function BoxStatus({ status }: { status: Status | undefined }) {
  const { connected } = useLive()

  let label = "Connecting…"
  let extra = ""
  let tone = "bg-muted-foreground"
  let detail = "Waiting for the panel server"
  if (status && !connected) {
    label = "Server offline"
    tone = "bg-destructive"
    detail = "Lost connection to the panel server. Retrying…"
  } else if (status?.scanning) {
    label = "Searching…"
    tone = "bg-amber-500 animate-pulse"
    detail = "Looking for the box on your network"
  } else if (status?.online) {
    label = "Online"
    extra = status.latencyMs !== null ? ` · ${status.latencyMs} ms` : ""
    tone = "bg-emerald-500"
    detail = `Button box at ${status.buttonBoxIp}`
  } else if (status) {
    label = "Box offline"
    tone = "bg-amber-500"
    detail = status.buttonBoxIp ? `Not responding at ${status.buttonBoxIp}` : "The box hasn't been found yet"
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className="flex items-center gap-2 rounded-full border px-2.5 py-1 text-xs text-muted-foreground" tabIndex={0}>
          <span className={cn("size-2 rounded-full", tone)} />
          <span className="whitespace-nowrap">
            {label}
            <span className="hidden xl:inline">{extra}</span>
          </span>
        </span>
      </TooltipTrigger>
      <TooltipContent>{detail}</TooltipContent>
    </Tooltip>
  )
}
