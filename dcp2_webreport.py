
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import sys, json, os
from dataclasses import dataclass
from typing import Dict, List, Tuple, Iterable, Set, Optional

Coord = Tuple[int, int]
WEEKDAYS = ["SUN","MON","TUE","WED","THU","FRI","SAT"]
W2IDX = {w:i for i,w in enumerate(WEEKDAYS)}
BOARD_W, BOARD_H = 7, 8
FIXED_HOLES: Set[Coord] = {(6,0),(6,1),(0,7),(1,7),(2,7),(3,7)}

def month_cell(month: int) -> Coord:
    if 1<=month<=6: return (month-1,0)
    return (month-7,1)

def day_cell(day: int) -> Coord:
    if 1<=day<=7:   return (day-1,2)
    if 8<=day<=14:  return (day-8,3)
    if 15<=day<=21: return (day-15,4)
    if 22<=day<=28: return (day-22,5)
    return (day-29,6)

def weekday_cell(widx: int) -> Coord:
    if 0<=widx<=3: return (3+widx,6)
    return (widx,7)

@dataclass(frozen=True)
class PieceDef:
    name: str
    cells: Set[Coord]
    chiral: bool

def normalize(cells: Iterable[Coord]):
    xs=[c[0] for c in cells]; ys=[c[1] for c in cells]
    minx, miny = min(xs), min(ys)
    return tuple(sorted((x-minx,y-miny) for (x,y) in cells))

def rot90(cells: Iterable[Coord]): return normalize([(-y,x) for (x,y) in cells])
def mirx(cells: Iterable[Coord]): return normalize([(-x,y) for (x,y) in cells])
def all_rots(cells: Iterable[Coord]):
    s=normalize(cells); rots={s}
    for _ in range(3):
        s=rot90(s); rots.add(s)
    return sorted(rots)

BASE_PIECES: List[PieceDef] = [
    PieceDef("I4", {(0,0),(1,0),(2,0),(3,0)}, chiral=False),
    PieceDef("L4", {(0,0),(0,1),(0,2),(1,2)}, chiral=True),
    PieceDef("S4", {(1,0),(2,0),(0,1),(1,1)}, chiral=True),
    PieceDef("I5", {(0,0),(1,0),(2,0),(3,0),(4,0)}, chiral=False),
    PieceDef("L5", {(0,0),(0,1),(0,2),(0,3),(1,3)}, chiral=True),
    PieceDef("P" , {(0,0),(1,0),(0,1),(1,1),(0,2)}, chiral=True),
    PieceDef("T" , {(0,0),(1,0),(2,0),(1,1),(1,2)}, chiral=False),
    PieceDef("U" , {(0,0),(0,1),(1,1),(2,0),(2,1)}, chiral=False),
    PieceDef("V" , {(0,0),(0,1),(0,2),(1,2),(2,2)}, chiral=False),
    PieceDef("Z" , {(0,0),(1,0),(1,1),(1,2),(2,2)}, chiral=True),
]

def gen_orients(side: str):
    out={}
    for p in BASE_PIECES:
        front=[(shape, False) for shape in all_rots(p.cells)]
        if side=="FRONT":
            out[p.name]=front
        elif side=="BACK":
            out[p.name]=[(shape, True) for shape in all_rots(mirx(p.cells))] if p.chiral else front
        else:
            if p.chiral:
                both=set(front+[(shape,True) for shape in all_rots(mirx(p.cells))])
                out[p.name]=sorted(both)
            else:
                out[p.name]=front
    return out

@dataclass
class Placed:
    name:str; cells:List[Coord]; mirror:bool

class Board:
    __slots__=("occ","meta","free_count")
    def __init__(self):
        self.occ=[[-2]*BOARD_W for _ in range(BOARD_H)]
        for (x,y) in FIXED_HOLES: self.occ[y][x]=-1
        self.meta: List[Placed]=[]
        self.free_count = BOARD_W*BOARD_H - len(FIXED_HOLES)
    def block(self, cell:Coord):
        x,y=cell
        if self.occ[y][x] != -2: raise ValueError("block on non-empty")
        self.occ[y][x]=-1; self.free_count-=1
    def inside(self,x:int,y:int)->bool: return 0<=x<BOARD_W and 0<=y<BOARD_H
    def next_empty(self)->Optional[Coord]:
        for y in range(BOARD_H):
            for x in range(BOARD_W):
                if self.occ[y][x]==-2: return (x,y)
        return None
    def region_prune(self)->bool:
        seen=[[False]*BOARD_W for _ in range(BOARD_H)]
        for y in range(BOARD_H):
            for x in range(BOARD_W):
                if self.occ[y][x]==-2 and not seen[y][x]:
                    q=[(x,y)]; seen[y][x]=True; sz=0
                    while q:
                        cx,cy=q.pop(); sz+=1
                        for nx,ny in ((cx+1,cy),(cx-1,cy),(cx,cy+1),(cx,cy-1)):
                            if self.inside(nx,ny) and not seen[ny][nx] and self.occ[ny][nx]==-2:
                                seen[ny][nx]=True; q.append((nx,ny))
                    if sz<4: return True
        return False
    def place(self, cells:List[Coord], mirror:bool, name:str):
        idx=len(self.meta)+1
        for (x,y) in cells: self.occ[y][x]=idx
        self.meta.append(Placed(name,cells,mirror))
        self.free_count-=len(cells)
    def unplace(self):
        pl=self.meta.pop()
        for (x,y) in pl.cells: self.occ[y][x]=-2
        self.free_count+=len(pl.cells)

def try_place(board:Board, shape, anchor:Coord):
    tl=min(shape, key=lambda c:(c[1],c[0]))
    dx,dy=anchor[0]-tl[0], anchor[1]-tl[1]
    cells=[(dx+x,dy+y) for (x,y) in shape]
    for (x,y) in cells:
        if not board.inside(x,y) or board.occ[y][x]!=-2: return None
    return cells

def solve_date(m:int,d:int,w:int,side:str, sample_limit:int=20):
    b=Board()
    b.block(month_cell(m)); b.block(day_cell(d)); b.block(weekday_cell(w))
    assert b.free_count==47
    orients=gen_orients(side); names=[p.name for p in BASE_PIECES]
    cnt=[0]; samples=[]
    def dfs():
        nxt=b.next_empty()
        if nxt is None:
            cnt[0]+=1
            if len(samples)<sample_limit:
                samples.append({"placements":[{"name":pl.name,"mirror":pl.mirror,"cells":pl.cells} for pl in b.meta]})
            return
        if b.region_prune(): return
        for name in names:
            if any(pl.name==name for pl in b.meta): continue
            for shape,mir in orients[name]:
                cells=try_place(b,shape,nxt)
                if cells is None: continue
                b.place(cells,mir,name)
                dfs()
                b.unplace()
    dfs()
    return cnt[0], samples

HTML_HEAD = """<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Daily Calendar Puzzle Report</title>
<style>
:root{--cell:28px;--gap:2px;--fz:12px;--frost:#A7D3FF;--smooth:#1E5BFF;--both:#7FB0FF;--hole:#ffffff;--blocked:#efefef;--grid:#ddd;--txt:#111}
body{font-family:ui-sans-serif,system-ui,"Noto Sans TC","Segoe UI",Arial;color:var(--txt)}
h1{font-size:20px;margin:12px 0 8px}
.grid{display:grid;grid-template-columns:repeat(7,var(--cell));grid-auto-rows:var(--cell);gap:var(--gap)}
.cell{width:var(--cell);height:var(--cell);display:flex;align-items:center;justify-content:center;font-size:var(--fz);border:1px solid var(--grid);box-sizing:border-box}
.blocked{background:var(--blocked)}.hole{background:var(--hole)}.pieceF{background:var(--frost);color:#fff;font-weight:700}.pieceB{background:var(--smooth);color:#fff;font-weight:700}.pieceO{background:var(--both);color:#fff;font-weight:700}
.legend{display:flex;gap:10px;margin:6px 0 10px;align-items:center}.tag{display:inline-flex;align-items:center;gap:6px}.swatch{width:14px;height:14px;border-radius:3px;display:inline-block}
.modeBox{border:1px solid #ccc;border-radius:8px;padding:10px;margin:12px 0}.kv{color:#555;font-size:13px}.btn{padding:6px 10px;font-size:13px;border:1px solid #888;border-radius:6px;background:#fafafa;cursor:pointer}.btn:hover{background:#f0f0f0}
pre{background:#fbfbfb;border:1px dashed #bbb;padding:8px;border-radius:6px;white-space:pre;overflow:auto}.row{display:flex;gap:14px;align-items:flex-start;flex-wrap:wrap}.card{border:1px solid #e0e0e0;border-radius:8px;padding:8px}.small{font-size:12px;color:#666}
</style>"""

HTML_SCAFFOLD = """
<body>
<h1>Daily Calendar Puzzle — __DATE_TITLE__</h1>
<div class="legend">
  <span class="tag"><i class="swatch" style="background:var(--frost)"></i>Frosted (淺藍)</span>
  <span class="tag"><i class="swatch" style="background:var(--smooth)"></i>Smooth (深藍)</span>
  <span class="tag"><i class="swatch" style="background:var(--both)"></i>Both（front/back 依實際姿態著色）</span>
</div>
__MODES_HTML__
<script>
const DATA = __JSON__;
function byId(id){return document.getElementById(id);}
function renderBoard(containerId, payload, modeTag, dateMeta){
  const holes = new Set([JSON.stringify([6,0]),JSON.stringify([6,1]),JSON.stringify([0,7]),JSON.stringify([1,7]),JSON.stringify([2,7]),JSON.stringify([3,7])]);
  const blocked = new Set([JSON.stringify(dateMeta.monthCell),JSON.stringify(dateMeta.dayCell),JSON.stringify(dateMeta.weekCell)]);
  const grid=[];
  for(let y=0;y<8;y++){ const row=[]; for(let x=0;x<7;x++){ const k=JSON.stringify([x,y]);
    if(holes.has(k)||blocked.has(k)) row.push({cls:"hole",txt:""}); else row.push({cls:"blocked",txt:""});
  } grid.push(row);}
  payload.placements.forEach(pl=>{
    const cls = (modeTag==="FROSTED")?"pieceF":(modeTag==="SMOOTH"?"pieceB":(pl.mirror?"pieceB":"pieceF"));
    pl.cells.forEach(([x,y])=>{ grid[y][x]={cls:cls, txt:pl.name}; });
  });
  const root=byId(containerId); root.innerHTML=""; const div=document.createElement("div"); div.className="grid";
  for(let y=0;y<8;y++){ for(let x=0;x<7;x++){ const c=document.createElement("div"); const cell=grid[y][x]; c.className="cell "+cell.cls; c.textContent=cell.txt; div.appendChild(c);} }
  root.appendChild(div);
}
function onCopy(textId){ const el=byId(textId); el.select(); el.setSelectionRange(0,99999); document.execCommand("copy"); }
function setupMode(modeTag){
  const data=DATA[modeTag], dateMeta=DATA["_dateMeta"];
  byId("cnt_"+modeTag).textContent=data.count;
  const samples=data.samples;
  if(samples.length===0){ byId("grid_"+modeTag).innerHTML="<div class='small'>（無範例）</div>"; return; }
  let idx=0;
  function refresh(){ byId("cap_"+modeTag).textContent="範例 #"+(idx+1)+" / "+samples.length; renderBoard("grid_"+modeTag, samples[idx], modeTag, dateMeta);
    byId("txt_"+modeTag).value = sampleToText(samples[idx], idx); }
  function sampleToText(s, idx){
    const occ=Array.from({length:8},()=>Array(7).fill("  "));
    const holes=new Set(["[6,0]","[6,1]","[0,7]","[1,7]","[2,7]","[3,7]"]);
    const bm={ m:"["+dateMeta.monthCell.join(",")+"]", d:"["+dateMeta.dayCell.join(",")+"]", w:"["+dateMeta.weekCell.join(",")+"]" };
    for(let y=0;y<8;y++){ for(let x=0;x<7;x++){ const k="["+x+","+y+"]"; if(holes.has(k)||k===bm.m||k===bm.d||k===bm.w){ occ[y][x]=".."; } } }
    s.placements.forEach(pl=>{ pl.cells.forEach(([x,y])=>{ occ[y][x]=(pl.name+"  ").slice(0,2); }); });
    const rows=occ.map(r=>r.join(" "));
    return ["Date: "+dateMeta.title, "Mode: "+modeTag, "Index: "+(idx+1)+" / "+samples.length, rows.join("\\n")].join("\\n");
  }
  byId("prev_"+modeTag).onclick=()=>{ idx=(idx-1+samples.length)%samples.length; refresh(); };
  byId("next_"+modeTag).onclick=()=>{ idx=(idx+1)%samples.length; refresh(); };
  byId("copy_"+modeTag).onclick=()=>onCopy("txt_"+modeTag);
  refresh();
}
["FROSTED","SMOOTH","BOTH"].forEach(setupMode);
</script>
</body></html>
"""

MODE_SECTION_TEMPLATE = """
<div class="modeBox" id="box___TAG__">
  <div class="row" style="justify-content:space-between;width:100%">
    <div><b>__TAG__</b> <span class="kv">解數量：</span><b id="cnt___TAG__">–</b></div>
    <div class="small" id="cap___TAG__"></div>
  </div>
  <div class="row">
    <div class="card" id="grid___TAG__"></div>
    <div class="card" style="min-width:380px;max-width:520px;">
      <div style="display:flex; gap:8px; margin-bottom:6px;">
        <button class="btn" id="prev___TAG__">上一個</button>
        <button class="btn" id="next___TAG__">下一個</button>
        <button class="btn" id="copy___TAG__">複製剪貼</button>
      </div>
      <textarea id="txt___TAG__" rows="16" style="width:100%; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace;"></textarea>
    </div>
  </div>
</div>
"""

def solve_and_build(date_str: str, sample_limit_per_mode=12, out_html=None):
    mm, dd, ww_token = date_str.upper().split("/")
    mm, dd = int(mm), int(dd)
    ww = W2IDX[ww_token]
    modes=[("FROSTED","FRONT"),("SMOOTH","BACK"),("BOTH","BOTH")]
    data={}
    for tag,side in modes:
        cnt,samples = solve_date(mm,dd,ww,side, sample_limit=sample_limit_per_mode)
        data[tag] = {"count": cnt, "samples": samples}
    data["_dateMeta"] = {"title": f"{mm:02d}/{dd:02d}/{WEEKDAYS[ww]}", "monthCell": list(month_cell(mm)), "dayCell": list(day_cell(dd)), "weekCell": list(weekday_cell(ww))}
    sections=[]
    for tag,_ in modes:
        sections.append(MODE_SECTION_TEMPLATE.replace("__TAG__", tag))
    html = HTML_HEAD + HTML_SCAFFOLD.replace("__DATE_TITLE__", data["_dateMeta"]["title"]) \
                                     .replace("__MODES_HTML__", "\n".join(sections)) \
                                     .replace("__JSON__", json.dumps(data))
    if out_html is None:
        safe = date_str.replace("/","-")
        out_html = os.path.abspath(f"dcp_report_{safe}.html")
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    return out_html

if __name__ == "__main__":
    date_str = sys.argv[1] if len(sys.argv)>1 else "01/01/WED"
    out = solve_and_build(date_str, sample_limit_per_mode=12, out_html=os.path.abspath(f"dcp_report_{date_str.replace('/','-')}.html"))
    print(out)
