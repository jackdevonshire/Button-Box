import { useQuery } from "@tanstack/react-query"

import { api } from "@/lib/api"

export const queryKeys = {
  status: ["status"] as const,
  controls: ["controls"] as const,
  configurations: ["configurations"] as const,
  configuration: (id: number) => ["configurations", id] as const,
  actions: ["actions"] as const,
  integrations: ["integrations"] as const,
  activity: ["activity"] as const,
  activityLog: ["activity-log"] as const,
  settings: ["settings"] as const,
  joystick: ["joystick"] as const,
  sound: ["sound"] as const,
}

export const useStatus = () => useQuery({ queryKey: queryKeys.status, queryFn: api.status })

export const useControls = () =>
  useQuery({ queryKey: queryKeys.controls, queryFn: api.controls, staleTime: Infinity })

export const useConfigurations = () =>
  useQuery({ queryKey: queryKeys.configurations, queryFn: api.configurations })

export const useConfiguration = (id: number | undefined) =>
  useQuery({
    queryKey: queryKeys.configuration(id ?? 0),
    queryFn: () => api.configuration(id!),
    enabled: id !== undefined,
  })

export const useActions = () => useQuery({ queryKey: queryKeys.actions, queryFn: api.actions })

export const useIntegrations = () =>
  useQuery({ queryKey: queryKeys.integrations, queryFn: api.integrations })

export const useActivity = () =>
  useQuery({ queryKey: queryKeys.activity, queryFn: () => api.activity({ limit: 100 }) })

export const useSettings = () => useQuery({ queryKey: queryKeys.settings, queryFn: api.settings })

export const useJoystick = () => useQuery({ queryKey: queryKeys.joystick, queryFn: api.joystick })

export const useSound = () => useQuery({ queryKey: queryKeys.sound, queryFn: api.sound })
