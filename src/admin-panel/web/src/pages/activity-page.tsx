import { useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Trash2 } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"

import { ActivityFeed } from "@/components/activity-feed"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { api } from "@/lib/api"
import { queryKeys } from "@/lib/queries"
import type { ActivityEntry } from "@/lib/types"

const PAGE_SIZE = 100

const filters = [
  { value: "all", label: "All" },
  { value: "press", label: "Presses" },
  { value: "error", label: "Errors" },
  { value: "system", label: "System" },
]

export function ActivityPage() {
  const queryClient = useQueryClient()
  const [kind, setKind] = useState("all")

  const log = useInfiniteQuery({
    queryKey: [...queryKeys.activityLog, kind],
    queryFn: ({ pageParam }) => api.activity({ limit: PAGE_SIZE, before: pageParam, kind: kind === "all" ? undefined : kind }),
    initialPageParam: undefined as number | undefined,
    getNextPageParam: (lastPage) => (lastPage.length === PAGE_SIZE ? lastPage[lastPage.length - 1].id : undefined),
  })

  const clear = useMutation({
    mutationFn: api.clearActivity,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.activityLog })
      queryClient.setQueryData(queryKeys.activity, [])
      toast.success("Activity log cleared")
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const entries = log.data?.pages.flat() ?? []

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-xl font-semibold">Activity</h1>
          <p className="text-sm text-muted-foreground">Everything the box and panel have done, newest first.</p>
        </div>
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button variant="outline" disabled={entries.length === 0}>
              <Trash2 data-icon="inline-start" />
              Clear log
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Clear the activity log?</AlertDialogTitle>
              <AlertDialogDescription>This removes every entry. Your setup isn't affected.</AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction variant="destructive" onClick={() => clear.mutate()}>
                Clear log
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>

      <ToggleGroup
        type="single"
        variant="outline"
        size="sm"
        value={kind}
        // Clicking the selected filter again gives an empty value - keep the current filter instead
        onValueChange={(value) => value && setKind(value)}
        className="self-start"
      >
        {filters.map((filter) => (
          <ToggleGroupItem key={filter.value} value={filter.value}>
            {filter.label}
          </ToggleGroupItem>
        ))}
      </ToggleGroup>

      <Card>
        <CardContent>
          {log.isPending ? (
            <div className="flex flex-col gap-2">
              {[0, 1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-6" />
              ))}
            </div>
          ) : (
            <GroupedByDay entries={entries} />
          )}
          {log.hasNextPage && (
            <Button
              variant="ghost"
              className="mt-3 w-full"
              onClick={() => log.fetchNextPage()}
              disabled={log.isFetchingNextPage}
            >
              {log.isFetchingNextPage ? "Loading…" : "Load older entries"}
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function GroupedByDay({ entries }: { entries: ActivityEntry[] }) {
  if (entries.length === 0) return <ActivityFeed entries={[]} />

  const days = new Map<string, ActivityEntry[]>()
  for (const entry of entries) {
    const day = new Date(entry.timestamp).toLocaleDateString([], { weekday: "long", day: "numeric", month: "long" })
    days.set(day, [...(days.get(day) ?? []), entry])
  }

  return (
    <div className="flex flex-col gap-4">
      {[...days.entries()].map(([day, dayEntries]) => (
        <section key={day}>
          <h2 className="mb-1 text-xs font-medium tracking-wide text-muted-foreground uppercase">{day}</h2>
          <ActivityFeed entries={dayEntries} />
        </section>
      ))}
    </div>
  )
}
