import { useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import { api, type SoundSettingsInput } from "@/lib/api"
import { queryKeys } from "@/lib/queries"

/** Saves sound settings, updating the page from the response */
export function useSoundSettings() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: SoundSettingsInput) => api.updateSoundSettings(input),
    onSuccess: (sound) => queryClient.setQueryData(queryKeys.sound, sound),
    onError: (e: Error) => {
      toast.error(e.message)
      queryClient.invalidateQueries({ queryKey: queryKeys.sound })
    },
  })
}
