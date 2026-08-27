"""The stylesheet the automation page carries inline.

Held apart from ``page.py`` because it is presentation data rather than derivation,
and because a page module that also holds sixty lines of CSS reaches the module
ceiling for a reason that has nothing to do with what it computes. The palette
follows docs/topology.html so the four rendered pages read as one surface.
"""

from __future__ import annotations

STYLE = """
:root{--bg:#fafafc;--panel:#f0f2f7;--fg:#151922;--fg2:#39404f;--muted:#616a7c;--line:#d3d9e4;--soft:#e3e8f0;--acc:#2e4fa8;
--ok:#0e7263;--okbg:#ddf0ec;--warn:#8f5c08;--warnbg:#f7ebd5;--bad:#a3282f;--badbg:#f8e3e4;--abs:#6e7789;--absbg:#eceef3}
@media(prefers-color-scheme:dark){:root{--bg:#0e1116;--panel:#161a22;--fg:#e6e9f0;--fg2:#bfc6d4;--muted:#8b94a6;
--line:#272d39;--soft:#1e232d;--acc:#86a5f0;--ok:#45c2ad;--okbg:#10312d;--warn:#dca748;--warnbg:#33280f;--bad:#e8868c;
--badbg:#3a1c1f;--abs:#8a93a5;--absbg:#1b202a}}
*{box-sizing:border-box}body{margin:0;padding:2.4rem 1.2rem 5rem;background:var(--bg);color:var(--fg);
font:15px/1.6 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}main{max-width:74rem;
margin:auto}h1{font-size:2.1rem;margin:0 0 .4rem;letter-spacing:-.03em;line-height:1.05}
h2{font-size:1.15rem;margin:2.8rem 0 .6rem;padding-bottom:.35rem;border-bottom:1px solid var(--line)}
h3{font-size:.95rem;margin:1.6rem 0 .4rem}p{margin:0 0 .85rem;max-width:68ch}
.sub{color:var(--fg2);margin:.2rem 0 1.5rem;max-width:64ch;font-size:1.02rem}
.prov{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--acc);border-radius:.3rem;
padding:.8rem 1rem;margin:0 0 1.4rem;overflow-x:auto;font:12px/1.8 ui-monospace,SFMono-Regular,Menlo,monospace;
color:var(--fg2)}.prov b{color:var(--muted);font-weight:500;display:inline-block;min-width:15ch}
.counts{display:grid;grid-template-columns:repeat(auto-fit,minmax(8rem,1fr));gap:1px;background:var(--line);
border:1px solid var(--line);border-radius:.3rem;overflow:hidden;margin:0 0 1.4rem}.counts div{background:var(--bg);
padding:.7rem .85rem}
.counts b{display:block;font:600 1.7rem/1.1 ui-monospace,SFMono-Regular,Menlo,monospace;font-variant-numeric:tabular-nums;
letter-spacing:-.03em}
.counts span{display:block;color:var(--muted);font-size:.68rem;text-transform:uppercase;letter-spacing:.09em;margin-top:.25rem}
.verdict{border:1px solid var(--line);border-left:3px solid var(--abs);background:var(--panel);border-radius:.3rem;
padding:1rem 1.15rem;margin:0 0 1.6rem}.verdict.bad{border-left-color:var(--bad)}.verdict.warn{border-left-color:var(--warn)}
.verdict.ok{border-left-color:var(--ok)}
.verdict b{display:block;font:600 1.25rem/1.2 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:-.02em;
margin-bottom:.35rem}.verdict p{margin:0;font-size:.92rem;color:var(--fg2);max-width:72ch}
.tag{font:.66rem/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;text-transform:uppercase;letter-spacing:.06em;
padding:.1rem .4rem;border:1px solid var(--line);border-radius:.2rem;color:var(--abs);background:var(--absbg);
white-space:nowrap}.tag.ok{color:var(--ok);border-color:var(--ok);background:var(--okbg)}
.tag.warn{color:var(--warn);border-color:var(--warn);background:var(--warnbg)}
.tag.bad{color:var(--bad);border-color:var(--bad);background:var(--badbg)}.tag.abs{border-style:dashed}
.wrap{overflow-x:auto;border:1px solid var(--line);border-radius:.3rem;margin:1rem 0}
table{border-collapse:collapse;width:100%;min-width:46rem;font-size:.86rem}
th{text-align:left;font:500 .66rem/1.6 ui-monospace,SFMono-Regular,Menlo,monospace;text-transform:uppercase;
letter-spacing:.09em;color:var(--muted);padding:.6rem .75rem;background:var(--panel);border-bottom:1px solid var(--line);
white-space:nowrap}td{padding:.5rem .75rem;border-bottom:1px solid var(--soft);vertical-align:top}
tr:last-child td{border-bottom:none}
td.n{font:400 .86rem/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;font-variant-numeric:tabular-nums;text-align:right;
white-space:nowrap}td.id{font:500 .86rem/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;white-space:nowrap}
td.t{font:400 .8rem/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;white-space:nowrap;color:var(--fg2)}
.rule{border:1px solid var(--line);border-left:3px solid var(--acc);background:var(--panel);border-radius:.3rem;
padding:.85rem 1rem;margin:.9rem 0;max-width:74ch}
.rule h4{margin:0 0 .35rem;font:600 .9rem/1.4 ui-monospace,SFMono-Regular,Menlo,monospace}
.rule p{margin:0 0 .45rem;font-size:.87rem}.rule p:last-child{margin-bottom:0}.rule .q{color:var(--muted)}
code{font:12.5px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--bg);border:1px solid var(--soft);
border-radius:.2rem;padding:.04rem .25rem}
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--line);color:var(--muted);
font-size:.82rem}footer li{margin-bottom:.35rem;max-width:80ch}

.live{background:#123d2a;color:#8ff0c0;padding:.5rem .9rem;border-radius:6px;
 margin:0 0 1rem;font-size:.85rem;letter-spacing:.02em}
.ro{background:#2a2a2e;color:#b9b9c2;padding:.5rem .9rem;border-radius:6px;
 margin:0 0 1rem;font-size:.85rem;letter-spacing:.02em}
p.note{font-size:.86rem;color:#b9b9c2;background:#232327;border-left:3px solid #4a4a55;
 padding:.6rem .9rem;border-radius:0 6px 6px 0}
td.sw{white-space:nowrap}
.btn{margin-left:.5rem;border:1px solid #55555f;background:#2c2c33;color:#e6e6ea;
 border-radius:5px;padding:.2rem .55rem;font:inherit;font-size:.78rem;cursor:pointer}
.btn:hover{background:#3a3a43}
.btn:disabled{opacity:.45;cursor:default}
.btn.arm{border-color:#7a5d1f;color:#f3d68b}
.btn.off{border-color:#6a2f2f;color:#f0a9a9}
.say{margin:.6rem 0 0;font-size:.85rem;min-height:1.2rem;white-space:pre-wrap}
.say.ok{color:#8ff0c0}
.say.bad{color:#f0a9a9}
"""
