import { BrowserRouter, Routes, Route, useNavigate, useSearchParams } from 'react-router-dom';
import { useEffect, useState, useRef } from 'react';

const InputLabel = ({ children }) => <label style={{ display: 'block', color: '#8b949e', fontSize: '0.8rem', marginBottom: '5px', fontWeight: 'bold' }}>{children}</label>;
const Section = ({ title, children }) => <div style={{ backgroundColor: '#161b22', border: '1px solid #30363d', borderRadius: '6px', padding: '15px', marginBottom: '15px' }}><h3 style={{ margin: '0 0 15px 0', fontSize: '0.9rem', color: '#c9d1d9' }}>{title}</h3><div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>{children}</div></div>;
const NavItem = ({ id, label, activeTab, setActiveTab }) => <li onClick={() => setActiveTab(id)} style={{ color: activeTab === id ? 'white' : '#8b949e', borderLeft: activeTab === id ? '2px solid #B75CFF' : 'none', paddingLeft: '15px', cursor: 'pointer', marginBottom: '10px' }}>{label}</li>;

function LoginHandler() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  useEffect(() => {
    const token = searchParams.get('token');
    if (token) { localStorage.setItem('auth_token', token); navigate('/dashboard'); } 
    else { navigate('/'); }
  }, [searchParams, navigate]);
  return <div style={{ backgroundColor: '#0D1117', height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><p style={{ color: '#B75CFF', fontFamily: 'monospace' }}>СИНХРОНИЗАЦИЯ...</p></div>;
}

function Home() {
  return (
    <div style={{ backgroundColor: '#0D1117', height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
      <h1 style={{ color: '#B75CFF', fontFamily: 'monospace', fontSize: '3rem', margin: '0 0 10px 0', letterSpacing: '2px' }}>404: CONTROL TOWER</h1>
      <a href="http://127.0.0.1:8000/login" style={{ padding: '14px 28px', backgroundColor: '#5865F2', color: 'white', textDecoration: 'none', borderRadius: '4px', fontFamily: 'monospace', fontWeight: 'bold' }}>IDENTIFY VIA DISCORD</a>
    </div>
  );
}

function Dashboard() {
  const token = localStorage.getItem('auth_token');
  const navigate = useNavigate();
  
  const [activeTab, setActiveTab] = useState('OVERVIEW');
  const [stats, setStats] = useState(null);
  const [configs, setConfigs] = useState([]);
  const [logs, setLogs] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [bots, setBots] = useState([]);
  
  // Состояния для Live Log Streamer
  const [activeLogBot, setActiveLogBot] = useState(null);
  const [liveLogs, setLiveLogs] = useState('');
  const logTerminalRef = useRef(null);

  const [embed, setEmbed] = useState({ channel_id: '', content: '', author_name: '', author_icon: '', author_url: '', title: '', url: '', description: '', color: '#5865F2', fields: [], image_url: '', thumbnail_url: '', footer_text: '', footer_icon: '', timestamp: false });
  const [embedStatus, setEmbedStatus] = useState('');

  // Полинг статусов ботов
  useEffect(() => {
    if (!token || activeTab !== 'OVERVIEW') return;
    const fetchBots = () => fetch('http://127.0.0.1:8000/api/infrastructure/bots', { headers: { 'Authorization': `Bearer ${token}` }}).then(res => res.json()).then(data => setBots(data));
    fetchBots();
    const interval = setInterval(fetchBots, 3000);
    return () => clearInterval(interval);
  }, [activeTab, token]);

  // Полинг логов (если открыта панель логов)
  useEffect(() => {
    if (!activeLogBot || activeTab !== 'OVERVIEW') return;
    const fetchLogs = () => {
      fetch(`http://127.0.0.1:8000/api/infrastructure/bots/${activeLogBot}/logs`, { headers: { 'Authorization': `Bearer ${token}` }})
        .then(res => res.json()).then(data => {
          setLiveLogs(data.logs);
          // Автоскролл вниз при новых логах
          if (logTerminalRef.current) logTerminalRef.current.scrollTop = logTerminalRef.current.scrollHeight;
        });
    };
    fetchLogs();
    const interval = setInterval(fetchLogs, 1500); // Обновляем логи каждые 1.5 сек
    return () => clearInterval(interval);
  }, [activeLogBot, activeTab, token]);

  useEffect(() => {
    if (!token) return;
    if (activeTab === 'OVERVIEW') fetch('http://127.0.0.1:8000/api/dashboard/stats', { headers: { 'Authorization': `Bearer ${token}` }}).then(res => res.json()).then(data => setStats(data)).catch(() => navigate('/'));
    else if (activeTab === 'SETTINGS') fetch('http://127.0.0.1:8000/api/config', { headers: { 'Authorization': `Bearer ${token}` }}).then(res => res.json()).then(data => setConfigs(data));
    else if (activeTab === 'AUDIT_TRAIL') fetch('http://127.0.0.1:8000/api/audit', { headers: { 'Authorization': `Bearer ${token}` }}).then(res => res.json()).then(data => setLogs(data));
    else if (activeTab === 'MODERATION') fetch('http://127.0.0.1:8000/api/moderation/tickets', { headers: { 'Authorization': `Bearer ${token}` }}).then(res => res.json()).then(data => setTickets(data));
  }, [activeTab, token, navigate]);

  const handleConfigSave = (key, newValue) => fetch('http://127.0.0.1:8000/api/config', { method: 'POST', headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ key, value: newValue }) });
  const handleTicketResolve = (ticketId, action) => fetch(`http://127.0.0.1:8000/api/moderation/tickets/${ticketId}/resolve`, { method: 'POST', headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ action }) }).then(res => { if (res.ok) setTickets(tickets.filter(t => t.id !== ticketId)); });
  const handleBotAction = (botId, action) => fetch(`http://127.0.0.1:8000/api/infrastructure/bots/${botId}/action`, { method: 'POST', headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ action }) });

  const handleSendEmbed = () => {
    if (!embed.channel_id) return setEmbedStatus('ОШИБКА: УКАЖИТЕ CHANNEL ID');
    const urlRegex = /^(https?:\/\/)/i;
    const urlFields = [{ name: 'URL', value: embed.url }, { name: 'AUTHOR URL', value: embed.author_url }, { name: 'AUTHOR ICON', value: embed.author_icon }, { name: 'IMAGE URL', value: embed.image_url }, { name: 'THUMBNAIL URL', value: embed.thumbnail_url }, { name: 'FOOTER ICON', value: embed.footer_icon }];
    for (const field of urlFields) if (field.value && !urlRegex.test(field.value.trim())) return setEmbedStatus(`ОШИБКА: НЕВЕРНЫЙ ${field.name} (нужен http:// или https://)`);
    setEmbedStatus('ОТПРАВКА...');
    fetch('http://127.0.0.1:8000/api/announcer/send', { method: 'POST', headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify(embed) }).then(async res => {
      if (!res.ok) { const errData = await res.json(); throw new Error(errData.detail || 'Неизвестная ошибка сервера'); }
      setEmbedStatus('УСПЕШНО ОТПРАВЛЕНО'); setTimeout(() => setEmbedStatus(''), 3000);
    }).catch(e => setEmbedStatus('ОШИБКА: ' + e.message));
  };

  const addField = () => setEmbed({...embed, fields: [...embed.fields, {name: 'New Field', value: 'Value', inline: false}]});
  const updateField = (i, key, val) => { const f = [...embed.fields]; f[i][key] = val; setEmbed({...embed, fields: f}); };
  const removeField = (i) => setEmbed({...embed, fields: embed.fields.filter((_, idx) => idx !== i)});

  if (!token) return <div style={{ backgroundColor: '#0D1117', height: '100vh' }}></div>;

  return (
    <div style={{ backgroundColor: '#0D1117', minHeight: '100vh', color: 'white', fontFamily: 'monospace', display: 'flex' }}>
      <div style={{ width: '260px', borderRight: '1px solid #30363d', padding: '30px 20px', display: 'flex', flexDirection: 'column' }}>
        <h2 style={{ color: '#B75CFF', margin: '0 0 40px 0', fontSize: '1.2rem' }}>[404_ADMIN_v1]</h2>
        <nav style={{ flex: 1 }}>
          <ul style={{ listStyle: 'none', padding: 0, lineHeight: '2.8' }}>
            <NavItem id="OVERVIEW" label="OVERVIEW" activeTab={activeTab} setActiveTab={setActiveTab} />
            <NavItem id="MODERATION" label="MODERATION" activeTab={activeTab} setActiveTab={setActiveTab} />
            <NavItem id="ANNOUNCER" label="ANNOUNCER" activeTab={activeTab} setActiveTab={setActiveTab} />
            <NavItem id="SETTINGS" label="GLOBAL_SETTINGS" activeTab={activeTab} setActiveTab={setActiveTab} />
            <NavItem id="AUDIT_TRAIL" label="AUDIT_TRAIL" activeTab={activeTab} setActiveTab={setActiveTab} />
          </ul>
        </nav>
        <button onClick={() => { localStorage.removeItem('auth_token'); navigate('/'); }} style={{ padding: '10px', backgroundColor: 'transparent', color: '#da3633', border: '1px solid #da3633', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>TERMINATE_SESSION</button>
      </div>

      <div style={{ flex: 1, padding: '50px', overflowY: 'auto' }}>
        {activeTab === 'OVERVIEW' && (
          <>
            <header style={{ marginBottom: '50px' }}><h1 style={{ margin: 0 }}>WELCOME, <span style={{color: '#B75CFF'}}>{stats?.admin_name}</span></h1></header>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '25px', marginBottom: '50px' }}>
              <div style={{ padding: '25px', backgroundColor: '#161b22', border: '1px solid #30363d', borderRadius: '8px' }}><h3 style={{ margin: '0 0 15px 0', color: '#8b949e' }}>АКТИВНЫЕ КОМНАТЫ</h3><p style={{ fontSize: '2.5rem', margin: 0, color: '#B75CFF' }}>{stats?.active_rooms}</p></div>
              <div style={{ padding: '25px', backgroundColor: '#161b22', border: '1px solid #30363d', borderRadius: '8px' }}><h3 style={{ margin: '0 0 15px 0', color: '#8b949e' }}>ОЖИДАЮТ ПРОВЕРКИ</h3><p style={{ fontSize: '2.5rem', margin: 0, color: '#d29922' }}>{stats?.pending_feedbacks}</p></div>
            </div>
            
            <h2 style={{ color: '#8b949e', fontSize: '1.2rem', marginBottom: '20px', borderBottom: '1px solid #30363d', paddingBottom: '10px' }}>// PROCESS MANAGER & LOGS</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              {bots.map(bot => (
                <div key={bot.id} style={{ backgroundColor: '#161b22', border: '1px solid #30363d', borderRadius: '8px', overflow: 'hidden' }}>
                  
                  {/* Заголовок карточки бота */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                      <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: bot.status === 'ONLINE' ? '#57ab5a' : '#da3633', boxShadow: `0 0 8px ${bot.status === 'ONLINE' ? '#57ab5a' : '#da3633'}` }}></div>
                      <div><div style={{ fontWeight: 'bold', fontSize: '1.1rem' }}>{bot.name}</div><div style={{ color: '#8b949e', fontSize: '0.85rem', marginTop: '5px' }}>RAM Usage: <span style={{ color: 'white' }}>{bot.ram}</span></div></div>
                    </div>
                    <div style={{ display: 'flex', gap: '10px' }}>
                      <button onClick={() => setActiveLogBot(activeLogBot === bot.id ? null : bot.id)} style={{ padding: '8px 16px', backgroundColor: activeLogBot === bot.id ? '#30363d' : 'transparent', color: 'white', border: '1px solid #30363d', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>{activeLogBot === bot.id ? 'HIDE LOGS' : 'VIEW LOGS'}</button>
                      {bot.status === 'OFFLINE' ? <button onClick={() => handleBotAction(bot.id, 'start')} style={{ padding: '8px 16px', backgroundColor: '#238636', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>START</button> : <><button onClick={() => handleBotAction(bot.id, 'restart')} style={{ padding: '8px 16px', backgroundColor: '#1f6feb', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>RESTART</button><button onClick={() => handleBotAction(bot.id, 'stop')} style={{ padding: '8px 16px', backgroundColor: 'transparent', color: '#da3633', border: '1px solid #da3633', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>STOP</button></>}
                    </div>
                  </div>

                  {/* Терминал Логов */}
                  {activeLogBot === bot.id && (
                    <div style={{ backgroundColor: '#000000', borderTop: '1px solid #30363d', padding: '15px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                        <span style={{ color: '#8b949e', fontSize: '0.8rem' }}>// LIVE CONSOLE OUTPUT ({bot.name})</span>
                        <span style={{ color: '#57ab5a', fontSize: '0.8rem', animation: 'blink 2s infinite' }}>● STREAMING</span>
                      </div>
                      <pre ref={logTerminalRef} style={{ margin: 0, color: '#c9d1d9', fontSize: '0.85rem', whiteSpace: 'pre-wrap', maxHeight: '300px', overflowY: 'auto', fontFamily: 'Consolas, monospace' }}>
                        {liveLogs || "Ожидание данных..."}
                      </pre>
                    </div>
                  )}

                </div>
              ))}
            </div>
          </>
        )}

        {/* ... (Вкладки ANNOUNCER, SETTINGS, MODERATION, AUDIT_TRAIL остаются без изменений) ... */}
        {activeTab === 'ANNOUNCER' && ( <div><div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}><h1 style={{ color: '#B75CFF', margin: 0 }}>// ADVANCED ANNOUNCER</h1><div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}><input type="text" placeholder="Channel ID..." value={embed.channel_id} onChange={(e) => setEmbed({...embed, channel_id: e.target.value})} style={{ padding: '10px', background: '#161b22', border: '1px solid #30363d', color: 'white', borderRadius: '4px', fontFamily: 'monospace' }} /><button onClick={handleSendEmbed} style={{ padding: '10px 20px', backgroundColor: '#5865F2', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>ОТПРАВИТЬ</button><span style={{ color: embedStatus.includes('ОШИБКА') ? '#da3633' : '#57ab5a' }}>{embedStatus}</span></div></div><div style={{ display: 'flex', gap: '30px', alignItems: 'flex-start' }}><div style={{ flex: '1', display: 'flex', flexDirection: 'column', height: '75vh', overflowY: 'auto', paddingRight: '10px' }}><Section title="MESSAGE CONTENT"><textarea value={embed.content} onChange={e => setEmbed({...embed, content: e.target.value})} placeholder="Текст вне эмбеда (пинги @here и т.д.)" style={{ width: '100%', padding: '10px', background: '#0D1117', color: 'white', border: '1px solid #30363d', minHeight: '60px' }} /></Section><Section title="AUTHOR"><div style={{ display: 'flex', gap: '10px' }}><div style={{ flex: 1 }}><InputLabel>NAME</InputLabel><input value={embed.author_name} onChange={e => setEmbed({...embed, author_name: e.target.value})} style={{ width: '100%', padding: '8px', background: '#0D1117', color: 'white', border: '1px solid #30363d' }} /></div><div style={{ flex: 1 }}><InputLabel>ICON URL</InputLabel><input value={embed.author_icon} onChange={e => setEmbed({...embed, author_icon: e.target.value})} style={{ width: '100%', padding: '8px', background: '#0D1117', color: 'white', border: '1px solid #30363d' }} /></div></div></Section><Section title="BODY"><div style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}><div style={{ flex: 2 }}><InputLabel>TITLE</InputLabel><input value={embed.title} onChange={e => setEmbed({...embed, title: e.target.value})} style={{ width: '100%', padding: '8px', background: '#0D1117', color: 'white', border: '1px solid #30363d' }} /></div><div style={{ flex: 1 }}><InputLabel>COLOR</InputLabel><input type="color" value={embed.color} onChange={e => setEmbed({...embed, color: e.target.value})} style={{ width: '100%', height: '34px', padding: '0', background: 'none', border: 'none', cursor: 'pointer' }} /></div></div><InputLabel>URL</InputLabel><input value={embed.url} onChange={e => setEmbed({...embed, url: e.target.value})} style={{ width: '100%', padding: '8px', background: '#0D1117', color: 'white', border: '1px solid #30363d', marginBottom: '10px' }} /><InputLabel>DESCRIPTION</InputLabel><textarea value={embed.description} onChange={e => setEmbed({...embed, description: e.target.value})} style={{ width: '100%', padding: '10px', background: '#0D1117', color: 'white', border: '1px solid #30363d', minHeight: '120px' }} /></Section><Section title="FIELDS">{embed.fields.map((field, i) => (<div key={i} style={{ border: '1px dashed #30363d', padding: '10px', marginBottom: '10px', display: 'flex', flexDirection: 'column', gap: '5px' }}><div style={{ display: 'flex', justifyContent: 'space-between' }}><input value={field.name} onChange={e => updateField(i, 'name', e.target.value)} placeholder="Field Name" style={{ flex: 1, padding: '6px', background: '#0D1117', color: 'white', border: '1px solid #30363d', marginRight: '10px' }} /><label style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.8rem' }}><input type="checkbox" checked={field.inline} onChange={e => updateField(i, 'inline', e.target.checked)} /> Inline</label><button onClick={() => removeField(i)} style={{ background: 'none', border: 'none', color: '#da3633', cursor: 'pointer', marginLeft: '10px' }}>[X]</button></div><textarea value={field.value} onChange={e => updateField(i, 'value', e.target.value)} placeholder="Field Value" style={{ width: '100%', padding: '6px', background: '#0D1117', color: 'white', border: '1px solid #30363d' }} /></div>))}<button onClick={addField} style={{ padding: '8px', background: 'transparent', color: '#8b949e', border: '1px solid #30363d', cursor: 'pointer' }}>+ ADD FIELD</button></Section><Section title="IMAGES"><div style={{ display: 'flex', gap: '10px' }}><div style={{ flex: 1 }}><InputLabel>IMAGE URL</InputLabel><input value={embed.image_url} onChange={e => setEmbed({...embed, image_url: e.target.value})} style={{ width: '100%', padding: '8px', background: '#0D1117', color: 'white', border: '1px solid #30363d' }} /></div><div style={{ flex: 1 }}><InputLabel>THUMBNAIL URL</InputLabel><input value={embed.thumbnail_url} onChange={e => setEmbed({...embed, thumbnail_url: e.target.value})} style={{ width: '100%', padding: '8px', background: '#0D1117', color: 'white', border: '1px solid #30363d' }} /></div></div></Section><Section title="FOOTER"><div style={{ display: 'flex', gap: '10px', alignItems: 'flex-end' }}><div style={{ flex: 2 }}><InputLabel>TEXT</InputLabel><input value={embed.footer_text} onChange={e => setEmbed({...embed, footer_text: e.target.value})} style={{ width: '100%', padding: '8px', background: '#0D1117', color: 'white', border: '1px solid #30363d' }} /></div><div style={{ flex: 1 }}><InputLabel>ICON URL</InputLabel><input value={embed.footer_icon} onChange={e => setEmbed({...embed, footer_icon: e.target.value})} style={{ width: '100%', padding: '8px', background: '#0D1117', color: 'white', border: '1px solid #30363d' }} /></div><label style={{ display: 'flex', alignItems: 'center', gap: '5px', padding: '8px', color: '#8b949e', fontSize: '0.8rem' }}><input type="checkbox" checked={embed.timestamp} onChange={e => setEmbed({...embed, timestamp: e.target.checked})} /> Time</label></div></Section></div><div style={{ flex: '1', backgroundColor: '#36393f', borderRadius: '4px', padding: '20px', fontFamily: '"gg sans", "Noto Sans", "Helvetica Neue", Helvetica, Arial, sans-serif', position: 'sticky', top: '0' }}><div style={{ color: '#8b949e', fontSize: '0.8rem', marginBottom: '15px', fontFamily: 'monospace' }}>DISCORD PREVIEW</div>{embed.content && <div style={{ color: '#dcddde', marginBottom: '10px', whiteSpace: 'pre-wrap', lineHeight: '1.4' }}>{embed.content}</div>}<div style={{ display: 'flex', backgroundColor: '#2f3136', borderRadius: '4px', maxWidth: '520px' }}><div style={{ width: '4px', backgroundColor: embed.color, borderRadius: '4px 0 0 4px', flexShrink: 0 }}></div><div style={{ padding: '16px', flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}><div style={{ display: 'flex', gap: '16px' }}><div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>{embed.author_name && (<div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>{embed.author_icon && <img src={embed.author_icon} alt="" style={{ width: '24px', height: '24px', borderRadius: '50%' }} />}<span style={{ color: 'white', fontWeight: 'bold', fontSize: '0.9rem' }}>{embed.author_name}</span></div>)}{embed.title && <div style={{ color: embed.url ? '#00b0f4' : 'white', fontWeight: 'bold', fontSize: '1rem', cursor: embed.url ? 'pointer' : 'default' }}>{embed.title}</div>}{embed.description && <div style={{ color: '#dcddde', fontSize: '0.9rem', whiteSpace: 'pre-wrap', lineHeight: '1.4' }}>{embed.description}</div>}{embed.fields.length > 0 && (<div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginTop: '5px' }}>{embed.fields.map((f, i) => (<div key={i} style={{ flex: f.inline ? '1 1 30%' : '1 1 100%', minWidth: '150px' }}><div style={{ color: 'white', fontWeight: 'bold', fontSize: '0.85rem', marginBottom: '2px' }}>{f.name || '\u200B'}</div><div style={{ color: '#dcddde', fontSize: '0.85rem', whiteSpace: 'pre-wrap' }}>{f.value || '\u200B'}</div></div>))}</div>)}</div>{embed.thumbnail_url && <div style={{ flexShrink: 0 }}><img src={embed.thumbnail_url} alt="thumb" style={{ maxWidth: '80px', maxHeight: '80px', borderRadius: '4px' }} /></div>}</div>{embed.image_url && <div style={{ marginTop: '10px' }}><img src={embed.image_url} alt="img" style={{ maxWidth: '100%', borderRadius: '4px' }} /></div>}{(embed.footer_text || embed.timestamp) && (<div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '5px' }}>{embed.footer_icon && <img src={embed.footer_icon} alt="" style={{ width: '20px', height: '20px', borderRadius: '50%' }} />}<span style={{ color: '#72767d', fontSize: '0.75rem' }}>{embed.footer_text} {embed.timestamp && ' • Сегодня в 12:00'}</span></div>)}</div></div></div></div></div>)}
        {activeTab === 'SETTINGS' && ( <div style={{ maxWidth: '800px' }}><h1 style={{ color: '#B75CFF', marginBottom: '40px' }}>// GLOBAL CONFIGURATION</h1>{configs.map(conf => (<div key={conf.key} style={{ display: 'flex', justifyContent: 'space-between', padding: '20px', backgroundColor: '#161b22', border: '1px solid #30363d', marginBottom: '15px' }}><div><div style={{ fontWeight: 'bold' }}>{conf.key}</div><div style={{ color: '#8b949e', fontSize: '0.85rem' }}>{conf.description}</div></div><div><input id={`in-${conf.key}`} defaultValue={conf.value} style={{ padding: '10px', background: '#0D1117', color: 'white', border: '1px solid #30363d', marginRight: '10px' }} /><button onClick={() => handleConfigSave(conf.key, document.getElementById(`in-${conf.key}`).value)} style={{ padding: '10px 20px', background: '#238636', color: 'white', border: 'none', cursor: 'pointer' }}>SAVE</button></div></div>))}</div>)}
        {activeTab === 'MODERATION' && ( <div><h1 style={{ color: '#B75CFF', marginBottom: '40px' }}>// TICKET PROCESSING</h1>{tickets.length === 0 ? <p style={{ color: '#8b949e' }}>Очередь тикетов пуста.</p> : (<div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>{tickets.map(ticket => (<div key={ticket.id} style={{ backgroundColor: '#161b22', border: '1px solid #30363d', padding: '25px', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}><div style={{ flex: 1, paddingRight: '20px' }}><div style={{ color: '#8b949e', fontSize: '0.85rem', marginBottom: '10px' }}>TICKET_ID: {ticket.id} | USER_ID: {ticket.user_id}</div><div style={{ fontSize: '1.1rem', lineHeight: '1.5' }}>{ticket.content}</div></div><div style={{ display: 'flex', gap: '10px', flexDirection: 'column' }}><button onClick={() => handleTicketResolve(ticket.id, 'approve')} style={{ padding: '10px 20px', backgroundColor: '#238636', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', width: '120px' }}>APPROVE</button><button onClick={() => handleTicketResolve(ticket.id, 'deny')} style={{ padding: '10px 20px', backgroundColor: 'transparent', color: '#da3633', border: '1px solid #da3633', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', width: '120px' }}>DENY</button></div></div>))}</div>)}</div>)}
        {activeTab === 'AUDIT_TRAIL' && ( <div style={{ border: '1px solid #30363d', borderRadius: '8px', overflow: 'hidden' }}><table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}><thead><tr style={{ background: '#0D1117', color: '#8b949e' }}><th style={{ padding: '15px' }}>TIME</th><th style={{ padding: '15px' }}>SOURCE</th><th style={{ padding: '15px' }}>ACTION</th><th style={{ padding: '15px' }}>DETAILS</th></tr></thead><tbody>{logs.map(log => (<tr key={log.id} style={{ borderTop: '1px solid #30363d', background: '#161b22' }}><td style={{ padding: '15px' }}>{log.timestamp}</td><td style={{ padding: '15px', color: '#B75CFF' }}>{log.source_bot}</td><td style={{ padding: '15px' }}>{log.action}</td><td style={{ padding: '15px', color: '#8b949e' }}>{log.details}</td></tr>))}</tbody></table></div>)}
      </div>
    </div>
  );
}

export default function App() { return <BrowserRouter><Routes><Route path="/" element={<Home />} /><Route path="/login" element={<LoginHandler />} /><Route path="/dashboard" element={<Dashboard />} /></Routes></BrowserRouter>; }