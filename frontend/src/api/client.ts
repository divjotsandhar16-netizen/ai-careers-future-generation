import type {
  AuthResponse,
  CareerPlan,
  ChatResult,
  EmotionResult,
  InterviewBatch,
  InterviewResult,
  PersonalityReport,
  ResumeIntelligence,
  ResumeResult,
  User,
} from "../types/career";

const apiHost = window.location.hostname || "localhost";
const API_URL = import.meta.env.VITE_API_URL ?? `http://${apiHost}:8010/api`;

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const isFormData = options?.body instanceof FormData;
  const token = localStorage.getItem("auth_token") ?? sessionStorage.getItem("auth_token");
  const response = await fetch(`${API_URL}${path}`, {
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options?.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    const detail = await response.text();
    try {
      const parsed = JSON.parse(detail) as { detail?: string };
      throw new Error(parsed.detail || "Request failed");
    } catch {
      throw new Error(detail || "Request failed");
    }
  }

  return response.json() as Promise<T>;
}

export const api = {
  captcha: () => request<{ captcha_id: string; question: string }>("/auth/captcha"),
  signup: (payload: unknown) => request<AuthResponse>("/auth/signup", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload: unknown) => request<AuthResponse>("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  googleAuth: (payload: unknown) => request<AuthResponse>("/auth/google", { method: "POST", body: JSON.stringify(payload) }),
  verifyOtp: (payload: unknown) => request<AuthResponse>("/auth/verify-otp", { method: "POST", body: JSON.stringify(payload) }),
  resendOtp: (payload: unknown) => request<{ message: string; dev_otp?: string }>("/auth/resend-otp", { method: "POST", body: JSON.stringify(payload) }),
  forgotPassword: (payload: unknown) => request<{ message: string; dev_otp?: string }>("/auth/forgot-password", { method: "POST", body: JSON.stringify(payload) }),
  resetPassword: (payload: unknown) => request<{ message: string }>("/auth/reset-password", { method: "POST", body: JSON.stringify(payload) }),
  me: () => request<User>("/auth/me"),
  createCareerPlan: (payload: unknown) =>
    request<CareerPlan>("/career/plan", { method: "POST", body: JSON.stringify(payload) }),
  listCareerPlans: () => request<CareerPlan[]>("/career/plans"),
  chat: (payload: unknown) => request<ChatResult>("/chat", { method: "POST", body: JSON.stringify(payload) }),
  analyzeResume: (payload: unknown) =>
    request<ResumeResult>("/resume/analyze", { method: "POST", body: JSON.stringify(payload) }),
  analyzeResumeFile: (payload: FormData) =>
    request<ResumeIntelligence>("/resume/intelligence", { method: "POST", headers: {}, body: payload }),
  getInterviewQuestion: (payload: unknown) =>
    request<{ question: string }>("/interview/question", { method: "POST", body: JSON.stringify(payload) }),
  getInterviewQuestions: (payload: unknown) =>
    request<InterviewBatch>("/interview/questions", { method: "POST", body: JSON.stringify(payload) }),
  evaluateInterview: (payload: unknown) =>
    request<InterviewResult>("/interview/evaluate", { method: "POST", body: JSON.stringify(payload) }),
  predictReadiness: (payload: unknown) =>
    request<{ readiness_score: number; label: string }>("/ml/readiness", { method: "POST", body: JSON.stringify(payload) }),
  analyzeEmotion: (payload: unknown) =>
    request<EmotionResult>("/intelligence/emotion", { method: "POST", body: JSON.stringify(payload) }),
  predictPersonality: (payload: unknown) =>
    request<PersonalityReport>("/intelligence/personality", { method: "POST", body: JSON.stringify(payload) }),
  emotionHistory: () => request<Array<EmotionResult & { created_at: string }>>("/intelligence/emotion/history"),
};
