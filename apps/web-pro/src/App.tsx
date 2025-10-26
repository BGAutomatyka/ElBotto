import React, { useEffect, useRef } from 'react'
import { createChart, ColorType, LineStyle } from 'lightweight-charts'

const PriceChart: React.FC<{ data: number[] }> = ({ data }) => {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(()=>{
    if(!ref.current) return
    const chart = createChart(ref.current, { width: ref.current.clientWidth, height: 320, layout:{ background:{ type: ColorType.Solid, color:'#fff' }, textColor:'#111827' }, rightPriceScale:{ borderVisible:false }, timeScale:{ borderVisible:false } })
    const line = chart.addLineSeries({ color: '#0ea5e9', lineWidth: 2 })
    const sma = chart.addLineSeries({ color: '#10b981', lineWidth: 1 })
    const ema = chart.addLineSeries({ color: '#ef4444', lineWidth: 1 })
    const N = data.length
    const points = data.map((v,i)=>({ time: i as any, value: v }))
    const smaArr = data.map((_,i)=>{ const s=data.slice(Math.max(0,i-49), i+1); return s.reduce((a,b)=>a+b,0)/s.length })
    const emaArr = (()=>{ const k=2/(21+1); let e=data[0]; return data.map((v,i)=>{ e = i? (v*k + e*(1-k)) : data[0]; return e }) })()
    line.setData(points)
    sma.setData(smaArr.map((v,i)=>({time:i as any, value:v})))
    ema.setData(emaArr.map((v,i)=>({time:i as any, value:v})))
    const resize = ()=> chart.applyOptions({ width: ref.current!.clientWidth })
    window.addEventListener('resize', resize)
    return ()=>{ window.removeEventListener('resize', resize); chart.remove() }
  },[data])
  return <div ref={ref} style={{width:'100%',height:320}}/>
}

const App: React.FC = () => {
  const [series, setSeries] = React.useState<number[]>([100])
  const [running, setRunning] = React.useState(true)
  useEffect(()=>{
    const id = setInterval(()=>{
      if(!running) return
      setSeries(s=>{ const price = s[s.length-1]; const drift=(100-price)*0.05; const shock=(Math.random()-0.5)*1.2; const next=Math.max(0.1, price+drift+shock); const arr=[...s, next].slice(-1000); return arr })
    }, 250)
    return ()=> clearInterval(id)
  },[running])
  return (
    <div style={{maxWidth:1200, margin:'0 auto', padding:16}}>
      <header style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:12}}>
        <div><h1 style={{margin:0,fontSize:20}}>ElBotto PRO</h1><div style={{color:'#6b7280',fontSize:12}}>React + Lightweight Charts</div></div>
        <div style={{display:'flex',gap:8}}><button onClick={()=>setRunning(true)}>Start</button><button onClick={()=>setRunning(false)}>Stop</button></div>
      </header>
      <div style={{background:'#fff',border:'1px solid #e5e7eb',borderRadius:14,padding:12}}>
        <PriceChart data={series}/>
      </div>
    </div>
  )
}
export default App
