import React, { useEffect, useMemo, useRef, useState } from 'react'
import type { FC } from 'react'

function useLiveOrSimFeed(enabledLive: boolean) {
  const [price, setPrice] = useState(100.0)
  const [series, setSeries] = useState<{ t: number; p: number }[]>([])
  const wsRef = useRef<WebSocket | null>(null)
  useEffect(() => {
    let timer: any
    if (enabledLive) {
      const proto = location.protocol === 'https:' ? 'wss' : 'ws'
      const ws = new WebSocket(`${proto}://${location.host}/ws`)
      wsRef.current = ws
      ws.onmessage = (ev) => {
        try {
          const m = JSON.parse(ev.data)
          if (m.type === 'status' && m.last_price) {
            const t = Date.now()
            const p = parseFloat(m.last_price)
            setPrice(p)
            setSeries((s) => {
              const next = [...s, { t, p }]
              return next.slice(-300)
            })
          }
        } catch {}
      }
      ws.onclose = () => { wsRef.current = null }
      return () => ws.close()
    } else {
      timer = setInterval(() => {
        const t = Date.now()
        const wave = Math.sin(t / 6000) * 0.0008
        const noise = (Math.random() - 0.5) * 0.0025
        setPrice((prev) => {
          const next = prev * (1 + wave + noise)
          setSeries((s) => {
            const arr = [...s, { t, p: next }]
            return arr.slice(-300)
          })
          return next
        })
      }, 700)
      return () => clearInterval(timer)
    }
  }, [enabledLive])
  return { price, series }
}

function zScore(values: number[], window: number) {
  if (values.length < window) return null
  const w = values.slice(-window)
  const mean = w.reduce((a, b) => a + b, 0) / w.length
  const varr = w.reduce((a, b) => a + (b - mean) ** 2, 0) / w.length
  const sd = Math.sqrt(varr) || 1e-9
  return (w[w.length - 1] - mean) / sd
}

function bbands(values: number[], window: number, k: number) {
  if (values.length < window) return { lower: null as number | null, mid: null as number | null, upper: null as number | null }
  const w = values.slice(-window)
  const mean = w.reduce((a, b) => a + b, 0) / w.length
  const varr = w.reduce((a, b) => a + (b - mean) ** 2, 0) / w.length
  const sd = Math.sqrt(varr) || 1e-9
  return { lower: mean - k * sd, mid: mean, upper: mean + k * sd }
}

type Position = { side: 'long'|'short'; qty: number; entry: number; highWater: number; lowWater: number; ts: number }

const App: FC = () => {
  const [live, setLive] = useState(false)
  const [running, setRunning] = useState(false)
  const [zWindow, setZWindow] = useState(60)
  const [zEntry, setZEntry] = useState(1.2)
  const [bbWindow, setBbWindow] = useState(60)
  const [bbK, setBbK] = useState(2.0)
  const [trailPct, setTrailPct] = useState(0.004)
  const [slPct, setSlPct] = useState(0.006)
  const [tpPct, setTpPct] = useState(0.008)
  const [perTradeUsd, setPerTradeUsd] = useState(25)
  const [maxPosMins, setMaxPosMins] = useState(240)

  const { price, series } = useLiveOrSimFeed(live)
  const prices = useMemo(() => series.map((s) => s.p), [series])

  const [equity, setEquity] = useState(1000)
  const [cash, setCash] = useState(1000)
  const [pos, setPos] = useState<Position|null>(null)
  const [wins, setWins] = useState(0)
  const [losses, setLosses] = useState(0)
  const [lastSignal, setLastSignal] = useState<string|null>(null)
  const [lastReason, setLastReason] = useState('—')

  useEffect(() => {
    if (!running || prices.length < Math.max(zWindow, bbWindow)) return
    const z = zScore(prices, zWindow)
    const { lower, upper } = bbands(prices, bbWindow, bbK)
    const last = prices[prices.length - 1]
    let signal: 'buy'|'sell'|null = null
    if (z != null && lower != null && upper != null) {
      if (last < lower && z <= -zEntry) signal = 'buy'
      else if (last > upper && z >= zEntry) signal = 'sell'
    }
    setLastSignal(signal ?? null)
    setLastReason(`z=${z ? z.toFixed(2) : '—'} lower=${lower ? lower.toFixed(2) : '—'} upper=${upper ? upper.toFixed(2) : '—'}`)
    const now = Date.now()
    setPos((p) => {
      if (p) {
        if (p.side === 'long') {
          const hw = Math.max(p.highWater, last)
          let doClose: string|null = null
          if (last <= hw * (1 - trailPct)) doClose = 'trail'
          else if (last <= p.entry * (1 - slPct)) doClose = 'sl'
          else if (last >= p.entry * (1 + tpPct)) doClose = 'tp'
          else if (now - p.ts >= maxPosMins * 60_000) doClose = 'time'
          if (doClose) {
            const pnl = (last - p.entry) * p.qty
            setCash((c) => c + pnl); setEquity((e) => e + pnl)
            pnl >= 0 ? setWins((w) => w + 1) : setLosses((l) => l + 1)
            return null
          }
          return { ...p, highWater: hw }
        } else {
          const lw = Math.min(p.lowWater, last)
          let doClose: string|null = null
          if (last >= lw * (1 + trailPct)) doClose = 'trail'
          else if (last >= p.entry * (1 + slPct)) doClose = 'sl'
          else if (last <= p.entry * (1 - tpPct)) doClose = 'tp'
          else if (now - p.ts >= maxPosMins * 60_000) doClose = 'time'
          if (doClose) {
            const pnl = (p.entry - last) * p.qty
            setCash((c) => c + pnl); setEquity((e) => e + pnl)
            pnl >= 0 ? setWins((w) => w + 1) : setLosses((l) => l + 1)
            return null
          }
          return { ...p, lowWater: lw }
        }
      }
      if (!p && signal) {
        const qty = perTradeUsd / last
        return { side: signal === 'buy' ? 'long' : 'short', qty, entry: last, highWater: last, lowWater: last, ts: now }
      }
      return p
    })
  }, [series])

  const wr = useMemo(() => { const t = wins + losses; return t ? (wins/t)*100 : 0 }, [wins, losses])
  const posText = pos ? `${pos.side} @ ${pos.entry.toFixed(2)} qty=${pos.qty.toFixed(5)}` : '—'

  return (
    <div style={{ fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, Arial', padding: 16 }}>
      <h1>ElBotto — Browser Game (Alpha)</h1>
      <div style={{ marginBottom: 8 }}>
        <button onClick={() => setRunning(true)}>Start</button>
        <button onClick={() => setRunning(false)} style={{ marginLeft: 8 }}>Stop</button>
        <button onClick={() => {
          // reset
          (window as any).RESET=1;
          setWins(0); setLosses(0); setPos(null); setCash(1000); setEquity(1000)
        }} style={{ marginLeft: 8 }}>Reset</button>
        <label style={{ marginLeft: 16 }}><input type="checkbox" checked={live} onChange={(e) => setLive(e.target.checked)} /> Live feed (WS)</label>
      </div>
      <div style={{ marginBottom: 8, fontSize: 12, color: '#555' }}>Signal: <b>{lastSignal ?? '—'}</b> • Reason: {lastReason}</div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <div>
          <div style={{ fontSize: 12, color: '#555', marginBottom: 4 }}>Pozycja</div>
          <div style={{ border: '1px solid #ddd', borderRadius: 8, padding: 8 }}>{posText}</div>
        </div>
        <div>
          <div style={{ fontSize: 12, color: '#555', marginBottom: 4 }}>Wyniki</div>
          <div style={{ border: '1px solid #ddd', borderRadius: 8, padding: 8, display: 'flex', gap: 16 }}>
            <div><div style={{ fontSize: 12 }}>Equity</div><div style={{ fontWeight: 600 }}>${equity.toFixed(2)}</div></div>
            <div><div style={{ fontSize: 12 }}>Cash</div><div style={{ fontWeight: 600 }}>${cash.toFixed(2)}</div></div>
            <div><div style={{ fontSize: 12 }}>Winrate</div><div style={{ fontWeight: 600 }}>{wr.toFixed(1)}%</div></div>
          </div>
        </div>
      </div>
      <hr style={{ margin: '12px 0' }} />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(220px, 1fr))', gap: 12 }}>
        <div>
          <div>Z-window: {zWindow}</div>
          <input type="range" min="20" max="200" value={zWindow} onChange={(e) => setZWindow(parseInt(e.target.value))} />
          <div>Z-entry: {zEntry.toFixed(2)}</div>
          <input type="range" min="0.5" max="3" step="0.1" value={zEntry} onChange={(e) => setZEntry(parseFloat(e.target.value))} />
          <div>BB window: {bbWindow}</div>
          <input type="range" min="20" max="200" value={bbWindow} onChange={(e) => setBbWindow(parseInt(e.target.value))} />
        </div>
        <div>
          <div>BB k: {bbK.toFixed(1)}</div>
          <input type="range" min="1" max="3.5" step="0.1" value={bbK} onChange={(e) => setBbK(parseFloat(e.target.value))} />
          <div>Trailing %: {(trailPct*100).toFixed(2)}%</div>
          <input type="range" min="0.001" max="0.02" step="0.0005" value={trailPct} onChange={(e) => setTrailPct(parseFloat(e.target.value))} />
          <div>SL %: {(slPct*100).toFixed(2)}%</div>
          <input type="range" min="0.001" max="0.03" step="0.0005" value={slPct} onChange={(e) => setSlPct(parseFloat(e.target.value))} />
        </div>
        <div>
          <div>TP %: {(tpPct*100).toFixed(2)}%</div>
          <input type="range" min="0.001" max="0.03" step="0.0005" value={tpPct} onChange={(e) => setTpPct(parseFloat(e.target.value))} />
          <div>Kwota na trade (USD): {perTradeUsd}</div>
          <input type="range" min="5" max="250" step="5" value={perTradeUsd} onChange={(e) => setPerTradeUsd(parseInt(e.target.value))} />
          <div>Maks. czas pozycji (min): {maxPosMins}</div>
          <input type="range" min="5" max="720" step="5" value={maxPosMins} onChange={(e) => setMaxPosMins(parseInt(e.target.value))} />
        </div>
      </div>
      <p style={{ marginTop: 12, fontSize: 12, color: '#555' }}>Tip: Zaznacz "Live feed" aby odbierać dane z backendu (/ws). Bez backendu działa w 100% w przeglądarce (symulator).</p>
    </div>
  )
}

export default App
