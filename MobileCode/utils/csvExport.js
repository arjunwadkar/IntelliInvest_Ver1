// MobileCode/utils/csvExport.js
export function jsonToCSV(rows = [], fields = null){
  if(!rows || rows.length === 0) return ''
  const keys = fields || Object.keys(rows[0])
  const header = keys.join(',')
  const lines = rows.map(r => keys.map(k => {
    const v = r[k] ?? ''
    const s = typeof v === 'string' ? v.replace(/"/g, '""') : `${v}`
    return `"${s}"`
  }).join(','))
  return [header, ...lines].join('\n')
}
