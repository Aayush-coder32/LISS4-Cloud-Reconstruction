"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { login, register, setToken } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function handleSubmit() {
    setPending(true);
    setError(null);
    try {
      const response =
        mode === "login"
          ? await login(email, password)
          : await register({ email, full_name: fullName, password });
      setToken(response.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top,_rgba(255,159,28,0.22),_transparent_30%),linear-gradient(180deg,#08131f,#0d3342)] px-4">
      <Card className="w-full max-w-md">
        <p className="font-mono text-xs uppercase tracking-[0.35em] text-mint/80">GenCloudNet Access</p>
        <h1 className="mt-3 text-3xl font-bold">{mode === "login" ? "Mission control login" : "Create operator account"}</h1>
        <div className="mt-6 space-y-4">
          {mode === "register" ? <Input placeholder="Full name" value={fullName} onChange={(event) => setFullName(event.target.value)} /> : null}
          <Input placeholder="Email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
          <Input placeholder="Password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
          <Button className="w-full" onClick={handleSubmit} disabled={pending}>
            {pending ? "Processing..." : mode === "login" ? "Sign in" : "Create account"}
          </Button>
          {error ? <p className="text-sm text-red-300">{error}</p> : null}
          <button
            className="text-sm text-cloud/70 hover:text-white"
            onClick={() => setMode(mode === "login" ? "register" : "login")}
            type="button"
          >
            {mode === "login" ? "Need an account? Register" : "Already registered? Log in"}
          </button>
        </div>
      </Card>
    </div>
  );
}
