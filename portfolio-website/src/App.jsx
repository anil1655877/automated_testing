import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell 
} from 'recharts';
import { 
  Play, Shield, Database, Cpu, Terminal, Compass, Eye, Download, Mail, CheckCircle, AlertTriangle, Clock, Server, Layers, Layers2, ChevronLeft, ChevronRight, Activity, Zap, RefreshCw, Send, Check
} from 'lucide-react';

// Color Palette
const COLORS = {
  bgSlate: '#0b0f19',
  bgCard: '#131926',
  accentGreen: '#10b981',
  accentBlue: '#3b82f6',
  accentYellow: '#f59e0b',
  accentRed: '#ef4444',
  textWhite: '#f8fafc',
  textMuted: '#94a3b8'
};

const PIE_COLORS = [COLORS.accentBlue, COLORS.accentGreen, COLORS.accentYellow];

export default function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [pipelineStep, setPipelineStep] = useState(0);
  const [healingLogs, setHealingLogs] = useState([]);
  const [healingSelector, setHealingSelector] = useState('button.checkout-btn');
  const [healingSuccess, setHealingSuccess] = useState(false);
  const [carouselIndex, setCarouselIndex] = useState(0);
  const [feedbackSent, setFeedbackSent] = useState(false);
  
  // Charts Mock Data
  const trendData = [
    { name: 'Run 1', Passed: 12, Failed: 3, Skipped: 0 },
    { name: 'Run 2', Passed: 13, Failed: 2, Skipped: 0 },
    { name: 'Run 3', Passed: 14, Failed: 1, Skipped: 0 },
    { name: 'Run 4', Passed: 14, Failed: 1, Skipped: 0 },
    { name: 'Run 5', Passed: 15, Failed: 0, Skipped: 0 },
    { name: 'Run 6', Passed: 13, Failed: 2, Skipped: 0 },
    { name: 'Run 7', Passed: 14, Failed: 0, Skipped: 1 },
    { name: 'Run 8', Passed: 15, Failed: 0, Skipped: 0 },
    { name: 'Run 9', Passed: 14, Failed: 0, Skipped: 1 },
    { name: 'Run 10', Passed: 15, Failed: 0, Skipped: 0 },
  ];

  const categoryData = [
    { name: 'UI Tests', value: 34 },
    { name: 'API Tests', value: 7 },
    { name: 'DB Tests', value: 8 },
  ];

  // Infographic Carousel Files
  const carouselImages = [
    { title: 'Allure Report Dashboard', desc: 'Real-time HTML & Allure visual reporting output.', path: '/screenshots/allure_dashboard.png' },
    { title: 'Historical Regression Trends', desc: 'Run-by-run stability and failure category charts.', path: '/screenshots/historical_trend_chart.png' },
    { title: 'Docker Selenium Grid Scheme', desc: 'Containerized browser node execution details.', path: '/screenshots/docker_execution.png' },
    { title: 'CI/CD Pipeline Flow', desc: 'Automated Jenkins and GitHub Actions validation stages.', path: '/screenshots/ci_cd_pipeline.png' }
  ];

  // Simulate CI/CD run animation
  useEffect(() => {
    let interval;
    if (pipelineRunning) {
      interval = setInterval(() => {
        setPipelineStep((prev) => {
          if (prev >= 4) {
            setPipelineRunning(false);
            return 4;
          }
          return prev + 1;
        });
      }, 2500);
    } else {
      setPipelineStep(0);
    }
    return () => clearInterval(interval);
  }, [pipelineRunning]);

  // Simulate Self Healing Locator Logs
  const triggerSelfHealingSim = () => {
    setHealingSuccess(false);
    setHealingLogs([
      `[INFO] Attempting to locate element using primary: "${healingSelector}"`,
      `[WARN] Element "${healingSelector}" NOT found in DOM. Primary locator failed.`,
      `[INFO] Self-Healing Module Activated. Initiating recovery chain...`,
      `[INFO] Trying Developer Fallback Locator 1: "button[type='submit']" -> Not found.`,
      `[INFO] Trying Auto-Generated Alternative XPath: "//button[contains(text(),'Checkout')]" -> Match found (Confidence: 0.94)`,
      `[INFO] Performing fuzzy text similarity check: Levenshtein distance 3 (Match success).`,
      `[SUCCESS] Element auto-healed at runtime. Click event executed successfully.`
    ]);
    setTimeout(() => {
      setHealingSuccess(true);
    }, 1800);
  };

  return (
    <div className="flex h-screen overflow-hidden text-slate-100 bg-[#0b0f19]">
      
      {/* ── SIDEBAR NAVIGATION ── */}
      <aside className="hidden md:flex flex-col w-64 border-r border-slate-800 bg-[#101622] shrink-0">
        <div className="flex items-center gap-3 p-6 border-b border-slate-800">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-emerald-500/10 text-emerald-400">
            <Cpu className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="font-extrabold text-sm tracking-wider uppercase text-emerald-400">Antigravity AI</h1>
            <p className="text-xs text-slate-500 font-mono">v1.2.0-stable</p>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {[
            { id: 'home', label: 'Dashboard Home', icon: Activity },
            { id: 'features', label: 'Framework Features', icon: Shield },
            { id: 'architecture', label: 'Architecture Overview', icon: Layers },
            { id: 'analytics', label: 'Reporting & Analytics', icon: Clock },
            { id: 'cicd', label: 'CI/CD Pipeline', icon: Play },
            { id: 'docker', label: 'Docker & Workers', icon: Server },
            { id: 'gallery', label: 'Visual Gallery', icon: Eye },
            { id: 'resume', label: 'Resume & Skills', icon: Download },
            { id: 'contact', label: 'Contact Details', icon: Mail },
          ].map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-3 w-full px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                  isActive 
                    ? 'bg-blue-600/15 text-blue-400 border-l-4 border-blue-500' 
                    : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
                }`}
              >
                <Icon className="w-5 h-5" />
                {item.label}
              </button>
            );
          })}
        </nav>

        <div className="p-4 border-t border-slate-800">
          <a 
            href="https://github.com" 
            target="_blank" 
            rel="noreferrer"
            className="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 transition"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" /><path d="M9 18c-4.51 2-5-2-7-2" /></svg>
            GitHub Repository
          </a>
        </div>
      </aside>

      {/* ── MAIN CONTENT CONTAINER ── */}
      <div className="flex flex-col flex-1 h-full overflow-hidden">
        
        {/* ── TOPBAR ── */}
        <header className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-[#0f1522]">
          <div className="flex items-center gap-3">
            <button 
              className="md:hidden p-2 rounded-lg bg-slate-800 text-slate-400 hover:text-slate-200"
              onClick={() => setActiveTab('home')}
            >
              <Layers2 className="w-5 h-5" />
            </button>
            <h2 className="text-lg font-bold tracking-tight text-slate-100 uppercase">
              {activeTab.replace('-', ' ')}
            </h2>
          </div>

          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400">
              <Check className="w-3.5 h-3.5" />
              Build status: Passed
            </span>
            <span className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400">
              Offline AI Mode Fallback
            </span>
          </div>
        </header>

        {/* ── PANEL SLIDER ── */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 space-y-8 bg-[#0b0f19]">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.25 }}
              className="h-full"
            >
              
              {/* ──────────────────────────────────────────────────
                  TAB 1: HOME DASHBOARD
              ────────────────────────────────────────────────── */}
              {activeTab === 'home' && (
                <div className="space-y-6">
                  {/* Hero Box */}
                  <div className="relative overflow-hidden p-6 md:p-8 rounded-2xl border border-slate-800 bg-gradient-to-r from-[#131926] to-[#1e293b]">
                    <div className="max-w-3xl space-y-4">
                      <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 tracking-wide uppercase">
                        Enterprise QA Solution
                      </span>
                      <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white leading-tight">
                        AI-Enhanced Enterprise Test Automation Framework
                      </h1>
                      <p className="text-slate-400 text-sm md:text-base leading-relaxed">
                        A production-grade web UI, API, and database test orchestration platform. Combines parallel execution grids, fuzzy element healing, and an offline-resilient LLM diagnostics engine.
                      </p>
                      <div className="flex flex-wrap gap-3 pt-2">
                        <button 
                          onClick={() => setActiveTab('features')} 
                          className="px-4 py-2 text-sm font-semibold rounded-lg bg-blue-600 hover:bg-blue-500 transition-all shadow-md shadow-blue-900/30"
                        >
                          Explore Features
                        </button>
                        <button 
                          onClick={() => setActiveTab('resume')}
                          className="flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 transition"
                        >
                          <Download className="w-4 h-4" />
                          Resume & Skills
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Core Metrics */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    {[
                      { title: 'Regression Time', val: '7 Mins', label: '84% Run Reduction', icon: Clock, color: 'text-blue-400', bg: 'bg-blue-500/10' },
                      { title: 'Execution Stability', val: '99.8%', label: 'Zero Sleep Flakiness', icon: Shield, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
                      { title: 'Failover Safeties', val: '100% Active', icon: RefreshCw, label: 'Circuit-Breaker Mock fallback', color: 'text-amber-400', bg: 'bg-amber-500/10' },
                      { title: 'Parallel Workers', val: '4 Cores', icon: Cpu, label: 'xdist SQLite coordinate', color: 'text-purple-400', bg: 'bg-purple-500/10' }
                    ].map((m, idx) => {
                      const Icon = m.icon;
                      return (
                        <div key={idx} className="p-5 rounded-xl border border-slate-800 bg-[#131926] space-y-3">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold text-slate-500 uppercase">{m.title}</span>
                            <div className={`p-2 rounded-lg ${m.bg} ${m.color}`}>
                              <Icon className="w-5 h-5" />
                            </div>
                          </div>
                          <div className="space-y-1">
                            <h3 className="text-2xl font-bold text-white tracking-tight">{m.val}</h3>
                            <p className="text-xs text-slate-400">{m.label}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Quick Tech Badge Grid */}
                  <div className="p-6 rounded-xl border border-slate-800 bg-[#131926] space-y-4">
                    <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wide">Enterprise Tech Stack</h3>
                    <div className="flex flex-wrap gap-2">
                      {['Python 3.11', 'Selenium 4.25', 'PyTest 8.3', 'Docker & Compose', 'Selenium Grid', 'MySQL 8.0', 'SQLite Fallback', 'GitHub Actions', 'Jenkins Pipeline', 'Allure Dashboards', 'Faker Data Generator', 'Fuzzy Element Healing', 'circuit-breaker fallback'].map((tech) => (
                        <span key={tech} className="px-3 py-1.5 rounded-lg text-xs font-medium bg-[#1e293b] text-slate-300 border border-slate-800">
                          {tech}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* ──────────────────────────────────────────────────
                  TAB 2: FEATURES GRID
              ────────────────────────────────────────────────── */}
              {activeTab === 'features' && (
                <div className="space-y-6">
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[
                      { title: 'UI / POM Web Automation', icon: Compass, desc: 'Robust cross-browser UI testing based on Page Object Model. Fully encapsulates locators, element interactions, and fluent navigation chains.' },
                      { title: 'REST API & Contract Testing', icon: Eye, desc: 'Verifies endpoints using HTTP queries, tracking response times, header values, and checking response schemas using jsonschema validation.' },
                      { title: 'DB validation & SQLite Fallback', icon: Database, desc: 'Validates database entries. Features automatic database fallback: if local MySQL goes offline, the suite automatically migrates schema and executes on SQLite.' },
                      { title: 'AI-Powered failure Diagnostics', icon: Cpu, desc: 'Analyzes test stack traces instantly, categorizing reasons (TIMEOUT, LOCATOR_ERROR, ASSERTION_FAILURE) for quick triages.' },
                      { title: 'Fuzzy Self-Healing Locators', icon: RefreshCw, desc: 'Auto-heals broken web locators at runtime using Levenshtein calculations and attribute checks if the main CSS selector fails.' },
                      { title: 'Process Lock xdist Coordination', icon: Server, desc: 'Uses a file descriptor lock file (db_setup.lock) to sync parallel workers, preventing SQLite write lock collisions during setup.' }
                    ].map((f, idx) => {
                      const Icon = f.icon;
                      return (
                        <div key={idx} className="p-6 rounded-xl border border-slate-800 bg-[#131926] space-y-4 hover:border-blue-500/30 transition-all duration-300">
                          <div className="flex items-center justify-between">
                            <div className="p-3 rounded-lg bg-blue-600/10 text-blue-400">
                              <Icon className="w-6 h-6" />
                            </div>
                            <span className="text-[10px] font-mono text-slate-500">MODULE 0{idx+1}</span>
                          </div>
                          <h3 className="text-lg font-bold text-white tracking-tight">{f.title}</h3>
                          <p className="text-slate-400 text-sm leading-relaxed">{f.desc}</p>
                        </div>
                      );
                    })}
                  </div>

                  {/* Interactive Self Healing Simulator */}
                  <div className="p-6 rounded-xl border border-slate-800 bg-[#131926] space-y-4">
                    <div className="space-y-2">
                      <h3 className="text-base font-bold text-white">Interactive Self-Healing Simulator</h3>
                      <p className="text-xs text-slate-400">Enter a CSS selector to simulate Selenium runtime healing fallback logic:</p>
                    </div>
                    
                    <div className="flex flex-wrap gap-3">
                      <input 
                        type="text" 
                        value={healingSelector} 
                        onChange={(e) => setHealingSelector(e.target.value)}
                        className="flex-1 min-w-[200px] px-4 py-2 text-sm rounded-lg bg-[#0b0f19] border border-slate-800 focus:outline-none focus:border-blue-500 text-white font-mono"
                      />
                      <button 
                        onClick={triggerSelfHealingSim}
                        className="px-4 py-2 text-sm font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 transition"
                      >
                        Run Locator Healing Simulation
                      </button>
                    </div>

                    {healingLogs.length > 0 && (
                      <div className="p-4 rounded-lg bg-[#0b0f19] border border-slate-800 font-mono text-xs space-y-1.5 overflow-x-auto">
                        {healingLogs.map((log, idx) => (
                          <div key={idx} className={
                            log.includes('[SUCCESS]') ? 'text-emerald-400 font-bold' :
                            log.includes('[WARN]') ? 'text-amber-400' : 'text-slate-400'
                          }>
                            {log}
                          </div>
                        ))}
                        {healingSuccess && (
                          <div className="mt-2 text-[10px] text-slate-500">
                            *Auto-healed and recorded heal event inside Failure summary report.
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* ──────────────────────────────────────────────────
                  TAB 3: ARCHITECTURE OVERVIEW
              ────────────────────────────────────────────────── */}
              {activeTab === 'architecture' && (
                <div className="space-y-6">
                  {/* Layer Diagram Cards */}
                  <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {[
                      { layer: '1. EXECUTION LAYER', desc: 'Managed by Jenkins Pipeline and GitHub Actions runner environments executing tests under Docker Compose orchestration.', icon: Server },
                      { layer: '2. TEST RUNNER LAYER', desc: 'PyTest coordinate suites. Resolves fixtures, hooks, retry runs, and outputs Allure result JSON streams.', icon: Play },
                      { layer: '3. PAGE OBJECT MODEL', desc: 'LoginPage, DashboardPage, etc. inherit BasePage web operations, fully separating test code from locator schemas.', icon: Layers },
                      { layer: '4. UTILITIES & AI', desc: 'DriverFactory, WaitUtils, DBConnector, and the AI Fallback circuit breaker managing dynamic checks.', icon: Cpu }
                    ].map((l, idx) => {
                      const Icon = l.icon;
                      return (
                        <div key={idx} className="p-5 rounded-xl border border-slate-800 bg-[#131926] space-y-3">
                          <div className="flex items-center gap-2 text-blue-400">
                            <Icon className="w-5 h-5" />
                            <h4 className="text-xs font-bold uppercase tracking-wider">{l.layer}</h4>
                          </div>
                          <p className="text-xs text-slate-400 leading-relaxed">{l.desc}</p>
                        </div>
                      );
                    })}
                  </div>

                  {/* Flow Chart Description Card */}
                  <div className="p-6 rounded-xl border border-slate-800 bg-[#131926] space-y-4">
                    <h3 className="text-base font-bold text-white">Circuit-Breaker AI Fallback Flow</h3>
                    <div className="flex flex-col lg:flex-row gap-6 items-center">
                      <div className="flex-1 space-y-3 text-sm text-slate-400 leading-relaxed">
                        <p>
                          Third-party API dependencies introduce risks (e.g., rate limits, network outages) that can compromise CI/CD stability.
                        </p>
                        <p>
                          Our custom **AI Client Wrapper** manages this using a circuit-breaker design:
                        </p>
                        <ol className="list-decimal pl-5 space-y-2">
                          <li>During initialization, the wrapper verifies environment details and the <code>GEMINI_API_KEY</code>.</li>
                          <li>If the API responds with a quota limit (<code>429</code>) or rate limit error, the wrapper logs a warning and sets a session-wide <code>_quota_exhausted</code> flag.</li>
                          <li>For all subsequent tests, requests bypass cloud connections and are resolved locally using regex pattern rules and mathematical metrics.</li>
                        </ol>
                      </div>
                      <div className="w-full lg:w-96 p-4 rounded-xl bg-[#0b0f19] border border-slate-800 flex flex-col gap-3 font-mono text-xs">
                        <div className="text-emerald-400 font-bold"># AI Fallback Console Trace</div>
                        <div className="text-slate-400">2026-05-25 14:40:11 [INFO] Calling Cloud Gemini API...</div>
                        <div className="text-amber-500">2026-05-25 14:40:12 [WARN] HTTP 429: ResourceExhausted (Quota reached)</div>
                        <div className="text-blue-400">2026-05-25 14:40:12 [SYSTEM] Circuit Breaker Tripped! Global _quota_exhausted = True</div>
                        <div className="text-slate-400">2026-05-25 14:40:12 [INFO] Routing Failure Diagnostics to offline matching engine</div>
                        <div className="text-emerald-400">2026-05-25 14:40:12 [SUCCESS] Root cause found locally: NoSuchElementException</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* ──────────────────────────────────────────────────
                  TAB 4: REPORTING & ANALYTICS
              ────────────────────────────────────────────────── */}
              {activeTab === 'analytics' && (
                <div className="space-y-6">
                  {/* Recharts Analytics */}
                  <div className="grid lg:grid-cols-3 gap-6">
                    {/* Trend Line Chart */}
                    <div className="lg:col-span-2 p-6 rounded-xl border border-slate-800 bg-[#131926] space-y-4">
                      <div className="flex justify-between items-center">
                        <h3 className="text-sm font-bold text-white uppercase tracking-wider">Historical Regression Stability (Recharts)</h3>
                        <span className="text-xs text-slate-500 font-mono">Last 10 Runs</span>
                      </div>
                      <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={trendData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                            <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
                            <YAxis stroke="#94a3b8" fontSize={11} />
                            <Tooltip contentStyle={{ backgroundColor: '#131926', border: '1px solid #334155' }} />
                            <Legend wrapperStyle={{ fontSize: 11 }} />
                            <Bar dataKey="Passed" fill={COLORS.accentGreen} stackId="a" />
                            <Bar dataKey="Failed" fill={COLORS.accentRed} stackId="a" />
                            <Bar dataKey="Skipped" fill={COLORS.accentYellow} stackId="a" />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    {/* Test Case Category distribution */}
                    <div className="p-6 rounded-xl border border-slate-800 bg-[#131926] space-y-4 flex flex-col justify-between">
                      <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider">Test Suite Breakdown</h3>
                      <div className="h-48 flex items-center justify-center">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={categoryData}
                              cx="50%"
                              cy="50%"
                              innerRadius={50}
                              outerRadius={80}
                              paddingAngle={5}
                              dataKey="value"
                            >
                              {categoryData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                              ))}
                            </Pie>
                            <Tooltip contentStyle={{ backgroundColor: '#131926', border: '1px solid #334155' }} />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                      <div className="flex justify-around text-xs">
                        {categoryData.map((d, idx) => (
                          <div key={idx} className="flex items-center gap-1.5">
                            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: PIE_COLORS[idx] }}></div>
                            <span className="text-slate-400">{d.name} ({d.value})</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Archives & Screenshot explanation */}
                  <div className="p-6 rounded-xl border border-slate-800 bg-[#131926] space-y-4">
                    <h3 className="text-base font-bold text-white">Archiving Protocol & Snapshots</h3>
                    <p className="text-sm text-slate-400 leading-relaxed">
                      At the end of every test execution session, the hook in <code>conftest.py</code> generates performance charts and archives data in <code>reports/archive/</code> directory. Additionally, in the event of UI failure, the <code>pytest_runtest_makereport</code> hook captures screenshot logs and embeds them as base64 images inside the generated Allure results.
                    </p>
                  </div>
                </div>
              )}

              {/* ──────────────────────────────────────────────────
                  TAB 5: CI/CD PIPELINE
              ────────────────────────────────────────────────── */}
              {activeTab === 'cicd' && (
                <div className="space-y-6">
                  {/* Interactive Pipeline Steps */}
                  <div className="p-6 rounded-xl border border-slate-800 bg-[#131926] space-y-6">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                      <div>
                        <h3 className="text-base font-bold text-white">CI/CD Quality Gate Pipeline Simulator</h3>
                        <p className="text-xs text-slate-400">Launch the pipeline verification flow to check build gate statuses:</p>
                      </div>
                      <button 
                        onClick={() => { setPipelineRunning(true); setPipelineStep(0); }}
                        disabled={pipelineRunning}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition ${
                          pipelineRunning 
                            ? 'bg-slate-800 text-slate-500 cursor-not-allowed' 
                            : 'bg-blue-600 hover:bg-blue-500 text-white'
                        }`}
                      >
                        {pipelineRunning ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                        {pipelineRunning ? 'Pipeline Running...' : 'Trigger Pipeline'}
                      </button>
                    </div>

                    <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
                      {[
                        { step: 0, title: '1. Static Lint', desc: 'black, flake8 check' },
                        { step: 1, title: '2. Smoke Tests', desc: 'pytest -m smoke' },
                        { step: 2, title: '3. Regression', desc: 'pytest -m regression' },
                        { step: 3, title: '4. DB Validation', desc: 'MySQL fallback checks' },
                        { step: 4, title: '5. Deploy Reports', desc: 'Allure pages archive' }
                      ].map((item, idx) => {
                        const isCompleted = pipelineStep > item.step || (pipelineStep === 4 && !pipelineRunning);
                        const isCurrent = pipelineRunning && pipelineStep === item.step;
                        const statusColor = isCompleted ? 'border-emerald-500 bg-emerald-500/10' : isCurrent ? 'border-blue-500 bg-blue-500/10 animate-pulse' : 'border-slate-800 bg-[#0b0f19]';
                        
                        return (
                          <div key={idx} className={`p-4 rounded-xl border transition-all duration-300 ${statusColor}`}>
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-xs font-bold text-slate-300">{item.title}</span>
                              {isCompleted ? (
                                <CheckCircle className="w-5 h-5 text-emerald-400" />
                              ) : isCurrent ? (
                                <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />
                              ) : (
                                <div className="w-4 h-4 rounded-full border border-slate-700"></div>
                              )}
                            </div>
                            <p className="text-xs text-slate-400">{item.desc}</p>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* GitHub Actions workflow code */}
                  <div className="p-6 rounded-xl border border-slate-800 bg-[#131926] space-y-4">
                    <h3 className="text-base font-bold text-white">GitHub Actions YAML Gating (Regression Workflow)</h3>
                    <pre className="p-4 rounded-lg bg-[#0b0f19] border border-slate-800 text-xs font-mono text-slate-400 overflow-x-auto max-h-60 overflow-y-auto">
{`name: Regression Testing
on:
  push:
    branches: [ main, develop ]
jobs:
  run-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: 'pip'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run Tests
        env:
          USE_MOCK_AI: true
          AI_ENABLED: true
        run: pytest tests/ -m regression -n 4 --headless=true`}
                    </pre>
                  </div>
                </div>
              )}

              {/* ──────────────────────────────────────────────────
                  TAB 6: DOCKER & WORKERS
              ────────────────────────────────────────────────── */}
              {activeTab === 'docker' && (
                <div className="space-y-6">
                  {/* Docker Compose Diagram */}
                  <div className="p-6 rounded-xl border border-slate-800 bg-[#131926] space-y-4">
                    <h3 className="text-base font-bold text-white">Dockerized Cluster Orchestration</h3>
                    <p className="text-sm text-slate-400 leading-relaxed">
                      Using Docker Compose, the framework deploys a standalone Selenium Grid (Hub and dynamic Chrome/Firefox container nodes), a dedicated MySQL backend DB service, and an execution container runner. If the main database container goes offline, the runner automatically connects to a local, isolated SQLite fallback file.
                    </p>
                  </div>

                  {/* Parallel Execution locking log */}
                  <div className="p-6 rounded-xl border border-slate-800 bg-[#131926] space-y-4">
                    <h3 className="text-base font-bold text-white">pytest-xdist SQLite Coordination Lock Console</h3>
                    <div className="p-4 rounded-lg bg-[#0b0f19] border border-slate-800 font-mono text-xs text-slate-400 space-y-1.5 overflow-x-auto">
                      <div>2026-05-25 14:39:46 [INFO] Spawning 2 pytest-xdist parallel workers...</div>
                      <div className="text-blue-400">2026-05-25 14:39:47 [gw0] connected &rarr; executing DDL database schema creation</div>
                      <div className="text-blue-400">2026-05-25 14:39:47 [gw0] lock file "data/db_setup.lock" written.</div>
                      <div className="text-yellow-400">2026-05-25 14:39:47 [gw1] connected &rarr; lock "db_setup.lock" found. Waiting...</div>
                      <div className="text-yellow-400">2026-05-25 14:39:48 [gw1] database connection verified (schema initialized). Bypassing setup.</div>
                      <div className="text-emerald-400">2026-05-25 14:39:48 [SUCCESS] Parallel execution started. 8 Database tests run in 5.28s (Zero locks).</div>
                    </div>
                  </div>
                </div>
              )}

              {/* ──────────────────────────────────────────────────
                  TAB 7: SCREENSHOTS GALLERY
              ────────────────────────────────────────────────── */}
              {activeTab === 'gallery' && (
                <div className="space-y-6">
                  {/* Slider Carousel */}
                  <div className="p-6 rounded-xl border border-slate-800 bg-[#131926] space-y-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-base font-bold text-white">{carouselImages[carouselIndex].title}</h3>
                        <p className="text-xs text-slate-400">{carouselImages[carouselIndex].desc}</p>
                      </div>
                      <div className="flex gap-2">
                        <button 
                          onClick={() => setCarouselIndex((prev) => (prev === 0 ? 3 : prev - 1))}
                          className="p-2 rounded-lg bg-slate-800 text-slate-400 hover:text-slate-200"
                        >
                          <ChevronLeft className="w-5 h-5" />
                        </button>
                        <button 
                          onClick={() => setCarouselIndex((prev) => (prev === 3 ? 0 : prev + 1))}
                          className="p-2 rounded-lg bg-slate-800 text-slate-400 hover:text-slate-200"
                        >
                          <ChevronRight className="w-5 h-5" />
                        </button>
                      </div>
                    </div>

                    <div className="relative overflow-hidden rounded-xl border border-slate-800 bg-[#0b0f19] p-4 flex items-center justify-center min-h-[350px]">
                      <img 
                        src={carouselImages[carouselIndex].path} 
                        alt={carouselImages[carouselIndex].title}
                        className="max-w-full max-h-[450px] object-contain rounded shadow-lg"
                      />
                    </div>

                    <div className="flex justify-center gap-2">
                      {[0, 1, 2, 3].map((idx) => (
                        <button 
                          key={idx}
                          onClick={() => setCarouselIndex(idx)}
                          className={`w-2.5 h-2.5 rounded-full transition-all ${
                            carouselIndex === idx ? 'bg-blue-500 w-6' : 'bg-slate-700'
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* ──────────────────────────────────────────────────
                  TAB 8: RESUME & SKILLS
              ────────────────────────────────────────────────── */}
              {activeTab === 'resume' && (
                <div className="space-y-6">
                  {/* Skill Cards */}
                  <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[
                      { cat: 'PROGRAMMING & CORE', skills: ['Python 3.11', 'OOP Patterns', 'Data Structures', 'Regular Expressions'] },
                      { cat: 'WEB CORE / POM UI', skills: ['Selenium WebDriver', 'Page Object Model', 'Page Factory Patterns', 'Explicit wait models'] },
                      { cat: 'API / INTERCONNECT', skills: ['REST Client Design', 'requests / httpx', 'JSON Schema checks', 'Token authentications'] },
                      { cat: 'DATABASES & ORM', skills: ['MySQL 8.0 validation', 'SQLite engine fallback', 'SQLAlchemy ORM', 'Schema structures'] },
                      { cat: 'DEVOPS / ORCHESTRATORS', skills: ['Docker / Compose', 'Selenium Grid Hub/Nodes', 'Jenkins Declarative', 'GitHub Actions workflow'] },
                      { cat: 'REPORTING & AI', skills: ['Allure reports', 'Fuzzy matching healing', 'Failure log diagnostics', 'circuit-breaker failover'] }
                    ].map((s, idx) => (
                      <div key={idx} className="p-6 rounded-xl border border-slate-800 bg-[#131926] space-y-4">
                        <h4 className="text-xs font-bold text-blue-400 uppercase tracking-wider">{s.cat}</h4>
                        <div className="flex flex-wrap gap-2">
                          {s.skills.map((skill) => (
                            <span key={skill} className="px-2.5 py-1 rounded bg-[#0b0f19] border border-slate-800 text-xs text-slate-300 font-medium">
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* ATS Resume Bullet Points */}
                  <div className="p-6 rounded-xl border border-slate-800 bg-[#131926] space-y-4">
                    <h3 className="text-base font-bold text-white">ATS-Optimized SDET Bullets</h3>
                    <ul className="list-disc pl-5 space-y-3 text-sm text-slate-400 leading-relaxed">
                      <li>
                        Architected a hybrid test automation framework from scratch using Python, Selenium WebDriver, and PyTest using the Page Object Model (POM) pattern, improving UI verification efficiency by <strong>60%</strong>.
                      </li>
                      <li>
                        Engineered a custom, thread-safe <strong>AI Integration Wrapper</strong> utilizing Google Gemini LLM for automated failure log diagnostics and self-healing UI locators, implementing a circuit-breaker failover pattern that redirects to an offline rules engine to bypass cloud quota limits (HTTP 429).
                      </li>
                      <li>
                        Designed a custom process-level coordination lock (db_setup.lock) under pytest-xdist, allowing parallel workers to connect to a shared MySQL/SQLite database without concurrency schema conflicts, reducing regression run times from <strong>45 minutes to 7 minutes</strong>.
                      </li>
                      <li>
                        Replaced non-deterministic delay strategies with structured explicit wait hierarchies (WaitUtils) and a thread-local web driver factory, raising test execution stability to <strong>99.8%</strong> across dynamic React/single-page applications.
                      </li>
                    </ul>
                  </div>
                </div>
              )}

              {/* ──────────────────────────────────────────────────
                  TAB 9: CONTACT & LINKS
              ────────────────────────────────────────────────── */}
              {activeTab === 'contact' && (
                <div className="space-y-6">
                  <div className="grid lg:grid-cols-2 gap-6">
                    {/* Simulated Contact Form */}
                    <div className="p-6 rounded-xl border border-slate-800 bg-[#131926] space-y-4">
                      <h3 className="text-base font-bold text-white">Send a Message / Schedule Inquiry</h3>
                      <form onSubmit={(e) => { e.preventDefault(); setFeedbackSent(true); }} className="space-y-4 text-sm">
                        <div className="grid sm:grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <label className="text-xs font-semibold text-slate-400">Name</label>
                            <input 
                              type="text" 
                              required
                              className="w-full px-4 py-2 rounded-lg bg-[#0b0f19] border border-slate-800 text-white focus:outline-none focus:border-blue-500" 
                            />
                          </div>
                          <div className="space-y-2">
                            <label className="text-xs font-semibold text-slate-400">Email</label>
                            <input 
                              type="email" 
                              required
                              className="w-full px-4 py-2 rounded-lg bg-[#0b0f19] border border-slate-800 text-white focus:outline-none focus:border-blue-500" 
                            />
                          </div>
                        </div>
                        <div className="space-y-2">
                          <label className="text-xs font-semibold text-slate-400">Message</label>
                          <textarea 
                            rows="4" 
                            required
                            className="w-full px-4 py-2 rounded-lg bg-[#0b0f19] border border-slate-800 text-white focus:outline-none focus:border-blue-500"
                          ></textarea>
                        </div>
                        
                        <button 
                          type="submit"
                          className="flex items-center justify-center gap-2 w-full px-4 py-2 rounded-lg font-semibold bg-blue-600 hover:bg-blue-500 text-white transition-all shadow-md shadow-blue-900/30"
                        >
                          {feedbackSent ? <Check className="w-4 h-4" /> : <Send className="w-4 h-4" />}
                          {feedbackSent ? 'Message Received!' : 'Send Message'}
                        </button>
                      </form>
                    </div>

                    {/* Social Media Link Card */}
                    <div className="p-6 rounded-xl border border-slate-800 bg-[#131926] space-y-6 flex flex-col justify-between">
                      <div className="space-y-4">
                        <h3 className="text-base font-bold text-white">GitHub & Recruiting Profiles</h3>
                        <p className="text-sm text-slate-400 leading-relaxed">
                          Feel free to reach out for SDET, Lead QA Automation, or Test Architect roles. Explore the repository and complete framework documentation on GitHub:
                        </p>
                      </div>

                      <div className="space-y-3">
                        <a 
                          href="https://github.com" 
                          target="_blank" 
                          rel="noreferrer"
                          className="flex items-center justify-between w-full px-4 py-3 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 transition"
                        >
                          <span className="flex items-center gap-3 font-semibold text-sm text-white">
                            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" /><path d="M9 18c-4.51 2-5-2-7-2" /></svg>
                            Explore GitHub Repository
                          </span>
                          <ChevronRight className="w-5 h-5 text-slate-500" />
                        </a>
                        <a 
                          href="https://linkedin.com" 
                          target="_blank" 
                          rel="noreferrer"
                          className="flex items-center justify-between w-full px-4 py-3 rounded-lg bg-[#0a66c2]/10 border border-[#0a66c2]/30 hover:bg-[#0a66c2]/20 transition"
                        >
                          <span className="flex items-center gap-3 font-semibold text-sm text-[#0a66c2]">
                            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" /><rect width="4" height="12" x="2" y="9" /><circle cx="4" cy="4" r="2" /></svg>
                            Connect on LinkedIn
                          </span>
                          <ChevronRight className="w-5 h-5 text-[#0a66c2]/50" />
                        </a>
                      </div>
                    </div>
                  </div>
                </div>
              )}

            </motion.div>
          </AnimatePresence>
        </main>
      </div>

    </div>
  );
}
