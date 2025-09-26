import React, { useState } from 'react'

export default function App(){
  const [sector, setSector] = useState('')
  const [subsector, setSubsector] = useState('')
  const [stage, setStage] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState('')

  async function analyzeSector(){
    if(!sector) return
    setLoading(true)
    setResult('')
    try{
      const res = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sector })
      })
      const data = await res.json()
      setResult(data.assistant_response || '')
      setStage(data.stage || 'done')
    }catch(e){
      setResult('Error: '+String(e))
    }finally{setLoading(false)}
  }

  async function analyzeSubsector(){
    if(!subsector) return
    setLoading(true)
    setResult('')
    try{
      const res = await fetch('http://localhost:8000/api/subsector', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subsector })
      })
      const data = await res.json()
      setResult(data.assistant_response || '')
      setStage('done')
    }catch(e){
      setResult('Error: '+String(e))
    }finally{setLoading(false)}
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-md mx-auto bg-white shadow-md rounded-xl p-4">
        <h1 className="text-xl font-semibold mb-2">Equity Research — Sector Explorer</h1>

        <label className="block text-sm font-medium text-gray-700">Sector</label>
        <input value={sector} onChange={e=>setSector(e.target.value)} className="mt-1 p-2 border rounded w-full" placeholder="e.g. Automotive" />
        <button onClick={analyzeSector} disabled={loading} className="mt-3 w-full py-2 rounded bg-blue-600 text-white">{loading? 'Analyzing...':'Analyze Sector'}</button>

        {stage === 'subsector_detail' && (
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700">Subsector</label>
            <input value={subsector} onChange={e=>setSubsector(e.target.value)} className="mt-1 p-2 border rounded w-full" placeholder="e.g. Electric Vehicles" />
            <button onClick={analyzeSubsector} disabled={loading} className="mt-3 w-full py-2 rounded bg-green-600 text-white">{loading? 'Loading...':'Analyze Subsector'}</button>
          </div>
        )}

        <div className="mt-4 p-3 bg-gray-100 rounded h-64 overflow-auto">
          <pre className="whitespace-pre-wrap text-sm">{result || 'Results will appear here...'}</pre>
        </div>
      </div>
    </div>
  )
}