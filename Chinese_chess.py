"""
中国象棋 3D · AI 人机对战
=========================
· 三档 AI 难度：简单 / 困难 / 专家
· 3D 立体棋子效果（高光 / 阴影 / 浮雕 / 投影）
· 完整规则：车马象士将炮兵 + 飞将/马腿/象眼/炮架
· 将军检测、将死/困毙判定
· 开局选择界面，运行后先选难度再下棋

快捷键：[R] 重新开局  [Q] 退出  [Esc] 返回菜单
"""

import pygame
import sys
import math
import threading
import random
import numpy as np
from copy import deepcopy
import struct
import os
import tempfile

# ═══════════════════ 常量 ═══════════════════
COLS, ROWS   = 9, 10
CELL         = 84
PAD_X        = 65
PAD_Y        = 55
BOARD_W      = PAD_X * 2 + CELL * (COLS - 1)
BOARD_H      = PAD_Y * 2 + CELL * (ROWS - 1)
INFO_H       = 64
WIN_W        = max(BOARD_W, 720)
WIN_H        = BOARD_H + INFO_H
MENU_H       = WIN_H

# 棋盘颜色
C_BG         = (232, 197, 134)
C_LINE       = (100,  68,  18)
C_RIVER      = ( 78,  48,  10)
C_GRID       = (175, 145,  90)

# 棋子 3D 颜色
PIECE_R_BG   = (210, 170, 105)   # 红方棋子底色
PIECE_R_EDGE = (160, 110,  50)   # 红方边缘
PIECE_R_TXT  = (190,  25,  25)   # 红方文字
PIECE_B_BG   = (195, 195, 190)   # 黑方棋子底色
PIECE_B_EDGE = (100, 100,  95)   # 黑方边缘
PIECE_B_TXT  = ( 18,  18,  18)   # 黑方文字
PIECE_HL     = (255, 230, 255,  90)  # 高光
PIECE_SH     = (  0,   0,   0,  60)  # 投影

# UI 颜色
C_SELECT     = (255, 215,   0)
C_LEGAL      = (  0, 190,   0)
C_CHECK      = (230,  40,  40)
C_INFO_BG    = ( 32,  32,  38)
C_INFO_TXT   = (235, 235, 235)
C_INFO_HINT  = (140, 140, 140)

# 菜单颜色
MENU_BG      = ( 25,  22,  18)
MENU_PANEL   = ( 40,  36,  28)
MENU_BTN     = (140,  95,  40)
MENU_BTN_HOV = (180, 130,  55)
MENU_BTN_BRD = (110,  70,  25)
MENU_TITLE   = (255, 225, 150)
MENU_SUB     = (170, 140, 100)
MENU_ACC     = (200, 160,  80)
MENU_ACC2    = (180, 200, 160)
MENU_GOLD    = (220, 185, 100)
MENU_DIM     = ( 90,  75,  55)

# 游戏结束弹窗
GEO_BG    = ( 20,  18,  15, 220)
GEO_WIN   = ( 50, 220, 100)
GEO_LOSE  = (230,  60,  60)
GEO_DRAW  = (220, 200,  60)

# 棋子名称
RED_NAMES   = {'K':'帅','A':'仕','B':'相','R':'车','N':'马','C':'炮','P':'兵'}
BLACK_NAMES = {'k':'将','a':'士','b':'象','r':'车','n':'马','c':'炮','p':'卒'}

# 棋子分值
PIECE_VALUE = {
    'K': 10000,'k':-10000,
    'R':   900,'r':  -900,
    'C':   450,'c':  -450,
    'N':   400,'n':  -400,
    'B':   200,'b':  -200,
    'A':   200,'a':  -200,
    'P':   100,'p':  -100,
}

# AI 难度配置
AI_LEVELS = {
    'easy':   {'depth': 1, 'name': '简  单', 'desc': '适合新手，偶尔犯错'},
    'hard':   {'depth': 3, 'name': '困  难', 'desc': '有一定棋力，需要认真对付'},
    'expert': {'depth': 4, 'name': '专  家', 'desc': '深搜 + 更强评估，高手对决'},
}

# 教学模式：棋子走法说明
PIECE_RULES = {
    'K': ('帅', [
        '活动范围：己方九宫内（3×3）',
        '每次只能走一格，横或竖',
        '不能走出九宫，不能对面将',
        '提示：将帅不能在同一列无阻挡相对',
    ]),
    'k': ('将', [
        '活动范围：己方九宫内（3×3）',
        '每次只能走一格，横或竖',
        '不能走出九宫，不能对面将',
        '提示：将帅不能在同一列无阻挡相对',
    ]),
    'A': ('仕', [
        '活动范围：己方九宫内',
        '只能斜走一格（走"×"字形）',
        '不能走出九宫',
    ]),
    'a': ('士', [
        '活动范围：己方九宫内',
        '只能斜走一格（走"×"字形）',
        '不能走出九宫',
    ]),
    'B': ('相', [
        '只能走"田"字形（斜走两格）',
        '不能过河（只在己方区域）',
        '象眼被堵时不能走该方向',
    ]),
    'b': ('象', [
        '只能走"田"字形（斜走两格）',
        '不能过河（只在己方区域）',
        '象眼被堵时不能走该方向',
    ]),
    'R': ('车', [
        '横或竖方向走任意格数',
        '路径上不能有其他棋子阻挡',
        '威力最强的棋子，价值极高',
    ]),
    'r': ('车', [
        '横或竖方向走任意格数',
        '路径上不能有其他棋子阻挡',
        '威力最强的棋子，价值极高',
    ]),
    'N': ('马', [
        '走"日"字形：先直走一格再斜走一格',
        '蹩马腿：直走方向有子则不能走',
        '马可以跳到对方棋子位置（吃子）',
    ]),
    'n': ('马', [
        '走"日"字形：先直走一格再斜走一格',
        '蹩马腿：直走方向有子则不能走',
        '马可以跳到对方棋子位置（吃子）',
    ]),
    'C': ('炮', [
        '不吃子时：横或竖走任意格，路径无阻',
        '吃子时：必须隔一个棋子（炮架）攻击',
        '炮架可以是任意方棋子',
    ]),
    'c': ('炮', [
        '不吃子时：横或竖走任意格，路径无阻',
        '吃子时：必须隔一个棋子（炮架）攻击',
        '炮架可以是任意方棋子',
    ]),
    'P': ('兵', [
        '过河前：只能向前走一格',
        '过河后：可向前或左右走一格',
        '兵不能后退',
    ]),
    'p': ('卒', [
        '过河前：只能向前走一格',
        '过河后：可向前或左右走一格',
        '卒不能后退',
    ]),
}

# 棋盘位置加分表（加强 AI）
# 这些是简化版，红方视角，row 0=黑方后排
POSITION_BONUS_R = {
    'P': [
        [0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0],
        [2,0,4,0,8,0,4,0,2],
        [6,12,18,18,20,18,18,12,6],
        [10,20,30,34,40,34,30,20,10],
        [14,26,42,60,80,60,42,26,14],
        [0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0],
    ],
    'R': [
        [6,8,8,14,14,14,8,8,6],
        [6,10,12,16,16,16,12,10,6],
        [4,6,8,12,14,12,8,6,4],
        [4,6,8,12,14,12,8,6,4],
        [4,6,8,12,14,12,8,6,4],
        [4,6,8,12,14,12,8,6,4],
        [4,6,8,12,14,12,8,6,4],
        [4,6,8,12,14,12,8,6,4],
        [4,6,8,12,14,12,8,6,4],
        [6,8,8,14,14,14,8,8,6],
    ],
    'N': [
        [2,4,4,8,8,8,4,4,2],
        [2,8,14,14,14,14,14,8,2],
        [4,8,14,18,18,18,14,8,4],
        [4,10,16,22,22,22,16,10,4],
        [6,12,18,24,26,24,18,12,6],
        [6,12,18,24,26,24,18,12,6],
        [4,10,16,22,22,22,16,10,4],
        [4,8,14,18,18,18,14,8,4],
        [2,8,14,14,14,14,14,8,2],
        [2,4,4,8,8,8,4,4,2],
    ],
    'C': [
        [2,2,2,6,6,6,2,2,2],
        [2,4,4,8,10,8,4,4,2],
        [2,4,4,8,10,8,4,4,2],
        [0,0,0,2,4,2,0,0,0],
        [0,0,0,0,2,0,0,0,0],
        [0,0,0,0,2,0,0,0,0],
        [0,0,0,2,4,2,0,0,0],
        [2,4,4,8,10,8,4,4,2],
        [2,4,4,8,10,8,4,4,2],
        [2,2,2,6,6,6,2,2,2],
    ],
}

# 黑方位置表 = 红方翻转
for ptype, table in list(POSITION_BONUS_R.items()):
    black_type = ptype.lower()
    POSITION_BONUS_R[black_type] = [row[:] for row in reversed(table)]


# 初始棋盘
INIT_RAW = [
    list('rnbakabnr'),
    list('         '),
    list(' c     c '),
    list('p p p p p'),
    list('         '),
    list('         '),
    list('P P P P P'),
    list(' C     C '),
    list('         '),
    list('RNBAKABNR'),
]

def parse_board(raw):
    return [[None if ch == ' ' else ch for ch in row] for row in raw]


# ═══════════════════ 棋盘逻辑 ═══════════════════
class CXBoard:
    def __init__(self):
        self.reset()

    def reset(self):
        self.grid     = parse_board(INIT_RAW)
        self.turn     = 'R'
        self.status   = 'playing'
        self.winner   = None
        self.last_move= None

    @staticmethod
    def side(piece):
        if piece is None: return None
        return 'R' if piece.isupper() else 'B'

    @staticmethod
    def opp(side):
        return 'B' if side == 'R' else 'R'

    def at(self, r, c):
        if 0 <= r < ROWS and 0 <= c < COLS:
            return self.grid[r][c]
        return None

    def find_king(self, side):
        k = 'K' if side == 'R' else 'k'
        for r in range(ROWS):
            for c in range(COLS):
                if self.grid[r][c] == k: return (r, c)
        return None

    # ─── 伪合法步 ───────────────────────────
    def pseudo_moves(self, r, c):
        p = self.grid[r][c]
        if not p: return []
        s = self.side(p); t = p.upper()
        if   t == 'K': return self._mv_king(r,c,s)
        elif t == 'A': return self._mv_advisor(r,c,s)
        elif t == 'B': return self._mv_bishop(r,c,s)
        elif t == 'R': return self._mv_rook(r,c,s)
        elif t == 'N': return self._mv_knight(r,c,s)
        elif t == 'C': return self._mv_cannon(r,c,s)
        elif t == 'P': return self._mv_pawn(r,c,s)
        return []

    def _in_palace(self, r, c, s):
        if s == 'R': return 7 <= r <= 9 and 3 <= c <= 5
        return 0 <= r <= 2 and 3 <= c <= 5

    def _mv_king(self, r, c, s):
        m = []
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if self._in_palace(nr,nc,s):
                t = self.at(nr,nc)
                if t is None or self.side(t) != s:
                    m.append((nr,nc))
        return m

    def _mv_advisor(self, r, c, s):
        m = []
        for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            nr, nc = r+dr, c+dc
            if self._in_palace(nr,nc,s):
                t = self.at(nr,nc)
                if t is None or self.side(t) != s:
                    m.append((nr,nc))
        return m

    def _mv_bishop(self, r, c, s):
        m = []
        for dr, dc in [(-2,-2),(-2,2),(2,-2),(2,2)]:
            nr, nc = r+dr, c+dc
            if not (0 <= nr < ROWS and 0 <= nc < COLS): continue
            if s == 'R' and nr < 5: continue
            if s == 'B' and nr > 4: continue
            if self.at(r+dr//2, c+dc//2): continue
            t = self.at(nr,nc)
            if t is None or self.side(t) != s:
                m.append((nr,nc))
        return m

    def _mv_rook(self, r, c, s):
        m = []
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            while 0 <= nr < ROWS and 0 <= nc < COLS:
                t = self.at(nr,nc)
                if t is None:
                    m.append((nr,nc))
                elif self.side(t) != s:
                    m.append((nr,nc)); break
                else: break
                nr += dr; nc += dc
        return m

    def _mv_knight(self, r, c, s):
        m = []
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            mr, mc = r+dr, c+dc
            if not (0 <= mr < ROWS and 0 <= mc < COLS): continue
            if self.at(mr,mc): continue  # 蹩马腿
            for sr, sc in self._knight2(dr,dc):
                nr, nc = mr+sr, mc+sc
                if 0 <= nr < ROWS and 0 <= nc < COLS:
                    t = self.at(nr,nc)
                    if t is None or self.side(t) != s:
                        m.append((nr,nc))
        return m

    @staticmethod
    def _knight2(dr, dc):
        if dr == -1: return [(-1,-1),(-1,1)]
        if dr ==  1: return [( 1,-1),( 1,1)]
        if dc == -1: return [(-1,-1),( 1,-1)]
        return [(-1,1),(1,1)]

    def _mv_cannon(self, r, c, s):
        m = []
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            jumped = False
            while 0 <= nr < ROWS and 0 <= nc < COLS:
                t = self.at(nr,nc)
                if not jumped:
                    if t is None: m.append((nr,nc))
                    else: jumped = True
                else:
                    if t is not None:
                        if self.side(t) != s: m.append((nr,nc))
                        break
                nr += dr; nc += dc
        return m

    def _mv_pawn(self, r, c, s):
        m = []
        if s == 'R':
            fwd = (-1, 0); crossed = r <= 4
        else:
            fwd = ( 1, 0); crossed = r >= 5
        nr, nc = r+fwd[0], c+fwd[1]
        if 0 <= nr < ROWS and 0 <= nc < COLS:
            t = self.at(nr,nc)
            if t is None or self.side(t) != s:
                m.append((nr,nc))
        if crossed:
            for dc in (-1,1):
                nc = c+dc
                if 0 <= nc < COLS:
                    t = self.at(r,nc)
                    if t is None or self.side(t) != s:
                        m.append((r,nc))
        return m

    # ─── 飞将检测 ──────────────────────────
    def _kings_face(self, g=None):
        g = g or self.grid
        Kr=Kc=kr=kc=None
        for r in range(ROWS):
            for c in range(COLS):
                p = g[r][c]
                if p == 'K': Kr,Kc = r,c
                if p == 'k': kr,kc = r,c
        if Kr is None or kr is None or Kc != kc: return False
        for r in range(min(Kr,kr)+1, max(Kr,kr)):
            if g[r][Kc]: return False
        return True

    # ─── 将军检测 ──────────────────────────
    def in_check(self, side, g=None):
        g = g or self.grid
        king = 'K' if side == 'R' else 'k'
        kr = kc = None
        for r in range(ROWS):
            for c in range(COLS):
                if g[r][c] == king: kr,kc = r,c; break
            if kr is not None: break
        if kr is None: return True
        opp = self.opp(side)
        b = CXBoard.__new__(CXBoard); b.grid = g
        for r in range(ROWS):
            for c in range(COLS):
                if g[r][c] and self.side(g[r][c]) == opp:
                    for mr, mc in b.pseudo_moves(r,c):
                        if mr == kr and mc == kc: return True
        return self._kings_face(g)

    # ─── 合法步 ────────────────────────────
    def legal_moves(self, r, c):
        p = self.grid[r][c]
        if not p or self.side(p) != self.turn: return []
        return [(tr,tc) for tr,tc in self.pseudo_moves(r,c)
                if not self._check_after(r,c,tr,tc)]

    def _check_after(self, fr, fc, tr, tc):
        g = [row[:] for row in self.grid]
        g[tr][tc] = g[fr][fc]; g[fr][fc] = None
        return self.in_check(self.side(self.grid[fr][fc]), g)

    def all_legal(self, side=None):
        side = side or self.turn
        moves = []
        for r in range(ROWS):
            for c in range(COLS):
                if self.grid[r][c] and self.side(self.grid[r][c]) == side:
                    for tr,tc in self.pseudo_moves(r,c):
                        if not self._check_after(r,c,tr,tc):
                            moves.append((r,c,tr,tc))
        return moves

    # ─── 执行 ──────────────────────────────
    def apply(self, fr, fc, tr, tc):
        self.last_move = ((fr,fc),(tr,tc))
        self.grid[tr][tc] = self.grid[fr][fc]
        self.grid[fr][fc] = None
        self.turn = self.opp(self.turn)
        self._refresh()

    def apply_raw(self, fr, fc, tr, tc):
        self.grid[tr][tc] = self.grid[fr][fc]
        self.grid[fr][fc] = None

    def _refresh(self):
        s = self.turn
        moves = self.all_legal(s)
        if not moves:
            if self.in_check(s):
                self.status = 'checkmate'; self.winner = self.opp(s)
            else:
                self.status = 'draw'
        elif self.in_check(s):
            self.status = 'check'
        else:
            self.status = 'playing'


# ═══════════════════ AI 引擎 ═══════════════════
class ChessAI:
    def __init__(self, side='B', depth=3):
        self.side  = side
        self.depth = depth

    def best_move(self, board):
        best = None
        alpha, beta = -999999, 999999
        moves = board.all_legal(self.side)
        random.shuffle(moves)
        for fr,fc,tr,tc in moves:
            b2 = deepcopy(board)
            b2.apply_raw(fr,fc,tr,tc)
            b2.turn = board.opp(self.side)
            score = -self._negamax(b2, self.depth-1, -beta, -alpha,
                                   board.opp(self.side))
            if score > alpha:
                alpha = score; best = (fr,fc,tr,tc)
        return best

    def _negamax(self, board, depth, alpha, beta, side):
        if depth == 0:
            return self._evaluate(board, side)
        moves = board.all_legal(side)
        if not moves:
            if board.in_check(side):
                return -9000 + (self.depth - depth)
            return 0
        # 简单排序：吃子优先
        moves.sort(key=lambda m: self._move_sort(board, m), reverse=True)
        for fr,fc,tr,tc in moves:
            b2 = deepcopy(board)
            b2.apply_raw(fr,fc,tr,tc)
            score = -self._negamax(b2, depth-1, -beta, -alpha,
                                   board.opp(side))
            if score >= beta: return beta
            if score > alpha: alpha = score
        return alpha

    def _move_sort(self, board, move):
        """吃子排前面，值越大越优先"""
        fr,fc,tr,tc = move
        target = board.grid[tr][tc]
        if target:
            return abs(PIECE_VALUE.get(target, 0))
        return 0

    def _evaluate(self, board, side):
        score = 0
        for r in range(ROWS):
            for c in range(COLS):
                p = board.grid[r][c]
                if not p: continue
                v = PIECE_VALUE.get(p, 0)
                # 位置加分
                bonus = 0
                for ptype, table in POSITION_BONUS_R.items():
                    if p == ptype:
                        bonus = table[r][c]
                        break
                v += bonus
                score += v
        if side == 'B': score = -score
        return score


# ═══════════════════ 音效生成（物理建模） ═══════════════════
def _make_wav_bytes(samples_arr, sample_rate=44100):
    """将 numpy float 数组（-1~1）打包为 WAV bytes"""
    s = np.clip(samples_arr, -1, 1)
    data = (s * 32767).astype(np.int16).tobytes()
    buf = bytearray()
    buf += b'RIFF'
    buf += struct.pack('<I', 36 + len(data))
    buf += b'WAVEfmt '
    buf += struct.pack('<IHHIIHH', 16, 1, 1, sample_rate, sample_rate * 2, 2, 16)
    buf += b'data'
    buf += struct.pack('<I', len(data))
    buf += data
    return bytes(buf)


def _bandpass(noise, low, high, sr):
    """频域带通滤波：只保留 low~high 频率成分"""
    n = len(noise)
    freq = np.fft.rfft(noise)
    bins = np.fft.rfftfreq(n, 1.0 / sr)
    mask = ((bins >= low) & (bins <= high)).astype(np.float64)
    edge = 50
    mask = np.where(bins < low + edge, np.clip((bins - low) / edge, 0, 1), mask)
    mask = np.where(bins > high - edge, np.clip((high - bins) / edge, 0, 1), mask)
    return np.fft.irfft(freq * mask, n)


def _resonance(sr, dur, freq, decay, gain=1.0):
    """模拟材质共振：正弦衰减振荡"""
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    return gain * np.sin(2 * np.pi * freq * t) * np.exp(-decay * t)


def _normalize(arr, peak=0.7):
    pk = np.max(np.abs(arr))
    if pk < 1e-6:
        return arr
    return arr / pk * peak


def make_place_sound():
    """落子音效：真实木质棋子放在棋盘上
    白噪声冲击 → 木质频段带通(300~5000Hz) → 多频共振衰减
    """
    sr = 44100
    dur = 0.12
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False)

    # 噪声冲击（瞬间碰撞）
    imp = np.random.randn(n) * np.exp(-t * 60)

    # 木质碰撞频段
    wood = _bandpass(imp, 300, 5000, sr)
    wood = _normalize(wood, 0.6)

    # 木质共振（棋盘+棋子的固有频率）
    res = (_resonance(sr, dur, 420 + random.randint(-30, 30), 28, 0.35)
         + _resonance(sr, dur, 1100 + random.randint(-60, 60), 45, 0.18)
         + _resonance(sr, dur, 2400 + random.randint(-100, 100), 70, 0.08))

    # 棋盘回响（低频共鸣）
    board = _resonance(sr, dur, 180 + random.randint(-15, 15), 15, 0.15)

    sig = _normalize(wood + res + board, 0.55)
    return _make_wav_bytes(sig, sr)


def make_capture_sound():
    """吃子音效：棋子碰撞棋子，更强冲击+摩擦
    强冲击 → 高频带通(400~8000Hz) + 双棋子共振 + 摩擦噪声
    """
    sr = 44100
    dur = 0.18
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False)

    imp = np.random.randn(n) * np.exp(-t * 45)
    hit = _bandpass(imp, 400, 8000, sr)
    hit = _normalize(hit, 0.7)

    # 双棋子共振
    r1, r2 = random.randint(-40, 40), random.randint(-80, 80)
    res = (_resonance(sr, dur, 680 + r1, 22, 0.40)
         + _resonance(sr, dur, 1600 + r2, 38, 0.20)
         + _resonance(sr, dur, 3200 + random.randint(-150, 150), 65, 0.10)
         + _resonance(sr, dur, 5200 + random.randint(-200, 200), 90, 0.05))

    # 碰撞后摩擦噪声
    f_len = int(0.06 * sr)
    friction = _bandpass(np.random.randn(f_len), 1000, 6000, sr) * 0.08
    friction *= np.linspace(1, 0, f_len)
    f_full = np.zeros(n)
    start = min(int(0.015 * sr), n - f_len)
    f_full[start:start + f_len] = friction

    sig = _normalize(hit + res + f_full, 0.6)
    return _make_wav_bytes(sig, sr)


def make_check_sound():
    """将军提示音：短促敲击 + 上升双音"""
    sr = 44100
    dur = 0.2
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False)

    imp = np.random.randn(n) * np.exp(-t * 70)
    tap = _bandpass(imp, 400, 4000, sr)
    tap = _normalize(tap, 0.3)

    note = np.zeros(n)
    mid = int(0.09 * sr)
    note[:mid] = np.sin(2 * np.pi * 880 * t[:mid]) * np.exp(-t[:mid] * 25) * 0.25
    note[mid:] = np.sin(2 * np.pi * 1100 * t[:n-mid]) * np.exp(-t[:n-mid] * 22) * 0.30

    sig = _normalize(tap + note, 0.45)
    return _make_wav_bytes(sig, sr)


def make_gameover_sound(win=True):
    """游戏结束音效：胜利上升和弦 / 失败下降双音"""
    sr = 44100
    dur = 0.6
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    sig = np.zeros(n)

    notes = [523.25, 659.25, 783.99] if win else [440.0, 329.63]
    nd = 0.14 if win else 0.18

    for i, freq in enumerate(notes):
        s = int(i * nd * sr)
        e = min(s + int(nd * sr), n)
        st = np.arange(e - s) / sr
        seg = np.sin(2 * np.pi * freq * st) * np.exp(-st * 8) * 0.3
        seg += np.sin(2 * np.pi * freq * 2 * st) * np.exp(-st * 15) * 0.1
        sig[s:e] += seg

    sig = _normalize(sig, 0.45)
    return _make_wav_bytes(sig, sr)


# ═══════════════════ TTS 语音生成 ═══════════════════
def _tts_to_file(text, voice_name='Microsoft Huihui Desktop', rate=0):
    """使用 Windows SAPI 生成中文语音 WAV 文件，返回文件路径"""
    tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    tmp.close()
    path = tmp.name
    try:
        import subprocess
        # 用 PowerShell 调用 SAPI 生成语音
        ps_cmd = (
            f'Add-Type -AssemblyName System.Speech; '
            f'$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
            f'$s.SelectVoice("{voice_name}"); '
            f'$s.Rate = {rate}; '
            f'$s.SetOutputToWaveFile("{path}"); '
            f'$s.Speak("{text}"); '
            f'$s.Dispose()'
        )
        subprocess.run(
            ['powershell', '-ExecutionPolicy', 'Bypass', '-Command', ps_cmd],
            capture_output=True, timeout=5
        )
    except Exception:
        path = None
    return path


def make_tts_sounds():
    """预生成所有需要的语音音效，返回 {name: pygame.mixer.Sound}"""
    sounds = {}
    texts = {
        'check': '将军',
        'capture': '吃',
        'checkmate_win': '你赢了',
        'checkmate_lose': '你输了',
        'draw_game': '和棋',
    }
    for name, text in texts.items():
        path = _tts_to_file(text)
        if path and os.path.exists(path):
            try:
                sounds[name] = pygame.mixer.Sound(path)
            except Exception:
                pass
    return sounds
def draw_piece_3d(surface, font, x, y, piece_name, side, radius=30, selected=False):
    """
    绘制一枚 3D 立体棋子
    side: 'R' 红方 / 'B' 黑方
    """
    r = radius

    # ── 投影（偏移阴影）───
    shadow_surf = pygame.Surface((r*2+10, r*2+10), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0,0,0,50),
                        (3, 6, r*2+4, r*2+2))
    surface.blit(shadow_surf, (x-r-5+3, y-r-5+4))

    # ── 底圈（模拟厚度）───
    bg   = PIECE_R_BG if side == 'R' else PIECE_B_BG
    edge = PIECE_R_EDGE if side == 'R' else PIECE_B_EDGE
    dark = tuple(max(0, c-40) for c in bg)

    pygame.draw.circle(surface, dark, (x, y+3), r+1)
    pygame.draw.circle(surface, edge, (x, y+3), r+1, 2)

    # ── 主体 ──
    pygame.draw.circle(surface, bg, (x, y), r)

    # ── 内圈纹理 ──
    inner_r = r - 4
    inner_bg = tuple(min(255, c+15) for c in bg)
    pygame.draw.circle(surface, inner_bg, (x, y), inner_r)
    pygame.draw.circle(surface, edge, (x, y), inner_r, 1)

    # ── 高光（左上弧形）───
    hl_surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
    hl_cx, hl_cy = r - r//3, r - r//3
    for i in range(r//2, 0, -1):
        alpha = int(60 * (1 - i/(r//2)))
        pygame.draw.circle(hl_surf, (255,255,255,alpha), (hl_cx, hl_cy), i)
    surface.blit(hl_surf, (x-r, y-r))

    # ── 边框 ──
    pygame.draw.circle(surface, edge, (x, y), r, 2)

    # ── 选中金环 ──
    if selected:
        pygame.draw.circle(surface, C_SELECT, (x, y), r+3, 4)

    # ── 文字 ──
    txt_color = PIECE_R_TXT if side == 'R' else PIECE_B_TXT
    txt = font.render(piece_name, True, txt_color)
    # 文字阴影
    txt_sh = font.render(piece_name, True, (0,0,0,80) if side=='R' else (180,180,180,80))
    surface.blit(txt_sh, (x - txt_sh.get_width()//2 + 1,
                          y - txt_sh.get_height()//2 + 1))
    surface.blit(txt, (x - txt.get_width()//2,
                       y - txt.get_height()//2))


# ═══════════════════ 菜单界面 ═══════════════════
class MenuScene:
    """两级菜单：主菜单（选模式）→ AI子菜单（选难度）"""
    def __init__(self, screen, font_title, font_md, font_sm, font_xs, font_deco):
        self.screen     = screen
        self.font_title = font_title
        self.font_md    = font_md
        self.font_sm    = font_sm
        self.font_xs    = font_xs
        self.font_deco  = font_deco
        self.choice     = None   # 最终选择，格式 'ai:easy' / 'pvp' / 'tutorial'
        self.page       = 'main' # 'main' | 'ai'

        cx = WIN_W // 2
        bw, bh = 300, 62
        gap = 16

        # 主菜单按钮
        cy_main = WIN_H // 2 + 10
        self.main_buttons = {
            'ai':       (pygame.Rect(cx-bw//2, cy_main - (bh+gap), bw, bh),
                         'AI  对  战', '挑战电脑，三档难度可选',
                         (220, 160,  60)),
            'pvp':      (pygame.Rect(cx-bw//2, cy_main,            bw, bh),
                         '普  通  模  式', '双人本地对弈，轮流操控红黑',
                         ( 80, 180, 120)),
            'tutorial': (pygame.Rect(cx-bw//2, cy_main + (bh+gap), bw, bh),
                         '教  学  模  式', '点击棋子查看走法规则说明',
                         (100, 160, 220)),
        }

        # AI 子菜单按钮
        cy_ai = WIN_H // 2 + 10
        self.ai_buttons = {
            'easy':   (pygame.Rect(cx-bw//2, cy_ai - (bh+gap), bw, bh),
                       '简  单', '适合新手，偶尔犯错',
                       ( 80, 180, 120)),
            'hard':   (pygame.Rect(cx-bw//2, cy_ai,            bw, bh),
                       '困  难', '有一定棋力，需要认真对付',
                       (220, 180,  60)),
            'expert': (pygame.Rect(cx-bw//2, cy_ai + (bh+gap), bw, bh),
                       '专  家', '深搜+强评估，高手对决',
                       (220,  80,  60)),
        }

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.page == 'main':
                for key, (rect, *_) in self.main_buttons.items():
                    if rect.collidepoint(event.pos):
                        if key == 'ai':
                            self.page = 'ai'
                        else:
                            self.choice = key
            elif self.page == 'ai':
                # 返回按钮
                if self._back_rect().collidepoint(event.pos):
                    self.page = 'main'
                    return
                for key, (rect, *_) in self.ai_buttons.items():
                    if rect.collidepoint(event.pos):
                        self.choice = f'ai:{key}'

    def _back_rect(self):
        return pygame.Rect(18, WIN_H - 48, 90, 32)

    # ── 公共绘制工具 ──────────────────
    def _draw_header(self, subtitle):
        """绘制顶部装饰 + 标题 + 副标题"""
        bar_h = 160
        bar = pygame.Surface((WIN_W, bar_h), pygame.SRCALPHA)
        for i in range(bar_h):
            alpha = int(35 * (1 - i / bar_h))
            pygame.draw.line(bar, (140, 110, 50, alpha), (0, i), (WIN_W, i))
        self.screen.blit(bar, (0, 0))

        red_pieces   = "車 馬 相 仕 帥"
        black_pieces = "車 馬 象 士 將"
        deco_r = self.font_deco.render(red_pieces,   True, (160, 60, 50))
        deco_b = self.font_deco.render(black_pieces, True, (100, 100, 95))
        self.screen.blit(deco_r, (WIN_W//2 - deco_r.get_width()//2, 18))
        self.screen.blit(deco_b, (WIN_W//2 - deco_b.get_width()//2, 42))

        title = self.font_title.render("中 国 象 棋", True, MENU_TITLE)
        self.screen.blit(title, (WIN_W//2 - title.get_width()//2, 68))

        sub = self.font_xs.render(subtitle, True, MENU_SUB)
        self.screen.blit(sub, (WIN_W//2 - sub.get_width()//2, 135))

        cx = WIN_W // 2
        sep_y = 160
        line_w = 100
        for i in range(line_w):
            alpha = int(180 * (1 - abs(i - line_w//2) / (line_w//2)))
            bright = tuple(min(255, c * alpha // 180) for c in MENU_GOLD)
            pygame.draw.line(self.screen, bright,
                             (cx - line_w + i, sep_y), (cx - line_w + i + 1, sep_y))
        d = 4
        pygame.draw.polygon(self.screen, MENU_GOLD,
                            [(cx, sep_y-d), (cx+d, sep_y), (cx, sep_y+d), (cx-d, sep_y)])

    def _draw_button(self, rect, name, desc, mark_color, hovered):
        """绘制一个通用按钮"""
        if hovered:
            glow = pygame.Surface((rect.w+16, rect.h+16), pygame.SRCALPHA)
            pygame.draw.rect(glow, (200, 160, 70, 40),
                             (0, 0, rect.w+16, rect.h+16), border_radius=14)
            self.screen.blit(glow, (rect.x-8, rect.y-8))

        pygame.draw.rect(self.screen, (12, 10, 8), rect.move(3, 4), border_radius=12)
        bg = MENU_BTN_HOV if hovered else MENU_BTN
        pygame.draw.rect(self.screen, bg, rect, border_radius=12)

        hl = pygame.Surface((rect.w-8, 1), pygame.SRCALPHA)
        hl.fill((255, 255, 255, 25 if hovered else 15))
        self.screen.blit(hl, (rect.x+4, rect.y+2))

        brd = MENU_GOLD if hovered else MENU_BTN_BRD
        pygame.draw.rect(self.screen, brd, rect, 2, border_radius=12)

        pygame.draw.rect(self.screen, mark_color,
                         (rect.x+10, rect.y+14, 4, rect.h-28), border_radius=2)

        ns = self.font_md.render(name, True, (255,245,220) if hovered else (240,225,195))
        self.screen.blit(ns, (rect.x+24, rect.y + rect.h//2 - ns.get_height()//2 - 9))
        ds = self.font_xs.render(desc, True, MENU_SUB)
        self.screen.blit(ds, (rect.x+24, rect.y + rect.h//2 - ds.get_height()//2 + 11))

    def draw(self, dt=0.016):
        self.screen.fill(MENU_BG)
        mx, my = pygame.mouse.get_pos()

        if self.page == 'main':
            self._draw_header("3D  ·  AI 对战  ·  双人  ·  教学")
            label = self.font_xs.render("— 选择模式 —", True, MENU_DIM)
            self.screen.blit(label, (WIN_W//2 - label.get_width()//2, 172))

            for key, (rect, name, desc, color) in self.main_buttons.items():
                self._draw_button(rect, name, desc, color, rect.collidepoint(mx, my))

        elif self.page == 'ai':
            self._draw_header("AI 对战  ·  选择难度")
            label = self.font_xs.render("— 选择难度 —", True, MENU_DIM)
            self.screen.blit(label, (WIN_W//2 - label.get_width()//2, 172))

            for key, (rect, name, desc, color) in self.ai_buttons.items():
                self._draw_button(rect, name, desc, color, rect.collidepoint(mx, my))

            # 返回按钮
            br = self._back_rect()
            back_hov = br.collidepoint(mx, my)
            pygame.draw.rect(self.screen, (50, 42, 32) if back_hov else (35, 28, 20),
                             br, border_radius=8)
            pygame.draw.rect(self.screen, MENU_GOLD if back_hov else MENU_DIM,
                             br, 1, border_radius=8)
            bs = self.font_xs.render("← 返回", True, (200,185,155) if back_hov else MENU_DIM)
            self.screen.blit(bs, (br.x + br.w//2 - bs.get_width()//2,
                                  br.y + br.h//2 - bs.get_height()//2))

        # 底部版本号
        ver = self.font_xs.render("v1.0", True, (50, 42, 35))
        self.screen.blit(ver, (WIN_W - ver.get_width() - 12, WIN_H - 22))


# ═══════════════════ 主应用 ═══════════════════
class ChessApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("中国象棋 3D · 人机对战")
        self.clock = pygame.time.Clock()

        # 字体
        self.font_piece = self._mk_font(34, bold=True)
        self.font_title = self._mk_font(70, bold=True)
        self.font_lg    = self._mk_font(58, bold=True)
        self.font_md    = self._mk_font(28)
        self.font_sm    = self._mk_font(22)
        self.font_river = self._mk_font(30, bold=True)
        self.font_coord = self._mk_font(16)
        self.font_xs    = self._mk_font(18)
        self.font_deco  = self._mk_font(26)

        self.scene    = 'menu'
        self.menu     = MenuScene(self.screen, self.font_title, self.font_md, self.font_sm, self.font_xs, self.font_deco)
        self.board    = CXBoard()
        self.ai       = None
        self.ai_level = None
        self.game_mode = None   # 'ai' | 'pvp' | 'tutorial'
        self.selected = None
        self.legal    = []
        self.ai_thinking = False
        self.ai_result   = None
        self.overlay  = pygame.Surface((WIN_W, BOARD_H), pygame.SRCALPHA)
        # 动画（easeOutCubic 平滑滑动）
        self.anim = None
        self.anim_base_dur = 0.18
        self.anim_px_per_sec = 800
        # 棋子半径
        self.pr = CELL // 2 - 5
        # 游戏结束语音标记
        self.game_over_announced = False

        # 音效
        pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
        self.snd_place = pygame.mixer.Sound(buffer=make_place_sound())
        self.snd_capture = pygame.mixer.Sound(buffer=make_capture_sound())
        self.snd_check = pygame.mixer.Sound(buffer=make_check_sound())
        self.snd_win = pygame.mixer.Sound(buffer=make_gameover_sound(win=True))
        self.snd_lose = pygame.mixer.Sound(buffer=make_gameover_sound(win=False))
        self.snd_place.set_volume(0.5)
        self.snd_capture.set_volume(0.6)
        self.snd_check.set_volume(0.45)
        # TTS 语音（异步加载避免卡界面）
        self.snd_tts = {}
        threading.Thread(target=self._load_tts, daemon=True).start()

    def _load_tts(self):
        """后台线程加载 TTS 语音"""
        self.snd_tts = make_tts_sounds()

    def _mk_font(self, size, bold=False):
        for name in ["microsoftyahei","simhei","simsun","fangsong"]:
            try:
                f = pygame.font.SysFont(name, size, bold=bold)
                if f.render("车", True, (0,0,0)).get_width() > 4:
                    return f
            except Exception:
                pass
        return pygame.font.SysFont(None, size, bold=bold)

    def rc_xy(self, r, c):
        return PAD_X + c * CELL, PAD_Y + r * CELL

    def xy_rc(self, x, y):
        c = round((x - PAD_X) / CELL)
        r = round((y - PAD_Y) / CELL)
        if 0 <= r < ROWS and 0 <= c < COLS:
            return r, c
        return None

    # ─── 主循环 ────────────────────────────
    def run(self):
        while True:
            dt = min(self.clock.tick(60) / 1000.0, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if self.scene == 'menu':
                    self.menu.handle_event(event)
                else:
                    self._game_event(event)

            # 菜单选择后进入游戏
            if self.scene == 'menu' and self.menu.choice:
                self._start_game(self.menu.choice)

            # AI 走棋（仅 ai 模式，等待动画结束）
            if (self.scene == 'game' and self.game_mode == 'ai' and
                    self.board.turn == 'B' and
                    self.board.status in ('playing','check') and
                    not self.ai_thinking and self.ai_result is None and
                    self.anim is None):
                self.ai_thinking = True
                threading.Thread(target=self._ai_work, daemon=True).start()

            if self.game_mode == 'ai' and self.ai_result and self.anim is None:
                self.ai_thinking = False
                fr,fc,tr,tc = self.ai_result
                self.ai_result = None
                piece = self.board.grid[fr][fc]
                side = CXBoard.side(piece)
                name = RED_NAMES.get(piece,'') or BLACK_NAMES.get(piece,piece)
                self._start_anim(piece, side, name, fr, fc, tr, tc)
                self.board.apply(fr,fc,tr,tc)
                self.selected = None; self.legal = []

            # 绘制
            if self.scene == 'menu':
                self.menu.draw(dt)
            else:
                self._update_anim(dt)
                self._draw_game()
                self._draw_game_over()
            pygame.display.flip()

    def _start_game(self, choice):
        """choice: 'ai:easy' | 'ai:hard' | 'ai:expert' | 'pvp' | 'tutorial'"""
        self.board.reset()
        self.selected = None; self.legal = []
        self.ai_thinking = False; self.ai_result = None
        self.anim = None
        self.game_over_announced = False

        if choice.startswith('ai:'):
            level_key = choice.split(':')[1]
            self.game_mode = 'ai'
            self.ai_level  = level_key
            lv = AI_LEVELS[level_key]
            self.ai = ChessAI(side='B', depth=lv['depth'])
        elif choice == 'pvp':
            self.game_mode = 'pvp'
            self.ai_level  = None
            self.ai        = None
        elif choice == 'tutorial':
            self.game_mode = 'tutorial'
            self.ai_level  = None
            self.ai        = None

        self.scene = 'game'

    def _ai_work(self):
        move = self.ai.best_move(self.board)
        self.ai_result = move

    def _game_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self._start_game(
                    f'ai:{self.ai_level}' if self.game_mode == 'ai' else self.game_mode
                )
                return
            elif event.key == pygame.K_ESCAPE:
                self.scene = 'menu'
                self.menu.choice = None
                self.menu.page = 'main'
                return
            elif event.key == pygame.K_q:
                pygame.quit(); sys.exit()
        elif (event.type == pygame.MOUSEBUTTONDOWN and
              event.button == 1 and not self.ai_thinking):
            self._click(event.pos)

    def _click(self, pos):
        # 教学模式：允许点任意方棋子查看走法，不实际落子
        if self.game_mode == 'tutorial':
            self._tutorial_click(pos)
            return

        # 游戏结束后禁止点击
        if self.board.status not in ('playing', 'check'):
            return
        # 动画中禁止点击
        if self.anim:
            return

        # PVP：当前轮到谁就操作谁；AI模式：只操作红方
        if self.game_mode == 'ai' and self.board.turn != 'R':
            return

        rc = self.xy_rc(*pos)
        if not rc: return
        r, c = rc
        cur_side = self.board.turn  # 当前要走的方

        if self.selected:
            if (r, c) in self.legal:
                piece = self.board.grid[self.selected[0]][self.selected[1]]
                side  = CXBoard.side(piece)
                name  = RED_NAMES.get(piece,'') or BLACK_NAMES.get(piece,piece)
                self._start_anim(piece, side, name, self.selected[0], self.selected[1], r, c)
                self.board.apply(self.selected[0], self.selected[1], r, c)
                self.selected = None; self.legal = []
                return
            p = self.board.grid[r][c]
            if p and CXBoard.side(p) == cur_side:
                self.selected = (r, c)
                self.legal = self.board.legal_moves(r, c)
                return
            self.selected = None; self.legal = []
        else:
            p = self.board.grid[r][c]
            if p and CXBoard.side(p) == cur_side:
                self.selected = (r, c)
                self.legal = self.board.legal_moves(r, c)

    # ─── 教学模式 ─────────────────────────
    def _tutorial_click(self, pos):
        """教学模式：点任意棋子显示走法 + 高亮可达格"""
        rc = self.xy_rc(*pos)
        if not rc:
            self.selected = None; self.legal = []
            return
        r, c = rc
        p = self.board.grid[r][c]
        if p:
            self.selected = (r, c)
            # 教学模式展示所有"伪合法步"（不管是否让自己被将）
            self.legal = self.board.pseudo_moves(r, c)
        else:
            self.selected = None; self.legal = []

    def _draw_tutorial_card(self):
        """教学模式右侧规则说明卡片"""
        card_x = PAD_X + CELL * 8 + PAD_X + 4
        card_w = WIN_W - card_x - 4
        if card_w < 20:
            # 窗口不够宽则改为棋盘下方浮层
            self._draw_tutorial_overlay()
            return

        card_rect = pygame.Rect(card_x, PAD_Y, card_w, BOARD_H - PAD_Y * 2)
        pygame.draw.rect(self.screen, (28, 24, 18), card_rect, border_radius=8)
        pygame.draw.rect(self.screen, MENU_DIM, card_rect, 1, border_radius=8)

        if not self.selected:
            tip = self.font_xs.render("点击任意棋子", True, MENU_DIM)
            tip2 = self.font_xs.render("查看走法说明", True, MENU_DIM)
            self.screen.blit(tip, (card_rect.centerx - tip.get_width()//2, card_rect.centery - 20))
            self.screen.blit(tip2,(card_rect.centerx - tip2.get_width()//2, card_rect.centery + 4))
            return

        r, c = self.selected
        p = self.board.grid[r][c]
        if not p or p not in PIECE_RULES:
            return

        name, rules = PIECE_RULES[p]
        side = CXBoard.side(p)
        color = PIECE_R_TXT if side == 'R' else (60, 60, 60)
        bg_c  = PIECE_R_BG  if side == 'R' else PIECE_B_BG

        # 棋子头像小圆
        cx2 = card_rect.centerx
        pygame.draw.circle(self.screen, bg_c,   (cx2, card_rect.y + 36), 22)
        pygame.draw.circle(self.screen, MENU_DIM,(cx2, card_rect.y + 36), 22, 1)
        ns = self.font_md.render(name, True, color)
        self.screen.blit(ns, (cx2 - ns.get_width()//2, card_rect.y + 36 - ns.get_height()//2))

        # 棋子名称标题
        title_s = self.font_sm.render(name + ('（红）' if side == 'R' else '（黑）'),
                                       True, MENU_TITLE)
        self.screen.blit(title_s, (cx2 - title_s.get_width()//2, card_rect.y + 66))

        # 分隔线
        pygame.draw.line(self.screen, MENU_DIM,
                         (card_rect.x + 6, card_rect.y + 86),
                         (card_rect.right - 6, card_rect.y + 86), 1)

        # 走法说明
        ty = card_rect.y + 95
        for i, rule in enumerate(rules):
            # 自动换行
            words = rule
            max_w = card_w - 14
            line = ''
            for ch in words:
                test = line + ch
                tw = self.font_xs.render(test, True, MENU_SUB).get_width()
                if tw > max_w and line:
                    rs = self.font_xs.render(f'{"·" if i==0 and not line else " "} {line}', True, MENU_SUB)
                    self.screen.blit(rs, (card_rect.x + 7, ty))
                    ty += rs.get_height() + 1
                    line = ch
                else:
                    line = test
            if line:
                prefix = '· ' if not any(rule.startswith(r[:3]) and line != rule for r in rules) else '  '
                rs = self.font_xs.render(prefix + line, True, MENU_SUB)
                self.screen.blit(rs, (card_rect.x + 7, ty))
                ty += rs.get_height() + 3

        # 可达格数提示
        ty += 4
        cnt_s = self.font_xs.render(f'可走 {len(self.legal)} 个位置', True, MENU_GOLD)
        self.screen.blit(cnt_s, (cx2 - cnt_s.get_width()//2, ty))

    def _draw_tutorial_overlay(self):
        """教学模式规则浮层（窗口窄时显示在棋盘左上角）"""
        if not self.selected: return
        r, c = self.selected
        p = self.board.grid[r][c]
        if not p or p not in PIECE_RULES: return
        name, rules = PIECE_RULES[p]
        side = CXBoard.side(p)
        color = PIECE_R_TXT if side == 'R' else (30, 30, 30)

        ow, oh = 200, 30 + len(rules) * 20 + 24
        ox, oy = 8, BOARD_H - oh - 8
        surf = pygame.Surface((ow, oh), pygame.SRCALPHA)
        surf.fill((20, 16, 10, 200))
        pygame.draw.rect(surf, MENU_DIM, (0, 0, ow, oh), 1, border_radius=6)
        ts = self.font_sm.render(name, True, MENU_TITLE)
        surf.blit(ts, (ow//2 - ts.get_width()//2, 6))
        ty2 = 28
        for rule in rules:
            rs = self.font_xs.render('· ' + rule[:22], True, MENU_SUB)
            surf.blit(rs, (6, ty2)); ty2 += 19
        self.screen.blit(surf, (ox, oy))

    # ─── 绘制游戏 ─────────────────────────
    def _draw_game(self):
        self.screen.fill(C_BG)
        self._draw_board_bg()
        self._draw_lines()
        self._draw_river()
        self._draw_coords()
        self._draw_overlays()
        self._draw_pieces()
        if self.game_mode == 'tutorial':
            self._draw_tutorial_card()
        self._draw_info()

    def _draw_board_bg(self):
        """棋盘木纹底色 + 边框"""
        # 外框
        border = pygame.Rect(PAD_X - 22, PAD_Y - 22,
                             CELL*8 + 44, CELL*9 + 44)
        pygame.draw.rect(self.screen, (120, 80, 30), border, 3, border_radius=4)
        # 内框
        inner = pygame.Rect(PAD_X - 8, PAD_Y - 8,
                            CELL*8 + 16, CELL*9 + 16)
        pygame.draw.rect(self.screen, (160, 120, 60), inner, 2)

    def _draw_lines(self):
        # 竖线
        for c in range(COLS):
            x = PAD_X + c * CELL
            y0, y4 = PAD_Y, PAD_Y + 4*CELL
            y5, y9 = PAD_Y + 5*CELL, PAD_Y + 9*CELL
            if c == 0 or c == COLS-1:
                pygame.draw.line(self.screen, C_LINE, (x,y0),(x,y9), 1)
            else:
                pygame.draw.line(self.screen, C_LINE, (x,y0),(x,y4), 1)
                pygame.draw.line(self.screen, C_LINE, (x,y5),(x,y9), 1)

        # 横线
        for r in range(ROWS):
            y = PAD_Y + r * CELL
            pygame.draw.line(self.screen, C_LINE, (PAD_X, y), (PAD_X+8*CELL, y), 1)

        # 九宫斜线
        for top in (0, 7):
            x1, x2 = PAD_X+3*CELL, PAD_X+5*CELL
            y1 = PAD_Y + top*CELL; y2 = PAD_Y + (top+2)*CELL
            pygame.draw.line(self.screen, C_LINE, (x1,y1),(x2,y2), 1)
            pygame.draw.line(self.screen, C_LINE, (x2,y1),(x1,y2), 1)

        # 炮/兵位小十字
        markers = [(2,1),(2,7),(7,1),(7,7),
                   (3,0),(3,2),(3,4),(3,6),(3,8),
                   (6,0),(6,2),(6,4),(6,6),(6,8)]
        for mr, mc in markers:
            self._cross(mr, mc)

    def _cross(self, r, c):
        x, y = self.rc_xy(r, c)
        d, g = 5, 3
        if c > 0:
            pygame.draw.line(self.screen, C_LINE, (x-g,y),(x-g-d,y), 1)
            pygame.draw.line(self.screen, C_LINE, (x-g,y-d),(x-g,y+d), 1)
        if c < COLS-1:
            pygame.draw.line(self.screen, C_LINE, (x+g,y),(x+g+d,y), 1)
            pygame.draw.line(self.screen, C_LINE, (x+g,y-d),(x+g,y+d), 1)

    def _draw_river(self):
        y = PAD_Y + 4*CELL + CELL//2
        t1 = self.font_river.render("楚  河", True, C_RIVER)
        t2 = self.font_river.render("汉  界", True, C_RIVER)
        self.screen.blit(t1, (PAD_X + CELL*1, y - t1.get_height()//2))
        self.screen.blit(t2, (PAD_X + CELL*5, y - t2.get_height()//2))

    def _draw_coords(self):
        # 底部列号 1-9
        for c in range(COLS):
            x = PAD_X + c * CELL
            # 红方视角从右到左 1-9
            num_r = str(9 - c)
            num_b = chr(ord('a') + c)
            # 底部（红方列号）
            s1 = self.font_coord.render(num_r, True, C_RIVER)
            self.screen.blit(s1, (x - s1.get_width()//2, PAD_Y + 9*CELL + 10))
            # 顶部（黑方列号）
            s2 = self.font_coord.render(num_b, True, C_RIVER)
            self.screen.blit(s2, (x - s2.get_width()//2, PAD_Y - 20))

    def _draw_overlays(self):
        self.overlay.fill((0,0,0,0))

        if self.board.last_move:
            for sq in self.board.last_move:
                x, y = self.rc_xy(*sq)
                pygame.draw.circle(self.overlay, (106,168,79,120), (x,y), self.pr+2)

        if self.board.status in ('check','checkmate'):
            king = self.board.find_king(self.board.turn)
            if king:
                x, y = self.rc_xy(*king)
                pygame.draw.circle(self.overlay, (*C_CHECK, 140), (x,y), self.pr+2)

        if self.selected:
            x, y = self.rc_xy(*self.selected)
            pygame.draw.circle(self.overlay, (*C_SELECT, 180), (x,y), self.pr+4, 4)

        for tr, tc in self.legal:
            x, y = self.rc_xy(tr, tc)
            if self.board.grid[tr][tc]:
                pygame.draw.circle(self.overlay, (*C_LEGAL, 160), (x,y), self.pr+1, 4)
            else:
                pygame.draw.circle(self.overlay, (*C_LEGAL, 160), (x,y), 10)

        self.screen.blit(self.overlay, (0,0))

    def _draw_pieces(self):
        # 动画中隐藏目标位置的棋子（因为 apply 已移过去）
        hide_r = self.anim['tr'] if self.anim else -1
        hide_c = self.anim['tc'] if self.anim else -1
        for r in range(ROWS):
            for c in range(COLS):
                p = self.grid(r, c)
                if not p: continue
                if self.anim and r == hide_r and c == hide_c: continue
                x, y = self.rc_xy(r, c)
                side = CXBoard.side(p)
                name = RED_NAMES.get(p,'') or BLACK_NAMES.get(p,p)
                is_sel = (self.selected == (r, c))
                draw_piece_3d(self.screen, self.font_piece, x, y,
                              name, side, self.pr, selected=is_sel)
        # 绘制动画中的棋子
        if self.anim:
            a = self.anim
            raw_t = min(1.0, a['t'] / a['dur'])
            # easeOutCubic：起手果断，到位减速，模拟真实落子手感
            t = 1 - (1 - raw_t) ** 3
            cx = a['fx'] + (a['tx'] - a['fx']) * t
            cy = a['fy'] + (a['ty'] - a['fy']) * t
            draw_piece_3d(self.screen, self.font_piece, cx, cy,
                          a['name'], a['side'], self.pr + 2, selected=False)

    def grid(self, r, c):
        return self.board.grid[r][c]

    def _draw_info(self):
        info_rect = pygame.Rect(0, BOARD_H, WIN_W, INFO_H)
        pygame.draw.rect(self.screen, C_INFO_BG, info_rect)

        s = self.board.status
        turn = "红方" if self.board.turn == 'R' else "黑方"

        if self.game_mode == 'tutorial':
            msg = "【教学模式】点击任意棋子 查看走法说明与可走位置"
            if self.selected:
                r, c = self.selected
                p = self.board.grid[r][c]
                if p and p in PIECE_RULES:
                    pname = PIECE_RULES[p][0]
                    side_str = "红方" if CXBoard.side(p) == 'R' else "黑方"
                    msg = f"【{side_str}】{pname}  ·  可走 {len(self.legal)} 个位置"
        elif self.game_mode == 'pvp':
            if s == 'playing':
                msg = f"【双人对战】{turn} 走棋"
            elif s == 'check':
                msg = f"⚠ {turn} 被将军！"
            elif s == 'checkmate':
                w = "红方" if self.board.winner == 'R' else "黑方"
                msg = f"将死！{w} 获胜！"
            elif s == 'draw':
                msg = "困毙 — 平局"
            else:
                msg = ""
        else:  # ai
            lv_name = AI_LEVELS[self.ai_level]['name'] if self.ai_level else ''
            if s == 'playing':
                msg = f"难度:{lv_name}  |  {turn} 走棋"
                if self.ai_thinking:
                    msg = f"难度:{lv_name}  |  电脑思考中…"
            elif s == 'check':
                msg = f"⚠ {turn} 被将军！"
            elif s == 'checkmate':
                w = "红方" if self.board.winner == 'R' else "黑方"
                msg = f"将死！{w} 获胜！"
            elif s == 'draw':
                msg = "困毙 — 平局"
            else:
                msg = ""

        surf = self.font_md.render(msg, True, C_INFO_TXT)
        self.screen.blit(surf, (20, BOARD_H + 8))

        hint_text = "[R] 重新开始   [Esc] 返回菜单   [Q] 退出"
        hint = self.font_sm.render(hint_text, True, C_INFO_HINT)
        self.screen.blit(hint, (20, BOARD_H + 34))

    # ─── 动画系统（平滑滑动） ────────────
    def _start_anim(self, piece, side, name, fr, fc, tr, tc):
        fx, fy = self.rc_xy(fr, fc)
        tx, ty = self.rc_xy(tr, tc)
        dist = math.hypot(tx - fx, ty - fy)
        # 时长 = 基础 + 距离/速度，模拟真实棋子"拿起→放到目标位置"的节奏
        dur = max(0.12, self.anim_base_dur + dist / self.anim_px_per_sec)
        captured = self.board.grid[tr][tc] is not None
        self.anim = {
            'piece': piece, 'side': side, 'name': name,
            'fx': fx, 'fy': fy, 'tx': tx, 'ty': ty,
            'sr': fr, 'sc': fc, 'tr': tr, 'tc': tc,
            't': 0.0, 'dur': dur, 'capture': captured,
        }

    def _update_anim(self, dt):
        if not self.anim: return
        self.anim['t'] += dt
        if self.anim['t'] >= self.anim['dur']:
            # 动画结束，播放音效
            if self.anim['capture']:
                self.snd_capture.play()
            else:
                self.snd_place.play()
            # 将军提示音
            if self.board.status == 'check':
                self.snd_check.play()
            # 语音播报
            if self.anim['capture'] and 'capture' in self.snd_tts:
                self.snd_tts['capture'].play()
            if self.board.status == 'check' and 'check' in self.snd_tts:
                self.snd_tts['check'].play()
            self.anim = None

    # ─── 游戏结束弹窗 ─────────────────────
    def _draw_game_over(self):
        if self.game_mode == 'tutorial':
            return
        st = self.board.status
        if st not in ('checkmate', 'draw'):
            return

        # 一次性音效 + 语音播报
        if not self.game_over_announced:
            self.game_over_announced = True
            tts = self.snd_tts
            if st == 'checkmate':
                w = self.board.winner
                if w == 'R':
                    self.snd_win.play()
                    if 'checkmate_win' in tts:
                        tts['checkmate_win'].play()
                else:
                    self.snd_lose.play()
                    if 'checkmate_lose' in tts:
                        tts['checkmate_lose'].play()
            elif st == 'draw':
                if 'draw_game' in tts:
                    tts['draw_game'].play()

        cx = WIN_W // 2
        cy = BOARD_H // 2
        bw, bh = 360, 180
        bx = cx - bw // 2
        by = cy - bh // 2

        # 半透明背景
        overlay = pygame.Surface((bw, bh), pygame.SRCALPHA)
        overlay.fill(GEO_BG)
        self.screen.blit(overlay, (bx, by))
        pygame.draw.rect(self.screen, (100, 85, 60), (bx, by, bw, bh), 2, border_radius=8)

        if st == 'checkmate':
            w = self.board.winner
            if w == 'R':
                title = "YOU WIN!"
                result = "将死！红方获胜"
                color = GEO_WIN
            else:
                title = "YOU LOSE"
                result = "将死！黑方获胜"
                color = GEO_LOSE
        else:
            title = "DRAW"
            result = "困毙 — 平局"
            color = GEO_DRAW

        ts = self.font_lg.render(title, True, color)
        self.screen.blit(ts, (cx - ts.get_width()//2, by + 20))
        rs = self.font_md.render(result, True, (220, 215, 200))
        self.screen.blit(rs, (cx - rs.get_width()//2, by + 85))
        hint = self.font_sm.render("R = 重新开始    Esc = 菜单", True, MENU_SUB)
        self.screen.blit(hint, (cx - hint.get_width()//2, by + 135))


# ═══════════════════ 入口 ═══════════════════
if __name__ == '__main__':
    app = ChessApp()
    app.run()
