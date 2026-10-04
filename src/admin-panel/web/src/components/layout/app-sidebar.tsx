import { ExternalLink, Gamepad2, Layers, LayoutGrid, Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"
import { NavLink, useMatch } from "react-router"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar"
import { integrationIcon } from "@/lib/controls"
import { useIntegrations } from "@/lib/queries"

// Action editors haven't moved to the new UI yet, so these open the original pages
const legacyActionPages: Record<string, string> = {
  keyboard: "/integration/keyboard/",
  command: "/integration/command/",
  script: "/integration/script/",
}

export function AppSidebar() {
  const { data: integrations = [] } = useIntegrations()
  const { resolvedTheme, setTheme } = useTheme()
  const editable = integrations.filter((integration) => integration.actionEditor && integration.active)

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <NavLink to="/">
                <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                  <Gamepad2 className="size-4" />
                </div>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-semibold">Button Box</span>
                  <span className="truncate text-xs text-muted-foreground">Admin panel</span>
                </div>
              </NavLink>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              <NavItem to="/" label="Panel" icon={LayoutGrid} end />
              <NavItem to="/configurations" label="Configurations" icon={Layers} />
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {editable.length > 0 && (
          <SidebarGroup>
            <SidebarGroupLabel>Actions</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {editable.map((integration) => {
                  const Icon = integrationIcon(integration.icon)
                  return (
                    <SidebarMenuItem key={integration.id}>
                      <SidebarMenuButton asChild tooltip={integration.name}>
                        <a href={legacyActionPages[integration.actionEditor!]}>
                          <Icon />
                          <span>{integration.name}</span>
                          <ExternalLink className="ml-auto size-3 text-muted-foreground" />
                        </a>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  )
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        )}
      </SidebarContent>

      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              tooltip="Toggle theme"
              onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
            >
              {resolvedTheme === "dark" ? <Sun /> : <Moon />}
              <span>{resolvedTheme === "dark" ? "Light mode" : "Dark mode"}</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}

function NavItem({ to, label, icon: Icon, end }: { to: string; label: string; icon: typeof Layers; end?: boolean }) {
  const isActive = useMatch({ path: to, end: end ?? false }) !== null
  return (
    <SidebarMenuItem>
      <SidebarMenuButton isActive={isActive} tooltip={label} asChild>
        <NavLink to={to} end={end}>
          <Icon />
          <span>{label}</span>
        </NavLink>
      </SidebarMenuButton>
    </SidebarMenuItem>
  )
}
