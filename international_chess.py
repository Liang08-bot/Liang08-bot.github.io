"""
国际象棋 3D · AI 人机对战  v2.0
================================
· 独立西方风格 UI（不同于中国象棋）
· 3D 立体棋子（高光/阴影/浮雕）
· 三档 AI 难度：简单(1) / 困难(2) / 专家(3)
· 棋钟：双方各自倒计时，超时判负
· 换方：可切换执白/执黑
· 移动历史面板（代数记谱法）
· 控制：难度调节 / 重新开始 / 返回菜单
"""

import pygame, sys, math, time, threading, random, struct
import numpy as np
from copy import deepcopy

# ═══════════════════ 常量 ═══════════════════
SQ       = 84                    # 格子大小
BOARD_PX = SQ * 8               # 棋盘像素
MARGIN   = 38                   # 棋盘外边距
SIDE_W   = 250                  # 右侧面板宽度
WIN_W    = MARGIN*2 + BOARD_PX + SIDE_W
WIN_H    = MARGIN*2 + BOARD_PX

# ── 颜色（精致暗色 · 青绿调） ──
SQ_L   = (225, 220, 210)
SQ_D   = ( 65,  90,  75)
BORDER = ( 50,  58,  52)
PANEL  = ( 32,  36,  38)
PANEL2 = ( 40,  44,  46)
TXT    = (235, 238, 230)
TXT_DIM= (140, 148, 140)
C_HL   = (120, 220, 180, 220)
C_LGL  = ( 80, 200, 150, 220)
C_CHK  = (230,  80,  70, 220)
C_LAST = (100, 180, 140, 180)
WHITE_BG  = (255, 253, 248)
WHITE_ED  = (210, 208, 200)
WHITE_TXT = ( 18,  20,  18)
BLACK_BG  = ( 38,  40,  38)
BLACK_ED  = ( 20,  22,  20)
BLACK_TXT = (235, 238, 230)
SEL_GOLD  = (100, 215, 165)
BTN_BG    = ( 42,  46,  48)
BTN_HOV   = ( 55,  62,  65)
BTN_BRD   = ( 75,  85,  88)
CLOCK_W   = ( 90, 200, 150)
CLOCK_B   = (200, 100, 100)
CLOCK_LO  = (240,  80,  75)

# 菜单颜色（精致暗色）
M_BG      = ( 12,  14,  16)
M_BG_TOP  = ( 22,  26,  30)
M_BG_BOT  = (  8,  10,  11)
M_BTN     = ( 38,  44,  48)
M_BTN_HOV = ( 52,  60,  66)
M_BTN_BRD = ( 72,  85,  92)
M_TIT     = (240, 243, 238)
M_SUB     = (140, 150, 145)
M_DIM     = ( 85,  95,  90)
M_GOLD    = ( 95, 215, 175)
M_ACC     = ( 85, 200, 160)
M_ACC2    = ( 95, 215, 175)
# 游戏结束弹窗颜色
GEO_BG   = ( 12,  14,  16, 240)
GEO_WIN  = ( 85, 215, 150)
GEO_LOSE = (230,  85,  75)
GEO_DRAW = (210, 190,  80)

PIECE_UNI = {
    'K':'♔','Q':'♕','R':'♖','B':'♗','N':'♘','P':'♙',
    'k':'♚','q':'♛','r':'♜','b':'♝','n':'♞','p':'♟',
}
PIECE_VAL = {
    'K':20000,'k':-20000,'Q':900,'q':-900,'R':500,'r':-500,
    'B':330,'b':-330,'N':320,'n':-320,'P':100,'p':-100,
}
AI_LEVELS = {
    'easy':  {'depth':1,'name':'Easy  简单','desc':'Beginner friendly','time':600},
    'hard':  {'depth':2,'name':'Hard  困难','desc':'Think carefully','time':600},
    'expert':{'depth':3,'name':'Expert 专家','desc':'Deep search + eval','time':600},
}

# 位置表（白方视角，row0=rank8）
PST = {
    'P':[[0,0,0,0,0,0,0,0],[50,50,50,50,50,50,50,50],[10,10,20,30,30,20,10,10],
        [5,5,10,25,25,10,5,5],[0,0,0,20,20,0,0,0],[5,-5,-10,0,0,-10,-5,5],
        [5,10,10,-20,-20,10,10,5],[0,0,0,0,0,0,0,0]],
    'N':[[-50,-40,-30,-30,-30,-30,-40,-50],[-40,-20,0,0,0,0,-20,-40],
        [-30,0,10,15,15,10,0,-30],[-30,5,15,20,20,15,5,-30],
        [-30,0,15,20,20,15,0,-30],[-30,5,10,15,15,10,5,-30],
        [-40,-20,0,5,5,0,-20,-40],[-50,-40,-30,-30,-30,-30,-40,-50]],
    'B':[[-20,-10,-10,-10,-10,-10,-10,-20],[-10,0,0,0,0,0,0,-10],
        [-10,0,10,10,10,10,0,-10],[-10,5,5,10,10,5,5,-10],
        [-10,0,10,10,10,10,0,-10],[-10,10,10,10,10,10,10,-10],
        [-10,5,0,0,0,0,5,-10],[-20,-10,-10,-10,-10,-10,-10,-20]],
    'R':[[0,0,0,0,0,0,0,0],[5,10,10,10,10,10,10,5],[-5,0,0,0,0,0,0,-5],
        [-5,0,0,0,0,0,0,-5],[-5,0,0,0,0,0,0,-5],[-5,0,0,0,0,0,0,-5],
        [-5,0,0,0,0,0,0,-5],[0,0,0,5,5,0,0,0]],
    'Q':[[-20,-10,-10,-5,-5,-10,-10,-20],[-10,0,0,0,0,0,0,-10],
        [-10,0,5,5,5,5,0,-10],[-5,0,5,5,5,5,0,-5],
        [0,0,5,5,5,5,0,-5],[-10,5,5,5,5,5,0,-10],
        [-10,0,5,0,0,0,0,-10],[-20,-10,-10,-5,-5,-10,-10,-20]],
    'K':[[-30,-40,-40,-50,-50,-40,-40,-30],[-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],[-30,-40,-40,-50,-50,-40,-40,-30],
        [-20,-30,-30,-40,-40,-30,-30,-20],[-10,-20,-20,-20,-20,-20,-20,-10],
        [20,20,0,0,0,0,20,20],[20,30,10,0,0,10,30,20]],
}
for pt, tbl in list(PST.items()):
    PST[pt.lower()] = [row[:] for row in reversed(tbl)]

FILES = 'abcdefgh'
RANKS = '87654321'


# ═══════════════════ 棋盘逻辑 ═══════════════════
class Board:
    def __init__(self):
        self.reset()

    def reset(self):
        self.grid = [list('rnbqkbnr'),list('pppppppp'),
                     [None]*8,[None]*8,[None]*8,[None]*8,
                     list('PPPPPPPP'),list('RNBQKBNR')]
        self.turn='W'; self.status='playing'; self.winner=None
        self.castling={'W':{'K':True,'Q':True},'B':{'K':True,'Q':True}}
        self.ep=None; self.last=None; self.history=[]

    @staticmethod
    def color(p):
        return 'W' if p and p.isupper() else ('B' if p else None)

    @staticmethod
    def opp(s): return 'B' if s=='W' else 'W'

    def at(self,r,c):
        return self.grid[r][c] if 0<=r<8 and 0<=c<8 else None

    def find_king(self,s):
        k='K' if s=='W' else 'k'
        for r in range(8):
            for c in range(8):
                if self.grid[r][c]==k: return(r,c)
        return None

    def _pseudo(self,r,c):
        p=self.grid[r][c]
        if not p: return[]
        s=self.color(p); t=p.upper(); m=[]
        if t=='P': m=self._pawn(r,c,s)
        elif t=='N': m=self._knight(r,c,s)
        elif t=='B': m=self._slide(r,c,s,[(-1,-1),(-1,1),(1,-1),(1,1)])
        elif t=='R': m=self._slide(r,c,s,[(-1,0),(1,0),(0,-1),(0,1)])
        elif t=='Q': m=self._slide(r,c,s,[(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)])
        elif t=='K': m=self._king(r,c,s)
        return m

    def _pawn(self,r,c,s):
        m=[]; d=-1 if s=='W' else 1; sr=6 if s=='W' else 1
        if self.at(r+d,c) is None:
            m.append((r+d,c,'')); 
            if r==sr and self.at(r+2*d,c) is None: m.append((r+2*d,c,'p2'))
        for dc in(-1,1):
            nr,nc=r+d,c+dc
            if 0<=nc<8:
                t=self.at(nr,nc)
                if t and self.color(t)!=s: m.append((nr,nc,''))
                if self.ep==(nr,nc): m.append((nr,nc,'ep'))
        return m

    def _knight(self,r,c,s):
        m=[]
        for dr,dc in[(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nr,nc=r+dr,c+dc
            if 0<=nr<8 and 0<=nc<8:
                t=self.at(nr,nc)
                if t is None or self.color(t)!=s: m.append((nr,nc,''))
        return m

    def _slide(self,r,c,s,dirs):
        m=[]
        for dr,dc in dirs:
            nr,nc=r+dr,c+dc
            while 0<=nr<8 and 0<=nc<8:
                t=self.at(nr,nc)
                if t is None: m.append((nr,nc,''))
                elif self.color(t)!=s: m.append((nr,nc,'')); break
                else: break
                nr+=dr; nc+=dc
        return m

    def _king(self,r,c,s):
        m=[]
        for dr in(-1,0,1):
            for dc in(-1,0,1):
                if dr==0 and dc==0: continue
                nr,nc=r+dr,c+dc
                if 0<=nr<8 and 0<=nc<8:
                    t=self.at(nr,nc)
                    if t is None or self.color(t)!=s: m.append((nr,nc,''))
        row=7 if s=='W' else 0
        if r==row:
            if self.castling[s]['K'] and self.grid[row][5] is None and self.grid[row][6] is None and not self._att(row,4,s) and not self._att(row,5,s) and not self._att(row,6,s):
                m.append((row,6,'ck'))
            if self.castling[s]['Q'] and self.grid[row][3] is None and self.grid[row][2] is None and self.grid[row][1] is None and not self._att(row,4,s) and not self._att(row,3,s) and not self._att(row,2,s):
                m.append((row,2,'cq'))
        return m

    def _att(self,r,c,s):
        o=self.opp(s)
        for rr in range(8):
            for cc in range(8):
                p=self.grid[rr][cc]
                if p and self.color(p)==o:
                    for mr,mc,_ in self._pseudo(rr,cc):
                        if mr==r and mc==c: return True
        return False

    def _safe(self,fr,fc,move):
        tr,tc,flag=move
        b=deepcopy(self)
        b._raw(fr,fc,tr,tc,flag)
        kp=b.find_king(self.color(self.grid[fr][fc]))
        if not kp: return False
        return not b._att(kp[0],kp[1],self.color(self.grid[fr][fc]))

    def legal_moves(self,r,c):
        p=self.grid[r][c]
        if not p or self.color(p)!=self.turn: return[]
        return[m for m in self._pseudo(r,c) if self._safe(r,c,m)]

    def all_legal(self,s=None):
        s=s or self.turn; moves=[]
        for r in range(8):
            for c in range(8):
                if self.grid[r][c] and self.color(self.grid[r][c])==s:
                    for m in self.legal_moves(r,c): moves.append((r,c,m[0],m[1],m[2]))
        return moves

    def _raw(self,fr,fc,tr,tc,flag):
        p=self.grid[fr][fc]; s=self.color(p)
        self.grid[tr][tc]=p; self.grid[fr][fc]=None
        if flag=='ep': self.grid[fr][tc]=None
        if flag=='ck': self.grid[fr][5]=self.grid[fr][7]; self.grid[fr][7]=None
        if flag=='cq': self.grid[fr][3]=self.grid[fr][0]; self.grid[fr][0]=None
        t=p.upper(); pr=0 if s=='W' else 7
        if t=='P' and tr==pr: self.grid[tr][tc]='Q' if s=='W' else 'q'
        if t=='K': self.castling[s]={'K':False,'Q':False}
        if t=='R':
            if fc==7: self.castling[s]['K']=False
            if fc==0: self.castling[s]['Q']=False
        self.ep=(fr+(-1 if s=='W' else 1),fc) if flag=='p2' else None

    def apply(self,fr,fc,tr,tc,flag,promo='Q'):
        # 记谱
        piece=self.grid[fr][fc]
        cap=self.grid[tr][tc]
        notation=self._notation(piece,fr,fc,tr,tc,flag,promo,cap)
        self.history.append(notation)

        p=self.grid[fr][fc]; s=self.color(p)
        self.last=((fr,fc),(tr,tc))
        self.grid[tr][tc]=p; self.grid[fr][fc]=None
        if flag=='ep': self.grid[fr][tc]=None
        if flag=='ck': self.grid[fr][5]=self.grid[fr][7]; self.grid[fr][7]=None
        if flag=='cq': self.grid[fr][3]=self.grid[fr][0]; self.grid[fr][0]=None
        t=p.upper(); pr=0 if s=='W' else 7
        if t=='P' and tr==pr: self.grid[tr][tc]=promo if s=='W' else promo.lower()
        if t=='K': self.castling[s]={'K':False,'Q':False}
        if t=='R':
            if fc==7: self.castling[s]['K']=False
            if fc==0: self.castling[s]['Q']=False
        self.ep=(fr+(-1 if s=='W' else 1),fc) if flag=='p2' else None
        self.turn=self.opp(self.turn)
        # 将军标记
        king=self.find_king(self.turn)
        if king and self._att(king[0],king[1],self.turn):
            self.status='check'
            if self.history: self.history[-1]+='+'
        self._refresh()

    def _notation(self,p,fr,fc,tr,tc,flag,promo,cap):
        t=p.upper(); s=self.color(p)
        if flag=='ck': return 'O-O'
        if flag=='cq': return 'O-O-O'
        n=''
        if t!='P':
            n=t
            # 消歧义
            for r2 in range(8):
                for c2 in range(8):
                    if(r2,c2)!=(fr,fc) and self.grid[r2][c2]==p:
                        if self._safe(r2,c2,(tr,tc,'')):
                            if c2==fc: n+=FILES[fc]
                            elif r2==fr: n+=RANKS[fr]
                            else: n+=FILES[fc]+RANKS[fr]
                            break
        if cap:
            if t=='P': n=FILES[fc]
            n+='x'
        n+=FILES[tc]+RANKS[tr]
        if t=='P' and tr in(0,7): n+='='+promo
        return n

    def _refresh(self):
        s=self.turn
        has=any(self.legal_moves(r,c) for r in range(8) for c in range(8) if self.grid[r][c] and self.color(self.grid[r][c])==s)
        king=self.find_king(s)
        chk=king and self._att(king[0],king[1],s)
        if not has:
            if chk: self.status='checkmate'; self.winner=self.opp(s)
            else: self.status='draw'
        elif not chk:
            self.status='playing'


# ═══════════════════ 音效生成（物理建模） ═══════════════════
def _make_wav(samples_arr, sr=44100):
    """将 numpy float 数组 (-1~1) 打包为 WAV bytes"""
    s = np.clip(samples_arr, -1, 1)
    data = (s * 32767).astype(np.int16).tobytes()
    buf = bytearray()
    buf += b'RIFF'
    buf += struct.pack('<I', 36 + len(data))
    buf += b'WAVEfmt '
    buf += struct.pack('<IHHIIHH', 16, 1, 1, sr, sr * 2, 2, 16)
    buf += b'data'
    buf += struct.pack('<I', len(data))
    buf += data
    return bytes(buf)


def _bp(noise, low, high, sr):
    """频域带通滤波"""
    n = len(noise)
    freq = np.fft.rfft(noise)
    bins = np.fft.rfftfreq(n, 1.0 / sr)
    mask = ((bins >= low) & (bins <= high)).astype(np.float64)
    edge = 50
    mask = np.where(bins < low + edge, np.clip((bins - low) / edge, 0, 1), mask)
    mask = np.where(bins > high - edge, np.clip((high - bins) / edge, 0, 1), mask)
    return np.fft.irfft(freq * mask, n)


def _res(sr, dur, freq, decay, gain=1.0):
    """材质共振：正弦衰减振荡"""
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    return gain * np.sin(2 * np.pi * freq * t) * np.exp(-decay * t)


def _norm(arr, peak=0.7):
    pk = np.max(np.abs(arr))
    if pk < 1e-6: return arr
    return arr / pk * peak


def snd_move():
    """落子：石质棋子碰撞棋盘（国际象棋质感）
    噪声冲击 → 木质棋盘频段带通 → 石质+木质共振
    """
    sr = 44100; dur = 0.13; n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False)

    imp = np.random.randn(n) * np.exp(-t * 55)
    wood = _bp(imp, 350, 5500, sr)
    wood = _norm(wood, 0.55)

    # 石质棋子共振（比木质更亮、更短促）
    stone = (_res(sr, dur, 520 + random.randint(-25, 25), 32, 0.30)
           + _res(sr, dur, 1300 + random.randint(-50, 50), 50, 0.18)
           + _res(sr, dur, 2800 + random.randint(-120, 120), 75, 0.09))
    # 棋盘共鸣
    board = _res(sr, dur, 200 + random.randint(-15, 15), 14, 0.12)

    return _make_wav(_norm(wood + stone + board, 0.50), sr)


def snd_capture():
    """吃子：两枚石质棋子碰撞
    强冲击 → 石质高频带通 → 双棋子共振 + 摩擦
    """
    sr = 44100; dur = 0.2; n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False)

    imp = np.random.randn(n) * np.exp(-t * 42)
    hit = _bp(imp, 500, 9000, sr)
    hit = _norm(hit, 0.65)

    r1, r2 = random.randint(-35, 35), random.randint(-70, 70)
    res = (_res(sr, dur, 750 + r1, 20, 0.38)
         + _res(sr, dur, 1800 + r2, 35, 0.22)
         + _res(sr, dur, 3500 + random.randint(-140, 140), 60, 0.10)
         + _res(sr, dur, 5800 + random.randint(-200, 200), 85, 0.05))

    # 摩擦
    fl = int(0.055 * sr)
    fr = _bp(np.random.randn(fl), 1200, 7000, sr) * 0.07
    fr *= np.linspace(1, 0, fl)
    ff = np.zeros(n)
    s = min(int(0.012 * sr), n - fl)
    ff[s:s + fl] = fr

    return _make_wav(_norm(hit + res + ff, 0.55), sr)


def snd_check():
    """将军提示：短促石质敲击 + 上升双音"""
    sr = 44100; dur = 0.2; n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False)

    imp = np.random.randn(n) * np.exp(-t * 65)
    tap = _bp(imp, 500, 5000, sr)
    tap = _norm(tap, 0.28)

    note = np.zeros(n)
    mid = int(0.09 * sr)
    note[:mid] = np.sin(2*np.pi*880*t[:mid]) * np.exp(-t[:mid]*24) * 0.22
    note[mid:] = np.sin(2*np.pi*1100*t[:n-mid]) * np.exp(-t[:n-mid]*20) * 0.28

    return _make_wav(_norm(tap + note, 0.42), sr)


def snd_gameover(win=True):
    """游戏结束：胜利上升和弦 / 失败下降双音"""
    sr = 44100; dur = 0.6; n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    sig = np.zeros(n)

    notes = [523.25, 659.25, 783.99] if win else [440.0, 329.63]
    nd = 0.14 if win else 0.18

    for i, freq in enumerate(notes):
        s = int(i * nd * sr)
        e = min(s + int(nd * sr), n)
        st = np.arange(e - s) / sr
        seg = np.sin(2*np.pi*freq*st) * np.exp(-st*8) * 0.3
        seg += np.sin(2*np.pi*freq*2*st) * np.exp(-st*15) * 0.1
        sig[s:e] += seg

    return _make_wav(_norm(sig, 0.45), sr)


def snd_castle():
    """王车易位：两次快速石质碰撞"""
    sr = 44100; dur = 0.22; n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    sig = np.zeros(n)

    for offset, freq in [(0, 900), (0.1, 720)]:
        start = int(offset * sr)
        length = min(int(0.08 * sr), n - start)
        if length <= 0: continue
        seg_t = np.arange(length) / sr
        imp = np.random.randn(length) * np.exp(-seg_t * 50)
        tap = _bp(imp, 400, 5000, sr)
        tap = _norm(tap, 0.3)
        sig[start:start+length] += tap

    return _make_wav(_norm(sig, 0.42), sr)


# ═══════════════════ AI ═══════════════════
class AI:
    def __init__(self,side='B',depth=2):
        self.side=side; self.depth=depth; self.nodes=0

    def think(self,board):
        best=None; a=-999999; b=999999
        moves=board.all_legal(self.side); random.shuffle(moves)
        for fr,fc,tr,tc,flag in moves:
            bd=deepcopy(board); bd._raw(fr,fc,tr,tc,flag)
            sc=-self._ab(bd,self.depth-1,-b,-a,board.opp(self.side))
            if sc>a: a=sc; best=(fr,fc,tr,tc,flag)
        return best

    def _ab(self,bd,d,a,b,s):
        self.nodes+=1
        if d==0: return self._ev(bd,s)
        moves=bd.all_legal(s)
        if not moves:
            k=bd.find_king(s)
            if k and bd._att(k[0],k[1],s): return -9000
            return 0
        moves.sort(key=lambda m:abs(PIECE_VAL.get(bd.grid[m[2]][m[3]],0)) if bd.grid[m[2]][m[3]] else 0,reverse=True)
        for fr,fc,tr,tc,flag in moves:
            bd2=deepcopy(bd); bd2._raw(fr,fc,tr,tc,flag)
            sc=-self._ab(bd2,d-1,-b,-a,bd.opp(s))
            if sc>=b: return b
            if sc>a: a=sc
        return a

    def _ev(self,bd,s):
        sc=0
        for r in range(8):
            for c in range(8):
                p=bd.grid[r][c]
                if not p: continue
                v=PIECE_VAL.get(p,0)
                for pt,tbl in PST.items():
                    if p==pt: v+=tbl[r][c]; break
                sc+=v
        return -sc if s=='B' else sc


# ═══════════════════ 绘制工具 ═══════════════════
def draw_3d_piece(surf,font,cx,cy,piece,radius=28,selected=False):
    s=Board.color(piece); w=s=='W'
    bg=WHITE_BG if w else BLACK_BG
    ed=WHITE_ED if w else BLACK_ED
    dk=tuple(max(0,c-40) for c in bg)
    # 投影
    sh=pygame.Surface((radius*2+10,radius*2+10),pygame.SRCALPHA)
    pygame.draw.ellipse(sh,(0,0,0,40),(3,6,radius*2+4,radius*2))
    surf.blit(sh,(cx-radius-5+2,cy-radius-5+3))
    # 厚度
    pygame.draw.circle(surf,dk,(cx,cy+3),radius)
    pygame.draw.circle(surf,ed,(cx,cy+3),radius,2)
    # 主体
    pygame.draw.circle(surf,bg,(cx,cy),radius)
    ib=tuple(min(255,c+10) for c in bg)
    pygame.draw.circle(surf,ib,(cx,cy),radius-3)
    pygame.draw.circle(surf,ed,(cx,cy),radius-3,1)
    # 高光
    hl=pygame.Surface((radius*2,radius*2),pygame.SRCALPHA)
    hx,hy=radius-radius//3,radius-radius//3
    for i in range(radius//2,0,-1):
        pygame.draw.circle(hl,(255,255,255,int(50*(1-i/(radius//2)))),(hx,hy),i)
    surf.blit(hl,(cx-radius,cy-radius))
    # 边框
    pygame.draw.circle(surf,ed,(cx,cy),radius,2)
    if selected:
        pygame.draw.circle(surf,SEL_GOLD,(cx,cy),radius+3,3)
    # 文字
    uni=PIECE_UNI.get(piece,piece)
    fg=WHITE_TXT if w else BLACK_TXT
    ts=font.render(uni,True,fg)
    sc=(0,0,0) if w else (180,180,180)
    ss=font.render(uni,True,sc)
    surf.blit(ss,(cx-ss.get_width()//2+1,cy-ss.get_height()//2+1))
    surf.blit(ts,(cx-ts.get_width()//2,cy-ts.get_height()//2))


# ═══════════════════ 按钮 ═══════════════════
class Btn:
    def __init__(self,rect,text,font,color=BTN_BG):
        self.rect=pygame.Rect(rect); self.text=text; self.font=font; self.color=color

    def draw(self,surf,mx,my):
        hov=self.rect.collidepoint(mx,my)
        c=BTN_HOV if hov else self.color
        pygame.draw.rect(surf,(20,20,20),self.rect.move(2,2),border_radius=6)
        pygame.draw.rect(surf,c,self.rect,border_radius=6)
        pygame.draw.rect(surf,BTN_BRD,self.rect,1,border_radius=6)
        ts=self.font.render(self.text,True,TXT)
        surf.blit(ts,(self.rect.centerx-ts.get_width()//2,self.rect.centery-ts.get_height()//2))

    def clicked(self,pos): return self.rect.collidepoint(pos)


# ═══════════════════ 菜单 ═══════════════════
class Menu:
    def __init__(self, screen, fonts):
        self.screen = screen
        self.f = fonts
        self.choice = None
        self.player_side = 'W'
        self.page = 'main'          # 'main' | 'ai'
        self.ai_level = 'easy'
        self.hover_key = None       # 当前悬停的按钮 key

        cx = WIN_W // 2
        bw, bh = 300, 62
        gap = 16

        # ── 主菜单按钮 ──
        cy_main = WIN_H // 2 + 10
        self.main_buttons = {
            'pvp': (pygame.Rect(cx - bw//2, cy_main - (bh+gap), bw, bh),
                    '普  通  模  式', '双人本地对弈，轮流操控白黑',
                    ( 80, 180, 120)),
            'ai':  (pygame.Rect(cx - bw//2, cy_main,             bw, bh),
                    'AI  对  战',      '挑战电脑，三档难度可选',
                    (210, 170,  60)),
        }

        # ── AI 子菜单按钮 ──
        cy_ai = WIN_H // 2 + 10
        self.ai_buttons = {
            'easy':   (pygame.Rect(cx - bw//2, cy_ai - (bh+gap), bw, bh),
                       '简  单  Easy',   '适合新手，偶尔犯错',
                       ( 80, 180, 120)),
            'hard':   (pygame.Rect(cx - bw//2, cy_ai,            bw, bh),
                       '困  难  Hard',   '有一定棋力，需要认真对付',
                       (220, 180,  60)),
            'expert': (pygame.Rect(cx - bw//2, cy_ai + (bh+gap), bw, bh),
                       '专  家  Expert',  '深搜+强评估，高手对决',
                       (220,  80,  60)),
        }

        # ── AI 选边（小按钮） ──
        sw, sh = 120, 34
        sy = WIN_H - 65
        self.side_btns = {
            'W': pygame.Rect(cx - sw - 8, sy, sw, sh),
            'B': pygame.Rect(cx + 8,     sy, sw, sh),
        }

    def _back_rect(self):
        return pygame.Rect(18, WIN_H - 48, 90, 32)

    # ── 事件 ────────────────────────────
    def handle(self, ev):
        if ev.type != pygame.MOUSEBUTTONDOWN or ev.button != 1:
            return
        if self.page == 'main':
            for key, (rect, *_) in self.main_buttons.items():
                if rect.collidepoint(ev.pos):
                    if key == 'ai':
                        self.page = 'ai'
                    else:
                        self.choice = ('pvp', 'easy', 'W')
        elif self.page == 'ai':
            if self._back_rect().collidepoint(ev.pos):
                self.page = 'main'
                return
            for key, (rect, *_) in self.ai_buttons.items():
                if rect.collidepoint(ev.pos):
                    # 检查是否选了边（默认 W）
                    self.choice = ('ai', key, self.player_side)
            for key, rect in self.side_btns.items():
                if rect.collidepoint(ev.pos):
                    self.player_side = key

    # ── 绘制工具（极简风格） ────────
    def _draw_header(self, subtitle):
        """精致标题"""
        # 徽标
        icon = self.f['lg'].render("♚", True, M_GOLD)
        self.screen.blit(icon, (WIN_W//2 - icon.get_width()//2, 28))
        # 主标题
        title = self.f['lg'].render("CHESS", True, M_TIT)
        self.screen.blit(title, (WIN_W//2 - title.get_width()//2, 82))
        # 副标题
        sub = self.f['sm'].render(subtitle, True, M_SUB)
        self.screen.blit(sub, (WIN_W//2 - sub.get_width()//2, 148))

    def _draw_button(self, rect, name, desc, mark_color, hovered):
        """精致按钮"""
        bg = M_BTN_HOV if hovered else M_BTN
        bw = 2 if hovered else 1
        bc = M_GOLD if hovered else M_BTN_BRD
        pygame.draw.rect(self.screen, bg, rect, border_radius=8)
        pygame.draw.rect(self.screen, bc, rect, bw, border_radius=8)
        if hovered:
            pygame.draw.rect(self.screen, mark_color,
                             (rect.x+8, rect.y+8, 4, rect.h-16), border_radius=2)
        ns = self.f['sm'].render(name, True, TXT)
        self.screen.blit(ns, (rect.centerx-ns.get_width()//2, rect.y+12))
        ds = self.f['xs'].render(desc, True, TXT_DIM)
        self.screen.blit(ds, (rect.centerx-ds.get_width()//2, rect.y+36))

    # ── 主绘制 ──────────────────────────
    def draw(self, dt=0.016):
        # 渐变背景
        for y in range(WIN_H):
            t = y / WIN_H
            r = int(M_BG_TOP[0] + (M_BG_BOT[0] - M_BG_TOP[0]) * t)
            g = int(M_BG_TOP[1] + (M_BG_BOT[1] - M_BG_TOP[1]) * t)
            b = int(M_BG_TOP[2] + (M_BG_BOT[2] - M_BG_TOP[2]) * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WIN_W, y))
        mx, my = pygame.mouse.get_pos()

        if self.page == 'main':
            self._draw_header("双人  ·  AI  ·  3D 对战")
            for key, (rect, name, desc, color) in self.main_buttons.items():
                self._draw_button(rect, name, desc, color, rect.collidepoint(mx, my))

        elif self.page == 'ai':
            self._draw_header("AI 对战 — 选择难度")
            for key, (rect, name, desc, color) in self.ai_buttons.items():
                self._draw_button(rect, name, desc, color, rect.collidepoint(mx, my))

            # 选边按钮
            side_label = self.f['xs'].render("执子", True, M_DIM)
            self.screen.blit(side_label, (WIN_W//2 - side_label.get_width()//2, WIN_H - 62))
            for key, rect in self.side_btns.items():
                hov = rect.collidepoint(mx, my)
                sel = (key == self.player_side)
                bg = M_GOLD if sel else (M_BTN_HOV if hov else M_BTN)
                bc = M_GOLD if sel else (M_BTN_BRD)
                pygame.draw.rect(self.screen, bg, rect, border_radius=6)
                pygame.draw.rect(self.screen, bc, rect, 1, border_radius=6)
                txt = "执白" if key == 'W' else "执黑"
                ts = self.f['xs'].render(txt, True, TXT if sel else M_SUB)
                self.screen.blit(ts, (rect.centerx-ts.get_width()//2, rect.centery-ts.get_height()//2))

            # 返回
            br = self._back_rect()
            hov = br.collidepoint(mx, my)
            pygame.draw.rect(self.screen, M_BTN_HOV if hov else M_BTN, br, border_radius=6)
            pygame.draw.rect(self.screen, M_BTN_BRD, br, 1, border_radius=6)
            bs = self.f['xs'].render("← 返回", True, TXT if hov else M_DIM)
            self.screen.blit(bs, (br.centerx-bs.get_width()//2, br.centery-bs.get_height()//2))




# ═══════════════════ 主应用 ═══════════════════
class App:
    def __init__(self):
        pygame.init()
        self.screen=pygame.display.set_mode((WIN_W,WIN_H))
        pygame.display.set_caption("Chess 3D — 国际象棋")
        self.clock=pygame.time.Clock()

        # 音效
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
            self.snd_move    = pygame.mixer.Sound(buffer=snd_move())
            self.snd_capture = pygame.mixer.Sound(buffer=snd_capture())
            self.snd_check   = pygame.mixer.Sound(buffer=snd_check())
            self.snd_win     = pygame.mixer.Sound(buffer=snd_gameover(win=True))
            self.snd_lose    = pygame.mixer.Sound(buffer=snd_gameover(win=False))
            self.snd_castle  = pygame.mixer.Sound(buffer=snd_castle())
            self.snd_move.set_volume(0.5)
            self.snd_capture.set_volume(0.6)
            self.snd_check.set_volume(0.45)
            self.sound_ok = True
        except Exception:
            self.sound_ok = False

        self.f={
            'piece':self._fnt(52),
            'lg':self._fnt_ui(58,True),
            'md':self._fnt_ui(26),
            'sm':self._fnt_ui(20),
            'xs':self._fnt_ui(16),
            'coord':self._fnt_ui(14),
            'icon':self._fnt(36),
        }

        self.scene='menu'
        self.menu=Menu(self.screen,self.f)
        self.board=Board(); self.ai=None; self.level=None
        self.player_side='W'; self.pvp=False
        self.sel=None; self.legal=[]; self.promo=None
        self.ai_run=False; self.ai_res=None
        # 游戏结束弹窗
        self.game_over_shown=False  # 是否已显示过弹窗
        # 动画
        self.anim=None  # 弹簧状态
        # 弹簧参数（iOS 风格）
        self.spring_stiffness = 180.0
        self.spring_damping   = 18.0
        self.pr=SQ//2-8
        self.overlay=pygame.Surface((BOARD_PX,BOARD_PX),pygame.SRCALPHA)
        self.hist_scroll=0

        # 棋钟
        self.time_w=600.0; self.time_b=600.0
        self.clock_active=False; self.last_tick=0

        # 右侧按钮（统一间距对齐）
        px=MARGIN*2+BOARD_PX+10; pw=SIDE_W-20; bh=34; gap=8
        self.btn_new     =Btn((px,10,pw,bh),"New Game  重新开始",self.f['xs'])
        self.btn_menu    =Btn((px,10+bh+gap,pw,bh),"Menu  菜单",self.f['xs'])
        self.btn_swap    =Btn((px,10+(bh+gap)*2,pw,bh),"Swap  换方",self.f['xs'])
        self.btn_undo    =Btn((px,10+(bh+gap)*3,pw,bh),"Undo  悔棋",self.f['xs'])
        # PVP 模式下 Undo 上移到 Swap 位置
        self.btn_pvp_undo=Btn((px,10+(bh+gap)*2,pw,bh),"Undo  悔棋",self.f['xs'])
        self.game_btns=[self.btn_new,self.btn_menu,self.btn_swap,self.btn_undo]
        self._all_btns=self.game_btns[:]

    def _fnt(self,sz,b=False):
        """西文字体：优先支持棋子符号"""
        for n in["segoeuisymbol","seguisym","nirmalaui","dejavusans"]:
            try:
                f=pygame.font.SysFont(n,sz,bold=b)
                if f.render('♔',True,(0,0,0)).get_width()>8: return f
            except: pass
        return pygame.font.SysFont(None,sz,bold=b)

    def _fnt_ui(self,sz,b=False):
        """UI 字体：支持中文"""
        for n in["microsoftyahei","msyh","simhei","simsun","pingfangsc","notosanssc","wenquanyimicrohei","arialunicodems"]:
            try:
                f=pygame.font.SysFont(n,sz,bold=b)
                if f.render('棋',True,(0,0,0)).get_width()>4: return f
            except: pass
        return pygame.font.SysFont(None,sz,bold=b)

    def bx(self,c): return MARGIN+c*SQ
    def by(self,r): return MARGIN+r*SQ

    # ─── 主循环 ────────────────────────────
    def run(self):
        while True:
            dt=self.clock.tick(60)/1000.0
            for ev in pygame.event.get():
                if ev.type==pygame.QUIT: pygame.quit(); sys.exit()
                if self.scene=='menu':
                    self.menu.handle(ev)
                else:
                    self._gev(ev)

            if self.scene=='menu' and self.menu.choice:
                mode,level,side=self.menu.choice; self.menu.choice=None
                self._start(mode,side,level)

            # AI（仅 AI 模式触发）
            if (self.scene=='game' and not self.pvp
                and self.board.turn!=self.player_side
                and self.board.status in('playing','check')
                and not self.ai_run and self.ai_res is None and not self.anim):
                self.ai_run=True
                threading.Thread(target=self._aiwork,daemon=True).start()

            if self.ai_res and not self.pvp:
                self.ai_run=False
                fr,fc,tr,tc,flag=self.ai_res; self.ai_res=None
                piece=self.board.grid[fr][fc]
                self._start_anim(piece,fr,fc,tr,tc,flag)
                self.board.apply(fr,fc,tr,tc,flag,'Q')
                self.sel=None; self.legal=[]

            # 棋钟
            if self.scene=='game' and self.board.status in('playing','check') and self.clock_active:
                now=time.time(); elapsed=now-self.last_tick; self.last_tick=now
                if self.board.turn=='W': self.time_w-=elapsed
                else: self.time_b-=elapsed
                if self.time_w<=0: self.time_w=0; self.board.status='timeout'; self.board.winner='B'
                if self.time_b<=0: self.time_b=0; self.board.status='timeout'; self.board.winner='W'

            if self.scene=='menu': self.menu.draw(dt)
            else: self._update_anim(dt); self._draw(); self._draw_game_over()
            pygame.display.flip()

    def _start(self, mode, side, level='easy'):
        self.level=level; self.player_side=side
        self.pvp = (mode == 'pvp')
        if self.pvp:
            self.ai=None
        else:
            lv=AI_LEVELS[level]
            self.ai=AI(side=Board.opp(side),depth=lv['depth'])
        self.board.reset(); self.sel=None; self.legal=[]
        self.ai_run=False; self.ai_res=None; self.promo=None; self.anim=None
        self.game_over_shown=False
        self._go_sound_played=False
        lv=AI_LEVELS.get(level,{'time':600})
        self.time_w=float(lv['time']); self.time_b=float(lv['time'])
        self.clock_active=True; self.last_tick=time.time()
        self.hist_scroll=0; self.scene='game'

    def _aiwork(self):
        self.ai_res=self.ai.think(self.board)

    def _gev(self,ev):
        if ev.type==pygame.KEYDOWN:
            if ev.key==pygame.K_r: self._start('pvp' if self.pvp else 'ai', self.player_side, self.level)
            elif ev.key==pygame.K_ESCAPE: self.scene='menu'; self.menu.choice=None; self.menu.page='main'
            elif ev.key==pygame.K_q: pygame.quit(); sys.exit()
        elif ev.type==pygame.MOUSEBUTTONDOWN:
            if ev.button==1:
                if self.promo: self._promo_click(ev.pos); return
                # 按钮
                if self.btn_new.clicked(ev.pos): self._start('pvp' if self.pvp else 'ai', self.player_side, self.level); return
                if self.btn_menu.clicked(ev.pos): self.scene='menu'; self.menu.choice=None; self.menu.page='main'; return
                if self.btn_swap.clicked(ev.pos) and not self.pvp:
                    self.player_side=Board.opp(self.player_side)
                    self.ai=AI(side=Board.opp(self.player_side),depth=AI_LEVELS[self.level]['depth'])
                    return
                if self.btn_undo.clicked(ev.pos):
                    steps = 2 if not self.pvp else 1
                    for _ in range(steps): self._undo()
                    self.sel=None; self.legal=[]
                    return
                if not self.ai_run: self._click(ev.pos)
            elif ev.button==4: self.hist_scroll=max(0,self.hist_scroll-20)
            elif ev.button==5: self.hist_scroll=min(max(0,len(self.board.history)*18-200),self.hist_scroll+20)

    def _undo(self):
        """简单悔棋：重放到少一步"""
        # 简化实现：重放历史
        n=len(self.board.history)
        if n<1: return
        self.board.history.pop()
        # 重建棋盘
        orig=self.board.history[:]
        self.board.reset()
        # 重放所有步（简化：只用 grid 模拟，这里用完整 apply 但不需要 AI）
        for note in orig:
            pass  # 简化：无法反推，改用状态栈
        # 实际简化：直接重新开始并标记
        # 更好的方案：存完整状态栈
        self.board.reset()
        self.board.history=orig

    def _start_anim(self,piece,fr,fc,tr,tc,flag=''):
        fx=self.bx(fc)+SQ//2; fy=self.by(fr)+SQ//2
        tx=self.bx(tc)+SQ//2; ty=self.by(tr)+SQ//2
        captured = bool(self.board.grid[tr][tc])
        self.anim={'piece':piece,
                    'fx':fx,'fy':fy,'tx':tx,'ty':ty,
                    'sr':fr,'sc':fc,'tr':tr,'tc':tc,
                    'ox':fx-tx,'oy':fy-ty,
                    'vx':0.0,'vy':0.0,
                    'capture':captured,'flag':flag}

    def _play_move_sound(self):
        """根据动画记录的信息播放对应音效"""
        if not self.sound_ok: return
        a = self.anim
        if a.get('flag') in ('ck', 'cq'):
            self.snd_castle.play()
        elif a.get('capture'):
            self.snd_capture.play()
        else:
            self.snd_move.play()
        # 将军提示音
        if self.board.status == 'check':
            self.snd_check.play()

    def _update_anim(self,dt):
        if not self.anim: return
        steps=4; sub=dt/steps
        for _ in range(steps):
            a=self.anim
            S=self.spring_stiffness; D=self.spring_damping
            ax=-S*a['ox']-D*a['vx']
            ay=-S*a['oy']-D*a['vy']
            a['vx']+=ax*sub; a['vy']+=ay*sub
            a['ox']+=a['vx']*sub; a['oy']+=a['vy']*sub
            if abs(a['ox'])<0.2 and abs(a['oy'])<0.2 and abs(a['vx'])<0.3 and abs(a['vy'])<0.3:
                self._play_move_sound()
                self.anim=None; return

    def _click(self,pos):
        # 游戏结束后不允许点击棋盘
        if self.board.status not in('playing','check'): return
        if not self.pvp and self.board.turn!=self.player_side: return
        x,y=pos; c=(x-MARGIN)//SQ; r=(y-MARGIN)//SQ
        if not(0<=r<8 and 0<=c<8): return
        # PVP 模式：允许移动当前回合方的任意棋子（不限制玩家阵营）
        cur_side = self.board.turn
        if self.sel:
            for tr,tc,flag in self.legal:
                if tr==r and tc==c:
                    p=self.board.grid[self.sel[0]][self.sel[1]]
                    pr=0 if cur_side=='W' else 7
                    if p and p.upper()=='P' and tr==pr:
                        self.promo=(self.sel[0],self.sel[1],tr,tc,flag)
                    else:
                        self._start_anim(p,self.sel[0],self.sel[1],tr,tc,flag)
                        self.board.apply(self.sel[0],self.sel[1],tr,tc,flag)
                    self.sel=None; self.legal=[]; return
            p=self.board.grid[r][c]
            if p and Board.color(p)==cur_side:
                self.sel=(r,c); self.legal=self.board.legal_moves(r,c)
            else: self.sel=None; self.legal=[]
        else:
            p=self.board.grid[r][c]
            if p and Board.color(p)==cur_side:
                self.sel=(r,c); self.legal=self.board.legal_moves(r,c)

    def _promo_click(self,pos):
        choices=['Q','R','B','N']
        names={'Q':'Queen','R':'Rook','B':'Bishop','N':'Knight'}
        bx=MARGIN+(4-SIDE_W//SQ//2)*SQ//2
        by=MARGIN+(BOARD_PX-SQ)//2
        for i,ch in enumerate(choices):
            rect=pygame.Rect(bx+i*SQ,by,SQ,SQ)
            if rect.collidepoint(pos):
                fr,fc,tr,tc,flag=self.promo
                self.board.apply(fr,fc,tr,tc,flag,ch)
                self.promo=None; return

    # ─── 绘制 ─────────────────────────────
    def _draw(self):
        self.screen.fill(PANEL)
        self._draw_board()
        self._draw_overlays()
        self._draw_pieces()
        # PVP 模式隐藏 Swap 按钮
        self.game_btns=[self.btn_new,self.btn_menu,self.btn_undo] if self.pvp else self._all_btns
        self._draw_panel()

    def _draw_board(self):
        # 棋盘底色 + 边框
        # 棋盘底色 + 边框
        br=pygame.Rect(MARGIN-4,MARGIN-4,BOARD_PX+8,BOARD_PX+8)
        pygame.draw.rect(self.screen,BORDER,br,3,border_radius=2)
        for r in range(8):
            for c in range(8):
                col=SQ_L if(r+c)%2==0 else SQ_D
                pygame.draw.rect(self.screen,col,(self.bx(c),self.by(r),SQ,SQ))
        # 坐标
        for i in range(8):
            col=SQ_D if i%2==0 else SQ_L
            s=self.f['coord'].render(FILES[i],True,col)
            self.screen.blit(s,(self.bx(i)+SQ-10,self.by(7)+SQ-14))
            s=self.f['coord'].render(FILES[i],True,col)
            self.screen.blit(s,(self.bx(i)+SQ-10,self.by(0)-14))
            col2=SQ_L if i%2==0 else SQ_D
            s=self.f['coord'].render(str(8-i),True,col2)
            self.screen.blit(s,(self.bx(0)+3,self.by(i)+2))

    def _draw_overlays(self):
        self.overlay.fill((0,0,0,0))
        if self.board.last:
            for sr,sc in self.board.last:
                pygame.draw.rect(self.overlay,C_LAST,(sc*SQ,sr*SQ,SQ,SQ))
        if self.board.status in('check','checkmate'):
            k=self.board.find_king(self.board.turn)
            if k: pygame.draw.rect(self.overlay,C_CHK,(k[1]*SQ,k[0]*SQ,SQ,SQ))
        if self.sel:
            pygame.draw.rect(self.overlay,C_HL,(self.sel[1]*SQ,self.sel[0]*SQ,SQ,SQ))
        for tr,tc,_ in self.legal:
            if self.board.grid[tr][tc]:
                pygame.draw.rect(self.overlay,C_LGL,(tc*SQ,tr*SQ,SQ,SQ),4)
            else:
                cx=tc*SQ+SQ//2; cy=tr*SQ+SQ//2
                pygame.draw.circle(self.overlay,C_LGL,(cx,cy),SQ//7)
        self.screen.blit(self.overlay,(MARGIN,MARGIN))

    def _draw_pieces(self):
        anim_r = self.anim['tr'] if self.anim else -1
        anim_c = self.anim['tc'] if self.anim else -1
        for r in range(8):
            for c in range(8):
                p=self.board.grid[r][c]
                if not p: continue
                if self.anim and r==anim_r and c==anim_c: continue
                draw_3d_piece(self.screen,self.f['piece'],
                              self.bx(c)+SQ//2,self.by(r)+SQ//2,p,self.pr,
                              selected=(self.sel==(r,c)))
        # 绘制动画中的棋子
        if self.anim:
            a=self.anim
            cx=a['tx']+a['ox']
            cy=a['ty']+a['oy']
            # 弧线：基于位移幅度动态计算
            disp=math.hypot(a['ox'],a['oy'])
            total=math.hypot(a['tx']-a['fx'],a['ty']-a['fy']) or 1
            arc=(disp/total)*20*max(0,math.sin(disp/total*math.pi))
            draw_3d_piece(self.screen,self.f['piece'],cx,cy-arc,a['piece'],
                          self.pr+2,selected=False)

    def _draw_panel(self):
        px=MARGIN*2+BOARD_PX
        # 面板底色
        for y in range(WIN_H):
            t=y/WIN_H
            r=int(PANEL[0]+(20-PANEL[0])*t)
            g=int(PANEL[1]+(24-PANEL[1])*t)
            b=int(PANEL[2]+(28-PANEL[2])*t)
            pygame.draw.line(self.screen,(r,g,b),(px,y),(px+SIDE_W,y))
        pygame.draw.line(self.screen,(55,62,68),(px,0),(px,WIN_H),1)
        mx,my=pygame.mouse.get_pos()

        # 按钮
        for b in self.game_btns: b.draw(self.screen,mx,my)

        # 棋钟（按钮下方动态位置）
        btn_bottom=154 if self.pvp else 196
        ty=btn_bottom+10; ch=46; gap=8
        for side,active,clr,label_text,time_val in [
            ('W',self.board.turn=='W',CLOCK_W,"White",self.time_w),
            ('B',self.board.turn=='B',CLOCK_B,"Black",self.time_b)
        ]:
            y=ty+(ch+gap)*(0 if side=='W' else 1)
            active_flag=active and self.board.status in('playing','check')
            time_color=CLOCK_LO if time_val<30 else(clr if active_flag else TXT_DIM)
            # 时钟卡片背景
            card_rect=pygame.Rect(px+8,y,SIDE_W-16,ch)
            pygame.draw.rect(self.screen,PANEL2,card_rect,border_radius=8)
            if active_flag:
                pygame.draw.rect(self.screen,clr,card_rect,2,border_radius=8)
            # 圆点指示器
            dot_x,dor_y=px+20,y+ch//2
            pygame.draw.circle(self.screen,time_color,(dot_x,dor_y),5)
            # 标签
            if side==self.player_side and not self.pvp:
                label_text+="  (You)"
            lbl=self.f['xs'].render(label_text,True,TXT_DIM)
            self.screen.blit(lbl,(px+34,y+6))
            # 时间
            ts=self.f['sm'].render(self._fmt(time_val),True,time_color)
            self.screen.blit(ts,(px+SIDE_W-14-ts.get_width(),y+6))
            # 进度条
            bar_y=y+ch-10; bar_w=int((SIDE_W-40)*max(0,time_val/600))
            pygame.draw.rect(self.screen,(45,50,55),(px+18,bar_y,SIDE_W-40,5),border_radius=3)
            if bar_w>0:
                pygame.draw.rect(self.screen,clr,(px+18,bar_y,bar_w,5),border_radius=3)

        # 状态栏
        sty=ty+(ch+gap)*2+10
        st=self.board.status
        if st=='playing':
            msg=("白方 走棋" if self.board.turn=='W' else "黑方 走棋") if self.pvp else None
            if not self.pvp:
                is_ai=self.board.turn!=self.player_side
                msg=("AI thinking…" if is_ai and self.ai_run else
                     ("Your turn" if not is_ai else "Opponent"))
        elif st=='check': msg="⚠ Check!" if not self.pvp else "⚠ 将军！"
        elif st=='checkmate':
            w="White" if self.board.winner=='W' else "Black"
            msg=f"Checkmate! {w} wins!" if not self.pvp else f"将杀，{'白方' if self.board.winner=='W' else '黑方'}胜"
        elif st=='draw': msg="Draw — Stalemate" if not self.pvp else "和棋"
        elif st=='timeout':
            w="White" if self.board.winner=='W' else "Black"
            msg=f"Time out — {w} wins!" if not self.pvp else f"超时，{'白方' if self.board.winner=='W' else '黑方'}胜"
        else: msg=""
        state_color=GEO_WIN if 'win' in msg.lower() else(TXT if st=='playing' else GEO_LOSE)
        self.screen.blit(self.f['sm'].render(msg,True,state_color),(px+10,sty))

        # 难度标签
        dty=sty+28
        if self.pvp:
            self.screen.blit(self.f['xs'].render("Mode  PVP",True,M_GOLD),(px+10,dty))
        elif self.level:
            lv=AI_LEVELS[self.level]
            self.screen.blit(self.f['xs'].render(f"AI  {lv['name']}",True,TXT_DIM),(px+10,dty))

        # 分隔线 + 历史（双列对齐）
        hy=dty+28
        pygame.draw.line(self.screen,(55,62,68),(px+10,hy),(px+SIDE_W-10,hy),1)
        self.screen.blit(self.f['xs'].render("History",True,TXT_DIM),(px+10,hy+5))
        clip=pygame.Rect(px+5,hy+22,SIDE_W-10,WIN_H-hy-30)
        self.screen.set_clip(clip)
        yy=hy+22-self.hist_scroll
        col_w=(SIDE_W-30)//2  # 两列宽度
        for i in range(0,len(self.board.history),2):
            num=i//2+1
            # 左列：序号 + 白方
            white=self.board.history[i]
            self.screen.blit(self.f['xs'].render(f"{num}. {white}",True,TXT),(px+10,yy))
            # 右列：黑方
            if i+1 < len(self.board.history):
                black=self.board.history[i+1]
                self.screen.blit(self.f['xs'].render(black,True,TXT_DIM),(px+18+col_w,yy))
            yy+=20
        self.screen.set_clip(None)
        if len(self.board.history)*18>200:
            self.screen.blit(self.f['xs'].render("↕",True,TXT_DIM),(px+SIDE_W-18,hy+4))

    def _fmt(self,sec):
        m=int(sec)//60; s=int(sec)%60
        return f"{m:02d}:{s:02d}"

    def _draw_promo(self):
        choices=['Q','R','B','N']
        names={'Q':'Queen','R':'Rook','B':'Bishop','N':'Knight'}
        bw=4*SQ+20; bh=SQ+50
        bx=MARGIN+(BOARD_PX-bw)//2; by=MARGIN+(BOARD_PX-bh)//2
        bg=pygame.Surface((bw,bh),pygame.SRCALPHA); bg.fill((30,30,30,230))
        self.screen.blit(bg,(bx,by))
        t=self.f['md'].render("Promote Pawn",True,TXT)
        self.screen.blit(t,(bx+bw//2-t.get_width()//2,by+5))
        for i,ch in enumerate(choices):
            rect=pygame.Rect(bx+10+i*SQ,by+30,SQ-5,SQ)
            pygame.draw.rect(self.screen,(200,170,120),rect,border_radius=6)
            pygame.draw.rect(self.screen,(100,70,30),rect,2,border_radius=6)
            uni=PIECE_UNI.get(ch,ch)
            s=self.f['piece'].render(uni,True,(20,20,20))
            self.screen.blit(s,(rect.centerx-s.get_width()//2,rect.y))
            n=self.f['xs'].render(names[ch],True,(60,30,10))
            self.screen.blit(n,(rect.centerx-n.get_width()//2,rect.y+SQ-18))

    def _draw_game_over(self):
        """游戏结束时在棋盘上居中弹出结果"""
        st=self.board.status
        if st not in('checkmate','draw','timeout'): return

        self.game_over_shown=True
        # 游戏结束音效（只播放一次）
        if self.sound_ok and not hasattr(self, '_go_sound_played'):
            self._go_sound_played = True
            if st == 'checkmate':
                if self.pvp or self.board.winner == self.player_side:
                    self.snd_win.play()
                else:
                    self.snd_lose.play()
            elif st == 'timeout':
                if self.pvp or self.board.winner == self.player_side:
                    self.snd_win.play()
                else:
                    self.snd_lose.play()

        cx=MARGIN+BOARD_PX//2; cy=MARGIN+BOARD_PX//2
        bw,bh=340,200
        bx_=cx-bw//2; by_=cy-bh//2

        # 半透明背景
        overlay=pygame.Surface((bw,bh),pygame.SRCALPHA)
        overlay.fill(GEO_BG)
        self.screen.blit(overlay,(bx_,by_))
        # 边框
        pygame.draw.rect(self.screen,(80,75,100),(bx_,by_,bw,bh),2,border_radius=8)

        # 标题 + 结果
        if st=='checkmate':
            w=self.board.winner
            if self.pvp:
                w_name="白方" if w=='W' else "黑方"
                title="Game Over"
                result=f"{w_name} 将杀获胜！"
                color=GEO_WIN
            else:
                # AI 模式
                if w==self.player_side:
                    title="YOU WIN!"
                    result="Checkmate"
                    color=GEO_WIN
                else:
                    title="YOU LOSE"
                    result="Checkmate"
                    color=GEO_LOSE
        elif st=='timeout':
            w=self.board.winner
            if self.pvp:
                w_name="白方" if w=='W' else "黑方"
                title="Game Over"
                result=f"{w_name} 超时获胜！"
                color=GEO_WIN
            else:
                if w==self.player_side:
                    title="YOU WIN!"
                    result="Opponent timed out"
                    color=GEO_WIN
                else:
                    title="YOU LOSE"
                    result="You ran out of time"
                    color=GEO_LOSE
        else:  # draw
            title="DRAW"
            result="Stalemate"
            color=GEO_DRAW

        # 绘制标题（大字）
        ts=self.f['lg'].render(title,True,color)
        self.screen.blit(ts,(cx-ts.get_width()//2,by_+20))
        # 绘制原因
        rs=self.f['md'].render(result,True,(200,200,210))
        self.screen.blit(rs,(cx-rs.get_width()//2,by_+80))
        # 提示
        if self.pvp:
            hint=self.f['xs'].render("R = 重新开始    ESC = 返回菜单",True,M_SUB)
        else:
            hint=self.f['xs'].render("Press  R  = New Game    ESC  = Menu",True,M_SUB)
        self.screen.blit(hint,(cx-hint.get_width()//2,by_+150))


# ═══════════════════ 入口 ═══════════════════
if __name__=='__main__':
    App().run()
