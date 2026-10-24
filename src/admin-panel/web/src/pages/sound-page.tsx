import { useMutation, useQueryClient } from "@tanstack/react-query"
import { PowerOff } from "lucide-react"
import { toast } from "sonner"

import { DevicesCard } from "@/components/sound/devices-card"
import { PushToTalkCard } from "@/components/sound/push-to-talk-card"
import { SoundboardCard } from "@/components/sound/soundboard-card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"
import { useSound } from "@/lib/queries"

export function SoundPage() {
  const { data: sound } = useSound()

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">Sound</h1>
        <p className="text-sm text-muted-foreground">
          Play sounds into the game alongside your voice, and press push-to-talk for you when you speak.
        </p>
      </div>

      {!sound ? (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_400px]">
          <Skeleton className="h-96 rounded-xl" />
          <Skeleton className="h-96 rounded-xl" />
        </div>
      ) : (
        <>
          {!sound.active && <InactiveNotice />}
          <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_400px]">
            <div className="flex min-w-0 flex-col gap-4">
              <SoundboardCard sound={sound} />
              <DevicesCard sound={sound} />
            </div>
            <div className="lg:sticky lg:top-4">
              <PushToTalkCard sound={sound} />
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function InactiveNotice() {
  const queryClient = useQueryClient()
  const enable = useMutation({
    mutationFn: () => api.setIntegrationActive(6, true),
    onSuccess: () => {
      queryClient.invalidateQueries()
      toast.success("Sound turned on")
    },
    onError: (e: Error) => toast.error(e.message),
  })
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm">
      <PowerOff className="size-4 text-amber-600 dark:text-amber-400" />
      <p className="flex-1">Sound is turned off, so nothing plays and push-to-talk won't press anything.</p>
      <Button size="sm" variant="outline" onClick={() => enable.mutate()} disabled={enable.isPending}>
        Turn on
      </Button>
    </div>
  )
}
