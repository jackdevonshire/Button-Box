import type { LucideProps } from "lucide-react"
import { createElement } from "react"

import { integrationIcon } from "@/lib/controls"

/** An integration's icon. The icon components are fixed, so this just picks which one to render */
export function IntegrationIcon({ icon, ...props }: { icon: string | undefined } & LucideProps) {
  return createElement(integrationIcon(icon), props)
}
