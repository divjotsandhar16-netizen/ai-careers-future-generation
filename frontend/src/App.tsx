import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  ArrowUpRight,
  Bell,
  Bot,
  BrainCircuit,
  BriefcaseBusiness,
  CalendarCheck,
  CheckCircle2,
  ClipboardList,
  Lock,
  Flame,
  FileText,
  Gauge,
  Layers3,
  Loader2,
  MessageSquareText,
  Mic,
  PanelsTopLeft,
  Route,
  Send,
  ShieldCheck,
  Sparkles,
  Sun,
  Target,
  Trophy,
  Upload,
  UserCircle,
  WandSparkles,
  Wifi,
  WifiOff,
} from "lucide-react";
import { motion } from "framer-motion";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { api } from "./api/client";
import { ScoreRing } from "./components/ScoreRing";
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
} from "./types/career";

type Tab = "dashboard" | "plan" | "chat" | "resume" | "interview" | "personality" | "ml";
type LiveStatus = "connecting" | "connected" | "offline";
type LiveEvent = {
  type: string;
  title: string;
  detail: string;
  score: number | null;
  created_at: string;
};
type CoachMessage = {
  role: "user" | "assistant";
  content: string;
};
type CoachMode = "local" | "gpt" | "openrouter";

const tabs: Array<{ id: Tab; label: string; icon: typeof Route }> = [
  { id: "dashboard", label: "Dashboard", icon: PanelsTopLeft },
  { id: "plan", label: "Plan", icon: Route },
  { id: "chat", label: "Chat", icon: Bot },
  { id: "resume", label: "Resume", icon: FileText },
  { id: "interview", label: "Interview", icon: Mic },
  { id: "personality", label: "Personality", icon: UserCircle },
  { id: "ml", label: "ML Score", icon: BrainCircuit },
];

const sampleResume =
  "Built a React dashboard and Python API for career analytics. Improved load time by 35%. Created SQL reports, deployed a portfolio project, and presented outcomes to users.";

const quickPrompts = [
  "Make me a 30 day roadmap",
  "Improve my resume bullets",
  "Prepare me for interview",
  "Find my biggest career gap",
];

const focusAreas = ["Resume proof", "Portfolio depth", "Mock interviews", "Applications", "Networking"];
const backendHost = window.location.hostname || "localhost";
const backendWsUrl = `${window.location.protocol === "https:" ? "wss" : "ws"}://${backendHost}:8010`;
const interviewDomains = [
  "AI / Machine Learning",
  "Data Science / Analytics",
  "Backend Engineering",
  "Frontend Engineering",
  "Full Stack Product Engineering",
  "Cloud / DevOps",
  "Behavioral / HR",
];
const defaultEvents: LiveEvent[] = [
  {
    type: "system",
    title: "Workspace initialized",
    detail: "Realtime career intelligence is ready to connect.",
    score: null,
    created_at: new Date().toISOString(),
  },
];
const defaultCoachMessages: CoachMessage[] = [
  {
    role: "assistant",
    content:
      "Hi. I am your realtime AI career coach. Upload a resume, generate a plan, or ask me to rewrite bullets, create a roadmap, or run a mock interview.",
  },
];

function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>("dashboard");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [plans, setPlans] = useState<CareerPlan[]>([]);
  const [plan, setPlan] = useState<CareerPlan | null>(null);
  const [chat, setChat] = useState<ChatResult | null>(null);
  const [coachMessages, setCoachMessages] = useState<CoachMessage[]>(defaultCoachMessages);
  const [coachStreaming, setCoachStreaming] = useState(false);
  const [coachMode, setCoachMode] = useState<CoachMode>("local");
  const [lastEmotion, setLastEmotion] = useState<EmotionResult | null>(null);
  const [emotionHistory, setEmotionHistory] = useState<Array<EmotionResult & { created_at: string }>>([]);
  const [personalityReport, setPersonalityReport] = useState<PersonalityReport | null>(null);
  const [resumeResult, setResumeResult] = useState<ResumeResult | null>(null);
  const [resumeIntelligence, setResumeIntelligence] = useState<ResumeIntelligence | null>(null);
  const [question, setQuestion] = useState("");
  const [interviewBatch, setInterviewBatch] = useState<InterviewBatch | null>(null);
  const [interviewResult, setInterviewResult] = useState<InterviewResult | null>(null);
  const [mlResult, setMlResult] = useState<{ readiness_score: number; label: string } | null>(null);
  const [liveStatus, setLiveStatus] = useState<LiveStatus>("connecting");
  const [liveEvents, setLiveEvents] = useState<LiveEvent[]>(defaultEvents);
  const chatSocketRef = useRef<WebSocket | null>(null);

  const latestScore = useMemo(() => plan?.readiness_score ?? mlResult?.readiness_score ?? 68, [plan, mlResult]);
  const resumeScore = resumeResult?.score ?? 62;
  const interviewScore = interviewResult?.score ?? 58;
  const overallScore = Math.round((latestScore + resumeScore + interviewScore) / 3);
  const readinessLabel = overallScore >= 78 ? "Launch ready" : overallScore >= 60 ? "Building momentum" : "Foundation mode";
  const activeTarget = plan?.target_role ?? "AI Engineer";
  const completedRoadmapItems = plan ? Math.max(1, Math.floor(plan.roadmap.length * (latestScore / 100))) : 2;
  const roadmapProgress = plan ? Math.round((completedRoadmapItems / plan.roadmap.length) * 100) : 38;
  const liveScore = liveEvents.find((event) => typeof event.score === "number")?.score;
  const emotionChart = Object.entries(lastEmotion?.scores ?? { motivated: 0.4, happy: 0.25, confused: 0.15, anxious: 0.1 }).map(
    ([name, score]) => ({ name, score: Math.round(score * 100) }),
  );

  useEffect(() => {
    api.me()
      .then(setCurrentUser)
      .catch(() => undefined)
      .finally(() => setAuthReady(true));
  }, []);

  useEffect(() => {
    api.listCareerPlans().then(setPlans).catch(() => undefined);
  }, []);

  useEffect(() => {
    let reconnectTimer = 0;
    let socket: WebSocket | null = null;

    function connect() {
      setLiveStatus("connecting");
      socket = new WebSocket(`${backendWsUrl}/ws/live`);
      socket.onopen = () => setLiveStatus("connected");
      socket.onmessage = (message) => {
        const event = JSON.parse(message.data) as LiveEvent;
        setLiveEvents((current) => [event, ...current].slice(0, 12));
      };
      socket.onerror = () => setLiveStatus("offline");
      socket.onclose = () => {
        setLiveStatus("offline");
        reconnectTimer = window.setTimeout(connect, 2500);
      };
    }

    connect();
    return () => {
      window.clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, []);

  async function run<T>(job: () => Promise<T>, onSuccess: (value: T) => void) {
    setLoading(true);
    setError("");
    try {
      const value = await job();
      onSuccess(value);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  function createPlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const skills = String(data.get("skills") ?? "")
      .split(",")
      .map((skill) => skill.trim())
      .filter(Boolean);
    run(
      () =>
        api.createCareerPlan({
          name: data.get("name"),
          current_role: data.get("current_role"),
          target_role: data.get("target_role"),
          skills,
          experience_years: Number(data.get("experience_years")),
          projects_count: Number(data.get("projects_count")),
          interview_confidence: Number(data.get("interview_confidence")),
        }),
      (value) => {
        setPlan(value);
        setPlans((current) => [value, ...current]);
      },
    );
  }

  function askChat(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const message = String(data.get("message") ?? "").trim();
    const targetRole = String(data.get("target_role") ?? activeTarget).trim();
    if (!message || coachStreaming) return;

    const userMessage: CoachMessage = { role: "user", content: message };
    const assistantMessage: CoachMessage = { role: "assistant", content: "" };
    const nextMessages = [...coachMessages, userMessage, assistantMessage];
    setCoachMessages(nextMessages);
    setCoachStreaming(true);
    setChat(null);
    (event.currentTarget.elements.namedItem("message") as HTMLTextAreaElement | null)?.form?.reset();

    chatSocketRef.current?.close();
    const socket = new WebSocket(`${backendWsUrl}/ws/chat`);
    chatSocketRef.current = socket;
    socket.onopen = () => {
      socket.send(
        JSON.stringify({
          message,
          target_role: targetRole,
          history: coachMessages.slice(-8),
          context: {
            activeTarget,
            careerScore: latestScore,
            resumeScore,
            interviewScore,
            skills: plan?.skills ?? [],
            resumeReport: resumeIntelligence,
          },
        }),
      );
    };
    socket.onmessage = (incoming) => {
      const eventData = JSON.parse(incoming.data) as { type: string; content?: string; mode?: CoachMode };
      if (eventData.type === "emotion") {
        const emotionPayload = (JSON.parse(incoming.data) as { emotion: EmotionResult }).emotion;
        setLastEmotion(emotionPayload);
        setEmotionHistory((current) => [{ ...emotionPayload, created_at: new Date().toISOString() }, ...current].slice(0, 20));
      }
      if (eventData.type === "delta") {
        setCoachMessages((current) => {
          const copy = [...current];
          const last = copy[copy.length - 1];
          copy[copy.length - 1] = { ...last, content: `${last.content}${eventData.content ?? ""}` };
          return copy;
        });
      }
      if (eventData.type === "meta") {
        setCoachMode(eventData.mode ?? "local");
      }
      if (eventData.type === "done") {
        setCoachStreaming(false);
        socket.close();
      }
    };
    socket.onerror = () => {
      setCoachStreaming(false);
      setError("Streaming coach connection failed. Make sure the backend is running on port 8010.");
    };
  }

  function logout() {
    localStorage.removeItem("auth_token");
    sessionStorage.removeItem("auth_token");
    setCurrentUser(null);
  }

  function handleAuthSuccess(response: AuthResponse, remember = false) {
    const storage = remember ? localStorage : sessionStorage;
    storage.setItem("auth_token", response.access_token);
    setCurrentUser(response.user);
  }

  function analyzeResume(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    run(
      () => api.analyzeResume({ resume_text: data.get("resume_text"), target_role: data.get("target_role") }),
      setResumeResult,
    );
  }

  function analyzeResumeFile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    run(
      () => api.analyzeResumeFile(data),
      (value) => {
        setResumeIntelligence(value);
        setResumeResult({
          id: value.id,
          score: value.overall_score,
          strengths: value.resume_strengths,
          gaps: value.missing_skills.map((skill) => `Missing or weak signal: ${skill}.`),
          suggestions: value.priority_fixes,
        });
      },
    );
  }

  function generateQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    run(
      () => api.getInterviewQuestion({ target_role: data.get("target_role"), difficulty: data.get("difficulty") }),
      (value) => setQuestion(value.question),
    );
  }

  function generateQuestionSet(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    run(
      () =>
        api.getInterviewQuestions({
          domain: data.get("domain"),
          difficulty: data.get("difficulty"),
          count: Number(data.get("count")),
        }),
      (value) => {
        setInterviewBatch(value);
        setQuestion(value.questions[0] ?? "");
      },
    );
  }

  function evaluateInterview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    run(
      () =>
        api.evaluateInterview({
          target_role: data.get("target_role"),
          question: question || data.get("question"),
          answer: data.get("answer"),
        }),
      setInterviewResult,
    );
  }

  function predictMl(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    run(
      () =>
        api.predictReadiness({
          experience_years: Number(data.get("experience_years")),
          projects_count: Number(data.get("projects_count")),
          skill_match_percent: Number(data.get("skill_match_percent")),
          interview_confidence: Number(data.get("interview_confidence")),
        }),
      setMlResult,
    );
  }

  function predictPersonality(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const interests = String(data.get("interests") ?? "")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
    run(
      () =>
        api.predictPersonality({
          typing_style: data.get("typing_style"),
          interests,
          answers: [data.get("answer_one"), data.get("answer_two"), data.get("answer_three")],
          choices: {
            leadership: Number(data.get("leadership")),
            communication: Number(data.get("communication")),
          },
        }),
      setPersonalityReport,
    );
  }

  if (!authReady) {
    return <div className="loading-screen">Preparing secure workspace...</div>;
  }

  if (!currentUser) {
    return <AuthScreen onAuthSuccess={handleAuthSuccess} />;
  }

  return (
    <main className={darkMode ? "app-shell dark" : "app-shell"}>
      <aside className="sidebar">
        <div className="brand">
          <Sparkles size={24} />
          <div>
            <h1>Ai Careers</h1>
            <p>for Future Generation</p>
          </div>
        </div>

        <nav className="tabs" aria-label="Career tools">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                className={activeTab === tab.id ? "tab active" : "tab"}
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                title={tab.label}
              >
                <Icon size={18} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="readiness-panel">
          <ScoreRing score={overallScore} />
          <p>{readinessLabel}</p>
          <div className="mini-stat">
            <span>Target</span>
            <strong>{activeTarget}</strong>
          </div>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Adaptive AI career clone phase</p>
            <h2>Career operating system</h2>
          </div>
          <div className="topbar-actions">
            <button className="ghost" onClick={() => setDarkMode((value) => !value)} title="Toggle theme">
              <Sun size={16} />
              {darkMode ? "Light" : "Dark"}
            </button>
            <div className="status-pill">
              <UserCircle size={16} />
              <span>{currentUser.name}</span>
            </div>
            <div className={`live-pill ${liveStatus}`}>
              {liveStatus === "connected" ? <Wifi size={16} /> : <WifiOff size={16} />}
              <span>{liveStatus === "connected" ? "Live" : liveStatus === "connecting" ? "Connecting" : "Offline"}</span>
            </div>
            <button className="ghost" onClick={() => setActiveTab("chat")} title="Open AI coach">
              <Bot size={16} />
              Coach
            </button>
            <div className="status-pill">
              {loading ? <Loader2 className="spin" size={16} /> : <Gauge size={16} />}
              <span>{loading ? "Working" : "Ready"}</span>
            </div>
            <button className="ghost" onClick={logout} title="Logout">
              <Lock size={16} />
              Logout
            </button>
          </div>
        </header>

        {error && <div className="alert">{error}</div>}

        {activeTab === "dashboard" && (
          <div className="dashboard">
            <section className="hero-panel">
              <div className="hero-copy">
                <p className="eyebrow">Mission control</p>
                <h3>{activeTarget} readiness sprint</h3>
                <p>
                  Track your plan, resume signal, interview strength, and ML readiness from one focused workspace.
                </p>
                <div className="hero-actions">
                  <button className="primary" onClick={() => setActiveTab("plan")}>
                    <Route size={18} />
                    Build roadmap
                  </button>
                  <button className="secondary" onClick={() => setActiveTab("resume")}>
                    <FileText size={18} />
                    Analyze resume
                  </button>
                </div>
              </div>
              <div className="hero-score">
                <ScoreRing score={overallScore} label="Overall" />
                <strong>{readinessLabel}</strong>
                <span>{roadmapProgress}% roadmap progress</span>
              </div>
            </section>

            <section className="metric-grid">
              <MetricCard icon={Target} label="Career readiness" value={`${Math.round(latestScore)}%`} note="Plan and skill match" />
              <MetricCard icon={FileText} label="Resume signal" value={`${Math.round(resumeScore)}%`} note="Keywords, proof, metrics" />
              <MetricCard icon={Mic} label="Interview score" value={`${Math.round(interviewScore)}%`} note="Structure and impact" />
              <MetricCard icon={Activity} label="Live signal" value={liveScore ? `${Math.round(liveScore)}%` : liveStatus} note="WebSocket event stream" />
            </section>

            <section className="grid dashboard-main">
              <div className="panel">
                <PanelHeader icon={ClipboardList} title="Today queue" />
                <div className="task-list">
                  <Task checked={Boolean(plan)} label="Generate a target-role roadmap" />
                  <Task checked={Boolean(resumeResult)} label="Run resume analyzer" />
                  <Task checked={Boolean(interviewResult)} label="Complete one mock interview answer" />
                  <Task checked={Boolean(mlResult)} label="Refresh ML readiness score" />
                </div>
              </div>

              <div className="panel">
                <PanelHeader icon={ShieldCheck} title="Skill signals" />
                <div className="skill-cloud">
                  {(plan?.skills ?? ["python", "react", "sql", "apis", "portfolio"]).map((skill) => (
                    <span key={skill}>{skill}</span>
                  ))}
                </div>
                <div className="focus-strip">
                  {focusAreas.map((focus, index) => (
                    <span className={index === plans.length % focusAreas.length ? "active" : ""} key={focus}>{focus}</span>
                  ))}
                </div>
              </div>

              <div className="panel">
                <PanelHeader icon={CalendarCheck} title="Weekly cadence" />
                <div className="cadence">
                  <span><strong>2</strong> portfolio blocks</span>
                  <span><strong>3</strong> resume bullets</span>
                  <span><strong>5</strong> applications</span>
                  <span><strong>2</strong> mock interviews</span>
                </div>
              </div>

              <LiveFeed events={liveEvents} status={liveStatus} />
            </section>

            <section className="grid two">
              <div className="panel">
                <PanelHeader icon={Activity} title="Emotion trends" />
                <div className="chart-box">
                  <ResponsiveContainer width="100%" height={240}>
                    <BarChart data={emotionChart}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="score" fill="#2563eb" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
              <div className="panel">
                <PanelHeader icon={UserCircle} title="Personality insights" />
                {personalityReport ? (
                  <PersonalitySummary report={personalityReport} />
                ) : (
                  <p className="empty">Complete the personality page to generate career compatibility insights.</p>
                )}
              </div>
            </section>

            <section className="panel wide">
              <PanelHeader icon={Trophy} title="Latest roadmaps" />
              <div className="plan-list">
                {plans.length ? plans.map((saved) => (
                  <button className="saved-plan advanced" key={saved.id} onClick={() => { setPlan(saved); setActiveTab("plan"); }}>
                    <strong>{saved.target_role}</strong>
                    <span>{Math.round(saved.readiness_score)} readiness</span>
                    <ArrowUpRight size={16} />
                  </button>
                )) : <p className="empty">Create your first plan and it will appear here.</p>}
              </div>
            </section>
          </div>
        )}

        {activeTab === "plan" && (
          <div className="grid two">
            <form className="panel" onSubmit={createPlan}>
              <PanelHeader icon={Route} title="Project planning and architecture" />
              <div className="field-row">
                <label>Name<input name="name" defaultValue="Divjot" required /></label>
                <label>Current role<input name="current_role" defaultValue="Student" required /></label>
              </div>
              <label>Target role<input name="target_role" defaultValue="AI Engineer" required /></label>
              <label>Skills<input name="skills" defaultValue="python, react, sql, apis" required /></label>
              <div className="field-row">
                <label>Experience<input name="experience_years" type="number" min="0" max="50" step="0.5" defaultValue="1" /></label>
                <label>Projects<input name="projects_count" type="number" min="0" max="100" defaultValue="3" /></label>
                <label>Confidence<input name="interview_confidence" type="number" min="1" max="10" defaultValue="6" /></label>
              </div>
              <button className="primary"><BriefcaseBusiness size={18} />Generate plan</button>
            </form>

            <div className="panel result-panel">
              <PanelHeader icon={Target} title="Roadmap" />
              {plan ? (
                <>
                  <ScoreRing score={plan.readiness_score} label="Score" />
                  <ProgressBar value={roadmapProgress} label="Roadmap completion model" />
                  <ol className="roadmap">{plan.roadmap.map((item) => <li key={item}>{item}</li>)}</ol>
                </>
              ) : (
                <p className="empty">Your generated plan will appear here.</p>
              )}
            </div>

            <div className="panel wide">
              <PanelHeader icon={Trophy} title="Saved plans" />
              <div className="plan-list">
                {plans.map((saved) => (
                  <button className="saved-plan" key={saved.id} onClick={() => setPlan(saved)}>
                    <strong>{saved.target_role}</strong>
                    <span>{Math.round(saved.readiness_score)} readiness</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === "chat" && (
          <div className="chat-workspace">
            <section className="panel chat-panel">
              <PanelHeader icon={Bot} title="AI chatbot" />
              <div className={`model-badge ${coachMode}`}>
                <BrainCircuit size={15} />
                <span>{coachMode === "openrouter" ? "OpenRouter intelligence" : coachMode === "gpt" ? "GPT streaming mode" : "Local fallback mode"}</span>
              </div>
              <div className="chat-stream">
                {coachMessages.map((message, index) => (
                  <article className={`chat-bubble ${message.role}`} key={`${message.role}-${index}`}>
                    <div className="chat-avatar">{message.role === "assistant" ? <Bot size={16} /> : <Sparkles size={16} />}</div>
                    <p>{message.content || (coachStreaming ? "Thinking..." : "")}</p>
                  </article>
                ))}
              </div>

              <form className="chat-composer" onSubmit={askChat}>
                <input name="target_role" defaultValue={activeTarget} aria-label="Target role" />
                <textarea name="message" placeholder="Ask like GPT: rewrite my bullets, create a roadmap, mock interview me, explain my resume gaps..." />
                <button className="primary" disabled={coachStreaming}>
                  {coachStreaming ? <Loader2 className="spin" size={18} /> : <Send size={18} />}
                  {coachStreaming ? "Streaming" : "Send"}
                </button>
              </form>
            </section>

            <aside className="panel coach-side">
              <PanelHeader icon={WandSparkles} title="Smart prompts" />
              <div className="prompt-chips vertical">
                {quickPrompts.concat(["Mock interview me for my target role", "Explain my resume score", "Give me job matches", "Rewrite these bullet points"]).map((prompt) => (
                  <button type="button" key={prompt} onClick={() => {
                    const input = document.querySelector<HTMLTextAreaElement>(".chat-composer textarea");
                    if (input) input.value = prompt;
                  }}>
                    {prompt}
                  </button>
                ))}
              </div>
              <div className="context-card">
                <strong>Context engine</strong>
                <span>Target: {activeTarget}</span>
                <span>Readiness: {Math.round(latestScore)}%</span>
                <span>Resume: {Math.round(resumeScore)}%</span>
                <span>Interview: {Math.round(interviewScore)}%</span>
              </div>
            </aside>
          </div>
        )}

        {activeTab === "resume" && (
          <div className="grid two resume-lab">
            <form className="panel" onSubmit={analyzeResumeFile}>
              <PanelHeader icon={WandSparkles} title="Resume intelligence upload" />
              <label>Target role<input name="target_role" defaultValue="AI Engineer" /></label>
              <label className="file-drop">
                <Upload size={22} />
                <span>Upload resume file</span>
                <small>.txt, .pdf, or .docx</small>
                <input name="file" type="file" accept=".txt,.pdf,.docx" required />
              </label>
              <label>Fallback text for scanned PDFs<textarea name="fallback_text" placeholder="If your PDF is image-based, paste the resume text here so the intelligence system can still score it." /></label>
              <button className="primary"><WandSparkles size={18} />Run intelligence report</button>
            </form>

            <form className="panel" onSubmit={analyzeResume}>
              <PanelHeader icon={FileText} title="Quick text analyzer" />
              <label>Target role<input name="target_role" defaultValue="Full Stack Developer" /></label>
              <label>Resume text<textarea name="resume_text" defaultValue={sampleResume} /></label>
              <button className="primary"><FileText size={18} />Analyze resume</button>
            </form>

            <div className="panel result-panel wide">
              <PanelHeader icon={Gauge} title="Resume intelligence report" />
              {resumeIntelligence ? (
                <ResumeIntelligenceReport report={resumeIntelligence} />
              ) : resumeResult ? (
                <>
                  <ScoreRing score={resumeResult.score} label="Resume" />
                  <ProgressBar value={resumeResult.score} label="ATS-style match signal" />
                  <List title="Strengths" items={resumeResult.strengths} />
                  <List title="Gaps" items={resumeResult.gaps} />
                  <List title="Suggestions" items={resumeResult.suggestions} />
                </>
              ) : <p className="empty">Resume insights will appear here.</p>}
            </div>
          </div>
        )}

        {activeTab === "interview" && (
          <div className="grid two">
            <form className="panel" onSubmit={generateQuestionSet}>
              <PanelHeader icon={Mic} title="Domain interview prep" />
              <label>Domain<select name="domain" defaultValue="AI / Machine Learning">{interviewDomains.map((domain) => <option key={domain}>{domain}</option>)}</select></label>
              <div className="field-row">
                <label>Difficulty<select name="difficulty" defaultValue="mid"><option>junior</option><option>mid</option><option>senior</option></select></label>
                <label>Questions<select name="count" defaultValue="7"><option>5</option><option>6</option><option>7</option><option>8</option><option>9</option><option>10</option></select></label>
              </div>
              <button className="primary"><Mic size={18} />Generate question set</button>
              {interviewBatch && (
                <div className="question-set">
                  {interviewBatch.questions.map((item, index) => (
                    <button type="button" key={item} onClick={() => setQuestion(item)}>
                      <strong>Q{index + 1}</strong>
                      <span>{item}</span>
                    </button>
                  ))}
                </div>
              )}
            </form>
            <form className="panel" onSubmit={generateQuestion}>
              <PanelHeader icon={MessageSquareText} title="Single role question" />
              <label>Target role<input name="target_role" defaultValue="Backend Developer" /></label>
              <label>Difficulty<select name="difficulty" defaultValue="mid"><option>junior</option><option>mid</option><option>senior</option></select></label>
              <button className="secondary"><Mic size={18} />Generate one question</button>
            </form>
            <form className="panel wide" onSubmit={evaluateInterview}>
              <PanelHeader icon={MessageSquareText} title="Mock answer" />
              <label>Question<textarea name="question" value={question} onChange={(event) => setQuestion(event.target.value)} /></label>
              <label>Target role<input name="target_role" defaultValue="Backend Developer" /></label>
              <label>Answer<textarea name="answer" defaultValue="I built a FastAPI resume analyzer, designed endpoints, stored results in SQLite, and improved feedback clarity using measurable scoring rules." /></label>
              <button className="primary"><Gauge size={18} />Evaluate answer</button>
              {interviewResult && (
                <>
                  <ProgressBar value={interviewResult.score} label="Answer strength" />
                  <p className="feedback">{interviewResult.score}/100 - {interviewResult.feedback}</p>
                </>
              )}
            </form>
          </div>
        )}

        {activeTab === "personality" && (
          <div className="grid two">
            <form className="panel" onSubmit={predictPersonality}>
              <PanelHeader icon={UserCircle} title="Personality & career prediction" />
              <label>Interests<input name="interests" defaultValue="AI, building products, design, helping people" /></label>
              <label>Typing style<textarea name="typing_style" defaultValue="I like clear answers, practical steps, and building useful projects quickly." /></label>
              <label>Question 1<textarea name="answer_one" defaultValue="When I am stuck, I break the problem into smaller parts and look for examples." /></label>
              <label>Question 2<textarea name="answer_two" defaultValue="I enjoy projects where I can combine technical systems with user experience." /></label>
              <label>Question 3<textarea name="answer_three" defaultValue="I prefer work environments where I can learn fast, get feedback, and ship real features." /></label>
              <div className="field-row">
                <label>Leadership<select name="leadership" defaultValue="4"><option>1</option><option>2</option><option>3</option><option>4</option><option>5</option></select></label>
                <label>Communication<select name="communication" defaultValue="4"><option>1</option><option>2</option><option>3</option><option>4</option><option>5</option></select></label>
              </div>
              <button className="primary"><BrainCircuit size={18} />Generate prediction</button>
            </form>
            <div className="panel result-panel">
              <PanelHeader icon={Gauge} title="Personality dashboard" />
              {personalityReport ? (
                <PersonalitySummary report={personalityReport} detailed />
              ) : (
                <p className="empty">Your personality, communication behavior, learning style, and career matches will appear here.</p>
              )}
            </div>
          </div>
        )}

        {activeTab === "ml" && (
          <div className="grid two">
            <form className="panel" onSubmit={predictMl}>
              <PanelHeader icon={BrainCircuit} title="ML model readiness" />
              <div className="field-row">
                <label>Experience<input name="experience_years" type="number" step="0.5" defaultValue="2" /></label>
                <label>Projects<input name="projects_count" type="number" defaultValue="4" /></label>
              </div>
              <div className="field-row">
                <label>Skill match<input name="skill_match_percent" type="number" min="0" max="100" defaultValue="72" /></label>
                <label>Confidence<input name="interview_confidence" type="number" min="1" max="10" defaultValue="7" /></label>
              </div>
              <button className="primary"><BrainCircuit size={18} />Predict readiness</button>
            </form>
            <div className="panel result-panel">
              <PanelHeader icon={Gauge} title="Prediction" />
              {mlResult ? (
                <>
                  <ScoreRing score={mlResult.readiness_score} label="ML" />
                  <ProgressBar value={mlResult.readiness_score} label="Model confidence proxy" />
                  <p className="feedback">{mlResult.label}</p>
                </>
              ) : <p className="empty">Train the model or use the heuristic predictor.</p>}
            </div>
          </div>
        )}
      </section>
    </main>
  );
}

function Result({ title, result, list }: { title: string; result?: string; list?: string[] }) {
  return (
    <div className="panel result-panel">
      <PanelHeader icon={MessageSquareText} title={title} />
      {result ? (
        <>
          <p className="answer">{result}</p>
          <List title="Actions" items={list ?? []} />
        </>
      ) : <p className="empty">Results will appear here.</p>}
    </div>
  );
}

function PanelHeader({ icon: Icon, title }: { icon: typeof Route; title: string }) {
  return (
    <div className="panel-header">
      <Icon size={18} />
      <h3>{title}</h3>
    </div>
  );
}

function MetricCard({ icon: Icon, label, value, note }: { icon: typeof Route; label: string; value: string; note: string }) {
  return (
    <div className="metric-card">
      <div className="metric-icon"><Icon size={18} /></div>
      <span>{label}</span>
      <strong>{value}</strong>
      <p>{note}</p>
    </div>
  );
}

function ProgressBar({ value, label }: { value: number; label: string }) {
  const safeValue = Math.max(0, Math.min(value, 100));
  return (
    <div className="progress-block">
      <div>
        <span>{label}</span>
        <strong>{Math.round(safeValue)}%</strong>
      </div>
      <div className="progress-track"><span style={{ width: `${safeValue}%` }} /></div>
    </div>
  );
}

function Task({ checked, label }: { checked: boolean; label: string }) {
  return (
    <div className={checked ? "task done" : "task"}>
      <CheckCircle2 size={18} />
      <span>{label}</span>
    </div>
  );
}

function ResumeIntelligenceReport({ report }: { report: ResumeIntelligence }) {
  return (
    <div className="intelligence-report">
      <div className="report-summary">
        <ScoreRing score={report.overall_score} label="Overall" />
        <div>
          <p className="eyebrow">Analyzed file</p>
          <h4>{report.file_name}</h4>
          <p className="answer">{report.target_role} · {report.seniority_signal} signal · {Math.round(report.ats_score)} ATS score</p>
        </div>
      </div>

      <div className="report-grid">
        <div className="report-box">
          <PanelHeader icon={BrainCircuit} title="NLP domain sorting" />
          <ProgressBar value={report.deep_learning_signal} label="Deep learning fit signal" />
          <div className="domain-ranking">
            {report.domain_ranking.slice(0, 4).map((item) => (
              <article key={item.domain}>
                <div>
                  <strong>{item.domain}</strong>
                  <span>{item.confidence} confidence</span>
                </div>
                <b>{Math.round(item.score)}%</b>
                <p>Evidence: {item.evidence.length ? item.evidence.join(", ") : "Needs stronger keyword proof"}</p>
              </article>
            ))}
          </div>
        </div>

        <div className="report-box">
          <PanelHeader icon={WandSparkles} title="NLP keywords" />
          <div className="skill-cloud">{report.nlp_keywords.map((keyword) => <span key={keyword}>{keyword}</span>)}</div>
        </div>

        <div className="report-box">
          <PanelHeader icon={BriefcaseBusiness} title="Suggested jobs" />
          <div className="job-list">
            {report.job_matches.slice(0, 4).map((job) => (
              <article className="job-match" key={job.title}>
                <div>
                  <strong>{job.title}</strong>
                  <p>{job.reason}</p>
                </div>
                <span>{Math.round(job.match_score)}%</span>
              </article>
            ))}
          </div>
        </div>

        <div className="report-box">
          <PanelHeader icon={ShieldCheck} title="Detected skills" />
          <div className="skill-cloud">{report.detected_skills.map((skill) => <span key={skill}>{skill}</span>)}</div>
        </div>

        <div className="report-box">
          <PanelHeader icon={Target} title="Skill gaps" />
          <div className="skill-cloud missing">{report.missing_skills.length ? report.missing_skills.map((skill) => <span key={skill}>{skill}</span>) : <span>No major gaps</span>}</div>
        </div>

        <div className="report-box">
          <PanelHeader icon={WandSparkles} title="Bullet rewrites" />
          <List title="Improved bullets" items={report.rewritten_bullets} />
        </div>

        <div className="report-box">
          <PanelHeader icon={Layers3} title="Portfolio projects" />
          <List title="Recommended proof" items={report.project_recommendations} />
        </div>

        <div className="report-box">
          <PanelHeader icon={Mic} title="Interview focus" />
          <List title="Practice plan" items={report.interview_focus} />
        </div>
      </div>

      <div className="report-box">
        <PanelHeader icon={CalendarCheck} title="Learning plan" />
        <List title="Next steps" items={report.learning_plan} />
      </div>
    </div>
  );
}

function PersonalitySummary({ report, detailed = false }: { report: PersonalityReport; detailed?: boolean }) {
  const scoreRows = Object.entries(report.scores).map(([name, score]) => ({ name, score }));
  return (
    <div className="personality-report">
      <div className="report-summary">
        <ScoreRing score={Number(report.scores.technical ?? 70)} label="Fit" />
        <div>
          <p className="eyebrow">Personality type</p>
          <h4>{report.personality_type}</h4>
          <p className="answer">{report.communication_style} · {report.learning_style}</p>
        </div>
      </div>
      <p className="feedback">{report.report}</p>
      <div className="chart-box">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={scoreRows}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="score" fill="#2563eb" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="report-grid">
        <div className="report-box">
          <PanelHeader icon={BriefcaseBusiness} title="Career matches" />
          <div className="skill-cloud">{report.career_matches.map((item) => <span key={item}>{item}</span>)}</div>
        </div>
        <div className="report-box">
          <PanelHeader icon={ShieldCheck} title="Strengths" />
          <List title="Top strengths" items={report.strengths} />
        </div>
        {detailed && (
          <>
            <div className="report-box">
              <PanelHeader icon={Target} title="Growth areas" />
              <List title="Watchouts" items={report.weaknesses} />
            </div>
            <div className="report-box">
              <PanelHeader icon={PanelsTopLeft} title="Best environment" />
              <p className="answer">{report.best_work_environment}</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function AuthScreen({ onAuthSuccess }: { onAuthSuccess: (response: AuthResponse, remember?: boolean) => void }) {
  const [mode, setMode] = useState<"login" | "signup" | "otp" | "forgot">("login");
  const [captcha, setCaptcha] = useState<{ captcha_id: string; question: string } | null>(null);
  const [authMessage, setAuthMessage] = useState("");
  const [pendingEmail, setPendingEmail] = useState("");
  const [remember, setRemember] = useState(true);

  useEffect(() => {
    api.captcha().then(setCaptcha).catch(() => undefined);
  }, [mode]);

  async function submitAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAuthMessage("");
    const data = new FormData(event.currentTarget);
    try {
      if (mode === "login") {
        const response = await api.login({
          email: data.get("email"),
          password: data.get("password"),
          remember_me: remember,
          captcha_id: captcha?.captcha_id,
          captcha_answer: data.get("captcha_answer"),
        });
        onAuthSuccess(response, remember);
      }
      if (mode === "signup") {
        const response = await api.signup({
          name: data.get("name"),
          email: data.get("email"),
          phone: data.get("phone"),
          password: data.get("password"),
          confirm_password: data.get("confirm_password"),
          captcha_id: captcha?.captcha_id,
          captcha_answer: data.get("captcha_answer"),
        });
        setPendingEmail(String(data.get("email") ?? ""));
        setAuthMessage(response.dev_otp ? `Dev OTP: ${response.dev_otp}` : "OTP sent to email.");
        setMode("otp");
      }
      if (mode === "otp") {
        const response = await api.verifyOtp({ email: pendingEmail || data.get("email"), otp: data.get("otp"), channel: "email" });
        onAuthSuccess(response, true);
      }
      if (mode === "forgot") {
        const response = await api.forgotPassword({ email: data.get("email") });
        setPendingEmail(String(data.get("email") ?? ""));
        setAuthMessage(response.dev_otp ? `Password reset OTP: ${response.dev_otp}` : response.message);
      }
    } catch (caught) {
      setAuthMessage(caught instanceof Error ? caught.message : "Authentication failed.");
    }
  }

  async function googleDemo() {
    const response = await api.googleAuth({ email: "google.user@example.com", name: "Google User", google_token: "demo-google-token" });
    onAuthSuccess(response, true);
  }

  return (
    <main className="auth-layout">
      <motion.section className="auth-card" initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }}>
        <div className="brand auth-brand">
          <Sparkles size={24} />
          <div>
            <h1>Ai Careers</h1>
            <p>secure intelligence workspace</p>
          </div>
        </div>
        <div className="auth-tabs">
          <button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>Login</button>
          <button className={mode === "signup" ? "active" : ""} onClick={() => setMode("signup")}>Signup</button>
          <button className={mode === "forgot" ? "active" : ""} onClick={() => setMode("forgot")}>Forgot</button>
        </div>
        <form className="auth-form" onSubmit={submitAuth}>
          {mode === "signup" && <label>Name<input name="name" required /></label>}
          {(mode === "login" || mode === "signup" || mode === "forgot") && <label>Email<input name="email" type="email" required /></label>}
          {mode === "signup" && <label>Phone<input name="phone" /></label>}
          {(mode === "login" || mode === "signup") && <label>Password<input name="password" type="password" required minLength={8} /></label>}
          {mode === "signup" && <label>Confirm password<input name="confirm_password" type="password" required minLength={8} /></label>}
          {mode === "otp" && (
            <>
              <label>Email<input name="email" type="email" defaultValue={pendingEmail} required /></label>
              <label>Email OTP<input name="otp" required /></label>
            </>
          )}
          {(mode === "login" || mode === "signup") && captcha && <label>CAPTCHA: {captcha.question}<input name="captcha_answer" required /></label>}
          {mode === "login" && <label className="check-row"><input type="checkbox" checked={remember} onChange={(event) => setRemember(event.target.checked)} />Remember me</label>}
          <button className="primary">{mode === "signup" ? "Create account" : mode === "otp" ? "Verify OTP" : mode === "forgot" ? "Send reset OTP" : "Login"}</button>
          <button type="button" className="secondary" onClick={googleDemo}>Continue with Google</button>
        </form>
        {authMessage && <p className="feedback">{authMessage}</p>}
      </motion.section>
    </main>
  );
}

function LiveFeed({ events, status }: { events: LiveEvent[]; status: LiveStatus }) {
  return (
    <div className="panel live-feed">
      <div className="live-feed-header">
        <PanelHeader icon={Bell} title="Live activity" />
        <span className={`live-dot ${status}`} />
      </div>
      <div className="event-list">
        {events.map((event, index) => (
          <article className="event-item" key={`${event.created_at}-${index}`}>
            <div className="event-icon"><Activity size={15} /></div>
            <div>
              <strong>{event.title}</strong>
              <p>{event.detail}</p>
              <span>{formatTime(event.created_at)}{typeof event.score === "number" ? ` · ${Math.round(event.score)} score` : ""}</span>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

function formatTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "just now";
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function List({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="mini-list">
      <h4>{title}</h4>
      <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul>
    </div>
  );
}

export default App;
