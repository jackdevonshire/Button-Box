import { Activity, Gamepad2, Layers, LayoutGrid, Moon, Plug, Settings, Sun } from "lucide-react"
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
                {editable.map((integration) => (
                  <NavItem
                    key={integration.id}
                    to={`/actions/${integration.actionEditor}`}
                    label={integration.name}
                    icon={integrationIcon(integration.icon)}
                  />
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        )}

        <SidebarGroup>
          <SidebarGroupLabel>System</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              <NavItem to="/activity" label="Activity" icon={Activity} />
              <NavItem to="/integrations" label="Integrations" icon={Plug} />
              <NavItem to="/settings" label="Settings" icon={Settings} />
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
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
