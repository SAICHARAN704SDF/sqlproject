const sendBtn = document.getElementById('send-btn');
const inputEl = document.getElementById('user-input');
const chatBox = document.getElementById('chat-box');
const analysisEl = document.getElementById('analysis');
const resourceList = document.getElementById('resource-list');
const breathingSteps = document.getElementById('breathing-steps');
const breathVisual = document.getElementById('breath-visual');
const breathToggle = document.getElementById('breath-toggle');

// sidebar buttons
const sideButtons = document.querySelectorAll('.side-btn');

// profile
const profileOpen = document.getElementById('profile-open');

// Lottie
let lottiePlayer = null;
let breathStepIndex = 0;
let breathStepTimer = null;
let breathPlaying = false;

function startBreathingAnimation(){
  if(!breathVisual) return;
  breathVisual.classList.add('playing');
  breathPlaying = true;
  if(breathToggle) breathToggle.textContent = 'Pause';
  highlightBreathingSteps();
}

function stopBreathingAnimation(){
  if(!breathVisual) return;
  breathVisual.classList.remove('playing');
  breathPlaying = false;
  if(breathToggle) breathToggle.textContent = 'Play';
  if(breathStepTimer){
    clearTimeout(breathStepTimer);
    breathStepTimer = null;
  }
  resetBreathingStepHighlight();
}

function highlightBreathingSteps(){
  if(!breathingSteps) return;
  const steps = breathingSteps.querySelectorAll('li');
  if(!steps.length) return;
  steps.forEach((li, idx)=>{
    li.classList.toggle('active-step', idx === breathStepIndex % steps.length);
  });
  breathStepIndex = (breathStepIndex + 1) % steps.length;
  breathStepTimer = setTimeout(highlightBreathingSteps, 3000);
}

function resetBreathingStepHighlight(){
  if(!breathingSteps) return;
  breathStepIndex = 0;
  breathingSteps.querySelectorAll('li').forEach(li=>li.classList.remove('active-step'));
}

function appendMessage(text, who='bot'){
  const div = document.createElement('div');
  div.className = `message ${who}`;
  div.textContent = text;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage(){
  const msg = inputEl.value.trim();
  if(!msg) return;
  appendMessage(msg, 'user');
  inputEl.value = '';

  try{
    const res = await fetch('/get', {
      method:'POST',
      headers:{'Content-Type':'application/x-www-form-urlencoded'},
      body: new URLSearchParams({msg})
    });
    if(!res.ok) throw new Error('Server error');
    const data = await res.json();

    appendMessage(data.message, 'bot');

    // Update analysis panel
    analysisEl.innerHTML = `
      <div class="label">Emotion: ${data.label} </div>
      <div class="confidence">Confidence: ${Object.entries(data.confidence).map(([k,v])=>`${k}: ${Math.round(v*100)}%`).join(' · ')}</div>
      <div class="stresstype">Type: ${data.stress_type}</div>
      <div class="tips">
        <h4>Suggested tips</h4>
        <ul>${data.tips.map(t=>`<li>${t}</li>`).join('')}</ul>
      </div>
      <div class="action-plan">
        <h4>Action plan</h4>
        <ol>${data.action_plan.map(s=>`<li>${s}</li>`).join('')}</ol>
      </div>
      <div class="resources">
        <h4>Resources</h4>
        <ul>${data.resources.map(r=>`<li><a href="${r.url}" target="_blank" rel="noopener">${r.title}</a></li>`).join('')}</ul>
      </div>
    `;

  }catch(err){
    console.error(err);
    appendMessage('Sorry — something went wrong. Try again later.', 'bot');
  }
}

sendBtn.addEventListener('click', sendMessage);
inputEl.addEventListener('keydown', (e)=>{ if(e.key === 'Enter') sendMessage(); });

// Seed welcome messages
appendMessage('Hello — I’m EscapeStress. I’m here to listen and offer gentle guidance.', 'bot');
appendMessage('Try typing how you feel (e.g., "I feel anxious about exams").', 'bot');

// Sidebar behavior: toggle panels
sideButtons.forEach(b => b.addEventListener('click', (e)=>{
  sideButtons.forEach(x=>x.classList.remove('active'));
  b.classList.add('active');
  const panel = b.dataset.panel;
  document.querySelectorAll('.panel').forEach(p=>p.style.display = 'none');
  const el = document.getElementById(panel);
  if(el) el.style.display = 'block';
  // load breathing steps if needed
  if(panel === 'breathing') {
    loadBreathing();
  } else {
    stopBreathingAnimation();
  }
}));

// show Learn by default when user clicks Learn
// handled by same sideButtons logic; ensure panels exist

// Profile handler (simple prompt)
profileOpen.addEventListener('click', ()=>{
  const name = prompt('Your first name (optional)');
  const email = prompt('Your email (optional)');
  if(!name && !email) return;
  // Post to /user
  fetch('/user', {method:'POST', body: new URLSearchParams({name, email})})
    .then(r=>r.json()).then(j=>{
      appendMessage(`Thanks ${j.name || 'there'} — I’ll remember you here.`, 'bot');
    }).catch(()=>appendMessage('Saved locally.', 'bot'));
});

// Load resources from DB
function loadResources(){
  fetch('/resources_db').then(r=>r.json()).then(list=>{
    resourceList.innerHTML = list.map(r=>`<li><a href="${r.url}" target="_blank" rel="noopener">${r.title}</a> <small class="muted">(${r.category})</small></li>`).join('');
  }).catch(()=>{resourceList.innerHTML = '<li>Unable to load resources</li>'});
}

// Load recent journals
function loadRecentJournals(){
  fetch('/journal/recent').then(r=>r.json()).then(list=>{
    const panel = document.getElementById('journaling');
    const html = list.map(j=>`<div class="card" style="margin-bottom:8px"><small class="muted">${j.created_at}</small><div>${escapeHtml(j.entry)}</div></div>`).join('');
    const container = panel.querySelector('#journal-list');
    if(container) container.innerHTML = html;
    else panel.insertAdjacentHTML('beforeend', `<div id="journal-list">${html}</div>`)
  }).catch(()=>{});
}

function escapeHtml(s){ return String(s).replace(/[&<>"']/g, c=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c])); }

// Load breathing guide
function loadBreathing(){
  fetch('/breathing').then(r=>r.json()).then(data=>{
    breathingSteps.innerHTML = data.steps.map(s=>`<li>${s.text}</li>`).join('');
    resetBreathingStepHighlight();
    if(breathPlaying){
      if(breathStepTimer){
        clearTimeout(breathStepTimer);
        breathStepTimer = null;
      }
      highlightBreathingSteps();
    }
    // init lottie if available
    if(window.lottie && !lottiePlayer){
      try{
        lottiePlayer = lottie.loadAnimation({container: document.getElementById('lottieBreath'), renderer: 'svg', loop: true, autoplay:true, path: 'https://assets9.lottiefiles.com/packages/lf20_touohxv0.json'});
      }catch(e){console.warn('Lottie failed', e)}
    }
  }).catch(()=>{});
}

// initial load
loadResources();
// load knowledge / learn entries
function loadLearn(){
  fetch('/knowledge').then(r=>r.json()).then(list=>{
    const container = document.getElementById('learn-list');
    container.innerHTML = list.map(k=>`
      <div class="card" style="margin-bottom:8px">
        <h5>${k.title}</h5>
        <p class="muted">${k.category}</p>
        <p>${k.content.substring(0,200)}... <a href="#" data-id="${k.id}" class="learn-more">Read more</a></p>
      </div>
    `).join('');
    // attach listeners
    document.querySelectorAll('.learn-more').forEach(a=>a.addEventListener('click', (e)=>{
      e.preventDefault();
      const id = a.dataset.id;
      const item = list.find(x=>String(x.id)===String(id));
      if(item){
        // insert modal-like detail below
        const modalHtml = `<div class="card glass"><h4>${item.title}</h4><p><strong>How it comes:</strong> ${item.how_it_comes}</p><p><strong>How it goes:</strong> ${item.how_it_goes}</p><p>${item.content}</p></div>`;
        const container = document.getElementById('learn-list');
        container.insertAdjacentHTML('afterbegin', modalHtml);
        // log action
        fetch('/log_action', {method:'POST', body: new URLSearchParams({action_type:'view_learn', details: item.title})});
      }
    }))
  }).catch(()=>{})
}
loadLearn();
// load journals when journaling panel is visible
document.querySelectorAll('.side-btn').forEach(b=>{
  b.addEventListener('click', ()=>{
    if(b.dataset.panel === 'journaling') setTimeout(loadRecentJournals, 150);
  });
});

// Hook journaling save
const saveJournalBtn = document.getElementById('save-journal');
if(saveJournalBtn){
  saveJournalBtn.addEventListener('click', ()=>{
    const text = document.getElementById('journal-text').value.trim();
    if(!text) return alert('Write something first');
    fetch('/journal', {method:'POST', body: new URLSearchParams({entry: text})})
      .then(r=>r.json()).then(j=>{
        document.getElementById('journal-text').value = '';
        document.getElementById('journal-saved').textContent = 'Saved';
        loadRecentJournals();
      }).catch(()=>alert('Save failed'));
  });
}

if(breathToggle){
  breathToggle.addEventListener('click', ()=>{
    if(breathPlaying){
      stopBreathingAnimation();
    } else {
      startBreathingAnimation();
    }
  });
}
