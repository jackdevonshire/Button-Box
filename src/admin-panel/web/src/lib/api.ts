import type {
  Action,
  ActivityEntry,
  Binding,
  Configuration,
  Control,
  ControlEvent,
  Integration,
  JoystickMapping,
  JoystickSnapshot,
  RunningApp,
  Settings,
  SoundClip,
  SoundSettings,
  SoundSnapshot,
  Status,
} from "@/lib/types"

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  let response: Response
  try {
    // Forms (file uploads) are sent as they are, and the browser sets their content type
    const isForm = body instanceof FormData
    response = await fetch(`/api${path}`, {
      method,
      headers: body === undefined || isForm ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
    })
  } catch {
    throw new ApiError("Can't reach the panel server. Is it running?", 0)
  }

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new ApiError(data?.error ?? `Request failed (${response.status})`, response.status)
  }
  return data as T
}

const get = <T>(path: string) => request<T>("GET", path)
const post = <T>(path: string, body: unknown = {}) => request<T>("POST", path, body)
const patch = <T>(path: string, body: unknown) => request<T>("PATCH", path, body)
const del = <T>(path: string) => request<T>("DELETE", path)

export interface BindingInput {
  name?: string
  control?: string
  event?: ControlEvent
  actionId?: number
  modifiers?: string[]
  enabled?: boolean
}

export interface ActionInput {
  integrationId?: number
  name?: string
  description?: string
  configuration?: unknown
}

export type JoystickMappingInput = Partial<Omit<JoystickMapping, "id" | "configurationId">>

export interface ImportResult {
  backupPath: string
  configurations: number
  actions: number
}

export type SoundSettingsInput = Partial<Omit<SoundSettings, "pushToTalk">> & {
  pushToTalk?: Partial<SoundSettings["pushToTalk"]>
}

export type ClipInput = Partial<Pick<SoundClip, "name" | "volume" | "again">>

export interface ConfigurationInput {
  name?: string
  description?: string
  displayLines?: string[] | null
}

export const api = {
  status: () => get<Status>("/status"),
  controls: () => get<Control[]>("/controls"),
  findBox: () => post<Status>("/box/find"),
  previewDisplay: (lines: string[], seconds = 5) => post("/box/display", { lines, seconds }),
  startLearning: () => post<{ seconds: number }>("/learn"),

  configurations: () => get<Configuration[]>("/configurations"),
  configuration: (id: number) => get<Configuration>(`/configurations/${id}`),
  createConfiguration: (input: ConfigurationInput) => post<Configuration>("/configurations", input),
  updateConfiguration: (id: number, input: ConfigurationInput) =>
    patch<Configuration>(`/configurations/${id}`, input),
  deleteConfiguration: (id: number) => del(`/configurations/${id}`),
  activateConfiguration: (id: number) => post<Status>(`/configurations/${id}/activate`),
  duplicateConfiguration: (id: number) => post<Configuration>(`/configurations/${id}/duplicate`),

  createBinding: (configurationId: number, input: BindingInput) =>
    post<Binding>(`/configurations/${configurationId}/bindings`, input),
  updateBinding: (id: number, input: BindingInput) => patch<Binding>(`/bindings/${id}`, input),
  deleteBinding: (id: number) => del(`/bindings/${id}`),

  joystick: () => get<JoystickSnapshot>("/joystick"),
  createJoystickMapping: (configurationId: number, input: JoystickMappingInput) =>
    post<JoystickMapping>(`/configurations/${configurationId}/joystick-mappings`, input),
  updateJoystickMapping: (id: number, input: JoystickMappingInput) =>
    patch<JoystickMapping>(`/joystick-mappings/${id}`, input),
  deleteJoystickMapping: (id: number) => del(`/joystick-mappings/${id}`),

  integrations: () => get<Integration[]>("/integrations"),
  setIntegrationActive: (id: number, active: boolean) => patch<Integration>(`/integrations/${id}`, { active }),

  actions: () => get<Action[]>("/actions"),
  createAction: (input: ActionInput) => post<Action>("/actions", input),
  updateAction: (id: number, input: ActionInput) => patch<Action>(`/actions/${id}`, input),
  deleteAction: (id: number) => del<{ removedBindings: number }>(`/actions/${id}`),
  testAction: (id: number) => post(`/actions/${id}/test`),

  activity: (options: { limit?: number; before?: number; kind?: string } = {}) => {
    const params = new URLSearchParams()
    params.set("limit", String(options.limit ?? 50))
    if (options.before) params.set("before", String(options.before))
    if (options.kind) params.set("kind", options.kind)
    return get<ActivityEntry[]>(`/activity?${params}`)
  },
  clearActivity: () => del("/activity"),

  sound: () => get<SoundSnapshot>("/sound"),
  updateSoundSettings: (input: SoundSettingsInput) => patch<SoundSnapshot>("/sound/settings", input),
  setSoundListening: (listening: boolean) => post<SoundSnapshot>("/sound/listen", { listening }),
  soundApps: () => get<RunningApp[]>("/sound/apps"),
  uploadClips: (files: File[]) => {
    const form = new FormData()
    for (const file of files) form.append("files", file)
    return post<SoundClip[]>("/sound/clips", form)
  },
  updateClip: (id: number, input: ClipInput) => patch<SoundClip>(`/sound/clips/${id}`, input),
  deleteClip: (id: number) => del<{ removedBindings: number }>(`/sound/clips/${id}`),
  playClip: (id: number) => post<{ playing: boolean }>(`/sound/clips/${id}/play`),
  stopSounds: () => post("/sound/stop"),

  settings: () => get<Settings>("/settings"),
  updateSettings: (input: Partial<Pick<Settings, "buttonBoxIp" | "startWithWindows">>) =>
    patch<Settings>("/settings", input),
  openLog: () => post("/system/open-log"),
  importBackup: (backup: unknown) => post<ImportResult>("/import", backup),
}
