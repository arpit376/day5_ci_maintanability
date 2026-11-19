#!/usr/bin/env python3
"""capture_view: turn a capture into ONE self-contained HTML page with a Wireshark-style layout
(packet list, packet details tree, hex bytes, display filter). Open it in any browser, no install.

    python libraries/capture_view.py results/captures/nas_order.capture.json      -> .html next to it
    python libraries/capture_view.py attach.pcap [-o view.html]                   -> needs tshark

Inputs
  *.json          the simulated capture of this kit. Addresses and bytes are GENERATED for display
                  (the page says so in its status bar); message order, NAS types, causes and TEIDs are real.
  *.pcap/.pcapng  a real capture, decoded by tshark: columns from `tshark -T fields -e _ws.col.*`,
                  details and bytes from `tshark -T json -x`.  (Written against tshark 3.x/4.x output,
                  not yet run on your VM: if a column looks wrong, send me the page.)

Display filter (top bar), a small subset: `s1ap`, `nas-eps`, `gtp`, `imsi == 0010...`, `nas == 0x44`,
`emm.cause == 8`, `ip.addr == 10.0.1.10`, `info contains "Reject"`, `frame.number > 5`,
combined with `&&`, `||` and a leading `!`.

This is an independent teaching viewer, not Wireshark and not affiliated with it.
"""
import argparse
import html
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from capture_backend import EMM_NAMES  # noqa: E402

ENB, MME, SGW, UE_NET = "10.0.1.12", "10.0.1.10", "10.0.1.10", "172.16.0.2"
DOWNLINK = {"DownlinkNASTransport", "InitialContextSetupRequest", "Paging", "UEContextReleaseCommand"}
S1AP_CODES = {"InitialUEMessage": 12, "DownlinkNASTransport": 11, "UplinkNASTransport": 13,
              "InitialContextSetupRequest": 9, "InitialContextSetupResponse": 9,
              "UEContextReleaseCommand": 23, "Paging": 10}


def _sentence(name):
    return name[:1].upper() + name[1:].lower() if name else name


# ---------------------------------------------------------------- simulated JSON
def packets_from_sim(path):
    with open(path) as f:
        events = json.load(f)["events"]
    out = []
    for n, e in enumerate(events, 1):
        proto, msg, nas = e["proto"], e["msg"], e.get("nas_type", "")
        code = int(nas, 16) if nas else None
        nas_name = EMM_NAMES.get(code, "") if code else ""
        imsi = e.get("imsi", "")
        if proto == "GTP-U":
            up = e.get("direction") == "UL"
            src, dst = (ENB, SGW) if up else (SGW, ENB)
            inner = (UE_NET, "8.8.8.8") if up else ("8.8.8.8", UE_NET)
            info = f"{msg} (TEID 0x{e.get('teid', 0):x})"
            payload = bytes([0x30, 0xFF, 0x00, 0x54]) + int(e.get("teid", 0)).to_bytes(4, "big") + \
                bytes([0x45, 0x00]) + (8 if "request" in msg else 0).to_bytes(1, "big")
            ip_proto, ports, pname, hl = 17, (2152, 2152), "GTP", None
            tree_proto = [("GPRS Tunnelling Protocol", [
                ("Flags: 0x30", []), ("Message Type: T-PDU (0xff)", []),
                (f"TEID: 0x{e.get('teid', 0):08x}", [])]),
                (f"Internet Protocol Version 4, Src: {inner[0]}, Dst: {inner[1]}", []),
                (f"Internet Control Message Protocol: {msg}", [])]
        else:
            down = msg in DOWNLINK
            src, dst = (MME, ENB) if down else (ENB, MME)
            info = msg + (f", {_sentence(nas_name)}" if nas_name else "")
            if e.get("emm_cause"):
                info += f" (EMM cause {e['emm_cause']})"
            payload = bytes([0x00, S1AP_CODES.get(msg, 0), 0x40, 0x20, 0x00, 0x00]) + \
                (bytes([0x07, code]) if code else b"")
            ip_proto, ports, pname = 132, (36412, 36412), "NAS-EPS" if nas_name else "S1AP"
            s1 = [(f"procedureCode: id-{msg} ({S1AP_CODES.get(msg, 0)})", []), ("criticality: reject (0)", [])]
            if e.get("erab_id") is not None:
                s1.append((f"E-RAB ID: {e['erab_id']}", []))
            if e.get("teid") is not None:
                s1.append((f"gTP-TEID: 0x{e['teid']:08x}", []))
            tree_proto = [("S1 Application Protocol", s1)]
            if nas_name:
                nasnode = [("Security header type: Plain NAS message, not security protected (0)", []),
                           (f"NAS EPS Mobility Management Message Type: {nas_name} (0x{code:02x})", [])]
                if e.get("emm_cause"):
                    nasnode.append((f"EMM cause: {e['emm_cause']}", []))
                tree_proto.append(("Non-Access-Stratum (NAS)PDU", nasnode))
        eth = bytes.fromhex("0a0000000002" "0a0000000001" "0800")
        iph = bytes([0x45, 0, 0, 0, 0, 0, 0, 0, 64, ip_proto, 0, 0]) + \
            bytes(int(x) for x in src.split(".")) + bytes(int(x) for x in dst.split("."))
        l4 = (ports[0].to_bytes(2, "big") + ports[1].to_bytes(2, "big") + bytes(8)) if ip_proto == 132 else \
            (ports[0].to_bytes(2, "big") + ports[1].to_bytes(2, "big") + bytes([0, 8, 0, 0]))
        raw = eth + iph + l4 + payload
        t = e["t"]
        tree = [
            (f"Frame {n}: {len(raw)} bytes on wire ({len(raw) * 8} bits)", [(f"Arrival Time offset: {t:.6f} s", []),
                                                                           ("[Protocols in frame: eth:ip:" +
                                                                            ("udp:gtp" if ip_proto == 17 else "sctp:s1ap" + (":nas-eps" if nas_name else "")) + "]", [])]),
            (f"Ethernet II", []),
            (f"Internet Protocol Version 4, Src: {src}, Dst: {dst}", []),
            ("User Datagram Protocol" if ip_proto == 17 else "Stream Control Transmission Protocol",
             [(f"Source Port: {ports[0]}", []), (f"Destination Port: {ports[1]}", [])]),
        ] + tree_proto
        if imsi:
            tree.append((f"[Test info] IMSI: {imsi}", []))
        out.append({"no": n, "time": f"{t:.6f}", "src": src, "dst": dst, "proto": pname, "len": len(raw),
                    "info": info, "imsi": imsi, "nas": f"0x{code:02x}" if code else "",
                    "emm_cause": str(e.get("emm_cause", "")), "tree": _t(tree), "hex": raw.hex(),
                    "bad": code in (0x44, 0x54, 0x5C)})
    return out, "simulated capture: addresses and bytes are generated for display"


def _t(nodes):
    return [{"t": t, "c": _t(c)} for t, c in nodes]


# ---------------------------------------------------------------- real pcap (tshark)
def _walk(obj, key=None):
    """tshark JSON layer -> tree nodes. Skips *_raw helper keys."""
    nodes = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.endswith("_raw") or k.endswith("_tree") and False:
                continue
            if isinstance(v, (dict, list)):
                nodes.append({"t": k.replace("_tree", ""), "c": _walk(v)})
            else:
                nodes.append({"t": f"{k}: {v}", "c": []})
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, (dict, list)):
                nodes.append({"t": f"[{i}]", "c": _walk(v)})
            else:
                nodes.append({"t": str(v), "c": []})
    return nodes


def packets_from_pcap(path):
    if subprocess.run(["which", "tshark"], capture_output=True).returncode != 0:
        raise SystemExit("tshark is not installed:  sudo apt install tshark")
    cols = ["frame.number", "frame.time_relative", "_ws.col.Source", "_ws.col.Destination",
            "_ws.col.Protocol", "frame.len", "_ws.col.Info", "nas_eps.nas_msg_emm_type", "e212.imsi",
            "nas_eps.emm.cause"]
    args = ["tshark", "-r", path, "-T", "fields", "-E", "separator=\t"]
    for c in cols:
        args += ["-e", c]
    rows = subprocess.check_output(args, text=True).splitlines()
    details = json.loads(subprocess.check_output(["tshark", "-r", path, "-T", "json", "-x"], text=True))
    out = []
    for i, line in enumerate(rows):
        f = (line.split("\t") + [""] * len(cols))[:len(cols)]
        layers = details[i]["_source"]["layers"] if i < len(details) else {}
        raw = layers.get("frame_raw", [""])[0] if isinstance(layers.get("frame_raw"), list) else ""
        nas = f[7].split(",")[0] if f[7] else ""
        nas_v = int(nas, 16) if nas else None
        tree = [{"t": name, "c": _walk(val)} for name, val in layers.items() if not name.endswith("_raw")]
        out.append({"no": int(f[0] or i + 1), "time": f"{float(f[1] or 0):.6f}", "src": f[2], "dst": f[3],
                    "proto": f[4], "len": int(f[5] or 0), "info": f[6], "imsi": f[8], "nas": f"0x{nas_v:02x}" if nas_v else "",
                    "emm_cause": f[9].split(",")[0], "tree": tree, "hex": raw,
                    "bad": nas_v in (0x44, 0x54, 0x5C)})
    return out, f"decoded with tshark from {os.path.basename(path)}"


# ---------------------------------------------------------------- page
PAGE = r"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>__TITLE__</title>
<style>
*{box-sizing:border-box}body{margin:0;font:12px/1.35 "DejaVu Sans",Arial,sans-serif;color:#111;background:#ececec;display:flex;flex-direction:column;height:100vh}
#bar{display:flex;align-items:center;gap:8px;padding:5px 8px;background:#f3f3f3;border-bottom:1px solid #bbb}
#bar b{font-size:12px;color:#222}#f{flex:1;padding:4px 6px;border:1px solid #999;font:12px Consolas,monospace;background:#fff}
#f.bad{background:#ffd6d6;border-color:#c00}#f.ok{background:#d9f7d9;border-color:#2a2}
button{padding:3px 10px;border:1px solid #999;background:#fafafa;cursor:pointer}
#pk{flex:0 0 38%;overflow:auto;background:#fff;border-bottom:3px solid #aaa}
table{border-collapse:collapse;width:100%;font-size:12px}th{position:sticky;top:0;background:#e9e9e9;text-align:left;padding:2px 6px;border-right:1px solid #ccc;border-bottom:1px solid #aaa;font-weight:600}
td{padding:1px 6px;white-space:nowrap;border-right:1px solid #f0f0f0}tr{cursor:default}
tr.s1ap td,tr.nas-eps td{background:#e7e6ff}tr.gtp td{background:#d6e8ff}tr.sctp td{background:#ffe3e5}tr.bad td{background:#12272e!important;color:#ff7878}
tr.sel td{background:#0b5fd1!important;color:#fff!important}
#mid{flex:1;display:flex;min-height:0}#dt{flex:1;overflow:auto;background:#fff;padding:4px 2px;border-right:3px solid #aaa;min-width:30%}
#hx{flex:0 0 560px;overflow:auto;background:#fff;padding:4px 8px;font:12px Consolas,"DejaVu Sans Mono",monospace;white-space:pre}
.n{margin-left:14px}.t{cursor:default;padding:0 2px}.t:hover{background:#e8f0ff}.t.sel{background:#0b5fd1;color:#fff}
.tg{display:inline-block;width:12px;color:#555;cursor:pointer}
.hi{background:#9cc3ff}#st{padding:2px 8px;background:#f3f3f3;border-top:1px solid #bbb;color:#333;font-size:11px}
</style></head><body>
<div id="bar"><b>Capture viewer</b><input id="f" placeholder="Display filter, e.g. nas-eps &amp;&amp; imsi == 0010...   (Enter to apply)" spellcheck="false"><button id="cl">Clear</button></div>
<div id="pk"><table><thead><tr><th>No.</th><th>Time</th><th>Source</th><th>Destination</th><th>Protocol</th><th>Length</th><th>Info</th></tr></thead><tbody id="tb"></tbody></table></div>
<div id="mid"><div id="dt"></div><div id="hx"></div></div>
<div id="st"></div>
<script>
const P=__DATA__, NOTE=__NOTE__;
const tb=document.getElementById('tb'),dt=document.getElementById('dt'),hx=document.getElementById('hx'),st=document.getElementById('st'),fi=document.getElementById('f');
let shown=[],cur=-1;
function cls(p){p=p.toLowerCase();return p.includes('nas')?'nas-eps':p.includes('s1ap')?'s1ap':p.includes('gtp')?'gtp':p.includes('sctp')?'sctp':''}
function esc(s){return String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
function val(p,name){switch(name){case 'frame.number':return p.no;case 'frame.len':return p.len;case 'imsi':return p.imsi;case 'nas':return p.nas;
 case 'emm.cause':return p.emm_cause;case 'info':return p.info;case 'proto':return p.proto;case 'ip.src':return p.src;case 'ip.dst':return p.dst;
 case 'ip.addr':return p.src+' '+p.dst;} return undefined}
function term(p,t){t=t.trim();let neg=false;while(t[0]=='!'){neg=!neg;t=t.slice(1).trim()}
 let r,m;
 if(m=t.match(/^([\w.]+)\s*(==|!=|>=|<=|>|<|contains)\s*"?([^"]*)"?$/)){const v=val(p,m[1]);const a=String(v===undefined?'':v),b=m[3];
  if(m[2]=='contains')r=a.toLowerCase().includes(b.toLowerCase());
  else if(m[1]=='ip.addr'&&m[2]=='==')r=a.split(' ').includes(b);
  else if(m[2]=='==')r=a==b;else if(m[2]=='!=')r=a!=b;else{const x=parseFloat(a),y=parseFloat(b);r=m[2]=='>'?x>y:m[2]=='<'?x<y:m[2]=='>='?x>=y:x<=y}}
 else{const k=t.toLowerCase();r=!k||p.proto.toLowerCase().includes(k)||p.info.toLowerCase().includes(k)||(k=='nas-eps'&&p.nas!=='')}
 return neg?!r:r}
function match(p,expr){return expr.split('||').some(o=>o.split('&&').every(a=>term(p,a)))}
function render(){tb.innerHTML='';shown.forEach((p,i)=>{const tr=document.createElement('tr');tr.className=cls(p.proto)+(p.bad?' bad':'');
 tr.innerHTML=`<td>${p.no}</td><td>${p.time}</td><td>${esc(p.src)}</td><td>${esc(p.dst)}</td><td>${esc(p.proto)}</td><td>${p.len}</td><td>${esc(p.info)}</td>`;
 tr.onclick=()=>pick(i);tb.appendChild(tr)});st.textContent=`${NOTE}  |  Displayed: ${shown.length} of ${P.length}`;cur=-1;dt.innerHTML='';hx.innerHTML=''}
function pick(i){if(i<0||i>=shown.length)return;if(cur>=0)tb.children[cur].classList.remove('sel');cur=i;const tr=tb.children[i];tr.classList.add('sel');tr.scrollIntoView({block:'nearest'});
 const p=shown[i];dt.innerHTML='';p.tree.forEach((n,k)=>dt.appendChild(node(n,k<1?false:k>3||false,p)));
 hexdump(p,null)}
function node(n,open,p){const d=document.createElement('div');const h=document.createElement('div');h.className='t';const has=n.c&&n.c.length;
 h.innerHTML=`<span class="tg">${has?(open?'▾':'▸'):''}</span>${esc(n.t)}`;d.appendChild(h);let kids;
 if(has){kids=document.createElement('div');kids.className='n';n.c.forEach(c=>kids.appendChild(node(c,false,p)));kids.style.display=open?'block':'none';d.appendChild(kids);
  h.querySelector('.tg').onclick=e=>{e.stopPropagation();const o=kids.style.display=='none';kids.style.display=o?'block':'none';h.querySelector('.tg').textContent=o?'▾':'▸'}}
 h.onclick=()=>{dt.querySelectorAll('.t.sel').forEach(x=>x.classList.remove('sel'));h.classList.add('sel');
  const m=n.t.match(/\(0x([0-9a-f]{2})\)/i);if(m&&p.hex){const idx=p.hex.toLowerCase().lastIndexOf(m[1].toLowerCase());hexdump(p,idx>=0&&idx%2==0?[idx/2,1]:null)}}
 return d}
function hexdump(p,hl){const b=p.hex.match(/../g)||[];let s='';for(let o=0;o<b.length;o+=16){const row=b.slice(o,o+16);
 const hexs=row.map((x,j)=>{const on=hl&&o+j>=hl[0]&&o+j<hl[0]+hl[1];return on?`<span class="hi">${x}</span>`:x}).join(' ');
 const asc=row.map((x,j)=>{const c=parseInt(x,16);const ch=c>=32&&c<127?String.fromCharCode(c):'.';return hl&&o+j>=hl[0]&&o+j<hl[0]+hl[1]?`<span class="hi">${esc(ch)}</span>`:esc(ch)}).join('');
 const pad='   '.repeat(16-row.length);s+=`${o.toString(16).padStart(4,'0')}  ${hexs}${pad}  ${asc}\n`}hx.innerHTML=s||'(no bytes)'}
function apply(){const e=fi.value.trim();fi.className='';if(!e){shown=P.slice();render();return}
 try{shown=P.filter(p=>match(p,e));fi.className='ok'}catch(x){fi.className='bad';return}render()}
fi.addEventListener('keydown',e=>{if(e.key=='Enter')apply()});document.getElementById('cl').onclick=()=>{fi.value='';apply()};
document.addEventListener('keydown',e=>{if(document.activeElement===fi)return;if(e.key=='ArrowDown'){pick(cur+1);e.preventDefault()}if(e.key=='ArrowUp'){pick(cur-1);e.preventDefault()}});
shown=P.slice();render();if(shown.length)pick(0);
</script></body></html>"""


def build_html(src, out=None, title=None):
    """Write the viewer page for ``src`` and return its path."""
    packets, note = packets_from_sim(src) if src.endswith(".json") else packets_from_pcap(src)
    out = out or os.path.splitext(src)[0].replace(".capture", "") + ".html"
    title = title or f"Capture viewer: {os.path.basename(src)}"
    data = json.dumps(packets).replace("</", "<\\/")
    page = PAGE.replace("__TITLE__", html.escape(title)).replace("__DATA__", data) \
        .replace("__NOTE__", json.dumps(note))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Wireshark-style HTML viewer for a capture")
    ap.add_argument("capture")
    ap.add_argument("-o", "--output")
    a = ap.parse_args()
    print(build_html(a.capture, a.output))
