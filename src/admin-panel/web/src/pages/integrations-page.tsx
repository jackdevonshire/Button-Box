import { useMutation, useQueryClient } from "@tanstack/react-query"
import { ArrowRight } from "lucide-react"
import { Link } from "react-router"
import { toast } from "sonner"

import { IntegrationIcon } from "@/components/integration-icon"
import { Button } from "@/components/ui/button"
import { Card, CardAction, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Switch } from "@/components/ui/switch"
import { api } from "@/lib/api"
import { useIntegrations } from "@/lib/queries"
import type { Integration } from "@/lib/types"

export function IntegrationsPage() {
  const { data: integrations } = useIntegrations()

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">Integrations</h1>
        <p className="text-sm text-muted-foreground">
          The kinds of action the box can run. Turn one off to stop its actions running without deleting them.
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        {integrations
          ? integrations.map((integration) => <IntegrationCard key={integration.id} integration={integration} />)
          : [0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-44 rounded-xl" />)}
      </div>
    </div>
  )
}

function IntegrationCard({ integration }: { integration: Integration }) {
  const queryClient = useQueryClient()

  const toggle = useMutation({
    mutationFn: (active: boolean) => api.setIntegrationActive(integration.id, active),
    onSuccess: (updated) => {
      queryClient.invalidateQueries()
      toast.success(`${updated.name} turned ${updated.active ? "on" : "off"}`)
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const count = integration.actionCount
  return (
    <Card>
      <CardHeader>
        <div className="mb-1 flex size-9 items-center justify-center rounded-lg bg-muted">
          <IntegrationIcon icon={integration.icon} className="size-4" />
        </div>
        <CardTitle>{integration.name}</CardTitle>
        <CardDescription>{integration.description}</CardDescription>
        <CardAction>
          <Switch
            checked={integration.active}
            onCheckedChange={(active) => toggle.mutate(active)}
            disabled={toggle.isPending}
            aria-label={`${integration.active ? "Turn off" : "Turn on"} ${integration.name}`}
          />
        </CardAction>
      </CardHeader>
      <CardContent className="text-sm text-muted-foreground">
        {integration.note ?? (count === 1 ? "1 action" : `${count} actions`)}
      </CardContent>
      {integration.actionEditor && (
        <CardFooter>
          <Button variant="outline" size="sm" asChild>
            <Link to={`/actions/${integration.actionEditor}`}>
              Manage actions
              <ArrowRight data-icon="inline-end" />
            </Link>
          </Button>
        </CardFooter>
      )}
    </Card>
  )
}
