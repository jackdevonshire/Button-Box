import { useEffect, useState } from "react"
import { BrowserRouter, Outlet, Route, Routes } from "react-router"

import { AppSidebar } from "@/components/layout/app-sidebar"
import { CommandMenu } from "@/components/layout/command-menu"
import { SiteHeader } from "@/components/layout/site-header"
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar"
import { ConfigurationsPage } from "@/pages/configurations-page"
import { PanelPage } from "@/pages/panel-page"

function Layout() {
  const [searchOpen, setSearchOpen] = useState(false)

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key.toLowerCase() === "k" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault()
        setSearchOpen((open) => !open)
      }
    }
    document.addEventListener("keydown", onKeyDown)
    return () => document.removeEventListener("keydown", onKeyDown)
  }, [])

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="min-w-0">
        <SiteHeader onSearch={() => setSearchOpen(true)} />
        <main className="mx-auto w-full max-w-7xl flex-1 p-4 md:p-6">
          <Outlet />
        </main>
      </SidebarInset>
      <CommandMenu open={searchOpen} onOpenChange={setSearchOpen} />
    </SidebarProvider>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<PanelPage />} />
          <Route path="configurations" element={<ConfigurationsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
