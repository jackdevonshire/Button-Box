export type ControlId = string
export type ControlKind = "button" | "toggle" | "protected"
export type ControlEvent = "on" | "off"

export interface Control {
  id: ControlId
  kind: ControlKind
  label: string
  row: number
  column: number
}

export interface Status {
  online: boolean
  latencyMs: number | null
  lastSeen: string | null
  lastEvent: string | null
  scanning: boolean
  buttonBoxIp: string
  activeConfigurationId: number
  states: Record<ControlId, ControlEvent>
  display: string[]
}

export interface Action {
  id: number
  integrationId: number
  integrationName: string
  name: string
  description: string
  configuration: unknown
  bindingCount: number
}

export interface Binding {
  id: number
  configurationId: number
  name: string
  control: ControlId
  event: ControlEvent
  modifiers: ControlId[]
  gesture: string
  enabled: boolean
  action: Action
}

export interface Configuration {
  id: number
  name: string
  description: string
  displayLines: string[]
  customDisplay: boolean
  active: boolean
  bindingCount?: number
  bindings?: Binding[]
  joystickMappingCount?: number
  joystickMappings?: JoystickMapping[]
}

export type HatDirection = "up" | "down" | "left" | "right"

export interface KeysOutput {
  keys: string[]
}

export interface ActionOutput {
  actionId: number
  when: "press" | "release"
}

export interface JoystickMapping {
  id: number
  configurationId: number
  name: string
  device: string
  inputType: "hat" | "button"
  input: string
  outputType: "keys" | "action"
  output: KeysOutput | ActionOutput
  enabled: boolean
}

export interface JoystickDevice {
  id: string
  name: string
  axes: number
  buttons: number
  hasHat: boolean
}

export interface JoystickDeviceState {
  hat: HatDirection[]
  buttons: number[]
  axes: Record<string, number>
}

export interface JoystickSnapshot {
  active?: boolean
  devices: JoystickDevice[]
  states: Record<string, JoystickDeviceState>
}

export interface Integration {
  id: number
  name: string
  description: string
  active: boolean
  icon: string
  actionEditor: "keyboard" | "command" | "script" | null
  userActions: boolean
  actionCount: number
  note?: string | null
  options?: {
    keys: string[]
    types: { value: string; label: string }[]
  }
}

export interface ActivityEntry {
  id: number
  timestamp: string
  kind: "press" | "action" | "error" | "system"
  title: string
  detail: string | null
  control: ControlId | null
  event: ControlEvent | null
}

export interface PressEvent {
  control: ControlId
  event: ControlEvent
  bindings: number[]
}

export interface Settings {
  buttonBoxIp: string
  startWithWindows: boolean
  panelUrl: string
  logPath: string
  backupDir: string
}

export interface KeyStep {
  key: string
  type: string
}

export interface PushToTalkSettings {
  enabled: boolean
  /** "key" holds the push-to-talk key, "gate" presses nothing and only lets your voice through while you talk */
  method: "key" | "gate"
  key: string
  onVoice: boolean
  onClips: boolean
  /** dB - louder than this counts as talking */
  threshold: number
  releaseMs: number
  micDelayMs: number
  /** Only hold the key while this app (e.g. "Wardogs.exe") is in front, or "" for any app */
  focusApp: string
}

export interface SoundSettings {
  micDevice: string | null
  gameDevice: string | null
  monitorDevice: string | null
  micVolume: number
  clipVolume: number
  /** Sounds in the game drop to this (of their volume) while you talk. 1 turns it off */
  duckVolume: number
  monitorVolume: number
  pushToTalk: PushToTalkSettings
}

export interface SoundDevice {
  name: string
  isCable: boolean
  isDefault: boolean
}

export type ClipAgain = "restart" | "stop" | "overlap"

export interface SoundClip extends Action {
  stopAll: boolean
  file?: string
  volume?: number
  again?: ClipAgain
  /** Seconds, or null if the file is missing */
  duration?: number | null
  /** Keyboard shortcut that plays it from any app, e.g. ["ctrlleft", "f1"] */
  hotkey?: string[] | null
  /** Why the shortcut isn't working, e.g. another app already uses it */
  hotkeyError?: string | null
}

export interface SoundLiveState {
  /** The mic's level in dB, or null when the mic isn't being listened to */
  level: number | null
  talking: boolean
  keyHeld: boolean
  /** How loud what comes out of the virtual cable is, in dB - what the game hears. Null when not sending to a cable */
  cableLevel: number | null
  /** Whether what the game hears is being played in your headphones */
  listening: boolean
  /** In mic gate mode, whether your voice is being let through */
  gateOpen: boolean
  focusOk: boolean
  playing: number[]
}

export interface SoundState extends SoundLiveState {
  running: Partial<Record<SoundStream, string>>
  errors: Partial<Record<SoundStream, string>>
}

export type SoundStream = "mic" | "game" | "monitor" | "listen"

export interface SoundSnapshot {
  active: boolean
  settings: SoundSettings
  devices: { inputs: SoundDevice[]; outputs: SoundDevice[] }
  clips: SoundClip[]
  /** Keys that can be used in shortcuts */
  hotkeyKeys: string[]
  state: SoundState
}

export interface RunningApp {
  exe: string
  title: string
}
