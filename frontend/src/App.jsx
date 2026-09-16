import React, { useState, useEffect } from 'react';
import {
  fetchBusinesses, fetchCampaigns, launchCampaign, fetchProspects,
  uploadProspectsCSV, fetchAllSMTPConfigs, searchLeads, saveLeadsToCampaign
} from './api';

export default function App() {
  const [businesses, setBusinesses] = useState([]);
  const [selectedBiz, setSelectedBiz] = useState(null);
  const [campaigns, setCampaigns] = useState([]);
  const [prospects, setProspects] = useState([]);
  const [smtps, setSmtps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState('home');
  const [msg, setMsg] = useState('');
  const [msgType, setMsgType] = useState('success');

  // Lead search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [selectedLeads, setSelectedLeads] = useState([]);
  const [saveToCampaign, setSaveToCampaign] = useState('');

  useEffect(() => { init(); }, []);

  async function init() {
    try {
      const list = await fetchBusinesses();
      setBusinesses(list);
      if (list.length > 0) {
        setSelectedBiz(list[0]);
        await load(list[0].id);
      }
    } catch (e) { console.error(e); }
  }

  async function load(bizId) {
    setLoading(true);
    try {
      const [c, p, s] = await Promise.all([
        fetchCampaigns(bizId), fetchProspects(bizId), fetchAllSMTPConfigs()
      ]);
      setCampaigns(c);
      setProspects(p);
      setSmtps(s);
    } catch (e) { console.error(e); }
    setLoading(false);
  }

  function showMsg(text, type = 'success') {
    setMsg(text);
    setMsgType(type);
    setTimeout(() => setMsg(''), 5000);
  }

  async function handleUpload(file) {
    if (!selectedBiz || !file) return;
    setLoading(true);
    try {
      const res = await uploadProspectsCSV(selectedBiz.id, file);
      showMsg(`Imported ${res.imported_count} leads! ${res.skipped_count > 0 ? `(${res.skipped_count} skipped)` : ''}`);
      await load(selectedBiz.id);
    } catch (e) { showMsg('Upload error: ' + e.message, 'error'); }
    setLoading(false);
  }

  async function handleLaunch(campId) {
    setLoading(true);
    try {
      const res = await launchCampaign(campId);
      showMsg(`Sent ${res.emails_sent || 0} emails!`);
      await load(selectedBiz.id);
    } catch (e) { showMsg('Launch error: ' + e.message, 'error'); }
    setLoading(false);
  }

  async function handleSearch() {
    if (!searchQuery.trim() || !selectedBiz) return;
    setSearching(true);
    setSearchResults([]);
    setSelectedLeads([]);
    try {
      const res = await searchLeads(selectedBiz.id, searchQuery);
      setSearchResults(res.leads || []);
      showMsg(res.message || `Found ${res.leads_found} leads`);
    } catch (e) { showMsg('Search error: ' + e.message, 'error'); }
    setSearching(false);
  }

  function toggleLead(idx) {
    setSelectedLeads(prev =>
      prev.includes(idx) ? prev.filter(i => i !== idx) : [...prev, idx]
    );
  }

  function selectAll() {
    if (selectedLeads.length === searchResults.length) {
      setSelectedLeads([]);
    } else {
      setSelectedLeads(searchResults.map((_, i) => i));
    }
  }

  async function handleSaveLeads() {
    if (!selectedBiz || !saveToCampaign || selectedLeads.length === 0) return;
    setLoading(true);
    try {
      const leadsToSave = selectedLeads.map(i => searchResults[i]);
      const res = await saveLeadsToCampaign(selectedBiz.id, saveToCampaign, leadsToSave);
      showMsg(res.message || `Saved ${res.saved} leads`);
      setSearchResults([]);
      setSelectedLeads([]);
      setSaveToCampaign('');
      await load(selectedBiz.id);
    } catch (e) { showMsg('Save error: ' + e.message, 'error'); }
    setLoading(false);
  }

  const realEmailProspects = prospects.filter(p => !p.email.includes('placeholder'));

  return (
    <div style={{ minHeight: '100vh', background: '#0a0e1a', color: '#e2e8f0', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif' }}>

      {/* Header */}
      <header style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%)', borderBottom: '1px solid #1e293b', padding: '0 32px' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', height: '64px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '16px' }}>A</div>
            <div>
              <div style={{ fontWeight: '700', fontSize: '16px', letterSpacing: '-0.02em' }}>Ascentra Global</div>
              <div style={{ fontSize: '11px', color: '#64748b' }}>Outreach System</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
            <div style={{ fontSize: '12px', color: '#94a3b8' }}>
              <span style={{ color: '#4ade80', marginRight: '4px' }}>●</span>
              {realEmailProspects.length} leads
            </div>
            <div style={{ fontSize: '12px', color: '#94a3b8' }}>{campaigns.length} campaigns</div>
            {smtps.length > 0 && (
              <div style={{ fontSize: '11px', padding: '4px 10px', background: '#065f46', color: '#4ade80', borderRadius: '12px' }}>SMTP Active</div>
            )}
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav style={{ background: '#0f172a', borderBottom: '1px solid #1e293b', padding: '0 32px' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', gap: '4px' }}>
          {[
            { id: 'home', label: 'Dashboard' },
            { id: 'search', label: 'Find Leads' },
            { id: 'upload', label: 'Upload CSV' },
            { id: 'campaigns', label: 'Campaigns' },
            { id: 'leads', label: 'All Leads' },
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              style={{
                padding: '12px 16px',
                border: 'none',
                borderBottom: tab === t.id ? '2px solid #3b82f6' : '2px solid transparent',
                background: 'transparent',
                color: tab === t.id ? '#3b82f6' : '#64748b',
                fontWeight: '600',
                fontSize: '13px',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              {t.label}
            </button>
          ))}
        </div>
      </nav>

      {/* Message Banner */}
      {msg && (
        <div style={{
          maxWidth: '1200px', margin: '16px auto', padding: '12px 20px',
          borderRadius: '8px', fontSize: '13px', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          background: msgType === 'error' ? '#450a0a' : '#052e16',
          border: `1px solid ${msgType === 'error' ? '#7f1d1d' : '#14532d'}`,
          color: msgType === 'error' ? '#fca5a5' : '#86efac',
        }}>
          {msg}
          <button onClick={() => setMsg('')} style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', fontSize: '16px' }}>×</button>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '8px 32px' }}>
          <div style={{ height: '2px', background: '#1e293b', borderRadius: '2px', overflow: 'hidden' }}>
            <div style={{ height: '100%', background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)', animation: 'loading 1.5s infinite', width: '30%' }} />
          </div>
        </div>
      )}

      {/* Content */}
      <main style={{ maxWidth: '1200px', margin: '0 auto', padding: '32px' }}>

        {/* HOME */}
        {tab === 'home' && (
          <div>
            <h2 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '4px' }}>Welcome back, Syed</h2>
            <p style={{ color: '#64748b', fontSize: '14px', marginBottom: '32px' }}>Here's your outreach overview</p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '32px' }}>
              {[
                { label: 'Total Leads', value: prospects.length, color: '#3b82f6' },
                { label: 'Real Emails', value: realEmailProspects.length, color: '#22c55e' },
                { label: 'Campaigns', value: campaigns.length, color: '#8b5cf6' },
                { label: 'Contacted', value: prospects.filter(p => p.status === 'contacted').length, color: '#f59e0b' },
              ].map((s, i) => (
                <div key={i} style={{ background: '#111827', borderRadius: '12px', padding: '20px', border: '1px solid #1f2937' }}>
                  <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{s.label}</div>
                  <div style={{ fontSize: '28px', fontWeight: '700', color: s.color }}>{s.value}</div>
                </div>
              ))}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div onClick={() => setTab('search')} style={{ background: '#111827', borderRadius: '12px', padding: '24px', border: '1px solid #1f2937', cursor: 'pointer', transition: 'border-color 0.15s' }}
                onMouseEnter={e => e.currentTarget.style.borderColor = '#3b82f6'}
                onMouseLeave={e => e.currentTarget.style.borderColor = '#1f2937'}>
                <div style={{ fontSize: '20px', marginBottom: '8px' }}>🔍</div>
                <h3 style={{ fontSize: '15px', fontWeight: '600', marginBottom: '4px' }}>Find New Leads</h3>
                <p style={{ fontSize: '12px', color: '#64748b' }}>Search Reddit for people who need your services</p>
              </div>
              <div onClick={() => setTab('upload')} style={{ background: '#111827', borderRadius: '12px', padding: '24px', border: '1px solid #1f2937', cursor: 'pointer', transition: 'border-color 0.15s' }}
                onMouseEnter={e => e.currentTarget.style.borderColor = '#3b82f6'}
                onMouseLeave={e => e.currentTarget.style.borderColor = '#1f2937'}>
                <div style={{ fontSize: '20px', marginBottom: '8px' }}>📁</div>
                <h3 style={{ fontSize: '15px', fontWeight: '600', marginBottom: '4px' }}>Upload CSV</h3>
                <p style={{ fontSize: '12px', color: '#64748b' }}>Import your own list of leads from a spreadsheet</p>
              </div>
            </div>
          </div>
        )}

        {/* FIND LEADS */}
        {tab === 'search' && (
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '4px' }}>Find Real Leads</h2>
            <p style={{ color: '#64748b', fontSize: '13px', marginBottom: '24px' }}>Search for people who are actively looking for services like yours. Results come from Reddit.</p>

            <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="e.g. need AI automation agency, looking for CTO, hire web developer"
                style={{ flex: 1, padding: '12px 16px', borderRadius: '8px', border: '1px solid #334155', background: '#111827', color: '#e2e8f0', fontSize: '14px', outline: 'none' }}
              />
              <button
                onClick={handleSearch}
                disabled={searching || !searchQuery.trim()}
                style={{
                  padding: '12px 28px', borderRadius: '8px', border: 'none',
                  background: searching ? '#475569' : 'linear-gradient(135deg, #3b82f6, #2563eb)',
                  color: '#fff', fontWeight: '600', cursor: searching ? 'wait' : 'pointer',
                  fontSize: '14px', whiteSpace: 'nowrap'
                }}
              >
                {searching ? 'Searching...' : 'Search'}
              </button>
            </div>

            <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '12px', color: '#475569', alignSelf: 'center' }}>Try:</span>
              {[
                'need AI automation agency',
                'looking for web developer',
                'hire CTO fractional',
                'cybersecurity consultant NHS',
                'remote engineer lease'
              ].map(s => (
                <button key={s} onClick={() => setSearchQuery(s)} style={{ fontSize: '11px', color: '#93c5fd', background: '#1e3a5f', border: '1px solid #1e40af', padding: '4px 10px', borderRadius: '6px', cursor: 'pointer' }}>
                  {s}
                </button>
              ))}
            </div>

            {searchResults.length > 0 && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <h3 style={{ fontSize: '14px', fontWeight: '600' }}>Found {searchResults.length} leads</h3>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <button onClick={selectAll} style={{ fontSize: '12px', color: '#93c5fd', background: 'none', border: '1px solid #334155', padding: '4px 12px', borderRadius: '6px', cursor: 'pointer' }}>
                      {selectedLeads.length === searchResults.length ? 'Deselect All' : 'Select All'}
                    </button>
                    <span style={{ fontSize: '12px', color: '#64748b' }}>{selectedLeads.length} selected</span>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', alignItems: 'center' }}>
                  <select
                    value={saveToCampaign}
                    onChange={(e) => setSaveToCampaign(e.target.value)}
                    style={{ padding: '8px 12px', borderRadius: '8px', border: '1px solid #334155', background: '#111827', color: '#e2e8f0', fontSize: '13px', flex: 1 }}
                  >
                    <option value="">Select campaign to save leads...</option>
                    {campaigns.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                  <button
                    onClick={handleSaveLeads}
                    disabled={loading || !saveToCampaign || selectedLeads.length === 0}
                    style={{
                      padding: '8px 20px', borderRadius: '8px', border: 'none',
                      background: selectedLeads.length > 0 && saveToCampaign ? '#22c55e' : '#334155',
                      color: '#fff', fontWeight: '600', cursor: selectedLeads.length > 0 && saveToCampaign ? 'pointer' : 'not-allowed',
                      fontSize: '13px'
                    }}
                  >
                    Save {selectedLeads.length} Leads
                  </button>
                </div>

                {searchResults.map((r, i) => (
                  <div
                    key={i}
                    onClick={() => toggleLead(i)}
                    style={{
                      background: selectedLeads.includes(i) ? '#1e3a5f' : '#111827',
                      borderRadius: '10px', padding: '16px', marginBottom: '8px',
                      border: `1px solid ${selectedLeads.includes(i) ? '#3b82f6' : '#1f2937'}`,
                      cursor: 'pointer', transition: 'all 0.1s ease',
                      display: 'flex', gap: '12px', alignItems: 'flex-start'
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={selectedLeads.includes(i)}
                      onChange={() => toggleLead(i)}
                      style={{ marginTop: '2px', accentColor: '#3b82f6' }}
                    />
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                        <span style={{ fontWeight: '600', fontSize: '14px' }}>{r.name}</span>
                        <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '4px', background: r.score >= 70 ? '#065f46' : r.score >= 50 ? '#713f12' : '#450a0a', color: r.score >= 70 ? '#4ade80' : r.score >= 50 ? '#fbbf24' : '#fca5a5' }}>
                          Score: {r.score}
                        </span>
                      </div>
                      <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>{r.email}</div>
                      <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>{r.company} · {r.title}</div>
                      <div style={{ fontSize: '12px', color: '#94a3b8', fontStyle: 'italic' }}>"{r.snippet}"</div>
                      <a href={r.source_url} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()} style={{ fontSize: '11px', color: '#60a5fa', textDecoration: 'none' }}>
                        View on Reddit →
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {!searching && searchResults.length === 0 && searchQuery && (
              <div style={{ textAlign: 'center', padding: '48px', color: '#475569' }}>
                No results found. Try different keywords.
              </div>
            )}
          </div>
        )}

        {/* UPLOAD CSV */}
        {tab === 'upload' && (
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '4px' }}>Upload CSV</h2>
            <p style={{ color: '#64748b', fontSize: '13px', marginBottom: '24px' }}>Import leads from a spreadsheet file</p>

            <div style={{ background: '#111827', borderRadius: '12px', border: '2px dashed #334155', padding: '48px', textAlign: 'center' }}>
              <label style={{ cursor: 'pointer', display: 'block' }}>
                <div style={{ fontSize: '40px', marginBottom: '12px' }}>📄</div>
                <div style={{ fontSize: '15px', fontWeight: '600', marginBottom: '4px' }}>Click to choose CSV file</div>
                <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '16px' }}>Supports .csv files up to 10MB</div>
                <input type="file" accept=".csv" style={{ display: 'none' }} onChange={(e) => e.target.files[0] && handleUpload(e.target.files[0])} />
                <span style={{ display: 'inline-block', padding: '10px 28px', background: 'linear-gradient(135deg, #22c55e, #16a34a)', borderRadius: '8px', fontSize: '13px', fontWeight: '600' }}>
                  Choose File
                </span>
              </label>
            </div>

            <div style={{ marginTop: '24px', background: '#111827', borderRadius: '12px', padding: '24px', border: '1px solid #1f2937' }}>
              <h3 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>Required CSV Format</h3>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid #334155' }}>
                      {['email*', 'first_name', 'last_name', 'company', 'title', 'phone', 'website'].map(h => (
                        <th key={h} style={{ textAlign: 'left', padding: '8px 12px', color: '#3b82f6', fontWeight: '600' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    <tr style={{ borderBottom: '1px solid #1f2937' }}>
                      {['john@acme.com', 'John', 'Smith', 'Acme Ltd', 'CTO', '+447123456789', 'acme.com'].map((v, i) => (
                        <td key={i} style={{ padding: '8px 12px', color: '#94a3b8' }}>{v}</td>
                      ))}
                    </tr>
                    <tr style={{ borderBottom: '1px solid #1f2937' }}>
                      {['sarah@techco.com', 'Sarah', 'Jones', 'TechCo', 'Founder', '+447987654321', 'techco.com'].map((v, i) => (
                        <td key={i} style={{ padding: '8px 12px', color: '#94a3b8' }}>{v}</td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
              <p style={{ fontSize: '11px', color: '#475569', marginTop: '8px' }}>* = required field</p>
            </div>
          </div>
        )}

        {/* CAMPAIGNS */}
        {tab === 'campaigns' && (
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '4px' }}>Email Campaigns</h2>
            <p style={{ color: '#64748b', fontSize: '13px', marginBottom: '24px' }}>Launch campaigns to send emails to your leads</p>

            {campaigns.map(c => {
              const smtp = smtps.find(s => s.id === c.smtp_config_id);
              const campProspects = prospects.filter(p => p.campaign_id === c.id);
              const contacted = campProspects.filter(p => p.status === 'contacted').length;

              return (
                <div key={c.id} style={{ background: '#111827', borderRadius: '12px', padding: '20px', marginBottom: '12px', border: '1px solid #1f2937' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <h3 style={{ fontSize: '15px', fontWeight: '600', marginBottom: '4px' }}>{c.name}</h3>
                      <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: '#64748b' }}>
                        <span>From: {smtp?.from_email || 'info@ascentraconsulting.co.uk'}</span>
                        <span>Leads: {campProspects.length}</span>
                        <span>Sent: {contacted}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleLaunch(c.id)}
                      disabled={loading || campProspects.length === 0}
                      style={{
                        padding: '10px 24px', borderRadius: '8px', border: 'none',
                        background: campProspects.length > 0 ? 'linear-gradient(135deg, #3b82f6, #2563eb)' : '#334155',
                        color: '#fff', fontWeight: '600', cursor: campProspects.length > 0 ? 'pointer' : 'not-allowed',
                        fontSize: '13px'
                      }}
                    >
                      {contacted > 0 ? 'Launch Again' : 'Launch'}
                    </button>
                  </div>
                </div>
              );
            })}

            {campaigns.length === 0 && (
              <div style={{ textAlign: 'center', padding: '48px', color: '#475569', background: '#111827', borderRadius: '12px' }}>
                No campaigns found. Run setup first.
              </div>
            )}
          </div>
        )}

        {/* ALL LEADS */}
        {tab === 'leads' && (
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '4px' }}>All Leads ({prospects.length})</h2>
            <p style={{ color: '#64748b', fontSize: '13px', marginBottom: '24px' }}>View and manage all your imported leads</p>

            <div style={{ background: '#111827', borderRadius: '12px', overflow: 'hidden', border: '1px solid #1f2937' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ background: '#1f2937' }}>
                    <th style={{ textAlign: 'left', padding: '12px 16px', fontWeight: '600', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#64748b' }}>Name</th>
                    <th style={{ textAlign: 'left', padding: '12px 16px', fontWeight: '600', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#64748b' }}>Email</th>
                    <th style={{ textAlign: 'left', padding: '12px 16px', fontWeight: '600', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#64748b' }}>Company</th>
                    <th style={{ textAlign: 'left', padding: '12px 16px', fontWeight: '600', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#64748b' }}>Source</th>
                    <th style={{ textAlign: 'left', padding: '12px 16px', fontWeight: '600', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#64748b' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {prospects.map(p => (
                    <tr key={p.id} style={{ borderTop: '1px solid #1f2937' }}>
                      <td style={{ padding: '12px 16px', fontWeight: '500' }}>{p.first_name} {p.last_name}</td>
                      <td style={{ padding: '12px 16px', color: p.email.includes('placeholder') ? '#ef4444' : '#60a5fa' }}>
                        {p.email}
                        {p.email.includes('placeholder') && <span style={{ fontSize: '10px', color: '#ef4444', marginLeft: '4px' }}>⚠ no email</span>}
                      </td>
                      <td style={{ padding: '12px 16px', color: '#94a3b8' }}>{p.company || '-'}</td>
                      <td style={{ padding: '12px 16px', color: '#64748b' }}>{p.source || '-'}</td>
                      <td style={{ padding: '12px 16px' }}>
                        <span style={{ padding: '3px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: '500', background: p.status === 'contacted' ? '#065f46' : '#1f2937', color: p.status === 'contacted' ? '#4ade80' : '#94a3b8' }}>
                          {p.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {prospects.length === 0 && (
                    <tr>
                      <td colSpan="5" style={{ padding: '48px', textAlign: 'center', color: '#475569' }}>
                        No leads yet. Find leads or upload a CSV to get started.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px 32px', borderTop: '1px solid #1f2937', fontSize: '11px', color: '#475569', textAlign: 'center' }}>
        Ascentra Global Ltd · outreach.britsyncai.com
      </footer>
    </div>
  );
}
