import React, { useEffect, useMemo, useRef, useState } from 'react'

// --- Minimal alpha logic (mean reversion + SL/TP + trailing) ---
function useAlphaSim() {
  const [price, setPrice] = useState(100)
  const [equity, setEquity] = useState(10000)
  const [pos, setPos] = useState(0) // -1, 0, +1
  const [log, setLog] = useState<string[]>([])
  const mu = 100
  const vol = 0.6
  const thr = 1.2
  const sl = 2.0
  const tp = 2.0
  const trailing = 1.0
  const best = useRef<number | null>(null)

  useEffect(() => {
    const id = setInterval(() => {
      // OU-like step
      const drift = (mu - price) * 0.05
      const shock = (Math.random() - 0.5) * vol * 2
      const p = Math.max(0.1, price + drift + shock)
      setPrice(p)

      // signal
      const z = p - mu
      if (pos === 0) {
        if (z > thr) { setPos(-1); setLog(l => ["SELL", ...l]) }
        if (z < -thr) { setPos( 1); setLog(l => ["BUY",  ...l]) }
        best.current = p
      } else {
        // trailing stop on best favourable price
        if (pos > 0) best.current = Math.max(best.current ?? p, p)
        if (pos < 0) best.current = Math.min(best.current ?? p, p)
        const trailHit = pos>0 ? (best.current!-p)>=trailing : (p-best.current!)>=trailing

        const pnl = (p - price) * pos
        if (Math.abs(z) < 0.2 || pnl <= -sl || pnl >= tp || trailHit) {
          setEquity(e => e + (p - price) * pos)
          setPos(0)
          setLog(l => ["FLAT", ...l])
          best.current = null
        }
      }
    }, 250)
    return () => clearInterval(id)
  }, [price, pos])

  return { price, equity, pos, log }
}

export default function App() {
  const { price, equity, pos, log } = useAlphaSim()
  const posTxt = pos===1? 'LONG' : pos===-1? 'SHORT' : 'FLAT'

  return (
    <div style={{fontFamily:'system-ui,Segoe UI,Roboto,Arial', padding:16, lineHeight:1.3}}>
      <h1 style={{margin:0}}>Alpha Bot (clean)</h1>
      <p style={{opacity:.7, marginTop:4}}>Minimalna symulacja mean-reversion + SL/TP/trailing. Zero starych plików.</p>
      <div style={{display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:12, marginTop:16}}>
        <Card title="Cena">{price.toFixed(2)}</Card>
        <Card title="Pozycja">{posTxt}</Card>
        <Card title="Equity">{equity.toFixed(2)}</Card>
      </div>
      <h3 style={{marginTop:16}}>Log</h3>
      <ul>{log.slice(0,30).map((e,i)=> <li key={i}>{e}</li>)}</ul>
    </div>
  )
}

function Card({title, children}:{title:string,children:React.ReactNode}){
  return (
    <div style={{border:'1px solid #e5e7eb', borderRadius:12, padding:16, boxShadow:'0 1px 4px rgba(0,0,0,0.04)'}}>
      <div style={{fontSize:12, textTransform:'uppercase', letterSpacing:'.08em', opacity:.7}}>{title}</div>
      <div style={{fontSize:28, fontWeight:600, marginTop:8}}>{children}</div>
    </div>
  )
}
