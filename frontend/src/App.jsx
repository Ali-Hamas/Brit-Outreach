import React, { useState, useEffect } from 'react';
import {
  fetchBusinesses, fetchCampaigns, launchCampaign, fetchProspects,
  uploadProspectsCSV, fetchAllSMTPConfigs, searchGoogleCSE
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
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);

  useEffect(() => { init(); }, []);

  async function init() {
    const list = await fetchBusinesses();
    setBusinesses(list);
    if (list.length > 0) {
      setSelectedBiz(list[0]);
      await load(list[0].id);
    }
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

  async function handleUpload(file) {
    if (!selectedBiz || !file) return;
    setLoading(true);
    try {
      const res = await uploadProspectsCSV(selectedBiz.id, file);
      setMsg(`Imported ${res.imported_count} leads!`);
      await load(selectedBiz.id);
    } catch (e) { setMsg('Error: ' + e.message); }
    setLoading(false);
  }

  async function handleLaunch(campId) {
    setLoading(true);
    try {
      const res = await launchCampaign(campId);
      setMsg(`Sent ${res.emails_sent} emails!`);
      await load(selectedBiz.id);
    } catch (e) { setMsg('Error: ' + e.message); }
    setLoading(false);
  }

  async function handleSearch() {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const res = await searchGoogleCSE(searchQuery, null, 10);
      setSearchResults(res.results || []);
    } catch (e) { setMsg('Search error: ' + e.message); }
    setSearching(false);
  }

  return (
    <div style={{ minHeight: '100vh', background: '#0f172a', color: '#fff', fontFamily: 'system-ui, sans-serif' }}>

      {/* Header */}
      <div style={{ background: '#1e293b', padding: '16px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #334155' }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: 'bold', margin: 0 }}>Ascentra Global</h1>
          <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0 }}>Outreach System</p>
        </div>
        <div style={{ display: 'flex', gap: '16px', fontSize: '13px', color: '#94a3b8' }}>
          <span>{prospects.length} leads</span>
          <span>{campaigns.length} campaigns</span>
          {smtps.length > 0 && <span style={{ color: '#4ade80' }}>SMTP Ready</span>}
        </div>
      </div>

      {/* Navigation */}
      <div style={{ background: '#1e293b', padding: '12px 24px', display: 'flex', gap: '8px', borderBottom: '1px solid #334155' }}>
        {[
          { id: 'home', label: 'Home' },
          { id: 'search', label: 'Find Leads' },
          { id: 'upload', label: 'Upload CSV' },
          { id: 'campaigns', label: 'Campaigns' },
          { id: 'leads', label: 'All Leads' },
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              border: 'none',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: '600',
              background: tab === t.id ? '#3b82f6' : 'transparent',
              color: tab === t.id ? '#fff' : '#94a3b8',
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Message */}
      {msg && (
        <div style={{ margin: '16px 24px', padding: '12px', background: '#065f46', borderRadius: '8px', fontSize: '13px', display: 'flex', justifyContent: 'space-between' }}>
          {msg}
          <button onClick={() => setMsg('')} style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer' }}>X</button>
        </div>
      )}

      {/* Loading */}
      {loading && <div style={{ padding: '16px 24px', color: '#60a5fa', fontSize: '13px' }}>Loading...</div>}

      {/* HOME TAB */}
      {tab === 'home' && (
        <div style={{ maxWidth: '800px', margin: '40px auto', padding: '0 24px', textAlign: 'center' }}>
          <h2 style={{ fontSize: '28px', fontWeight: 'bold', marginBottom: '8px' }}>Welcome to Ascentra Global</h2>
          <p style={{ color: '#94a3b8', fontSize: '16px', marginBottom: '40px' }}>Find leads and send outreach emails in 3 simple steps</p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '24px' }}>
            <div onClick={() => setTab('search')} style={{ background: '#1e293b', borderRadius: '12px', padding: '32px 24px', cursor: 'pointer', border: '1px solid #334155' }}>
              <div style={{ fontSize: '32px', marginBottom: '12px' }}>1</div>
              <h3 style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '8px' }}>Find Leads</h3>
              <p style={{ fontSize: '13px', color: '#94a3b8' }}>Search for companies by keyword</p>
            </div>
            <div onClick={() => setTab('upload')} style={{ background: '#1e293b', borderRadius: '12px', padding: '32px 24px', cursor: 'pointer', border: '1px solid #334155' }}>
              <div style={{ fontSize: '32px', marginBottom: '12px' }}>2</div>
              <h3 style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '8px' }}>Upload CSV</h3>
              <p style={{ fontSize: '13px', color: '#94a3b8' }}>Or upload your own lead list</p>
            </div>
            <div onClick={() => setTab('campaigns')} style={{ background: '#1e293b', borderRadius: '12px', padding: '32px 24px', cursor: 'pointer', border: '1px solid #334155' }}>
              <div style={{ fontSize: '32px', marginBottom: '12px' }}>3</div>
              <h3 style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '8px' }}>Launch</h3>
              <p style={{ fontSize: '13px', color: '#94a3b8' }}>Send emails to your leads</p>
            </div>
          </div>
        </div>
      )}

      {/* FIND LEADS TAB */}
      {tab === 'search' && (
        <div style={{ maxWidth: '800px', margin: '40px auto', padding: '0 24px' }}>
          <h2 style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '8px' }}>Find Leads</h2>
          <p style={{ color: '#94a3b8', fontSize: '13px', marginBottom: '16px' }}>Type what you're looking for and click Search</p>

          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="e.g. UK AI startups with email addresses"
              style={{ flex: 1, padding: '12px 16px', borderRadius: '8px', border: '1px solid #334155', background: '#0f172a', color: '#fff', fontSize: '14px' }}
            />
            <button
              onClick={handleSearch}
              disabled={searching}
              style={{ padding: '12px 24px', borderRadius: '8px', border: 'none', background: '#3b82f6', color: '#fff', fontWeight: 'bold', cursor: 'pointer', fontSize: '14px' }}
            >
              {searching ? 'Searching...' : 'Search'}
            </button>
          </div>

          <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '12px', color: '#64748b' }}>Try:</span>
            {['UK tech startups CTO email', 'NHS digital transformation manager', 'e-commerce store owners UK'].map(s => (
              <button key={s} onClick={() => { setSearchQuery(s); }} style={{ fontSize: '12px', color: '#60a5fa', background: '#1e3a5f', border: 'none', padding: '4px 8px', borderRadius: '4px', cursor: 'pointer' }}>
                {s}
              </button>
            ))}
          </div>

          {searchResults.length > 0 && (
            <div>
              <h3 style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '12px' }}>Results ({searchResults.length})</h3>
              {searchResults.map((r, i) => (
                <div key={i} style={{ background: '#1e293b', borderRadius: '8px', padding: '16px', marginBottom: '8px', border: '1px solid #334155' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '4px' }}>{r.title}</h4>
                  <p style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>{r.snippet}</p>
                  <a href={r.link} target="_blank" rel="noreferrer" style={{ fontSize: '12px', color: '#60a5fa' }}>{r.link}</a>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* UPLOAD TAB */}
      {tab === 'upload' && (
        <div style={{ maxWidth: '800px', margin: '40px auto', padding: '0 24px' }}>
          <h2 style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '8px' }}>Upload CSV</h2>
          <p style={{ color: '#94a3b8', fontSize: '13px', marginBottom: '24px' }}>Upload a CSV file with your leads</p>

          <div style={{ background: '#1e293b', borderRadius: '12px', padding: '32px', border: '2px dashed #334155', textAlign: 'center' }}>
            <label style={{ cursor: 'pointer' }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>📁</div>
              <div style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '8px' }}>Click to choose CSV file</div>
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '16px' }}>or drag and drop</div>
              <input
                type="file"
                accept=".csv"
                className="hidden"
                style={{ display: 'none' }}
                onChange={(e) => e.target.files[0] && handleUpload(e.target.files[0])}
              />
              <span style={{ display: 'inline-block', padding: '10px 24px', background: '#22c55e', borderRadius: '8px', fontSize: '14px', fontWeight: 'bold', color: '#fff' }}>
                Choose File
              </span>
            </label>
          </div>

          <div style={{ marginTop: '24px', background: '#1e293b', borderRadius: '12px', padding: '24px', border: '1px solid #334155' }}>
            <h3 style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '12px' }}>CSV Format</h3>
            <p style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '12px' }}>Your CSV must have these columns:</p>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #334155' }}>
                  <th style={{ textAlign: 'left', padding: '8px', color: '#60a5fa' }}>email</th>
                  <th style={{ textAlign: 'left', padding: '8px', color: '#60a5fa' }}>first_name</th>
                  <th style={{ textAlign: 'left', padding: '8px', color: '#60a5fa' }}>last_name</th>
                  <th style={{ textAlign: 'left', padding: '8px', color: '#60a5fa' }}>company</th>
                  <th style={{ textAlign: 'left', padding: '8px', color: '#60a5fa' }}>title</th>
                </tr>
              </thead>
              <tbody>
                <tr style={{ borderBottom: '1px solid #334155' }}>
                  <td style={{ padding: '8px', color: '#94a3b8' }}>john@acme.com</td>
                  <td style={{ padding: '8px', color: '#94a3b8' }}>John</td>
                  <td style={{ padding: '8px', color: '#94a3b8' }}>Smith</td>
                  <td style={{ padding: '8px', color: '#94a3b8' }}>Acme Ltd</td>
                  <td style={{ padding: '8px', color: '#94a3b8' }}>CTO</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* CAMPAIGNS TAB */}
      {tab === 'campaigns' && (
        <div style={{ maxWidth: '800px', margin: '40px auto', padding: '0 24px' }}>
          <h2 style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '8px' }}>Campaigns</h2>
          <p style={{ color: '#94a3b8', fontSize: '13px', marginBottom: '24px' }}>Click Launch to send emails to all leads</p>

          {campaigns.map(c => {
            const smtp = smtps.find(s => s.id === c.smtp_config_id);
            const sent = prospects.filter(p => p.campaign_id === c.id && p.status === 'contacted').length;

            return (
              <div key={c.id} style={{ background: '#1e293b', borderRadius: '12px', padding: '20px', marginBottom: '12px', border: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '4px' }}>{c.name}</h3>
                  <p style={{ fontSize: '12px', color: '#94a3b8' }}>From: {smtp?.from_email || 'info@ascentraconsulting.co.uk'}</p>
                  <p style={{ fontSize: '12px', color: '#94a3b8' }}>Sent: {sent} emails</p>
                </div>
                <button
                  onClick={() => handleLaunch(c.id)}
                  disabled={loading || prospects.length === 0}
                  style={{ padding: '10px 24px', borderRadius: '8px', border: 'none', background: '#3b82f6', color: '#fff', fontWeight: 'bold', cursor: 'pointer', fontSize: '14px', opacity: prospects.length === 0 ? 0.5 : 1 }}
                >
                  Launch
                </button>
              </div>
            );
          })}

          {campaigns.length === 0 && (
            <div style={{ textAlign: 'center', padding: '48px', color: '#64748b' }}>
              No campaigns found. Run setup first.
            </div>
          )}

          {prospects.length === 0 && campaigns.length > 0 && (
            <div style={{ textAlign: 'center', padding: '24px', color: '#f59e0b', fontSize: '13px', background: '#1e293b', borderRadius: '12px', marginTop: '16px' }}>
              Upload leads first before launching campaigns
            </div>
          )}
        </div>
      )}

      {/* ALL LEADS TAB */}
      {tab === 'leads' && (
        <div style={{ maxWidth: '1000px', margin: '40px auto', padding: '0 24px' }}>
          <h2 style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '24px' }}>All Leads ({prospects.length})</h2>

          <div style={{ background: '#1e293b', borderRadius: '12px', overflow: 'hidden', border: '1px solid #334155' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ background: '#334155' }}>
                  <th style={{ textAlign: 'left', padding: '12px 16px' }}>Name</th>
                  <th style={{ textAlign: 'left', padding: '12px 16px' }}>Email</th>
                  <th style={{ textAlign: 'left', padding: '12px 16px' }}>Company</th>
                  <th style={{ textAlign: 'left', padding: '12px 16px' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {prospects.map(p => (
                  <tr key={p.id} style={{ borderTop: '1px solid #334155' }}>
                    <td style={{ padding: '12px 16px' }}>{p.first_name} {p.last_name}</td>
                    <td style={{ padding: '12px 16px', color: '#60a5fa' }}>{p.email}</td>
                    <td style={{ padding: '12px 16px', color: '#94a3b8' }}>{p.company || '-'}</td>
                    <td style={{ padding: '12px 16px' }}>
                      <span style={{ padding: '4px 8px', borderRadius: '4px', fontSize: '11px', background: p.status === 'contacted' ? '#065f46' : '#1e293b', color: p.status === 'contacted' ? '#4ade80' : '#94a3b8' }}>
                        {p.status}
                      </span>
                    </td>
                  </tr>
                ))}
                {prospects.length === 0 && (
                  <tr>
                    <td colSpan="4" style={{ padding: '48px', textAlign: 'center', color: '#64748b' }}>
                      No leads yet. Find leads or upload a CSV first.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
