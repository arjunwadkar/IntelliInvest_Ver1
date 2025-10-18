// MobileCode/components/SectorSelector.jsx
import React from 'react'
import { View, Text, ScrollView, TouchableOpacity } from 'react-native'
import styles from '../styles'

export default function SectorSelector({ sectorsObj = {}, selectedSector, setSelectedSector, selectedSubsector, setSelectedSubsector }){
  const sectors = Object.keys(sectorsObj || {})
  const subsectors = selectedSector ? (sectorsObj[selectedSector] || []) : []

  return (
    <View style={{marginBottom:12}}>
      <Text style={{fontWeight:'600', marginBottom:6}}>Sector</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{marginBottom:8}}>
        {sectors.map(s => (
          <TouchableOpacity key={s} onPress={()=>{ setSelectedSector(s); setSelectedSubsector('') }} style={[styles.chip, selectedSector===s && styles.chipActive]}>
            <Text>{s}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <Text style={{fontWeight:'600', marginBottom:6}}>Subsector</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        <TouchableOpacity onPress={()=>setSelectedSubsector('')} style={[styles.chip, selectedSubsector==='' && styles.chipActive]}>
          <Text>All</Text>
        </TouchableOpacity>
        {subsectors.map(sub => (
          <TouchableOpacity key={sub} onPress={()=>setSelectedSubsector(sub)} style={[styles.chip, selectedSubsector===sub && styles.chipActive]}>
            <Text>{sub}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  )
}
