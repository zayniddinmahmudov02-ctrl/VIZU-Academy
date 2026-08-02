"use client";

import { useRouter } from "next/navigation";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import Button from "@/components/ui/button";
import Input from "@/components/ui/input";

import { useLogin } from "../hooks/use-login";
import { saveToken } from "@/lib/token";

import {
  loginSchema,
  LoginFormData,
} from "../validation/login.schema";

export default function LoginForm() {
  const router = useRouter();

  const loginMutation = useLogin();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  async function onSubmit(data: LoginFormData) {
    try {
      const response = await loginMutation.mutateAsync(data);

      saveToken(response.access_token);

      router.push("/dashboard");

    } catch (error) {
      console.warn("Login failed:", error);
      alert("Email yoki parol noto'g'ri.");
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
      <div>
        <label className="mb-2 block text-sm font-medium text-text-primary">Email</label>

        <Input type="email" placeholder="Email" error={!!errors.email} {...register("email")} />

        {errors.email && (
          <p className="mt-2 text-sm text-danger">{errors.email.message}</p>
        )}
      </div>

      <div>
        <label className="mb-2 block text-sm font-medium text-text-primary">Password</label>

        <Input
          type="password"
          placeholder="Password"
          error={!!errors.password}
          {...register("password")}
        />

        {errors.password && (
          <p className="mt-2 text-sm text-danger">{errors.password.message}</p>
        )}
      </div>

      <Button type="submit" fullWidth disabled={loginMutation.isPending}>
        {loginMutation.isPending ? "Signing in..." : "Login"}
      </Button>
    </form>
  );
}