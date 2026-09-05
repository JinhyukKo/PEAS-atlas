#!/usr/bin/env python3
"""Portable LinPEAS result viewer (Python standard library only)."""
from __future__ import annotations

import html
import json
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

TITLE1 = "══════════════╣"
TITLE2 = "╔══════════╣"
TITLE3 = "══╣"
INFO = "╚ "
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
BOX_DRAWING_CHARS = frozenset("═─━│┃║╔╗╚╝╠╣╦╩╬┌┐└┘├┤┬┴┼")
COLOR_CODES = {
    "REDYELLOW": "1;31;103", "RED": "1;31", "GREEN": "1;32", "YELLOW": "1;33",
    "BLUE": "1;34", "MAGENTA": "1;95", "CYAN": "1;36", "LIGHT_GREY": "1;37",
    "DARKGREY": "1;90",
}

def clean(s: str) -> str:
    return ANSI_RE.sub("", s).replace("\x1b", "").replace("[0m", "").strip()

def is_decoration(s: str) -> bool:
    """Return True for terminal borders such as ╚══════════╝."""
    value = clean(s).strip()
    return bool(value) and all(char in BOX_DRAWING_CHARS for char in value)

def title(s: str) -> str:
    return clean(s).replace("═", "").replace("╔", "").replace("╗", "").replace("╣", "").replace("╠", "").replace("╚", "").replace("╝", "").strip()

def colors(s: str) -> list[str]:
    found = []
    for name, code in COLOR_CODES.items():
        if f"\x1b[{code}m" in s and name not in found:
            found.append(name)
    return found

def parse_text(text: str) -> dict:
    data: dict = {}
    current = data
    main = sub = None
    def section() -> dict:
        return {"sections": {}, "lines": [], "infos": []}
    for raw in text.splitlines():
        line = raw.strip("\r\n")
        if not line or not clean(line) or is_decoration(line):
            continue
        if TITLE1 in line:
            name = title(line); data[name] = section(); main = data[name]; current = main
        elif TITLE2 in line and main is not None:
            name = title(line); main["sections"][name] = section(); sub = main["sections"][name]; current = sub
        elif TITLE3 in line and sub is not None:
            name = title(line); sub["sections"][name] = section(); current = sub["sections"][name]
        elif INFO in line:
            current.setdefault("infos", []).append(title(line))
        elif current is not data:
            current["lines"].append({"text": clean(line), "raw": line, "colors": colors(line)})
    return data

def stats(node: dict) -> tuple[int, int]:
    lines = len(node.get("lines", [])); sections = len(node.get("sections", {}))
    for child in node.get("sections", {}).values():
        a, b = stats(child); lines += a; sections += b
    return lines, sections

PAGE = r'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LinPEAS Atlas</title>
<style>
:root{color-scheme:dark;--bg:#071019;--surface:#0d1825;--surface-2:#111f30;--line:#20354a;--text:#edf5ff;--muted:#8fa5bb;--accent:#5eead4;--accent-dark:#123e42;--danger:#ff7a89;--warning:#ffd166}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:radial-gradient(900px 520px at 88% -15%,#173e58 0,transparent 66%),var(--bg);color:var(--text);font:14px/1.5 ui-sans-serif,system-ui,sans-serif}header{padding:28px 5vw 22px;border-bottom:1px solid var(--line);background:rgba(7,16,25,.8);backdrop-filter:blur(14px)}h1{margin:0;font-size:28px;letter-spacing:-.04em}header p{color:var(--muted);margin:5px 0 0}.layout{display:grid;grid-template-columns:320px minmax(0,1fr);min-height:calc(100vh - 112px)}aside{border-right:1px solid var(--line);padding:18px;background:rgba(7,16,25,.58);overflow:auto}.toolbar{position:sticky;top:0;background:var(--bg);padding-bottom:14px;z-index:2}input,button{font:inherit;color:var(--text);border-radius:9px}input{width:100%;padding:11px 12px;background:var(--surface);border:1px solid var(--line);outline:0;margin-bottom:10px}input:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(94,234,212,.12)}button{cursor:pointer;border:1px solid transparent}.upload{display:block;text-align:center;background:linear-gradient(135deg,#103543,#0d2232);border:1px dashed #397283;padding:12px;border-radius:9px;margin-bottom:12px;color:var(--accent);font-weight:700}.upload:hover{border-style:solid;background:#123845}.upload input{display:none}.download{width:100%;padding:10px;background:transparent;border-color:var(--line);color:#bdcee0}.download:hover{border-color:var(--accent);color:var(--accent)}.color-filters,.tactic-filters{display:flex;flex-wrap:wrap;gap:5px;margin:0 0 12px}.color-filters button,.tactic-filters button{padding:5px 7px;border:1px solid var(--line);background:var(--surface);font-size:10px;font-weight:800}.color-filters button.active,.tactic-filters button.active{border-color:currentColor;background:#182838}.color-filters .all,.tactic-filters .all{color:#bfd0df}.tactic-filters{padding-top:10px;border-top:1px solid var(--line)}.tactic-filters .tactic{color:#c8a8ff}.nav-label{color:var(--muted);font-size:11px;letter-spacing:.08em;text-transform:uppercase;margin:18px 8px 8px}.nav{margin-top:4px}.nav button{display:flex;align-items:center;justify-content:space-between;gap:10px;width:100%;text-align:left;margin:4px 0;padding:10px;border-color:transparent;background:transparent;color:#c7d5e4}.nav button.level-1{padding-left:21px;font-size:12px}.nav button.level-2{padding-left:34px;font-size:11px;color:#a9bdd0}.nav button.active,.nav button:hover{background:linear-gradient(90deg,var(--accent-dark),rgba(18,62,66,.18));color:#eafffb;border-color:#25646a}.nav-name{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.nav-meta{flex:none;color:var(--muted);font-size:11px}.nav-alert{color:var(--danger);margin-left:5px}.content{padding:30px 5vw 70px;max-width:1280px;width:100%}.eyebrow{color:var(--accent);font-size:12px;font-weight:800;letter-spacing:.1em;text-transform:uppercase}.summary{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0 28px}.metric{background:linear-gradient(145deg,rgba(17,31,48,.96),rgba(10,21,33,.96));border:1px solid var(--line);border-radius:12px;padding:13px 17px;min-width:140px;box-shadow:0 12px 28px rgba(0,0,0,.12)}.metric b{display:block;font-size:22px}.metric span{color:var(--muted);font-size:12px}.section{display:none;scroll-margin-top:24px}.section.active{display:block}.section h2{font-size:25px;letter-spacing:-.03em;margin:0 0 4px}.sub{color:var(--muted);margin:0 0 18px}.card{background:rgba(13,24,37,.9);border:1px solid var(--line);border-radius:11px;margin:12px 0;overflow:hidden}.card.section-filtered,.direct-lines.section-filtered{display:none!important}.card h3{font-size:14px;margin:0;padding:13px 16px;background:rgba(20,38,56,.8);border-bottom:1px solid var(--line);color:#cfe0ef}.tactic-tags{display:inline-flex;gap:4px;flex-wrap:wrap;margin-left:8px;vertical-align:middle}.tactic{display:inline-block;color:#d5bdff;background:rgba(153,104,255,.14);border:1px solid rgba(179,136,255,.35);border-radius:20px;padding:3px 6px;font:700 10px/1.1 ui-sans-serif,system-ui}.info{padding:10px 16px;color:#a9c9de;font-size:13px;border-bottom:1px solid rgba(32,53,74,.65)}.lines{padding:2px 16px 12px}.direct-lines{margin:12px 0;background:rgba(13,24,37,.6);border:1px solid var(--line);border-radius:11px;padding:2px 16px 12px}.card>.direct-lines{margin:0;border:0;border-radius:0;background:transparent}.line{padding:8px 0;border-bottom:1px solid rgba(32,53,74,.62);white-space:pre-wrap;word-break:break-word;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:12px}.line:last-child{border:0}.tag{display:inline-block;font:700 10px/1 ui-sans-serif,system-ui;padding:3px 6px;border-radius:20px;margin-left:7px;background:#273a51;color:#b8cae0}.mitre{display:inline-flex;align-items:baseline;gap:6px;margin-left:7px;color:#74ddff;text-decoration:none;font:700 11px/1.25 ui-sans-serif,system-ui;vertical-align:middle}.mitre:hover{text-decoration:underline}.mitre-name{color:#a9c9de;font-weight:600}.REDYELLOW{color:#ffe08a;background:#4b3320}.RED{color:var(--danger)}.GREEN{color:#76e8ae}.YELLOW{color:var(--warning)}.BLUE{color:#85b6ff}.MAGENTA{color:#f1a4ff}.CYAN{color:#71e8ef}.empty{padding:56px 22px;text-align:center;color:var(--muted);border:1px dashed var(--line);border-radius:12px}@media(max-width:800px){.layout{grid-template-columns:1fr}aside{border-right:0;border-bottom:1px solid var(--line);max-height:48vh}.toolbar{position:relative}.content{padding:24px 4vw}.nav{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:4px}.nav button{margin:0}.nav-label{grid-column:1/-1}.mitre-name{display:block}}
</style></head><body><div class="app-shell"><aside class="sidebar"><div class="brand"><span class="brand-kicker">LOCAL SECURITY REVIEW</span><h1>LinPEAS Atlas</h1><p>Structured privilege-escalation findings</p></div><div class="toolbar"><label class="upload">+ Upload result file<input id="file" type="file" accept=".txt,.log,.json,text/plain,application/json"></label><input id="search" placeholder="Search selected results"><div class="control-label">Severity</div><div class="color-filters" id="colorFilters"></div><div class="control-label">MITRE ATT&amp;CK tactics</div><div class="tactic-filters" id="tacticFilters"></div><button id="download" class="download">Download structured JSON</button></div><nav class="nav" id="nav"></nav></aside><main class="workbench"><header class="topbar"><div><span class="topbar-label">CURRENT VIEW</span><div class="scope" id="scope">Analysis results</div></div><div class="topbar-status"><span></span> Local analysis</div></header><div class="content"><div class="summary" id="summary"></div><div id="view"><div class="empty">Upload a result file to view the analysis.</div></div></div></main></div>
<script>
let parsed={}, flat=[],selectedId=null,selectedColors=new Set(); const $=id=>document.getElementById(id);
const FILTER_COLORS=['REDYELLOW','RED','YELLOW','GREEN','BLUE','MAGENTA','CYAN'];
document.head.insertAdjacentHTML('beforeend',`<style>.nav-root .nav-item{width:100%}.nav-children.collapsed{display:none}.nav .nav-item.level-1{padding-left:21px;font-size:12px}.nav .nav-item.level-2{padding-left:34px;font-size:11px;color:#a9bdd0}@media(max-width:800px){.nav-root{display:contents}}</style>`);
let selectedTactics=new Set();
const TACTICS={
 'T1003.003':['Credential Access'],'T1003.007':['Credential Access'],'T1005':['Collection'],'T1007':['Discovery'],'T1010':['Discovery'],'T1016':['Discovery'],'T1018':['Discovery'],'T1021.004':['Lateral Movement'],'T1033':['Discovery'],'T1040':['Credential Access','Discovery'],'T1049':['Discovery'],'T1053.003':['Execution','Persistence','Privilege Escalation'],'T1057':['Discovery'],'T1068':['Privilege Escalation'],'T1069.001':['Discovery'],'T1070.002':['Defense Evasion'],'T1080':['Defense Evasion','Lateral Movement'],'T1082':['Discovery'],'T1083':['Discovery'],'T1087.001':['Discovery'],'T1114.001':['Collection'],'T1120':['Discovery'],'T1134.004':['Defense Evasion','Privilege Escalation'],'T1211':['Defense Evasion'],'T1217':['Discovery'],'T1222':['Defense Evasion'],'T1518.001':['Discovery'],'T1539':['Credential Access'],'T1543.002':['Persistence','Privilege Escalation'],'T1546.004':['Persistence','Privilege Escalation'],'T1547.006':['Persistence','Privilege Escalation'],'T1548.001':['Defense Evasion','Privilege Escalation'],'T1548.003':['Defense Evasion','Privilege Escalation'],'T1548.004':['Defense Evasion','Privilege Escalation'],'T1552.001':['Credential Access'],'T1552.004':['Credential Access'],'T1552.007':['Credential Access'],'T1559.001':['Execution'],'T1563':['Credential Access','Lateral Movement'],'T1564.001':['Defense Evasion'],'T1574.007':['Defense Evasion','Persistence','Privilege Escalation'],'T1587.001':['Resource Development'],'T1590':['Reconnaissance'],'T1611':['Defense Evasion','Privilege Escalation'],'T1613':['Discovery']
};
const MITRE={
 'T1003.003':'NTDS','T1003.007':'Proc Filesystem','T1005':'Data from Local System','T1007':'System Service Discovery','T1010':'Application Window Discovery','T1016':'System Network Configuration Discovery','T1018':'Remote System Discovery','T1021.004':'Remote Services: SSH','T1033':'System Owner/User Discovery','T1040':'Network Sniffing','T1049':'System Network Connections Discovery','T1053.003':'Scheduled Task/Job: Cron','T1057':'Process Discovery','T1068':'Exploitation for Privilege Escalation','T1069.001':'Permission Groups Discovery: Local Groups','T1070.002':'Indicator Removal: Clear Linux or Mac System Logs','T1080':'Taint Shared Content','T1082':'System Information Discovery','T1083':'File and Directory Discovery','T1087.001':'Account Discovery: Local Account','T1114.001':'Email Collection: Local Email Collection','T1120':'Peripheral Device Discovery','T1134.004':'Access Token Manipulation: Parent PID Spoofing','T1211':'Exploitation for Defense Evasion','T1217':'Browser Bookmark Discovery','T1222':'File and Directory Permissions Modification','T1518.001':'Software Discovery: Security Software Discovery','T1539':'Steal Web Session Cookie','T1543.002':'Create or Modify System Process: Systemd Service','T1546.004':'Event Triggered Execution: Unix Shell Configuration Modification','T1547.006':'Boot or Logon Autostart Execution: Kernel Modules and Extensions','T1548.001':'Abuse Elevation Control Mechanism: Setuid and Setgid','T1548.003':'Abuse Elevation Control Mechanism: Sudo and Sudo Caching','T1548.004':'Abuse Elevation Control Mechanism: Elevated Execution with Prompt','T1552.001':'Unsecured Credentials: Credentials In Files','T1552.004':'Unsecured Credentials: Private Keys','T1552.007':'Unsecured Credentials: Container API','T1559.001':'Inter-Process Communication: Component Object Model','T1563':'Remote Service Session Hijacking','T1564.001':'Hide Artifacts: Hidden Files and Directories','T1574.007':'Hijack Execution Flow: PATH Interception by PATH Environment Variable','T1587.001':'Develop Capabilities: Malware','T1590':'Gather Victim Network Information','T1611':'Escape to Host','T1613':'Container and Resource Discovery'
};
function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function mitreText(s){return esc(s).replace(/\b(T\d{4}(?:\.\d{3})?)\b/gi,(all,id)=>{let key=id.toUpperCase(),name=MITRE[key];if(!name)return key;let url=`https://attack.mitre.org/techniques/${key.replace('.', '/')}/`;return `<a class="mitre" href="${url}" target="_blank" rel="noopener noreferrer" title="Open in MITRE ATT&CK">${key}<span class="mitre-name">${esc(name)}</span></a>`})}
function tacticsFor(text){let ids=String(text).match(/\bT\d{4}(?:\.\d{3})?\b/gi)||[];return [...new Set(ids.flatMap(id=>TACTICS[id.toUpperCase()]||[]))]}
function tacticsForNode(node,name){return [...new Set([ ...tacticsFor(name), ...Object.entries(node.sections||{}).flatMap(([child,n])=>tacticsForNode(n,child)) ])]}
function tacticTags(name){let tactics=tacticsFor(name);return tactics.length?`<span class="tactic-tags">${tactics.map(t=>`<span class="tactic" title="MITRE ATT&CK tactic">${esc(t)}</span>`).join('')}</span>`:''}
function renderTacticFilters(){let root=$('tacticFilters'),tactics=[...new Set(flat.flatMap(item=>item.tactics))].sort();root.innerHTML=`<button class="all ${selectedTactics.size?'':'active'}" data-tactic="">ALL TACTICS</button>`+tactics.map(t=>`<button class="tactic ${selectedTactics.has(t)?'active':''}" data-tactic="${esc(t)}">${esc(t)}</button>`).join('');root.querySelectorAll('button').forEach(b=>b.onclick=()=>{let t=b.dataset.tactic;if(!t)selectedTactics.clear();else selectedTactics.has(t)?selectedTactics.delete(t):selectedTactics.add(t);renderTacticFilters();filter()})}
function normalize(data){let walk=n=>({sections:Object.fromEntries(Object.entries(n.sections||{}).map(([k,v])=>[k,walk(v)])),infos:Array.isArray(n.infos)?n.infos:[],lines:Array.isArray(n.lines)?n.lines.map(x=>({text:x.text??x.clean_text??'',raw:x.raw??x.raw_text??'',colors:Array.isArray(x.colors)?x.colors:Object.keys(x.colors||{})})):[]});return Object.fromEntries(Object.entries(data||{}).map(([k,v])=>[k,walk(v)]))}
function renderColorFilters(){let root=$('colorFilters');root.innerHTML=`<button class="all ${selectedColors.size?'':'active'}" data-color="">ALL</button>`+FILTER_COLORS.map(c=>`<button class="${c} ${selectedColors.has(c)?'active':''}" data-color="${c}">${c}</button>`).join('');root.querySelectorAll('button').forEach(b=>b.onclick=()=>{let c=b.dataset.color;if(!c)selectedColors.clear();else selectedColors.has(c)?selectedColors.delete(c):selectedColors.add(c);renderColorFilters();filter()})}
function navLabel(name){return String(name).replace(/\s*\([^)]*\bT\d{4}(?:\.\d{3})?[^)]*\)/gi,'').trim()||name}
function makeNavItem(name,node,id,level,rootId){let n=count(node),label=navLabel(name||'(Untitled)'),item={id,name:label,node,level,rootId,search:index(node,name),tactics:tacticsForNode(node,name)};flat.push(item);let b=document.createElement('button');b.className=`nav-item level-${Math.min(level,2)}`;b.innerHTML=`<span class="nav-name">${level?'↳ ':''}${esc(label)}</span><span class="nav-meta">${n.lines.toLocaleString()}<span class="nav-alert">${n.critical?` · ${n.critical} !`:''}</span></span>`;b.dataset.id=id;b.onclick=()=>show(id,true);return b}
function addNavItem(nav,name,node,id,level,rootId){nav.appendChild(makeNavItem(name,node,id,level,rootId));Object.entries(node.sections||{}).forEach(([child,childNode],i)=>addNavItem(nav,child,childNode,`${id}-${i}`,level+1,rootId))}
function addRootNav(nav,name,node,id){let row=document.createElement('div'),group=document.createElement('div'),rootButton=makeNavItem(name,node,id,0,id);row.className='nav-root';rootButton.onclick=()=>toggleRoot(id);row.appendChild(rootButton);nav.appendChild(row);group.className='nav-children collapsed';group.id=`nav-${id}`;Object.entries(node.sections||{}).forEach(([child,childNode],i)=>addNavItem(group,child,childNode,`${id}-${i}`,1,id));nav.appendChild(group)}
function render(){flat=[];const nav=$('nav'),view=$('view');nav.innerHTML='<div class="nav-label">Categories & sections</div>';view.innerHTML='';let total=0,critical=0;
 Object.entries(parsed).forEach(([name,node],i)=>{let id='s'+i,n=count(node),label=name||'(Untitled)';total+=n.lines;critical+=n.critical;addRootNav(nav,label,node,id);view.insertAdjacentHTML('beforeend',`<article class="section" id="${id}"><h2>${mitreText(label)}</h2><p class="sub">${n.lines.toLocaleString()} lines · ${n.sections} subsections · <span class="nav-alert">${n.critical} RED signals</span></p>${cards(node,id)}</article>`)});
 $('summary').innerHTML=`<div class="metric"><b>${Object.keys(parsed).length}</b><span>Top-level categories</span></div><div class="metric"><b>${total.toLocaleString()}</b><span>Analyzed lines</span></div><div class="metric"><b style="color:var(--danger)">${critical.toLocaleString()}</b><span>RED signals</span></div>`;
 renderColorFilters();renderTacticFilters();if(!flat.length){view.innerHTML='<div class="empty">No recognizable LinPEAS sections were found.</div>';return}show(selectedId&&flat.some(x=>x.id===selectedId)?selectedId:flat[0].id,false,false);}
function count(n){let lines=(n.lines||[]).length,critical=(n.lines||[]).filter(x=>x.colors.includes('RED')||x.colors.includes('REDYELLOW')).length,sections=Object.keys(n.sections||{}).length;Object.values(n.sections||{}).forEach(c=>{let x=count(c);lines+=x.lines;critical+=x.critical;sections+=x.sections});return {lines,critical,sections}}
function directLines(n){return n.lines?.length?`<div class="lines direct-lines">${n.lines.map(line).join('')}</div>`:''}
function cards(n,base){let out=directLines(n);Object.entries(n.sections||{}).forEach(([name,c],i)=>{let id=`${base}-${i}`,tactics=tacticsFor(name);out+=`<div class="card" id="${id}" data-tactics="${tactics.join('|')}"><h3>${mitreText(name)}${tacticTags(name)}</h3>${(c.infos||[]).map(x=>`<div class="info">${esc(x)}</div>`).join('')}${cards(c,id)}</div>`});return out}
function ansi(x){let source=x.raw||x.text,active='',out='',last=0,rx=/\x1b\[([0-9;]*)m/g,m,map={'1;31;103':'REDYELLOW','1;31':'RED','1;32':'GREEN','1;33':'YELLOW','1;34':'BLUE','1;95':'MAGENTA','1;35':'MAGENTA','1;36':'CYAN','1;96':'CYAN','1;37':'LIGHT_GREY','1;90':'DARKGREY'};while((m=rx.exec(source))){let part=esc(source.slice(last,m.index));out+=active?`<span class="${active}">${part}</span>`:part;let code=m[1];active=code==='0'||!code?'':(map[code]||active);last=rx.lastIndex}let tail=esc(source.slice(last));return out+(active?`<span class="${active}">${tail}</span>`:tail)}
function line(x){let colorList=(x.colors||[]).join(',');return `<div class="line" data-text="${esc(x.text.toLowerCase())}" data-colors="${colorList}">${ansi(x)}</div>`}
function index(n,name){return `${name} ${(n.infos||[]).join(' ')} ${(n.lines||[]).map(x=>x.text).join(' ')} ${Object.entries(n.sections||{}).map(([k,v])=>index(v,k)).join(' ')}`.toLowerCase()}
function expandRoot(rootId){document.querySelectorAll('.nav-children').forEach(group=>group.classList.toggle('collapsed',group.id!==`nav-${rootId}`))}
function toggleRoot(rootId){let group=$(`nav-${rootId}`),wasClosed=group.classList.contains('collapsed');if(wasClosed)expandRoot(rootId);else group.classList.add('collapsed');show(rootId,true,false)}
function show(id,move,expand=true){selectedId=id;let item=flat.find(x=>x.id===id);if(!item)return;if(expand)expandRoot(item.rootId);let root=$(item.rootId),target=$(id);document.querySelectorAll('.section').forEach(x=>x.classList.toggle('active',x.id===item.rootId));root.querySelectorAll('.card').forEach(card=>card.classList.toggle('section-filtered',item.level>0&&card!==target&&!card.contains(target)));root.querySelectorAll('.direct-lines').forEach(lines=>{let owner=lines.closest('.card');lines.classList.toggle('section-filtered',item.level>0&&owner!==target)});document.querySelectorAll('.nav .nav-item').forEach(x=>x.classList.toggle('active',x.dataset.id===id));$('scope').textContent=`${item.level?'Section':'Category'} / ${item.name}`;filter();if(move)requestAnimationFrame(()=>target.scrollIntoView({behavior:'smooth',block:'start'}))}
function filter(){let q=$('search').value.trim().toLowerCase(),active=$(selectedId),hasColors=selectedColors.size>0,hasTactics=selectedTactics.size>0;if(!active)return;active.querySelectorAll('.line').forEach(x=>{let colors=x.dataset.colors.split(',').filter(Boolean),colorMatch=!hasColors||colors.some(c=>selectedColors.has(c)),match=(!q||x.dataset.text.includes(q))&&colorMatch;x.dataset.visible=match?'1':'0';x.style.display=match?'block':'none'});active.querySelectorAll('.card').forEach(c=>{let lineMatch=[...c.querySelectorAll('.line')].some(x=>x.dataset.visible==='1'),textMatch=!q||c.textContent.toLowerCase().includes(q),ownTactics=c.dataset.tactics.split('|').filter(Boolean),tacticMatch=!hasTactics||ownTactics.some(t=>selectedTactics.has(t))||[...c.querySelectorAll('.card')].some(child=>child.dataset.tactics.split('|').some(t=>selectedTactics.has(t)));c.style.display=textMatch&&(!hasColors||lineMatch)&&tacticMatch?'block':'none'});document.querySelectorAll('.nav .nav-item').forEach(b=>{let item=flat.find(x=>x.id===b.dataset.id),colorMatch=!hasColors||[...$(b.dataset.id).querySelectorAll('.line')].some(x=>x.dataset.colors.split(',').some(c=>selectedColors.has(c))),tacticMatch=!hasTactics||item.tactics.some(t=>selectedTactics.has(t));b.style.display=(!q||item.search.includes(q))&&colorMatch&&tacticMatch?'flex':'none'});}
$('file').onchange=async e=>{let f=e.target.files[0];if(!f)return;let t=await f.text();try{parsed=normalize(JSON.parse(t))}catch(_){let r=await fetch('/parse',{method:'POST',headers:{'Content-Type':'text/plain; charset=utf-8'},body:t});parsed=normalize(await r.json())}render()};
$('search').oninput=filter;$('download').onclick=()=>{let a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(parsed,null,2)],{type:'application/json'}));a.download='linpeas-structured.json';a.click()};
fetch('/default.json').then(r=>r.ok?r.json():null).then(x=>{if(x){parsed=normalize(x);render()}})
</script></body></html>'''

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/": self.send(200, "text/html; charset=utf-8", PAGE.encode())
        elif path == "/default.json":
            try:
                with open("result.txt", encoding="utf-8", errors="replace") as f: body=json.dumps(parse_text(f.read())).encode()
                self.send(200, "application/json", body)
            except OSError: self.send(404, "application/json", b"{}")
        else: self.send(404, "text/plain", b"Not found")
    def do_POST(self):
        if urlparse(self.path).path != "/parse": self.send(404, "text/plain", b"Not found"); return
        length=int(self.headers.get("Content-Length",0))
        if length > 50 * 1024 * 1024:
            self.send(413, "text/plain; charset=utf-8", b"File too large (max 50 MB)"); return
        raw=self.rfile.read(length)
        body=json.dumps(parse_text(raw.decode("utf-8", "replace"))).encode(); self.send(200,"application/json",body)
    def send(self, code, typ, body):
        self.send_response(code); self.send_header("Content-Type",typ); self.send_header("Content-Length",str(len(body))); self.send_header("Cache-Control","no-store"); self.end_headers(); self.wfile.write(body)

def main():
    import argparse
    p=argparse.ArgumentParser(description="LinPEAS result web viewer")
    p.add_argument("--host",default="0.0.0.0"); p.add_argument("--port",type=int,default=8080); args=p.parse_args()
    print(f"LinPEAS Atlas: http://127.0.0.1:{args.port} (Ctrl+C to stop)")
    ThreadingHTTPServer((args.host,args.port),Handler).serve_forever()
if __name__ == "__main__": main()
