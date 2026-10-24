/**
 * Maps browser keyboard events to the key names the Keyboard integration sends (PyDirectInput's names).
 * Uses `event.code` - the physical key - so the result doesn't depend on Shift or the keyboard layout.
 */
const codeToKey: Record<string, string> = {
  Escape: "esc",
  Backquote: "`",
  Minus: "-",
  Equal: "=",
  Backspace: "backspace",
  Tab: "tab",
  BracketLeft: "[",
  BracketRight: "]",
  Backslash: "\\",
  CapsLock: "capslock",
  Semicolon: ";",
  Quote: "'",
  Enter: "enter",
  ShiftLeft: "shiftleft",
  ShiftRight: "shiftright",
  Comma: ",",
  Period: ".",
  Slash: "/",
  ControlLeft: "ctrlleft",
  ControlRight: "ctrlright",
  MetaLeft: "winleft",
  MetaRight: "winright",
  AltLeft: "altleft",
  AltRight: "altright",
  Space: "space",
  ContextMenu: "apps",
  PrintScreen: "printscreen",
  ScrollLock: "scrolllock",
  Pause: "pause",
  Insert: "insert",
  Home: "home",
  PageUp: "pageup",
  Delete: "delete",
  End: "end",
  PageDown: "pagedown",
  ArrowUp: "up",
  ArrowDown: "down",
  ArrowLeft: "left",
  ArrowRight: "right",
  NumLock: "numlock",
  NumpadDivide: "divide",
  NumpadMultiply: "multiply",
  NumpadSubtract: "subtract",
  NumpadAdd: "add",
  NumpadDecimal: "decimal",
  NumpadEnter: "enter",
}

export function keyFromEvent(event: KeyboardEvent | React.KeyboardEvent): string | null {
  const { code } = event
  if (code in codeToKey) return codeToKey[code]
  if (/^Key[A-Z]$/.test(code)) return code.slice(3).toLowerCase()
  if (/^Digit[0-9]$/.test(code)) return code.slice(5)
  if (/^F([1-9]|1\d|2[0-4])$/.test(code)) return code.toLowerCase()
  if (/^Numpad[0-9]$/.test(code)) return `num${code.slice(6)}`
  return null
}

const keyLabels: Record<string, string> = {
  esc: "Esc",
  escape: "Esc",
  backspace: "Backspace",
  tab: "Tab",
  capslock: "Caps Lock",
  enter: "Enter",
  return: "Enter",
  shift: "Shift",
  shiftleft: "Left Shift",
  shiftright: "Right Shift",
  ctrl: "Ctrl",
  ctrlleft: "Left Ctrl",
  ctrlright: "Right Ctrl",
  win: "Win",
  winleft: "Left Win",
  winright: "Right Win",
  alt: "Alt",
  altleft: "Left Alt",
  altright: "Right Alt",
  space: "Space",
  " ": "Space",
  apps: "Menu",
  printscreen: "Print Screen",
  prntscrn: "Print Screen",
  prtsc: "Print Screen",
  prtscr: "Print Screen",
  scrolllock: "Scroll Lock",
  pause: "Pause",
  insert: "Insert",
  home: "Home",
  pageup: "Page Up",
  del: "Delete",
  delete: "Delete",
  end: "End",
  pagedown: "Page Down",
  up: "↑",
  down: "↓",
  left: "←",
  right: "→",
  numlock: "Num Lock",
  divide: "Num /",
  multiply: "Num *",
  subtract: "Num -",
  add: "Num +",
  decimal: "Num .",
}

const shortcutModifiers: Record<string, string> = {
  ctrl: "Ctrl", ctrlleft: "Ctrl", ctrlright: "Ctrl",
  shift: "Shift", shiftleft: "Shift", shiftright: "Shift",
  alt: "Alt", altleft: "Alt", altright: "Alt",
  win: "Win", winleft: "Win", winright: "Win",
}

/** A readable keyboard shortcut, e.g. ["ctrlleft", "num5"] -> "Ctrl+Num 5" */
export function shortcutLabel(keys: string[]) {
  return keys.map((key) => shortcutModifiers[key] ?? keyLabel(key)).join("+")
}

/** A readable name for a key, e.g. "ctrlleft" -> "Left Ctrl" */
export function keyLabel(key: string) {
  if (keyLabels[key]) return keyLabels[key]
  if (/^f\d+$/.test(key)) return key.toUpperCase()
  if (/^num\d$/.test(key)) return `Num ${key.slice(3)}`
  return key.length === 1 ? key.toUpperCase() : key
}
