import { keyLabel } from "@/lib/keys"
import type {
  Action,
  ActionOutput,
  HatDirection,
  JoystickMapping,
  KeysOutput,
} from "@/lib/types"

export const hatDirections: HatDirection[] = ["up", "down", "left", "right"]

/** A stable key for an input, e.g. "hat:up" or "button:3" */
export const inputKey = (inputType: string, input: string) => `${inputType}:${input}`

export function inputLabel(inputType: string, input: string) {
  return inputType === "hat" ? `Hat ${input}` : `Button ${input}`
}

export function outputSummary(mapping: JoystickMapping, actions: Action[]) {
  if (mapping.outputType === "keys") {
    return `Hold ${(mapping.output as KeysOutput).keys.map(keyLabel).join(" + ")}`
  }
  const output = mapping.output as ActionOutput
  const action = actions.find((a) => a.id === output.actionId)
  return `Run ${action?.name ?? "a deleted action"}${output.when === "release" ? " on release" : ""}`
}

export function mappingTitle(mapping: JoystickMapping, actions: Action[]) {
  return mapping.name || outputSummary(mapping, actions)
}
