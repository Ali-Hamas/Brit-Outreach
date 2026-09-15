import React, { useState, useEffect } from 'react';
import {
  fetchBusinesses, fetchCampaigns, launchCampaign, fetchProspects,
  uploadProspectsCSV, createProspect, fetchAllSMTPConfigs, fetchCadenceStatus,
  triggerCadenceCalling, triggerDirectColdCalling, fetchVoiceJobs, syncVoiceOutcomes,
  chatWithInfluencerAgent, addInfluencerToCampaign
} from './api';

const PRODUCT_DEFINITIONS = [
  {
    id: 'camp-ai-consultancy',
    name: 'AI Consultancy — AI & Business Transformation',
    tagline: 'AI Strategy Sprints, Automated Copilots & Enterprise Workflows',
    hook: 'Cut operational costs by up to 40% with custom autonomous AI agent workflows in 2-4 weeks.',
    pitch: 'We help UK/US leadership deploy high-impact AI agents and automation without costly R&D.',
    icon: '🧠',
    color: 'border-purple-500/30 bg-purple-950/20'
  },
  {
    id: 'camp-talentbridge',
    name: 'TalentBridge — AI & Tech Talent Provision',
    tagline: 'Pre-Vetted Senior Engineers & Squads on Lease',
    hook: 'Save 60% compared to local hiring with zero recruiter overhead; start in under 2 weeks.',
    pitch: 'Eliminate hiring bottlenecks with pre-vetted AI, DevOps, and Full-Stack remote squads.',
    icon: '👥',
    color: 'border-blue-500/30 bg-blue-950/20'
  },
  {
    id: 'camp-biometric',
    name: 'Biometric Sign Up — Passwordless Tech',
    tagline: 'Frictionless Identity Verification & Security',
    hook: 'Eliminate phishing and password resets while boosting onboarding conversion rates.',
    pitch: 'GDPR and ISO 27001 compliant biometric authentication for SaaS, FinTech, and healthcare.',
    icon: '🔐',
    color: 'border-emerald-500/30 bg-emerald-950/20'
  },
  {
    id: 'camp-sentrivault',
    name: 'Sentrivault — NHS & Enterprise Compliance Vault',
    tagline: 'Zero-Knowledge Biometric Vault & NHS DTAC Pack',
    hook: 'Full NHS DTAC and DSPT compliance pack ready in 30 days (£990 launch offer).',
    pitch: 'Guaranteed NHS DTAC compliance in 30 days to avoid losing critical healthcare vendor contracts.',
    icon: '🛡️',
    color: 'border-amber-500/30 bg-amber-950/20'
  }
];

export default function App() {
  const [businesses, setBusinesses] = useState([]);
  const [selectedBiz, setSelectedBiz] = useState(null);
  const [campaigns, setCampaigns] = useState([]);
  const [prospects, setProspects] = useState([]);
  const [smtps, setSmtps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState('lead_gen'); // 'lead_gen', 'cadence', 'direct_calling', 'campaigns', 'prospects', 'call_logs'
  const [msg, setMsg] = useState({ type: '', text: '' });

  // Cadence State
  const [cadenceStatus, setCadenceStatus] = useState(null);
  const [cadenceHours, setCadenceHours] = useState(48);
  const [cadenceDryRun, setCadenceDryRun] = useState(false);

  // Direct Cold Calling State
  const [selectedProduct, setSelectedProduct] = useState(PRODUCT_DEFINITIONS[0].id);
  const [selectedProspectIds, setSelectedProspectIds] = useState([]);

  // Voice Jobs State
  const [voiceJobs, setVoiceJobs] = useState([]);

  // Lead Generation Hub State
  const [leadGenMode, setLeadGenMode] = useState('ai_search'); // 'ai_search', 'csv_upload', 'quick_add'
  const [aiQuery, setAiQuery] = useState('Find 5 UK YouTube tech influencers reviewing AI SaaS tools with business emails');
  const [aiSearching, setAiSearching] = useState(false);
  const [aiResults, setAiResults] = useState(null);
  const [quickLead, setQuickLead] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    company: '',
    title: '',
    campaign_id: PRODUCT_DEFINITIONS[0].id
  });

  useEffect(() => {
    init();
  }, []);

  async function init() {
    try {
      const list = await fetchBusinesses();
      setBusinesses(list);
      if (list.length > 0) {
        setSelectedBiz(list[0]);
        await loadAll(list[0].id);
      }
    } catch (e) {
      console.error(e);
      showMsg('error', 'Initialization error: ' + e.message);
    }
  }

  async function loadAll(bizId) {
    setLoading(true);
    try {
      const [c, p, s, cad, jobs] = await Promise.all([
        fetchCampaigns(bizId),
        fetchProspects(bizId),
        fetchAllSMTPConfigs(),
        fetchCadenceStatus(cadenceHours, bizId),
        fetchVoiceJobs(50)
      ]);
      setCampaigns(c);
      setProspects(p);
      setSmtps(s);
      setCadenceStatus(cad);
      setVoiceJobs(jobs.jobs || []);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  }

  function showMsg(type, text) {
    setMsg({ type, text });
    setTimeout(() => {
      setMsg({ type: '', text: '' });
    }, 6000);
  }

  // 1. Upload CSV Leads
  async function handleUpload(file) {
    if (!selectedBiz || !file) return;
    setLoading(true);
    try {
      const res = await uploadProspectsCSV(selectedBiz.id, file);
      showMsg('success', `Successfully imported ${res.imported_count} leads! (${res.skipped_count} duplicates skipped)`);
      await loadAll(selectedBiz.id);
      setTab('prospects');
    } catch (e) {
      showMsg('error', 'CSV Upload Error: ' + e.message);
    }
    setLoading(false);
  }

  // 2. Quick Add Single Lead
  async function handleQuickAdd(e) {
    e.preventDefault();
    if (!selectedBiz || !quickLead.email) return;
    setLoading(true);
    try {
      await createProspect({
        business_id: selectedBiz.id,
        ...quickLead
      });
      showMsg('success', `Added lead: ${quickLead.first_name} ${quickLead.last_name} (${quickLead.email})`);
      setQuickLead({
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        company: '',
        title: '',
        campaign_id: PRODUCT_DEFINITIONS[0].id
      });
      await loadAll(selectedBiz.id);
      setTab('prospects');
    } catch (err) {
      showMsg('error', 'Failed adding lead: ' + err.message);
    }
    setLoading(false);
  }

  // 3. AI Lead & Influencer Search
  async function handleAiSearch() {
    if (!aiQuery.trim()) return;
    setAiSearching(true);
    try {
      const res = await chatWithInfluencerAgent(aiQuery);
      setAiResults(res);
      showMsg('info', `AI Search finished! Discovered ${res.influencers?.length || 0} contacts.`);
    } catch (err) {
      showMsg('error', 'AI Search failed: ' + err.message);
    }
    setAiSearching(false);
  }

  // 4. Add Discovered Influencer to Leads
  async function handleAddDiscovered(inf) {
    if (!selectedBiz) return;
    try {
      await addInfluencerToCampaign({
        business_id: selectedBiz.id,
        campaign_id: selectedProduct,
        influencer_name: inf.name,
        handle: inf.handle,
        platform: inf.platform,
        niche: inf.niche,
        contact_email: inf.contact_email,
        followers_count: inf.followers_count,
        affiliate_fit_score: inf.affiliate_fit_score || 85,
        profile_url: inf.profile_url
      });
      showMsg('success', `Added ${inf.name} (${inf.contact_email}) to Leads & BritCRM!`);
      await loadAll(selectedBiz.id);
    } catch (err) {
      showMsg('error', 'Failed adding lead: ' + err.message);
    }
  }

  // 5. Launch Email Campaign
  async function handleLaunchCampaign(campId) {
    setLoading(true);
    try {
      const res = await launchCampaign(campId);
      showMsg('success', `Dispatched outreach emails to ${res.emails_sent} qualified leads!`);
      await loadAll(selectedBiz.id);
    } catch (e) {
      showMsg('error', 'Campaign Launch Error: ' + e.message);
    }
    setLoading(false);
  }

  // 6. Trigger 48-Hour Cold Call Cadence for Non-Replied Leads
  async function handleTriggerCadence() {
    setLoading(true);
    try {
      const res = await triggerCadenceCalling(cadenceHours, cadenceDryRun, selectedBiz.id);
      if (res.dry_run) {
        showMsg('info', `[DRY-RUN] Found ${res.enqueued_count} unreplied leads ready for calling.`);
      } else {
        showMsg('success', `Queued ${res.enqueued_count} non-replied leads for automated cold calling!`);
      }
      await loadAll(selectedBiz.id);
    } catch (e) {
      showMsg('error', 'Cadence Calling Error: ' + e.message);
    }
    setLoading(false);
  }

  // 7. Direct Cold Calling (Instant Calling without Email)
  async function handleDirectColdCall() {
    if (selectedProspectIds.length === 0) {
      showMsg('error', 'Please select at least one prospect with a phone number.');
      return;
    }
    setLoading(true);
    try {
      const res = await triggerDirectColdCalling(selectedProspectIds, selectedProduct, selectedBiz.id);
      showMsg('success', `Direct Cold Calling Started! Queued ${res.enqueued_count} calls for ${res.product_selected}.`);
      setSelectedProspectIds([]);
      await loadAll(selectedBiz.id);
      setTab('call_logs');
    } catch (e) {
      showMsg('error', 'Direct Calling Error: ' + e.message);
    }
    setLoading(false);
  }

  // 8. Sync Voice Outcomes
  async function handleSyncOutcomes() {
    setLoading(true);
    try {
      const res = await syncVoiceOutcomes();
      showMsg('success', `Synced ${res.synced_prospects} call outcomes back to CRM pipeline!`);
      await loadAll(selectedBiz.id);
    } catch (e) {
      showMsg('error', 'Sync Outcomes Error: ' + e.message);
    }
    setLoading(false);
  }

  function toggleProspectSelection(id) {
    setSelectedProspectIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  }

  function selectAllProspectsWithPhones() {
    const idsWithPhones = prospects
      .filter(p => p.phone && p.phone.trim().length >= 7)
      .map(p => p.id);
    setSelectedProspectIds(idsWithPhones);
  }

  const activeProduct = PRODUCT_DEFINITIONS.find(p => p.id === selectedProduct) || PRODUCT_DEFINITIONS[0];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navigation Bar */}
      <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-30 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 flex items-center justify-center font-black text-xl shadow-md text-white">
              A
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold tracking-tight text-white">Ascentra Global</h1>
                <span className="text-[10px] bg-blue-500/20 text-blue-300 font-semibold px-2 py-0.5 rounded-full border border-blue-500/30">
                  Client Hunter Suite
                </span>
              </div>
              <p className="text-xs text-slate-400">Autonomous Email Outreach & Real-Time AI Cold Calling Engine</p>
            </div>
          </div>

          {/* System Status Indicators */}
          <div className="flex items-center gap-3 text-xs">
            <div className="flex items-center gap-1.5 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700/60">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="text-slate-300">Sender:</span>
              <span className="text-emerald-300 font-mono">info@ascentraconsulting.co.uk</span>
            </div>
            <div className="flex items-center gap-1.5 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700/60">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
              <span className="text-slate-300">Caller ID:</span>
              <span className="text-cyan-300 font-mono">+16814056546 (Sarah)</span>
            </div>
            <div className="flex items-center gap-1.5 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700/60">
              <span className="text-slate-400">Total Leads:</span>
              <span className="text-white font-bold">{prospects.length}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-slate-900/60 border-b border-slate-800 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 flex gap-2 overflow-x-auto py-2">
          {[
            { id: 'lead_gen', label: 'Lead Generation Hub', icon: '🎯', highlight: true },
            { id: 'cadence', label: 'Multi-Channel Cadence (Email → Cold Call)', icon: '🔄', badge: cadenceStatus?.funnel?.unreplied_ready_for_call },
            { id: 'direct_calling', label: 'Direct Cold Calling Mode', icon: '📞' },
            { id: 'campaigns', label: 'Email Campaigns', icon: '📢' },
            { id: 'call_logs', label: 'Live Call Queue & Outcomes', icon: '📊', badge: voiceJobs.length },
            { id: 'prospects', label: 'CRM Prospects', icon: '👥', badge: prospects.length },
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                tab === t.id
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                  : t.highlight
                  ? 'bg-emerald-950/40 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-900/50'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <span>{t.icon}</span>
              <span>{t.label}</span>
              {t.badge !== undefined && t.badge > 0 && (
                <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                  tab === t.id ? 'bg-white text-blue-900' : 'bg-slate-700 text-slate-200'
                }`}>
                  {t.badge}
                </span>
              )}
            </button>
          ))}
        </div>
      </nav>

      {/* Notification Toast */}
      {msg.text && (
        <div className="max-w-7xl mx-auto px-4 pt-4 w-full">
          <div className={`p-3 rounded-xl text-sm flex items-center justify-between border ${
            msg.type === 'error'
              ? 'bg-rose-950/80 border-rose-700 text-rose-200'
              : msg.type === 'info'
              ? 'bg-cyan-950/80 border-cyan-700 text-cyan-200'
              : 'bg-emerald-950/80 border-emerald-700 text-emerald-200'
          }`}>
            <span>{msg.text}</span>
            <button onClick={() => setMsg({ type: '', text: '' })} className="font-bold opacity-70 hover:opacity-100">✕</button>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 py-6 flex-1 w-full">

        {/* ------------------------------------------------------------- */}
        {/* TAB 0: LEAD GENERATION HUB (AI Search + CSV + Quick Add) */}
        {/* ------------------------------------------------------------- */}
        {tab === 'lead_gen' && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-emerald-500/30 rounded-2xl p-6 shadow-xl">
              <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
                <div>
                  <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <span>🎯</span> Lead Generation & Discovery Hub
                  </h2>
                  <p className="text-xs text-slate-400 mt-1">
                    Feed your client hunting pipeline. Generate leads with AI web search, import bulk CSV files, or add decision-makers manually.
                  </p>
                </div>

                {/* Sub Mode Selector */}
                <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
                  <button
                    onClick={() => setLeadGenMode('ai_search')}
                    className={`px-3 py-1.5 rounded-lg font-semibold transition ${
                      leadGenMode === 'ai_search' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    🤖 AI Web Discovery
                  </button>
                  <button
                    onClick={() => setLeadGenMode('csv_upload')}
                    className={`px-3 py-1.5 rounded-lg font-semibold transition ${
                      leadGenMode === 'csv_upload' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    📁 Bulk CSV Import
                  </button>
                  <button
                    onClick={() => setLeadGenMode('quick_add')}
                    className={`px-3 py-1.5 rounded-lg font-semibold transition ${
                      leadGenMode === 'quick_add' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    ➕ Quick Add Single Lead
                  </button>
                </div>
              </div>

              {/* Sub-Mode 1: AI Lead Discovery */}
              {leadGenMode === 'ai_search' && (
                <div className="space-y-4">
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <label className="text-xs font-bold uppercase text-slate-300 tracking-wider block mb-2">
                      Enter Search Prompt for AI Agent (Live Web Scraping + Groq LLM):
                    </label>
                    <div className="flex gap-3">
                      <input
                        type="text"
                        value={aiQuery}
                        onChange={(e) => setAiQuery(e.target.value)}
                        placeholder="e.g. Find 5 UK YouTube tech influencers reviewing AI SaaS tools with business emails..."
                        className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 font-medium"
                      />
                      <button
                        onClick={handleAiSearch}
                        disabled={aiSearching || !aiQuery.trim()}
                        className="bg-emerald-600 hover:bg-emerald-500 text-white px-5 py-2.5 rounded-xl text-xs font-bold shadow-lg shadow-emerald-600/30 transition disabled:opacity-40 flex items-center gap-2"
                      >
                        {aiSearching ? <span>Searching Live Web...</span> : <span>🔍 Run AI Hunter</span>}
                      </button>
                    </div>
                    <div className="flex gap-2 mt-3 text-[11px] text-slate-400">
                      <span className="text-slate-500">Suggested:</span>
                      <button onClick={() => setAiQuery('Find 5 UK YouTube tech influencers reviewing AI SaaS tools with business emails')} className="hover:text-emerald-400 underline">UK AI Influencers</button>
                      <span>•</span>
                      <button onClick={() => setAiQuery('Find B2B SaaS creators and newsletters covering cyber security')} className="hover:text-emerald-400 underline">Cyber Security Creators</button>
                    </div>
                  </div>

                  {/* AI Results Table */}
                  {aiResults && (
                    <div className="border border-slate-800 rounded-xl overflow-hidden mt-4">
                      <div className="bg-slate-950 p-3 border-b border-slate-800 flex items-center justify-between text-xs">
                        <span className="font-semibold text-emerald-400">
                          Discovered {aiResults.influencers?.length || 0} Contacts from Live Web
                        </span>
                        <span className="text-slate-500 text-[11px]">Model: {aiResults.model_used || 'Groq AI'}</span>
                      </div>
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-800/80 text-slate-300 uppercase font-semibold">
                          <tr>
                            <th className="p-3">Creator / Profile</th>
                            <th className="p-3">Channel / Handle</th>
                            <th className="p-3">Business Email</th>
                            <th className="p-3">Niche / Audience</th>
                            <th className="p-3">Fit Score</th>
                            <th className="p-3">Action</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                          {(aiResults.influencers || []).map((inf, idx) => (
                            <tr key={idx} className="hover:bg-slate-800/40 transition">
                              <td className="p-3 font-semibold text-white">{inf.name}</td>
                              <td className="p-3 text-cyan-300 font-mono">{inf.handle}</td>
                              <td className="p-3 font-mono text-emerald-300">{inf.contact_email}</td>
                              <td className="p-3 text-slate-400">{inf.niche} ({inf.followers_count || 'N/A'})</td>
                              <td className="p-3">
                                <span className="bg-emerald-950 text-emerald-300 border border-emerald-700 px-2 py-0.5 rounded text-[10px] font-bold">
                                  {inf.affiliate_fit_score || 85}
                                </span>
                              </td>
                              <td className="p-3">
                                <button
                                  onClick={() => handleAddDiscovered(inf)}
                                  className="bg-blue-600 hover:bg-blue-500 text-white px-3 py-1 rounded-lg text-[11px] font-semibold transition"
                                >
                                  🚀 Add to Leads
                                </button>
                              </td>
                            </tr>
                          ))}
                          {(!aiResults.influencers || aiResults.influencers.length === 0) && (
                            <tr>
                              <td colSpan="6" className="p-6 text-center text-slate-500">
                                {aiResults.response_text || 'No verified email contacts found for this specific query. Try another query.'}
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* Sub-Mode 2: Bulk CSV Import */}
              {leadGenMode === 'csv_upload' && (
                <div className="space-y-4">
                  <div className="border-2 border-dashed border-slate-700 hover:border-emerald-500 rounded-2xl p-8 bg-slate-950/60 text-center transition group">
                    <label className="cursor-pointer block">
                      <div className="w-12 h-12 rounded-xl bg-emerald-600/20 text-emerald-400 flex items-center justify-center text-2xl mx-auto mb-3 border border-emerald-500/30">
                        📁
                      </div>
                      <span className="text-sm font-bold text-emerald-400 group-hover:text-emerald-300">
                        Click here to select and upload your CSV file
                      </span>
                      <p className="text-xs text-slate-500 mt-1">
                        Automatically parses emails, full names, companies, titles, and <strong>phone numbers (+44...)</strong>
                      </p>
                      <input
                        type="file"
                        accept=".csv"
                        className="hidden"
                        onChange={(e) => e.target.files[0] && handleUpload(e.target.files[0])}
                      />
                    </label>
                  </div>

                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs">
                    <p className="font-semibold text-slate-300 mb-2">Supported Column Format:</p>
                    <code className="text-emerald-400 font-mono bg-slate-900 p-2.5 rounded border border-slate-800 block">
                      email,first_name,last_name,company,title,industry,location,phone
                    </code>
                    <p className="text-slate-500 text-[11px] mt-2">
                      * Tip: Providing phone numbers with the country code (e.g. <span className="text-cyan-400 font-mono">+447911123456</span>) allows Sarah to immediately call non-replied leads after 48h!
                    </p>
                  </div>
                </div>
              )}

              {/* Sub-Mode 3: Quick Add Single Lead */}
              {leadGenMode === 'quick_add' && (
                <form onSubmit={handleQuickAdd} className="bg-slate-950 p-5 rounded-xl border border-slate-800 space-y-4">
                  <h3 className="text-xs font-bold uppercase text-slate-300 tracking-wider">
                    Add Single Lead Directly to Pipeline & Cold Caller
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div>
                      <label className="text-slate-400 block mb-1">First Name *</label>
                      <input
                        type="text"
                        required
                        value={quickLead.first_name}
                        onChange={(e) => setQuickLead({ ...quickLead, first_name: e.target.value })}
                        placeholder="John"
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-white"
                      />
                    </div>
                    <div>
                      <label className="text-slate-400 block mb-1">Last Name</label>
                      <input
                        type="text"
                        value={quickLead.last_name}
                        onChange={(e) => setQuickLead({ ...quickLead, last_name: e.target.value })}
                        placeholder="Smith"
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-white"
                      />
                    </div>
                    <div>
                      <label className="text-slate-400 block mb-1">Email Address *</label>
                      <input
                        type="email"
                        required
                        value={quickLead.email}
                        onChange={(e) => setQuickLead({ ...quickLead, email: e.target.value })}
                        placeholder="john.smith@company.co.uk"
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-white font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-slate-400 block mb-1">Phone Number (For Sarah)</label>
                      <input
                        type="text"
                        value={quickLead.phone}
                        onChange={(e) => setQuickLead({ ...quickLead, phone: e.target.value })}
                        placeholder="+447911123456"
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-white font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-slate-400 block mb-1">Company</label>
                      <input
                        type="text"
                        value={quickLead.company}
                        onChange={(e) => setQuickLead({ ...quickLead, company: e.target.value })}
                        placeholder="Acme Enterprise Ltd"
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-white"
                      />
                    </div>
                    <div>
                      <label className="text-slate-400 block mb-1">Job Title</label>
                      <input
                        type="text"
                        value={quickLead.title}
                        onChange={(e) => setQuickLead({ ...quickLead, title: e.target.value })}
                        placeholder="Chief Technology Officer"
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-white"
                      />
                    </div>
                  </div>

                  <div className="pt-2 flex justify-end">
                    <button
                      type="submit"
                      disabled={loading}
                      className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2.5 rounded-xl text-xs font-bold shadow-lg shadow-emerald-600/30 transition"
                    >
                      ➕ Save Lead to Database
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* TAB 1: MULTI-CHANNEL CADENCE (Email -> Wait 48h -> Cold Call) */}
        {/* ------------------------------------------------------------- */}
        {tab === 'cadence' && (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-slate-900 via-indigo-950/50 to-slate-900 border border-indigo-500/30 rounded-2xl p-6 shadow-xl relative overflow-hidden">
              <div className="relative z-10">
                <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
                  <div>
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                      <span>🚀</span> Multi-Channel Automated Cadence Pipeline
                    </h2>
                    <p className="text-xs text-indigo-200/80 mt-1">
                      Rule: Send personalized email from <code className="text-cyan-300 font-mono">info@ascentraconsulting.co.uk</code>.
                      If the prospect does not reply within {cadenceHours} hours, Sarah automatically calls them with campaign context!
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2 bg-slate-900/80 px-3 py-1.5 rounded-xl border border-slate-700 text-xs">
                      <span className="text-slate-400">Wait Window:</span>
                      <select
                        value={cadenceHours}
                        onChange={(e) => {
                          setCadenceHours(Number(e.target.value));
                          loadAll(selectedBiz?.id);
                        }}
                        className="bg-slate-800 text-white rounded px-2 py-0.5 border border-slate-600 font-semibold"
                      >
                        <option value="0">0 Hours (Immediate Test)</option>
                        <option value="12">12 Hours</option>
                        <option value="24">24 Hours</option>
                        <option value="48">48 Hours (Standard)</option>
                        <option value="72">72 Hours</option>
                      </select>
                    </div>

                    <label className="flex items-center gap-2 text-xs text-slate-300 bg-slate-900/80 px-3 py-1.5 rounded-xl border border-slate-700 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={cadenceDryRun}
                        onChange={(e) => setCadenceDryRun(e.target.checked)}
                        className="rounded border-slate-600 text-blue-600"
                      />
                      <span>Dry Run Preview</span>
                    </label>

                    <button
                      onClick={handleTriggerCadence}
                      disabled={loading || (cadenceStatus?.funnel?.unreplied_ready_for_call || 0) === 0}
                      className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white px-5 py-2.5 rounded-xl text-xs font-bold shadow-lg shadow-indigo-600/30 transition disabled:opacity-40 flex items-center gap-2"
                    >
                      <span>📞</span>
                      <span>Run Voice Cadence ({cadenceStatus?.funnel?.unreplied_ready_for_call || 0} Ready)</span>
                    </button>
                  </div>
                </div>

                {/* Cadence Funnel Cards */}
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 mt-4">
                  <div className="bg-slate-900/90 border border-slate-800 p-3.5 rounded-xl">
                    <p className="text-[11px] text-slate-400 uppercase font-semibold">Total Leads</p>
                    <p className="text-2xl font-bold text-white mt-1">{cadenceStatus?.funnel?.total_leads || prospects.length}</p>
                    <p className="text-[10px] text-slate-500 mt-1">In Database</p>
                  </div>

                  <div className="bg-slate-900/90 border border-slate-800 p-3.5 rounded-xl">
                    <p className="text-[11px] text-blue-400 uppercase font-semibold">Step 1: Emailed</p>
                    <p className="text-2xl font-bold text-blue-300 mt-1">{cadenceStatus?.funnel?.emails_dispatched || 0}</p>
                    <p className="text-[10px] text-blue-400/70 mt-1">Initial Contact</p>
                  </div>

                  <div className="bg-slate-900/90 border border-slate-800 p-3.5 rounded-xl">
                    <p className="text-[11px] text-emerald-400 uppercase font-semibold">Email Replied</p>
                    <p className="text-2xl font-bold text-emerald-300 mt-1">{cadenceStatus?.funnel?.inbound_replies || 0}</p>
                    <p className="text-[10px] text-emerald-400/70 mt-1">AI Handled</p>
                  </div>

                  <div className="bg-slate-900/90 border border-amber-500/30 p-3.5 rounded-xl bg-amber-950/10">
                    <p className="text-[11px] text-amber-400 uppercase font-semibold">No Reply (&gt;{cadenceHours}h)</p>
                    <p className="text-2xl font-bold text-amber-300 mt-1">{cadenceStatus?.funnel?.unreplied_leads || 0}</p>
                    <p className="text-[10px] text-amber-400/70 mt-1">{cadenceStatus?.funnel?.unreplied_ready_for_call || 0} have phones</p>
                  </div>

                  <div className="bg-slate-900/90 border border-cyan-500/30 p-3.5 rounded-xl bg-cyan-950/10">
                    <p className="text-[11px] text-cyan-400 uppercase font-semibold">Calls Queued</p>
                    <p className="text-2xl font-bold text-cyan-300 mt-1">{cadenceStatus?.funnel?.calls_currently_queued || 0}</p>
                    <p className="text-[10px] text-cyan-400/70 mt-1">In Voice Queue</p>
                  </div>

                  <div className="bg-slate-900/90 border border-purple-500/30 p-3.5 rounded-xl bg-purple-950/10">
                    <p className="text-[11px] text-purple-400 uppercase font-semibold">Meetings Booked</p>
                    <p className="text-2xl font-bold text-purple-300 mt-1">{cadenceStatus?.funnel?.meetings_booked || 0}</p>
                    <p className="text-[10px] text-purple-400/70 mt-1">For Syed Islam</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Unreplied Leads List Ready for Cold Calling */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-md">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <span>⏳</span> Unreplied Prospects Eligible for Voice Follow-up
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    These leads were emailed &gt;={cadenceHours}h ago and have not replied yet. They will receive an automated cold call from Sarah.
                  </p>
                </div>
                <button
                  onClick={() => loadAll(selectedBiz?.id)}
                  className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg border border-slate-700"
                >
                  🔄 Refresh Status
                </button>
              </div>

              <div className="overflow-x-auto border border-slate-800 rounded-xl">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-800/80 text-slate-300 uppercase tracking-wider font-semibold">
                    <tr>
                      <th className="p-3">Decision Maker</th>
                      <th className="p-3">Company & Title</th>
                      <th className="p-3">Email</th>
                      <th className="p-3">Phone (For Sarah)</th>
                      <th className="p-3">Email Sent</th>
                      <th className="p-3">Cadence Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {(cadenceStatus?.eligible_leads || []).map((lead) => (
                      <tr key={lead.id} className="hover:bg-slate-800/40 transition">
                        <td className="p-3 font-semibold text-white">{lead.name}</td>
                        <td className="p-3 text-slate-300">
                          <div>{lead.company}</div>
                          <div className="text-[11px] text-slate-400">{lead.title}</div>
                        </td>
                        <td className="p-3 font-mono text-slate-300">{lead.email}</td>
                        <td className="p-3 font-mono">
                          {lead.has_valid_phone ? (
                            <span className="text-cyan-300 font-semibold">{lead.phone}</span>
                          ) : (
                            <span className="text-rose-400 italic">No Phone Number</span>
                          )}
                        </td>
                        <td className="p-3 text-slate-400">
                          {lead.hours_since_email !== null ? `${lead.hours_since_email}h ago` : '-'}
                        </td>
                        <td className="p-3">
                          {lead.has_valid_phone ? (
                            <span className="bg-amber-500/20 text-amber-300 border border-amber-500/30 px-2 py-0.5 rounded-full text-[10px] font-bold">
                              Ready for Cold Call
                            </span>
                          ) : (
                            <span className="bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full text-[10px]">
                              Email Only
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                    {(!cadenceStatus?.eligible_leads || cadenceStatus.eligible_leads.length === 0) && (
                      <tr>
                        <td colSpan="6" className="p-8 text-center text-slate-500">
                          No unreplied leads waiting right now. Either all leads replied, or wait window has not elapsed.
                          Try setting Wait Window to "0 Hours (Immediate Test)" above.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* TAB 2: DIRECT COLD CALLING MODE (Instant Calling without Email) */}
        {/* ------------------------------------------------------------- */}
        {tab === 'direct_calling' && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-emerald-500/30 rounded-2xl p-6 shadow-xl">
              <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
                <div>
                  <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <span>🎯</span> Direct Cold Calling Mode (Instant Dialing)
                  </h2>
                  <p className="text-xs text-slate-400 mt-1">
                    Select which Ascentra Global product Sarah will pitch, select your target leads, and start outbound calls immediately without waiting for emails.
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={selectAllProspectsWithPhones}
                    className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3.5 py-2 rounded-xl border border-slate-700 font-semibold"
                  >
                    ✓ Select All with Phones
                  </button>
                  <button
                    onClick={handleDirectColdCall}
                    disabled={loading || selectedProspectIds.length === 0}
                    className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white px-6 py-2.5 rounded-xl text-xs font-bold shadow-lg shadow-emerald-600/30 transition disabled:opacity-40 flex items-center gap-2"
                  >
                    <span>📞</span>
                    <span>Start Direct Cold Calling ({selectedProspectIds.length} Leads)</span>
                  </button>
                </div>
              </div>

              {/* Step 1: Product Selection Cards */}
              <div className="mb-6">
                <label className="text-xs font-bold uppercase text-slate-400 tracking-wider mb-2 block">
                  1. Select Product / Campaign for Cold Calling
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                  {PRODUCT_DEFINITIONS.map((prod) => (
                    <div
                      key={prod.id}
                      onClick={() => setSelectedProduct(prod.id)}
                      className={`cursor-pointer border rounded-xl p-4 transition-all ${
                        selectedProduct === prod.id
                          ? `${prod.color} border-2 ring-2 ring-emerald-500/40 shadow-lg`
                          : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      <div className="text-2xl mb-2">{prod.icon}</div>
                      <h4 className="font-bold text-sm text-white">{prod.name}</h4>
                      <p className="text-[11px] text-slate-400 mt-1 font-medium">{prod.tagline}</p>
                      <div className="mt-3 pt-2 border-t border-slate-800/80 text-[10px] text-slate-300">
                        <span className="font-semibold text-emerald-400">Sarah's Hook: </span>
                        {prod.hook}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Live Pitch Preview */}
              <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 mb-6">
                <p className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
                  <span>🎙️</span> Realtime AI Caller Pitch Preview (Sarah)
                </p>
                <p className="text-xs text-slate-300 mt-2 italic font-mono bg-slate-900 p-3 rounded-lg border border-slate-800">
                  "Hi [Lead Name], this is Sarah calling from Ascentra Global in London. I know I caught you out of the blue —
                  we are reaching out to technology leaders regarding <strong>{activeProduct.name}</strong>. {activeProduct.pitch}
                  Would you be open to a 15-minute introductory consultation with Syed Islam next week?"
                </p>
              </div>

              {/* Step 2: Select Leads Table */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-bold uppercase text-slate-400 tracking-wider">
                    2. Select Leads to Dial ({selectedProspectIds.length} selected)
                  </label>
                  <span className="text-xs text-slate-400">
                    Showing {prospects.length} leads in database
                  </span>
                </div>

                <div className="overflow-x-auto border border-slate-800 rounded-xl max-h-96">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-800/80 text-slate-300 uppercase tracking-wider font-semibold sticky top-0 z-10">
                      <tr>
                        <th className="p-3 w-10">
                          <input
                            type="checkbox"
                            checked={selectedProspectIds.length > 0 && selectedProspectIds.length === prospects.filter(p => p.phone).length}
                            onChange={(e) => {
                              if (e.target.checked) selectAllProspectsWithPhones();
                              else setSelectedProspectIds([]);
                            }}
                          />
                        </th>
                        <th className="p-3">Name</th>
                        <th className="p-3">Phone (Required)</th>
                        <th className="p-3">Company & Title</th>
                        <th className="p-3">Score</th>
                        <th className="p-3">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {prospects.map((p) => {
                        const hasPhone = Boolean(p.phone && p.phone.trim().length >= 7);
                        const isSelected = selectedProspectIds.includes(p.id);

                        return (
                          <tr
                            key={p.id}
                            onClick={() => hasPhone && toggleProspectSelection(p.id)}
                            className={`cursor-pointer transition ${
                              isSelected ? 'bg-emerald-950/30' : 'hover:bg-slate-800/40'
                            }`}
                          >
                            <td className="p-3">
                              <input
                                type="checkbox"
                                disabled={!hasPhone}
                                checked={isSelected}
                                onChange={() => {}}
                              />
                            </td>
                            <td className="p-3 font-semibold text-white">
                              {p.first_name} {p.last_name || ''}
                            </td>
                            <td className="p-3 font-mono">
                              {hasPhone ? (
                                <span className="text-emerald-300 font-semibold">{p.phone}</span>
                              ) : (
                                <span className="text-slate-500 italic">No Phone (Upload phone to call)</span>
                              )}
                            </td>
                            <td className="p-3 text-slate-300">
                              <div>{p.company || '-'}</div>
                              <div className="text-[11px] text-slate-400">{p.title || '-'}</div>
                            </td>
                            <td className="p-3">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                (p.score || 0) >= 80 ? 'bg-emerald-900/80 text-emerald-300' :
                                (p.score || 0) >= 60 ? 'bg-amber-900/80 text-amber-300' : 'bg-slate-800 text-slate-400'
                              }`}>
                                {p.score || 0}
                              </span>
                            </td>
                            <td className="p-3 text-slate-400 uppercase text-[10px]">
                              {p.status}
                            </td>
                          </tr>
                        );
                      })}
                      {prospects.length === 0 && (
                        <tr>
                          <td colSpan="6" className="p-8 text-center text-slate-500">
                            No prospects yet. Go to the "Lead Generation Hub" tab to add leads!
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* TAB 3: LIVE CALL QUEUE & OUTCOMES */}
        {/* ------------------------------------------------------------- */}
        {tab === 'call_logs' && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
              <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
                <div>
                  <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <span>📊</span> Outbound Calling Queue & Transcripts
                  </h2>
                  <p className="text-xs text-slate-400 mt-1">
                    Live calling queue managed by Voice Agent. Shows Sarah's active dials, completed calls, and booked appointments.
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={handleSyncOutcomes}
                    className="text-xs bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded-xl font-semibold shadow-md transition flex items-center gap-1.5"
                  >
                    <span>📥</span>
                    <span>Sync Booked Meetings to CRM</span>
                  </button>
                  <button
                    onClick={() => loadAll(selectedBiz?.id)}
                    className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3.5 py-2 rounded-xl border border-slate-700 font-semibold"
                  >
                    🔄 Refresh
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto border border-slate-800 rounded-xl">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-800/80 text-slate-300 uppercase tracking-wider font-semibold">
                    <tr>
                      <th className="p-3">Job ID</th>
                      <th className="p-3">Lead Contact</th>
                      <th className="p-3">Phone Number</th>
                      <th className="p-3">Product / Campaign</th>
                      <th className="p-3">Source / Mode</th>
                      <th className="p-3">Status</th>
                      <th className="p-3">Scheduled / Updated</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {voiceJobs.map((job) => (
                      <tr key={job.id} className="hover:bg-slate-800/40 transition">
                        <td className="p-3 font-mono text-slate-400">#{job.id}</td>
                        <td className="p-3 font-semibold text-white">
                          <div>{job.guest_name || 'Decision Maker'}</div>
                          <div className="text-[11px] text-slate-400">{job.context?.company || '-'}</div>
                        </td>
                        <td className="p-3 font-mono text-cyan-300 font-semibold">{job.to_number}</td>
                        <td className="p-3 text-slate-300">
                          <span className="font-medium text-white">{job.context?.campaign || 'Ascentra Advisory'}</span>
                        </td>
                        <td className="p-3">
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                            job.source === 'brit_cadence_48h'
                              ? 'bg-indigo-950 text-indigo-300 border border-indigo-700/50'
                              : 'bg-emerald-950 text-emerald-300 border border-emerald-700/50'
                          }`}>
                            {job.source === 'brit_cadence_48h' ? '48h Cadence' : 'Direct Call'}
                          </span>
                        </td>
                        <td className="p-3">
                          <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                            job.status === 'completed' ? 'bg-emerald-950 text-emerald-300 border border-emerald-600' :
                            job.status === 'in_call' || job.status === 'dialing' ? 'bg-cyan-950 text-cyan-300 border border-cyan-500 animate-pulse' :
                            job.status === 'queued' ? 'bg-amber-950 text-amber-300 border border-amber-600' :
                            'bg-slate-800 text-slate-400'
                          }`}>
                            {job.status}
                          </span>
                        </td>
                        <td className="p-3 text-slate-400">
                          {job.updated_at ? new Date(job.updated_at * 1000).toLocaleTimeString() : '-'}
                        </td>
                      </tr>
                    ))}
                    {voiceJobs.length === 0 && (
                      <tr>
                        <td colSpan="7" className="p-8 text-center text-slate-500">
                          No outbound calling jobs yet. Trigger 48-Hour Cadence or start a Direct Cold Call above to populate the queue!
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* TAB 4: EMAIL CAMPAIGNS */}
        {/* ------------------------------------------------------------- */}
        {tab === 'campaigns' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-white">Ascentra Global Campaigns</h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Core outbound email campaigns dispatched through universal corporate sender: <code className="text-emerald-400 font-mono">info@ascentraconsulting.co.uk</code>
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {campaigns.map((c) => {
                const step1 = c.sequence_config?.steps?.[0];
                const contactedCount = prospects.filter(p => p.campaign_id === c.id && (p.status === 'contacted' || p.status === 'meeting_booked')).length;
                const repliedCount = prospects.filter(p => p.campaign_id === c.id && (p.status === 'replied' || p.status === 'meeting_booked')).length;

                return (
                  <div key={c.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-md flex flex-col justify-between hover:border-slate-700 transition">
                    <div>
                      <div className="flex items-start justify-between gap-2">
                        <h3 className="font-bold text-base text-white">{c.name}</h3>
                        <span className="text-[10px] bg-blue-950 text-blue-300 border border-blue-800 px-2 py-0.5 rounded-full font-semibold">
                          Active
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 mt-2 font-medium">
                        Subject: <span className="text-slate-400">{step1?.subject || 'Outreach'}</span>
                      </p>
                      <div className="flex gap-4 mt-4 text-xs text-slate-400">
                        <div>
                          <span className="text-slate-500 block text-[10px]">Contacted:</span>
                          <span className="text-white font-bold">{contactedCount}</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block text-[10px]">Replies:</span>
                          <span className="text-emerald-400 font-bold">{repliedCount}</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block text-[10px]">From:</span>
                          <span className="text-slate-300 font-mono text-[11px]">info@ascentraconsulting.co.uk</span>
                        </div>
                      </div>
                    </div>

                    <div className="mt-5 pt-4 border-t border-slate-800 flex items-center justify-between">
                      <span className="text-[11px] text-slate-500">Step 1 Outreach</span>
                      <button
                        onClick={() => handleLaunchCampaign(c.id)}
                        disabled={loading || prospects.length === 0}
                        className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl text-xs font-bold shadow transition disabled:opacity-40"
                      >
                        🚀 Dispatch Campaign
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* TAB 5: CRM PROSPECTS TABLE */}
        {/* ------------------------------------------------------------- */}
        {tab === 'prospects' && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-xl font-bold text-white">All Prospects ({prospects.length})</h2>
                  <p className="text-xs text-slate-400 mt-0.5">Unified lead table synced across Email Outreach and Voice Agent</p>
                </div>
                <button
                  onClick={() => setTab('lead_gen')}
                  className="text-xs bg-emerald-600 hover:bg-emerald-500 text-white px-3.5 py-2 rounded-xl font-semibold shadow transition flex items-center gap-1.5"
                >
                  <span>➕</span>
                  <span>Add More Leads</span>
                </button>
              </div>

              <div className="overflow-x-auto border border-slate-800 rounded-xl">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-800/80 text-slate-300 uppercase tracking-wider font-semibold">
                    <tr>
                      <th className="p-3">Decision Maker</th>
                      <th className="p-3">Email Address</th>
                      <th className="p-3">Phone</th>
                      <th className="p-3">Company & Title</th>
                      <th className="p-3">Fit Score</th>
                      <th className="p-3">Current Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {prospects.map((p) => (
                      <tr key={p.id} className="hover:bg-slate-800/40 transition">
                        <td className="p-3 font-semibold text-white">
                          {p.first_name} {p.last_name || ''}
                        </td>
                        <td className="p-3 font-mono text-blue-400">{p.email}</td>
                        <td className="p-3 font-mono text-slate-300">{p.phone || '-'}</td>
                        <td className="p-3 text-slate-300">
                          <div>{p.company || '-'}</div>
                          <div className="text-[11px] text-slate-400">{p.title || '-'}</div>
                        </td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            (p.score || 0) >= 80 ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' :
                            (p.score || 0) >= 60 ? 'bg-amber-950 text-amber-300 border border-amber-800' :
                            'bg-slate-800 text-slate-400'
                          }`}>
                            {p.score || 0}
                          </span>
                        </td>
                        <td className="p-3">
                          <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                            p.status === 'meeting_booked' ? 'bg-purple-950 text-purple-300 border border-purple-700' :
                            p.status === 'replied' ? 'bg-emerald-950 text-emerald-300 border border-emerald-700' :
                            p.status === 'contacted' ? 'bg-blue-950 text-blue-300 border border-blue-700' :
                            'bg-slate-800 text-slate-400'
                          }`}>
                            {p.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                    {prospects.length === 0 && (
                      <tr>
                        <td colSpan="6" className="p-8 text-center text-slate-500">
                          No prospects in database. Go to "Lead Generation Hub" to add or discover leads!
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-800 py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 flex items-center justify-between text-xs text-slate-500">
          <div>Ascentra Global Ltd • Enterprise B2B Client Hunter Suite</div>
          <div className="flex items-center gap-4">
            <span>Powered by OpenAI Realtime & Groq</span>
            <span>London, UK</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
