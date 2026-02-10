"use client"

import { useState } from "react"
import { toast } from "sonner"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { PageHeader } from "@/components/layout/page-header"
import { useAuth } from "@/hooks/use-auth"
import { ROLES } from "@/lib/constants"
import { apiClient } from "@/lib/api-client"

export default function SettingsPage() {
  const { user } = useAuth()
  const [profileForm, setProfileForm] = useState({
    username: user?.username ?? "",
    email: user?.email ?? "",
  })
  const [passwordForm, setPasswordForm] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  })

  const handleProfileSave = async () => {
    try {
      await apiClient.put("/api/auth/me", profileForm)
      toast.success("Profile updated")
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Failed to update profile")
    }
  }

  const handlePasswordChange = async () => {
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      toast.error("Passwords do not match")
      return
    }
    try {
      await apiClient.put("/api/auth/me/password", {
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
      })
      toast.success("Password changed")
      setPasswordForm({ current_password: "", new_password: "", confirm_password: "" })
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Failed to change password")
    }
  }

  const roleInfo = user?.role ? ROLES[user.role as keyof typeof ROLES] : null

  return (
    <div className="space-y-6">
      <PageHeader title="Settings" breadcrumbs={[{ label: "Settings" }]} />

      <div className="mx-auto max-w-2xl space-y-6">
        {/* Profile */}
        <Card>
          <CardHeader>
            <CardTitle>Profile</CardTitle>
            <CardDescription>Manage your account information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Role</Label>
              <div className="mt-1">
                {roleInfo ? (
                  <Badge className={roleInfo.color}>{roleInfo.label}</Badge>
                ) : (
                  <Badge variant="outline">{user?.role ?? "unknown"}</Badge>
                )}
              </div>
            </div>
            <Separator />
            <div>
              <Label>Username</Label>
              <Input
                value={profileForm.username}
                onChange={(e) => setProfileForm({ ...profileForm, username: e.target.value })}
              />
            </div>
            <div>
              <Label>Email</Label>
              <Input
                type="email"
                value={profileForm.email}
                onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
              />
            </div>
            <Button onClick={handleProfileSave} disabled={!profileForm.username || !profileForm.email}>
              Save Changes
            </Button>
          </CardContent>
        </Card>

        {/* Password */}
        <Card>
          <CardHeader>
            <CardTitle>Change Password</CardTitle>
            <CardDescription>Update your password</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Current Password</Label>
              <Input
                type="password"
                value={passwordForm.current_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
              />
            </div>
            <div>
              <Label>New Password</Label>
              <Input
                type="password"
                value={passwordForm.new_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
              />
            </div>
            <div>
              <Label>Confirm New Password</Label>
              <Input
                type="password"
                value={passwordForm.confirm_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
              />
            </div>
            <Button
              onClick={handlePasswordChange}
              disabled={!passwordForm.current_password || !passwordForm.new_password || !passwordForm.confirm_password}
            >
              Change Password
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
