import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Download, FileText, Radar, Upload } from "lucide-react"
import { useRef, useState } from "react"
import { toast } from "sonner"

import { ThemeToggleGroup } from "@/components/layout/theme-menu"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Field, FieldContent, FieldDescription, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { Switch } from "@/components/ui/switch"
import { api } from "@/lib/api"
import { useSettings, useStatus } from "@/lib/queries"
import type { Settings } from "@/lib/types"

export function SettingsPage() {
  const { data: settings } = useSettings()

  return (
    <div className="flex max-w-3xl flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">Settings</h1>
        <p className="text-sm text-muted-foreground">How the panel connects to the box and runs on this PC.</p>
      </div>
      {settings ? (
        <>
          <BoxSettings settings={settings} />
          <AppearanceSettings />
          <StartupSettings settings={settings} />
          <BackupSettings settings={settings} />
          <TroubleshootingSettings settings={settings} />
        </>
      ) : (
        [0, 1, 2].map((i) => <Skeleton key={i} className="h-40 rounded-xl" />)
      )}
    </div>
  )
}

function BoxSettings({ settings }: { settings: Settings }) {
  const queryClient = useQueryClient()
  const { data: status } = useStatus()
  const [ip, setIp] = useState(settings.buttonBoxIp)
  const [error, setError] = useState<string | null>(null)

  const save = useMutation({
    mutationFn: () => api.updateSettings({ buttonBoxIp: ip }),
    onSuccess: (updated) => {
      queryClient.setQueryData(["settings"], updated)
      queryClient.invalidateQueries({ queryKey: ["status"] })
      toast.success("Saved. Reconnecting to the box")
    },
    onError: (e: Error) => setError(e.message),
  })
  const find = useMutation({
    mutationFn: api.findBox,
    onSuccess: (found) => {
      setIp(found.buttonBoxIp)
      queryClient.invalidateQueries({ queryKey: ["settings"] })
      toast.success(`Found the box at ${found.buttonBoxIp}`)
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const connection = status?.scanning
    ? "Searching your network…"
    : status?.online
      ? `Online at ${status.buttonBoxIp}${status.latencyMs !== null ? ` (${status.latencyMs} ms)` : ""}`
      : "Not connected"

  return (
    <Card>
      <CardHeader>
        <CardTitle>Button box</CardTitle>
        <CardDescription>
          The panel finds the box by itself: it learns the address when you press a button and searches your network if
          the box goes quiet. You only need this if that doesn't work.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <form
          className="flex flex-wrap items-end gap-2"
          onSubmit={(e) => {
            e.preventDefault()
            setError(null)
            save.mutate()
          }}
        >
          <Field className="w-56" data-invalid={error ? true : undefined}>
            <FieldLabel htmlFor="box-ip">IP address</FieldLabel>
            <Input id="box-ip" value={ip} onChange={(e) => setIp(e.target.value)} placeholder="192.168.1.50" />
          </Field>
          <Button type="submit" variant="outline" disabled={save.isPending || ip === settings.buttonBoxIp}>
            Save
          </Button>
          <Button type="button" variant="outline" onClick={() => find.mutate()} disabled={find.isPending || status?.scanning}>
            <Radar data-icon="inline-start" />
            Find box
          </Button>
        </form>
        {error && <p className="-mt-2 text-sm text-destructive">{error}</p>}
        <p className="text-sm text-muted-foreground">{connection}</p>
      </CardContent>
    </Card>
  )
}

function AppearanceSettings() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Appearance</CardTitle>
        <CardDescription>System follows your Windows light or dark setting.</CardDescription>
      </CardHeader>
      <CardContent>
        <ThemeToggleGroup />
      </CardContent>
    </Card>
  )
}

function StartupSettings({ settings }: { settings: Settings }) {
  const queryClient = useQueryClient()
  const toggle = useMutation({
    mutationFn: (enabled: boolean) => api.updateSettings({ startWithWindows: enabled }),
    onSuccess: (updated) => queryClient.setQueryData(["settings"], updated),
    onError: (e: Error) => toast.error(e.message),
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle>Startup</CardTitle>
      </CardHeader>
      <CardContent>
        <Field orientation="horizontal">
          <FieldContent>
            <FieldLabel htmlFor="start-with-windows">Start with Windows</FieldLabel>
            <FieldDescription>
              Runs the panel in the system tray when you sign in, so the box works without opening anything.
            </FieldDescription>
          </FieldContent>
          <Switch
            id="start-with-windows"
            checked={settings.startWithWindows}
            onCheckedChange={(enabled) => toggle.mutate(enabled)}
            disabled={toggle.isPending}
          />
        </Field>
      </CardContent>
    </Card>
  )
}

function BackupSettings({ settings }: { settings: Settings }) {
  const queryClient = useQueryClient()
  const fileInput = useRef<HTMLInputElement>(null)
  const [pending, setPending] = useState<{ name: string; data: unknown; summary: string } | null>(null)

  const restore = useMutation({
    mutationFn: (data: unknown) => api.importBackup(data),
    onSuccess: (result) => {
      queryClient.invalidateQueries()
      setPending(null)
      toast.success(`Restored ${result.configurations} configurations and ${result.actions} actions`, {
        description: "Your previous setup was backed up first.",
      })
    },
    onError: (e: Error) => {
      setPending(null)
      toast.error(e.message)
    },
  })

  const readFile = async (file: File) => {
    try {
      const data = JSON.parse(await file.text())
      const configurations = Array.isArray(data?.configurations) ? data.configurations.length : 0
      const actions = Array.isArray(data?.actions) ? data.actions.length : 0
      setPending({
        name: file.name,
        data,
        summary: `${configurations} ${configurations === 1 ? "configuration" : "configurations"} and ${actions} ${actions === 1 ? "action" : "actions"}`,
      })
    } catch {
      toast.error("That file isn't a backup. Choose a .json file exported from the panel.")
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Backups</CardTitle>
        <CardDescription>
          Save everything you've set up - configurations, bindings, actions and integrations - to a file, or restore
          from one.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" asChild>
            <a href="/api/export" download>
              <Download data-icon="inline-start" />
              Export backup
            </a>
          </Button>
          <Button variant="outline" onClick={() => fileInput.current?.click()}>
            <Upload data-icon="inline-start" />
            Restore from file
          </Button>
          <input
            ref={fileInput}
            type="file"
            accept=".json,application/json"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) readFile(file)
              e.target.value = ""
            }}
          />
        </div>
        <p className="text-xs text-muted-foreground">
          Before restoring, your current setup is saved to <code className="break-all">{settings.backupDir}</code>.
        </p>
      </CardContent>

      <AlertDialog open={pending !== null} onOpenChange={(open) => !open && setPending(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Restore from {pending?.name}?</AlertDialogTitle>
            <AlertDialogDescription>
              This replaces your configurations, bindings and actions with the {pending?.summary} in the backup. Your
              current setup is saved first, so you can restore it if you need to.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={(e) => {
                e.preventDefault()
                if (pending) restore.mutate(pending.data)
              }}
              disabled={restore.isPending}
            >
              Restore
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  )
}

function TroubleshootingSettings({ settings }: { settings: Settings }) {
  const open = useMutation({ mutationFn: api.openLog, onError: (e: Error) => toast.error(e.message) })
  return (
    <Card>
      <CardHeader>
        <CardTitle>Troubleshooting</CardTitle>
        <CardDescription>
          The log has everything the panel has done, including full details of errors.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-wrap items-center gap-3">
        <Button variant="outline" onClick={() => open.mutate()}>
          <FileText data-icon="inline-start" />
          Open log file
        </Button>
        <code className="text-xs break-all text-muted-foreground">{settings.logPath}</code>
      </CardContent>
    </Card>
  )
}
