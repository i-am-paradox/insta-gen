import { useState, useRef, useCallback } from 'react'
import {
  Camera, Play, Square, Upload, Plus, Trash2, Download,
  Wifi, WifiOff, Monitor, CheckCircle2, XCircle, Loader2,
  Clock, Phone, KeyRound, Settings2, ChevronDown, ChevronUp,
  AlertCircle, Eye, EyeOff, ShieldCheck, Zap, Timer, Bug
} from 'lucide-react'
import { useSocket, type OTPRequest, type TabStatus } from './useSocket'

interface AntiBanState {
  level: 'low' | 'medium' | 'high' | 'paranoid';
  typing_speed: string;
  tab_cooldown_min: number;
  tab_cooldown_max: number;
  random_delays: boolean;
  debug_screenshots: boolean;
  max_retries: number;
}

const PRESETS: Record<string, Omit<AntiBanState, 'level'>> = {
  low:      { typing_speed: 'fast',     tab_cooldown_min: 2,  tab_cooldown_max: 5,  random_delays: false, debug_screenshots: false, max_retries: 1 },
  medium:   { typing_speed: 'medium',   tab_cooldown_min: 5,  tab_cooldown_max: 15, random_delays: true,  debug_screenshots: false, max_retries: 2 },
  high:     { typing_speed: 'slow',     tab_cooldown_min: 15, tab_cooldown_max: 30, random_delays: true,  debug_screenshots: false, max_retries: 3 },
  paranoid: { typing_speed: 'paranoid', tab_cooldown_min: 30, tab_cooldown_max: 60, random_delays: true,  debug_screenshots: true,  max_retries: 3 },
};

const LEVEL_META: Record<string, { label: string; color: string; bg: string; border: string; pct: number }> = {
  low:      { label: 'Low',      color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/40', pct: 25  },
  medium:   { label: 'Medium',   color: 'text-blue-400',   bg: 'bg-blue-500/10',   border: 'border-blue-500/40',   pct: 55  },
  high:     { label: 'High',     color: 'text-green-400',  bg: 'bg-green-500/10',  border: 'border-green-500/40',  pct: 80  },
  paranoid: { label: 'Paranoid', color: 'text-[#E1306C]',  bg: 'bg-[#E1306C]/10', border: 'border-[#E1306C]/40',  pct: 100 },
};

/* ─── OTP Modal ─── */
function OtpModal({ req, onSubmit, onSkip }: {
  req: OTPRequest;
  onSubmit: (id: string, otp: string) => void;
  onSkip: (id: string) => void;
}) {
  const [otp, setOtp] = useState('');
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-2xl p-6 w-full max-w-sm mx-4 glow-pink">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-[#E1306C]/20 flex items-center justify-center">
            <KeyRound className="w-5 h-5 text-[#E1306C]" />
          </div>
          <div>
            <h3 className="text-white font-semibold text-lg">OTP Required</h3>
            <p className="text-sm text-gray-400">{req.phone}</p>
          </div>
        </div>
        <input
          type="text"
          maxLength={8}
          value={otp}
          onChange={e => setOtp(e.target.value.replace(/\D/g, ''))}
          placeholder="Enter OTP code"
          className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-xl px-4 py-3 text-white text-center text-2xl tracking-[0.3em] font-mono placeholder:text-gray-600 placeholder:text-base placeholder:tracking-normal focus:outline-none focus:border-[#E1306C]/50 mb-4"
          autoFocus
          onKeyDown={e => { if (e.key === 'Enter' && otp.length >= 4) onSubmit(req.activation_id, otp); }}
        />
        <div className="flex gap-3">
          <button
            onClick={() => onSkip(req.activation_id)}
            className="flex-1 py-2.5 rounded-xl border border-[#1e1e2e] text-gray-400 hover:bg-[#1a1a28] transition-colors cursor-pointer"
          >
            Skip
          </button>
          <button
            onClick={() => otp.length >= 4 && onSubmit(req.activation_id, otp)}
            disabled={otp.length < 4}
            className="flex-1 py-2.5 rounded-xl bg-[#E1306C] text-white font-semibold hover:bg-[#E1306C]/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
}

/* ─── Tab Card ─── */
function TabCard({ tab }: { tab: TabStatus }) {
  const statusConfig: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
    IDLE: { color: 'text-gray-500', icon: <Clock className="w-4 h-4" />, label: 'Idle' },
    STARTING: { color: 'text-blue-400', icon: <Loader2 className="w-4 h-4 animate-spin" />, label: 'Starting' },
    REGISTERING: { color: 'text-yellow-400', icon: <Loader2 className="w-4 h-4 animate-spin" />, label: 'Registering' },
    WARMING: { color: 'text-orange-400', icon: <Loader2 className="w-4 h-4 animate-spin" />, label: 'Warming' },
    FILLING: { color: 'text-blue-400', icon: <Loader2 className="w-4 h-4 animate-spin" />, label: 'Filling Form' },
    SUBMITTING: { color: 'text-purple-400', icon: <Loader2 className="w-4 h-4 animate-spin" />, label: 'Submitting' },
    OTP_WAIT: { color: 'text-[#E1306C]', icon: <KeyRound className="w-4 h-4" />, label: 'Waiting OTP' },
    SUCCESS: { color: 'text-green-400', icon: <CheckCircle2 className="w-4 h-4" />, label: 'Success' },
    FAILED: { color: 'text-red-400', icon: <XCircle className="w-4 h-4" />, label: 'Failed' },
    ERROR: { color: 'text-red-400', icon: <AlertCircle className="w-4 h-4" />, label: 'Error' },
    COOLDOWN: { color: 'text-cyan-400', icon: <Clock className="w-4 h-4" />, label: 'Cooldown' },
  };
  const cfg = statusConfig[tab.status] || statusConfig.IDLE;

  return (
    <div className={`bg-[#12121a] border rounded-xl p-4 ${tab.status === 'OTP_WAIT' ? 'animate-pulse-ring border-[#E1306C]/40' : 'border-[#1e1e2e]'}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-gray-500">TAB {tab.tab_id}</span>
        <span className={`flex items-center gap-1.5 text-xs font-medium ${cfg.color}`}>
          {cfg.icon} {cfg.label}
        </span>
      </div>
      {tab.username && <p className="text-sm text-white truncate">@{tab.username}</p>}
      {tab.phone && <p className="text-xs text-gray-500 mt-1 flex items-center gap-1 font-mono"><Phone className="w-3 h-3" />{tab.phone}</p>}
    </div>
  );
}

/* ─── Account Row ─── */
function AccountRow({ acc, idx }: { acc: { username: string; password: string; full_name: string; phone: string; status: string }; idx: number }) {
  const [showPw, setShowPw] = useState(false);
  return (
    <tr className="border-b border-[#1e1e2e]/50 hover:bg-[#1a1a28]/50 transition-colors">
      <td className="py-3 px-4 text-gray-500 text-sm">{idx + 1}</td>
      <td className="py-3 px-4 text-white font-medium">@{acc.username}</td>
      <td className="py-3 px-4">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-300 font-mono">{showPw ? acc.password : '••••••••'}</span>
          <button onClick={() => setShowPw(!showPw)} className="text-gray-500 hover:text-gray-300 cursor-pointer">
            {showPw ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
          </button>
        </div>
      </td>
      <td className="py-3 px-4 text-sm text-gray-400">{acc.full_name}</td>
      <td className="py-3 px-4 text-sm text-gray-400">{acc.phone}</td>
      <td className="py-3 px-4">
        {acc.status === 'success'
          ? <span className="text-xs bg-green-500/10 text-green-400 px-2 py-1 rounded-full">Success</span>
          : <span className="text-xs bg-red-500/10 text-red-400 px-2 py-1 rounded-full">Failed</span>}
      </td>
    </tr>
  );
}

/* ─── Main App ─── */
export default function App() {
  const { connected, state, otpRequests, logs, sendOtp } = useSocket();

  // Form state
  const [phones, setPhones] = useState<string[]>([]);
  const [phoneInput, setPhoneInput] = useState('');
  const [concurrentTabs, setConcurrentTabs] = useState(5);
  const [sessionLimit, setSessionLimit] = useState(100);
  const [headless, setHeadless] = useState(false);
  const [warming, setWarming] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [showLogs, setShowLogs] = useState(false);
  const [starting, setStarting] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const [antiBan, setAntiBan] = useState<AntiBanState>({
    level: 'medium', ...PRESETS.medium,
  });
  const [showAntiBan, setShowAntiBan] = useState(true);

  const applyPreset = (level: AntiBanState['level']) => {
    setAntiBan({ level, ...PRESETS[level] });
  };

  const addPhones = useCallback((text: string) => {
    const lines = text.split(/[\n,]+/).map(l => l.trim()).filter(l => l.length > 3);
    if (lines.length > 0) {
      setPhones(prev => {
        const set = new Set([...prev, ...lines]);
        return Array.from(set).slice(0, 500);
      });
    }
  }, []);

  const handleFile = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => addPhones(reader.result as string);
    reader.readAsText(file);
    e.target.value = '';
  }, [addPhones]);

  const handleAddManual = () => {
    if (phoneInput.trim()) {
      addPhones(phoneInput);
      setPhoneInput('');
    }
  };

  const handleStart = async () => {
    if (phones.length === 0 || state.running) return;
    setStarting(true);
    try {
      await fetch('/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone_numbers: phones,
          concurrent_tabs: concurrentTabs,
          session_limit: sessionLimit,
          headless,
          enable_warming: warming,
          anti_ban: {
            typing_speed: antiBan.typing_speed,
            tab_cooldown_min: antiBan.tab_cooldown_min,
            tab_cooldown_max: antiBan.tab_cooldown_max,
            random_delays: antiBan.random_delays,
            debug_screenshots: antiBan.debug_screenshots,
            max_retries: antiBan.max_retries,
          },
        }),
      });
    } catch (err) {
      console.error('Start failed:', err);
    } finally {
      setStarting(false);
    }
  };

  const handleStop = async () => {
    try {
      await fetch('/api/stop', { method: 'POST' });
    } catch (err) {
      console.error('Stop failed:', err);
    }
  };

  const handleOtpSkip = (id: string) => {
    sendOtp(id, '000000');
  };

  const tabs = Object.values(state.tabs);
  const progress = state.total > 0 ? ((state.success + state.failed) / state.total * 100) : 0;

  return (
    <div className="min-h-screen bg-[#0a0a0f]">
      {/* OTP Modals */}
      {otpRequests.length > 0 && (
        <OtpModal req={otpRequests[0]} onSubmit={sendOtp} onSkip={handleOtpSkip} />
      )}

      {/* Header */}
      <header className="border-b border-[#1e1e2e] bg-[#12121a]/90 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center ig-gradient">
              <Camera className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold gradient-text">IG Creator PRO</h1>
              <p className="text-xs text-gray-500">Account Automation Dashboard</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {/* OTP badge */}
            {otpRequests.length > 0 && (
              <span className="bg-[#E1306C]/20 text-[#E1306C] text-xs font-bold px-3 py-1.5 rounded-full animate-pulse-ring">
                {otpRequests.length} OTP Pending
              </span>
            )}
            {/* Connection status */}
            <div className={`flex items-center gap-1.5 text-xs ${connected ? 'text-green-400' : 'text-red-400'}`}>
              {connected ? <Wifi className="w-3.5 h-3.5" /> : <WifiOff className="w-3.5 h-3.5" />}
              {connected ? 'Connected' : 'Disconnected'}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6 pb-12">
        {/* ── Top Stats ── */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard label="Total" value={state.total} icon={<Monitor className="w-5 h-5" />} color="text-blue-400" bg="bg-blue-500/10" />
          <StatCard label="Success" value={state.success} icon={<CheckCircle2 className="w-5 h-5" />} color="text-green-400" bg="bg-green-500/10" />
          <StatCard label="Failed" value={state.failed} icon={<XCircle className="w-5 h-5" />} color="text-red-400" bg="bg-red-500/10" />
          <StatCard label="In Progress" value={state.in_progress} icon={<Loader2 className="w-5 h-5 animate-spin" />} color="text-yellow-400" bg="bg-yellow-500/10" />
        </div>

        {/* Progress bar */}
        {state.running && state.total > 0 && (
          <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">Progress</span>
              <span className="text-sm text-white font-medium">{state.success + state.failed} / {state.total}</span>
            </div>
            <div className="h-2 bg-[#0a0a0f] rounded-full overflow-hidden">
              <div
                className="h-full rounded-full ig-gradient transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* ── Phone Input + Controls ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Phone numbers panel */}
          <div className="lg:col-span-2 bg-[#12121a] border border-[#1e1e2e] rounded-2xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-white font-semibold flex items-center gap-2">
                <Phone className="w-4 h-4 text-[#E1306C]" /> Phone Numbers
                <span className="text-xs text-gray-500 font-normal ml-1">({phones.length} loaded)</span>
              </h2>
              <div className="flex gap-2">
                <input type="file" ref={fileRef} accept=".txt,.csv" onChange={handleFile} className="hidden" />
                <button
                  onClick={() => fileRef.current?.click()}
                  className="flex items-center gap-1.5 text-xs bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-2 text-gray-300 hover:bg-[#1a1a28] transition-colors cursor-pointer"
                >
                  <Upload className="w-3.5 h-3.5" /> Upload .txt
                </button>
                {phones.length > 0 && (
                  <button
                    onClick={() => setPhones([])}
                    className="flex items-center gap-1.5 text-xs border border-red-500/30 text-red-400 rounded-lg px-3 py-2 hover:bg-red-500/10 transition-colors cursor-pointer"
                  >
                    <Trash2 className="w-3.5 h-3.5" /> Clear
                  </button>
                )}
              </div>
            </div>

            {/* Input area */}
            <div className="flex gap-2 mb-3">
              <textarea
                value={phoneInput}
                onChange={e => setPhoneInput(e.target.value)}
                placeholder="Paste phone numbers here (one per line, or comma separated)&#10;+91XXXXXXXXXX&#10;+91XXXXXXXXXX"
                rows={3}
                className="flex-1 bg-[#0a0a0f] border border-[#1e1e2e] rounded-xl px-4 py-3 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:border-[#E1306C]/40 resize-none"
              />
              <button
                onClick={handleAddManual}
                disabled={!phoneInput.trim()}
                className="self-end px-4 py-3 bg-[#E1306C] text-white rounded-xl hover:bg-[#E1306C]/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              >
                <Plus className="w-5 h-5" />
              </button>
            </div>

            {/* Phone list */}
            {phones.length > 0 && (
              <div className="max-h-40 overflow-y-auto bg-[#0a0a0f] rounded-xl border border-[#1e1e2e] p-3 space-y-1">
                {phones.map((p, i) => (
                  <div key={i} className="flex items-center justify-between text-sm py-1 px-2 rounded hover:bg-[#1a1a28] group">
                    <span className="text-gray-300 font-mono">{p}</span>
                    <button
                      onClick={() => setPhones(prev => prev.filter((_, idx) => idx !== i))}
                      className="text-gray-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Controls panel */}
          <div className="bg-[#12121a] border border-[#1e1e2e] rounded-2xl p-5 flex flex-col">
            <h2 className="text-white font-semibold flex items-center gap-2 mb-4">
              <Settings2 className="w-4 h-4 text-[#833AB4]" /> Controls
            </h2>

            {/* Concurrent tabs slider */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-1">
                <label className="text-sm text-gray-400">Concurrent Tabs</label>
                <span className="text-sm text-white font-mono bg-[#0a0a0f] px-2 py-0.5 rounded">{concurrentTabs}</span>
              </div>
              <input
                type="range" min={1} max={10} value={concurrentTabs}
                onChange={e => setConcurrentTabs(Number(e.target.value))}
                className="w-full"
                style={{ accentColor: '#E1306C' }}
                disabled={state.running}
              />
              <div className="flex justify-between text-xs text-gray-600 mt-0.5"><span>1</span><span>10</span></div>
            </div>

            {/* Session limit */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-1">
                <label className="text-sm text-gray-400">Session Limit</label>
                <span className="text-sm text-white font-mono bg-[#0a0a0f] px-2 py-0.5 rounded">{sessionLimit}</span>
              </div>
              <input
                type="range" min={1} max={100} value={sessionLimit}
                onChange={e => setSessionLimit(Number(e.target.value))}
                className="w-full"
                style={{ accentColor: '#E1306C' }}
                disabled={state.running}
              />
              <div className="flex justify-between text-xs text-gray-600 mt-0.5"><span>1</span><span>100</span></div>
            </div>

            {/* Advanced settings toggle */}
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="flex items-center justify-between text-sm text-gray-400 mb-3 hover:text-gray-300 cursor-pointer"
            >
              Advanced Settings {showSettings ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
            {showSettings && (
              <div className="space-y-3 mb-4 p-3 bg-[#0a0a0f] rounded-xl border border-[#1e1e2e]">
                <label className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">Headless Mode</span>
                  <input type="checkbox" checked={headless} onChange={e => setHeadless(e.target.checked)}
                    disabled={state.running}
                    style={{ accentColor: '#E1306C' }} className="w-4 h-4" />
                </label>
                <label className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">Session Warming</span>
                  <input type="checkbox" checked={warming} onChange={e => setWarming(e.target.checked)}
                    disabled={state.running}
                    style={{ accentColor: '#E1306C' }} className="w-4 h-4" />
                </label>
              </div>
            )}

            {/* Start / Stop button */}
            <div className="mt-auto pt-4">
              {!state.running ? (
                <button
                  onClick={handleStart}
                  disabled={phones.length === 0 || starting}
                  className="w-full flex items-center justify-center gap-2 py-3 rounded-xl ig-gradient text-white font-bold text-lg hover:opacity-90 transition-opacity disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                >
                  {starting ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
                  {starting ? 'Starting...' : 'Start'}
                </button>
              ) : (
                <button
                  onClick={handleStop}
                  className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-red-500/20 border border-red-500/30 text-red-400 font-bold text-lg hover:bg-red-500/30 transition-colors cursor-pointer"
                >
                  <Square className="w-5 h-5" /> Stop
                </button>
              )}
            </div>
          </div>
        </div>

        {/* ── Live Tabs ── */}
        {tabs.length > 0 && (
          <div>
            <h2 className="text-white font-semibold mb-3 flex items-center gap-2">
              <Monitor className="w-4 h-4 text-[#E1306C]" /> Live Tabs
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3">
              {tabs.map(t => <TabCard key={t.tab_id} tab={t} />)}
            </div>
          </div>
        )}

        {/* ── Created Accounts ── */}
        {state.created_accounts.length > 0 && (
          <div className="bg-[#12121a] border border-[#1e1e2e] rounded-2xl overflow-hidden">
            <div className="flex items-center justify-between p-5 border-b border-[#1e1e2e]">
              <h2 className="text-white font-semibold flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-400" /> Created Accounts
                <span className="text-xs text-gray-500 font-normal">({state.created_accounts.length})</span>
              </h2>
              <a
                href="/api/download-csv"
                className="flex items-center gap-1.5 text-xs bg-green-500/10 text-green-400 border border-green-500/20 rounded-lg px-3 py-2 hover:bg-green-500/20 transition-colors"
              >
                <Download className="w-3.5 h-3.5" /> Download CSV
              </a>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="text-xs text-gray-500 border-b border-[#1e1e2e]/50">
                    <th className="py-3 px-4 font-medium">#</th>
                    <th className="py-3 px-4 font-medium">Username</th>
                    <th className="py-3 px-4 font-medium">Password</th>
                    <th className="py-3 px-4 font-medium">Full Name</th>
                    <th className="py-3 px-4 font-medium">Phone</th>
                    <th className="py-3 px-4 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {state.created_accounts.map((acc, i) => (
                    <AccountRow key={i} acc={acc} idx={i} />
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── Anti-Ban Protection ── */}
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-2xl overflow-hidden">
          <button
            onClick={() => setShowAntiBan(!showAntiBan)}
            className="w-full flex items-center justify-between px-5 py-4 hover:bg-[#1a1a28] transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-[#E1306C]/15 flex items-center justify-center">
                <ShieldCheck className="w-4 h-4 text-[#E1306C]" />
              </div>
              <div className="text-left">
                <p className="text-white font-semibold text-sm">Anti-Ban Protection</p>
                <p className={`text-xs font-medium ${LEVEL_META[antiBan.level].color}`}>
                  {LEVEL_META[antiBan.level].label} — {LEVEL_META[antiBan.level].pct}% protection
                </p>
              </div>
            </div>
            {showAntiBan ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
          </button>

          {showAntiBan && (
            <div className="border-t border-[#1e1e2e] p-5 space-y-5">
              {/* Protection level presets */}
              <div>
                <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wider">Protection Preset</p>
                <div className="grid grid-cols-4 gap-2">
                  {(['low', 'medium', 'high', 'paranoid'] as const).map(lvl => {
                    const m = LEVEL_META[lvl];
                    const active = antiBan.level === lvl;
                    return (
                      <button
                        key={lvl}
                        onClick={() => applyPreset(lvl)}
                        disabled={state.running}
                        className={`py-2.5 rounded-xl text-xs font-semibold border transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed ${
                          active ? `${m.bg} ${m.color} ${m.border}` : 'border-[#1e1e2e] text-gray-500 hover:border-[#333] hover:text-gray-300'
                        }`}
                      >
                        {m.label}
                      </button>
                    );
                  })}
                </div>
                {/* Protection meter */}
                <div className="mt-3">
                  <div className="h-1.5 bg-[#0a0a0f] rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        antiBan.level === 'low' ? 'bg-yellow-500' :
                        antiBan.level === 'medium' ? 'bg-blue-500' :
                        antiBan.level === 'high' ? 'bg-green-500' : 'ig-gradient'
                      }`}
                      style={{ width: `${LEVEL_META[antiBan.level].pct}%` }}
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                {/* Typing speed */}
                <div>
                  <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wider flex items-center gap-1.5">
                    <Zap className="w-3 h-3" /> Typing Speed
                  </p>
                  <div className="grid grid-cols-4 gap-1.5">
                    {(['fast', 'medium', 'slow', 'paranoid'] as const).map(spd => (
                      <button
                        key={spd}
                        onClick={() => setAntiBan(p => ({ ...p, typing_speed: spd }))}
                        disabled={state.running}
                        className={`py-1.5 rounded-lg text-xs font-medium border transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed capitalize ${
                          antiBan.typing_speed === spd
                            ? 'bg-[#833AB4]/20 text-[#c084fc] border-[#833AB4]/40'
                            : 'border-[#1e1e2e] text-gray-500 hover:text-gray-300'
                        }`}
                      >
                        {spd}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Tab cooldown */}
                <div>
                  <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wider flex items-center gap-1.5">
                    <Timer className="w-3 h-3" /> Tab Cooldown
                    <span className="text-gray-600 normal-case font-normal">
                      {antiBan.tab_cooldown_min}–{antiBan.tab_cooldown_max}s
                    </span>
                  </p>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-600 w-7">Min</span>
                      <input type="range" min={1} max={59}
                        value={antiBan.tab_cooldown_min}
                        onChange={e => setAntiBan(p => ({ ...p, tab_cooldown_min: Number(e.target.value), level: 'medium' }))}
                        disabled={state.running}
                        className="flex-1" style={{ accentColor: '#833AB4' }}
                      />
                      <span className="text-xs text-gray-400 w-6 text-right">{antiBan.tab_cooldown_min}s</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-600 w-7">Max</span>
                      <input type="range" min={antiBan.tab_cooldown_min + 1} max={120}
                        value={antiBan.tab_cooldown_max}
                        onChange={e => setAntiBan(p => ({ ...p, tab_cooldown_max: Number(e.target.value), level: 'medium' }))}
                        disabled={state.running}
                        className="flex-1" style={{ accentColor: '#833AB4' }}
                      />
                      <span className="text-xs text-gray-400 w-6 text-right">{antiBan.tab_cooldown_max}s</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Toggles */}
              <div className="grid grid-cols-2 gap-2">
                {[
                  { key: 'random_delays',     label: 'Random Delays',     icon: <Timer className="w-3.5 h-3.5" />,      desc: 'Extra human-like pauses' },
                  { key: 'debug_screenshots', label: 'Debug Screenshots', icon: <Bug className="w-3.5 h-3.5" />,        desc: 'Save on failure (slow)' },
                ].map(({ key, label, icon, desc }) => {
                  const active = antiBan[key as keyof AntiBanState] as boolean;
                  return (
                    <button
                      key={key}
                      onClick={() => setAntiBan(p => ({ ...p, [key]: !active }))}
                      disabled={state.running}
                      className={`flex items-center gap-2.5 p-3 rounded-xl border text-left transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed ${
                        active ? 'bg-green-500/10 border-green-500/30' : 'border-[#1e1e2e] hover:border-[#333]'
                      }`}
                    >
                      <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${active ? 'bg-green-500/20 text-green-400' : 'bg-[#0a0a0f] text-gray-600'}`}>
                        {icon}
                      </div>
                      <div>
                        <p className={`text-xs font-semibold ${active ? 'text-green-400' : 'text-gray-400'}`}>{label}</p>
                        <p className="text-xs text-gray-600">{desc}</p>
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Max retries */}
              <div className="flex items-center justify-between bg-[#0a0a0f] rounded-xl px-4 py-3">
                <div>
                  <p className="text-sm text-gray-300 font-medium">Max Retries</p>
                  <p className="text-xs text-gray-600">Retry on failure before marking failed</p>
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={() => setAntiBan(p => ({ ...p, max_retries: Math.max(0, p.max_retries - 1) }))}
                    disabled={state.running || antiBan.max_retries === 0}
                    className="w-7 h-7 rounded-lg bg-[#1a1a28] text-white flex items-center justify-center hover:bg-[#1e1e2e] disabled:opacity-40 cursor-pointer font-bold">−</button>
                  <span className="text-white font-mono font-bold w-4 text-center">{antiBan.max_retries}</span>
                  <button onClick={() => setAntiBan(p => ({ ...p, max_retries: Math.min(5, p.max_retries + 1) }))}
                    disabled={state.running || antiBan.max_retries === 5}
                    className="w-7 h-7 rounded-lg bg-[#1a1a28] text-white flex items-center justify-center hover:bg-[#1e1e2e] disabled:opacity-40 cursor-pointer font-bold">+</button>
                </div>
              </div>

              {/* Active protection pills */}
              <div className="flex flex-wrap gap-2">
                <span className="text-xs text-gray-600">Active:</span>
                {warming && <span className="text-xs bg-green-500/10 text-green-400 px-2 py-1 rounded-full">Session Warming</span>}
                {antiBan.random_delays && <span className="text-xs bg-blue-500/10 text-blue-400 px-2 py-1 rounded-full">Random Delays</span>}
                {antiBan.typing_speed !== 'fast' && <span className="text-xs bg-[#833AB4]/10 text-[#c084fc] px-2 py-1 rounded-full capitalize">{antiBan.typing_speed} Typing</span>}
                {antiBan.tab_cooldown_min > 5 && <span className="text-xs bg-yellow-500/10 text-yellow-400 px-2 py-1 rounded-full">{antiBan.tab_cooldown_min}–{antiBan.tab_cooldown_max}s Cooldown</span>}
                {antiBan.debug_screenshots && <span className="text-xs bg-orange-500/10 text-orange-400 px-2 py-1 rounded-full">Debug Screenshots</span>}
              </div>
            </div>
          )}
        </div>

        {/* ── Logs ── */}
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-2xl overflow-hidden">
          <button
            onClick={() => setShowLogs(!showLogs)}
            className="w-full flex items-center justify-between p-4 text-sm text-gray-400 hover:text-gray-300 cursor-pointer"
          >
            <span className="flex items-center gap-2">
              <Clock className="w-4 h-4" /> Activity Log
              <span className="text-xs text-gray-600">({logs.length})</span>
            </span>
            {showLogs ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
          {showLogs && (
            <div className="border-t border-[#1e1e2e] p-4 max-h-60 overflow-y-auto bg-[#0a0a0f]/80 font-mono text-xs space-y-0.5">
              {logs.length === 0 && <p className="text-gray-600">No activity yet...</p>}
              {logs.map((l, i) => (
                <p key={i} className="text-gray-500">{l}</p>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#1e1e2e] py-4 mt-8">
        <p className="text-center text-xs text-gray-600">Instagram Creator PRO v3.0 &mdash; For authorized use only</p>
      </footer>
    </div>
  );
}

/* ─── Stat Card Component ─── */
function StatCard({ label, value, icon, color, bg }: { label: string; value: number; icon: React.ReactNode; color: string; bg: string }) {
  return (
    <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4 flex items-center gap-3">
      <div className={`w-10 h-10 rounded-lg ${bg} flex items-center justify-center ${color}`}>{icon}</div>
      <div>
        <p className="text-2xl font-bold text-white">{value}</p>
        <p className="text-xs text-gray-500">{label}</p>
      </div>
    </div>
  );
}
