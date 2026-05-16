export type CareerPlan = {
  id: number;
  name: string;
  current_role: string;
  target_role: string;
  skills: string[];
  readiness_score: number;
  roadmap: string[];
};

export type ResumeResult = {
  id: number;
  score: number;
  strengths: string[];
  gaps: string[];
  suggestions: string[];
};

export type JobMatch = {
  title: string;
  match_score: number;
  reason: string;
  missing_skills: string[];
};

export type DomainScore = {
  domain: string;
  score: number;
  confidence: string;
  evidence: string[];
  missing_keywords: string[];
};

export type ResumeIntelligence = {
  id: number;
  file_name: string;
  target_role: string;
  overall_score: number;
  ats_score: number;
  seniority_signal: string;
  detected_skills: string[];
  missing_skills: string[];
  nlp_keywords: string[];
  domain_ranking: DomainScore[];
  deep_learning_signal: number;
  job_matches: JobMatch[];
  resume_strengths: string[];
  priority_fixes: string[];
  rewritten_bullets: string[];
  project_recommendations: string[];
  interview_focus: string[];
  learning_plan: string[];
};

export type ChatResult = {
  answer: string;
  recommended_actions: string[];
};

export type InterviewResult = {
  id: number;
  score: number;
  feedback: string;
};

export type InterviewBatch = {
  domain: string;
  difficulty: string;
  questions: string[];
};

export type User = {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  is_email_verified: boolean;
  is_phone_verified: boolean;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: User;
  dev_otp?: string | null;
};

export type EmotionResult = {
  emotion: string;
  sentiment: string;
  tone: string;
  confidence: number;
  scores: Record<string, number>;
  source: string;
  recommendation: string;
};

export type PersonalityReport = {
  personality_type: string;
  communication_style: string;
  learning_style: string;
  career_matches: string[];
  best_work_environment: string;
  strengths: string[];
  weaknesses: string[];
  scores: Record<string, number>;
  report: string;
};
