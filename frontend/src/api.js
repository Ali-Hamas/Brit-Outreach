const BASE_URL = '/api/v1';

export async function fetchBusinesses() {
  const res = await fetch(`${BASE_URL}/businesses`);
  if (!res.ok) return [];
  return res.json();
}

export async function createBusiness(name, domain) {
  const res = await fetch(`${BASE_URL}/businesses`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, domain })
  });
  return res.json();
}

export async function fetchSMTPConfigs(businessId) {
  const res = await fetch(`${BASE_URL}/smtp/business/${businessId}`);
  if (!res.ok) return [];
  return res.json();
}

export async function fetchAllSMTPConfigs() {
  const res = await fetch(`${BASE_URL}/smtp/all`);
  if (!res.ok) return [];
  return res.json();
}

export async function createSMTPConfig(data) {
  const res = await fetch(`${BASE_URL}/smtp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function fetchTargetMarkets(businessId) {
  const res = await fetch(`${BASE_URL}/target-markets/business/${businessId}`);
  if (!res.ok) return [];
  return res.json();
}

export async function createTargetMarket(data) {
  const res = await fetch(`${BASE_URL}/target-markets`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function fetchCampaigns(businessId) {
  const res = await fetch(`${BASE_URL}/campaigns/business/${businessId}`);
  if (!res.ok) return [];
  return res.json();
}

export async function createCampaign(data) {
  const res = await fetch(`${BASE_URL}/campaigns`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function updateCampaign(campaignId, data) {
  const res = await fetch(`${BASE_URL}/campaigns/${campaignId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error('Failed to update campaign');
  return res.json();
}

export async function deleteCampaign(campaignId) {
  const res = await fetch(`${BASE_URL}/campaigns/${campaignId}`, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error('Failed to delete campaign');
  return res.json();
}

export async function launchCampaign(campaignId) {
  const res = await fetch(`${BASE_URL}/campaigns/${campaignId}/launch`, {
    method: 'POST'
  });
  return res.json();
}

export async function fetchProspects(businessId, status = null) {
  let url = `${BASE_URL}/prospects/business/${businessId}`;
  if (status) url += `?status=${status}`;
  const res = await fetch(url);
  if (!res.ok) return [];
  return res.json();
}

export async function createProspect(data) {
  const res = await fetch(`${BASE_URL}/prospects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed creating prospect');
  }
  return res.json();
}

export async function chatWithInfluencerAgent(userQuery, chatHistory = [], groqApiKey = null) {
  const res = await fetch(`${BASE_URL}/influencers/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_query: userQuery, chat_history: chatHistory, groq_api_key: groqApiKey })
  });
  return res.json();
}

export async function addInfluencerToCampaign(data) {
  const res = await fetch(`${BASE_URL}/influencers/add-to-campaign`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function uploadProspectsCSV(businessId, file, campaignId = null) {
  const formData = new FormData();
  formData.append('business_id', businessId);
  if (campaignId) formData.append('campaign_id', campaignId);
  formData.append('file', file);

  const res = await fetch(`${BASE_URL}/prospects/upload-csv`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed uploading CSV');
  }
  return res.json();
}

// --- Social Listening ---

export async function searchReddit(keywords, subreddits, limit = 25) {
  const res = await fetch(`${BASE_URL}/social-listening/reddit/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ keywords, subreddits, limit })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Reddit search failed');
  }
  return res.json();
}

export async function searchGoogleCSE(query, siteFilter, limit = 10) {
  const res = await fetch(`${BASE_URL}/social-listening/google/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, site_filter: siteFilter, limit })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Google search failed');
  }
  return res.json();
}

export async function draftAIReply(title, content, author, platform, subreddit) {
  const res = await fetch(`${BASE_URL}/social-listening/draft-reply`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, content, author, platform, subreddit })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'AI draft failed');
  }
  return res.json();
}

export async function fetchRedditDefaults() {
  const res = await fetch(`${BASE_URL}/social-listening/reddit/defaults`);
  if (!res.ok) return { default_subreddits: [], default_keywords: [] };
  return res.json();
}

// --- Voice Calling & Cadence ---

export async function fetchCadenceStatus(hours = 48.0, businessId = 'biz-ascentra') {
  const res = await fetch(`${BASE_URL}/voice/cadence/status?cadence_hours=${hours}&business_id=${businessId}`);
  if (!res.ok) throw new Error('Failed to fetch cadence status');
  return res.json();
}

export async function triggerCadenceCalling(hours = 48.0, dryRun = false, businessId = 'biz-ascentra') {
  const res = await fetch(`${BASE_URL}/voice/cadence/trigger`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ cadence_hours: hours, dry_run: dryRun, business_id: businessId })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to trigger voice cadence');
  }
  return res.json();
}

export async function triggerDirectColdCalling(prospectIds, campaignId, businessId = 'biz-ascentra') {
  const res = await fetch(`${BASE_URL}/voice/direct-call`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prospect_ids: prospectIds, campaign_id: campaignId, business_id: businessId })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to trigger direct cold calling');
  }
  return res.json();
}

export async function fetchVoiceJobs(limit = 50) {
  const res = await fetch(`${BASE_URL}/voice/jobs?limit=${limit}`);
  if (!res.ok) return { total: 0, jobs: [] };
  return res.json();
}

export async function syncVoiceOutcomes() {
  const res = await fetch(`${BASE_URL}/voice/sync-outcomes`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed syncing voice outcomes');
  return res.json();
}

