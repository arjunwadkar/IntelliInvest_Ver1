// MobileCode/components/ComparisonTable.jsx
import React, { forwardRef } from 'react'
import { View, Text } from 'react-native'
import styles from '../styles'

const ComparisonTable = forwardRef(({ companiesData = {} }, ref) => {
  const symbols = Object.keys(companiesData)
  if(symbols.length === 0){
    return <View ref={ref} style={styles.comparisonContainer}><Text>No companies selected</Text></View>
  }

  const cols = new Set()
  symbols.forEach(sym => {
    const obj = companiesData[sym] || {}
    Object.keys(obj).forEach(k => cols.add(k))
  })
  const columns = Array.from(cols)

  return (
    <View ref={ref} style={styles.comparisonContainer}>
      <Text style={styles.comparisonTitle}>Company Comparison</Text>
      <View style={{flexDirection:'row', paddingBottom:8}}>
        <Text style={{width:100, fontWeight:'700'}}>Symbol</Text>
        {columns.map(c => <Text key={c} style={{flex:1, fontWeight:'700'}}>{c}</Text>)}
      </View>
      {symbols.map(sym => {
        const obj = companiesData[sym] || {}
        return (
          <View key={sym} style={{flexDirection:'row', paddingVertical:6, borderTopWidth:1, borderTopColor:'#f0f0f0'}}>
            <Text style={{width:100}}>{sym}</Text>
            {columns.map(c => <Text key={c} style={{flex:1}}>{obj[c] ?? '-'}</Text>)}
          </View>
        )
      })}
    </View>
  )
})

export default ComparisonTable
