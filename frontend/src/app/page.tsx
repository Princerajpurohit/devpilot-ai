"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  Search,
  ShieldAlert,
  FileText,
  GitCommit,
  FolderGit2,
  ChevronRight,
  Download,
  Award,
  AlertTriangle,
  TrendingUp,
  User,
  Clock,
  ArrowRightLeft,
  ArrowLeft,
  CheckCircle2,
  XCircle,
  ExternalLink,
  Lock,
  BookOpen,
  Plus,
  CornerDownRight,
  ShieldCheck,
  RefreshCw,
  Copy,
  MessageSquare,
  Send,
  Lightbulb,
  Info,
} from "lucide-react";

// Custom Github Icon component since it is missing in the installed lucide-react version
const Github = ({ className }: { className?: string }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
    <path d="M9 18c-4.51 2-5-2-7-2" />
  </svg>
);

// API Base URL for local development
const API_BASE = "http://localhost:8000/api";

// Helper to render basic inline markdown elements: **bold**, `code`, and *italic* / _italic_
const renderFormattedText = (text: string) => {
  if (!text) return "";
  const parts = text.split(/(\*\*.*?\*\*|`.*?`|\*.*?\*|_.*?_)/g);
  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={index} className="font-semibold text-white">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={index} className="px-1.5 py-0.5 bg-slate-950 border border-slate-800 rounded font-mono text-cyan-400 text-xs">
          {part.slice(1, -1)}
        </code>
      );
    }
    if ((part.startsWith("*") && part.endsWith("*")) || (part.startsWith("_") && part.endsWith("_"))) {
      return (
        <em key={index} className="italic text-slate-200">
          {part.slice(1, -1)}
        </em>
      );
    }
    return part;
  });
};

interface Toast {
  id: string;
  message: string;
  type: "success" | "error" | "info";
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  referencedFiles?: string[];
}

interface Insight {
  type: "warning" | "info" | "good";
  message: string;
  file?: string | null;
}

export default function Home() {
  // App views: "landing" | "loading" | "report" | "compare"
  const [view, setView] = useState<"landing" | "loading" | "report" | "compare">("landing");
  const [repoUrl, setRepoUrl] = useState("");
  const [githubToken, setGithubToken] = useState("");
  const [history, setHistory] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<"overview" | "security" | "docs" | "commits" | "structure" | "roadmap" | "chat" | "insights">("overview");
  
  // Scanned Repo Data
  const [report, setReport] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loaderMessage, setLoaderMessage] = useState("");
  const [loaderSubMessage, setLoaderSubMessage] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatQuestion, setChatQuestion] = useState("");
  const [isChatting, setIsChatting] = useState(false);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [isLoadingInsights, setIsLoadingInsights] = useState(false);
  
  // Comparison state
  const [compareUrlA, setCompareUrlA] = useState("");
  const [compareUrlB, setCompareUrlB] = useState("");
  const [compareResult, setCompareResult] = useState<any>(null);
  const [isComparing, setIsComparing] = useState(false);

  // Toasts
  const [toasts, setToasts] = useState<Toast[]>([]);
  
  // Drag & drop state
  const [isDragOver, setIsDragOver] = useState(false);

  // Load history on mount
  useEffect(() => {
    fetchHistory();
  }, []);

  useEffect(() => {
    if (!report?.id) {
      setChatMessages([]);
      return;
    }

    const loadChatHistory = async () => {
      try {
        const response = await fetch(`${API_BASE}/chat/${report.id}`);
        if (!response.ok) return;
        const data = await response.json();
        setChatMessages(data.map((message: { role: "user" | "assistant"; content: string }) => ({
          role: message.role,
          content: message.content,
        })));
      } catch (error) {
        console.error("Failed to load chat history:", error);
      }
    };

    loadChatHistory();
  }, [report?.id]);

  useEffect(() => {
    if (activeTab !== "insights" || !report?.id || insights.length || isLoadingInsights) return;
    const loadInsights = async () => {
      setIsLoadingInsights(true);
      try {
        const response = await fetch(`${API_BASE}/insights/${report.id}`);
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Unable to load insights");
        setInsights(data);
      } catch (error: any) {
        showToast(error.message || "Unable to load insights", "error");
      } finally {
        setIsLoadingInsights(false);
      }
    };
    loadInsights();
  }, [activeTab, report?.id, insights.length, isLoadingInsights]);

  const showToast = (message: string, type: "success" | "error" | "info" = "success") => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_BASE}/history`);
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (e) {
      console.error("Failed to load history:", e);
    }
  };

  // Simulate progress statements to give the loader a dynamic feel
  const startLoadingAnimations = () => {
    const messages = [
      { main: "Connecting to GitHub...", sub: "Authenticating and fetching repository metadata" },
      { main: "Retrieving File System Tree...", sub: "Scanning directory paths, checking configs & Dockerfiles" },
      { main: "Parsing Documentation...", sub: "Analyzing README.md for install setup guides and API references" },
      { main: "Auditing Commit Logs...", sub: "Compiling timeline trends, contributors count, and flagging generic commits" },
      { main: "Running Secret Scanner...", sub: "Regex searching source code variables for API keys and JWT credentials" },
      { main: "Checking OSV Database...", sub: "Querying Open Source Vulnerability CVEs for manifest dependencies" },
      { main: "Invoking AI Principal Reviewer...", sub: "Generating startup codebase summary and investor due diligence reports" },
      { main: "Compiling PDF ReportLab Layout...", sub: "Structuring score vectors and creating multi-page report files" }
    ];

    let idx = 0;
    setLoaderMessage(messages[0].main);
    setLoaderSubMessage(messages[0].sub);

    const interval = setInterval(() => {
      idx += 1;
      if (idx < messages.length) {
        setLoaderMessage(messages[idx].main);
        setLoaderSubMessage(messages[idx].sub);
      } else {
        clearInterval(interval);
      }
    }, 2800);

    return interval;
  };

  const handleScan = async (url: string = repoUrl) => {
    if (!url) {
      showToast("Please enter a valid GitHub repository URL", "error");
      return;
    }

    setView("loading");
    setIsLoading(true);
    const loaderInterval = startLoadingAnimations();

    try {
      const response = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repo_url: url,
          github_token: githubToken || null,
        }),
      });

      clearInterval(loaderInterval);

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Server failed to scan repository");
      }

      const data = await response.json();
      setReport(data);
      setChatMessages([]);
      setChatQuestion("");
      setInsights([]);
      setView("report");
      setActiveTab("overview");
      showToast("Analysis complete!", "success");
      fetchHistory(); // Refresh history panel
    } catch (err: any) {
      clearInterval(loaderInterval);
      setView("landing");
      showToast(err.message || "Failed to analyze repository.", "error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCompare = async () => {
    if (!compareUrlA || !compareUrlB) {
      showToast("Please enter both repository URLs to compare", "error");
      return;
    }

    setIsComparing(true);
    setView("loading");
    setLoaderMessage("Comparing Repositories...");
    setLoaderSubMessage("Fetching metadata and analyzing both repositories concurrently...");

    try {
      const response = await fetch(`${API_BASE}/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          urls: [compareUrlA, compareUrlB],
        }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Server comparison failed");
      }

      const data = await response.json();
      setCompareResult(data);
      setView("compare");
      showToast("Comparison loaded!", "success");
    } catch (e: any) {
      setView("landing");
      showToast(e.message || "Failed to compile comparison.", "error");
    } finally {
      setIsComparing(false);
    }
  };

  const handleDownloadPDF = async () => {
    if (!report || !report.id) return;
    showToast("Generating PDF download stream...", "info");
    
    try {
      window.open(`${API_BASE}/report/${report.id}/pdf`, "_blank");
      showToast("PDF download started!", "success");
    } catch (e) {
      showToast("Failed to download PDF report", "error");
    }
  };

  const handleChatSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const question = chatQuestion.trim();
    if (!question || !report?.id || isChatting) return;

    const previousMessages = chatMessages;
    const userMessage: ChatMessage = { role: "user", content: question };
    setChatMessages((messages) => [...messages, userMessage]);
    setChatQuestion("");
    setIsChatting(true);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          analysis_id: report.id,
          question,
          chat_history: previousMessages.map(({ role, content }) => ({ role, content })),
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Unable to answer that repository question");
      }
      setChatMessages((messages) => [
        ...messages,
        { role: "assistant", content: data.answer, referencedFiles: data.referenced_files || [] },
      ]);
    } catch (error: any) {
      setChatMessages((messages) => messages.slice(0, -1));
      setChatQuestion(question);
      showToast(error.message || "Unable to send chat message", "error");
    } finally {
      setIsChatting(false);
    }
  };

  // Drag & Drop event handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const text = e.dataTransfer.getData("text");
    if (text && text.includes("github.com")) {
      setRepoUrl(text);
      showToast("GitHub URL pasted from drag!", "info");
      handleScan(text);
    } else {
      showToast("Please drop a valid GitHub repository link", "error");
    }
  };

  // Render score rating label/color
  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-[#06b6d4] border-[#06b6d4]";
    if (score >= 60) return "text-[#f59e0b] border-[#f59e0b]";
    return "text-[#f43f5e] border-[#f43f5e]";
  };

  const getScoreBg = (score: number) => {
    if (score >= 80) return "bg-[#06b6d4]/10 text-[#06b6d4] border-[#06b6d4]/20";
    if (score >= 60) return "bg-[#f59e0b]/10 text-[#f59e0b] border-[#f59e0b]/20";
    return "bg-[#f43f5e]/10 text-[#f43f5e] border-[#f43f5e]/20";
  };

  const getSeverityColor = (sev: string) => {
    switch (sev.toLowerCase()) {
      case "high":
      case "critical":
        return "bg-[#f43f5e]/10 text-[#f43f5e] border-[#f43f5e]/20";
      case "medium":
      case "moderate":
        return "bg-[#f59e0b]/10 text-[#f59e0b] border-[#f59e0b]/20";
      default:
        return "bg-slate-800 text-slate-300 border-slate-700";
    }
  };

  return (
    <div className="flex-1 flex flex-col relative min-h-screen selection:bg-indigo-500 selection:text-white">
      
      {/* Background Ambient Glowing Orbs */}
      <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-purple-500/10 rounded-full blur-[120px] pointer-events-none -z-10" />
      <div className="absolute bottom-10 right-1/4 w-[400px] h-[400px] bg-cyan-500/10 rounded-full blur-[100px] pointer-events-none -z-10" />

      {/* Header Bar */}
      <header className="border-b border-slate-800 bg-[#090d16]/80 backdrop-blur-md sticky top-0 z-40 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div 
            className="flex items-center gap-2 cursor-pointer" 
            onClick={() => { setView("landing"); setRepoUrl(""); }}
          >
            <div className="p-2 bg-gradient-to-tr from-indigo-600 to-cyan-400 rounded-lg text-white font-bold">
              <Github className="w-5 h-5" />
            </div>
            <div>
              <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-indigo-400 to-cyan-300 bg-clip-text text-transparent">
                DevPilot AI
              </span>
              <span className="text-[10px] text-slate-500 block uppercase font-mono tracking-widest leading-none">
                Repository intelligence
              </span>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            {view !== "landing" && (
              <button 
                onClick={() => setView("landing")}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-700 hover:border-slate-600 bg-slate-900 text-sm hover:text-white transition"
              >
                <ArrowLeft className="w-4 h-4" /> Back to Search
              </button>
            )}
            
            <a 
              href="https://github.com" 
              target="_blank" 
              className="text-slate-400 hover:text-indigo-400 transition"
              title="GitHub Platform"
            >
              <Github className="w-5 h-5" />
            </a>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 flex flex-col justify-start">
        
        {/* VIEW 1: LANDING SCREEN */}
        {view === "landing" && (
          <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-8 py-8 items-start">
            
            {/* Search inputs */}
            <div className="lg:col-span-2 space-y-8">
              <div className="space-y-4">
                <span className="px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 text-xs font-semibold border border-indigo-500/20 uppercase tracking-wider inline-block">
                  Principal codebase due-diligence
                </span>
                <h1 className="text-4xl md:text-5xl font-black tracking-tight leading-tight text-white">
                  Audit any GitHub Repository <br />
                  <span className="bg-gradient-to-r from-indigo-400 via-cyan-400 to-cyan-400 bg-clip-text text-transparent">
                    with AI-Powered Intelligence
                  </span>
                </h1>
                <p className="text-slate-400 text-lg leading-relaxed max-w-xl">
                  Analyze README structures, secret leaks, version control velocity, and vulnerability dependency checks. Complete with Fix-It Roadmaps and vector PDF downloads.
                </p>
              </div>

              {/* URL Input Form */}
              <div 
                className={`p-6 bg-slate-900/60 rounded-lg border transition-all ${
                  isDragOver ? "border-indigo-500 bg-indigo-950/20 shadow-2xl scale-[1.01]" : "border-slate-800"
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <div className="space-y-4">
                  <div className="flex flex-col gap-1">
                    <label className="text-xs text-slate-400 uppercase tracking-widest font-mono">
                      Drag & Drop URL or Paste Repository
                    </label>
                    <div className="flex items-center gap-2 mt-1 relative">
                      <div className="absolute left-4 text-slate-500">
                        <Search className="w-5 h-5" />
                      </div>
                      <input
                        type="text"
                        placeholder="https://github.com/owner/repository"
                        value={repoUrl}
                        onChange={(e) => setRepoUrl(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleScan()}
                        className="w-full pl-12 pr-4 py-3.5 bg-slate-950 border border-slate-800 rounded-md focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-white placeholder-slate-600 outline-none transition text-sm"
                      />
                      <button
                        onClick={() => handleScan()}
                        className="px-6 py-3.5 bg-indigo-600 hover:bg-indigo-500 font-bold rounded-md text-white transition-all text-sm flex items-center gap-2 hover:shadow-lg shadow-indigo-900/20 hover:scale-[1.02]"
                      >
                        Analyze <ChevronRight className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Settings accordion (Optional Token) */}
                  <div className="pt-2 border-t border-slate-800/60">
                    <details className="group">
                      <summary className="text-xs text-slate-500 cursor-pointer list-none flex items-center gap-1 hover:text-slate-400 transition font-mono">
                        <Lock className="w-3 h-3 text-slate-600 group-open:text-indigo-500" />
                        <span>Configure GitHub Access Token (Optional)</span>
                      </summary>
                      <div className="mt-2 pl-4 border-l-2 border-slate-800">
                        <input
                          type="password"
                          placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxx"
                          value={githubToken}
                          onChange={(e) => setGithubToken(e.target.value)}
                          className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-300 placeholder-slate-700 outline-none focus:border-indigo-500 transition text-xs font-mono"
                        />
                        <span className="text-[10px] text-slate-500 mt-1 block">
                          Bypasses GitHub public rate limits (60 requests/hr). Tokens are never saved.
                        </span>
                      </div>
                    </details>
                  </div>
                </div>
              </div>

              {/* Repository Compare Trigger Card */}
              <div className="p-5 bg-gradient-to-r from-slate-900/80 to-slate-950/80 rounded-md border border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-indigo-500/10 rounded-lg border border-indigo-500/20 text-indigo-400">
                    <ArrowRightLeft className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-white">Compare Two Repositories</h3>
                    <p className="text-xs text-slate-400">Check side-by-side grades and audit scores of competitors.</p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setView("compare");
                    setCompareUrlA("");
                    setCompareUrlB("");
                    setCompareResult(null);
                  }}
                  className="px-4 py-2 border border-slate-700 hover:border-indigo-500 hover:text-white bg-slate-900 hover:bg-slate-900 rounded-lg text-xs font-semibold transition"
                >
                  Launch Comparison
                </button>
              </div>
            </div>

            {/* History panel */}
            <div className="bg-slate-900/40 rounded-lg border border-slate-800 p-6 flex flex-col h-[480px]">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-indigo-400" />
                  <h3 className="font-bold text-sm text-white uppercase tracking-wider font-mono">Recent Scans</h3>
                </div>
                <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px] font-mono">
                  {history.length} Cached
                </span>
              </div>

              <div className="flex-1 overflow-y-auto space-y-3 pr-1">
                {history.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-slate-600 text-xs text-center p-4">
                    <BookOpen className="w-8 h-8 mb-2 stroke-1 text-slate-700" />
                    <span>No reports cached yet. Submit a repository URL above to generate your first audit.</span>
                  </div>
                ) : (
                  history.map((h, i) => (
                    <div 
                      key={h.id || i}
                      onClick={() => handleScan(h.repo_url)}
                      className="p-3 bg-slate-950/60 hover:bg-slate-900 border border-slate-800/80 hover:border-slate-700 rounded-md cursor-pointer transition flex items-center justify-between group"
                    >
                      <div className="space-y-1 min-w-0 pr-2">
                        <span className="font-bold text-xs text-slate-200 block truncate group-hover:text-indigo-400 transition">
                          {h.owner}/{h.repo_name}
                        </span>
                        <span className="text-[10px] text-slate-500 block font-mono">
                          {new Date(h.timestamp).toLocaleDateString()}
                        </span>
                      </div>
                      <div className={`px-2.5 py-1 text-xs font-bold font-mono rounded border flex items-center justify-center ${getScoreBg(h.score)}`}>
                        {h.score}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* VIEW 2: INTERACTIVE SKELETON LOADER */}
        {view === "loading" && (
          <div className="flex-1 flex flex-col items-center justify-center py-20 text-center space-y-8">
            <div className="relative w-24 h-24 flex items-center justify-center">
              <div className="absolute inset-0 border-4 border-slate-800 rounded-full" />
              <div className="absolute inset-0 border-4 border-t-indigo-500 border-r-indigo-500/20 border-b-indigo-500/10 border-l-transparent rounded-full animate-spin" />
              <Github className="w-8 h-8 text-indigo-400 animate-pulse" />
            </div>

            <div className="space-y-2 max-w-md">
              <h2 className="text-2xl font-black text-white">{loaderMessage}</h2>
              <p className="text-slate-400 text-sm animate-pulse">{loaderSubMessage}</p>
            </div>

            {/* Visual Shimmer Bar */}
            <div className="w-64 h-1.5 bg-slate-800 rounded-full overflow-hidden relative">
              <div className="absolute top-0 bottom-0 left-0 bg-gradient-to-r from-indigo-500 to-cyan-400 w-1/2 rounded-full animate-shimmer animate-pulse" style={{ width: "200%" }} />
            </div>

            <span className="text-[10px] text-slate-500 uppercase tracking-widest font-mono">
              Gathering API nodes concurrently • OSV CVE scanner • PDF Generator
            </span>
          </div>
        )}

        {/* VIEW 3: COMPREHENSIVE INTELLIGENCE REPORT DASHBOARD */}
        {view === "report" && report && (
          <div className="flex-1 flex flex-col space-y-6 py-4">
            
            {/* Repo Summary Header */}
            <div className="p-6 bg-slate-900/50 rounded-lg border border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-slate-800 rounded-md text-indigo-400 border border-slate-700">
                  <Github className="w-8 h-8" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-2xl font-extrabold text-white">{report.metadata.owner}/{report.metadata.name}</h2>
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-[10px] text-slate-400 uppercase font-mono tracking-wider border border-slate-700">
                      {report.metadata.license || "NO LICENSE"}
                    </span>
                  </div>
                  <p className="text-sm text-slate-400 mt-1 max-w-xl line-clamp-1">{report.metadata.description || "No description provided."}</p>
                  
                  {/* Stars / Forks / Issues Pill Bar */}
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500 font-mono mt-2">
                    <span>★ {report.metadata.stars.toLocaleString()} stars</span>
                    <span>⑂ {report.metadata.forks.toLocaleString()} forks</span>
                    <span>☉ {report.metadata.open_issues.toLocaleString()} issues</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-3">
                <button
                  onClick={handleDownloadPDF}
                  className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 font-bold rounded-md text-white text-xs flex items-center gap-2 transition hover:shadow-lg shadow-indigo-900/20 active:scale-95"
                >
                  <Download className="w-4 h-4" /> Download PDF Report
                </button>
                <button
                  onClick={() => {
                    setView("compare");
                    setCompareUrlA(report.repo_url);
                    setCompareUrlB("");
                    setCompareResult(null);
                  }}
                  className="px-4 py-2.5 border border-slate-700 hover:border-slate-600 bg-slate-900 hover:text-white rounded-md text-xs font-semibold transition"
                >
                  Compare Repository
                </button>
                <button
                  onClick={() => { setView("landing"); setRepoUrl(""); }}
                  className="px-4 py-2.5 border border-slate-700 hover:border-slate-600 bg-slate-950 hover:text-white rounded-md text-xs font-semibold transition text-slate-400"
                >
                  Scan New Repo
                </button>
              </div>
            </div>

            {/* Scoring Summary & Category grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              
              {/* Overall Score Circle */}
              <div className="bg-slate-900/40 p-6 rounded-lg border border-slate-800 flex flex-col items-center justify-center text-center">
                <span className="text-xs text-slate-400 font-mono uppercase tracking-widest mb-4">Overall Score</span>
                
                <div className="relative w-36 h-36 flex items-center justify-center">
                  <svg className="w-full h-full transform -rotate-90">
                    <circle
                      cx="72"
                      cy="72"
                      r="64"
                      className="score-circle-bg"
                      strokeWidth="8"
                      fill="transparent"
                    />
                    <circle
                      cx="72"
                      cy="72"
                      r="64"
                      className="score-circle-progress"
                      strokeWidth="8"
                      fill="transparent"
                      stroke={report.scores.overall >= 80 ? "#14b8a6" : (report.scores.overall >= 60 ? "#f59e0b" : "#f43f5e")}
                      strokeDasharray={402}
                      strokeDashoffset={402 - (402 * report.scores.overall) / 100}
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute flex flex-col items-center justify-center">
                    <span className="text-4xl font-black text-white leading-none">{report.scores.overall}</span>
                    <span className="text-[10px] text-slate-500 font-mono">/100</span>
                  </div>
                </div>

                <span className={`mt-4 px-3 py-1 text-[10px] font-extrabold uppercase rounded-full border ${getScoreBg(report.scores.overall)}`}>
                  {report.scores.overall >= 80 ? "Grade A — Strong Asset" : (report.scores.overall >= 60 ? "Grade B — Minor Risks" : "Grade C — Critical Debt")}
                </span>
              </div>

              {/* Sub-scores details */}
              <div className="md:col-span-3 bg-slate-900/40 p-6 rounded-lg border border-slate-800 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-center">
                
                {/* Documentation subscore */}
                <div 
                  onClick={() => setActiveTab("docs")}
                  className="p-4 bg-slate-950/60 hover:bg-slate-900 border border-slate-850 hover:border-indigo-500/30 rounded-md cursor-pointer transition space-y-3 group"
                >
                  <div className="flex items-center justify-between">
                    <FileText className="w-5 h-5 text-indigo-400" />
                    <span className="text-xs text-slate-500 font-mono">30% wt</span>
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 block">Documentation</span>
                    <span className="text-xl font-bold text-slate-100 group-hover:text-indigo-400 transition">{report.scores.documentation}/100</span>
                  </div>
                  <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                    <div className="bg-indigo-500 h-full" style={{ width: `${report.scores.documentation}%` }} />
                  </div>
                </div>

                {/* Security subscore */}
                <div 
                  onClick={() => setActiveTab("security")}
                  className="p-4 bg-slate-950/60 hover:bg-slate-900 border border-slate-850 hover:border-indigo-500/30 rounded-md cursor-pointer transition space-y-3 group"
                >
                  <div className="flex items-center justify-between">
                    <ShieldAlert className="w-5 h-5 text-rose-400" />
                    <span className="text-xs text-slate-500 font-mono">30% wt</span>
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 block">Security Scans</span>
                    <span className="text-xl font-bold text-slate-100 group-hover:text-rose-400 transition">{report.scores.security}/100</span>
                  </div>
                  <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                    <div className="bg-rose-500 h-full" style={{ width: `${report.scores.security}%` }} />
                  </div>
                </div>

                {/* Commits subscore */}
                <div 
                  onClick={() => setActiveTab("commits")}
                  className="p-4 bg-slate-950/60 hover:bg-slate-900 border border-slate-850 hover:border-indigo-500/30 rounded-md cursor-pointer transition space-y-3 group"
                >
                  <div className="flex items-center justify-between">
                    <GitCommit className="w-5 h-5 text-cyan-400" />
                    <span className="text-xs text-slate-500 font-mono">20% wt</span>
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 block">Commit History</span>
                    <span className="text-xl font-bold text-slate-100 group-hover:text-cyan-400 transition">{report.scores.commits}/100</span>
                  </div>
                  <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                    <div className="bg-cyan-500 h-full" style={{ width: `${report.scores.commits}%` }} />
                  </div>
                </div>

                {/* Structure subscore */}
                <div 
                  onClick={() => setActiveTab("structure")}
                  className="p-4 bg-slate-950/60 hover:bg-slate-900 border border-slate-850 hover:border-indigo-500/30 rounded-md cursor-pointer transition space-y-3 group"
                >
                  <div className="flex items-center justify-between">
                    <FolderGit2 className="w-5 h-5 text-blue-400" />
                    <span className="text-xs text-slate-500 font-mono">20% wt</span>
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 block">Project Hygiene</span>
                    <span className="text-xl font-bold text-slate-100 group-hover:text-blue-400 transition">{report.scores.structure}/100</span>
                  </div>
                  <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                    <div className="bg-blue-500 h-full" style={{ width: `${report.scores.structure}%` }} />
                  </div>
                </div>

              </div>
            </div>

            {/* Tabs Selector Navigation */}
            <div className="flex border-b border-slate-800 overflow-x-auto pb-px">
              {[
                { id: "overview", label: "Executive Summary", icon: Award },
                { id: "security", label: `Security (${report.security.secrets.length + report.security.vulnerabilities.length})`, icon: ShieldAlert },
                { id: "docs", label: "Documentation", icon: FileText },
                { id: "commits", label: "Git Analytics", icon: GitCommit },
                { id: "structure", label: "Code Hygiene", icon: FolderGit2 },
                { id: "roadmap", label: `Fix-It Roadmap (${report.roadmap.length})`, icon: TrendingUp },
                { id: "chat", label: "Chat", icon: MessageSquare },
                { id: "insights", label: "Insights", icon: Lightbulb },
              ].map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`flex items-center gap-2 px-5 py-3 border-b-2 text-sm font-semibold whitespace-nowrap transition-all ${
                      activeTab === tab.id
                        ? "border-indigo-500 text-indigo-400 bg-indigo-950/5"
                        : "border-transparent text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                );
              })}
            </div>

            {/* TAB CONTENTS */}
            <div className="min-h-[300px]">

              {activeTab === "insights" && (
                <div className="max-w-4xl mx-auto space-y-4">
                  <div className="p-5 rounded-lg bg-slate-900/40 border border-slate-800 flex items-center gap-3">
                    <Lightbulb className="w-5 h-5 text-amber-400" />
                    <div><h3 className="font-bold text-white">Repository Insights</h3><p className="text-xs text-slate-400 mt-1">Actionable observations generated from this saved analysis.</p></div>
                  </div>
                  {isLoadingInsights ? <div className="p-8 text-center text-sm text-slate-400 animate-pulse">Generating insights from the saved analysis…</div> : insights.map((insight, index) => {
                    const Icon = insight.type === "warning" ? AlertTriangle : insight.type === "good" ? CheckCircle2 : Info;
                    const color = insight.type === "warning" ? "text-rose-400 border-rose-500/20 bg-rose-500/5" : insight.type === "good" ? "text-emerald-400 border-emerald-500/20 bg-emerald-500/5" : "text-cyan-400 border-cyan-500/20 bg-cyan-500/5";
                    return <div key={index} className={`p-4 rounded-lg border flex gap-3 ${color}`}><Icon className="w-5 h-5 shrink-0 mt-0.5" /><div className="min-w-0"><p className="text-sm text-slate-200">{insight.message}</p>{insight.file && <span className="inline-block mt-2 px-2 py-0.5 rounded border border-slate-700 bg-slate-950 text-[10px] font-mono text-slate-300">{insight.file}</span>}</div></div>;
                  })}
                  {!isLoadingInsights && insights.length === 0 && <div className="p-8 text-center text-sm text-slate-500 border border-slate-800 rounded-lg">No notable insights were generated for this analysis.</div>}
                </div>
              )}

              {/* TAB: REPOSITORY CHAT */}
              {activeTab === "chat" && (
                <div className="max-w-4xl mx-auto bg-slate-900/40 border border-slate-800 rounded-lg overflow-hidden">
                  <div className="p-5 border-b border-slate-800 flex items-start gap-3">
                    <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400">
                      <MessageSquare className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-white">Chat with {report.metadata.name}</h3>
                      <p className="text-xs text-slate-400 mt-1">Ask about the saved repository structure, configuration, README, and key entry files.</p>
                    </div>
                  </div>

                  <div className="min-h-[330px] max-h-[520px] overflow-y-auto p-5 space-y-4 bg-slate-950/30">
                    {chatMessages.length === 0 ? (
                      <div className="h-64 flex flex-col items-center justify-center text-center px-6">
                        <MessageSquare className="w-10 h-10 text-indigo-400/70 mb-3" />
                        <p className="text-sm font-semibold text-slate-200">Ask a repository-specific question</p>
                        <p className="text-xs text-slate-500 mt-1 max-w-md">Try “Where is the application entry point?” or “How is authentication configured?”</p>
                      </div>
                    ) : (
                      chatMessages.map((message, index) => (
                        <div key={index} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                          <div className={`max-w-[85%] rounded-lg border px-4 py-3 text-sm leading-relaxed ${message.role === "user" ? "bg-indigo-600/20 border-indigo-500/30 text-slate-100" : "bg-slate-900 border-slate-800 text-slate-300"}`}>
                            <div className="text-[10px] uppercase tracking-widest font-mono mb-1.5 text-slate-500">
                              {message.role === "user" ? "You" : "DevPilot AI"}
                            </div>
                            <div className="whitespace-pre-wrap">{renderFormattedText(message.content)}</div>
                            {message.role === "assistant" && message.referencedFiles && message.referencedFiles.length > 0 && (
                              <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-slate-800/80">
                                {message.referencedFiles.map((file) => (
                                  <span key={file} className="px-2 py-0.5 rounded border border-cyan-500/20 bg-cyan-500/10 text-cyan-300 text-[10px] font-mono">
                                    {file}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                    {isChatting && (
                      <div className="flex justify-start">
                        <div className="bg-slate-900 border border-slate-800 rounded-lg px-4 py-3 text-xs text-slate-400 animate-pulse">Studying the saved repository context…</div>
                      </div>
                    )}
                  </div>

                  <form onSubmit={handleChatSubmit} className="p-4 border-t border-slate-800 flex gap-3 bg-slate-900/50">
                    <input
                      type="text"
                      value={chatQuestion}
                      onChange={(event) => setChatQuestion(event.target.value)}
                      placeholder="Ask about this repository…"
                      disabled={isChatting}
                      className="flex-1 px-4 py-3 bg-slate-950 border border-slate-800 rounded-md text-sm text-slate-200 placeholder-slate-600 outline-none focus:border-indigo-500 disabled:opacity-60 transition"
                    />
                    <button
                      type="submit"
                      disabled={!chatQuestion.trim() || isChatting}
                      className="px-4 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed rounded-md text-white transition"
                      aria-label="Send chat message"
                    >
                      <Send className="w-4 h-4" />
                    </button>
                  </form>
                </div>
              )}
              
              {/* TAB: OVERVIEW */}
              {activeTab === "overview" && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* AI audit report details */}
                  <div className="lg:col-span-2 bg-slate-900/40 border border-slate-800 rounded-lg p-6 space-y-4">
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                      <Award className="w-5 h-5 text-indigo-400" />
                      Due Diligence & Valuation Audit
                    </h3>
                    
                    {/* Render AI Summary content directly */}
                    <div className="prose prose-invert prose-sm max-w-none text-slate-300 leading-relaxed space-y-4 font-sans border-t border-slate-800/80 pt-4">
                      {report.ai_assessment.split("\n\n").map((para: string, idx: number) => {
                        if (para.startsWith("###")) {
                          return (
                            <h4 key={idx} className="text-slate-100 font-bold text-base mt-6 mb-2 border-l-2 border-indigo-500 pl-3">
                              {renderFormattedText(para.replace("###", "").trim())}
                            </h4>
                          );
                        }
                        if (para.startsWith("####")) {
                          return (
                            <h5 key={idx} className="text-cyan-400 font-semibold text-sm mt-4 mb-1 pl-3">
                              {renderFormattedText(para.replace("####", "").trim())}
                            </h5>
                          );
                        }
                        if (para.includes("-") || para.includes("•")) {
                          // List item elements
                          const items = para.split("\n").filter(li => li.trim());
                          return (
                            <ul key={idx} className="list-disc pl-5 space-y-1.5 my-2">
                              {items.map((item, i) => (
                                <li key={i} className="text-slate-300 text-sm">
                                  {renderFormattedText(item.replace(/^[\s\-\*•]+/, ""))}
                                </li>
                              ))}
                            </ul>
                          );
                        }
                        return (
                          <p key={idx} className="text-sm">
                            {renderFormattedText(para)}
                          </p>
                        );
                      })}
                    </div>
                  </div>

                  {/* Languages breakdown & Quick Roadmap summary */}
                  <div className="space-y-6">
                    
                    {/* Primary Languages Card */}
                    <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6">
                      <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono mb-4">Technology Stack</h3>
                      <div className="space-y-3">
                        {Object.entries(report.metadata.languages).map(([lang, pct]: any) => (
                          <div key={lang} className="space-y-1">
                            <div className="flex justify-between text-xs font-mono">
                              <span className="text-slate-300 font-semibold">{lang}</span>
                              <span className="text-slate-500">{pct}%</span>
                            </div>
                            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                              <div className="bg-gradient-to-r from-indigo-500 to-cyan-500 h-full" style={{ width: `${pct}%` }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Quick fixes roadmap summary */}
                    <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">Impact Fixes</h3>
                        <span className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 text-[10px] font-mono border border-indigo-500/20">
                          +{report.roadmap.reduce((acc: number, curr: any) => acc + curr.estimated_score_gain, 0)} pts Gain
                        </span>
                      </div>
                      
                      <div className="space-y-3">
                        {report.roadmap.slice(0, 3).map((item: any) => (
                          <div 
                            key={item.id}
                            onClick={() => setActiveTab("roadmap")}
                            className="p-3 bg-slate-950/50 hover:bg-slate-950 border border-slate-800 hover:border-slate-700 rounded-md cursor-pointer transition flex items-center justify-between"
                          >
                            <div className="min-w-0 pr-2">
                              <span className="text-xs font-bold text-slate-200 block truncate">{item.title}</span>
                              <span className="text-[10px] text-slate-500 font-mono mt-0.5 block">Potential Score Gain: +{item.estimated_score_gain} pts</span>
                            </div>
                            <span className={`px-2 py-0.5 rounded text-[9px] font-bold border uppercase tracking-wider ${getSeverityColor(item.severity)}`}>
                              {item.severity}
                            </span>
                          </div>
                        ))}
                        {report.roadmap.length > 3 && (
                          <button 
                            onClick={() => setActiveTab("roadmap")}
                            className="w-full py-2 bg-slate-950 border border-slate-800 hover:border-slate-700 rounded-md text-xs text-slate-400 font-semibold text-center hover:text-white transition"
                          >
                            View All {report.roadmap.length} Roadmap Fixes
                          </button>
                        )}
                      </div>
                    </div>

                  </div>
                </div>
              )}

              {/* TAB: SECURITY */}
              {activeTab === "security" && (
                <div className="space-y-6">
                  
                  {/* Security score details banner */}
                  <div className="p-5 rounded-lg bg-slate-900/40 border border-slate-800 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div>
                      <h3 className="font-extrabold text-lg text-white">Security Vulnerability Assessment</h3>
                      <p className="text-slate-400 text-xs mt-1">Regex scanner for private keys, AWS tokens, and OSV API package vulnerability queries.</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <span className="text-[10px] text-slate-500 font-mono uppercase block">Security Grade</span>
                        <span className={`text-2xl font-black ${getScoreColor(report.scores.security)}`}>{report.scores.security}/100</span>
                      </div>
                    </div>
                  </div>

                  {/* Exposed Secrets */}
                  <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 space-y-4">
                    <h3 className="text-md font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
                      <ShieldAlert className="w-5 h-5 text-rose-500" />
                      Hardcoded Credentials & Leaked Secrets
                    </h3>

                    {report.security.secrets.length === 0 ? (
                      <div className="p-6 bg-indigo-950/10 rounded-md border border-indigo-500/20 text-center flex flex-col items-center">
                        <ShieldCheck className="w-8 h-8 text-indigo-400 mb-2" />
                        <span className="text-indigo-400 text-sm font-bold">Zero Leaks Detected</span>
                        <span className="text-slate-400 text-xs mt-1">No API keys, Firebase secrets, JWT payloads, or private certificates were identified in scanned scripts.</span>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {report.security.secrets.map((sec: any, idx: number) => (
                          <div key={idx} className="p-4 bg-rose-950/10 border border-rose-500/20 rounded-md space-y-2">
                            <div className="flex items-center justify-between flex-wrap gap-2 text-xs">
                              <span className="px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/20 text-rose-400 font-bold font-mono">
                                {sec.secret_type}
                              </span>
                              <span className="text-slate-500 font-mono">
                                File: <span className="text-slate-300 font-semibold">{sec.file_path}</span> (Line {sec.line})
                              </span>
                            </div>
                            <pre className="p-3 bg-slate-950 border border-slate-850 rounded-lg text-rose-300 text-xs overflow-x-auto font-mono">
                              <code>{sec.snippet}</code>
                            </pre>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Package Vulnerabilities */}
                  <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 space-y-4">
                    <h3 className="text-md font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
                      <AlertTriangle className="w-5 h-5 text-cyan-500" />
                      Dependency Vulnerability Audit (OSV CVE)
                    </h3>

                    {report.security.vulnerabilities.length === 0 ? (
                      <div className="p-6 bg-indigo-950/10 rounded-md border border-indigo-500/20 text-center flex flex-col items-center">
                        <ShieldCheck className="w-8 h-8 text-indigo-400 mb-2" />
                        <span className="text-indigo-400 text-sm font-bold">All Libraries Patched</span>
                        <span className="text-slate-400 text-xs mt-1">No vulnerable packages were found pinned in requirements.txt or package.json within scanned bounds.</span>
                      </div>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs border-collapse">
                          <thead>
                            <tr className="border-b border-slate-800 text-slate-400 font-mono">
                              <th className="pb-3 pl-2">Package</th>
                              <th className="pb-3">Version</th>
                              <th className="pb-3">Severity</th>
                              <th className="pb-3">CVE Summary</th>
                              <th className="pb-3 pr-2">Patched In</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800/60">
                            {report.security.vulnerabilities.map((vul: any, idx: number) => (
                              <tr key={idx} className="hover:bg-slate-950/50">
                                <td className="py-3 pl-2 font-bold text-slate-200">{vul.package_name}</td>
                                <td className="py-3 font-mono">{vul.current_version}</td>
                                <td className="py-3">
                                  <span className={`px-2 py-0.5 rounded font-bold uppercase text-[9px] border ${getSeverityColor(vul.severity)}`}>
                                    {vul.severity}
                                  </span>
                                </td>
                                <td className="py-3 text-slate-300 max-w-xs truncate" title={vul.description}>
                                  {vul.description}
                                </td>
                                <td className="py-3 pr-2 font-mono text-indigo-400">{vul.patched_version || "N/A"}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>

                  {/* Security Deductions */}
                  {report.security.deductions.length > 0 && (
                    <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6">
                      <h4 className="text-xs text-slate-400 uppercase tracking-widest font-mono mb-3">Security Score Deductions</h4>
                      <div className="space-y-2">
                        {report.security.deductions.map((d: any, idx: number) => (
                          <div key={idx} className="flex gap-2.5 items-start text-xs border-l-2 border-rose-500 pl-4 py-1">
                            <div>
                              <span className="font-extrabold text-rose-400 block">-{d.points} Points</span>
                              <span className="text-slate-300 block mt-0.5">{d.explanation}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* TAB: DOCS */}
              {activeTab === "docs" && (
                <div className="space-y-6">
                  
                  {/* Banner */}
                  <div className="p-5 rounded-lg bg-slate-900/40 border border-slate-800 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div>
                      <h3 className="font-extrabold text-lg text-white">Documentation Scoring & Deduction</h3>
                      <p className="text-slate-400 text-xs mt-1">Validates presence of README content and key operational markdown headings.</p>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] text-slate-500 font-mono uppercase block">Doc Score</span>
                      <span className={`text-2xl font-black ${getScoreColor(report.scores.documentation)}`}>{report.scores.documentation}/100</span>
                    </div>
                  </div>

                  {/* Checklist and Deductions grid */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    
                    {/* Checklist */}
                    <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 space-y-4">
                      <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono border-b border-slate-800 pb-3">
                        README Checklist
                      </h3>
                      
                      <div className="space-y-3.5">
                        {[
                          { label: "README.md Exists", check: report.documentation.readme_exists },
                          { label: "Opening Description", check: report.documentation.has_description },
                          { label: "Installation Instructions", check: report.documentation.has_installation },
                          { label: "Usage/Configuration Examples", check: report.documentation.has_usage },
                          { label: "Live Demo Links", check: report.documentation.has_demo },
                          { label: "Visual Screenshots/GIFs", check: report.documentation.has_screenshots },
                          { label: "API Reference docs", check: report.documentation.has_api_docs },
                          { label: "Contribution Guideline", check: report.documentation.has_contribution_guide },
                          { label: "License declarations", check: report.documentation.has_license_info },
                        ].map((item, idx) => (
                          <div key={idx} className="flex items-center justify-between text-xs">
                            <span className="text-slate-350">{item.label}</span>
                            {item.check ? (
                              <CheckCircle2 className="w-4.5 h-4.5 text-indigo-400 shrink-0" />
                            ) : (
                              <XCircle className="w-4.5 h-4.5 text-slate-700 shrink-0" />
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Deductions */}
                    <div className="md:col-span-2 bg-slate-900/40 border border-slate-800 rounded-lg p-6 space-y-4">
                      <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono border-b border-slate-800 pb-3">
                        Audit Deductions Explanation
                      </h3>

                      {report.documentation.deductions.length === 0 ? (
                        <div className="p-8 text-center flex flex-col items-center justify-center h-48">
                          <CheckCircle2 className="w-10 h-10 text-indigo-400 mb-2" />
                          <span className="text-indigo-400 font-bold text-sm">Perfect Score!</span>
                          <span className="text-slate-400 text-xs mt-1">The README contains all checked onboarding references and details.</span>
                        </div>
                      ) : (
                        <div className="space-y-4">
                          {report.documentation.deductions.map((d: any, idx: number) => (
                            <div key={idx} className="p-3 bg-slate-950 border border-slate-850 rounded-md flex gap-3 items-start">
                              <span className="px-2.5 py-1 rounded bg-rose-500/10 text-rose-400 font-extrabold font-mono text-[10px] shrink-0 border border-rose-500/15">
                                -{d.points} pts
                              </span>
                              <div className="text-xs">
                                <span className="font-extrabold text-slate-200 block">Deduction: {d.explanation.split('.')[0]}.</span>
                                <span className="text-slate-400 block mt-1">{d.explanation}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                  </div>
                </div>
              )}

              {/* TAB: COMMITS */}
              {activeTab === "commits" && (
                <div className="space-y-6">
                  
                  {/* Score banner */}
                  <div className="p-5 rounded-lg bg-slate-900/40 border border-slate-800 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div>
                      <h3 className="font-extrabold text-lg text-white">Commit Quality & Dev Frequency</h3>
                      <p className="text-slate-400 text-xs mt-1">Examines git log conventions, flags poor descriptions (wip/fix), and charts historical activity.</p>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] text-slate-500 font-mono uppercase block">Commit Grade</span>
                      <span className={`text-2xl font-black ${getScoreColor(report.scores.commits)}`}>{report.scores.commits}/100</span>
                    </div>
                  </div>

                  {/* Summary grid */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-md space-y-1">
                      <span className="text-[10px] text-slate-500 uppercase tracking-widest font-mono block">Analyzed Commits</span>
                      <span className="text-2xl font-bold text-white">{report.commits.total_commits}</span>
                    </div>
                    <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-md space-y-1">
                      <span className="text-[10px] text-slate-500 uppercase tracking-widest font-mono block">Weekly Velocity</span>
                      <span className="text-2xl font-bold text-white">{report.commits.avg_commits_per_week} / wk</span>
                    </div>
                    <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-md space-y-1">
                      <span className="text-[10px] text-slate-500 uppercase tracking-widest font-mono block">Active Contributors</span>
                      <span className="text-2xl font-bold text-white flex items-center gap-1">
                        <User className="w-5 h-5 text-indigo-400" />
                        {report.commits.contributors_count}
                      </span>
                    </div>
                    <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-md space-y-1">
                      <span className="text-[10px] text-slate-500 uppercase tracking-widest font-mono block">Generic Messages</span>
                      <span className={`text-2xl font-bold ${report.commits.poor_messages_percentage > 20 ? "text-rose-400" : "text-indigo-400"}`}>
                        {report.commits.poor_messages_percentage}%
                      </span>
                    </div>
                  </div>

                  {/* Chart and generic logs */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    
                    {/* Line Chart */}
                    <div className="md:col-span-2 bg-slate-900/40 border border-slate-800 rounded-lg p-6 space-y-4">
                      <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">Recent Commit Timeline</h3>
                      <div className="h-64">
                        {report.commits.timeline.length === 0 ? (
                          <div className="h-full flex items-center justify-center text-xs text-slate-500">
                            No timeline data available.
                          </div>
                        ) : (
                          <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={report.commits.timeline} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                              <XAxis dataKey="date" stroke="#64748b" fontSize={10} />
                              <YAxis stroke="#64748b" fontSize={10} />
                              <Tooltip contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #1e293b", color: "#f1f5f9", fontSize: "12px", borderRadius: "8px" }} />
                              <Line type="monotone" dataKey="count" stroke="#14b8a6" strokeWidth={2.5} activeDot={{ r: 6 }} dot={false} />
                            </LineChart>
                          </ResponsiveContainer>
                        )}
                      </div>
                    </div>

                    {/* Generic Commits Warning Log */}
                    <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 space-y-4">
                      <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono border-b border-slate-800 pb-3">
                        Identified Generic Commits
                      </h3>

                      {report.commits.poor_messages.length === 0 ? (
                        <div className="p-4 text-center h-48 flex flex-col items-center justify-center text-xs text-slate-500">
                          <CheckCircle2 className="w-8 h-8 text-indigo-400 mb-2" />
                          <span>No lazy messages flagged! High version control descriptive discipline.</span>
                        </div>
                      ) : (
                        <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                          {report.commits.poor_messages.map((m: any, idx: number) => (
                            <div key={idx} className="p-2 bg-slate-950 border border-slate-850 rounded-lg space-y-1">
                              <div className="flex items-center justify-between text-[10px]">
                                <span className="font-mono text-indigo-400 font-semibold">{m.hash}</span>
                                <span className="text-slate-500">{m.author}</span>
                              </div>
                              <span className="text-xs text-slate-350 block font-mono truncate" title={m.message}>
                                "{m.message}"
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                  </div>
                </div>
              )}

              {/* TAB: HYGIENE STRUCTURE */}
              {activeTab === "structure" && (
                <div className="space-y-6">
                  
                  {/* Banner */}
                  <div className="p-5 rounded-lg bg-slate-900/40 border border-slate-800 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div>
                      <h3 className="font-extrabold text-lg text-white">Repository Organization & Hygiene</h3>
                      <p className="text-slate-400 text-xs mt-1">Audits the directory framework for docker support, CI setups, licenses, and tests files.</p>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] text-slate-500 font-mono uppercase block">Hygiene Grade</span>
                      <span className={`text-2xl font-black ${getScoreColor(report.scores.structure)}`}>{report.scores.structure}/100</span>
                    </div>
                  </div>

                  {/* Checklist / Files found */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    
                    {/* Structure Checklist */}
                    <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 space-y-4">
                      <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono border-b border-slate-800 pb-3">
                        Hygiene Checklist
                      </h3>
                      <div className="space-y-3">
                        {[
                          { label: "Gitignore File", check: report.structure.has_gitignore },
                          { label: "License File", check: report.structure.has_license },
                          { label: "GitHub Actions workflow", check: report.structure.has_github_actions },
                          { label: "Docker Configurations", check: report.structure.has_docker },
                          { label: "Automated Tests Folder/Scripts", check: report.structure.has_tests },
                        ].map((item, idx) => (
                          <div key={idx} className="flex items-center justify-between text-xs">
                            <span className="text-slate-350">{item.label}</span>
                            {item.check ? (
                              <CheckCircle2 className="w-4.5 h-4.5 text-indigo-400" />
                            ) : (
                              <XCircle className="w-4.5 h-4.5 text-slate-700" />
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Detected Config files */}
                    <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 space-y-4">
                      <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono border-b border-slate-800 pb-3">
                        Config Files Located
                      </h3>
                      {report.structure.config_files.length === 0 ? (
                        <div className="p-4 text-center text-xs text-slate-500">
                          No standard framework configuration files found in the root.
                        </div>
                      ) : (
                        <div className="flex flex-wrap gap-2">
                          {report.structure.config_files.map((file: string, idx: number) => (
                            <span key={idx} className="px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-slate-300">
                              {file}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Deductions details */}
                    <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 space-y-4">
                      <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono border-b border-slate-800 pb-3">
                        Structure Deductions
                      </h3>
                      {report.structure.deductions.length === 0 ? (
                        <div className="p-4 text-center h-28 flex flex-col items-center justify-center text-xs text-slate-500">
                          <CheckCircle2 className="w-8 h-8 text-indigo-400 mb-1" />
                          <span>No structural defects found.</span>
                        </div>
                      ) : (
                        <div className="space-y-3 overflow-y-auto max-h-48 pr-1">
                          {report.structure.deductions.map((d: any, idx: number) => (
                            <div key={idx} className="border-l-2 border-rose-500 pl-3 text-xs">
                              <span className="font-bold text-slate-200 block">-{d.points} pts</span>
                              <span className="text-slate-400 block mt-0.5">{d.explanation}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                  </div>
                </div>
              )}

              {/* TAB: FIXED ROADMAP */}
              {activeTab === "roadmap" && (
                <div className="space-y-6">
                  
                  <div className="p-5 rounded-lg bg-slate-900/40 border border-slate-800">
                    <h3 className="font-extrabold text-lg text-white">Impact-Ranked Fix-It Roadmap</h3>
                    <p className="text-slate-400 text-xs mt-1">Issues are ranked by score gain impact. Execute these changes to repair technical debt and boost codebase health.</p>
                  </div>

                  {report.roadmap.length === 0 ? (
                    <div className="p-12 text-center bg-slate-900/20 border border-slate-800 rounded-lg flex flex-col items-center">
                      <CheckCircle2 className="w-12 h-12 text-indigo-400 mb-2" />
                      <h4 className="text-indigo-400 font-extrabold text-lg">Congratulations!</h4>
                      <p className="text-slate-400 text-sm mt-1 max-w-md">No action items required. The repository scores perfectly in all checked categories.</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {report.roadmap.map((item: any) => (
                        <details 
                          key={item.id} 
                          className="group bg-slate-900/30 border border-slate-800 hover:border-slate-700 rounded-lg transition"
                        >
                          <summary className="flex items-center justify-between p-5 cursor-pointer list-none select-none">
                            <div className="flex items-center gap-3 min-w-0 pr-4">
                              <span className="font-mono font-bold text-xs text-slate-500 shrink-0">{item.id}</span>
                              <span className="font-bold text-sm text-slate-200 block truncate hover:text-indigo-400 transition">
                                {item.title}
                              </span>
                            </div>
                            
                            <div className="flex items-center gap-2.5 shrink-0">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold font-mono border uppercase tracking-wider ${getSeverityColor(item.severity)}`}>
                                {item.severity}
                              </span>
                              <span className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/25 text-[10px] font-bold font-mono">
                                +{item.estimated_score_gain} pts
                              </span>
                              <ChevronRight className="w-4 h-4 text-slate-500 group-open:rotate-90 transition-transform" />
                            </div>
                          </summary>
                          
                          <div className="p-5 border-t border-slate-850/60 bg-slate-950/40 rounded-b-2xl space-y-4 text-xs leading-relaxed">
                            
                            {/* Metadata row */}
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 font-mono pb-3 border-b border-slate-850">
                              <div>
                                <span className="text-slate-500 block uppercase text-[10px] tracking-wider">Complexity</span>
                                <span className="text-slate-350 font-bold block mt-0.5">{item.difficulty}</span>
                              </div>
                              <div>
                                <span className="text-slate-500 block uppercase text-[10px] tracking-wider">Est. Effort Time</span>
                                <span className="text-slate-355 font-bold block mt-0.5">{item.time_estimate}</span>
                              </div>
                              <div>
                                <span className="text-slate-500 block uppercase text-[10px] tracking-wider">Target Domain</span>
                                <span className="text-slate-350 font-bold block mt-0.5">{item.category}</span>
                              </div>
                              <div>
                                <span className="text-slate-500 block uppercase text-[10px] tracking-wider">Exposed Files</span>
                                <span className="text-slate-350 font-semibold block mt-0.5 truncate">
                                  {item.files_involved.length > 0 ? item.files_involved[0] : "All repository"}
                                </span>
                              </div>
                            </div>

                            {/* Suggested Fix */}
                            <div className="space-y-2">
                              <span className="font-bold text-slate-200 uppercase font-mono tracking-widest text-[9px] block text-indigo-400">Action Plan Guide:</span>
                              <div className="p-4 bg-slate-950 border border-slate-850 rounded-md text-slate-300 font-mono space-y-1">
                                <span className="flex items-start gap-1">
                                  <CornerDownRight className="w-3.5 h-3.5 mt-0.5 text-indigo-500 shrink-0" />
                                  <span>{item.suggested_fix}</span>
                                </span>
                              </div>
                            </div>
                            
                          </div>
                        </details>
                      ))}
                    </div>
                  )}

                </div>
              )}

            </div>

          </div>
        )}

        {/* VIEW 4: SIDE-BY-SIDE COMPARE SCREEN */}
        {view === "compare" && (
          <div className="flex-1 flex flex-col space-y-6 py-4">
            
            {/* Comparer Inputs Bar */}
            <div className="p-6 bg-slate-900/50 rounded-lg border border-slate-800 space-y-4">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <ArrowRightLeft className="w-5 h-5 text-indigo-400" />
                Compare Repositories Side-by-Side
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-[10px] text-slate-500 font-mono uppercase tracking-wider">Repository A URL</label>
                  <input
                    type="text"
                    placeholder="https://github.com/owner/repository-a"
                    value={compareUrlA}
                    onChange={(e) => setCompareUrlA(e.target.value)}
                    className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-md text-slate-300 placeholder-slate-700 outline-none focus:border-indigo-500 transition text-sm"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] text-slate-500 font-mono uppercase tracking-wider">Repository B URL</label>
                  <input
                    type="text"
                    placeholder="https://github.com/owner/repository-b"
                    value={compareUrlB}
                    onChange={(e) => setCompareUrlB(e.target.value)}
                    className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-md text-slate-300 placeholder-slate-700 outline-none focus:border-indigo-500 transition text-sm"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  onClick={() => { setView("landing"); setCompareUrlA(""); setCompareUrlB(""); setCompareResult(null); }}
                  className="px-4 py-2 border border-slate-850 hover:border-slate-850 bg-slate-950 text-xs font-semibold rounded-lg text-slate-400 hover:text-white transition"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCompare}
                  className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 font-bold rounded-lg text-white text-xs transition"
                >
                  Compile Comparison
                </button>
              </div>
            </div>

            {/* Comparison results tables */}
            {compareResult && (
              <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 space-y-6">
                <h3 className="text-lg font-bold text-white uppercase tracking-wider font-mono border-b border-slate-800 pb-3">
                  Scorecard Comparison Table
                </h3>
                
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-500 font-mono">
                        <th className="pb-3 pl-2">Feature / Metric</th>
                        <th className="pb-3 text-center text-indigo-400 font-bold">{compareResult.repository_a.metadata.owner}/{compareResult.repository_a.metadata.name}</th>
                        <th className="pb-3 text-center text-indigo-400 font-bold">{compareResult.repository_b.metadata.owner}/{compareResult.repository_b.metadata.name}</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/50">
                      
                      {/* Overall Score */}
                      <tr className="hover:bg-slate-950/20 font-bold">
                        <td className="py-4 pl-2 text-slate-350">Overall Score</td>
                        <td className="py-4 text-center">
                          <span className={`px-3 py-1 font-mono rounded border ${getScoreBg(compareResult.repository_a.scores.overall)}`}>
                            {compareResult.repository_a.scores.overall} / 100
                          </span>
                        </td>
                        <td className="py-4 text-center">
                          <span className={`px-3 py-1 font-mono rounded border ${getScoreBg(compareResult.repository_b.scores.overall)}`}>
                            {compareResult.repository_b.scores.overall} / 100
                          </span>
                        </td>
                      </tr>

                      {/* Security Subscore */}
                      <tr className="hover:bg-slate-950/20">
                        <td className="py-3.5 pl-2 text-slate-400">Security & Secrets Grade</td>
                        <td className={`py-3.5 text-center font-bold font-mono ${getScoreColor(compareResult.repository_a.scores.security)}`}>{compareResult.repository_a.scores.security}</td>
                        <td className={`py-3.5 text-center font-bold font-mono ${getScoreColor(compareResult.repository_b.scores.security)}`}>{compareResult.repository_b.scores.security}</td>
                      </tr>

                      {/* Docs Subscore */}
                      <tr className="hover:bg-slate-950/20">
                        <td className="py-3.5 pl-2 text-slate-400">Documentation Grade</td>
                        <td className={`py-3.5 text-center font-bold font-mono ${getScoreColor(compareResult.repository_a.scores.documentation)}`}>{compareResult.repository_a.scores.documentation}</td>
                        <td className={`py-3.5 text-center font-bold font-mono ${getScoreColor(compareResult.repository_b.scores.documentation)}`}>{compareResult.repository_b.scores.documentation}</td>
                      </tr>

                      {/* Commits Subscore */}
                      <tr className="hover:bg-slate-950/20">
                        <td className="py-3.5 pl-2 text-slate-400">Commit History & Velocity</td>
                        <td className={`py-3.5 text-center font-bold font-mono ${getScoreColor(compareResult.repository_a.scores.commits)}`}>{compareResult.repository_a.scores.commits}</td>
                        <td className={`py-3.5 text-center font-bold font-mono ${getScoreColor(compareResult.repository_b.scores.commits)}`}>{compareResult.repository_b.scores.commits}</td>
                      </tr>

                      {/* Structure Subscore */}
                      <tr className="hover:bg-slate-950/20">
                        <td className="py-3.5 pl-2 text-slate-400">Project Hygiene & Actions</td>
                        <td className={`py-3.5 text-center font-bold font-mono ${getScoreColor(compareResult.repository_a.scores.structure)}`}>{compareResult.repository_a.scores.structure}</td>
                        <td className={`py-3.5 text-center font-bold font-mono ${getScoreColor(compareResult.repository_b.scores.structure)}`}>{compareResult.repository_b.scores.structure}</td>
                      </tr>

                      {/* Stars count */}
                      <tr className="hover:bg-slate-950/20 font-mono">
                        <td className="py-3.5 pl-2 text-slate-400">GitHub Stars</td>
                        <td className="py-3.5 text-center text-slate-200">{compareResult.repository_a.metadata.stars.toLocaleString()}</td>
                        <td className="py-3.5 text-center text-slate-200">{compareResult.repository_b.metadata.stars.toLocaleString()}</td>
                      </tr>

                      {/* Forks count */}
                      <tr className="hover:bg-slate-950/20 font-mono">
                        <td className="py-3.5 pl-2 text-slate-400">Forks Count</td>
                        <td className="py-3.5 text-center text-slate-200">{compareResult.repository_a.metadata.forks.toLocaleString()}</td>
                        <td className="py-3.5 text-center text-slate-200">{compareResult.repository_b.metadata.forks.toLocaleString()}</td>
                      </tr>

                      {/* Open Issues */}
                      <tr className="hover:bg-slate-950/20 font-mono">
                        <td className="py-3.5 pl-2 text-slate-400">Open Issues</td>
                        <td className="py-3.5 text-center text-slate-200">{compareResult.repository_a.metadata.open_issues.toLocaleString()}</td>
                        <td className="py-3.5 text-center text-slate-200">{compareResult.repository_b.metadata.open_issues.toLocaleString()}</td>
                      </tr>

                      {/* Exposed secrets */}
                      <tr className="hover:bg-slate-950/20 font-mono">
                        <td className="py-3.5 pl-2 text-slate-400">Hardcoded Secret Leaks</td>
                        <td className={`py-3.5 text-center font-bold ${compareResult.repository_a.security.secrets.length > 0 ? "text-rose-400" : "text-slate-400"}`}>
                          {compareResult.repository_a.security.secrets.length}
                        </td>
                        <td className={`py-3.5 text-center font-bold ${compareResult.repository_b.security.secrets.length > 0 ? "text-rose-400" : "text-slate-400"}`}>
                          {compareResult.repository_b.security.secrets.length}
                        </td>
                      </tr>

                      {/* Vuln packages */}
                      <tr className="hover:bg-slate-950/20 font-mono">
                        <td className="py-3.5 pl-2 text-slate-400">OSV Vulnerabilities (CVE)</td>
                        <td className={`py-3.5 text-center font-bold ${compareResult.repository_a.security.vulnerabilities.length > 0 ? "text-rose-400" : "text-slate-400"}`}>
                          {compareResult.repository_a.security.vulnerabilities.length}
                        </td>
                        <td className={`py-3.5 text-center font-bold ${compareResult.repository_b.security.vulnerabilities.length > 0 ? "text-rose-400" : "text-slate-400"}`}>
                          {compareResult.repository_b.security.vulnerabilities.length}
                        </td>
                      </tr>

                      {/* Roadmap Items count */}
                      <tr className="hover:bg-slate-950/20 font-mono">
                        <td className="py-3.5 pl-2 text-slate-400">Roadmap Action Items</td>
                        <td className="py-3.5 text-center text-slate-200">{compareResult.repository_a.roadmap.length}</td>
                        <td className="py-3.5 text-center text-slate-200">{compareResult.repository_b.roadmap.length}</td>
                      </tr>

                      {/* Quick links */}
                      <tr className="hover:bg-slate-950/20">
                        <td className="py-3.5 pl-2 text-slate-400">Quick Actions</td>
                        <td className="py-3.5 text-center">
                          <button
                            onClick={() => { setReport(compareResult.repository_a); setView("report"); setActiveTab("overview"); }}
                            className="px-3 py-1 bg-slate-950 hover:bg-slate-900 border border-slate-805 hover:border-indigo-500 rounded text-[10px] text-indigo-400 transition"
                          >
                            Load Report A
                          </button>
                        </td>
                        <td className="py-3.5 text-center">
                          <button
                            onClick={() => { setReport(compareResult.repository_b); setView("report"); setActiveTab("overview"); }}
                            className="px-3 py-1 bg-slate-950 hover:bg-slate-900 border border-slate-805 hover:border-indigo-500 rounded text-[10px] text-indigo-400 transition"
                          >
                            Load Report B
                          </button>
                        </td>
                      </tr>

                    </tbody>
                  </table>
                </div>
              </div>
            )}

          </div>
        )}

      </main>

      {/* Footer copyright */}
      <footer className="border-t border-slate-900 bg-slate-950 py-6 px-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-2">
          <span>&copy; {new Date().getFullYear()} DevPilot AI.</span>
          <span className="font-mono text-[10px] text-slate-600">
            Engine Version 1.0.0 (ReportLab, FastAPI, SQLite)
          </span>
        </div>
      </footer>

      {/* Floating TOAST Notifications */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 max-w-sm pointer-events-none">
        <AnimatePresence>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: 30, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
              className={`p-4 rounded-md border shadow-2xl flex items-center gap-2.5 pointer-events-auto ${
                toast.type === "success"
                  ? "bg-indigo-950/90 border-indigo-500/35 text-indigo-300"
                  : toast.type === "error"
                  ? "bg-rose-950/90 border-rose-500/35 text-rose-300"
                  : "bg-slate-900/90 border-slate-800 text-slate-200"
              }`}
            >
              {toast.type === "success" && <CheckCircle2 className="w-4.5 h-4.5 text-indigo-400 shrink-0" />}
              {toast.type === "error" && <XCircle className="w-4.5 h-4.5 text-rose-400 shrink-0" />}
              <span className="text-xs font-semibold">{toast.message}</span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

    </div>
  );
}
